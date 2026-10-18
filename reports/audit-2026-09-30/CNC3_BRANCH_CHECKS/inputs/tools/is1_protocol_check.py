#!/usr/bin/env python3
"""Consistency checks for interface specification IS-1, section 01 (protocol and schedule).

Checks spec/protocol.json against itself and against
docs/interface-spec/01-protocol-and-schedule.md:

* spec revision identifiers;
* every frame layout is contiguous, sums to its frame length and ends in its CRC;
* CRC known answers and the recorded frame vectors;
* the per-cycle schedule arithmetic at 5 and 6.25 MHz;
* opcode uniqueness and chip-select assignment;
* fault-word and safety-word bit numbering;
* every frame field name and every connection id appears in the markdown.

``--hd`` additionally runs the exhaustive CRC Hamming-distance search quoted in
the document (needs numpy; the CRC-32C case takes several minutes).

This is a specification check (arithmetic and source consistency). It does not
test any RTL, driver, firmware or hardware. Exit status 0 = all checks passed.
"""
import argparse
import binascii
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "spec", "protocol.json")
DOC = os.path.join(ROOT, "docs", "interface-spec", "01-protocol-and-schedule.md")

FRAME_LENGTHS = {
    "fb_command": 176, "fb_response_CNF3": 176, "cmd_command": 96, "cmd_response_CNS3": 96,
    "fb_read_payload_at_16": 158, "configure_payload_at_16": 158, "configure_io_page0_at_16": 158,
    "configure_io_page1_at_16": 158, "configure_io_card_pages_at_16": 158,
    "cap3_page0": 176, "cap3_page1": 176, "flt3_page2": 176, "idp3_page3": 176,
    "iol1_command": 40, "iol1_response": 40,
}
CRC_FRAMES = {"fb_command", "fb_response_CNF3", "cmd_command", "cmd_response_CNS3",
              "cap3_page0", "cap3_page1", "flt3_page2", "idp3_page3", "iol1_command", "iol1_response"}


def crc16(data):
    return binascii.crc_hqx(bytes(data), 0xFFFF)


def crc32c(data):
    crc = 0xFFFFFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


class Checker:
    def __init__(self):
        self.failures = []
        self.passed = 0

    def check(self, cond, what):
        if cond:
            self.passed += 1
        else:
            self.failures.append(what)


def check_frames(c, spec):
    frames = spec["frames"]
    for name, length in FRAME_LENGTHS.items():
        c.check(name in frames, f"frame {name} present")
        if name not in frames:
            continue
        off = 0
        for f in frames[name]:
            c.check(f["offset"] == off, f"{name}.{f['name']} offset {f['offset']} == {off}")
            off = f["offset"] + f["size"]
        c.check(off == length, f"{name} total {off} == {length}")
        names = [f["name"] for f in frames[name]]
        c.check(len(names) == len(set(names)), f"{name} unique field names")
        if name in CRC_FRAMES:
            last = frames[name][-1]
            want = 4 if name.startswith("iol1") else 2
            c.check(last["name"].startswith("crc") and last["size"] == want and last["offset"] == length - want,
                    f"{name} ends in its CRC")


def check_crc(c, spec):
    c.check(crc16(b"123456789") == 0x29B1, "CRC-16/CCITT-FALSE check value")
    c.check(crc32c(b"123456789") == 0xE3069283, "CRC-32C check value")
    c.check(spec["crc"]["host_frames"]["check_123456789"] == "0x29B1", "recorded CRC-16 check value")
    c.check(spec["crc"]["io_link"]["check_123456789"] == "0xE3069283", "recorded CRC-32C check value")
    for name, v in spec["crc"]["vectors"].items():
        raw = bytes.fromhex(v["hex"])
        if name.startswith("iol1"):
            c.check(len(raw) == 40 and crc32c(raw[:-4]) == int.from_bytes(raw[-4:], "big"), f"vector {name} CRC-32C")
        else:
            c.check(len(raw) in (96, 176) and crc16(raw[:-2]) == int.from_bytes(raw[-2:], "big"), f"vector {name} CRC-16")
            c.check(raw[:4] == b"CNC3" and raw[4] == 3, f"vector {name} header")


def check_schedule(c, spec):
    s = spec["schedule"]
    a = s["allocations_us_REQ"]
    guard = 24 * 0.02
    total = sum(v for k, v in a.items() if k != "cmd_ioctl_post")
    c.check(abs(total - s["allocation_total_to_commit_us"]) < 1e-9, "allocation total")
    fb_bits = FRAME_LENGTHS["fb_command"] * 8
    cmd_bits = FRAME_LENGTHS["cmd_command"] * 8
    for key, f in (("5.00_MHz", 5e6), ("6.25_MHz", 6.25e6)):
        case = s["cases"][key]
        fbx = fb_bits / f * 1e6 + guard
        cmx = cmd_bits / f * 1e6 + guard
        comp = total + fbx + cmx
        c.check(abs(case["completion_C_us"] - round(comp, 2)) < 0.006, f"{key} completion")
        c.check(abs(case["wire_plus_guards_us"] - round(fbx + cmx, 2)) < 0.006, f"{key} wire")
        c.check(abs(case["margin_to_700_us"] - round(700 - comp, 2)) < 0.006, f"{key} 700 us margin")
        c.check(abs(case["host_overhead_allowed_for_700_us"] - round(700 - fbx - cmx, 2)) < 0.006, f"{key} overhead allowance")
        c.check(comp < 1000.0, f"{key} allocation inside the 1 ms period")
    link = spec["io_link"]["timing"]
    frame_us = 40 * 8 / (50e6 / 6) * 1e6
    c.check(abs(link["frame_us"] - round(frame_us, 2)) < 0.006, "IOL1 frame time")
    c.check(link["slot_us"] < link["period_us"], "IOL1 frame fits its period")
    c.check(spec["io_link"]["card_watchdogs"]["accept_timer"].startswith("firmware timer"), "card accept timer text")


def check_tables(c, spec):
    codes = [o["code"] for o in spec["opcodes"]]
    c.check(len(codes) == len(set(codes)), "opcode codes unique")
    for cs, info in spec["host_link"]["chip_selects"].items():
        listed = set(info["opcodes"])
        actual = {o["code"] for o in spec["opcodes"] if o["cs"] == cs}
        c.check(listed == actual, f"{cs} opcode list matches the opcode table")
    bits = [b["bit"] for b in spec["fault_word"]]
    c.check(bits == list(range(len(bits))) and len(bits) <= 32, "fault word bits consecutive")
    sbits = [b["bit"] for b in spec["safety_power_word"] if isinstance(b["bit"], int)]
    c.check(sbits == list(range(len(sbits))) and len(sbits) <= 32, "safety word bits consecutive")
    for rec, rows in spec["history_records"].items():
        c.check(sum(r["size"] for r in rows) == 64, f"history record {rec} is 64 bytes")


def check_doc(c, spec):
    c.check(spec.get("spec_revision") == "IS-1", "JSON spec_revision IS-1")
    c.check(os.path.exists(DOC), "markdown present")
    if not os.path.exists(DOC):
        return
    text = open(DOC, encoding="utf-8").read()
    c.check(text.splitlines()[0].strip() == "Interface specification revision: IS-1", "markdown revision header")
    c.check("\r\n" not in text, "markdown uses LF line endings")
    for name, fields in spec["frames"].items():
        for f in fields:
            c.check(f"`{f['name']}`" in text, f"markdown lists {name}.{f['name']}")
    for row in spec["connections"]:
        c.check(row["id"] in text, f"markdown lists connection {row['id']}")


def hamming_search():
    import numpy as np

    def syn(poly, width, n):
        top = 1 << width
        s, out = 1, []
        for _ in range(n):
            out.append(s)
            s <<= 1
            if s & top:
                s ^= top | poly
        return np.array(out, dtype=np.uint64)

    def min_weight(poly, width, n, maxw):
        S = syn(poly, width, n)
        if len(np.unique(S)) < n:
            return 2
        i, j = np.triu_indices(n, 1)
        P = S[i] ^ S[j]
        if np.isin(P, S).any():
            return 3
        order = np.argsort(P, kind="stable")
        Ps = P[order]
        for k in np.nonzero(Ps[1:] == Ps[:-1])[0]:
            a, b = order[k], order[k + 1]
            if len({i[a], j[a], i[b], j[b]}) == 4:
                return 4
        if maxw < 5:
            return None
        Pu = np.unique(P)
        for x in range(n):
            for y in range(x + 1, n):
                if np.isin(S[x] ^ S[y] ^ S[np.arange(y + 1, n)], Pu).any():
                    return 5
        if maxw < 6:
            return None
        T = np.sort(np.concatenate([S[x] ^ S[y] ^ S[np.arange(y + 1, n)] for x in range(n) for y in range(x + 1, n)]))
        return 6 if (T[1:] == T[:-1]).any() else None

    return {
        "CRC-16/CCITT 1408-bit": min_weight(0x1021, 16, 1408, 4),
        "CRC-16/CCITT 768-bit": min_weight(0x1021, 16, 768, 4),
        "CRC-16/CCITT 320-bit": min_weight(0x1021, 16, 320, 4),
        "CRC-32/IEEE 320-bit": min_weight(0x04C11DB7, 32, 320, 5),
        "CRC-32C 320-bit": min_weight(0x1EDC6F41, 32, 320, 6),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hd", action="store_true", help="run the exhaustive CRC Hamming-distance search (slow)")
    args = ap.parse_args()
    spec = json.load(open(SPEC, encoding="utf-8"))
    c = Checker()
    check_frames(c, spec)
    check_crc(c, spec)
    check_schedule(c, spec)
    check_tables(c, spec)
    check_doc(c, spec)
    result = {"passed": c.passed, "failed": len(c.failures), "failures": c.failures[:50]}
    if args.hd:
        hd = hamming_search()
        expected = {"CRC-16/CCITT 1408-bit": 4, "CRC-16/CCITT 768-bit": 4, "CRC-16/CCITT 320-bit": 4,
                    "CRC-32/IEEE 320-bit": 5, "CRC-32C 320-bit": 6}
        result["hamming_distance"] = hd
        for k, v in expected.items():
            c.check(hd[k] == v, f"HD {k} == {v}")
        result["passed"], result["failed"], result["failures"] = c.passed, len(c.failures), c.failures[:50]
    print(json.dumps(result, indent=1))
    return 0 if not c.failures else 1


if __name__ == "__main__":
    sys.exit(main())
