"""Render docs/interface-spec/01-protocol-and-schedule.md (IS-1) from 01-template.md and spec/protocol.json.

usage: python tools/interface_spec/render_01.py [root]   (root defaults to the repository)
spec/protocol.json is the frozen IS-1 source; this script only renders the markdown from it.
"""
import json, os, sys, re
SCR = os.path.dirname(os.path.abspath(__file__))
DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = json.load(open(os.path.join(DEST, "spec", "protocol.json"), encoding="utf-8"))
t = open(os.path.join(SCR, "01-template.md"), encoding="utf-8").read()

def esc(x):
    return str(x).replace("|", "\\|")

def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)

def frame_table(fields):
    rows = []
    for f in fields:
        a = f["offset"]; b = a + f["size"] - 1
        rows.append([f"{a}" if a == b else f"{a}–{b}", f"`{f['name']}`", f["type"], f["rule"], f.get("logical", "")])
    return table(["Bytes", "Field", "Type", "Rule", "Logical name"], rows)

for name, fields in spec["frames"].items():
    t = t.replace("{{TABLE:%s}}" % name, frame_table(fields))

t = t.replace("{{OPCODES}}", table(["Code", "Name", "Chip select", "Session / sequence", "Accepted when", "Effect"],
    [[o["code"], o["name"], o["cs"], o["session_seq"], o["accepted_when"], o["effect"]] for o in spec["opcodes"]]))
t = t.replace("{{FAULTS}}", table(["Bit", "Name", "Cause", "Response", "Cleared by"],
    [[f["bit"], f"`{f['name']}`", f["cause"], f["response"], f["cleared_by"]] for f in spec["fault_word"]]))
sw = spec["safety_power_word"]
rows = []
for i in range(0, len(sw), 2):
    pair = sw[i:i + 2]
    row = []
    for p in pair:
        row += [p["bit"], f"`{p['name']}`"]
    while len(row) < 4:
        row += ["", ""]
    rows.append(row)
t = t.replace("{{SAFETY}}", table(["Bit", "Name", "Bit", "Name"], rows))
t = t.replace("{{EVENTS}}", table(["Type", "Name", "Source", "Flags", "Values"],
    [[e["type"], e["name"], e["source"], e["flags"], e["values"]] for e in spec["events"]]))
vec = []
for k, v in spec["crc"]["vectors"].items():
    h = v["hex"]
    vec.append([f"`{k}`", len(h) // 2, f"`{h[:36]}…`", f"`0x{v['crc'].upper()}`"])
t = t.replace("{{VECTORS}}", table(["Vector", "Bytes", "Start of frame (hex)", "CRC"], vec) +
              "\n\nFull frames are in `spec/protocol.json` (`crc.vectors`). They are format vectors: `update_8ch_do5` also needs the matching session state and I/O enabled to be accepted.")
t = t.replace("{{CLASSES}}", table(["Class", "Card", "Port", "MCU", "Command payload (bytes 10–35)", "Realtime payload (response bytes 10–25)", "Configuration blob (24 B)"],
    [[c["class"], c["name"], c["port"], c["mcu"], c["command_payload"], c["realtime"], c["config_blob"]] for c in spec["io_link"]["card_classes"]]))
tel = []
for k, pages in spec["telemetry"]["pages"].items():
    tel.append(f"**{k}**\n")
    for p in pages:
        tel.append(f"- {p}")
    tel.append("")
t = t.replace("{{TELEMETRY}}", "\n".join(tel).rstrip())
sr = spec["io_link"]["status_registers"]
t = t.replace("{{STATUSREG}}", table(["Register", "Wires", "Bits", "Read period", "Layout", "Acceptance"],
    [[k, ", ".join(v["wires"]), v["bits"], f"{v['period_us']} µs at {v['sclk']}", v["layout"], v["acceptance"]] for k, v in sr.items() if k != "note"]) + "\n\n" + sr["note"])

s5 = spec["schedule"]["cases"]["5.00_MHz"]; s6 = spec["schedule"]["cases"]["6.25_MHz"]
a = spec["schedule"]["allocations_us_REQ"]
phases = [("Scheduling delay (wake latency)", a["scheduling_delay"], a["scheduling_delay"], "[REQ]"),
          ("FB ioctl entry to CS_FB assert", a["fb_ioctl_pre"], a["fb_ioctl_pre"], "[REQ]"),
          ("CS_FB 176 B wire + 0.48 µs guards", s5["fb_wire_us"] + 0.48, s6["fb_wire_us"] + 0.48, "[AR]"),
          ("CS_FB release to ioctl return", a["fb_ioctl_post"], a["fb_ioctl_post"], "[REQ]"),
          ("CNF3 decode and pin publish", a["decode_publish"], a["decode_publish"], "[REQ]"),
          ("LinuxCNC motion, kinematics, HAL functions", a["linuxcnc_compute"], a["linuxcnc_compute"], "[REQ]"),
          ("UPDATE encode", a["encode"], a["encode"], "[REQ]"),
          ("CMD ioctl entry to CS_CMD assert", a["cmd_ioctl_pre"], a["cmd_ioctl_pre"], "[REQ]"),
          ("CS_CMD 96 B wire + 0.48 µs guards", s5["cmd_wire_us"] + 0.48, s6["cmd_wire_us"] + 0.48, "[AR]")]
rows = []; c5 = c6 = 0.0
for n, d5, d6, lab in phases:
    c5 += d5; c6 += d6
    rows.append([n, f"{d5:.2f}", f"{c5:.2f}", f"{d6:.2f}", f"{c6:.2f}", lab])
rows.append(["**Completion C(k)** (commit)", "", f"**{s5['completion_C_us']:.2f}**", "", f"**{s6['completion_C_us']:.2f}**", "[AR on REQ]"])
rows.append(["Margin to the 700 µs target", "", f"{s5['margin_to_700_us']:.2f}", "", f"{s6['margin_to_700_us']:.2f}", "[AR on REQ]"])
rows.append(["Margin to the 1 ms period", "", f"{s5['margin_to_1000_us']:.2f}", "", f"{s6['margin_to_1000_us']:.2f}", "[AR on REQ]"])
rows.append(["CS_CMD release to ioctl return (thread end)", f"{a['cmd_ioctl_post']:.2f}", f"{s5['thread_end_us']:.2f}", f"{a['cmd_ioctl_post']:.2f}", f"{s6['thread_end_us']:.2f}", "[REQ]"])
rows.append(["FPGA commit processing after CS release", "≤ 0.2", "", "≤ 0.2", "", "[REQ, RTL design]"])
t = t.replace("{{SCHEDULE}}", table(["Phase", "5 MHz (µs)", "ends at (µs)", "6.25 MHz (µs)", "ends at (µs)", "Label"], rows) +
              "\n\nThe full-I/O card exchanges (section 5.4) run inside the FPGA in parallel with this schedule and take no host time; the host reads their latest validated results in CNF3.")

nums = {
    "WIRE5": f"{s5['wire_plus_guards_us']:.2f}", "WIRE625": f"{s6['wire_plus_guards_us']:.2f}",
    "REJ3X128": f"{spec['schedule']['rejected_alternatives_us']['record_v3_plus_separate_io_3x128B_5MHz_wire_us']:.2f}",
    "REJSYM": f"{spec['schedule']['rejected_alternatives_us']['symmetric_2x176B_5MHz_wire_us']:.2f}",
    "REJ3X128LEFT": f"{700 - spec['schedule']['rejected_alternatives_us']['record_v3_plus_separate_io_3x128B_5MHz_wire_us']:.2f}",
    "MIRROR": str(spec["telemetry"]["mirror_entries_is1_default"]),
    "OV5": f"{s5['host_overhead_allowed_for_700_us']:.2f}", "OV5K": f"{s5['host_overhead_allowed_for_1000_us']:.2f}",
    "OV625": f"{s6['host_overhead_allowed_for_700_us']:.2f}", "OV625K": f"{s6['host_overhead_allowed_for_1000_us']:.2f}",
    "ALLOC": f"{spec['schedule']['allocation_total_to_commit_us']:.2f}",
    "TWOK": f"{spec['schedule']['rejected_alternatives_us']['is1_at_2kHz_5MHz_wire_fraction_of_500us'] * 100:.1f} %",
    "AGE5": f"{s5['input_age_counters_us']:.2f}", "AGE625": f"{s6['input_age_counters_us']:.2f}",
    "DIAGE5": f"{s5['input_age_counters_us'] + 240.6:.2f}", "DIAGE625": f"{s6['input_age_counters_us'] + 240.6:.2f}",
    "DIWORST5": f"{s5['input_age_counters_us'] + spec['io_link']['age_rules']['din_stale_limit_us']['max']:.2f}", "DIWORST625": f"{s6['input_age_counters_us'] + spec['io_link']['age_rules']['din_stale_limit_us']['max']:.2f}",
    "MIRRORMAX": str(spec["telemetry"]["worst_case_rotation_ms"]),
    "CMD5": f"{s5['command_to_commit_us']:.2f}", "CMD625": f"{s6['command_to_commit_us']:.2f}",
    "DO5": f"{s5['command_to_commit_us'] + 160.4:.2f}", "DO625": f"{s6['command_to_commit_us'] + 160.4:.2f}",
    "LINKFRAME": f"{spec['io_link']['timing']['frame_us']:.2f}", "LINKSLOT": f"{spec['io_link']['timing']['slot_us']:.2f}",
    "LINKWIN": f"{spec['io_link']['timing']['card_processing_window_us']:.2f}",
}
for k, v in nums.items():
    t = t.replace("{{%s}}" % k, v)

t = t.replace("{{CONNECTIONS}}", table(["Connection", "Dir", "Transport field", "Update rate", "Maximum data age", "Fault response", "LinuxCNC HAL"],
    [[c["id"], c["dir"], c["field"], c["rate"], c["age"], c["fault"], c["hal"]] for c in spec["connections"]]))
t = t.replace("{{DIAG}}", table(["Signal", "Physical source", "Transport field", "Update rate", "Age bound", "Validity", "HAL / service", "Fault response"],
    [[d["signal"], d["source"], d["transport"], d["rate"], d["age_bound"], d["validity"], d["hal"], d["response"]] for d in spec["diagnostics"]]))
for rec in ("HR1", "HR2"):
    rows = []
    for r in spec["history_records"][rec]:
        a_ = r["offset"]; b_ = a_ + r["size"] - 1
        rows.append([f"{a_}" if a_ == b_ else f"{a_}–{b_}", f"`{r['name']}`", r["rule"]])
    t = t.replace("{{%s}}" % rec, table(["Bytes", "Field", "Content"], rows))
t = t.replace("{{HWREQ}}", "\n".join(f"- {h}" for h in spec["hardware_requirements_for_codex"]))
t = t.replace("{{BLOCKERS}}", table(["Item", "Blocked by"], [[b["item"], b["blocked_by"]] for b in spec["blockers"]]))

NL2 = chr(10) * 2
t = t.replace("{{HALREG}}", table(["Pin", "Type", "Dir", "Source", "Published by"],
    [[f"`{h['name']}`", h["type"], h["dir"], h["source"], "cnc1 (real time)" if h["realtime"] else "service / other component"] for h in spec["hal_pins"]]) +
    NL2 + "Index placeholders: " +"; ".join(f"`{{{k}}}` = " + (f"{v[0]}–{v[1]}" if isinstance(v[0], int) else ", ".join(v)) for k, v in spec["hal_index"].items()) + ".")
t = t.replace("{{TELMAP}}", table(["Logical name", "Mirror source", "Page", "Bytes", "Age from", "Rate", "Stale after (ms)"],
    [[f"`{m['logical']}`", m["source"], m["page"], m["bytes"], m["age"], m["rate"], m["stale_ms"]] for m in spec["telemetry_map"]]) + NL2 +
    table(["Host-side name", "Source", "Rate", "Stale after (ms)"],
    [[f"`{h['logical']}`", h["source"], h["rate"], "-" if h["stale_ms"] is None else h["stale_ms"]] for h in spec["host_sources"]]))
left = re.findall(r"\{\{[A-Z0-9_:a-z]+\}\}", t)
assert not left, left
out = os.path.join(DEST, "docs", "interface-spec", "01-protocol-and-schedule.md")
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(t)
print("wrote", out, len(t))
