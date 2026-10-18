# SPDX-License-Identifier: LicenseRef-Proprietary
"""Reference codec for the CNC3 host link (ABI 3) and the IOL1 card link, interface spec IS-1.

Every frame layout, frame length, opcode, chip-select assignment and CRC parameter is read
from spec/protocol.json at run time. Nothing about the wire format is restated here, so the
codec cannot drift from the frozen specification without its self-test failing.

Scope: structural encoding, decoding and validation (length, CRC, magic, ABI, opcode and
chip select, reserved/zero fields, channel-mask width, unmasked-rate rule). Stateful rules
(session and sequence continuity, arm/fault state, watchdogs) belong to the FPGA and driver
state machines and are exercised by their own tests.

    python gateware/v3/tools/protocol_v3.py --check            # self-test against IS-1 vectors
    python gateware/v3/tools/protocol_v3.py --vectors OUT.json  # write golden vectors
"""
import argparse
import binascii
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SPEC_PATH = os.path.join(ROOT, "spec", "protocol.json")

MAX_CHANNELS = 12
CHANNEL_MASK_LIMIT = (1 << MAX_CHANNELS) - 1


class ProtocolError(ValueError):
    """A frame violates a structural rule of IS-1. ``code`` is a stable identifier."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


# ---------------------------------------------------------------- CRCs


def crc16_ccitt_false(data):
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no final XOR."""
    return binascii.crc_hqx(bytes(data), 0xFFFF)


_CRC32C_TABLE = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0x82F63B78 if _c & 1 else _c >> 1
    _CRC32C_TABLE.append(_c)


def crc32c(data):
    """CRC-32C (Castagnoli): reflected poly 0x82F63B78, init and final XOR 0xFFFFFFFF."""
    crc = 0xFFFFFFFF
    for byte in bytes(data):
        crc = _CRC32C_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


# ---------------------------------------------------------------- spec model

_ARRAY = re.compile(r"^(\d+) x (u8|u16)$")
_SCALAR = {"u8": (1, False), "u16": (2, False), "u24": (3, False), "u32": (4, False),
           "s16": (2, True), "s32": (4, True)}


class Field:
    __slots__ = ("name", "type", "offset", "size", "rule", "logical", "count", "elem", "rules")

    def __init__(self, raw):
        self.name = raw["name"]
        self.type = raw["type"]
        self.offset = int(raw["offset"])
        self.size = int(raw["size"])
        self.rule = raw.get("rule", "")
        self.logical = raw.get("logical", "")
        self.count = None
        self.elem = None
        self.rules = {}
        m = _ARRAY.match(self.type)
        if m:
            self.count = int(m.group(1))
            self.elem = m.group(2)
            if self.count * _SCALAR[self.elem][0] != self.size:
                raise ProtocolError("SPEC_FIELD_SIZE", f"{self.name}: {self.type} does not fill {self.size} bytes")
        elif self.type in _SCALAR:
            if _SCALAR[self.type][0] != self.size:
                raise ProtocolError("SPEC_FIELD_SIZE", f"{self.name}: {self.type} is not {self.size} bytes")
        elif self.type not in ("bytes", "ascii"):
            raise ProtocolError("SPEC_FIELD_TYPE", f"{self.name}: unsupported type {self.type}")

    @property
    def must_be_zero(self):
        return self.name == "zero" or self.name.startswith(("zero_", "reserved"))


# ---------------------------------------------------------------- rules derived from the spec text
#
# IS-1 states field and opcode acceptance rules as short phrases. The phrases below are the
# machine-checkable ones; anything else (for example "subset of installed_mask") depends on
# endpoint state and is the receiver's job. tests/test_protocol_v3_reference.py pins the
# derived rules so that a reworded spec phrase shows up as a test failure, not a silent change.

_HEX_PART = re.compile(r"^\s*0x([0-9A-Fa-f]+)(?:-0x([0-9A-Fa-f]+))?(?=$|[ (;])")


def _int(text):
    return int(text.replace(",", ""))


def _allowed(value, ranges):
    return any(lo <= value <= hi for lo, hi in ranges)


def _bits(lo, hi):
    return ((1 << (hi - lo + 1)) - 1) << lo


def derive_field_rules(field, layout):
    """Checkable rules of one field: allowed ranges, zero bits, nonzero, opcode restriction, relations."""
    rule = field.rule.strip()
    inherited = re.match(r"^as ([a-z]+\d)$", rule)
    sibling = re.match(r"^([a-z]+)(\d)(_.*)$", field.name)
    if inherited and sibling:
        # "as probe0": the same rules as the channel-0 row of this table.
        rule = layout.by_name[inherited.group(1) + sibling.group(3)].rule.strip()
    elif not rule and sibling and sibling.group(2) != "0":
        # A blank rule on a channel-1 row repeats the channel-0 row (IS-1 table convention;
        # recorded as an interpretation in gateware/v3/README.md).
        base = layout.by_name.get(sibling.group(1) + "0" + sibling.group(3))
        if base is not None:
            rule = base.rule.strip()
    out = {}
    if not rule or field.type == "ascii":
        return out
    if field.must_be_zero or re.match(r"^(all )?zero\b", rule):
        out["zero"] = True
        return out
    m = re.match(r"^exactly 0x([0-9A-Fa-f]+)\b", rule)
    if m:
        out["allowed"] = [(int(m.group(1), 16),) * 2]
    elif _HEX_PART.match(rule):
        ranges = []
        for part in rule.split(";"):
            hm = _HEX_PART.match(part)
            if hm and "reject" not in part:
                lo = int(hm.group(1), 16)
                ranges.append((lo, int(hm.group(2), 16) if hm.group(2) else lo))
        out["allowed"] = ranges
    elif re.match(r"^\d+$", rule):
        out["allowed"] = [(int(rule),) * 2]
    elif re.match(r"^\d[\d,]*\.\.\d[\d,]*", rule):
        m = re.match(r"^(\d[\d,]*)\.\.(\d[\d,]*)", rule)
        out["allowed"] = [(_int(m.group(1)), _int(m.group(2)))]
    elif re.match(r"^\d+ [A-Za-z0-9]+(, \d+ [A-Za-z0-9]+)+$", rule):
        out["allowed"] = [(int(v),) * 2 for v in re.findall(r"(\d+) [A-Za-z0-9]+", rule)]
    m = re.search(r"each in \[(\d+), (\d+)\]", rule)
    if m:
        out["allowed"] = [(int(m.group(1)), int(m.group(2)))]
    if "nonzero is rejected" in rule:
        out["allowed"] = [(0, 0)]
    if re.match(r"^nonzero\b", rule):
        out["nonzero"] = True
    zero_bits = 0
    for lo, hi in re.findall(r"\bbits (\d+)-(\d+) zero", rule) + re.findall(r"\bb(\d+)-(\d+) zero", rule):
        zero_bits |= _bits(int(lo), int(hi))
    for bit in re.findall(r"\bb(\d+) zero", rule):
        zero_bits |= 1 << int(bit)
    if zero_bits:
        out["zero_bits"] = zero_bits
    m = re.match(r"^([A-Z][A-Z_]*(?:(?:/|, | or )[A-Z][A-Z_]*)*):", rule)
    if m and re.search(r"\bzero\b.*\bfor (unmasked channels and )?(every )?other opcodes?", rule):
        out["only_opcodes"] = set(re.findall(r"[A-Z][A-Z_]+", m.group(1)))
    m = re.search(r"the same bits must be 0 in (\w+)", rule)
    if m:
        out["disjoint_with"] = m.group(1)
    m = re.match(r"^subset of (\w+)$", rule)
    if m and m.group(1) in layout.by_name:
        out["subset_of"] = m.group(1)
    m = re.search(r"bits (\d+)-(\d+) only with (\w+) != 0", rule)
    if m and m.group(3) in layout.by_name:
        out["bits_require"] = (_bits(int(m.group(1)), int(m.group(2))), m.group(3), "nonzero")
    m = re.search(r"bits (\d+)-(\d+) need ([A-Z0-9]+)\b", rule)
    if m:
        for other in layout.fields:
            em = re.search(r"(\d+) " + m.group(3) + r"\b", other.rule)
            if other is not field and em:
                out["bits_require"] = (_bits(int(m.group(1)), int(m.group(2))), other.name, int(em.group(1)))
    return out


def derive_opcode_rules(op, opcodes_by_name, layouts):
    """Structural session/sequence/payload rules of one opcode from the section 3.4 table."""
    session_seq, accepted = op["session_seq"], op["accepted_when"]
    if session_seq.strip() == "as CONFIGURE":
        session_seq = opcodes_by_name["CONFIGURE"]["session_seq"]
    r = {"sequence": None, "session_nonzero": False, "paired": False, "mask_zero": False, "mask_nonzero": False,
         "zero_ranges": [], "byte16": None, "embedded_iol1": None, "rest_zero": False,
         "payload_layout": None, "payload_pages": []}
    if "session 0/sequence 0 before a session" in session_seq:
        r["paired"] = True
    elif re.search(r"\bsequence 0\b", session_seq):
        r["sequence"] = "zero"
    if "next sequence" in session_seq and not r["paired"]:
        r["sequence"] = "nonzero"
        r["session_nonzero"] = True
    if "new nonzero session" in session_seq:
        r["session_nonzero"] = True
    m = re.search(r"bytes (\d+)-(\d+)(?: and (\d+)-(\d+))? zero", accepted)
    if m:
        r["zero_ranges"].append((int(m.group(1)), int(m.group(2))))
        if m.group(3):
            r["zero_ranges"].append((int(m.group(3)), int(m.group(4))))
    frame_len = 176 if op["cs"] == "CS_FB" else 96
    if re.search(r"\bpayload zero\b", accepted):
        r["zero_ranges"].append((16, frame_len - 3))
    if re.search(r"\bmask and rates zero\b|\brates and mask zero\b", accepted):
        r["mask_zero"] = True
    if "mask == required_mask" in accepted:
        r["mask_nonzero"] = True
    m = re.search(r"byte 16 = (?:[a-z]+ )?(\d+)-(\d+)", accepted)
    if m:
        r["byte16"] = [(int(m.group(1)), int(m.group(2)))]
    else:
        m = re.search(r"byte 16 = ((?:\d+ [a-z ]+?)(?:, \d+ [a-z ]+?)*);", accepted)
        if m:
            r["byte16"] = [(int(v),) * 2 for v in re.findall(r"(\d+) [a-z]", m.group(1))]
    m = re.search(r"bytes (\d+)-(\d+) = one complete 40-byte IOL1 frame with control b(\d) set", accepted)
    if m:
        r["embedded_iol1"] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if re.search(r"\brest zero\b", accepted):
        r["rest_zero"] = True
    m = re.search(r"payload per (\w+)", accepted)
    if m and m.group(1) + "_at_16" in layouts:
        r["payload_layout"] = m.group(1) + "_at_16"
    elif "payload valid" in accepted and op["name"].lower() + "_payload_at_16" in layouts:
        r["payload_layout"] = op["name"].lower() + "_payload_at_16"
    elif re.search(r"\bpage \d+-\d+ valid", accepted):
        prefix = op["name"].lower() + "_"
        r["payload_pages"] = sorted(n for n in layouts if n.startswith(prefix) and n.endswith("_at_16")
                                    and "page" in n)
    return r


def check_field(field, value):
    """Return an error code when ``value`` breaks one of the field's derived rules, else None."""
    rules = field.rules
    if isinstance(value, (bytes, bytearray)):
        return "RESERVED_NONZERO" if rules.get("zero") and any(value) else None
    values = value if isinstance(value, list) else [value]
    for v in values:
        if rules.get("zero") and v:
            return "RESERVED_NONZERO"
        if "allowed" in rules and not _allowed(v, rules["allowed"]):
            return "FIELD_RANGE"
        if rules.get("nonzero") and not v:
            return "FIELD_RANGE"
        if v & rules.get("zero_bits", 0):
            return "FIELD_BITS"
    return None


def check_layout(layout, data, base, skip=frozenset()):
    """Apply every derived field rule of ``layout`` to ``data`` starting at ``base``."""
    values = {}
    for f in layout.fields:
        span = range(base + f.offset, base + f.offset + f.size)
        if any(i in skip for i in span):
            continue
        value = _get(data[base:], f)
        values[f.name] = value
        code = check_field(f, value)
        if code:
            raise ProtocolError(code, f"{layout.name}.{f.name} = {value!r} breaks '{f.rule}'")
    for f in layout.fields:
        r = f.rules
        if f.name not in values:
            continue
        if "disjoint_with" in r and values[f.name] & values.get(r["disjoint_with"], 0):
            raise ProtocolError("FIELD_RELATION", f"{f.name} overlaps {r['disjoint_with']}")
        if "subset_of" in r and values[f.name] & ~values.get(r["subset_of"], 0):
            raise ProtocolError("FIELD_RELATION", f"{f.name} is not a subset of {r['subset_of']}")
        if "bits_require" in r:
            bits, other, need = r["bits_require"]
            if values[f.name] & bits:
                ok = values.get(other, 0) != 0 if need == "nonzero" else values.get(other) == need
                if not ok:
                    raise ProtocolError("FIELD_RELATION", f"{f.name} bits need {other} {need}")
    return values


class Layout:
    def __init__(self, name, raw_fields):
        self.name = name
        self.fields = [Field(f) for f in raw_fields]
        self.by_name = {}
        cursor = 0
        for f in sorted(self.fields, key=lambda f: f.offset):
            if f.offset != cursor:
                raise ProtocolError("SPEC_LAYOUT_GAP", f"{name}: {f.name} starts at {f.offset}, expected {cursor}")
            cursor = f.offset + f.size
            if f.name in self.by_name and not f.must_be_zero:
                raise ProtocolError("SPEC_DUPLICATE_FIELD", f"{name}: {f.name}")
            self.by_name.setdefault(f.name, f)
        self.length = cursor
        for f in self.fields:
            f.rules = derive_field_rules(f, self)
        crc = [f for f in self.fields if f.name in ("crc16", "crc32c")]
        self.crc = crc[0] if crc else None
        if self.crc and self.crc.offset + self.crc.size != self.length:
            raise ProtocolError("SPEC_CRC_POSITION", f"{name}: CRC is not the last field")

    def field(self, name):
        try:
            return self.by_name[name]
        except KeyError:
            raise ProtocolError("UNKNOWN_FIELD", f"{self.name} has no field {name!r}") from None


class Spec:
    """IS-1 protocol definitions loaded from spec/protocol.json."""

    def __init__(self, path=SPEC_PATH):
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
        if raw.get("spec_revision") != "IS-1":
            raise ProtocolError("SPEC_REVISION", f"expected IS-1, found {raw.get('spec_revision')!r}")
        self.raw = raw
        self.revision = raw["spec_revision"]
        self.layouts = {name: Layout(name, fields) for name, fields in raw["frames"].items()}
        cs = raw["host_link"]["chip_selects"]
        self.cs_frame_bytes = {name: int(v["frame_bytes"]) for name, v in cs.items()}
        self.cs_opcodes = {name: {int(code, 16) for code in v["opcodes"]} for name, v in cs.items()}
        self.opcodes = {int(o["code"], 16): o for o in raw["opcodes"]}
        self.opcode_by_name = {o["name"]: int(o["code"], 16) for o in raw["opcodes"]}
        by_name = {o["name"]: o for o in raw["opcodes"]}
        self.opcode_rules = {code: derive_opcode_rules(o, by_name, self.layouts) for code, o in self.opcodes.items()}
        self.vectors = {name: bytes.fromhex(v["hex"]) for name, v in raw["crc"]["vectors"].items()}
        self.command_layout = {"CS_FB": "fb_command", "CS_CMD": "cmd_command"}
        self.response_layout = {"CS_FB": "fb_response_CNF3", "CS_CMD": "cmd_response_CNS3"}
        for cs_name, layout in self.command_layout.items():
            if self.layouts[layout].length != self.cs_frame_bytes[cs_name]:
                raise ProtocolError("SPEC_FRAME_LENGTH", f"{layout} is not {self.cs_frame_bytes[cs_name]} bytes")
        payload = self.layouts["fb_command"].field("payload")
        self.payload_offset = payload.offset
        self.payload_size = payload.size

    def layout(self, name):
        try:
            return self.layouts[name]
        except KeyError:
            raise ProtocolError("UNKNOWN_LAYOUT", name) from None

    def cs_for_opcode(self, opcode):
        for cs_name, codes in self.cs_opcodes.items():
            if opcode in codes:
                return cs_name
        raise ProtocolError("UNKNOWN_OPCODE", f"0x{opcode:02X}")


_SPEC = None


def spec():
    global _SPEC
    if _SPEC is None:
        _SPEC = Spec()
    return _SPEC


# ---------------------------------------------------------------- field packing


def _pack_int(value, size, signed):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProtocolError("FIELD_TYPE", f"integer expected, got {value!r}")
    lo, hi = (-(1 << (8 * size - 1)), (1 << (8 * size - 1)) - 1) if signed else (0, (1 << (8 * size)) - 1)
    if not lo <= value <= hi:
        raise ProtocolError("FIELD_RANGE", f"{value} does not fit {'s' if signed else 'u'}{8 * size}")
    return value.to_bytes(size, "big", signed=signed)


def _put(buf, field, value):
    if field.count is not None:
        size, signed = _SCALAR[field.elem]
        if not isinstance(value, (list, tuple)) or len(value) != field.count:
            raise ProtocolError("FIELD_TYPE", f"{field.name}: list of {field.count} expected")
        data = b"".join(_pack_int(v, size, signed) for v in value)
    elif field.type in _SCALAR:
        size, signed = _SCALAR[field.type]
        data = _pack_int(value, size, signed)
    elif field.type == "ascii":
        data = value.encode("ascii") if isinstance(value, str) else bytes(value)
        if len(data) != field.size:
            raise ProtocolError("FIELD_RANGE", f"{field.name}: {field.size} ASCII bytes expected")
    else:
        data = bytes(value)
        if len(data) > field.size:
            raise ProtocolError("FIELD_RANGE", f"{field.name}: at most {field.size} bytes")
        data = data + bytes(field.size - len(data))
    buf[field.offset:field.offset + field.size] = data


def _get(data, field):
    raw = bytes(data[field.offset:field.offset + field.size])
    if field.count is not None:
        size, signed = _SCALAR[field.elem]
        return [int.from_bytes(raw[i * size:(i + 1) * size], "big", signed=signed) for i in range(field.count)]
    if field.type in _SCALAR:
        return int.from_bytes(raw, "big", signed=_SCALAR[field.type][1])
    if field.type == "ascii":
        return raw.decode("ascii", errors="replace")
    return raw


def pack_layout(layout_name, values, length=None):
    """Pack named fields into a zero-filled buffer. CRC fields are left for seal()."""
    layout = spec().layout(layout_name)
    buf = bytearray(length or layout.length)
    for name, value in values.items():
        field = layout.field(name)
        if field is layout.crc:
            raise ProtocolError("FIELD_RANGE", "CRC is computed, not supplied")
        _put(buf, field, value)
    return buf


def unpack_layout(layout_name, data):
    layout = spec().layout(layout_name)
    if len(data) < layout.length:
        raise ProtocolError("LENGTH", f"{layout_name} needs {layout.length} bytes, got {len(data)}")
    out = {}
    for f in layout.fields:
        if f.must_be_zero:
            continue
        out[f.name] = _get(data, f)
    return out


def seal(layout_name, buf):
    """Write the frame CRC (MSB first) over every byte before it."""
    layout = spec().layout(layout_name)
    if layout.crc is None:
        raise ProtocolError("NO_CRC", layout_name)
    if len(buf) != layout.length:
        raise ProtocolError("LENGTH", f"{layout_name} is {layout.length} bytes, got {len(buf)}")
    body = bytes(buf[:layout.crc.offset])
    value = crc32c(body) if layout.crc.name == "crc32c" else crc16_ccitt_false(body)
    buf[layout.crc.offset:layout.length] = value.to_bytes(layout.crc.size, "big")
    return bytes(buf)


def crc_ok(layout_name, data):
    layout = spec().layout(layout_name)
    body = bytes(data[:layout.crc.offset])
    stored = int.from_bytes(data[layout.crc.offset:layout.length], "big")
    return stored == (crc32c(body) if layout.crc.name == "crc32c" else crc16_ccitt_false(body))


# ---------------------------------------------------------------- host commands


def encode_command(opcode, *, session=0, sequence=0, channel_mask=0, fields=None, payload_layout=None,
                   payload=None):
    """Build a sealed CNC3 command for ``opcode`` on its own chip select.

    ``fields`` sets named fields of the command frame (for example ``rate_3`` or ``dout_image``).
    For CS_FB commands, ``payload`` is a dict packed through ``payload_layout`` (one of the
    ``*_at_16`` layouts) or raw bytes; it is placed at the payload offset.
    """
    s = spec()
    if isinstance(opcode, str):
        opcode = s.opcode_by_name[opcode]
    cs = s.cs_for_opcode(opcode)
    layout = s.command_layout[cs]
    values = {"magic": "CNC3", "abi": 3, "opcode": opcode, "channel_mask": channel_mask,
              "session": session, "sequence": sequence}
    values.update(fields or {})
    buf = pack_layout(layout, values)
    if payload is not None:
        if cs != "CS_FB":
            raise ProtocolError("PAYLOAD_ON_CMD", "only CS_FB commands carry a payload")
        if isinstance(payload, dict):
            if not payload_layout:
                raise ProtocolError("PAYLOAD_LAYOUT", "payload_layout is required for a dict payload")
            body = pack_layout(payload_layout, payload)
        else:
            body = bytes(payload)
        if len(body) > s.payload_size:
            raise ProtocolError("FIELD_RANGE", "payload too long")
        buf[s.payload_offset:s.payload_offset + len(body)] = body
    validate_command(cs, bytes(buf[:-2]) + b"\x00\x00", check_crc=False)
    return cs, seal(layout, buf)


def encode_update(*, session, sequence, rates, channel_mask, max_rate=0x01000000, **io_fields):
    """UPDATE for up to twelve channels. ``rates`` has one entry per channel 0..11 (missing = 0)."""
    rates = list(rates) + [0] * (MAX_CHANNELS - len(rates))
    if len(rates) != MAX_CHANNELS:
        raise ProtocolError("FIELD_RANGE", f"at most {MAX_CHANNELS} rates")
    if channel_mask & ~CHANNEL_MASK_LIMIT:
        raise ProtocolError("MASK_WIDTH", f"channel_mask 0x{channel_mask:04X} sets bits above M11")
    fields = dict(io_fields)
    for ch, rate in enumerate(rates):
        if not channel_mask & (1 << ch) and rate != 0:
            raise ProtocolError("UNMASKED_RATE", f"channel {ch} is not in the mask but has rate {rate}")
        if abs(rate) > max_rate:
            raise ProtocolError("RATE_CLAMP", f"channel {ch} rate {rate} exceeds {max_rate}")
        fields[f"rate_{ch}"] = rate
    return encode_command("UPDATE", session=session, sequence=sequence, channel_mask=channel_mask,
                          fields=fields)[1]


def _opcode_owned_bytes(rules):
    owned = set()
    if rules.get("byte16") is not None:
        owned.add(16)
    if rules.get("embedded_iol1"):
        start, stop, _ = rules["embedded_iol1"]
        owned.update(range(start, stop + 1))
    return owned


def _check_opcode_rules(cs, data, opcode):
    s = spec()
    rules = s.opcode_rules[opcode]
    name = s.opcodes[opcode]["name"]
    session = int.from_bytes(data[8:12], "big")
    sequence = int.from_bytes(data[12:16], "big")
    mask = int.from_bytes(data[6:8], "big")
    end = len(data) - 3
    if rules["sequence"] == "zero" and sequence != 0:
        raise ProtocolError("SEQUENCE_RULE", f"{name} carries sequence 0")
    if rules["sequence"] == "nonzero" and sequence == 0:
        raise ProtocolError("SEQUENCE_RULE", f"{name} carries the next nonzero sequence")
    if rules["session_nonzero"] and session == 0:
        raise ProtocolError("SESSION_RULE", f"{name} needs a nonzero session")
    if rules["paired"] and (session == 0) != (sequence == 0):
        raise ProtocolError("SEQUENCE_RULE", f"{name}: session 0 and sequence 0 go together")
    if rules["mask_zero"] and mask:
        raise ProtocolError("MASK_RULE", f"{name} carries channel_mask 0")
    if rules["mask_nonzero"] and not mask:
        raise ProtocolError("MASK_RULE", f"{name} needs a nonzero channel_mask")
    owned = _opcode_owned_bytes(rules)
    if cs == "CS_CMD":
        layout = s.layout(s.command_layout[cs])
        for f in layout.fields:
            allowed = f.rules.get("only_opcodes")
            if allowed is None or name in allowed:
                continue
            span = set(range(f.offset, f.offset + f.size)) - owned
            if any(data[i] for i in span):
                code = "RATE_ON_NON_UPDATE" if f.name.startswith("rate_") else "FIELD_NOT_ALLOWED"
                raise ProtocolError(code, f"{f.name} must be zero for {name}")
    for lo, hi in rules["zero_ranges"]:
        if any(data[lo:hi + 1]):
            raise ProtocolError("PAYLOAD_NONZERO", f"{name}: bytes {lo}-{hi} must be zero")
    if rules["byte16"] is not None and not _allowed(data[16], rules["byte16"]):
        raise ProtocolError("FIELD_RANGE", f"{name}: byte 16 value {data[16]} not allowed")
    if rules["embedded_iol1"]:
        start, stop, bit = rules["embedded_iol1"]
        inner = bytes(data[start:stop + 1])
        try:
            validate_iol1("iol1_command", inner)
        except ProtocolError as error:
            raise ProtocolError("EMBEDDED_FRAME", f"{name}: {error}") from None
        if not inner[s.layout("iol1_command").field("control").offset] & (1 << bit):
            raise ProtocolError("EMBEDDED_FRAME", f"{name}: embedded frame lacks control b{bit}")
    if rules["rest_zero"]:
        covered = owned
        if any(data[i] for i in range(16, end + 1) if i not in covered):
            raise ProtocolError("PAYLOAD_NONZERO", f"{name}: unused payload bytes must be zero")
    return rules


def payload_layout_for(opcode, data):
    """The payload layout that applies to a CS_FB command, or None when the opcode has none."""
    s = spec()
    rules = s.opcode_rules[opcode]
    if rules["payload_layout"]:
        return rules["payload_layout"]
    candidates = rules["payload_pages"]
    if not candidates:
        return None
    page = data[s.payload_offset]
    for layout_name in candidates:
        page_field = s.layout(layout_name).field("page")
        if check_field(page_field, page) is None:
            return layout_name
    raise ProtocolError("FIELD_RANGE", f"no {s.opcodes[opcode]['name']} page {page}")


DEFAULT_TIMING = [250, 250, 250, 250]


def configure_values(**overrides):
    """CONFIGURE payload fields (section 3.13) with conservative defaults for tests and tools."""
    values = {"format": 2, "expected_module_class": 0, "required_mask": 0x00FF, "alarm_trip_mask": 0,
              "alarm_on_no_current": 0, "config_hash": 0, "servo_period_us": 1000,
              "expected_encoder_expansion_class": 0, "encoder_filter_ticks": 0, "required_encoder_mask": 0,
              "mpg_config": 0}
    for ch in range(MAX_CHANNELS):
        values[f"timing_{ch}"] = list(DEFAULT_TIMING)
    values.update(overrides)
    return values


def encode_configure(*, session=0, sequence=0, **payload):
    """Sealed CONFIGURE (CS_FB). Session 0 / sequence 0 before a session, else current/next."""
    return encode_command("CONFIGURE", session=session, sequence=sequence,
                          payload=configure_values(**payload), payload_layout="configure_payload_at_16")[1]


def encode_fb_read(*, session=0, event_ack=0, telemetry_source=0xFF, telemetry_page=0):
    return encode_command("FB_READ", session=session, payload={
        "event_ack": event_ack, "telemetry_priority_source": telemetry_source,
        "telemetry_priority_page": telemetry_page}, payload_layout="fb_read_payload_at_16")[1]


def validate_command(cs, data, *, check_crc=True):
    """Structural validation of a command frame as received on chip select ``cs``.

    Checks, in order: length, CRC, magic, ABI, opcode and chip select, channel-mask width,
    reserved/zero fields and bit rules of the frame, the per-opcode session/sequence and
    payload rules of section 3.4, the unmasked-rate rule, and the rules of the payload layout.
    Stateful rules (current session, next sequence, armed state, installed channels) are the
    receiver's. Raises ProtocolError with a stable code; returns the decoded fields.
    """
    s = spec()
    if cs not in s.cs_frame_bytes:
        raise ProtocolError("UNKNOWN_CS", cs)
    length = s.cs_frame_bytes[cs]
    if len(data) != length:
        raise ProtocolError("LENGTH", f"{cs} frames are {length} bytes, got {len(data)}")
    layout_name = s.command_layout[cs]
    layout = s.layout(layout_name)
    if check_crc and not crc_ok(layout_name, data):
        raise ProtocolError("CRC", f"{layout_name} CRC mismatch")
    if bytes(data[0:4]) != b"CNC3":
        raise ProtocolError("MAGIC", f"expected CNC3, got {bytes(data[0:4])!r}")
    if data[4] != 3:
        raise ProtocolError("ABI", f"expected ABI 3, got {data[4]}")
    opcode = data[5]
    if opcode not in s.opcodes:
        raise ProtocolError("UNKNOWN_OPCODE", f"0x{opcode:02X}")
    if opcode not in s.cs_opcodes[cs]:
        raise ProtocolError("WRONG_CS", f"opcode 0x{opcode:02X} is not valid on {cs}")
    mask = int.from_bytes(data[6:8], "big")
    if mask & ~CHANNEL_MASK_LIMIT:
        raise ProtocolError("MASK_WIDTH", f"channel_mask bits 12-15 set (0x{mask:04X})")
    rules = _check_opcode_rules(cs, data, opcode)
    owned = _opcode_owned_bytes(rules)
    check_layout(layout, data, 0, skip=owned | {i for f in layout.fields if f.name in ("magic", "abi", "opcode",
                                                                                   "channel_mask", "crc16")
                                                for i in range(f.offset, f.offset + f.size)})
    decoded = unpack_layout(layout_name, data)
    if cs == "CS_CMD":
        for ch in range(MAX_CHANNELS):
            if not mask & (1 << ch) and decoded[f"rate_{ch}"] != 0 and not (ch == 0 and 16 in owned):
                raise ProtocolError("UNMASKED_RATE", f"channel {ch} not in mask has nonzero rate")
    payload_name = payload_layout_for(opcode, data) if cs == "CS_FB" else None
    if payload_name:
        payload_layout = s.layout(payload_name)
        check_layout(payload_layout, data, s.payload_offset)
        decoded["payload_layout"] = payload_name
        decoded["payload_fields"] = unpack_layout(payload_name, bytes(data[s.payload_offset:]))
    decoded["opcode_name"] = s.opcodes[opcode]["name"]
    decoded["chip_select"] = cs
    return decoded


def decode_response(cs, data):
    """Decode a CNF3 (CS_FB) or CNS3 (CS_CMD) response after length and CRC checks."""
    s = spec()
    layout_name = s.response_layout[cs]
    layout = s.layout(layout_name)
    if len(data) != layout.length:
        raise ProtocolError("LENGTH", f"{layout_name} is {layout.length} bytes, got {len(data)}")
    if not crc_ok(layout_name, data):
        raise ProtocolError("CRC", f"{layout_name} CRC mismatch")
    magic = layout.field("magic")
    expected = "CNF3" if cs == "CS_FB" else "CNS3"
    got = bytes(data[magic.offset:magic.offset + magic.size])
    if got != expected.encode():
        raise ProtocolError("MAGIC", f"expected {expected}, got {got!r}")
    return unpack_layout(layout_name, data)


PAGE_LAYOUTS = {("CAP3", 0): "cap3_page0", ("CAP3", 1): "cap3_page1", ("FLT3", 2): "flt3_page2",
                ("IDP3", 3): "idp3_page3"}


def decode_page(data):
    """Decode a READ_PAGE result returned on CS_FB (section 3.14): length, CRC, magic/page pairing."""
    if len(data) != spec().cs_frame_bytes["CS_FB"]:
        raise ProtocolError("LENGTH", f"pages are {spec().cs_frame_bytes['CS_FB']} bytes, got {len(data)}")
    key = (bytes(data[0:4]).decode("ascii", errors="replace"), data[5])
    if key not in PAGE_LAYOUTS:
        raise ProtocolError("MAGIC", f"no page {key!r}")
    name = PAGE_LAYOUTS[key]
    if not crc_ok(name, data):
        raise ProtocolError("CRC", f"{name} CRC mismatch")
    if data[4] != 3:
        raise ProtocolError("ABI", f"expected ABI 3, got {data[4]}")
    decoded = unpack_layout(name, data)
    decoded["layout"] = name
    return decoded


def encode_page(layout_name, values):
    """Build a sealed page (endpoint models and tests; the FPGA produces these on hardware)."""
    magic = layout_name[:4].upper()
    base = {"magic": magic, "abi": 3, "page": int(layout_name[-1])}
    base.update(values)
    return seal(layout_name, pack_layout(layout_name, base))


def encode_response(cs, values):
    """Build a sealed CNF3/CNS3 response (used by simulators and tests)."""
    s = spec()
    layout_name = s.response_layout[cs]
    base = {"magic": "CNF3" if cs == "CS_FB" else "CNS3", "abi": 3}
    base.update(values)
    return seal(layout_name, pack_layout(layout_name, base))


def unwrap_u24(previous_total, raw24):
    """Extend a 24-bit wrapping counter to a running signed total (host rule: modulo 2^24)."""
    if not 0 <= raw24 < (1 << 24):
        raise ProtocolError("FIELD_RANGE", "u24 value out of range")
    delta = (raw24 - (previous_total & 0xFFFFFF)) & 0xFFFFFF
    if delta >= 1 << 23:
        delta -= 1 << 24
    return previous_total + delta


# ---------------------------------------------------------------- IOL1 card link


def encode_iol1(values):
    """Build a sealed 40-byte IOL1 command frame."""
    base = {"sof": 0xA7, "version": 1}
    base.update(values)
    return seal("iol1_command", pack_layout("iol1_command", base))


def validate_iol1(layout_name, data, *, expected_class=None, expected_slot=None):
    """Card-side (iol1_command) or FPGA-side (iol1_response) structural checks before any use."""
    layout = spec().layout(layout_name)
    if len(data) != layout.length:
        raise ProtocolError("LENGTH", f"{layout_name} is {layout.length} bytes, got {len(data)}")
    if not crc_ok(layout_name, data):
        raise ProtocolError("CRC", f"{layout_name} CRC-32C mismatch")
    decoded = unpack_layout(layout_name, data)
    if decoded.get("sof") != 0xA7:
        raise ProtocolError("SOF", f"expected 0xA7, got {decoded.get('sof')}")
    if decoded.get("version") != 1:
        raise ProtocolError("VERSION", f"expected 1, got {decoded.get('version')}")
    if layout_name == "iol1_command":
        if expected_class is not None and decoded["expected_class"] != expected_class:
            raise ProtocolError("CLASS", "frame is addressed to another card class")
        if expected_slot is not None and decoded["expected_slot"] != expected_slot:
            raise ProtocolError("SLOT", "frame is addressed to another slot")
        if decoded["expected_slot"] & 0xF0:
            raise ProtocolError("SLOT", "expected_slot bits 4-7 must be zero")
        if decoded["epoch"] == 0:
            raise ProtocolError("EPOCH", "epoch must be nonzero")
        control = decoded["control"]
        if control & 0xC0:
            raise ProtocolError("CONTROL", "control bits 6-7 must be zero")
        if bool(control & 0x01) != (decoded["sequence"] == 0):
            raise ProtocolError("SEQUENCE", "sequence is 0 exactly in SYNC frames")
    return decoded


def iol1_next_sequence(sequence):
    """IOL1 sequence rule: last+1, wrapping 0xFFFF -> 0x0001 (0 is reserved for SYNC)."""
    return 1 if sequence == 0xFFFF else sequence + 1


# ---------------------------------------------------------------- self-test and vectors


def self_check():
    s = spec()
    results = []

    def ok(name, cond):
        results.append((name, bool(cond)))

    crcs = s.raw["crc"]
    ok("CRC-16/CCITT-FALSE known answer", f"0x{crc16_ccitt_false(b'123456789'):04X}" == crcs["host_frames"]["check_123456789"])
    ok("CRC-32C known answer", f"0x{crc32c(b'123456789'):08X}" == crcs["io_link"]["check_123456789"])
    for name, data in s.vectors.items():
        layout = "iol1_command" if name.startswith("iol1") else s.command_layout[s.cs_for_opcode(data[5])]
        ok(f"vector {name} CRC", crc_ok(layout, data))
        if layout == "iol1_command":
            decoded = validate_iol1(layout, data)
            rebuilt = encode_iol1({k: v for k, v in decoded.items() if k not in ("crc32c",)})
        else:
            decoded = validate_command(s.cs_for_opcode(data[5]), data)
            fields = {k: v for k, v in decoded.items()
                      if k not in ("crc16", "opcode_name", "chip_select", "magic", "abi", "opcode",
                                   "channel_mask", "session", "sequence", "payload_layout", "payload_fields")}
            rebuilt = encode_command(decoded["opcode"], session=decoded["session"], sequence=decoded["sequence"],
                                     channel_mask=decoded["channel_mask"], fields=fields)[1]
        ok(f"vector {name} re-encodes byte-exact", rebuilt == data)
    return results


def golden_vectors():
    """Deterministic vectors for the gateware testbench and the C driver tests."""
    out = {"spec_revision": spec().revision, "source": "gateware/v3/tools/protocol_v3.py", "vectors": []}

    def add(name, cs, data, expect):
        out["vectors"].append({"name": name, "chip_select": cs, "hex": data.hex(), "expect": expect})

    for name, data in spec().vectors.items():
        cs = "IOL1" if name.startswith("iol1") else spec().cs_for_opcode(data[5])
        add("is1_" + name, cs, data, "valid")
    # Eight-motor (M0-M7) and twelve-motor (M0-M11) UPDATE frames.
    r8 = [1000, -2000, 3000, -4000, 5000, -6000, 7000, -8000]
    add("update_8ch", "CS_CMD", encode_update(session=0x11223344, sequence=7, rates=r8, channel_mask=0x00FF,
                                              dout_image=0x0021), "valid")
    r12 = r8 + [9000, -10000, 0x01000000, -0x01000000]
    add("update_12ch_limits", "CS_CMD", encode_update(session=0x11223344, sequence=8, rates=r12, channel_mask=0x0FFF),
        "valid")
    good = bytearray(encode_update(session=1, sequence=1, rates=r8, channel_mask=0x00FF))
    bad_crc = bytearray(good); bad_crc[-1] ^= 0x01
    add("bad_crc", "CS_CMD", bytes(bad_crc), "CRC")
    bad_magic = bytearray(good); bad_magic[0] ^= 0x20
    add("bad_magic", "CS_CMD", seal("cmd_command", bad_magic), "MAGIC")
    bad_abi = bytearray(good); bad_abi[4] = 2
    add("bad_abi", "CS_CMD", seal("cmd_command", bad_abi), "ABI")
    wide = bytearray(good); wide[6] |= 0x10
    add("mask_bit12", "CS_CMD", seal("cmd_command", wide), "MASK_WIDTH")
    unmasked = bytearray(encode_update(session=1, sequence=1, rates=r8, channel_mask=0x00FF))
    unmasked[48:52] = (5).to_bytes(4, "big")
    add("unmasked_rate_m8", "CS_CMD", seal("cmd_command", unmasked), "UNMASKED_RATE")
    zero = bytearray(good); zero[82] = 1
    add("zero_field_set", "CS_CMD", seal("cmd_command", zero), "RESERVED_NONZERO")
    wrong_cs = bytearray(spec().vectors["fb_read_session0"])
    add("fb_read_on_cmd_length", "CS_CMD", bytes(wrong_cs), "LENGTH")
    short = bytes(good[:-1])
    add("short_frame", "CS_CMD", short, "LENGTH")
    iol = bytearray(spec().vectors["iol1_sync_doa"])
    flipped = bytearray(iol); flipped[12] ^= 0x04
    add("iol1_payload_bit_flip", "IOL1", bytes(flipped), "CRC")

    def fb(opcode, payload, session=0, sequence=0, mask=0):
        buf = pack_layout("fb_command", {"magic": "CNC3", "abi": 3, "opcode": spec().opcode_by_name[opcode],
                                         "channel_mask": mask, "session": session, "sequence": sequence})
        buf[16:16 + len(payload)] = payload
        return seal("fb_command", buf)

    def cmd(opcode, session=1, sequence=1, mask=0, **fields):
        values = {"magic": "CNC3", "abi": 3, "opcode": spec().opcode_by_name[opcode], "channel_mask": mask,
                  "session": session, "sequence": sequence}
        values.update(fields)
        return seal("cmd_command", pack_layout("cmd_command", values))

    def conf(**kw):
        return pack_layout("configure_payload_at_16", configure_values(**kw))

    # Motion CONFIGURE: eight channels on the base card, twelve with the MX4 module.
    add("configure_8ch", "CS_FB", encode_configure(required_mask=0x00FF), "valid")
    add("configure_12ch_mx4", "CS_FB", encode_configure(required_mask=0x0FFF, expected_module_class=1,
                                                        alarm_trip_mask=0x0FFF), "valid")
    add("configure_12ch_without_module_class", "CS_FB", fb("CONFIGURE", conf(required_mask=0x0FFF)), "FIELD_RELATION")
    add("configure_format_1", "CS_FB", fb("CONFIGURE", conf(format=1)), "FIELD_RANGE")
    add("configure_timing_99", "CS_FB", fb("CONFIGURE", conf(timing_3=[99, 250, 250, 250])), "FIELD_RANGE")
    add("configure_alarm_outside_required", "CS_FB", fb("CONFIGURE", conf(alarm_trip_mask=0x0100)), "FIELD_RELATION")
    add("configure_encoder_4_without_ex8", "CS_FB", fb("CONFIGURE", conf(required_encoder_mask=0x0010)),
        "FIELD_RELATION")
    add("configure_session_without_sequence", "CS_FB", fb("CONFIGURE", conf(), session=5), "SEQUENCE_RULE")
    add("configure_io_page0", "CS_FB", fb("CONFIGURE_IO", pack_layout("configure_io_page0_at_16", {
        "page": 0, "expected_port_class": [1, 2, 2, 3], "required_port_mask": 0x0F, "motion_critical_port_mask": 0x3F,
        "dout_enable_mask": 0xFFFF, "din_stale_limit_us": 440, "ain_stale_limit_us": 440})), "valid")
    add("configure_io_page0_stale_limit_100", "CS_FB", fb("CONFIGURE_IO", pack_layout("configure_io_page0_at_16", {
        "page": 0, "din_stale_limit_us": 100, "ain_stale_limit_us": 440})), "FIELD_RANGE")
    add("configure_io_page_10", "CS_FB", fb("CONFIGURE_IO", bytes([10])), "FIELD_RANGE")
    # FB_READ, READ_PAGE and MAINT payload rules.
    add("fb_read_ack_7", "CS_FB", encode_fb_read(session=1, event_ack=7), "valid")
    add("fb_read_trailing_byte", "CS_FB", fb("FB_READ", bytes(3) + bytes([1]), session=1), "RESERVED_NONZERO")
    add("fb_read_with_sequence", "CS_FB", fb("FB_READ", b"", session=1, sequence=3), "SEQUENCE_RULE")
    add("read_page_3", "CS_FB", fb("READ_PAGE", bytes([3])), "valid")
    add("read_page_4", "CS_FB", fb("READ_PAGE", bytes([4])), "FIELD_RANGE")
    add("read_page_trailing_byte", "CS_FB", fb("READ_PAGE", bytes([1, 0, 9])), "PAYLOAD_NONZERO")
    maint = encode_iol1({"expected_class": 2, "expected_slot": 1, "epoch": 9, "sequence": 4, "control": 0x28})
    add("maint_port1", "CS_FB", fb("MAINT", bytes([1]) + maint, session=1), "valid")
    plain = encode_iol1({"expected_class": 2, "expected_slot": 1, "epoch": 9, "sequence": 4, "control": 0x08})
    add("maint_without_maint_bit", "CS_FB", fb("MAINT", bytes([1]) + plain, session=1), "EMBEDDED_FRAME")
    # CS_CMD session, sequence, mask and per-opcode payload rules.
    add("nop_with_mask", "CS_CMD", cmd("NOP", session=0, sequence=0, mask=1), "PAYLOAD_NONZERO")
    add("sync_with_sequence", "CS_CMD", cmd("SYNC", session=2, sequence=1), "SEQUENCE_RULE")
    add("sync_session_0", "CS_CMD", cmd("SYNC", session=0, sequence=0), "SESSION_RULE")
    add("update_sequence_0", "CS_CMD", cmd("UPDATE", sequence=0, mask=1), "SEQUENCE_RULE")
    add("arm_8ch", "CS_CMD", cmd("ARM", mask=0x00FF), "valid")
    add("arm_mask_0", "CS_CMD", cmd("ARM"), "MASK_RULE")
    add("disarm_with_mask", "CS_CMD", cmd("DISARM", mask=1), "MASK_RULE")
    add("arm_with_rate", "CS_CMD", cmd("ARM", mask=1, rate_0=5), "RATE_ON_NON_UPDATE")
    add("arm_with_dout", "CS_CMD", cmd("ARM", mask=1, dout_image=1), "FIELD_NOT_ALLOWED")
    add("update_clear_overlaps_image", "CS_CMD", cmd("UPDATE", mask=1, dout_image=3, dout_fault_clear=2),
        "FIELD_RELATION")
    add("update_probe_arm_bit2", "CS_CMD", cmd("UPDATE", mask=1, probe_arm=4), "FIELD_BITS")
    add("selftest_output", "CS_CMD", cmd("SELFTEST", rate_0=0x02000000), "valid")
    add("selftest_3", "CS_CMD", cmd("SELFTEST", rate_0=0x03000000), "FIELD_RANGE")
    add("selftest_rate_low_byte", "CS_CMD", cmd("SELFTEST", rate_0=0x01000001), "RATE_ON_NON_UPDATE")
    add("selftest_trailing", "CS_CMD", cmd("SELFTEST", rate_0=0x01000000, pwm0_duty=1), "PAYLOAD_NONZERO")
    add("io_enable_with_payload", "CS_CMD", cmd("IO_ENABLE", pwm0_duty=1), "PAYLOAD_NONZERO")
    add("clear_continuity_8ch", "CS_CMD", cmd("CLEAR_CONTINUITY", mask=0x00FF), "valid")
    return out


def _check_vector(entry):
    data = bytes.fromhex(entry["hex"])
    try:
        if entry["chip_select"] == "IOL1":
            validate_iol1("iol1_command", data)
        else:
            validate_command(entry["chip_select"], data)
        return "valid"
    except ProtocolError as error:
        return error.code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="self-test against IS-1 vectors (default)")
    parser.add_argument("--vectors", help="write golden vectors JSON to this path")
    args = parser.parse_args(argv)
    results = self_check()
    vectors = golden_vectors()
    for entry in vectors["vectors"]:
        results.append((f"golden {entry['name']} -> {entry['expect']}", _check_vector(entry) == entry["expect"]))
    failed = [name for name, passed in results if not passed]
    for name, passed in results:
        print(("PASS " if passed else "FAIL ") + name)
    if args.vectors:
        with open(args.vectors, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(vectors, indent=1) + "\n")
        print(f"wrote {len(vectors['vectors'])} vectors to {args.vectors}")
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
