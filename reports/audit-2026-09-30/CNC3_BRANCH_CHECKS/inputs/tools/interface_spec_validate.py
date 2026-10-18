#!/usr/bin/env python3
"""Cross-reference validator for interface specification IS-1.

Loads spec/protocol.json, spec/modules.json, spec/terminals.json, spec/allocations.json and
spec/safety.json and checks that the sections agree with each other:

* every file carries spec revision IS-1; every IS-1 markdown file starts with the revision header
  and uses LF line endings; relative links in the markdown resolve;
* every terminal belongs to a declared module (card) and a valid resource (FPGA pin, IOL1 serial
  link, host bus or none); connectors are fully populated and the counts match;
* every function in every allocation sheet maps to existing terminals of the right class, and no
  terminal or resource channel is allocated twice within one configuration;
* per-boundary conductor counts equal the sum of their groups, and the field-side counts equal the
  terminals (nets and differential pairs) routed through that boundary; the FPGA pin budget adds up;
* every advertised connection in the protocol table has an update rate, a maximum data age, a fault
  response and HAL pins that resolve in the HAL pin registry; every CNC1 field and HAL pin named by
  a terminal or by the safety status table resolves in section 01;
* frame layouts are contiguous with no overlaps, and the CRC is the last field and covers every
  preceding byte;
* the per-cycle schedule recomputes to the stated completion, stays inside the 700 us target and
  the servo period with the stated margins, and the separate data-age bounds hold;
* every motor channel 0-11 has STEP, DIR, both enable terminals (EN_NO, EN_COM, EN_NC) and an alarm;
  the I/O inventory (24 DI, 16 DO, 12 encoders, probes, frequency, PWM, process enables, analog,
  buses, MPG, safety interface) is complete; the watchdog path stays inside 20 ms;
* the rendered/generated documents are current (tools/interface_spec/*).

This is a specification check (arithmetic and source consistency). It does not test RTL, firmware,
schematics or hardware. Usage:

    python tools/interface_spec_validate.py [--check] [--root DIR] [--no-render] [--json]

--check is the default and only mode: the validator never writes into the repository (rendered
documents are produced in a temporary directory and compared). Exit status 0 = no problems;
1 = problems found (listed on stdout).
"""
import argparse
import collections
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

REVISION = "IS-1"
HEADER = "Interface specification revision: IS-1"
SPEC_FILES = ["protocol", "modules", "terminals", "allocations", "safety", "service"]
DOCS = ["docs/interface-spec/01-protocol-and-schedule.md", "docs/interface-spec/02-modules-and-boundaries.md",
        "docs/interface-spec/03-terminals-and-allocations.md", "docs/interface-spec/04-safety-power-timing.md",
        "docs/interface-spec/05-service-contract.md", "docs/CONTROLLER_INTERFACE_SPEC.md"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRAME_LENGTHS = {
    "fb_command": 176, "fb_response_CNF3": 176, "cmd_command": 96, "cmd_response_CNS3": 96,
    "fb_read_payload_at_16": 158, "configure_payload_at_16": 158, "configure_io_page0_at_16": 158,
    "configure_io_page1_at_16": 158, "configure_io_card_pages_at_16": 158,
    "cap3_page0": 176, "cap3_page1": 176, "flt3_page2": 176, "idp3_page3": 176,
    "iol1_command": 40, "iol1_response": 40,
}
CRC_FRAMES = {"fb_command": 2, "fb_response_CNF3": 2, "cmd_command": 2, "cmd_response_CNS3": 2, "cap3_page0": 2,
              "cap3_page1": 2, "flt3_page2": 2, "idp3_page3": 2, "iol1_command": 4, "iol1_response": 4}
MOTOR_NETS = {"STEP+": "_STEP_P", "STEP-": "_STEP_N", "DIR+": "_DIR_P", "DIR-": "_DIR_N",
              "EN_NO": "_EN_NO", "EN_COM": "_EN_COM", "EN_NC": "_EN_NC", "ALARM": "_ALM_IN"}
CLASS_CONNECTOR = {"motor": r"XM\d+", "encoder": r"XE\d+", "di": r"XDI\d", "do": r"XDO\d", "probe": r"XPR",
                   "freq": r"XF", "pwm": r"XPW", "proc_en": r"XPC\d", "ao": r"XAO", "ai": r"XAI", "rs485": r"XB1",
                   "can": r"XB2", "mpg": r"XH1", "pendant_sel": r"XH2"}
CLASS_CONNECTOR_DEFAULT = r"XS1"


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


class Report:
    def __init__(self):
        self.problems = []
        self.passed = 0

    def ok(self, cond, msg):
        if cond:
            self.passed += 1
        else:
            self.problems.append(msg)
        return cond


def load(root):
    specs = {}
    for name in SPEC_FILES:
        with open(os.path.join(root, "spec", name + ".json"), encoding="utf-8") as fh:
            specs[name] = json.load(fh)
    return specs


# ------------------------------------------------------------------ revision and documents
def check_revision(r, root, specs, docs=True):
    for name, s in specs.items():
        r.ok(s.get("spec_revision") == REVISION, f"spec/{name}.json: top-level spec_revision is not {REVISION}")
        raw = read_bytes(os.path.join(root, "spec", name + ".json"))
        r.ok(b"\r" not in raw, f"spec/{name}.json: contains CR characters (LF line endings required)")
    if not docs:
        return
    for rel in DOCS:
        path = os.path.join(root, rel)
        if not r.ok(os.path.exists(path), f"{rel}: missing"):
            continue
        raw = read_bytes(path)
        r.ok(b"\r" not in raw, f"{rel}: contains CR characters")
        text = raw.decode("utf-8")
        r.ok(text.splitlines()[0].startswith(HEADER), f"{rel}: first line is not the '{HEADER}' header")
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
            if re.match(r"^[a-z]+://", target) or target.startswith("mailto:"):
                continue
            tpath = os.path.normpath(os.path.join(os.path.dirname(path), target))
            r.ok(os.path.exists(tpath), f"{rel}: relative link '{target}' does not resolve")


# ------------------------------------------------------------------ terminals
def check_terminals(r, specs):
    t, m = specs["terminals"], specs["modules"]
    declared = set(m["boundaries"]) | {"BASE"}
    r.ok("base" in m, "modules.json: the fixed wiring base is not declared")
    ids = [x["id"] for x in t["terminals"]]
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    r.ok(not dup, f"terminals.json: duplicate terminal ids {dup[:5]}")
    conns = {c["id"]: c for c in t["connectors"]}
    by_conn = collections.defaultdict(list)
    for x in t["terminals"]:
        by_conn[x["connector"]].append(x["position"])
        r.ok(x["connector"] in conns, f"terminal {x['id']}: connector {x['connector']} not declared")
        r.ok(x["id"] == f"{x['connector']}.{x['position']}", f"terminal {x['id']}: id does not match connector.position")
        r.ok(x["owner_card"] in declared, f"terminal {x['id']}: owner card {x['owner_card']} is not a declared module")
        r.ok(x["owner_card"] in t["cards"], f"terminal {x['id']}: owner card {x['owner_card']} missing from terminals.cards")
        res = x.get("resource") or {}
        kind = res.get("kind")
        if not r.ok(kind in ("fpga_pin", "serial_io", "host", "none"), f"terminal {x['id']}: resource kind {kind!r} invalid"):
            continue
        if kind == "fpga_pin":
            r.ok(bool(res.get("signal")), f"terminal {x['id']}: FPGA resource without a signal name")
            r.ok(res.get("signal") in t["fpga_demand"]["direct_field_signal_names"],
                 f"terminal {x['id']}: FPGA signal {res.get('signal')} not in fpga_demand.direct_field_signal_names")
        elif kind == "serial_io":
            card = str(res.get("link", "")).split(".")[0]
            r.ok(card in declared, f"terminal {x['id']}: serial link {res.get('link')} names no declared card")
            r.ok("bit" in res, f"terminal {x['id']}: serial resource without a bit/channel")
        elif kind == "host":
            r.ok(bool(res.get("resource")), f"terminal {x['id']}: host resource not described")
    for cid, c in conns.items():
        r.ok(sorted(by_conn.get(cid, [])) == list(range(1, c["positions"] + 1)),
             f"connector {cid}: positions are not exactly 1..{c['positions']}")
        r.ok(c["owner_card"] in declared, f"connector {cid}: owner card {c['owner_card']} not declared")
    xtb = {c["id"] for c in t["connectors"] if "XTB" in c["location"]}
    n_all = len(t["terminals"])
    n_xtb = sum(1 for x in t["terminals"] if x["connector"] in xtb)
    cnt = t["counts"]
    r.ok(cnt["field_connectors"] == len(conns), f"terminals.counts.field_connectors {cnt['field_connectors']} != {len(conns)}")
    r.ok(cnt["field_terminals"] == n_all, f"terminals.counts.field_terminals {cnt['field_terminals']} != {n_all}")
    r.ok(cnt["expansion_terminals"] == n_xtb, f"terminals.counts.expansion_terminals {cnt['expansion_terminals']} != {n_xtb}")
    r.ok(cnt["standard_unit_terminals"] == n_all - n_xtb, f"terminals.counts.standard_unit_terminals != {n_all - n_xtb}")
    d = t["fpga_demand"]
    fp = {x["resource"]["signal"] for x in t["terminals"] if x["resource"]["kind"] == "fpga_pin"}
    r.ok(set(d["direct_field_signal_names"]) == fp, "fpga_demand.direct_field_signal_names differs from the FPGA signals used by terminals")
    r.ok(d["direct_field_signals"] == len(d["direct_field_signal_names"]), "fpga_demand.direct_field_signals miscounted")
    r.ok(d["serial_link_pin_total"] == sum(d["serial_link_pins"].values()), "fpga_demand.serial_link_pin_total miscounted")
    r.ok(d["total_field_driven_fpga_pins"] == d["direct_field_signals"] + d["serial_link_pin_total"],
         "fpga_demand.total_field_driven_fpga_pins != direct + serial")


def check_channels(r, specs):
    """Every motor channel has STEP, DIR, both enable terminals and an alarm; full I/O inventory present."""
    t = specs["terminals"]
    nets = {}
    for x in t["terminals"]:
        nets[x["net"]] = x
    for n in range(12):
        for label, suffix in MOTOR_NETS.items():
            x = nets.get(f"M{n}{suffix}")
            if not r.ok(x is not None, f"motor channel M{n}: {label} terminal missing"):
                continue
            r.ok(x["connector"] == f"XM{n}", f"motor channel M{n}: {label} not on connector XM{n}")
        for label, sig in (("STEP", f"STEP{n}_FPGA"), ("DIR", f"DIR{n}_FPGA"), ("EN_N", f"EN{n}_N_FPGA"), ("ALM", f"ALM{n}_FPGA")):
            r.ok(sig in t["fpga_demand"]["direct_field_signal_names"], f"motor channel M{n}: FPGA signal {sig} for {label} missing")
        for suffix in ("_EN_NO", "_EN_NC"):
            x = nets.get(f"M{n}{suffix}")
            if x:
                r.ok(x["resource"].get("signal") == f"EN{n}_N_FPGA", f"motor channel M{n}: {suffix[1:]} is not driven by EN{n}_N_FPGA")
                r.ok(bool(x.get("hal_pin")) and f"cnc1.{n}.enable" in x["hal_pin"], f"motor channel M{n}: {suffix[1:]} has no per-channel enable HAL pin")
        x = nets.get(f"M{n}_ALM_IN")
        if x:
            r.ok(bool(x.get("hal_pin")) and f"cnc1.{n}.alarm" in x["hal_pin"], f"motor channel M{n}: alarm has no per-channel HAL pin")
    s = specs["safety"]["enable_interface"]["parts"]
    r.ok("form_a" in s and "form_b" in s, "safety.json: enable interface lacks a normally-open and a normally-closed switch")
    for k in range(12):
        for sfx in ("_A_P", "_A_N", "_B_P", "_B_N", "_Z_P", "_Z_N", "_5V"):
            r.ok(f"ENC{k}{sfx}" in nets, f"encoder ENC{k}: terminal {sfx[1:]} missing")
    for d in range(24):
        r.ok(f"DI{d:02d}" in nets, f"general input DI{d} missing")
    for o in range(16):
        r.ok(f"DO{o:02d}" in nets, f"general output DO{o} missing")
    for net in ("PRB0_IN", "PRB1_IN", "FREQ0_P", "FREQ1_P", "PWM0", "PWM1", "PEN0_1", "PEN1_1", "AO0", "AO1", "AI0_P", "AI1_P",
                "AI2_P", "AI3_P", "RS485_A", "RS485_B", "CAN_H", "CAN_L", "MPG_A_P", "MPG_B_P", "EXT_PERMIT_IN", "PROCESS_PERMIT_IN",
                "SAFETY_STATUS_IN", "RESET_ARM_IN", "CONTACTOR_FB_IN", "STO_FB_IN", "PERMIT_OUT_1"):
        r.ok(net in nets, f"I/O inventory: terminal net {net} missing")


# ------------------------------------------------------------------ allocations
TERM_REF = re.compile(r"(X[A-Z]+\d*)\.(\d+)(?:-(\d+))?")


def parse_terminal_ref(text):
    out = []
    for conn, a, b in TERM_REF.findall(text):
        a = int(a)
        b = int(b) if b else a
        out += [f"{conn}.{p}" for p in range(a, b + 1)]
    return out


def check_allocations(r, specs):
    t = specs["terminals"]
    tids = {x["id"] for x in t["terminals"]}
    xtb = {c["id"] for c in t["connectors"] if "XTB" in c["location"]}
    has_twelve_by_twelve = False
    for cfg in specs["allocations"]["configurations"]:
        cid = cfg["id"]
        seen_t, seen_c = {}, {}
        used = collections.defaultdict(set)
        for a in cfg["assignments"]:
            refs = parse_terminal_ref(str(a["terminal"]))
            if not r.ok(bool(refs), f"allocation {cid}: '{a['function']}' has no parsable terminal"):
                continue
            pattern = CLASS_CONNECTOR.get(a["resource_class"], CLASS_CONNECTOR_DEFAULT)
            for ref in refs:
                r.ok(ref in tids, f"allocation {cid}: '{a['function']}' maps to missing terminal {ref}")
                r.ok(re.fullmatch(pattern, ref.split(".")[0]) is not None,
                     f"allocation {cid}: '{a['function']}' ({a['resource_class']}) uses terminal {ref} of the wrong connector class")
                if ref in seen_t:
                    r.ok(False, f"allocation {cid}: terminal {ref} double-allocated ('{seen_t[ref]}' and '{a['function']}')")
                seen_t[ref] = a["function"]
                conn = ref.split(".")[0]
                if conn in xtb and conn.startswith("XM"):
                    r.ok(cfg["counts"]["motor"]["capacity"] == 12, f"allocation {cid}: expansion terminal {ref} used without MX4 (motor capacity {cfg['counts']['motor']['capacity']})")
                if conn in xtb and conn.startswith("XE"):
                    r.ok(cfg["counts"]["encoder"]["capacity"] == 12, f"allocation {cid}: expansion terminal {ref} used without EX8 (encoder capacity {cfg['counts']['encoder']['capacity']})")
            key = (a["resource_class"], a["channel"])
            if key in seen_c:
                r.ok(False, f"allocation {cid}: resource {key} double-allocated ('{seen_c[key]}' and '{a['function']}')")
            seen_c[key] = a["function"]
            used[a["resource_class"]].add(a["channel"])
        for cls, c in cfg["counts"].items():
            r.ok(c["used"] == len(used.get(cls, ())), f"allocation {cid}: counts.{cls}.used {c['used']} != {len(used.get(cls, ()))}")
            r.ok(c["used"] + c["spare"] == c["capacity"], f"allocation {cid}: counts.{cls} used + spare != capacity")
            r.ok(c["used"] <= c["capacity"], f"allocation {cid}: {cls} over capacity")
        if cfg["counts"]["motor"]["used"] == 12 and cfg["counts"]["encoder"]["used"] == 12:
            has_twelve_by_twelve = True
    r.ok(has_twelve_by_twelve, "allocations.json: no sheet proves twelve motors and twelve encoders fitted at the same time")


# ------------------------------------------------------------------ modules and boundaries
def field_counts(terminals, cards, connectors=None):
    nets, seen = [], set()
    for x in terminals:
        if x["owner_card"] not in cards or (connectors is not None and x["connector"] not in connectors):
            continue
        if x["net"] not in seen:
            seen.add(x["net"])
            nets.append(x["net"])
    s, used, pairs = set(nets), set(), 0
    for n in nets:
        for a, b, pre in (("_P", "_N", ""), ("_H", "_L", "CAN"), ("_A", "_B", "RS485")):
            if n.endswith(a) and n.startswith(pre):
                mate = n[: -len(a)] + b
                if mate in s and n not in used:
                    pairs += 1
                    used.update({n, mate})
    return pairs, len(nets) - 2 * pairs


def check_modules(r, specs):
    m, t = specs["modules"], specs["terminals"]
    bnd = m["boundaries"]
    for mod in m["modules"]:
        if mod["id"] in bnd:
            r.ok(mod["boundary"] == bnd[mod["id"]], f"modules.json: module {mod['id']} boundary differs from boundaries.{mod['id']}")
    kinds = {"se": "single_ended_signals", "dp": "differential_pairs", "ret": "signal_returns", "pwr": "power_contacts",
             "fld": "field_conductors_other", "pres": "presence_contacts", "id": "identity_bus_contacts"}
    for card, recs in bnd.items():
        for i, rec in enumerate(recs):
            where = f"boundary {card}[{i}] ({rec['connector']})"
            total = sum(g["conductors"] for g in rec["groups"])
            r.ok(rec["contacts_used"] == total, f"{where}: contacts_used {rec['contacts_used']} != sum of groups {total}")
            r.ok(rec["contacts_used"] <= rec["contacts_total"], f"{where}: {rec['contacts_used']} conductors exceed {rec['contacts_total']} contacts")
            r.ok(rec["contacts_spare"] == rec["contacts_total"] - rec["contacts_used"], f"{where}: spare count wrong")
            for g in rec["groups"]:
                r.ok(g["conductors"] == g["count"] * (2 if g["kind"] == "dp" else 1), f"{where}: group '{g['group']}' conductor count wrong")
            for k, field in kinds.items():
                r.ok(rec[field] == sum(g["count"] for g in rec["groups"] if g["kind"] == k), f"{where}: {field} does not match its groups")
    # field side: conductors routed through each field boundary equal the terminals it carries
    xtb = {c["id"] for c in t["connectors"] if "XTB" in c["location"]}
    field_cards = {"MIA": ({"MIA"}, None), "MX4": ({"MX4"}, None), "EIA": ({"EIA"}, None), "EX8": ({"EX8"}, None),
                   "DIC": ({"DIC"}, None), "DOA": ({"DOA"}, None), "DOB": ({"DOB"}, None), "ACC": ({"ACC"}, None),
                   "XTB": ({"MX4", "EX8"}, xtb)}
    for card, (owners, conns) in field_cards.items():
        if not r.ok(card in bnd, f"boundary {card} missing"):
            continue
        pairs, singles = field_counts(t["terminals"], owners, conns)
        recs = [x for x in bnd[card] if any(g["kind"] in ("fld", "dp") and ("terminals" in g["group"] or card == "XTB") for g in x["groups"])]
        dp = sum(g["count"] for x in recs for g in x["groups"] if g["kind"] == "dp")
        fld = sum(g["count"] for x in recs for g in x["groups"] if g["kind"] == "fld")
        r.ok(dp == pairs, f"boundary {card}: {dp} field differential pairs routed but terminals.json has {pairs}")
        r.ok(fld == singles, f"boundary {card}: {fld} other field conductors routed but terminals.json has {singles}")
    psm_service = sum(1 for x in t["terminals"] if x["owner_card"] == "PSM" and x["function_class"] == "service_input")
    psm_fld = sum(g["count"] for x in bnd.get("PSM", []) for g in x["groups"] if g["kind"] == "fld")
    r.ok(psm_fld == psm_service, f"boundary PSM: {psm_fld} field conductors routed but terminals.json has {psm_service} service inputs")
    # logic side against the protocol: IOL1 ports and host chip selects
    ports = specs["protocol"]["io_link"]["ports"]
    mc_groups = {g["group"]: g for x in bnd["MC"] for g in x["groups"]}
    iol = [g for name, g in mc_groups.items() if name.startswith("IOL1 links")]
    r.ok(bool(iol) and iol[0]["count"] == 4 * len(ports), f"boundary MC: IOL1 conductors != 4 wires x {len(ports)} ports")
    host = [g for name, g in mc_groups.items() if name.startswith("host SPI")]
    cs = specs["protocol"]["host_link"]["chip_selects"]
    r.ok(bool(host) and host[0]["count"] == 3 + len(cs), f"boundary MC: host SPI conductors != SCLK/MOSI/MISO + {len(cs)} chip selects")
    r.ok(bool(host) and all(k in host[0]["group"] for k in cs), "boundary MC: host SPI group does not name every chip select")
    # FPGA pin budget
    fb = m["fpga_pin_budget"]
    r.ok(fb["total"] == sum(g["pins"] for g in fb["groups"]), "modules.fpga_pin_budget: total != sum of groups")
    r.ok(fb["field_driven_section_03"] == t["fpga_demand"]["total_field_driven_fpga_pins"],
         "modules.fpga_pin_budget: field-driven pins differ from terminals.fpga_demand")
    r.ok(fb["total"] <= fb["t20f256_usable"], "modules.fpga_pin_budget: total exceeds usable T20F256 pins")
    r.ok(fb["spare"] == fb["t20f256_usable"] - fb["total"], "modules.fpga_pin_budget: spare miscounted")
    grp = {g["group"]: g["pins"] for g in fb["groups"]}
    motor = [v for k, v in grp.items() if k.startswith("STEP/DIR/EN_N/ALM")]
    enc = [v for k, v in grp.items() if k.startswith("ENC0-11")]
    r.ok(motor == [48], "modules.fpga_pin_budget: motor pins != 4 x 12 channels (both expansions reserved)")
    r.ok(enc == [36], "modules.fpga_pin_budget: encoder pins != 3 x 12 encoders (both expansions reserved)")


# ------------------------------------------------------------------ protocol
def check_frames(r, p):
    frames = p["frames"]
    for name, length in FRAME_LENGTHS.items():
        if not r.ok(name in frames, f"protocol: frame {name} missing"):
            continue
        end = 0
        for f in sorted(frames[name], key=lambda f: f["offset"]):
            r.ok(f["offset"] >= end, f"protocol: frame {name} field {f['name']} at {f['offset']} overlaps the previous field (ends at {end})")
            r.ok(f["offset"] <= end, f"protocol: frame {name} has a gap before {f['name']} ({end}..{f['offset']})")
            r.ok(f["size"] > 0, f"protocol: frame {name} field {f['name']} has no size")
            end = max(end, f["offset"] + f["size"])
        r.ok(end == length, f"protocol: frame {name} covers {end} bytes, expected {length}")
        names = [f["name"] for f in frames[name]]
        r.ok(len(names) == len(set(names)), f"protocol: frame {name} has duplicate field names")
        if name in CRC_FRAMES:
            w = CRC_FRAMES[name]
            last = max(frames[name], key=lambda f: f["offset"])
            ok = last["name"].startswith("crc") and last["size"] == w and last["offset"] == length - w
            r.ok(ok, f"protocol: frame {name} does not end in a {w}-byte CRC covering bytes 0-{length - w - 1}")
            crcs = [f for f in frames[name] if f["name"].startswith("crc")]
            r.ok(len(crcs) == 1, f"protocol: frame {name} has {len(crcs)} CRC fields")
    host_cov = p["crc"]["host_frames"]["coverage"]
    r.ok("0..n-3" in host_cov, "protocol: host-frame CRC coverage is not every byte before the CRC")
    r.ok("bytes 0-35" in p["crc"]["io_link"]["coverage"], "protocol: IOL1 CRC coverage is not bytes 0-35")
    fb = [f for f in frames.get("fb_command", []) if f["name"] == "payload"]
    r.ok(bool(fb) and fb[0]["offset"] == 16 and fb[0]["size"] == 158, "protocol: CS_FB payload is not bytes 16-173")


def logical_names(p):
    names = set()
    for fr in p["frames"].values():
        for f in fr:
            if f.get("logical"):
                names.add(norm_logical(f["logical"]))
    return names


def norm_logical(s):
    return re.sub(r"\[[^\]]*\]", "[i]", s.strip())


def hal_registry(p):
    idx = p["hal_index"]
    concrete, patterns = set(), set()
    for h in p["hal_pins"]:
        name = h["name"]
        patterns.add(norm_hal(name))
        keys = re.findall(r"\{(\w+)\}", name)
        vals = [[str(v) for v in (range(idx[k][0], idx[k][1] + 1) if isinstance(idx[k][0], int) else idx[k])] for k in keys]
        combos = [[]]
        for vs in vals:
            combos = [c + [v] for c in combos for v in vs]
        for c in combos:
            n = name
            for k, v in zip(keys, c):
                n = n.replace("{" + k + "}", v, 1)
            concrete.add(n)
    return concrete, patterns


def norm_hal(n):
    n = re.sub(r"\{\w+\}|<[^>]+>", "#", n)
    n = re.sub(r"(?<=\.)(\d+|[A-Z])(?=[.\-]|$)", "#", n)
    n = re.sub(r"(?<=-)(\d+|[A-Z])(?=[.\-]|$)", "#", n)
    return n


def hal_resolves(name, concrete, patterns):
    if name in concrete:
        return True
    placeholder = re.search(r"\{\w+\}|<[^>]+>|(?<=\.)[A-Z](?=[.\-]|$)", name)
    return bool(placeholder) and norm_hal(name) in patterns


def split_hal(s):
    out = []
    for part in str(s).split(" / "):
        part = re.sub(r"\s*\(.*$", "", part.strip())
        if part:
            out.append(part)
    return out


def check_protocol(r, specs):
    p = specs["protocol"]
    check_frames(r, p)
    concrete, patterns = hal_registry(p)
    names = [h["name"] for h in p["hal_pins"]]
    r.ok(len(names) == len(set(names)), "protocol: duplicate names in hal_pins")
    for h in p["hal_pins"]:
        r.ok(all(h.get(k) not in (None, "") for k in ("type", "dir", "source")), f"protocol: hal_pins entry {h['name']} incomplete")
    for c in p["connections"]:
        cid = c.get("id", "?")
        for k, what in (("rate", "update rate"), ("age", "maximum data age"), ("fault", "fault response"), ("hal", "HAL mapping")):
            r.ok(bool(str(c.get(k, "")).strip()), f"connection '{cid}': no {what}")
        pins = c.get("hal_pins")
        if pins == [] and c.get("hal_note"):
            continue
        if not r.ok(bool(pins), f"connection '{cid}': no structured hal_pins"):
            continue
        for n in pins:
            r.ok(hal_resolves(n, concrete, patterns), f"connection '{cid}': HAL pin {n} not in the hal_pins registry")
    for d in p["diagnostics"]:
        for k in ("source", "transport", "rate", "age_bound", "validity", "hal", "response"):
            r.ok(bool(str(d.get(k, "")).strip()), f"diagnostic '{d.get('signal')}': no {k}")
    # schedule (T3)
    s = p["schedule"]
    a = s["allocations_us_REQ"]
    g = s["guard_us_per_transaction"]
    fb_bits, cmd_bits = FRAME_LENGTHS["fb_command"] * 8, FRAME_LENGTHS["cmd_command"] * 8
    r.ok(set(s["pre_commit_phases"]) - {"fb_wire", "cmd_wire"} | set(s["post_commit_phases"]) == set(a),
         "schedule: pre/post-commit phase lists do not cover every host allocation exactly")
    pre = sum(a[k] for k in s["pre_commit_phases"] if k in a)
    r.ok(abs(pre - s["allocation_total_to_commit_us"]) < 1e-6, "schedule: allocation_total_to_commit_us != sum of pre-commit allocations")
    for key, hz in (("5.00_MHz", 5e6), ("6.25_MHz", 6.25e6)):
        c = s["cases"][key]
        fbx = fb_bits / hz * 1e6 + g
        cmx = cmd_bits / hz * 1e6 + g
        comp = pre + fbx + cmx
        end = comp + sum(a[k] for k in s["post_commit_phases"])
        r.ok(abs(c["completion_C_us"] - comp) < 0.006, f"schedule {key}: stated completion {c['completion_C_us']} != computed {comp:.2f}")
        r.ok(abs(c["thread_end_us"] - end) < 0.006, f"schedule {key}: stated thread end {c['thread_end_us']} != computed {end:.2f}")
        r.ok(comp <= s["completion_target_us"], f"schedule {key}: completion {comp:.2f} us exceeds the {s['completion_target_us']} us target")
        r.ok(end < s["servo_period_us"], f"schedule {key}: thread end {end:.2f} us not inside the {s['servo_period_us']} us servo period")
        r.ok(abs(c["margin_to_700_us"] - (s["completion_target_us"] - comp)) < 0.006, f"schedule {key}: stated 700 us margin wrong")
        r.ok(abs(c["margin_to_1000_us"] - (s["servo_period_us"] - comp)) < 0.006, f"schedule {key}: stated period margin wrong")
        age = fbx + a["fb_ioctl_post"] + a["decode_publish"]
        r.ok(abs(c["input_age_counters_us"] - age) < 0.006, f"schedule {key}: stated counter input age {c['input_age_counters_us']} != computed {age:.2f}")
        r.ok(c["input_age_counters_us"] <= s["separate_bounds_us_REQ"]["counter_input_age"],
             f"schedule {key}: counter input age {c['input_age_counters_us']} exceeds its bound")
        r.ok(c["command_to_commit_us"] <= s["separate_bounds_us_REQ"]["motion_command_to_commit"],
             f"schedule {key}: command-to-commit {c['command_to_commit_us']} exceeds its bound")
    kd = s["kept_distinct_ms"]
    r.ok(kd["completion_target"] < kd["servo_deadline"] < kd["fpga_command_watchdog"] < kd["fault_to_inhibit"],
         "schedule: completion target, servo deadline, watchdog and fault-to-inhibit are not kept in increasing, distinct order")


def check_names(r, specs):
    """CNC1 fields and HAL pins named by terminals and by the safety table resolve in section 01."""
    p, t = specs["protocol"], specs["terminals"]
    concrete, patterns = hal_registry(p)
    logical = logical_names(p)
    events = {e["name"] for e in p["events"]}
    tel = {norm_logical(m["logical"]) for m in p["telemetry_map"]}
    host = {norm_logical(h["logical"]) for h in p["host_sources"]}
    for x in t["terminals"]:
        cf = x.get("cnc1_field")
        if cf:
            for tok in cf.split(" / "):
                tok = re.sub(r"\s*\(.*$", "", tok.strip())
                base = norm_logical(re.sub(r"\s+bit\s+\d+$", "", tok))
                if base.startswith("EVT.type "):
                    r.ok(base.split(" ", 1)[1] in events, f"terminal {x['id']}: event {base} not defined in protocol events")
                elif base.startswith(("CMD.", "STS.", "EVT.")):
                    r.ok(base in logical, f"terminal {x['id']}: CNC1 field {base} not defined in any protocol frame")
                elif base.startswith("TEL."):
                    r.ok(base in tel, f"terminal {x['id']}: telemetry name {base} not in protocol telemetry_map")
                elif base.startswith("HOST."):
                    r.ok(base in host, f"terminal {x['id']}: host-side name {base} not in protocol host_sources")
                else:
                    r.ok(False, f"terminal {x['id']}: CNC1 field token '{tok}' has no known prefix")
        hp = x.get("hal_pin")
        if hp:
            for n in split_hal(hp):
                r.ok(hal_resolves(n, concrete, patterns), f"terminal {x['id']}: HAL pin {n} not in the hal_pins registry")
        companion = isinstance(x.get("diagnostics"), dict) and "see" in x["diagnostics"]
        if x.get("update", {}).get("class") == "servo" and not companion and x["function_class"] not in ("return", "spacing", "bond", "enable_switch", "permission_output"):
            r.ok(bool(cf) and bool(hp), f"terminal {x['id']}: servo-class terminal without CNC1 field and HAL pin")
    for f in specs["safety"]["safety_status_fields"]:
        for n in f.get("hal", []):
            r.ok(hal_resolves(n, concrete, patterns), f"safety.json status field {f['field']}: HAL pin {n} not in the registry")


# ------------------------------------------------------------------ safety timing
def expand_terms(expr, eqs, depth=3):
    """Set of term names reachable from expr through the permission equations (raw_inhibit_n -> base_ok, WD_M_OK, ...)."""
    seen, frontier = set(), set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr))
    for _ in range(depth + 1):
        seen |= frontier
        nxt = set()
        for t in frontier:
            if t in eqs:
                nxt |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", eqs[t]))
        frontier = nxt - seen
    return seen


def check_safety(r, specs):
    s = specs["safety"]
    w = s["watchdogs"]
    csb = w["clock_stall_budget"]
    # recompute tWD from the formula, capacitor tolerance, TI factors and the CWD leakage allowance
    b = csb.get("wd_max_basis", {})
    if r.ok(all(k in b for k in ("capacitor_nf", "cap_tolerance", "ti_factor_max", "charge_current_na", "leakage_na")),
            "safety: clock_stall_budget.wd_max_basis incomplete (capacitor, tolerance, TI factor, charge current, leakage)"):
        wd = lambda c: 3.23 * c + 0.381
        i, lk = b["charge_current_na"], b["leakage_na"]
        wmax = 1.095 * wd(b["capacitor_nf"] * (1 + b["cap_tolerance"])) * i / (i - lk)
        wmin = 0.905 * wd(b["capacitor_nf"] * (1 - b["cap_tolerance"])) * i / (i + lk)
        r.ok(b["ti_factor_max"] == 1.095, "safety: TI timing factor is not the recorded 1.095")
        r.ok(abs(csb["wd_max_ms"] - wmax) < 0.006, f"safety: stated tWD(max) {csb['wd_max_ms']} ms != recomputed {wmax:.2f} ms (formula, tolerance, leakage)")
        tc = {t["id"]: t for t in s["timing_classes"]}
        ew = tc.get("external_watchdog", {})
        r.ok(abs(ew.get("max_ms", -1) - wmax) < 0.006 and abs(ew.get("min_ms", -1) - wmin) < 0.006,
             f"safety: timing class external_watchdog {ew.get('min_ms')}/{ew.get('max_ms')} ms != recomputed {wmin:.2f}/{wmax:.2f} ms")
        st = w["self_test"]["pass_window_ms"]
        r.ok(abs(st[0] - (wmin - 0.2)) < 0.006 and abs(st[1] - (wmax + 0.35)) < 0.006,
             f"safety: self-test window {st} != [tWD(min) - 0.2, tWD(max) + 0.35] = [{wmin - 0.2:.2f}, {wmax + 0.35:.2f}]")
    stages = csb["stages_ms"]
    down = sum(v for k, v in stages.items() if not k.startswith("form_")) + max(v for k, v in stages.items() if k.startswith("form_"))
    r.ok(abs(csb["downstream_total_ms"] - down) < 0.006, f"safety: downstream_total_ms {csb['downstream_total_ms']} != recomputed {down:.3f} from stages_ms")
    r.ok(csb["motion_total_ms"] <= 20.0, f"safety: clock-stall fault-to-inhibit {csb['motion_total_ms']} ms exceeds 20 ms")
    r.ok(abs(csb["motion_total_ms"] - (csb["wd_max_ms"] + csb["downstream_total_ms"])) < 0.011, "safety: clock-stall budget does not add up")
    r.ok(abs(csb["output_path_total_ms"] - (csb["wd_max_ms"] + csb.get("output_driver_ms", float("nan")))) < 0.011,
         "safety: output_path_total_ms != wd_max_ms + output_driver_ms")
    r.ok(csb["output_path_total_ms"] <= 20.0, "safety: output-path fault-to-inhibit exceeds 20 ms")
    for sc in s["fault_timing"]["scenarios"]:
        v = sc.get("t_inhibit_max_ms")
        if not r.ok(isinstance(v, (int, float)) and not isinstance(v, bool),
                    f"safety: scenario {sc['id']} has no numeric t_inhibit_max_ms ({v!r}); a 'blocked:' marker fails the freeze"):
            continue
        r.ok(v <= 20.0, f"safety: scenario {sc['id']} t_inhibit {v} ms exceeds 20 ms")
        if "detect_ms" in sc and sc["id"] not in ("output_short", "output_permit_glitch", "startup"):
            r.ok(abs(v - (sc["detect_ms"] + csb["downstream_total_ms"])) < 0.011, f"safety: scenario {sc['id']} t_inhibit != detect_ms + downstream_total_ms")
    perm = s["permission"]
    fan = {f["net"]: f["receivers"] for f in perm["fanout"]}
    r.ok(any("PERMIT_OUT" in x for x in fan.get("TX_PERMIT", [])), "safety: PERMIT_OUT receiver missing from the TX_PERMIT fan-out")
    r.ok(any("PERMIT_OUT" in x and "PERMIT_OUT_REQ" in x for x in fan.get("TX_PERMIT", [])), "safety: PERMIT_OUT receiver is not gated by PERMIT_OUT_REQ (it would close during the watchdog self-test)")
    r.ok(not any("base Ioff" in x for x in fan.get("TX_PERMIT", [])), "safety: TX_PERMIT fan-out still routes through a base Ioff buffer (section 02 D02-5)")
    # every arm latch has an asynchronous clear containing its own watchdog and base terms
    eqs = {e.split("=", 1)[0].strip(): e.split("=", 1)[1] for e in perm["equations"] if "=" in e}
    latches = perm.get("arm_latches", [])
    r.ok({l["id"] for l in latches} >= {"arm_latch_M", "arm_latch_O"}, "safety: permission.arm_latches must define arm_latch_M and arm_latch_O")
    for l in latches:
        terms = set(l.get("clear_terms", []))
        r.ok(l.get("watchdog") in terms and l.get("base") in terms, f"safety: {l['id']} clear terms {sorted(terms)} lack its watchdog {l.get('watchdog')} or base {l.get('base')}")
        rhs = eqs.get(l.get("clear_equation"), "")
        r.ok(bool(rhs), f"safety: {l['id']} clear equation {l.get('clear_equation')!r} not among permission.equations")
        for t in (l.get("watchdog"), l.get("base")):
            r.ok(bool(t) and t in expand_terms(rhs, eqs), f"safety: {l['id']} clear equation does not contain {t}")
        r.ok(l.get("watchdog", "") in expand_terms(eqs.get(l.get("gates", ""), ""), eqs), f"safety: {l['id']} gate {l.get('gates')} does not include {l.get('watchdog')}")
    # every hardware permission input has a defined absent-driver default
    defaults = {d["net"]: d for d in perm.get("defaults", [])} if isinstance(perm.get("defaults"), list) else {}
    for net in ("TX_PERMIT", "OUT_PERMIT", "PROC_PERMIT", "EXT_PERMIT_3V3", "PROCESS_PERMIT_EXT_3V3", "DIC_OK", "PERMIT_OUT_REQ",
                "FPGA_MOTION_REQUEST", "FPGA_OUTPUT_REQUEST"):
        r.ok(net in defaults and bool(defaults[net].get("default")), f"safety: hardware permission input {net} has no defined absent-driver default")
    r.ok("DIC_OK" in eqs.get("base_ok", "") and "DIC_OK" in eqs.get("out_base_ok", ""), "safety: base_ok/out_base_ok do not include DIC_OK")
    # self-test containment: nothing that can close a field contact or energize an output lacks a hold-off term
    for c in perm.get("selftest_containment", []):
        if c.get("field_contact") or c.get("energizes_output"):
            r.ok(bool(str(c.get("held_off_during_selftest_by", "")).strip()), f"safety: receiver '{c['receiver']}' can act in the field during SELFTEST without a hold-off term")
    r.ok(any("PERMIT_OUT" in c["receiver"] for c in perm.get("selftest_containment", [])), "safety: selftest_containment does not list PERMIT_OUT")
    # power budgets
    pr = s["power_requirements"]
    for ent in ("FIELD_A", "FIELD_B"):
        e = pr["field"][ent]
        r.ok(abs(sum(e.get("loads_a", {}).values()) - e["continuous_a"]) < 0.006, f"safety: {ent} loads_a do not sum to continuous_a {e['continuous_a']}")
        r.ok(abs(e["ilim_min_a"] - (e["continuous_a"] + 0.5)) < 0.011, f"safety: {ent} current-limit minimum != continuous - 0.5 + 1.0")
        fbt = specs["terminals"]["field_power_budget"][ent]
        r.ok(abs(fbt["total_a"] - e["continuous_a"]) < 0.006 and abs(fbt["entry_current_limit_min_a"] - e["ilim_min_a"]) < 0.006,
             f"terminals.field_power_budget.{ent} differs from safety.json")
    ci = pr["core_24v_input_a"]
    parts = ["core5v", "analog", "ai_group"]
    t8 = sum(ci[k] for k in parts) + ci["motion5v_8"]
    t12 = sum(ci[k] for k in parts) + ci["motion5v_12"]
    r.ok(abs(ci["total_8_motor"] - t8) < 0.006 and abs(ci["total_12_motor"] - t12) < 0.006, "safety: CORE_24V input totals do not add up")
    r.ok(abs(ci["total_12_motor_plus_encoder_expansion"] - (t12 + ci["encoder_expansion"])) < 0.006, "safety: CORE_24V full-configuration total does not add up")
    r.ok(abs(pr["core_entry_requirement"]["ilim_min_a_at_18v"] - round(1.2 * ci["total_12_motor_plus_encoder_expansion"], 2)) < 0.006, "safety: core entry current-limit minimum != 1.2 x full-configuration input")
    r.ok(abs(specs["terminals"]["field_power_budget"]["CORE"]["entry_current_limit_min_a"] - pr["core_entry_requirement"]["ilim_min_a_at_18v"]) < 0.006,
         "terminals.field_power_budget.CORE differs from safety.json")
    budgets = {"FIELD_A": pr["field"]["FIELD_A"].get("loads_a", {}), "FIELD_B": pr["field"]["FIELD_B"].get("loads_a", {}), "CORE_24V": ci}
    tids = {x["id"]: x for x in specs["terminals"]["terminals"]}
    per_key = collections.defaultdict(float)
    for ld in pr.get("terminal_supply_loads", []):
        x = tids.get(ld["terminal"])
        r.ok(x is not None and x["net"] == ld["net"], f"safety: terminal_supply_loads {ld['terminal']} ({ld['net']}) not in terminals.json")
        r.ok(ld["budget_key"] in budgets.get(ld["entry"], {}), f"safety: terminal {ld['terminal']} load has no budget item {ld['budget_key']} in entry {ld['entry']}")
        per_key[(ld["entry"], ld["budget_key"])] += ld["a"]
    for (ent, key), a in per_key.items():
        cap = budgets.get(ent, {}).get(key)
        if isinstance(cap, (int, float)) and ent != "CORE_24V":
            r.ok(a <= cap + 1e-9, f"safety: terminal loads on {ent}.{key} ({a:.3f} A) exceed the budget item ({cap} A)")
    for x in specs["terminals"]["terminals"]:
        if x["function_class"] in ("supply", "status_output") and x["domain"] in ("FIELD_B", "ISO_AI") and x["net"] not in ("SENS24_G1", "SENS24_G2"):
            r.ok(any(ld["net"] == x["net"] for ld in pr.get("terminal_supply_loads", [])) or not re.search(r"\d+ ?mA|A limit", x["electrical_target"]),
                 f"safety: sourcing terminal {x['id']} ({x['net']}) is not listed in terminal_supply_loads")
    a5 = pr["aux_supplies"]["AUX_5V"].get("chain")
    if r.ok(isinstance(a5, dict), "safety: AUX_5V chain arithmetic missing"):
        term = a5["aux5_ok_trip_falling_min_v"] - a5["distribution_drop_max_v"]
        ena = term - (a5["ron_max_ohm"] + a5["cable_loop_resistance_max_ohm"]) * a5["ena_current_max_a"]
        r.ok(abs(a5["ena_min_v"] - ena) < 0.002 and ena >= a5["ena_disable_min_v"], f"safety: worst-case DM542T ENA voltage {ena:.3f} V below {a5['ena_disable_min_v']} V or misstated")
        r.ok(a5["setpoint_v"] * (1 - a5["regulation_pct"] / 100) - a5["limiter_drop_max_v"] > a5["aux5_ok_trip_falling_min_v"], "safety: AUX_5V monitor node can sit below the AUX5_OK trip in normal operation")
    r.ok(any("PWM" in o["function"] for o in s["output_fault_states"]), "safety: output_fault_states has no PWM row")
    si = s.get("safety_interface", {})
    r.ok(all(k in si for k in ("reset_arm", "contactor_fb", "sto_fb", "chain_status", "machine_enable_nets")), "safety: safety_interface behaviour incomplete")


# ------------------------------------------------------------------ fault names used in fault texts resolve
FAULT_REF = [re.compile(r"latch(?:es|ed)?\s+([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+)"), re.compile(r"([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+) \(fault bit (\d+)\)"),
             re.compile(r"=> ([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+)"), re.compile(r"⇒ ([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+)")]


def check_fault_names(r, specs):
    p = specs["protocol"]
    faults = {f["name"]: f["bit"] for f in p["fault_word"]}
    events = {e["name"] for e in p["events"]}
    texts = [(f"terminal {x['id']} fault_state", str(x.get("fault_state", ""))) for x in specs["terminals"]["terminals"]]
    texts += [(f"connection '{c['id']}' fault", c["fault"]) for c in p["connections"]]
    texts += [(f"safety status field {f['field']}", str(f.get("response", ""))) for f in specs["safety"]["safety_status_fields"]]
    texts += [(f"safety_interface.{k}", v) for k, v in specs["safety"].get("safety_interface", {}).items() if isinstance(v, str)]
    for where, t in texts:
        for rx in FAULT_REF:
            for m in rx.finditer(t):
                name = m.group(1)
                if name in ("OPI_OK", "SW_STATE", "CARD_EN"):
                    continue
                r.ok(name in faults or name in events, f"{where}: fault or event name {name} is not defined in protocol fault_word or events")
                if rx.groups == 2 and name in faults:
                    r.ok(str(faults[name]) == m.group(2), f"{where}: {name} is fault bit {faults[name]}, text says {m.group(2)}")


# ------------------------------------------------------------------ allocation net lists (single writer, joints, homing, spindles)
PIN = re.compile(r"^[a-z0-9_]+(\.[A-Za-z0-9_-]+)+$")


def check_hal_nets(r, specs):
    t = specs["terminals"]
    nets = {x["id"]: x["net"] for x in t["terminals"]}
    registry = {h["name"] for h in specs["protocol"]["hal_pins"]}
    r.ok("halui.joint.{jt}.unhome" in registry and "halui.joint.{m}.unhome" not in registry,
         "protocol: halui unhome must be registered per joint index ({jt}), not per channel ({m})")
    jt = specs["protocol"]["hal_index"].get("jt", [0, -1])
    for cfg in specs["allocations"]["configurations"]:
        cid = cfg["id"]
        hm = cfg.get("hal_map")
        if not r.ok(isinstance(hm, dict), f"allocation {cid}: no hal_map"):
            continue
        writers = collections.defaultdict(list)
        motors = [a for a in cfg["assignments"] if a["resource_class"] == "motor"]
        joints = {}
        for a in motors:
            h = a.get("hal", {})
            if not r.ok(all(k in h for k in ("joint", "axis", "extra_joint", "pos_fb")), f"allocation {cid}: motor channel {a['channel']} lacks joint/axis/extra_joint/pos_fb"):
                continue
            r.ok(h["joint"] not in joints, f"allocation {cid}: joint {h['joint']} mapped to two channels")
            joints[h["joint"]] = (a["channel"], h)
            writers[f"joint.{h['joint']}.motor-pos-fb"].append(h["pos_fb"])
            writers[f"cnc1.{a['channel']}.enable"].append(f"joint.{h['joint']}.amp-enable-out")
            writers[f"cnc1.{a['channel']}.position-cmd"].append(f"joint.{h['joint']}.motor-pos-cmd")
        n = hm.get("joints_total", -1)
        r.ok(n == hm.get("kinematic_joints", 0) + hm.get("extra_joints", 0), f"allocation {cid}: joints_total != kinematic + extra")
        r.ok(sorted(joints) == list(range(n)), f"allocation {cid}: joints {sorted(joints)} are not exactly 0..{n - 1}, each with one channel")
        r.ok(n - 1 <= jt[1], f"allocation {cid}: joint index {n - 1} beyond the halui unhome registry (jt 0-{jt[1]})")
        for j, (ch, h) in joints.items():
            r.ok(h["extra_joint"] == (j >= hm.get("kinematic_joints", 0)), f"allocation {cid}: joint {j} extra-joint flag wrong (LinuxCNC numbers extra joints last)")
        for a in cfg["assignments"]:
            h = a.get("hal", {})
            rc = a["resource_class"]
            src = {"di": f"cnc1.din.{a['channel']}", "encoder": f"cnc1.encoder.{a['channel']}", "probe": f"cnc1.probe.{a['channel']}.in",
                   "freq": f"cnc1.freq.{a['channel']}"}.get(rc)
            if src:
                for tg in h.get("targets", []):
                    if " <- " in tg:
                        pin, w = tg.split(" <- ", 1)
                        pin = pin.strip()
                        if pin.endswith("motor-pos-fb"):
                            j = int(pin.split(".")[1])
                            own = joints.get(j, (None, {}))[1].get("pos_fb")
                            r.ok(own == w.split(" (")[0].strip(), f"allocation {cid}: joint {j} motor-pos-fb written by {w.split(' (')[0]} and by {own} (two writers)")
                            continue
                        writers[pin].append(w.split(" (")[0].strip())
                    elif PIN.match(tg):
                        writers[tg].append(src)
            if rc in ("do", "ao", "proc_en"):
                pin = {"do": f"cnc1.dout.{a['channel']}", "ao": f"cnc1.aout.{a['channel']}.value", "proc_en": f"cnc1.proc-en.{a['channel']}.cmd"}[rc]
                if r.ok(bool(h.get("writer")), f"allocation {cid}: {rc} {a['channel']} ('{a['function']}') has no single named writer"):
                    writers[pin].append(h["writer"])
            if rc == "do":
                if r.ok(isinstance(a.get("peak_a"), (int, float)), f"allocation {cid}: DO{a['channel']} has no declared peak current"):
                    r.ok(a["peak_a"] <= 0.62 or a.get("via_relay"), f"allocation {cid}: DO{a['channel']} peak {a['peak_a']} A exceeds the 0.62 A current-limit minimum without an interposing relay")
                r.ok(a["assumed_load_a"] <= 0.5, f"allocation {cid}: DO{a['channel']} continuous load above 0.5 A")
            if rc == "pendant_sel" and "axis" in h:
                r.ok(nets.get(a["terminal"]) == f"MPG_SEL_{h['axis']}", f"allocation {cid}: '{a['function']}' on {a['terminal']} ({nets.get(a['terminal'])}), not the MPG_SEL_{h['axis']} terminal")
            if rc == "process_permit":
                r.ok(not re.search(r"spindle/|spindle permit|spindle chain|spindle/torch", a["function"], re.I),
                     f"allocation {cid}: XS1.3 advertised as a spindle permit; it gates XPC0/XPC1 only")
        pn = hm.get("probe_net", {})
        if pn.get("mode") in ("or2", "mux2"):
            writers[pn["target"]].append(f"{pn.get('component', pn['mode'])}.out")
        for pin, ws in writers.items():
            r.ok(len(ws) == 1, f"allocation {cid}: HAL pin {pin} has {len(ws)} writers {ws}")
        for j in range(n):
            r.ok(len(writers.get(f"joint.{j}.motor-pos-fb", [])) == 1, f"allocation {cid}: joint {j} has no single motor-pos-fb source")
        # gantry groups: members with the same letter share one negative HOME_SEQUENCE
        by_axis = collections.defaultdict(list)
        for j, (ch, h) in joints.items():
            if h["axis"] != "-":
                by_axis[h["axis"]].append(j)
        seq = {}
        for g in hm.get("homing_groups", []):
            for j in g["joints"]:
                seq[j] = g["home_sequence"]
        for axis, js in by_axis.items():
            if len(js) > 1:
                ss = {seq.get(j) for j in js}
                r.ok(len(ss) == 1 and None not in ss and next(iter(ss)) < 0,
                     f"allocation {cid}: gantry {axis} joints {sorted(js)} do not share one negative HOME_SEQUENCE ({ss})")
        # spindles: never a bus-only run path; referenced channels exist
        dos = {a["channel"] for a in cfg["assignments"] if a["resource_class"] == "do"}
        pens = {a["channel"] for a in cfg["assignments"] if a["resource_class"] == "proc_en"}
        for sp in hm.get("spindles", []):
            hw = [x for x in sp.get("run_paths", []) if x.startswith(("do:", "proc_en:"))]
            r.ok(bool(hw), f"allocation {cid}: spindle {sp['id']} has no hardware run path (bus-only run-enable refused)")
            for x in hw:
                kind, ch = x.split(":")
                r.ok(int(ch) in (dos if kind == "do" else pens), f"allocation {cid}: spindle {sp['id']} run path {x} is not allocated")
        uses_bus_spindle = any(a["resource_class"] in ("rs485", "can") and "spindle" in a["function"].lower() for a in cfg["assignments"])
        r.ok(not uses_bus_spindle or bool(hm.get("spindles")), f"allocation {cid}: bus-controlled spindle without a spindle run-path record")
        for g, chk in cfg["do_group_current_check"].items():
            lo, hi = [int(x) for x in re.findall(r"DO(\d+)", g)]
            tot = sum(a["assumed_load_a"] for a in cfg["assignments"] if a["resource_class"] == "do" and lo <= a["channel"] <= hi)
            r.ok(abs(tot - chk["assumed_all_on_a"]) < 0.006 and tot <= chk["group_limit_a"], f"allocation {cid}: DO group {g} sum {tot:.2f} A misstated or above {chk['group_limit_a']} A")
        for o in cfg.get("optional", []):
            r.ok(not re.search(r"modbus", o, re.I) or re.search(r"run-enable|run path", o, re.I), f"allocation {cid}: optional variant '{o}' makes Modbus the only run path")


# ------------------------------------------------------------------ protocol additions: ages, telemetry, diagnostics references
def check_protocol_repair(r, specs):
    p = specs["protocol"]
    ar = p["io_link"].get("age_rules", {})
    s = p["schedule"]
    if r.ok(bool(ar), "protocol: io_link.age_rules missing"):
        for key in ("din_stale_limit_us", "ain_stale_limit_us"):
            lim = ar[key]
            valid_max = ar["snapshot_staleness_nominal_us"] + ar["link_period_us"] * (ar["failures_before_port_fault"] - 1)
            r.ok(lim["min"] > ar["snapshot_staleness_nominal_us"] and lim["max"] <= valid_max, f"protocol: {key} range {lim['min']}-{lim['max']} us outside ({ar['snapshot_staleness_nominal_us']}, {valid_max}]")
            for case in s["cases"].values():
                r.ok(lim["max"] + case["input_age_counters_us"] <= s["separate_bounds_us_REQ"]["di_input_age_worst_valid_excluding_debounce"],
                     f"protocol: {key} maximum + counter age exceeds the published worst-case DI/AI age bound")
                r.ok(ar["snapshot_staleness_nominal_us"] + case["input_age_counters_us"] <= s["separate_bounds_us_REQ"]["di_input_age_excluding_debounce"],
                     "protocol: nominal DI age exceeds its bound")
        f0 = {f["name"]: f for f in p["frames"]["configure_io_page0_at_16"]}
        for key in ("din_stale_limit_us", "ain_stale_limit_us"):
            r.ok(f"{ar[key]['min']}..{ar[key]['max']}" in f0[key]["rule"], f"protocol: CONFIGURE_IO {key} rule does not state the {ar[key]['min']}..{ar[key]['max']} range")
    tel = p["telemetry"]
    r.ok(tel.get("worst_case_rotation_ms") == 2 * tel["mirror_entries_is1_default"], "protocol: telemetry worst-case rotation != 2 x entries (priority limited to every other slot)")
    cur = next(m for m in p["telemetry_map"] if m["logical"] == "TEL.dout[i].current")
    r.ok(tel.get("worst_case_rotation_ms", 1e9) + 3.05 <= cur["stale_ms"], "protocol: output-current worst-case age exceeds its stale limit")
    for f in p["frames"]["configure_io_page1_at_16"]:
        if f["name"].startswith("pwm") and f["name"].endswith("_flags"):
            r.ok(f["rule"].startswith("zero") and "b0 inverted" not in f["rule"], f"protocol: {f['name']} still defines an inverted PWM mode")
    logical = logical_names(p)
    events = {e["name"] for e in p["events"]}
    tel_names = {norm_logical(m["logical"]) for m in p["telemetry_map"]}
    host = {norm_logical(h["logical"]) for h in p["host_sources"]}
    groups = {g["group"] for recs in specs["modules"]["boundaries"].values() for x in recs for g in x["groups"]}
    for d in p["diagnostics"]:
        refs = d.get("transport_refs")
        if not r.ok(bool(refs), f"diagnostic '{d['signal']}': no transport_refs (physical path to the host)"):
            continue
        for ref in refs:
            base = norm_logical(ref)
            if base.startswith("EVT.type "):
                ok = base.split(" ", 1)[1] in events
            elif base.startswith(("STS.", "CMD.", "EVT.")):
                ok = base in logical
            elif base.startswith("TEL."):
                ok = base in tel_names
            elif base.startswith("HOST."):
                ok = base in host
            elif base.startswith("conductor:"):
                ok = base.split(":", 1)[1] in groups
            else:
                ok = False
            r.ok(ok, f"diagnostic '{d['signal']}': transport reference {ref} resolves to no frame field, event, telemetry entry, host source or conductor group")
    fw = {f["name"] for f in p["fault_word"]}
    r.ok({"CONTACTOR_FEEDBACK", "STO_FEEDBACK", "ARM_REFUSED"} <= fw, "protocol: safety-interface fault bits missing")
    p1 = {f["name"] for f in p["frames"]["configure_io_page1_at_16"]}
    r.ok({"safety_if_flags", "reset_arm_window_ms", "contactor_close_ms", "contactor_open_ms", "sto_response_ms"} <= p1, "protocol: CONFIGURE_IO page 1 lacks the safety-interface fields")


def check_display_rule(r, specs):
    p = specs["protocol"]
    for m in p["telemetry_map"]:
        r.ok(isinstance(m.get("stale_ms"), (int, float)), f"protocol: telemetry {m['logical']} has no stale limit")
    for h in p["host_sources"]:
        cyclic = not re.search(r"request|qualification", h["rate"])
        r.ok(not cyclic or isinstance(h.get("stale_ms"), (int, float)), f"protocol: host source {h['logical']} is cyclic but has no stale limit")
    r.ok("stale_ms" in specs["terminals"].get("display_rule", ""), "terminals.json: display_rule does not cite the per-source stale_ms limits")
    for x in specs["terminals"]["terminals"]:
        d = x.get("diagnostics")
        if isinstance(d, dict):
            r.ok("3 telemetry periods" not in str(d.get("shown_as", "")), f"terminal {x['id']}: uses the withdrawn '3 reporting periods' stale rule")


# ------------------------------------------------------------------ pricing
def check_pricing(r, specs):
    m = specs["modules"]
    pr = m["pricing"]
    f = pr.get("formula")
    if not r.ok(isinstance(f, dict), "modules.pricing.formula missing"):
        return
    def price(cost, gm):
        return int(math.ceil(cost / (1 - gm) / f["round_up_to_usd"]) * f["round_up_to_usd"]) - f["less_usd"]
    cs = m["cost_summary_usd_qty100"]
    per = cs["per_item"]
    gm = f["gross_margin"]
    exp = {"controller_8_motor": [price(cs["controller_8_motor"]["low"], gm["controller"]), price(cs["controller_8_motor"]["high"], gm["controller"])],
           "mx4_with_xtb": [price(per["MX4"]["low"] + per["XTB"]["low"], gm["spares_and_expansions"]), price(per["MX4"]["high"] + per["XTB"]["high"], gm["spares_and_expansions"])],
           "ex8": [price(per["EX8"]["low"], gm["spares_and_expansions"]), price(per["EX8"]["high"], gm["spares_and_expansions"])]}
    for k, v in exp.items():
        r.ok(pr[k] == v, f"modules.pricing.{k} {pr[k]} does not follow the stated rule ({v})")
    for pk in m["packages_usd_qty100"]["packages"]:
        add = pk["display_usd"] + pk["control_psu_usd"] + pk["hdmi_usd"]
        lo = price(cs["controller_8_motor"]["low"], gm["controller"]) + price(add, gm["package_addons"]) + int(f["ai_allowance_usd"])
        r.ok(pk["price_low"] == lo, f"modules: package {pk['screen']} price_low {pk['price_low']} != rule {lo}")
    sp = m.get("spare_targets_usd", {})
    r.ok(sp.get("EX8", 1e9) <= pr["ex8"][1], f"modules: EX8 spare target {sp.get('EX8')} above the EX8 expansion price {pr['ex8'][1]}")
    for k, v in sp.items():
        if k not in ("CMC",) and v > 0.10 * pr["controller_8_motor"][0]:
            r.ok(k in m.get("spare_target_reasons", {}), f"modules: spare target {k} ${v} above 10 % of the controller price without a written reason")


# ------------------------------------------------------------------ service contract (section 05)
def check_service(r, specs, root=None, docs=True):
    sv = specs["service"]
    ids = [x["id"] for x in sv["validator_rules"]]
    r.ok(len(ids) == len(set(ids)), "service: duplicate validator rule ids")
    for i in ids:
        r.ok(re.fullmatch(r"V-(EL|CH|ML|TM)-\d\d", i) is not None, f"service: rule id {i} malformed")
    r.ok(sv["hw_modules"]["slot_keys"] == specs["protocol"]["hal_index"]["slot"], "service: hw.modules slot keys differ from the protocol slot index")
    for fld in sv["preview"]["fields"]:
        r.ok(bool(fld.get("source")) and bool(fld.get("label_rule")), f"service: preview field {fld.get('name')} lacks a source or label rule")
    th = sv["preview"]["thresholds"]
    r.ok(all(isinstance(th[k], (int, float)) for k in ("disagreement_warn_fraction_of_ferror", "disagreement_alarm_fraction_of_ferror", "feedback_stale_after_ms")),
         "service: preview thresholds are not numeric")
    r.ok(th["disagreement_warn_fraction_of_ferror"] < th["disagreement_alarm_fraction_of_ferror"], "service: warn threshold not below alarm threshold")
    r.ok(any("commanded position" in f["label_rule"] for f in sv["preview"]["fields"]), "service: no 'commanded position' label rule for joints without feedback")
    r.ok("never" in sv["question"]["rule"], "service: the question rule does not forbid invented values")
    for item in ("host_image", "card_firmware", "gateware", "esp_firmware", "configuration"):
        u = sv["update_states"].get(item, {})
        r.ok(bool(u.get("states")) and bool(u.get("power_loss")), f"service: update item {item} lacks states or power-loss behaviour")
    known = set(ids)
    for fn in ("check_allocations", "check_hal_nets", "check_protocol", "check_display_rule"):
        pass
    for rid, fn in sv.get("spec_validator_coverage", {}).items():
        r.ok(rid in known and fn in globals(), f"service: coverage entry {rid} -> {fn} does not resolve")
    blobs = [json.dumps(specs[n], ensure_ascii=False) for n in SPEC_FILES if n != "service"]
    if docs and root:
        for rel in DOCS:
            path = os.path.join(root, rel)
            if os.path.exists(path):
                blobs.append(read_bytes(path).decode("utf-8"))
    for b in blobs:
        for ref in set(re.findall(r"\bV-(?:EL|CH|ML|TM)-\d\d\b", b)):
            r.ok(ref in known, f"validator rule {ref} is referenced but not defined in spec/service.json")


# ------------------------------------------------------------------ rendered documents are current
def check_rendered(r, root):
    tools = os.path.join(root, "tools", "interface_spec")
    if not r.ok(os.path.isdir(tools), "tools/interface_spec missing"):
        return
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "spec"))
        os.makedirs(os.path.join(tmp, "docs", "interface-spec"))
        for name in SPEC_FILES:
            shutil.copy(os.path.join(root, "spec", name + ".json"), os.path.join(tmp, "spec"))
        jobs = [(["render_01.py", tmp], ["docs/interface-spec/01-protocol-and-schedule.md"]),
                (["render_03.py", tmp], ["docs/interface-spec/03-terminals-and-allocations.md"]),
                (["gen_02.py", tmp, os.path.join(tools, "02-template.md")], ["spec/modules.json", "docs/interface-spec/02-modules-and-boundaries.md"]),
                (["gen_04_json.py", tmp], ["spec/safety.json"])]
        for args, outputs in jobs:
            proc = subprocess.run([sys.executable, os.path.join(tools, args[0])] + args[1:], capture_output=True, text=True)
            if not r.ok(proc.returncode == 0, f"{args[0]} failed: {proc.stderr.strip()[-300:]}"):
                continue
            for rel in outputs:
                a = read_bytes(os.path.join(tmp, rel))
                b = read_bytes(os.path.join(root, rel))
                r.ok(a == b, f"{rel} is not current: re-run tools/interface_spec/{args[0]}")


def validate(root=REPO, render=True, docs=True):
    r = Report()
    specs = load(root)
    check_revision(r, root, specs, docs=docs)
    check_terminals(r, specs)
    check_channels(r, specs)
    check_allocations(r, specs)
    check_modules(r, specs)
    check_protocol(r, specs)
    check_names(r, specs)
    check_protocol_repair(r, specs)
    check_safety(r, specs)
    check_fault_names(r, specs)
    check_hal_nets(r, specs)
    check_display_rule(r, specs)
    check_pricing(r, specs)
    check_service(r, specs, root, docs)
    if render:
        check_rendered(r, root)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description="IS-1 interface specification cross-reference validator (read-only)")
    ap.add_argument("--check", action="store_true", help="validate without writing anything (the default and only mode)")
    ap.add_argument("--root", default=REPO, help="repository root to validate (default: this repository)")
    ap.add_argument("--no-render", action="store_true", help="skip the rendered-document currency check")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    r = validate(args.root, render=not args.no_render)
    if args.json:
        print(json.dumps({"spec_revision": REVISION, "passed": r.passed, "problems": r.problems}, indent=1))
    else:
        print(f"IS-1 interface specification: {r.passed} checks passed, {len(r.problems)} problems")
        for p in r.problems:
            print("  PROBLEM: " + p)
    return 1 if r.problems else 0


if __name__ == "__main__":
    sys.exit(main())
