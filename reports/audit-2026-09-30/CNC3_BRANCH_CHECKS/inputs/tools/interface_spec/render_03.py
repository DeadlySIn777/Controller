"""Render docs/interface-spec/03-terminals-and-allocations.md (IS-1) from spec/terminals.json and spec/allocations.json.

usage: python tools/interface_spec/render_03.py [root]   (root defaults to the repository)
The JSON files are the frozen IS-1 source; this script only renders the markdown from them.
"""
import json, os, sys, re

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = json.load(open(os.path.join(ROOT, "spec", "terminals.json"), encoding="utf-8"))
AL = json.load(open(os.path.join(ROOT, "spec", "allocations.json"), encoding="utf-8"))

def esc(s):
    if s is None:
        return "-"
    return str(s).replace("|", "/").replace("\n", " ")

def res_txt(r):
    k = r["kind"]
    if k == "fpga_pin":
        b = f" ball {r['ball']}" if r.get("ball") else " (ball unassigned)"
        return f"FPGA {r['signal']}{b}"
    if k == "serial_io":
        return f"serial {r['link']} bit {r['bit']}"
    if k == "host":
        return "host: " + r["resource"]
    return "-"

L = []
w = L.append
w("Interface specification revision: IS-1")
w("")
w("# 03 - Field terminals and machine allocations")
w("")
w("Section 03 of interface specification IS-1, written 28 September 2026. Machine-readable companions: `spec/terminals.json` and `spec/allocations.json` (both `\"spec_revision\": \"IS-1\"`). Codex's hardware and Claude's implementation both build against this revision; a change needs a new revision identifier (IS-2), not an in-place edit.")
w("")
w("**Status: specification only.** Nothing in this section is implemented, built, measured or ready for manufacture. No schematic, PCB, gateware or driver change is claimed. Every electrical figure is a proposed target, a datasheet value or arithmetic, labelled as such. Codex owns the schematics, power/protection, connectors, PCB and hardware BOM that realise these terminals; Claude owns the FPGA logic, CNC1 protocol/driver and configuration-service integration that consume them. Both reference IS-1.")
w("")
w("Machine-readable sources: [`spec/terminals.json`](../../spec/terminals.json) (every field terminal with all columns) and [`spec/allocations.json`](../../spec/allocations.json) (allocation sheets with counts). The tables below are rendered from those files; if they ever disagree, the JSON wins and the disagreement is a defect.")
w("")
w("## 1. Evidence classes used here")
w("")
w("| Class | Meaning in this section |")
w("|---|---|")
for k, v in T["evidence_classes"].items():
    w(f"| {k} | {v} |")
w("")
w("No ERC, DRC, SPICE, HDL simulation, synthesis or physical measurement exists for anything specified in this section. The six-joint/two-encoder terminal map (`hardware/terminal-map.csv`, 96 positions) is historical baseline evidence and is superseded here as the product target; it is not relabelled.")
w("")
w("## 2. Decisions made in this section (delegated engineering authority)")
w("")
w("Section 04 (safety, permission, power and fault timing) fixes the enable circuit, its parts, the motor-plug signal set, the AUX loop supplies, the permission nets and the field-entry split. This section adopts those decisions unchanged and fixes the contact numbers, connector parts, card ownership and allocations around them.")
w("")
w("| # | Decision | Reason | Cost direction (numbers unknown unless stated) | Standard or option |")
w("|---|---|---|---|---|")
dec = [
 ("D03-1", "One fixed wiring base (BASE) carries every standard field terminal. It is passive copper (terminals, fuse holders, chassis/shield bonding, card slots) with no semiconductors; TVS, limiters and isolators sit on the replaceable card next to its slot connector.",
  "A failed protection part is replaced with its card, never by rewiring. The short unprotected run from terminal to card is accepted and must pass the ESD/surge tests of the qualification plan.", "Base PCB + terminal set on every unit; card connectors per slot (unpriced)", "Standard"),
 ("D03-2", "Terminal family: Phoenix Contact COMBICON MC 1,5 (3.81 mm) pluggable headers with screw-flange plugs for all signal and I/O groups; MSTB 2,5 (5.08 mm) for the three 24 V entries. Item numbers verified on manufacturer/distributor listings (section 4).",
  "Pluggable plugs let the whole base be replaced without disturbing individual wires; flange screws resist vibration. One family keeps tooling and spares simple. Contact ratings (8 A nominal, 160 V for MC 1,5) are far above every signal load; the power entries use the larger family, derated by Codex against the 10 A-class requirement of section 04.", "Header + plug per connector; price not yet recorded", "Standard"),
 ("D03-3", "Motor plug = 14 positions, 13 used; IS-1 contact numbers for Codex's connector map: 1 STEP+, 2 STEP-, 3 DIR+, 4 DIR-, 5 SIG_0V, 6 SHIELD, 7 empty gap, 8 EN_NO, 9 EN_COM, 10 EN_NC, 11 AUX_5V, 12 AUX_24V, 13 AUX_RTN, 14 ALARM_IN (signal set and parts from section 04 section 3.5).",
  "Both enable polarities with correct power-loss behaviour (TLP3640A form A + TLP4176A form B on one LED current); AUX_5V/AUX_24V from FIELD keep a DM542T V4 disabled on LOGIC power loss; LOGIC contacts 1-5 separated from floating/FIELD contacts by the shield and an empty position. Supersedes the 10-contact order of MOTION_EXPANSION section 7.2.", "14-way plug instead of 10-way; two photorelays per channel", "Standard (all 12 channels)"),
 ("D03-4", "Channels 8-11 and encoders 4-11 terminate on an expansion terminal board XTB, fitted once (factory-fitted on twelve-motor units) and then part of the fixed wiring; the MX4 and EX8 electronics cards plug in behind it.",
  "Eight-motor units do not pay for 4 unused motor plugs and 8 encoder plugs, while a twelve-motor unit's field terminals never move when MX4 or EX8 is replaced.", "XTB board + 12 headers only on expanded units", "Option (twelve-motor / encoder expansion)"),
 ("D03-5", "Encoder expansion EX8 provides ENC4-ENC11, so a twelve-motor unit has one encoder per motor (12 total) with MX4 and EX8 fitted at the same time.",
  "Nobody chooses between twelve motors and their feedback. Matches the expanded target's 'eight additional ABZ ports; twelve total' and the encoder-expansion power reservation of section 04 section 10.1.", "EX8 card (6 quad receivers, 8 supply limiters, own converter) + 24 FPGA pins", "Option"),
 ("D03-6", "Three 24 V entries with their own plugs: XP1 CORE (4 A class), XP2 FIELD_A (DO0-DO7, AUX supplies, probes), XP3 FIELD_B (DO8-DO15, DI and safety sensor supplies). Loads and limits are section 04 section 10's.",
  "16 x 0.5 A = 8 A cannot come through the single 6 A entry; splitting keeps every output at its full rating without raising any limit.", "One more entry branch (Codex's TPS26630 topology repeated)", "Standard"),
 ("D03-7", "General DO terminals use the T1 driver selected in section 02 section 11.2: TPS274C65ASRHAR (integrated 10-bit ADC; per-channel current, VOUT and FET temperature; on/off-state open-load; short-to-supply; adjustable current limit). TPS274C65BS is excluded (its datasheet comparison table lists no ADC and no current sense).",
  "Per-channel digital current, on/off-state open-load, short-to-supply, current limit, thermal and VS/VOUT/temperature over SPI fit the serial DO-card transport; section 02 section 11.2 holds the full comparison against TPS4H160BQPWPRQ1 plus external acquisition.", "Driver price not recorded (unknown, not zero); one isolator per card instead of three", "Standard"),
 ("D03-8", "Channel names are 0-based everywhere (M0-M11, ENC0-ENC11, DI0-DI23, DO0-DO15) on silkscreen, UI, HAL and CNC1. HAL prefixes follow the existing cnc1 driver: `cnc1.N.*` per motor channel, `cnc1.encoder.N.*` per encoder.",
  "One name per wire from terminal to software removes a common wiring error; matches the existing driver's pin names.", "None", "Standard"),
 ("D03-9", "Handwheel port = XH1 (differential or single-ended A/B with a 2.5 V bias terminal, enable button) + XH2 (10 selector inputs). MPG A/B use receiver channels 15-16 of the four base quad receivers.",
  "A dedicated port that never consumes a general DI or an encoder port.", "Shift register + bias network on EIA", "Standard"),
 ("D03-10", "XF measurement-module port = FREQ0/1 differential inputs + 5 V supply + module presence + 1-Wire identity line.",
  "The plasma divided-voltage module (and later measurement modules) is identified and presence-checked through its own plug; raw arc voltage never reaches the controller.", "1-Wire bridge on EIA", "Standard"),
 ("D03-11", "XS1 machine safety interface on the digital-input card (DIC): EXT_PERMIT and PROCESS_PERMIT hard-wired into the permission chain (section 04 section 6), chain status, deliberate reset/arm with lamp, contactor and STO feedback, and a PERMIT_OUT contact that follows TX_PERMIT.",
  "Gives the machine safety design a monitored hand-off without making the controller a safety controller. PERMIT_OUT adds one TX_PERMIT receiver, now listed in the section 04 section 6.3 fan-out table (integration item R03-1, closed).", "ISO1212 channels + one photorelay", "Standard"),
 ("D03-12", "Analog outputs AO0/AO1 each get their own isolation domain; the four AI share one isolated group with software-selected 0-10 V / 4-20 mA ranges.",
  "Two VFDs or process devices with different commons connect without a ground loop; AI sensors usually share one supply.", "Second isolated AO supply", "Standard"),
]
for d in dec:
    w("| " + " | ".join(esc(x) for x in d) + " |")
w("")
w("### 2.1 Enable and process-contact parts (from section 04, verified there)")
w("")
w("| Function | Part | Values used here | IS-1 published rating |")
w("|---|---|---|---|")
w("| Normally-open enable, process contacts, PERMIT_OUT | Toshiba TLP3640A(TPL,E), 1-Form-A photorelay | 60 V, 1 A, RON <= 0.3 ohm (section 04 section 3.1, datasheet) | AC or DC 0-30 V, <= 50 mA |")
w("| Normally-closed enable | Toshiba TLP4176A(TP,F), 1-Form-B photorelay | 60 V, 0.5 A, RON <= 2.5 ohm (section 04 section 3.1, datasheet) | AC or DC 0-30 V, <= 50 mA |")
w("")
w("One LED current drives both switches of a channel (section 04 section 3.2). With no command, no TX_PERMIT or no LOGIC power the LEDs are dark: **EN_NO open, EN_NC closed**. States and exceptions E1-E5 are normative in section 04 sections 3.3-3.4; the configuration service shows them in the wiring guide.")
w("")
w("**DM542T V4 reference drive, supported (wiring mode NC-5V):** XMn.1/2 -> PUL+/PUL-, XMn.3/4 -> DIR+/DIR- (drive switch S2 set to 5 V; opto drive compatibility is profile test TT-XMn-01..04), XMn.11 AUX_5V -> ENA+, ENA- -> XMn.10 EN_NC, XMn.9 EN_COM -> XMn.13 AUX_RTN, XMn.12 AUX_24V -> ALM+, ALM- -> XMn.14 ALARM_IN, `alarm_on_no_current` = 1. The drive is disabled whenever the channel is disarmed and when the controller's LOGIC power is lost with FIELD present. The profile carries section 04's timing (ENA leads DIR by >= 200 ms, 2.5 us high/low, 5 us DIR setup, <= 200 kHz).")
w("")
w("## 3. Domains, returns and bonding")
w("")
w("| Domain | Terminals | Reference | Crosses to LOGIC through |")
w("|---|---|---|---|")
w("| CORE_24V | XP1 | CORE 0 V (logic converter input side) | Converter (Codex core_converter) |")
w("| LOGIC_TX | STEP/DIR pairs, SIG_0V, PWM | LOGIC_GND (non-isolated RS-422) | Direct; AM26C31 / buffer |")
w("| LOGIC_ENC | Encoder, MPG and FREQ lines and their 5 V supplies | LOGIC_GND (non-isolated) | Direct; receivers |")
w("| FIELD_A | DO0-DO7, AUX_5V/AUX_24V/AUX_RTN, ALARM_IN, probes | FIELD_A 0 V (not tied to LOGIC on the controller) | ISO1212, isolators, TPS274C65ASRHAR SPI isolation (ISO7762FDBQR) |")
w("| FIELD_B | DO8-DO15, DI0-DI23, sensor supplies, XS1 safety interface | FIELD_B 0 V | ISO1212, isolators |")
w("| ISO_SW | EN_NO/EN_COM/EN_NC, process contacts, PERMIT_OUT | Floating (each contact isolated) | Photorelay barrier |")
w("| ISO_AO0, ISO_AO1, ISO_AI | Analog outputs (one domain each), analog-input group | Own isolated commons | Isolated converters/isolators on ACC |")
w("| ISO_485, ISO_CAN | Field buses | Own isolated commons | Isolated transceivers on ACC |")
w("| CHASSIS | SHIELD contacts, SB1 clamp rail, XPE1 | Protective earth | Never a signal return |")
w("")
w("The motor plug carries LOGIC_TX (1-5), CHASSIS (6), an empty gap (7), ISO_SW (8-10) and FIELD_A (11-14). Creepage/clearance between SIG_0V and any floating or FIELD contact must suit 60 V working voltage (section 04 section 3.5); at 3.81 mm pitch the empty position 7 gives 7.62 mm between contacts 6 and 8 (arithmetic, pitch only; Codex checks the real PCB and plug geometry). Shield drains terminate at the controller end only (SB1 clamp rail bonded to XPE1).")
w("")
w("## 4. Connector summary")
w("")
w("| Connector | Location | Pos | Header / plug (Phoenix item) | Owning card | Fitted | Purpose |")
w("|---|---|---:|---|---|---|---|")
for c in T["connectors"]:
    w(f"| {c['id']} | {esc(c['location'])} | {c['positions']} | {esc(c['header_mpn'])} / {esc(c['plug_mpn'])} | {c['owner_card']} | {esc(c['fitted'])} | {esc(c['purpose'])} |")
w("")
w(f"Totals (arithmetic): {T['counts']['field_connectors']} field connectors, {T['counts']['field_terminals']} field terminals; {T['counts']['standard_unit_terminals']} on a standard eight-motor unit, {T['counts']['expansion_terminals']} added by XTB (XM8-XM11, XE4-XE11). Connector item numbers are proposals to Codex (connector owner): verified as orderable catalogue items, not yet footprint-approved or derated for this design. Coding profiles (so that no plug fits a wrong header of the same size) are Codex's selection; the rule is stated per connector in `terminals.json`.")
w("")
base_pos = sum(c["positions"] for c in T["connectors"] if c["location"].startswith("fixed base") and "MC 1,5" in c["family"])
xtb_pos = sum(c["positions"] for c in T["connectors"] if c["location"].startswith("expansion terminal board"))
w(f"Edge length (arithmetic, pitch only, no flange/gap allowance): {base_pos} MC 1,5 positions on the base x 3.81 mm = {base_pos*3.81:.0f} mm; {xtb_pos} positions on XTB = {xtb_pos*3.81:.0f} mm; plus three MSTB 4-way entries at 5.08 mm. The base therefore needs its terminals on more than one edge or in two tiers (motor/encoder row, I/O row, process/analog/communication/safety row, power edge); the mechanical arrangement is Codex's, the row grouping above is fixed.")
w("")
w("### 4.1 Card ownership")
w("")
w("| Card | Contents |")
w("|---|---|")
for k, v in T["cards"].items():
    w(f"| {k} | {esc(v)} |")
w("")
w("Card names are the IS-1 names of section 02 (slot map in section 02 section 3), which adopted this list unchanged.")
w("")
w("## 5. Terminal tables")
w("")
w("Columns rendered here: position, net, function, domain, electrical target, FPGA/serial resource, CNC1 field, HAL pin, power-up state, fault state, test id. The UI label, protection and owning card of each terminal are in `terminals.json` (the UI label equals the silkscreen text). Update class: `servo` = carried every 1 ms exchange (T2); `telemetry` = sampled locally, timestamped, reported with age; `none` = passive.")
w("")
groups = {}
for t in T["terminals"]:
    groups.setdefault(t["connector"], []).append(t)
seen_motor_template = False
for c in T["connectors"]:
    cid = c["id"]
    rows = groups[cid]
    if cid.startswith("XM") and cid != "XM0" and cid != "XM8":
        continue
    if cid.startswith("XE") and cid not in ("XE0", "XE4"):
        continue
    title = cid
    if cid == "XM0":
        title = "XM0 (template for XM0-XM7 on the base: replace 0 by n; owner MIA)"
    elif cid == "XM8":
        title = "XM8 (template for XM8-XM11 on XTB: replace 8 by n; owner MX4; permission TX_PERMIT_B)"
    elif cid == "XE0":
        title = "XE0 (template for XE0-XE3 on the base; owner EIA)"
    elif cid == "XE4":
        title = "XE4 (template for XE4-XE11 on XTB; owner EX8)"
    w(f"### {title}")
    w("")
    w(f"{esc(c['purpose'])}. Keying: {esc(c['keying'])}. Cable: {esc(c['cable_and_shield'])}.")
    w("")
    w("| Pos | Net | Function | Domain | Electrical target | Resource | CNC1 field | HAL pin | Power-up | Fault state | Update | Test |")
    w("|---:|---|---|---|---|---|---|---|---|---|---|---|")
    for t in rows:
        upd = t["update"]["class"] if t.get("update") else "-"
        w(f"| {t['position']} | {t['net']} | {esc(t['function'])} | {t['domain']} | {esc(t['electrical_target'])} | {esc(res_txt(t['resource']))} | {esc(t['cnc1_field'])} | {esc(t['hal_pin'])} | {esc(t['power_up_state'])} | {esc(t['fault_state'])} | {upd} | {t['test_id']} |")
    w("")
w("Every motor connector XM0-XM11 and encoder connector XE0-XE11 has its own complete rows in `terminals.json` (nets, FPGA signal names and Codex candidate balls differ per channel). FPGA balls quoted are Codex's candidate allocation (`hardware/fpga_core/pin-allocation.json`, candidate `minimum8_expand12_t20f256`, status candidate_not_vendor_fitted; source inspection). Signals without a ball (EN via `DRIVE_ENABLE#_FPGA_RESERVED` excepted) are new IS-1 requirements on Codex's pin plan.")
w("")
w("### 5.1 Test ids")
w("")
w("Test id `TT-<connector>-<position>` applies the procedure of the terminal's function class. These are commissioning/qualification procedures to be run on built hardware; none has been run.")
w("")
w("| Function class | Procedure and pass condition |")
w("|---|---|")
for k, v in T["test_procedures"].items():
    w(f"| {k} | {esc(v)} |")
w("")
w("### 5.2 Correction (2) as it applies at the terminal")
w("")
w("STEP/DIR outputs have two legal states under fault: driven by the stepgen, or high-impedance through hardware permission. The normative rule and its circuit (output-path-interruption latches, filtered module terms, pos_continuity, unhoming) are section 04 section 4; at the terminal it means any interruption of an active pulse train is a latched fault with the affected joints unhomed, and a noise pulse rejected by an input filter never changes any output pin. The bank-B Ioff-buffer OE therefore follows the filtered module terms (section 04 section 6.2), superseding the unfiltered OE of MOTION_EXPANSION section 7.3.1, and its qualified OE net also clears the OPI_BOE latch; every AM26C31 STEP/DIR input on the MIA and MX4 has a 10 kohm pull-down, so a floating input rests at the idle level. XS1.3 gates only the process-enable contacts XPC0/XPC1.")
w("")
w("## 6. Diagnostics at output and supply terminals (T4 display rule)")
w("")
w("Rule applied to every row: a displayed measurement carries validity and age; a missing sense path shows **unavailable**, a reading older than its source's fixed stale limit (`stale_ms` in the telemetry map and host-source tables of section 01 section 8.1a; for example 100 ms for output current, 5 s for 1 Hz card temperatures) shows **stale**, and neither is ever shown as 0. This is the single stale rule of section 01 section 3.12. Measured facts (for example 'DO7 overcurrent, 1.9 A, 12:03:04') are stored and shown separately from any diagnosis text; guidance text below is a suggested next test, not a fact.")
w("")
w("| Terminal type | Current | Open load | Short / overcurrent | Thermal | Supply voltage | Shown to the user as | Terminal-level guidance |")
w("|---|---|---|---|---|---|---|---|")
shown = set()
for t in T["terminals"]:
    d = t.get("diagnostics")
    if not d or "see" in d:
        continue
    label = {"motion_output": "STEP/DIR", "enable_switch": "Enable NO/NC", "supply": "Supply", "general_output": "General DO", "power": "Power entry",
             "bond": "PE bond", "process_output": "PWM output", "analog_output": "Analog output", "analog_input": "Analog input",
             "fieldbus": "Field bus", "permission_output": "PERMIT_OUT", "feedback_input": "Encoder line"}.get(t["function_class"], t["function_class"])
    if t["connector"].startswith("XPC"):
        label = "Process contact"
    fam = re.sub(r"\d+", "n", t["net"])
    if (label, fam) in shown:
        continue
    shown.add((label, fam))
    w(f"| {label}: {t['connector']}.{t['position']} ({t['net']}; family {fam}) | {esc(d['current'])} | {esc(d['open_load'])} | {esc(d['short'])} | {esc(d['thermal'])} | {esc(d['supply_voltage'])} | {esc(d['shown_as'])} | {esc(d['guidance'])} |")
w("")
w("Output-current accuracy is stated only across the declared range (0.10-0.50 A per DO channel) from the TPS274C65 ISNS table (datasheet arithmetic); it must be verified by measurement at 0.10, 0.25 and 0.50 A per channel and at the bank's temperature extremes, not at one convenient load (test TT-DO-ACC: per channel, resistive loads drawing 0.10, 0.25 and 0.50 A, reference ammeter in series, at minimum and maximum rated ambient; pass = reading inside the stated datasheet band and flagged valid). Enable contacts, process contacts and PERMIT_OUT have no contact-state measurement in the standard product; the UI therefore labels them 'commanded (not measured)'. A per-channel enable readback would cost 12 FPGA pins plus 12 sense circuits and is recorded as an optional improvement, not fitted.")
w("")
w("## 7. Field power arithmetic (proposal, not a rating)")
w("")
fb = T["field_power_budget"]
for ent in ("FIELD_A", "FIELD_B"):
    w(f"- **{ent}:** {fb[ent]['loads']}; **{fb[ent]['total_a']} A** continuous; entry current-limit minimum {fb[ent]['entry_current_limit_min_a']} A.")
w(f"- **CORE:** {fb['CORE']['input_a_at_18v_12_motors_plus_encoder_expansion']} A at 18 V with twelve motors and the encoder expansion; entry current-limit minimum {fb['CORE']['entry_current_limit_min_a']} A (4 A class).")
w(f"- Source and basis: {fb['source']}. {fb['basis']} Per-output 0.5 A, 2.0 A per 4-output group, driver current-limit maximum <= 1.0 A are enforced in hardware and by the configuration validator (section 04 section 10.2); the allocation sheets below check the 2.0 A group limit against declared loads.")
w("")
w("## 8. Non-field and service connectors")
w("")
w("| Id | Type | Owner | Function | Domain | Diagnostics | Fault behaviour |")
w("|---|---|---|---|---|---|---|")
for o in T["other_connectors"]:
    w(f"| {o['id']} | {esc(o['type'])} | {esc(o['owner_card'])} | {esc(o['function'])} | {esc(o['domain'])} | {esc(o['diagnostics'])} | {esc(o['fault_behaviour'])} |")
w("")
w("## 9. Allocation sheets")
w("")
w("Each sheet assigns every function of an advertised machine to a physical terminal and carries a machine-readable HAL mapping (joint and axis per motor, the single motor-pos-fb source per joint, the pins every input writes, the single writer of every output, homing groups, probe net and spindle run paths); the validator builds the net list from it and rejects double use, capacity overflow and any pin with two writers. Counts are arithmetic from the sheet. Every sheet also uses the XS1 safety interface (external permit, process permit, chain status, reset/arm, contactor and STO feedback, PERMIT_OUT). Output fault states follow section 04 section 9 (de-energised on permission loss; workholding must be spring-applied or bistable; drawbar energise-to-release). DO group currents use stated example loads (valve 0.25 A, 24 V LED lamp 0.1 A, relay coil 0.05 A, brake 0.5 A max; pumps through an interposing relay) and must be replaced by the selected device profiles. Every DO also carries a declared start (peak) current: a load whose peak exceeds the 0.62 A minimum current-limit setting needs an interposing relay, because the card rejects the inrush modes and a current-limit event latches the output off.")
w("")
w("| Sheet | Hardware | Fits | Motors used/spare | Encoders | DI | DO | Probes | FREQ | PWM | Proc. enables | AO | AI | DO groups 0-3/4-7/8-11/12-15 assumed all-on A (limit 2.0 each) | Not-fitting variants |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for a in AL["configurations"]:
    c = a["counts"]
    def uc(k):
        return f"{c[k]['used']}/{c[k]['spare']}"
    bk = list(a["do_group_current_check"].values())
    nf = "; ".join(v["id"] for v in a["variants_not_fitting"]) or "-"
    w(f"| {a['id']} | {esc(a['hardware'])} | {'yes' if a['fits'] else 'NO'} | {uc('motor')} | {uc('encoder')} | {uc('di')} | {uc('do')} | {uc('probe')} | {uc('freq')} | {uc('pwm')} | {uc('proc_en')} | {uc('ao')} | {uc('ai')} | {' / '.join(str(x['assumed_all_on_a']) for x in bk)} | {nf} |")
w("")
for a in AL["configurations"]:
    w(f"### {a['id']}: {esc(a['title'])}")
    w("")
    w(f"Hardware: {esc(a['hardware'])}. Interpretation: {esc(a['interpretation'])} LinuxCNC mapping: {esc(a['linuxcnc_mapping'])}.")
    w("")
    w("| Function | Class | Channel | Terminal | Assumed load / peak | LinuxCNC mapping |")
    w("|---|---|---:|---|---|---|")
    for x in a["assignments"]:
        load = f"{x['assumed_load_a']} A / {x['peak_a']} A" + (" (relay)" if x.get('via_relay') else "") if "assumed_load_a" in x else "-"
        note = f" ({esc(x['note'])})" if x.get("note") else ""
        h = x.get("hal", {})
        if "joint" in h:
            hm = f"joint {h['joint']} ({h['axis']}{', extra joint' if h['extra_joint'] else ''}); motor-pos-fb {h['pos_fb']}"
        elif "targets" in h:
            hm = "; ".join(h["targets"])
        elif "writer" in h:
            hm = f"written by {h['writer']}"
        elif "axis" in h:
            hm = f"axis {h['axis']}"
        else:
            hm = "-"
        w(f"| {esc(x['function'])}{note} | {x['resource_class']} | {x['channel']} | {x['terminal']} | {load} | {esc(hm)} |")
    hmap = a.get("hal_map", {})
    if hmap:
        w("")
        w(f"- Joints: {hmap['kinematic_joints']} kinematic + {hmap['extra_joints']} extra = {hmap['joints_total']}. Homing groups: " + "; ".join(f"{g['axis']} joints {g['joints']} HOME_SEQUENCE {g['home_sequence']}" for g in hmap['homing_groups']) + ".")
        pn = hmap['probe_net']
        w(f"- Probe net: {pn['mode']} - {esc(pn['rule'])}.")
        if hmap['spindles']:
            w("- Spindles: " + "; ".join(f"spindle.{sp['id']} run {', '.join(sp['run_paths'])}, speed {sp['speed']}, at-speed {sp['at_speed']}, feedback {sp['feedback'] or 'none'}" for sp in hmap['spindles']) + ".")
        w(f"- Process interlock (XS1.3): {esc(a.get('process_interlock_scope', ''))}")
        for n in hmap.get('notes', []):
            w(f"- Note: {esc(n)}.")
    w("")
    spare = ", ".join(f"{k} {v['spare']}" for k, v in a["counts"].items() if v["spare"] and k not in ("pendant_sel",))
    w(f"Spare after allocation: {spare or 'none'}. Pendant selector inputs used: {a['counts']['pendant_sel']['used']} of 10.")
    for v in a["variants_not_fitting"]:
        w("")
        w(f"**Does not fit - {v['id']}:** {esc(v['reason'])} Resolution: {esc(v['resolution'])}")
    if a.get("optional"):
        w("")
        w("Optional additions checked against spare capacity: " + "; ".join(esc(o) for o in a["optional"]) + ".")
    if a.get("safety_note"):
        w("")
        w(f"Safety note: {esc(a['safety_note'])}")
    w("")
w("## 10. Resource demand created by these terminals")
w("")
d = T["fpga_demand"]
w(f"- Direct FPGA signals from field terminals (12 motors, 12 encoders fitted): **{d['direct_field_signals']}** (STEP 12, DIR 12, EN_N 12, ALM 12, encoder A/B/Z 36, FREQ 2, MPG A/B 2, probes 2, PWM 2, process enables 2, XS1 status/feedback 6, arm lamp 1).")
w(f"- Serial-link pins: " + ", ".join(f"{k} {v}" for k, v in d["serial_link_pins"].items()) + f" = **{d['serial_link_pin_total']}**. Total field-driven FPGA pins **{d['total_field_driven_fpga_pins']}** (arithmetic).")
w(f"- {esc(d['basis'])}")
w("- Differential receiver channels: 16 on the base (ENC0-3 ABZ 12 + FREQ 2 + MPG 2 = four quad receivers, no spare channel) and 24 on EX8 (six quad receivers).")
w("- Protocol fields: every servo-class terminal above needs its CNC1 field in every servo exchange (T2); telemetry-class rows need a telemetry-page field with timestamp/age. Section 01 carries all of them for 12 motors and 12 encoders simultaneously (CNF3/CNS3 field sets, telemetry map), and `tools/interface_spec_validate.py` checks that every CNC1 and HAL name in `terminals.json` resolves to section 01.")
w("")
w("## 11. Blockers and dependencies (exact)")
w("")
w("| Item | Blocked by | What continues meanwhile |")
w("|---|---|---|")
blk = [
 ("FPGA pin fit of the 123 field-driven pins plus support pins on T20F256", "Efinix Efinity place-and-route (tool not installed here)", "Yosys technology mapping and the pin plan by bank/voltage"),
 ("Connector footprints, coding-profile items, creepage between motor-plug domains", "Codex schematic/PCB work (owner)", "Terminal/net list frozen here as IS-1"),
 ("Enable LED driver, TVS values, limiter parts for sensor/probe/alarm supplies", "Codex part selection and ERC", "Functional behaviour and ratings fixed here"),
 ("DM542T V4 opto-input compatibility with AM26C31 drive, enable/alarm polarity", "Physical drive + bench measurement (purchase)", "Profile text and tests TT-XMn-*"),
 ("DO current accuracy across 0.10-0.50 A, open-load thresholds, photorelay timing", "Built DO/MIA cards + measurement", "Datasheet arithmetic in section 6"),
 ("Encoder 10 M transitions/s, FREQ 1 MHz, probe capture latency", "Built EIA card + signal generator measurement", "HDL simulation of the decoders (gateware work)"),
 ("Field entry fuse, cable and PSU ratings (E-34)", "Codex power_entry selection + measurement", "Split-entry arithmetic in section 7"),
]
for b in blk:
    w("| " + " | ".join(esc(x) for x in b) + " |")
w("")
w("Reproduce: this file is rendered from `spec/terminals.json` and `spec/allocations.json` by `python tools/interface_spec/render_03.py`; the JSON files are the frozen IS-1 source (the author-time generator that first produced them is superseded by the integrated JSON and is not archived). `python tools/interface_spec_validate.py` checks that this rendering is current and runs the structural checks: unique terminal ids, every connector position 1..n populated exactly once, every allocation terminal present, no terminal or resource channel used twice in a sheet, no channel above capacity, every CNC1 and HAL name resolvable. These are specification checks, not hardware tests.")
w("")

os.makedirs(os.path.join(ROOT, "docs", "interface-spec"), exist_ok=True)
with open(os.path.join(ROOT, "docs", "interface-spec", "03-terminals-and-allocations.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L))
print("lines", len(L))
