"""Generate spec/modules.json and the derived tables of docs/interface-spec/02-modules-and-boundaries.md (IS-1).

Inputs: spec/terminals.json (section 03, field terminals and owning cards) and the data below.
Field-side conductor counts are computed from terminals.json; logic-side counts are arithmetic over
the listed signal groups. Cost lines carry an evidence class. Nothing here is implemented,
measured or ready for manufacture.

usage: python tools/interface_spec/gen_02.py [root] [template]  (defaults: the repository and 02-template.md beside this script)
"""
import collections
import json
import math
import sys
from pathlib import Path

WT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
TEMPLATE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "02-template.md"
REV = "IS-1"

TERM = json.loads((WT / "spec" / "terminals.json").read_text(encoding="utf-8"))
assert TERM["spec_revision"] == REV
TS = TERM["terminals"]
XTB_CONNECTORS = {c["id"] for c in TERM["connectors"] if "XTB" in c["location"]}
STD_TERMINALS = TERM["counts"]["standard_unit_terminals"]
XTB_TERMINALS = TERM["counts"]["expansion_terminals"]
ALL_TERMINALS = TERM["counts"]["field_terminals"]

# ---------------------------------------------------------------- connectors
CONNECTORS = {
    "C096": {
        "family": "DIN 41612 / IEC 60603-2 type C, 96 contacts (rows a, b, c), 2.54 mm grid",
        "card_part": "HARTING 09 03 196 6921 (DIN-Signal C096MS-3,0C1-2, male, angled); coded version 09 03 696 6921 (C096MS-3,0C1-2-cod)",
        "base_part": "HARTING 09 03 296 6825 (type C female, 96, straight, 4.5 mm solder pins)",
        "contacts": 96, "rated_a": 2.0, "design_a_per_contact": 1.0, "performance_level": "2 (IEC 60603-2)", "mating_cycles_min": 400,
        "verified": "HARTING product pages 09031966921 and 09032966421 (sister female part) opened 28 Sep 2026; 09 03 296 6825 description and GBP price on a Rapid Electronics page",
        "price": "female 09 03 296 6825: GBP 2.54 at 100+ ex VAT (Rapid page, opened); male 09 03 196 6921: $4.67-5.23 qty 1 (DigiKey search snippets, page not opened). No USD qty-100 price recorded",
    },
    "C032": {
        "family": "DIN 41612 / IEC 60603-2 type C, 32 contacts, 2.54 mm grid",
        "card_part": "HARTING 09 03 132 6921 (DIN-Signal C032MS-3,0C1-2, male, angled)",
        "base_part": "HARTING 09 03 232 6824 (DIN-Signal C032FS-2,9C1-2, female, straight)",
        "contacts": 32, "rated_a": 2.0, "design_a_per_contact": 1.0, "performance_level": "2 (IEC 60603-2)", "mating_cycles_min": 400,
        "verified": "HARTING product page 09031326921 opened; 09032326824 from a HARTING catalogue listing",
        "price": "not recorded",
    },
    "HB160": {
        "family": "HARTING har-bus 64 (IEC 61076-4-113), 160 contacts in rows z, a, b, c, d, 2.54 mm grid, same outline as type C",
        "card_part": "HARTING 02 04 160 1101 (female, right angle, solder)",
        "base_part": "HARTING 02 01 160 1101 (har-bus64-160MR-3,0C1-1-V4, male)",
        "contacts": 160, "rated_a": 1.0, "design_a_per_contact": 0.5, "performance_level": "1 (IEC 61076-4-113)", "mating_cycles_min": 500,
        "verified": "HARTING product pages 02011601101 and 02071601101 opened; 02041601101 gender and orientation from an RS listing. Codex confirms the mating drawing before layout",
        "price": "not recorded",
    },
    "H15": {
        "family": "DIN 41612 type H15 (DIN-Power), 15 contacts, 15 A",
        "card_part": "HARTING 09 06 115 2911 (DIN-Power H015MS-3,2C1-1, male, angled)",
        "base_part": "HARTING 09 06 215 2821 (DIN-Power H015FS4,0C1-1, female, straight, wave solder)",
        "contacts": 15, "rated_a": 15.0, "design_a_per_contact": 7.5, "performance_level": "1 (IEC 60603-2)", "mating_cycles_min": 500,
        "verified": "HARTING product page 09061152911 opened; 09062152821 from a HARTING catalogue listing",
        "price": "not recorded",
    },
}


# ---------------------------------------------------------------- field side from terminals.json
def field_nets(card, on_xtb=None):
    nets, seen = [], set()
    for t in TS:
        if t["owner_card"] != card:
            continue
        if on_xtb is not None and (t["connector"] in XTB_CONNECTORS) != on_xtb:
            continue
        if t["net"] not in seen:
            seen.add(t["net"])
            nets.append(t["net"])
    return nets


def count_pairs(nets):
    s, used, pairs = set(nets), set(), 0
    for n in nets:
        for a, b, pre in (("_P", "_N", ""), ("_H", "_L", "CAN"), ("_A", "_B", "RS485")):
            if n.endswith(a) and n.startswith(pre):
                m = n[: -len(a)] + b
                if m in s and n not in used:
                    pairs += 1
                    used.update({n, m})
    return pairs, len(nets) - 2 * pairs


def field_groups(card, on_xtb=False, extra=None):
    pairs, singles = count_pairs(field_nets(card, on_xtb))
    g = []
    if pairs:
        g.append((f"{card} field differential pairs (terminals.json)", "dp", pairs))
    g.append((f"{card} other field conductors (terminals.json; shields and spacing positions stay on the base)", "fld", singles))
    return g + (extra or [])


def rec(conn, n_conn, groups, note=""):
    total = CONNECTORS[conn]["contacts"] * n_conn
    used = sum(c * (2 if k == "dp" else 1) for _, k, c in groups)
    assert used <= total, (conn, used, total)
    tally = collections.Counter()
    for _, k, c in groups:
        tally[k] += c
    return {"connector": f"{n_conn} x {conn}" if n_conn > 1 else conn, "contacts_total": total, "contacts_used": used, "contacts_spare": total - used,
            "single_ended_signals": tally["se"], "differential_pairs": tally["dp"], "signal_returns": tally["ret"], "power_contacts": tally["pwr"],
            "field_conductors_other": tally["fld"], "presence_contacts": tally["pres"], "identity_bus_contacts": tally["id"],
            "groups": [{"group": g, "kind": k, "count": c, "conductors": c * (2 if k == "dp" else 1)} for g, k, c in groups if c], "note": note}


STD = [("presence A and B at opposite connector ends", "pres", 2), ("card power-good, open drain", "se", 1), ("identity I2C branch SDA/SCL", "id", 2)]


def logic(conn, groups, feed, extra=None, note="P1 logic"):
    s = sum(c for _, k, c in groups if k in ("se", "pres", "id"))
    g = groups + [("LOGIC_GND signal returns, 1 per 3 signals", "ret", math.ceil(s / 3)),
                  ("slot supply feed contacts", "pwr", feed), ("slot supply return contacts", "pwr", feed)] + (extra or [])
    return rec(conn, 1, g, note)


B = {}
MC_GROUPS = [
    ("STEP/DIR/EN_N M0-M7 to MIA through Ioff buffers on the MC", "se", 24),
    ("STEP/DIR/EN_N M8-M11 to MX4 through Ioff buffers on the MC (reserved)", "se", 12),
    ("ALM0-7 from MIA", "se", 8), ("ALM8-11 from MX4 (reserved)", "se", 4),
    ("ENC0-3 A/B/Z from EIA", "se", 12), ("ENC4-11 A/B/Z from EX8 (reserved)", "se", 24),
    ("FREQ0-1, MPG A/B, PRB0-1 from EIA", "se", 6), ("PWM0-1 and PEN0-1 commands to ACC", "se", 4),
    ("XS1 status/feedback from DIC: EXT_PERMIT, PROCESS_PERMIT, SAFETY_STATUS, RESET_ARM, CONTACTOR_FB, STO_FB", "se", 6),
    ("ARM_LAMP to DIC", "se", 1), ("IOL1 links L0-L3 to DIC, DOA, DOB, ACC (SCLK, CMD, RSP, CS_N each)", "se", 16),
    ("status shift registers EIA (3) and EX8 (3, reserved)", "se", 6), ("host SPI SCLK/MOSI/MISO/CS_FB/CS_CMD from CMC (section 01 D01-1)", "se", 5),
    ("MX4 status PRESENT_A/B, EXP_PGOOD, MOD_ID0-2 (reserved)", "se", 6), ("TAMPER_N from PSM", "se", 1),
    ("MIA status PRESENT_A/B, PGOOD", "se", 3), ("OPI_OK_A, OPI_OK_B, OPI_REARM", "se", 3), ("RAILS_OK from PSM", "se", 1),
    ("slot presence A/B and power-good to the MC slot status register: EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC, XS (27) and SCART presence A/B (2); the DIC lines also feed the DIC_OK filter of base_ok", "se", 29),
    ("XS link (4) + SYNC_STROBE + XS_REFCLK (reserved)", "se", 6),
    ("TX_PERMIT_A to MIA; TX_PERMIT_B (Ioff copy) to MX4", "se", 2),
    ("OUT_PERMIT_DOA, OUT_PERMIT_DOB, OUT_PERMIT_ACC (own driver and pull-down each)", "se", 3),
    ("PROC_PERMIT to ACC", "se", 1), ("PERMIT_OUT drive to DIC photorelay", "se", 1), ("XS_PERMIT (reserved)", "se", 1),
    ("configuration-flash restore path from CMC: SCK, MOSI, MISO, CS_N, CRESET_N, CDONE, BUS_SEL", "se", 7),
    ("MOTION_DISARMED observation to ESC", "se", 1),
] + STD
mc_sig = sum(c for _, k, c in MC_GROUPS if k in ("se", "pres", "id"))
B["MC"] = [rec("HB160", 2, MC_GROUPS + [("LOGIC_GND signal returns, 1 per 3 signals", "ret", math.ceil(mc_sig / 3)),
                                         ("CORE_5V feed (0.5 A/contact design)", "pwr", 4), ("CORE_5V return", "pwr", 4)],
               "P1+P2 pooled: P1 motion and feedback groups, P2 links, host, flash and supervision; rows z and d used as ground rows")]
B["MIA"] = [logic("C096", [("STEP0-7, DIR0-7, EN0-7_N", "se", 24), ("ALM0-7 (ISO1212 outputs)", "se", 8), ("TX_PERMIT_A", "se", 1), ("OPI_OK_A, OPI_REARM", "se", 2)] + STD, 2,
                  note="P1 logic; MOTION_5V feed"),
            rec("C096", 1, field_groups("MIA", False, [("FIELD_A 0 V reference for the ISO1212 field side", "pwr", 2)]), "P2 field")]
B["MX4"] = [logic("C096", [("STEP8-11, DIR8-11, EN8-11_N", "se", 12), ("ALM8-11", "se", 4), ("TX_PERMIT_B", "se", 1), ("OPI_OK_B, OPI_REARM", "se", 2),
                           ("MOD_ID0-2 straps", "se", 3)] + STD, 2, note="P1 logic; EXP_5V feed"),
            rec("C096", 1, field_groups("MX4", True, [("FIELD_A 0 V reference", "pwr", 2)]), "P2 field, routed on the base from the XTB connector")]
B["EIA"] = [logic("C096", [("ENC0-3 A/B/Z", "se", 12), ("FREQ0-1, MPG A/B, PRB0-1", "se", 6), ("status shift register CLK/LATCH/DATA", "se", 3)] + STD, 2,
                  note="P1 logic; MOTION_5V feed"),
            rec("C096", 1, field_groups("EIA", False, [("FIELD_A 24 V and 0 V for the probe supplies", "pwr", 2)]), "P2 field")]
B["EX8"] = [logic("C096", [("ENC4-11 A/B/Z", "se", 24), ("status shift register CLK/LATCH/DATA", "se", 3)] + STD, 2,
                  extra=[("CORE_24V expansion feed and return (own 5 V converter)", "pwr", 2)], note="P1 logic"),
            rec("C096", 1, field_groups("EX8", True), "P2 field, routed on the base from the XTB connector")]
B["DIC"] = [logic("C096", [("IOL1 link SCLK/CMD/RSP/CS_N", "se", 4), ("slot straps (4, base copper)", "se", 4), ("EXT_PERMIT, PROCESS_PERMIT, SAFETY_STATUS, RESET_ARM, CONTACTOR_FB, STO_FB", "se", 6),
                           ("ARM_LAMP", "se", 1), ("PERMIT_OUT drive", "se", 1)] + STD, 1, note="P1 logic"),
            rec("C096", 1, field_groups("DIC", False, [("FIELD_B 24 V feed for sensor/safety supplies and 0 V", "pwr", 4)]), "P2 field")]
for c, bank in (("DOA", "FIELD_A"), ("DOB", "FIELD_B")):
    B[c] = [logic("C032", [("IOL1 link SCLK/CMD/RSP/CS_N", "se", 4), ("slot straps (4, base copper)", "se", 4), (f"OUT_PERMIT_{c}", "se", 1)] + STD, 1, note="P1 logic"),
            rec("C032", 1, field_groups(c, False, [(f"{bank} bank feed to TPS274C65 VS (4 A over 5 contacts)", "pwr", 5)]), "P2 field")]
B["ACC"] = [logic("C096", [("IOL1 link SCLK/CMD/RSP/CS_N", "se", 4), ("slot straps (4, base copper)", "se", 4), ("PWM0-1, PEN0-1 commands", "se", 4), ("OUT_PERMIT_ACC, PROC_PERMIT", "se", 2),
                           ("RS-485 TX/RX/DE from CMC UART", "se", 3), ("CAN controller SPI SCLK/MOSI/MISO/CS_N/INT from CMC", "se", 5)] + STD, 2,
                  extra=[("CORE_24V feed and return for the three isolated supplies", "pwr", 2)], note="P1 logic"),
            rec("C096", 1, field_groups("ACC", False), "P2 field")]
B["PSM"] = [logic("C096", [("RAILS_OK, C_PGOOD, F_PGOOD_A/B, AUX24_OK_A/B, AUX5_OK_A/B", "se", 8), ("TAMPER_N", "se", 1), ("POWERFAIL_N to CMC", "se", 1),
                           ("ESP_CHIP_PU", "se", 1), ("PSM_ALERT_N", "se", 1), ("tamper-latch inputs: presence and PGOOD of MIA, MX4, EIA, EX8", "se", 12),
                           ("cartridge slot XCART1 pass-through to CMC: SDA/SCL, CART_WP_EN, CART_PRES_A/B", "se", 5),
                           ("XP1-XP3 remote shutdown inputs (terminals.json service_input nets)", "fld", 6)] + STD, 12,
                  extra=[("AUX_5V_A, AUX_24V_A, AUX_5V_B, AUX_24V_B bank buses (the base fans them out per motor)", "pwr", 4), ("MOTION_5V and EXP_5V feeds", "pwr", 6)],
                  note="P1: 12 switched CORE_5V feed contacts (CMC 4, MC 2, ESC 1, DIC 1, DOA 1, DOB 1, ACC 1, XS 1) and 12 returns"),
            rec("H15", 1, [("CORE_24V in and 0 V", "pwr", 2), ("FIELD_A 24 V in and 0 V", "pwr", 2), ("FIELD_B 24 V in and 0 V", "pwr", 2),
                           ("FIELD_A/FIELD_B bank feeds out and 0 V buses", "pwr", 4), ("CORE_24V_PROT out (ACC, EX8)", "pwr", 1), ("LOGIC_GND bus", "pwr", 2), ("PE/chassis", "pwr", 1)],
                "P2 power; the physical fuses are in holders on the base beside XP1-XP3 (section 03)")]
B["CMC"] = [logic("C096", [("host SPI SCLK/MOSI/MISO/CS_FB/CS_CMD to MC", "se", 5), ("MC configuration-flash restore path", "se", 7), ("ESP UART TX/RX and ESP_BOOT", "se", 3),
                           ("cartridge bus (dedicated): SDA/SCL, CART_WP_EN, CART_PRES_A/B", "se", 5),
                           ("identity I2C branches for 13 slots via 2 x TCA9548APWR", "id", 26), ("RS-485 UART and CAN SPI to ACC", "se", 8), ("POWERFAIL_N", "se", 1)] + STD, 4,
                  note="P1; XETH1, XDSP1, XUSB1/2 and XANT1 are on the card's bracket")]
B["ESC"] = [logic("C032", [("UART TX/RX", "se", 2), ("ESP_BOOT", "se", 1), ("ESP_CHIP_PU", "se", 1), ("RAILS_OK and MOTION_DISARMED observation", "se", 2)] + STD, 1,
                  note="P1; XUSB_SVC and XANT2 are on the card's bracket")]
B["SCART"] = [rec("C032", 1, [("cartridge I2C SDA/SCL", "id", 2), ("CART_WP_EN", "se", 1), ("presence A/B", "pres", 2), ("CART_3V3", "pwr", 2), ("LOGIC_GND", "pwr", 2)],
                  "XCART1 on the PSM bracket; dedicated cartridge bus, never an identity branch")]
B["XS"] = [logic("C096", [("card link", "se", 4), ("SYNC_STROBE, XS_REFCLK", "se", 2), ("XS_PERMIT", "se", 1)] + STD, 1,
                 extra=[("CORE_24V feed and return", "pwr", 2)], note="base connector only; reserved for a future synchronized module")]
xp, xs_ = count_pairs(field_nets("MX4", True) + field_nets("EX8", True))
B["XTB"] = [rec("HB160", 1, [("MX4 and EX8 field differential pairs", "dp", xp), ("MX4 and EX8 other field conductors", "fld", xs_),
                             ("AUX_5V_B and AUX_24V_B bank buses for XM8-XM11", "pwr", 2), ("FIELD_A 0 V (AUX return bus)", "pwr", 2)],
                "XTB to base, fitted once; shields bond to chassis through the XTB mounting studs")]

# ---------------------------------------------------------------- FPGA budget
FPGA = [
    ("STEP/DIR/EN_N/ALM M0-M11 (section 03)", 48, "M8-M11: 16 reserved for MX4"),
    ("ENC0-11 A/B/Z (section 03)", 36, "ENC4-11: 24 reserved for EX8"),
    ("FREQ, MPG A/B, probes, PWM, process enables (section 03)", 10, ""),
    ("XS1 status/feedback + ARM_LAMP (section 03)", 7, ""),
    ("serial links DIC/DOA/DOB/ACC + shift registers EIA/EX8 (section 03)", 22, "EX8 register: 3 reserved"),
    ("host SPI SCLK/MOSI/MISO/CS_FB/CS_CMD", 5, "two chip selects, section 01"), ("MX4 PRESENT_A/B, EXP_PGOOD, MOD_ID0-2 + TAMPER_N", 7, "6 reserved"),
    ("MIA PRESENT_A/B, PGOOD", 3, ""), ("OPI_OK_TX/A/B + OPI_REARM", 4, "OPI_OK_B reserved"), ("RAILS_OK readback", 1, ""),
    ("XS link + SYNC_STROBE + XS_REFCLK", 6, "reserved"),
    ("progress_m, progress_o, MOTION_REQUEST, OUTPUT_REQUEST, ENDPOINT_READY", 5, "local to MC"),
    ("WD_M_OK, WD_O_OK, TX/OUT/PROC_PERMIT readback", 5, "local to MC"), ("watchdog trip flags x2 + clear", 3, "local to MC"),
    ("clock, local reset", 2, "local to MC"), ("fault LEDs", 4, "local to MC"),
    ("MC slot status register SSR_CLK/SSR_LOAD_N/SSR_DATA", 3, "local to MC; section 01 section 4.10"),
    ("OPI_OK_BOE, OPI_OK_OUT, OPI_REARM_O", 3, "local to MC; section 04 section 4.2"), ("PERMIT_OUT_REQ", 1, "local to MC; section 04 section 6.2"),
]
FPGA_TOTAL = sum(p[1] for p in FPGA)
FPGA_FIELD = 48 + 36 + 10 + 7 + 22
FPGA_RESERVED = 16 + 24 + 3 + 6 + 1 + 6
FPGA_LOCAL = 5 + 5 + 3 + 2 + 4 + 1 + 3 + 3 + 1
assert FPGA_FIELD == TERM["fpga_demand"]["total_field_driven_fpga_pins"]

# ---------------------------------------------------------------- costs (qty-100 unit USD per line: low, high)
E, R = "estimate", "recorded price (research ladder, qty 100)"
HDR_LO, HDR_HI, PLG_LO, PLG_HI = 0.28, 0.36, 0.35, 0.60
C = {
    "BASE": [
        ("base PCB, 4 layers, about 360 x 280 mm", 1, 32, 60, E),
        ("female C096 slot connectors (PSM, CMC, MIA x2, MX4 x2, EIA x2, EX8 x2, DIC x2, ACC x2, XS)", 15, 3.0 * 15, 3.6 * 15, "estimate from observation GBP 2.54 @100"),
        ("female C032 (DOA x2, DOB x2, ESC)", 5, 1.5 * 5, 2.5 * 5, E), ("male har-bus 64 (MC x2, XTB)", 3, 8 * 3, 15 * 3, E),
        ("female H15 (PSM power)", 1, 4, 8, E),
        (f"field headers for the {STD_TERMINALS} standard positions (section 03 families)", STD_TERMINALS, HDR_LO * STD_TERMINALS, HDR_HI * STD_TERMINALS,
         "estimate from observation GBP 2.83 per 12-way MC 1,5 header @100 (3.5 mm sister family)"),
        ("fuse holders and fuses for XP1-XP3", 3, 3, 8, E), ("card guides, chassis bonding, SB1 clamp rail, card-cage frame and cover", 1, 25, 55, E),
        ("assembly (about 50 through-hole connectors), continuity test", 1, 14, 28, E),
    ],
    "PLUGS": [(f"field plugs for the {STD_TERMINALS} standard positions", STD_TERMINALS, PLG_LO * STD_TERMINALS, PLG_HI * STD_TERMINALS, "estimate; plug price not recorded")],
    "PSM": [
        ("PCB 4 layers 100 x 220 mm", 1, 6, 10, E), ("male C096", 1, 3.5, 4.7, "estimate from observation $4.67-5.23 qty 1"), ("male H15", 1, 5, 9, E),
        ("three entry eFuses TPS26630RGER with FETs and TVS (Codex topology)", 3, 9, 15, E), ("CORE_5V 6 A converter (Codex design)", 1, 6, 12, E),
        ("MOTION_5V >= 3 A converter", 1, 3, 6, E), ("AUX_5V/AUX_24V limiters and monitors, two banks", 1, 4, 8, E), ("8 switched slot feeds with fault flags", 8, 4.8, 9.6, E),
        ("TPS386000 supervision, sequencer, POR and tamper latches", 1, 4, 9, E), ("INA238AIDGSR entry monitors", 3, 6, 10, E), ("I2C expander for slot fault flags", 1, 0.5, 1.0, E),
        ("AT30TSE752A-XM8M-T", 1, 0.6, 1.0, E), ("female C032 cartridge slot XCART1 + guide", 1, 2, 4, E), ("passives, bracket, handle, retaining screw", 1, 4, 8, E),
        ("assembly, identity programming, test", 1, 6, 12, E),
    ],
    "CMC": [
        ("Raspberry Pi CM5 CM5102016 (2 GB/16 GB, wireless)", 1, 97.5, 97.5, "recorded retail price, qty 1 only; volume price unknown"),
        ("carrier PCB 6 layers", 1, 10, 18, E), ("module mates (2 x 100-way, Hirose DF40 class)", 2, 2, 4, E), ("RJ45 with magnetics", 1, 2, 4, E),
        ("USB-A x2 with current limit, HDMI, ESD", 1, 3, 6, E), ("TCA9548APWR x2", 2, 1.6, 3, E), ("male C096", 1, 3.5, 4.7, E),
        ("CM5 heatsink and fan", 1, 4, 8, E), ("certified CM4/CM5 antenna kit and bulkhead", 1, 4, 7, E), ("assembly, image programming, test", 1, 8, 15, E),
    ],
    "MC": [
        ("T20F256I4", 1, 13, 20, "estimate; T20F256C4 recorded $12.75 qty 1 only"), ("W25Q32JVSSIQ", 1, 0.4, 0.8, E), ("ASE-50.000MHZ-L-C-T", 1, 0.8, 1.5, E),
        ("2 x TPS3851G18SDRBT + 2 x CL10C332JB8NNNC (WD_M, WD_O)", 2, 2.0, 3.4, E), ("arm latches, OPI_TX, trip flags (SN74LVC2G74DCUR) and final gates", 1, 2, 4, E),
        ("OPI_BOE and OPI_OUT (SN74LVC2G74DCUR), PERMIT_OUT_REQ gate, DIC_OK filter", 1, 0.8, 1.6, E), ("slot status register, 5 x 8-bit parallel-in shift registers", 5, 1.0, 2.0, E),
        ("Ioff buffers on all card-bound outputs (about 6 x 16-bit)", 6, 3, 6, E), ("1.2 V and 3.3 V regulators + supervisor", 1, 2.5, 5, E),
        ("flash-path bus switch", 1, 0.4, 0.8, E), ("female har-bus 64 x2", 2, 16, 30, E), ("AT30TSE752A-XM8M-T", 1, 0.6, 1.0, E),
        ("PCB 6 layers 100 x 220 mm", 1, 10, 18, E), ("passives, LEDs, bracket", 1, 3, 6, E), ("assembly, gateware programming, self-test", 1, 8, 15, E),
    ],
    "MIA": [
        ("AM26C31IPWR", 4, 2.70, 2.70, R), ("ISO1212DBQR (alarms)", 4, 2.74, 2.74, R), ("SMF36A (alarm inputs)", 8, 1.33, 1.33, R),
        ("TLP3640A(TPL,E) x8 + TLP4176A(TP,F) x8 (section 04)", 16, 12, 24, "estimate; no price recorded"),
        ("SN74LVC07APWR x2, TPS22918DBVR, OPI latch", 1, 2, 4, E), ("TVS x2 per channel, line protection", 1, 3, 6, E),
        ("AT30TSE752A-XM8M-T + 3.3 V regulator + supervisor", 1, 1.4, 2.5, E), ("male C096 x2", 2, 7, 9.4, E), ("PCB 4 layers", 1, 6, 10, E),
        ("passives, filters", 1, 2, 4, E), ("assembly, test", 1, 6, 10, E),
    ],
    "MX4": [
        ("AM26C31IPWR", 2, 1.35, 1.35, R), ("ISO1212DBQR", 2, 1.37, 1.37, R), ("SMF36A", 4, 0.66, 0.66, R), ("TLP3640A x4 + TLP4176A x4", 8, 6, 12, E),
        ("SN74LVC07APWR, TPS22918DBVR, OPI latch", 1, 1.5, 3, E), ("EXP_5V supervisor, straps", 1, 0.8, 1.6, E), ("TVS and line protection", 1, 1.5, 3, E),
        ("AT30TSE752A + regulator", 1, 1.4, 2.5, E), ("male C096 x2", 2, 7, 9.4, E), ("PCB", 1, 6, 10, E), ("passives", 1, 1.5, 3, E), ("assembly, test", 1, 5, 8, E),
    ],
    "EIA": [
        ("AM26LV32EIPWR (ENC0-3, FREQ0-1, MPG)", 4, 5.59, 5.59, R), ("TPS2553DBVR-1 per-port limits (ENC0-3, MPG, FREQ)", 6, 3.6, 6, E),
        ("probe front ends + typed supplies", 1, 2, 4, E), ("pendant/status shift registers, XF 1-Wire bridge", 1, 1.5, 3, E), ("encoder line ESD/surge protection", 1, 3, 6, E),
        ("AT30TSE752A + regulator", 1, 1.4, 2.5, E), ("male C096 x2", 2, 7, 9.4, E), ("PCB", 1, 6, 10, E), ("passives, terminations", 1, 2, 4, E), ("assembly, test", 1, 6, 10, E),
    ],
    "EX8": [
        ("AM26LV32EIPWR", 6, 8.38, 8.38, R), ("TPS2553DBVR-1", 8, 4.8, 8, E), ("own 24 V to 5 V converter", 1, 3, 6, E), ("status shift register", 1, 0.5, 1, E),
        ("line protection", 1, 4, 8, E), ("AT30TSE752A + regulator", 1, 1.4, 2.5, E), ("male C096 x2", 2, 7, 9.4, E), ("PCB", 1, 6, 10, E), ("passives", 1, 2, 4, E),
        ("assembly, test", 1, 6, 10, E),
    ],
    "XTB": [
        (f"XTB PCB and {XTB_TERMINALS} header positions", XTB_TERMINALS, 6 + HDR_LO * XTB_TERMINALS, 12 + HDR_HI * XTB_TERMINALS, E),
        ("female har-bus 64 to the base", 1, 8, 15, E), ("fixings and chassis studs", 1, 1.5, 3, E),
        (f"field plugs for the {XTB_TERMINALS} expansion positions", XTB_TERMINALS, PLG_LO * XTB_TERMINALS, PLG_HI * XTB_TERMINALS, E), ("assembly, continuity test", 1, 3, 6, E),
    ],
    "DIC": [
        ("ISO1212DBQR: 12 for DI0-23, 3 for XS1 safety inputs", 15, 10.26, 10.26, R), ("SMF36A", 30, 4.97, 4.97, R), ("DI threshold/sense passives", 1, 3, 6, E),
        ("group sensor-supply limiters x3 and safety supply", 4, 3, 6, E), ("PERMIT_OUT TLP3640A and ARM_LAMP driver", 1, 1, 2, E), ("STM32G031C8T6 card controller", 1, 1.3, 2.5, E),
        ("AT30TSE752A + regulator", 1, 1.4, 2.5, E), ("male C096 x2", 2, 7, 9.4, E), ("PCB 4 layers", 1, 6, 10, E), ("passives", 1, 2, 4, E),
        ("assembly, firmware programming, test", 1, 6, 10, E),
    ],
    "DO": [
        ("TPS274C65ASRHAR", 2, 6, 10, "estimate; no price recorded (unknown)"), ("output support and clamps", 1, 1, 2, E), ("STM32G031K8T6 card controller", 1, 1.2, 2.4, E),
        ("ISO7762FDBQR digital isolator, 4 forward + 2 reverse", 1, 1.6, 2.5, "estimate; price of ISO7762FDBQR not recorded; ISO7740FDBQR recorded $1.61044 @100 as class reference"),
        ("OUT_PERMIT AND OUT_EN AND CARD_EN gate", 1, 0.2, 0.4, E), ("OUT_EN latch (SN74LVC2G74DCUR)", 1, 0.3, 0.6, E), ("AT30TSE752A + regulator", 1, 1.4, 2.5, E),
        ("male C032 x2", 2, 4, 6.4, E), ("PCB 4 layers", 1, 5, 9, E), ("passives", 1, 1.5, 3, E), ("assembly, firmware programming, test", 1, 5, 9, E),
    ],
    "ACC": [
        ("STM32G031K8T6", 1, 1.2, 2.4, E), ("DAC80501ZDQFR x2", 2, 10.56, 10.56, R), ("OPA197IDBVR x2", 2, 2.52, 2.52, R), ("ISO7740FDBQR x2 (AO0, AO1)", 2, 3.22, 3.22, R),
        ("TRACO TMR 1-2412 x2 (AO0, AO1 own domains)", 2, 18.19, 18.19, R), ("AI group: 4-channel ADC, scaling, isolator, LDO", 1, 8, 14, E),
        ("RECOM REC3.5-2424SRW/R8/A AI-group converter (18-36 V in, 24 V 145 mA, 84 %)", 1, 42, 47, "observation CAD 61.39 @100 (DigiKey Canada listing, 29 Sep 2026); USD range is an estimate of the conversion"),
        ("OUT_EN and PEN latches (SN74LVC2G74DCUR)", 1, 0.3, 0.6, E),
        ("PWM buffers", 2, 0.5, 1, E), ("TLP3640A process enables + PROC_PERMIT gating", 2, 1.5, 3, E), ("isolated RS-485", 1, 3, 6, E), ("CAN controller + isolated CAN", 1, 5, 9, E),
        ("AT30TSE752A + regulator", 1, 1.4, 2.5, E), ("male C096 x2", 2, 7, 9.4, E), ("PCB 4 layers", 1, 6, 10, E), ("passives, references", 1, 3, 6, E),
        ("assembly, firmware, calibration, test", 1, 8, 14, E),
    ],
    "ESC": [
        ("ESP32-S3-WROOM-1U-N8", 1, 4.3, 5.7, "estimate; WROOM-1-N8 recorded $4.2691 @100; WROOM-1U-N8 $5.66 qty 1 (snippet)"),
        ("U.FL to RP-SMA bulkhead cable and antenna", 1, 3, 7, E), ("reset, UART buffer, USB switch (Codex esp_service parts)", 1, 2, 4, E), ("regulator", 1, 0.8, 1.5, E),
        ("AT30TSE752A-XM8M-T", 1, 0.6, 1.0, E), ("male C032", 1, 2, 3.2, E), ("PCB", 1, 4, 7, E), ("passives", 1, 1, 2, E), ("assembly, firmware, test", 1, 4, 8, E),
    ],
    "SCART": [
        ("FM24V02A-G history F-RAM (section 04)", 1, 2, 5, E), ("configuration memory (capacity gate open)", 1, 0.5, 4, E), ("WP circuitry, ESD", 1, 0.6, 1.4, E),
        ("male C032", 1, 2, 3.2, E), ("PCB", 1, 1.5, 3, E), ("keyed housing", 1, 2, 6, E), ("assembly, format, test", 1, 2, 4, E),
    ],
}
CS = {k: (round(sum(l[2] for l in v), 2), round(sum(l[3] for l in v), 2)) for k, v in C.items()}
STANDARD = ["BASE", "PLUGS", "PSM", "CMC", "MC", "MIA", "EIA", "DIC", "DO", "DO", "ACC", "ESC", "SCART"]
lo8, hi8 = round(sum(CS[k][0] for k in STANDARD), 2), round(sum(CS[k][1] for k in STANDARD), 2)
lo12, hi12 = round(lo8 + CS["MX4"][0] + CS["XTB"][0], 2), round(hi8 + CS["MX4"][1] + CS["XTB"][1], 2)
lo12e, hi12e = round(lo12 + CS["EX8"][0], 2), round(hi12 + CS["EX8"][1], 2)
READY = {"female C096 x4 (MX4, EX8) + female C096 (XS) + male har-bus 64 (XTB)": (3.0 * 5 + 8, 3.6 * 5 + 15), "PCB area and routing": (4, 8)}
READY_LO, READY_HI = round(sum(v[0] for v in READY.values()), 2), round(sum(v[1] for v in READY.values()), 2)
OPTA_LO = round(HDR_LO * XTB_TERMINALS + 6 - (8 + 1.5), 2)
OPTA_HI = round(HDR_HI * XTB_TERMINALS + 12 - (15 + 3), 2)
TBP_PAIR = (0.39005 + 0.98061) / 8

CHOICES = [
    ["Retained screw-flange field plugs (section 03) instead of Same Sky TBP01 5.08 mm non-locking plugs",
     f"+{(HDR_LO + PLG_LO - TBP_PAIR) * STD_TERMINALS:.0f} to +{(HDR_HI + PLG_HI - TBP_PAIR) * STD_TERMINALS:.0f}",
     "plugs cannot vibrate loose; 3.81 mm pitch keeps the terminal rows about 25 % shorter", "none", "standard (adopted)"],
    ["Fixed wiring base with separate cards instead of one board with keyed pluggable terminal groups",
     "+176 to +292 (board-to-board connector halves on both sides, $146-222 from the cost lines, plus per-card PCB, regulation and identity overhead, estimate $30-70)",
     "card replacement in under 5 minutes without moving a plug; faults contained per card", "spare is one card, not the whole board", "standard (user decision)"],
    ["DIN 41612 / har-bus slot connectors instead of card-edge fingers", "+60 to +110 (card-edge candidate not verified)",
     "guided, coded, >= 400 mating cycles, no hard-gold fingers on every card", "none", "standard (adopted)"],
    ["Expansion readiness on every unit (MX4, EX8, XS slots and the XTB connector)", f"+{READY_LO:.0f} to +{READY_HI:.0f}",
     "MX4, EX8 and a future synchronized module install without soldering or a new base", "none", "standard (required)"],
    ["Expansion terminals on the XTB (section 03) instead of all 136 on the base", f"-{OPTA_LO:.0f} to -{OPTA_HI:.0f} on 8-motor units",
     "8-motor units do not carry unused terminals", "XTB is one more expansion part", "XTB (adopted)"],
    ["TPS274C65ASRHAR instead of TPS4H160BQPWPRQ1 with external acquisition", "unknown (TPS274C65 price not recorded)",
     "per-output current, open-load, temperature and bank-supply readings reach software", "the DO spare carries the same difference", "standard"],
    ["Separate isolation for AO0 and AO1 (section 03 D03-12) instead of one shared domain", "+11 to +13 (second TMR 1-2412 and ISO7740, recorded prices)",
     "two devices with different commons without a ground loop", "ACC spare", "standard"],
    ["Isolated 24 V AI sensor supply on the ACC (RECOM REC3.5-2424SRW/R8/A)", "+42 to +47 (observation CAD 61.39 @100; USD is an estimate)",
     "loop-powered 2- and 4-wire transmitters on AI0-AI3 without an external supply; the CORE_24V budget includes it (0.19 A)", "ACC spare target $249 instead of $199", "standard (XAI.10 belongs to the full I/O)"],
    ["Repair-round safety parts: OPI_BOE/OPI_OUT, OUT_EN and PEN latches, slot status register, STEP/DIR pull-downs", "+3 to +6 across MC, DOA, DOB, ACC (estimate)",
     "no output returns after a permission glitch; interrupted bank-B paths always latched; module power-good visible for every slot", "DO spare +$0.3-0.6; MC +$2-4", "standard (required)"],
    ["CM5 instead of CM4 on the CMC", "+10 (qty 1 recorded retail: $97.50 against $87.50)", "CPU headroom (not measured)", "CMC spare", "standard; CM4 qualified later"],
]

DISPLAYS = [("7 in", "Waveshare 7inch HDMI LCD (B), SKU 10829", 44.29, "qty 100"), ("10 in", "Waveshare 10.1DP-CAPLCD, SKU 23739", 76.27, "qty 100"),
            ("12 in", "Waveshare 12.3inch 1920x720, SKU 28481", 106.59, "qty 100"), ("14 in", "Waveshare 14inch 2160x1440 (US), SKU 28504", 179.99, "qty 1 only"),
            ("18 in", "Luckfox 18.5-Touch-Monitor (US), SKU 32186", 129.99, "qty 1 only"), ("21 in", "Luckfox 21.5-Touch-Monitor (US), SKU 34985", 159.99, "qty 1 only")]
PSU, HDMI, AI = 27.20, 3.96, 15.0
GM_CTRL, GM_PKG, GM_SPARE = 0.45, 0.35, 0.50


def price(cost, gm):
    return int(math.ceil(cost / (1 - gm) / 10.0) * 10) - 1


SPARE = {"PSM": 199, "CMC": 279, "MC": 219, "MIA": 149, "MX4": 159, "EIA": 129, "EX8": 149, "XTB": 199, "DIC": 119, "DO": 99, "ACC": 249, "ESC": 79, "SCART": 39}
# a spare is the same card as the expansion, so its target never exceeds the expansion selling price
SPARE["EX8"] = min(SPARE["EX8"], price(CS["EX8"][1], GM_SPARE))
SPARE_REASONS = {"ACC": "the isolated AI group (REC3.5-2424SRW/R8/A, about $42-47) and two isolated AO domains; a cheaper isolated 24 V converter is a Codex costing task",
                 "MC": "FPGA, both watchdogs and the permission logic are one tested unit", "PSM": "three entry eFuses and two converters", "CMC": "dominated by the compute module",
                 "EX8": "set equal to the EX8 expansion selling price (the spare is the same card)",
                 "XTB": "fitted once as part of the fixed wiring (like the base), not a routine service spare"}

IDENT = {
    "device": "Microchip AT30TSE752A-XM8M-T: digital temperature sensor with 2 Kbit serial EEPROM, MSOP-8, 1.7-5.5 V, -40 to +125 C",
    "evidence": "datasheet Atmel-8854G (ordering code 13.1, Reversible Software Write Protect 10.5, accuracy table) downloaded and read 28 Sep 2026; LCSC listing of the exact code found by search",
    "address": "A2 = A1 = A0 = GND on every card: EEPROM 0x50, temperature 0x48; each card has its own mux branch, so equal addresses never share a bus",
    "write_protection": "RSWP set at the factory. Setting or clearing it needs VHV on A0, which only the factory fixture applies, so no field software can rewrite the record; a 0x63 probe NACKs while protected",
    "temperature": "typical +/-0.5 C (0 to 85 C), +/-1.0 C (-25 to 105 C), +/-2.0 C (-40 to 125 C); datasheet typical figures only",
    "record": "MIR-1, 256 bytes",
    "mir1_layout": [[0, 4, "magic 'CNCM'"], [4, 1, "format version = 1"], [5, 1, "class code"], [6, 2, "hardware revision (major, minor)"],
                    [8, 16, "serial number, ASCII, zero padded"], [24, 4, "manufacture date, days since 2026-01-01"], [28, 4, "variant flags"],
                    [32, 32, "rated capabilities: channel count, first channel, per-channel ratings, supply allocations"],
                    [64, 16, "compatibility: min/max CNC1 ABI, min driver, min gateware build, min/max card firmware (u16 each)"],
                    [80, 16, "calibration descriptor: method id, range, units, SHA-256 prefix of the calibration record (ACC only; zero elsewhere)"],
                    [96, 32, "SHA-256 of the factory test record"], [128, 64, "manufacturer signature (Ed25519) over bytes 0-127; all zero on development cards"],
                    [192, 60, "reserved, 0xFF"], [252, 4, "CRC-32 over bytes 0-251"]],
    "class_codes": {"0x01": "MX4", "0x02": "EX8", "0x03": "MIA", "0x04": "EIA", "0x05": "MC", "0x06": "CMC", "0x07": "PSM", "0x08": "ESC",
                    "0x11": "DIC (= IOL1 class)", "0x21": "DO (DOA/DOB, = IOL1 class)", "0x31": "ACC (= IOL1 class)", "0x50": "XS module",
                    "0x7F": "reserved (IOL1 bootloader state)", "0x00, 0xFF": "invalid"},
    "compatibility_rules": [
        "class code must equal the slot's class; for MX4 the FPGA-latched straps and for EX8 the shift-register class bits must equal the EEPROM class",
        "hardware revision must be listed in the installed software package's compatibility table",
        "rated capabilities must cover every channel the active configuration uses; a weaker card stays in a diagnostic state",
        "CNC1 ABI, gateware build and card firmware must fall inside the driver's supported ranges; otherwise offer a local update or refuse",
        "the signature must verify against the manufacturer key on production units; development cards show 'unqualified' and cannot arm",
        "CRC-32 failure or an unreadable record: card unidentified and inhibited",
    ],
}

PROC = [["stop the machine; the service commits pending configuration (automatic)", 30],
        ["switch off the machine main disconnect / drive power; the service screen asks for this confirmation before it shows any card-removal step (exceptions E1 and E2 of section 04)", 30],
        ["switch off controller power and both field entries; wait for the PSM 'safe' LED, or a fixed 60 s when the LED stays dark or the PSM is the failed card (Codex sizes bleeders so every rail is below 5 V within 30 s [REQ])", 60],
        ["open the card-cage cover (two captive screws)", 30], ["release the card's retaining screw and lever it out along its guides", 20],
        ["slide the replacement along the same guides until the lever seats; tighten the retaining screw", 30], ["close the cover", 30],
        ["power on: disarmed boot, identification, compatibility verdict and list of required checks", 90]]
PROC_TOTAL = sum(p[1] for p in PROC)
REMOVAL = ("Power-off service only (no hot plug). At power-up the card's two presence contacts, its power-good and its MIR-1 record are read; outputs stay inhibited, "
           "position and homing are never restored, and nothing moves or energises until the affected checks pass and the operator arms deliberately.")
MCU_FW = ("STM32G031 firmware (C8T6 on DIC, K8T6 on DOA/DOB/ACC), factory-programmed: a write-protected bootloader plus one application. The host service "
          "updates the application offline from an approved local image through IOL1 MAINT records (section 01 section 4.8) while motion is disarmed and I/O disabled; "
          "an interrupted update leaves the card in its bootloader (IOL1 class 0x7F) with outputs off and the service restarts it. A card whose bootloader itself "
          "fails is replaced, never reflashed in the field")


def mod(i, slot, name, contents, identity, firmware, removal, reverify, contain, proc=PROC, reserved=None, fitted=("yes", "yes")):
    return {"id": i, "slot": slot, "name": name, "contents": contents, "boundary": B.get(i if i != "DO" else "DOA", []), "identity": identity, "firmware": firmware,
            "removal_and_replacement": removal, "replacement_reverifies": reverify, "fault_containment": contain, "replacement_procedure_s": proc,
            "reserved_capacity": reserved or [], "fitted": {"8_motor": fitted[0], "12_motor": fitted[1]},
            "cost_usd_qty100": {"low": CS[i][0], "high": CS[i][1], "lines": [{"item": l[0], "qty": l[1], "low": round(l[2], 2), "high": round(l[3], 2), "evidence": l[4]} for l in C[i]]},
            "spare_price_target_usd": SPARE.get(i)}


MODS = [
    mod("PSM", "S0", "Power and service module",
        ["entry eFuses and reverse protection for XP1 CORE (4 A class), XP2 FIELD_A and XP3 FIELD_B (section 04 section 10); physical fuses in holders on the base",
         "CORE_5V 6 A and MOTION_5V >= 3 A converters, EXP_5V switch with a real power-good, AUX_5V/AUX_24V bank limiters and monitors",
         "8 switched CORE_5V slot feeds (12 feed contacts) with fault flags", "TPS386000 rail supervision, sequencing, POR and the power-cycle tamper latches for MIA, MX4, EIA and EX8",
         "3 x INA238AIDGSR entry monitors, POWERFAIL_N early warning, ESP_CHIP_PU", "cartridge slot XCART1 with guide", "AT30TSE752A identity and temperature"],
        "MIR-1 class 0x07", "none", REMOVAL,
        ["entry voltages and currents against the INA238 readings", "every slot feed and power-good", "tamper latch set/clear by power cycle", "AUX_5V/AUX_24V per bank",
         "POWERFAIL_N warning time against the history-ring flush time"],
        {"port": ["short at one AUX terminal: that bank's AUX limiter"], "card": ["short on a card's logic supply: only that slot feed trips", "FIELD_A overload: FIELD_A eFuse; FIELD_B and logic unaffected"],
         "machine": ["CORE entry or converter failure stops all logic; permission falls through RAILS_OK"]}),
    mod("CMC", "S1", "Compute carrier card",
        ["dual 100-pin CM4/CM5-family module socket, mated at the factory (fine-pitch module connectors never handled in the field); reference module Raspberry Pi CM5102016 for costing and the first timing qualification; other modules (CM4, CB2) are qualified separately before they are offered",
         "bracket: XETH1, XDSP1, XUSB1, XUSB2, XANT1; customer Wi-Fi uses the CM5's certified radio, never the ESP",
         "2 x TCA9548APWR identity branches and the dedicated cartridge bus", "host side of CNC1 SPI, MC flash-restore path, ESP UART, RS-485 UART and CAN SPI"],
        "CM5 OTP serial + MIR-1 class 0x06", "factory-programmed eMMC image: Linux, LinuxCNC, CNC1 driver, configuration service and the local image store for every programmable card",
        REMOVAL + " A replacement CMC has no configuration authority; the cartridge supplies the setup through the explicit recovery workflow.",
        ["image and package manifest", "cartridge read and mirror reconciliation", "CNC1 link, ABI and capability pages", "display and touch", "rehoming"],
        {"port": ["USB or Ethernet port fault: that port only"], "card": ["CMC crash: the FPGA 5 ms command watchdog disarms"], "machine": ["motion stops with the host"]}),
    mod("MC", "S2", "Motion card",
        ["Efinix T20F256I4, ASE-50.000MHZ-L-C-T clock, W25Q32JVSSIQ configuration flash (Codex fpga_core candidates)",
         "section 04 supervisory circuitry: WD_M and WD_O (TPS3851G18SDRBT with CL10C332JB8NNNC), both arm latches, OPI_TX latch, sticky trip flags, final TX/OUT/PROC_PERMIT gates",
         "Ioff buffers on every card-bound output, including the MX4 buffer (TX_PERMIT_B, STEP/DIR/EN 8-11) whose qualified OE clears OPI_BOE; bank-A buffers have OE tied active", "OPI_OUT latch, PERMIT_OUT_REQ gate (PERMIT_OUT open during self-tests), DIC_OK filter, 10 kOhm pull-downs on EXT_PERMIT_3V3 and PROCESS_PERMIT_EXT_3V3", "slot status register (presence and power-good of every slot without another FPGA path)", "configuration-flash restore path from the CMC",
         "local 1.2 V/3.3 V regulation and supervisor; AT30TSE752A"],
        "MIR-1 class 0x05; gateware build ID in CNC1 capability pages",
        "gateware factory-programmed; the host restores it offline from an approved local image with CRESET_N held low and permission withheld (CDONE low keeps every permission off), then verifies by readback and the capability page",
        REMOVAL + " Removing the MC removes every permission line; each receiving card has its own pull-down.",
        ["watchdog self-tests (section 04 section 5.4) and OPI proof tests", "every installed channel: step/dir timing, enables NO/NC, alarms",
         "every encoder, probe and frequency input in use", "gateware build and ABI", "rehoming"],
        {"port": ["a shorted card-bound line: its Ioff buffer channel, never the FPGA pin"], "card": ["FPGA clock stall: WD_M/WD_O remove permission (section 04 section 5.5)"],
         "machine": ["MC failure stops motion and permission-gated outputs"]}),
    mod("MIA", "S3", "Motor interface card A (M0-M7)",
        ["4 x AM26C31IPWR with 10 kOhm pull-downs on every STEP and DIR input (idle low)", "per channel TLP3640A(TPL,E) normally open and TLP4176A(TP,F) normally closed on one LED current (section 04 section 3)",
         "SN74LVC07APWR LED drivers, TPS22918DBVR LED-supply switch, OPI_A latch", "4 x ISO1212DBQR alarm inputs", "AT30TSE752A; local 3.3 V and supervisor"],
        "MIR-1 class 0x03; presence and PGOOD latched by the FPGA and the PSM tamper latch", "none", REMOVAL,
        ["per channel M0-M7: 'disarmed => drive disabled' (E3), enable NO/NC, alarm polarity", "direction check: a channel outside any gantry group jogs alone at low rate; the channels of a gantry group (from the sheet's homing groups) are homed with their shared negative HOME_SEQUENCE and jogged together as one axis, never one joint alone", "scales and geometry preserved"],
        {"port": ["STEP/DIR pair short: that AM26C31 output's short-circuit limit", "enable contact overstress: that photorelay pair", "alarm input surge: its TVS/ISO1212 channel"],
         "card": ["card power loss or removal: tamper latch, whole machine inhibited until a power cycle"], "machine": ["any MIA fault disarms all motion (all-or-nothing arming)"]}),
    mod("MX4", "S4", "Motor expansion card (M8-M11)",
        ["MIA circuits for 4 channels on TX_PERMIT_B", "MOD_ID0-2 straps (class 1)", "EXP_5V supervisor driving EXP_PGOOD", "sold with the XTB for field upgrades; factory-fitted on twelve-motor units"],
        "MIR-1 class 0x01 + FPGA-latched straps (must agree)", "none", REMOVAL + " Profiles using M8-M11 become 'unavailable - inhibited' when it is absent; nothing is deleted.",
        ["M8-M11 only: E3, enables, alarms, direction check with the MIA gantry rule"], {"port": ["as MIA"], "card": ["as MIA"], "machine": ["all-or-nothing arming"]},
        reserved=["FPGA: 16 channel pins, 6 status pins, OPI_OK_B", "base: slot S4 (2 x C096) and the XTB connector", "EXP_5V 0.45 A on MOTION_5V", "installed-mask bits 8-11"],
        fitted=("no", "yes")),
    mod("EIA", "S5", "Encoder and fast-input card",
        ["4 x AM26LV32EIPWR: ENC0-3 A/B/Z, FREQ0-1, MPG A/B (16 channels, none spare)", "TPS2553DBVR-1 per encoder port, MPG and FREQ supply",
         "two unfiltered probe front ends with typed supplies", "pendant/status shift register (XH2 selectors, MPG enable, XF presence, supply faults)", "XF 1-Wire identity bridge", "AT30TSE752A"],
        "MIR-1 class 0x04", "none", REMOVAL,
        ["encoder direction, count and index per port in use", "MPG counts and pendant selectors", "probe polarity and capture", "frequency reading against a reference", "XF module identity"],
        {"port": ["encoder 5 V short: that port's TPS2553; that encoder's data invalid at once"], "card": ["card power loss: tamper latch, machine inhibited until a power cycle"],
         "machine": ["loss of feedback used by a loop stops motion"]}),
    mod("EX8", "S6", "Encoder expansion card (ENC4-ENC11)",
        ["6 x AM26LV32EIPWR (24 channels)", "8 x TPS2553DBVR-1", "own 24 V to 5 V converter fed from CORE_24V through the expansion power switch", "status shift register with class bits", "AT30TSE752A"],
        "MIR-1 class 0x02 + class bits in its shift register", "none", REMOVAL, ["ENC4-ENC11 in use"], {"port": ["as EIA"], "card": ["as EIA"], "machine": ["as EIA"]},
        reserved=["FPGA: 24 encoder pins, 3 shift-register pins", "base: slot S6 (2 x C096)", "CORE_24V 0.523 A (section 04)", "encoder mask bits 4-11"], fitted=("no", "option")),
    mod("XTB", "fixed once", "Expansion terminal board",
        [f"{XTB_TERMINALS} header positions: XM8-XM11 and XE4-XE11 (section 03)", "passive; one har-bus 64 connector and two chassis studs to the base",
         "factory-fitted on twelve-motor units; fitted once in the field together with the first MX4 or EX8, then part of the fixed wiring"],
        "none (the MX4 and EX8 identities cover the expansion)", "none",
        "Fitted with power off and never removed during card service. A damaged XTB is replaced like the base: plug by plug, no individual wire moves.",
        ["continuity of XM8-XM11 and XE4-XE11 during MX4/EX8 commissioning"], {"port": [], "card": [], "machine": []},
        proc=[["power off", 45], ["fit the XTB on its studs and seat its connector", 120], ["fit MX4 and/or EX8 like any card", 150], ["power on and commission", 90]],
        fitted=("no", "yes")),
    mod("DIC", "S7", "Digital input card",
        ["DI0-DI23: 12 x ISO1212DBQR with group sensor-supply limiters",
         "XS1 safety interface: EXT_PERMIT and PROCESS_PERMIT hard-wired to the MC (pulled down at the MC receiver; DIC presence and power-good form DIC_OK in base_ok); SAFETY_STATUS, RESET_ARM, CONTACTOR_FB, STO_FB direct to the FPGA; ARM_LAMP (FIELD_B 0.05 A); PERMIT_OUT photorelay",
         "card controller STM32G031C8T6 (IOL1 port L0)", "AT30TSE752A"],
        "MIR-1 class 0x11 (= IOL1 class) + class and slot in every IOL1 response", MCU_FW, REMOVAL,
        ["DI0-DI23 polarity and assignments", "XS1: external permit removes permission; XS1.3 open opens XPC0/XPC1 (and stops a spindle only where its run or STO input is wired through XPC0); reset/arm window, contactor and STO feedback mismatch faults; PERMIT_OUT follows TX_PERMIT and stays open during both watchdog self-tests"],
        {"port": ["input surge: its TVS/RTHR/ISO1212 channel", "sensor supply short: that group's limiter"], "card": ["controller hang: 3 failed IOL1 frames latch the port fault; DI keep their last value with growing age, then become invalid; safety terms stay in hardware"],
         "machine": ["EXT_PERMIT open removes permission"]}),
    mod("DO", "S8, S9", "Output card DOA/DOB (one part number; bank from the slot code)",
        ["8 outputs: 2 x TPS274C65ASRHAR (quad 72 mOhm high-side, SPI with CRC, 10-bit ADC for per-channel current, VS and FET temperature, on/off-state open-load, DO_EN)",
         "card controller STM32G031K8T6 on the LOGIC side (IOL1 port L1 or L2); one ISO7762FDBQR isolator (4 forward: SCLK, SDI, CS_N, DO_EN; 2 reverse: SDO, wired-OR FLT; F variant: outputs default low when the logic side is unpowered) to the switches' SPI (device CRC on)",
         "card watchdogs of section 01 section 4.7: 1.0 ms accept timer and hardware-started IWDG (<= 2 ms), both refreshed only by fully accepted frames",
         "DO_EN = OUT_PERMIT_k AND OUT_EN latch Q AND CARD_EN (controller pin with pull-down); the OUT_EN latch (SN74LVC2G74DCUR half, CLR_N = qualified OUT_PERMIT_k) keeps the outputs off after any accepted permission drop until a new epoch and IO_ENABLE", "AT30TSE752A"],
        "MIR-1 class 0x21 (= IOL1 class), bank from the slot straps", MCU_FW,
        REMOVAL + " The controller starts with every SW_STATE bit off and CARD_EN low, and raises CARD_EN only in ACTIVE after a new epoch (section 01 section 4.8).",
        ["each assigned output energised once in a scoped commissioning action with current, open-load and fault readback", "bank VS reading against the PSM monitor"],
        {"port": ["DO short: TPS274C65 current limit/thermal on that channel; the entry never trips"],
         "card": ["controller hang: accept timer (1.0 ms) or IWDG (<= 2 ms) drops CARD_EN and so DO_EN", "bank load above 2.0 A: measured against declared loads, bank fault"],
         "machine": ["an output feeding an essential service follows the machine's hold/inhibit policy"]}),
    mod("ACC", "S10", "Analog, communication and process card",
        ["AO0 and AO1, each in its own isolated domain (DAC80501ZDQFR, OPA197IDBVR, ISO7740FDBQR, TMR 1-2412 per channel), zero clamp on OUT_PERMIT_ACC",
         "AI0-AI3 in one isolated group, 0-10 V / 4-20 mA ranges, powered with the 24 V 100 mA sensor supply from a RECOM REC3.5-2424SRW/R8/A", "PWM0-1 buffers (FPGA-generated; OE from OUT_PERMIT_ACC through the OUT_EN latch; no inverted mode)", "PEN0-1 TLP3640A contacts, LED current gated by PROC_PERMIT through the PEN latch in hardware",
         "isolated RS-485 (CMC UART) and isolated CAN transceiver; the MCP2518FDT-E/SL CAN controller (section 01 D01-6) sits on the CMC SPI", "card controller STM32G031K8T6 (IOL1 port L3): analog acquisition, timestamps, calibration", "AT30TSE752A"],
        "MIR-1 class 0x31 (= IOL1 class) with calibration descriptor; full calibration record in the controller's protected flash", MCU_FW,
        REMOVAL + " The replacement brings its own factory calibration; a failed card's calibration is never copied.",
        ["AO zero and full scale against a meter", "AI chain end to end", "PROC_PERMIT removal opens PEN0/PEN1", "RS-485/CAN device discovery"],
        {"port": ["AO short: that output stage", "bus wiring fault: that isolated transceiver"], "card": ["AI isolated supply failure: AI0-3 unavailable; AO domains unaffected"],
         "machine": ["loss of a spindle speed command follows the process fault policy"]}),
    mod("ESC", "S11", "ESP32-S3 service card",
        ["ESP32-S3-WROOM-1U-N8, U.FL to the XANT2 unique-coupling bulkhead", "XUSB_SVC USB-C service port", "wired UART to the CMC; ESP_CHIP_PU owned by the PSM supervisor",
         "observes RAILS_OK and MOTION_DISARMED only; no motion or permission authority", "AT30TSE752A"],
        "eFuse MAC + MIR-1 class 0x08", "ESP-IDF 5.5.4 application factory-programmed with two OTA slots and rollback; offline restore by the host over the UART in ROM download mode (ESP_BOOT plus a supervised reset)",
        REMOVAL, ["service heartbeat", "accessory sequences that depend on it"],
        {"port": ["USB service port fault: that port"], "card": ["ESP failure: service and accessory functions stop"], "machine": ["only declared essential-service dependencies"]}),
    mod("SCART", "XCART1", "Settings cartridge",
        ["protected configuration memory with two committed generations (Codex BOM item with the interface limits of codex_bom_items_with_limits: >= 2 x the committed-record capacity of MODULAR_REPAIR_AND_MEMORY.md, >= 10^5 write cycles, >= 20 years retention, hardware write-protect pin, I2C at 400 kHz)",
         "Infineon FM24V02A-G history-ring F-RAM (section 04 section 12.2), separate from the write-protected configuration memory",
         "hardware WP default-protected; write window only on CART_WP_EN", "keyed housing"],
        "cartridge serial + machine lineage", "none (records only)",
        "Remove only with power off. A cartridge from another machine never becomes the active setup silently; the recovery workflow shows a diff.",
        ["lineage, both committed records, history ring, mirror reconciliation"],
        {"port": [], "card": ["stuck bus: dedicated cartridge bus with host timeouts"], "machine": ["edits blocked until resolved; motion unaffected"]},
        proc=[["power off", 30], ["pull the cartridge from its guide", 10], ["insert the replacement or original", 10], ["power on, follow the recovery diff", 90]]),
]

PERMISSION = {
    "decision": "Adopted from section 04 section 6.2: WD_M, WD_O, both arm latches, the OPI_TX, OPI_BOE and OPI_OUT latches, the PERMIT_OUT_REQ gate, the DIC_OK filter and the final permission gates on the motion card; tamper latches on the PSM, which owns logic power-on reset; an OUT_EN latch on every output card.",
    "module_reasons": ["the user's decision puts the FPGA 'with its clock, configuration flash and supervisory circuitry' on the replaceable motion card",
                       "every latch input originates on the MC; only permission outputs and EXT_PERMIT, PROCESS_PERMIT, RAILS_OK and TAMPER_N cross a connector, so a connector fault can only remove permission",
                       "watchdogs and FPGA are factory-tested and replaced together; the self-test of section 04 section 5.4 runs after every MC replacement",
                       "the fixed base stays passive (section 03 D03-1), so no permission silicon can force a base replacement",
                       "each receiving card has its own pull-down and its own local AND with presence and power-good"],
    "rejected": {"fixed base": "active silicon on the base; a base replacement cannot meet the 5-minute target",
                 "PSM": "separates the watchdogs from their WDI sources by two connectors; the PSM keeps only the tamper latches because it owns POR"},
    "reconciliation": "Section 04 section 6.3 routes MX4 'through the base Ioff buffer'. IS-1 places that Ioff buffer on the motion card (this section governs card boundaries); equations and filters are unchanged.",
}
TERMINAL_DECISION = {
    "adopted": "Section 03 D03-4: M8-M11 and ENC4-ENC11 terminate on the XTB expansion terminal board, fitted once and then part of the fixed wiring; MX4 and EX8 stay replaceable behind it",
    "cost": f"XTB with {XTB_TERMINALS} headers and plugs: estimate ${CS['XTB'][0]:.0f}-{CS['XTB'][1]:.0f} per expanded unit; carrying the headers on every base instead adds about ${OPTA_LO:.0f}-{OPTA_HI:.0f} per 8-motor unit",
    "usability": "twelve-motor units ship with the XTB fitted, so their wiring never changes; a field upgrade fits the XTB once (two studs and one guided connector, no soldering), then the card",
    "alternative": "all 136 expansion terminals on the base: one wiring diagram for every unit and no XTB part, paid by every 8-motor unit",
}
T1 = {
    "selected": "TPS274C65ASRHAR (TI; quad 72 mOhm high-side switch with SPI and integrated ADC; VQFN-40, 6 x 6 mm)",
    "not_permitted": "TPS274C65BS (device comparison table: no current sense, no ADC)",
    "evidence": "TI datasheet SLVSFZ2C (Feb 2024) downloaded and read 28 Sep 2026; its packaging addendum lists TPS274C65ASRHAR as Active",
    "rows": [
        ["complete measurement path", "CS pin per quad (K(CS) = 300) -> RC -> field-side multichannel ADC -> isolated ADC SPI -> card MCU; channel chosen by SEL1/SEL2 with DIAG_EN; in the drawn design CS reaches only a test point, so no reading reaches software",
         "ISNS -> 10-bit ADC inside the switch -> addressable SPI with device CRC -> ISO7762FDBQR -> card MCU; per-channel current, VOUT, FET temperature and VS"],
        ["isolation per 8-output card", "8 IN + SEL1/SEL2/DIAG_EN (shared) + ADC SPI (3) forward, ADC SDO + 2 FAULT reverse: about 14 forward and 3 reverse channels, four or more isolator packages; the drawn design has no free channel",
         "one ISO7762FDBQR: SCLK, SDI, CS_N, DO_EN forward; SDO and wired-OR FLT reverse; outputs switched by SPI, so no per-channel IN lines cross the barrier"],
        ["sampling time", "one channel per select setting; settling after each select change (time not recorded here) plus one ADC conversion; four channels per device read in sequence",
         "128 us per measurement (Tconv1, datasheet); a full sequential round of 4 channels x 4 quantities is at most 2.05 ms (arithmetic, interpretation, to be measured), inside the 93.05 ms age bound"],
        ["accuracy at the declared 0.10-0.50 A", "K(CS) sense error class +/-8 % recorded at the design point (part-selections, datasheet SLVSCV8E); low-current spread not recorded; plus ADC and settling error",
         "sense-current spread +/-4.7 % at 500 mA, +/-9.9 % at 200 mA, +/-15 % at 100 mA relative to the datasheet min-max midpoint (arithmetic), plus ADC reference 2.72-2.85 V, before per-channel factory calibration; both paths need measurement over 0.10-0.50 A, never one convenient load"],
        ["transient withstand", "48 V transient (< 400 ms) absolute maximum, below the SMCJ30CA 48.4 V reference clamp: an open defect",
         "VS 40 V continuous and 60 V transient (< 1 ms, ON state) absolute maximum (datasheet); the 48.4 V clamp is inside the transient rating only if the clamped surge lasts < 1 ms, and the OFF-state transient is not specified: Codex confirms clamp duration or lowers the clamp"],
        ["fault behaviour", "current limit (+/-15 % for 0.5-7 A, recorded), thermal, FAULT pin",
         "current limit per channel, IS-1 default 0.72 A setting = 0.62-0.82 A (datasheet), inrush setting, thermal, on/off-state open-load and wire-break (on-state threshold 0.38-0.61 mA), short-to-supply, SPI CRC, SPI watchdog, DO_EN disables all outputs"],
        ["firmware and test effort", "ADC driver, select sequencing and settling, per-channel analog calibration, test of every select state and of the analog chain",
         "register driver with CRC, ADC readout, fault registers; per-channel factory calibration at two currents"],
        ["complete implemented cost", "2 x TPS4H160BQPWPRQ1 $2.2172 @100 recorded + field ADC + about three extra isolator packages (ISO7740FDBQR class $1.61 @100 recorded) + select and ADC passives: roughly $6-10 more per card than (b) excluding the driver price difference (estimate)",
         "2 x TPS274C65ASRHAR (price not recorded: unknown, not zero) + one ISO7762FDBQR (price not recorded) + sense resistors"],
        ["replacement-card cost", "every DO spare carries the ADC and extra isolators", "DO spare target $99 (section 15.1); the driver price must be quoted before it is confirmed"],
    ],
    "reason": "Only the TPS274C65ASRHAR path brings per-output current, open-load, temperature and bank-supply readings to software through one isolated digital link, with a hardware disable pin and a wider transient margin. The ASH variant's extra current-limit settings serve 2 A loads; IS-1 outputs are 0.5 A with a 1.0 A limit maximum.",
    "do_en_note": "When DO_EN returns high the switch restores the stored SW_STATE, so the card controller writes SW_STATE = 0 and holds CARD_EN low after any permission loss, reset or watchdog trip; an output changes only on a newly accepted command.",
}
LINK = {"name": "IOL1; section 01 section 4 governs frames, CRC-32C, order of checks and watchdogs", "period_us": 100, "port_fault_after_failed_frames": 3,
        "checks_before_any_output_change": ["complete 40-byte frame", "CRC-32C", "SOF and version", "expected class equals the card's class", "expected slot equals the slot straps the card reads",
                                            "epoch equals the current epoch", "sequence = last + 1", "reserved bits zero", "class-specific limits"],
        "card_watchdogs": "1.0 ms accept timer + hardware-started IWDG (<= 2 ms), both refreshed only in the accept path (section 01 section 4.7)",
        "hardware_gate": "every output enable = OUT_PERMIT_k AND OUT_EN latch Q AND CARD_EN (pull-down)",
        "module_additions": "slot straps are copper on the base (4 contacts per linked slot)"}
TELEMETRY = [["DO current, driver temperature and VOUT per channel (current valid only while on)", ">= 11 Hz worst case (>= 22 Hz without host priority requests), <= 93.05 ms age", "section 01 section 8.1"],
             ["bank VS from each TPS274C65", ">= 11 Hz", "section 01 section 8.1"], ["card controller temperature and VDD (DIC, DOA, DOB, ACC)", ">= 5 Hz", "section 01 section 8.1"],
             ["IOL1 counters per port", ">= 11 Hz through the telemetry mirror (about 22 Hz without priority requests)", "section 01 section 3.12"],
             ["card temperature (AT30TSE752A, every card)", "1 Hz", "host I2C, this section"], ["entry voltage/current (INA238)", "10 Hz", "host I2C (TEL.supply, section 03)"],
             ["MIR-1 identity", "power-up and on request", "host I2C, never cyclic"]]
HAL = [["cnc1.module.<slot>.present", "bit", "both presence contacts"], ["cnc1.module.<slot>.power-good", "bit", "card supervisor"],
       ["cnc1.module.<slot>.accepted", "bit", "MIR-1 class, revision and signature accepted"], ["cnc1.module.<slot>.class", "u32", "MIR-1 class code"],
       ["cnc1.module.<slot>.temperature", "float", "AT30TSE752A; with .temperature-valid (bit) and .temperature-age (float s)"]]
SLOT_KEYS = ["psm", "cmc", "mc", "mia", "mx4", "eia", "ex8", "dic", "doa", "dob", "acc", "esc", "scart", "xs"]
POWER = [["CMC", "CORE_5V", 3.00, "section 04: compute 3.00"], ["MC", "CORE_5V", 0.45, "CORE_1V2 input 0.28 + its IO_3V3 share"], ["ESC", "CORE_5V", 0.60, "section 04: ESP_3V3 input"],
         ["DIC, DOA, DOB, ACC logic (card-local 3.3 V)", "CORE_5V", 0.35, "remaining IO_3V3 share + misc"], ["MIA", "MOTION_5V", 0.90, "TX bank A 0.80 + LEDs 0.097"],
         ["EIA", "MOTION_5V", 1.00, "4 encoders 0.80 + MPG 0.10 + FREQ 0.10"], ["MX4", "EXP_5V from MOTION_5V", 0.45, "section 04"],
         ["EX8", "CORE_24V (own converter)", 0.523, "section 04; amperes at 24 V"], ["ACC isolated AO domains", "CORE_24V", 0.06, "section 04 'analog'; amperes at 18 V input"], ["ACC AI group (REC3.5-2424SRW/R8/A)", "CORE_24V", 0.19, "section 04 ai_group; amperes at 18 V input"],
         ["XS (reserved)", "CORE_5V + CORE_24V", None, "contacts reserved; allocation set when a module is defined"]]

# ---------------------------------------------------------------- repair round (29 Sep 2026): external modules, drawn-hardware changes, Codex BOM limits
EXTERNAL_MODULES = [
    {"id": "plasma.divided_voltage.v1", "kind": "external accessory module on the XF port, not a card slot",
     "interface": "XF: FREQ0 differential frequency output on XF.3-4 (FREQ1 on the second pair), FREQ_5V supply 150 mA limit (XF.1), 1-Wire identity on XF.7 and presence on XF.8, both bound to the module record",
     "provides": ["isolated measurement of the source's documented divided arc voltage, delivered as a frequency on FREQ0",
                  "conditioned Arc OK and a source-compatible torch-start interface for sources whose CNC port does not offer a dry Arc OK contact and a torch-start input within the XPC0 rating (0-30 V, <= 50 mA)"],
     "isolation": "module-rated between the source's CNC port and XF; the rating is set by the module qualification (PLASMA_MODULE_SYSTEM section 2); raw arc voltage never enters any controller terminal",
     "identity": "1-Wire record read by the host (HOST.onewire.xf.identity); an absent or unidentified module leaves cnc1.freq.* invalid and the plasma profile unarmable",
     "rules": ["HF-start sources combined with ohmic sensing are rejected by profile", "the module carries no motion or permission authority"],
     "cost_usd": None, "cost_note": "unknown, not zero; priced with the plasma package, not the controller", "status": "proposal (docs/PLASMA_MODULE_SYSTEM.md); not designed, rated or qualified"},
    {"id": "external ohmic-sensing module", "kind": "external accessory, not specified in IS-1",
     "interface": "isolated contact output into PRB1 (XPR.4) and enable from process-enable 1 (XPC1)", "provides": ["ohmic torch-to-plate contact detection"],
     "isolation": "must isolate the torch shield/nozzle potential from every controller terminal; rating to be set by its own qualification",
     "identity": "none defined in IS-1", "rules": ["HF-start sources combined with ohmic sensing are rejected by profile"],
     "cost_usd": None, "cost_note": "unknown, not zero", "status": "requires a separately qualified module; no interface record beyond the terminals above"},
]
HW_CHANGES = [
    {"drawn_file": "hardware/fpga_core/pin-allocation.json (sha256 24d4f7a4...)", "drawn_value": "22 dedicated FPGA machine inputs: HOME0-11_FPGA, PROBE_FPGA (G12), TOOLSETTER_FPGA (G15), DOOR_STATUS_FPGA, PROTECTIVE_STATUS_FPGA (G16), SPINDLE_FAULT_FPGA, SPINDLE_READY_FPGA, FEED_HOLD_FPGA, CYCLE_START_FPGA, LUBE_STATUS_FPGA, SPARE_FPGA",
     "is1_value": "homes and machine status move to the 24 general DI on the DIC (IOL1 L0, identity/sequence/CRC checked); balls reused: G16 -> EXT_PERMIT status copy, G15 -> PRB1, G12 -> PRB0 (terminals.json codex_net/ball fields); the other balls return to the IS-1 ball plan", "reason": "all 24 DI kept with validated serial transport; FPGA pins go to 12 motors, 12 encoders and the safety logic"},
    {"drawn_file": "hardware/fpga_core/pin-allocation.json", "drawn_value": "DRIVE_ENABLE0-11_FPGA_RESERVED", "is1_value": "EN0-11_N_FPGA per-channel enable (active low) to the SN74LVC07A LED drivers of the NO/NC photorelay pair", "reason": "individual enable on every channel (decision 3)"},
    {"drawn_file": "hardware/fpga_core/design.json motor_capacity", "drawn_value": "individual_enable_circuits_present 0; alarm_circuits_present 6", "is1_value": "12 per-channel NO + NC enable circuits; 12 alarm inputs (ISO1212)", "reason": "eight motors standard with twelve on MX4, individual enable and alarm on every channel"},
    {"drawn_file": "hardware/power_entry (requirements.json)", "drawn_value": "two protected entries: CORE_24V_PROTECTED and FIELD_24V_PROTECTED", "is1_value": "three entries: CORE (4 A class, current-limit minimum >= 3.61 A), FIELD_A (>= 5.08 A), FIELD_B (>= 5.32 A)", "reason": "16 x 0.5 A outputs plus AUX loads exceed one 6 A field entry; single-short containment (section 04 section 10.2)"},
    {"drawn_file": "hardware/encoder_power", "drawn_value": "ENC0_5V_LIMITED and ENC1_5V_LIMITED only", "is1_value": "ENC0-3 on the EIA and ENC4-11 on the EX8, one TPS2553DBVR-1 per port", "reason": "4 ABZ encoders standard plus the 8-port expansion fitted together with MX4"},
    {"drawn_file": "hardware/machine_permission", "drawn_value": "TPS3431 watchdog (about 57.7-71.9 ms), one arm latch", "is1_value": "2 x TPS3851G18SDRBT with CL10C332JB8NNNC (WD_M, WD_O), wired-AND WDO/RESET, arm_latch_M cleared by latch_clear_n and arm_latch_O cleared by latch_clear_O_n, CWD guard ring", "reason": "20 ms fault-to-inhibit with the normally-closed enable switch (section 04 section 5)"},
    {"drawn_file": "hardware/machine_permission and controller_assembly/assembly-map.json", "drawn_value": "six-G-input permission fan-out", "is1_value": "IS-1 fan-out of section 04 section 6.3: PERMIT_OUT gated by PERMIT_OUT_REQ, OPI_TX/A/B/BOE/OUT, DIC_OK in base_ok, pull-downs on EXT_PERMIT_3V3 and PROCESS_PERMIT_EXT_3V3, OUT_EN latch on each output card; Codex re-runs the permission validator", "reason": "corrections (2) and the repair-round safety findings"},
    {"drawn_file": "controller_assembly/assembly-map.json host SPI", "drawn_value": "one chip select through SN74AVC4T774PWR (4 bits)", "is1_value": "CS_FB and CS_CMD: five buffered channels (second buffer or wider part), SERVO_MARK test point", "reason": "two fixed-length transactions per cycle (section 01 D01-1)"},
    {"drawn_file": "output driver block (assembly map)", "drawn_value": "TPS4H160BQPWPRQ1 with CS only to a test point", "is1_value": "2 x TPS274C65ASRHAR per 8 outputs behind one ISO7762FDBQR, OUT_EN latch, STM32G031K8T6 on IOL1", "reason": "T1: per-output current, open-load and temperature must reach software"},
    {"drawn_file": "tx_twelve / tx_bank", "drawn_value": "10-contact motor plug; STEP/DIR receiver-input idle pulls not stated", "is1_value": "14-position motor plug (13 used, section 03 D03-3); 10 kOhm pull-downs on every AM26C31 STEP/DIR input on MIA and MX4", "reason": "enable NO/NC and AUX supplies per plug; a floating input must rest at the idle level (section 04 section 4.2)"},
    {"drawn_file": "base and motion-card connectors (not drawn)", "drawn_value": "presence/power-good of DIC, DOA, DOB, ACC, ESC, CMC, XS, SCART not routed to the FPGA", "is1_value": "29 lines to the MC slot status register (section 6 MC groups; section 01 section 4.10)", "reason": "module power-good diagnostics (A2) need a physical path"},
]
BOM_LIMITS = [
    {"item": "cartridge configuration memory (SCART)", "owner": "Codex", "limits": "capacity >= 2 x the committed-record size of MODULAR_REPAIR_AND_MEMORY.md (two generations); >= 10^5 write cycles; >= 20 years retention; hardware WP pin driven by CART_WP_EN; I2C 400 kHz on the dedicated cartridge bus; 2.7-3.6 V"},
    {"item": "ACC AI ADC", "owner": "Codex", "limits": ">= 4 channels; >= 1 kHz per channel [REQ]; >= 16-bit; <= +/-0.1 % of full scale after the card's factory calibration over 0-55 C on the 0-10 V and 4-20 mA ranges; SPI to the STM32G031K8T6 across the AI-group isolator"},
    {"item": "ACC AI-group isolated supply", "owner": "Codex", "limits": "selected: RECOM REC3.5-2424SRW/R8/A (18-36 V in, 24 V 145 mA, 84 %, DigiKey listing); a cheaper isolated converter meeting 24 V >= 120 mA, >= 80 % efficiency and >= 1.5 kV isolation may replace it after costing"},
    {"item": "isolated RS-485 transceiver (ACC)", "owner": "Codex", "limits": "half-duplex, >= 1 Mbit/s, fail-safe receiver, driver enable from RTS, >= 2.5 kVrms isolation, bus-pin ESD >= 8 kV contact, <= 1/4 unit load"},
    {"item": "isolated CAN FD transceiver (ACC)", "owner": "Codex", "limits": ">= 2 Mbit/s data phase (MCP2518FDT-E/SL controller), >= 2.5 kVrms isolation, bus-fault protection covering a 24 V short, dominant time-out"},
    {"item": "ARM_LAMP driver (DIC)", "owner": "Codex", "limits": "24 V high-side, 50 mA continuous, current limit <= 0.1 A, survives a sustained short, fault flag readable by the DIC controller"},
    {"item": "MPG, XF and probe supply limiters (EIA)", "owner": "Codex", "limits": "MPG 5 V 100 mA, XF 5 V 150 mA, probes 24 V 100 mA each; limit <= 1.5 x load; fault flag into the EIA status register"},
    {"item": "enable-loop and PERMIT_OUT TVS (MIA, MX4, DIC)", "owner": "Codex", "limits": "bidirectional, stand-off >= 30 V, clamp < 60 V at its rated pulse (section 04 section 3.2)"},
]

spec = {
    "spec_revision": REV, "section": "02-modules-and-boundaries", "date": "2026-09-28",
    "status": "Interface specification. Not implemented, not drawn, not built, not measured, not ready for manufacture.",
    "evidence_classes": {"datasheet": "manufacturer datasheet or product page read for this section", "recorded price": "ladder already recorded in research/*.json",
                         "observation": "price or listing seen on a distributor page or search snippet on 28 Sep 2026, quantity stated", "arithmetic": "derived here",
                         "estimate": "engineering estimate, not evidence", "source inspection": "read from the repository, IS-1 sections 03/04 or Codex files"},
    "owners": {"Codex": "schematics, power/protection, connectors, PCB, hardware BOM", "Claude": "gateware, CNC1 protocol/driver, card-controller firmware, configuration/diagnostics service"},
    "consistency": {"card_names": "section 03 section 4.1 adopted", "field_counts_source": "spec/terminals.json (section 03)", "enable_parts_watchdogs_rails": "section 04"},
    "connectors": CONNECTORS,
    "connector_requirements": ["guided: card guides bring the connector into alignment before any contact touches; no fine-pitch alignment by eye",
                               "retained: card lever plus one captive retaining screw; field plugs retained by screw flanges (section 03)",
                               "keyed: HARTING coded versions or coding keys per card class; 1-connector and 2-connector cards also differ in guide position",
                               ">= 400 mating cycles (DIN 41612 performance level 2) or >= 500 (har-bus 64, H15)",
                               "power contacts rated >= 2x continuous current (section 04 section 10.4): design 1.0 A per 2 A DIN contact, 0.5 A per 1 A har-bus contact, 7.5 A per 15 A H15 contact",
                               "presence contacts at both connector ends; LOGIC and FIELD conductors in separate rows with an unused row or a separate connector between them",
                               "a ground contact next to every permission net on the motion-card connectors (section 04 section 10.4)"],
    "identity": IDENT,
    "fpga_pin_budget": {"groups": [{"group": g, "pins": n, "note": x} for g, n, x in FPGA], "total": FPGA_TOTAL, "field_driven_section_03": FPGA_FIELD, "reserved_for_expansion": FPGA_RESERVED,
                        "local_to_mc": FPGA_LOCAL, "t20f256_usable": 189, "t20f256_full_feature": 137, "spare": 189 - FPGA_TOTAL, "on_lvds_as_gpio_min": FPGA_TOTAL - 137,
                        "evidence": "arithmetic; no package fit, bank audit or place-and-route"},
    "permission_placement": PERMISSION, "expansion_terminals": TERMINAL_DECISION, "output_driver_T1": T1, "card_link": LINK,
    "telemetry": [{"quantity": a, "rate": b, "source": c} for a, b, c in TELEMETRY],
    "hal_and_service": {"slot_keys": SLOT_KEYS, "pins": [{"name": a, "type": b, "note": c} for a, b, c in HAL],
                        "publisher": "userspace configuration service from host I2C, not the real-time component; linked cards also have the section 01 cnc1.io.P.* pins", "service": "controller_config service object hw.modules[<slot>] with the same fields, the decoded MIR-1, the compatibility verdict and the required checks"},
    "power_allocation": [{"consumer": a, "rail": b, "a": c, "basis": d} for a, b, c, d in POWER],
    "base": {"name": "Fixed wiring base", "active_silicon": "none", "firmware": "none", "field_positions_standard": STD_TERMINALS,
             "replacement": "not a 5-minute module: every field plug is unscrewed and moved plug by plug; no individual wire moves"},
    "boundaries": B, "modules": MODS,
    "cost_summary_usd_qty100": {"per_item": {k: {"low": v[0], "high": v[1]} for k, v in CS.items()}, "controller_8_motor": {"low": lo8, "high": hi8},
                                "controller_12_motor": {"low": lo12, "high": hi12}, "controller_12_motor_12_encoder": {"low": lo12e, "high": hi12e},
                                "reference_controller_price": 400, "expansion_readiness_every_unit": {"low": READY_LO, "high": READY_HI},
                                "evidence": "sum of recorded prices and engineering estimates; no quotation",
                                "unknown_not_zero": ["TPS274C65ASRHAR, TLP3640A, TLP4176A, AT30TSE752A, INA238, TPS3851 and HARTING USD prices", "PCBWay fabrication and assembly quotes",
                                                     "yield and rework", "freight and duties", "warranty and support", "certification and EMC testing"]},
    "cost_driving_choices": [{"choice": a, "cost_difference_usd": b, "capability": c, "spare_effect": d, "placement": e} for a, b, c, d, e in CHOICES],
    "pricing": {"rule": "price = complete implemented cost / (1 - gross margin), rounded up to the next multiple of US$10, less US$1; controller 45 %, package add-ons 35 %, spares and expansions 50 %; a package price is the separately rounded controller price plus the separately rounded add-on price plus the $15 AI allowance",
                "formula": {"round_up_to_usd": 10, "less_usd": 1, "gross_margin": {"controller": GM_CTRL, "package_addons": GM_PKG, "spares_and_expansions": GM_SPARE}, "ai_allowance_usd": AI},
                "status": "recommendation from estimates; replace with quotes before publishing",
                "controller_8_motor": [price(lo8, GM_CTRL), price(hi8, GM_CTRL)],
                "mx4_with_xtb": [price(CS["MX4"][0] + CS["XTB"][0], GM_SPARE), price(CS["MX4"][1] + CS["XTB"][1], GM_SPARE)],
                "ex8": [price(CS["EX8"][0], GM_SPARE), price(CS["EX8"][1], GM_SPARE)]},
    "spare_targets_rule": "no field-facing card spare above 10 % of the controller price; MC, PSM and ACC above that need a written reason; the CMC is dominated by the compute module; an expansion card's spare target never exceeds its expansion selling price",
    "spare_targets_usd": SPARE, "spare_target_reasons": SPARE_REASONS,
    "external_modules": EXTERNAL_MODULES, "changes_to_codex_drawn_hardware": HW_CHANGES, "codex_bom_items_with_limits": BOM_LIMITS,
}
PK = []
for scr, disp, usd, ev in DISPLAYS:
    add = usd + PSU + HDMI
    PK.append({"screen": scr, "display": disp, "display_usd": usd, "display_evidence": ev, "control_psu_usd": PSU, "hdmi_usd": HDMI, "ai_allowance_usd": AI,
               "package_cost_low": round(lo8 + add + AI, 2), "package_cost_high": round(hi8 + add + AI, 2),
               "unknown": ["enclosure or pendant housing", "machine-side field supplies", "harnesses", "packaging", "setup assistance"],
               "price_low": price(lo8, GM_CTRL) + price(add, GM_PKG) + int(AI), "price_high": price(hi8, GM_CTRL) + price(add, GM_PKG) + int(AI)})
spec["packages_usd_qty100"] = {"packages": PK, "note": "controller estimate + recorded display + MEAN WELL GST90A24-P1M $27.20 (sizing not re-derived) + HDMI cable $3.96 + $15 AI allowance (a ceiling); unknown items excluded, never zero"}

with open(WT / "spec" / "modules.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)
    f.write("\n")


def tab(h, rows):
    s = "| " + " | ".join(h) + " |\n|" + "|".join("---" for _ in h) + "|\n"
    return s + "".join("| " + " | ".join(str(x) for x in r) + " |\n" for r in rows)


T = {}
rows = []
for k in ["PSM", "CMC", "MC", "MIA", "MX4", "EIA", "EX8", "XTB", "DIC", "DOA", "DOB", "ACC", "ESC", "SCART", "XS"]:
    for i, b in enumerate(B[k]):
        rows.append([k, f"P{i + 1}" if k != "MC" else "P1+P2", b["connector"], b["single_ended_signals"], b["differential_pairs"], b["signal_returns"], b["power_contacts"],
                     b["field_conductors_other"], b["presence_contacts"], b["identity_bus_contacts"], f"{b['contacts_used']}/{b['contacts_total']}", b["contacts_spare"]])
T["BOUNDARY_TABLE"] = tab(["Card", "Conn.", "Family", "Single-ended", "Diff. pairs", "Signal returns", "Power", "Other field", "Presence", "Identity bus", "Used/total", "Spare"], rows)
T["MC_TABLE"] = tab(["Group crossing the motion-card connectors", "Conductors"], [[g["group"], g["conductors"]] for g in B["MC"][0]["groups"]])
T["FPGA_TABLE"] = tab(["FPGA signal group", "Pins", "Note"], [[g, n, x] for g, n, x in FPGA] + [["**Total**", f"**{FPGA_TOTAL}**", f"{FPGA_RESERVED} reserved for MX4, EX8, XS"]])
names = {"BASE": "Fixed wiring base with card cage", "PLUGS": f"Field plugs, {STD_TERMINALS} standard positions", "PSM": "PSM", "CMC": "CMC (CM5 + carrier)", "MC": "MC",
         "MIA": "MIA", "MX4": "MX4", "XTB": f"XTB, {XTB_TERMINALS} headers and plugs", "EIA": "EIA", "EX8": "EX8", "DIC": "DIC", "DO": "DOA or DOB (each; two fitted)", "ACC": "ACC",
         "ESC": "ESC", "SCART": "SCART"}
crow = []
for k in ["BASE", "PLUGS", "PSM", "CMC", "MC", "MIA", "EIA", "DIC", "DO", "ACC", "ESC", "SCART", "MX4", "XTB", "EX8"]:
    rc = sum(l[2] for l in C[k] if l[4].startswith("recorded"))
    crow.append([names[k], f"{rc:.2f}", f"{CS[k][0]:.0f}-{CS[k][1]:.0f}", f"${SPARE[k]}" if k in SPARE else "-",
                 "expansion" if k in ("MX4", "XTB", "EX8") else ("fixed" if k in ("BASE", "PLUGS") else "standard")])
T["COST_TABLE"] = tab(["Item", "Recorded-price lines (USD)", "Estimate (USD, qty 100)", "Spare price target", "Standard / expansion"], crow)
T["TOTALS_TABLE"] = tab(["Build", "Estimate (USD, qty 100)", "Against the US$400 reference", "Recommended price at 45 % margin (USD)"],
                        [["8 motors, 4 encoders", f"{lo8:.0f}-{hi8:.0f}", f"{lo8 / 400:.1f}-{hi8 / 400:.1f} x", f"{price(lo8, GM_CTRL)}-{price(hi8, GM_CTRL)}"],
                         ["12 motors (MX4 + XTB)", f"{lo12:.0f}-{hi12:.0f}", f"{lo12 / 400:.1f}-{hi12 / 400:.1f} x", f"{price(lo12, GM_CTRL)}-{price(hi12, GM_CTRL)}"],
                         ["12 motors + 12 encoders (MX4 + XTB + EX8)", f"{lo12e:.0f}-{hi12e:.0f}", f"{lo12e / 400:.1f}-{hi12e / 400:.1f} x", f"{price(lo12e, GM_CTRL)}-{price(hi12e, GM_CTRL)}"]])
T["CHOICE_TABLE"] = tab(["Engineering choice", "Cost difference per controller (USD, estimate)", "Capability gained", "Replacement-card effect", "Standard or optional"], CHOICES)
T["PACKAGE_TABLE"] = tab(["Screen", "Display (recorded)", "Display USD", "Package cost estimate (USD)", "Recommended package price (USD)"],
                         [[p["screen"], p["display"], f"{p['display_usd']:.2f} ({p['display_evidence']})", f"{p['package_cost_low']:.0f}-{p['package_cost_high']:.0f}",
                           f"{p['price_low']}-{p['price_high']}"] for p in PK])
T["PROC_TABLE"] = tab(["Step", "Time budget (s, estimate)"], PROC + [["**Total**", f"**{PROC_TOTAL}** ({PROC_TOTAL / 60:.1f} min)"]])
T["IDENT_TABLE"] = tab(["Offset", "Bytes", "Field"], IDENT["mir1_layout"])
T["HWCHANGE_TABLE"] = tab(["Drawn file / block", "Drawn value", "IS-1 value", "Reason"], [[h["drawn_file"], h["drawn_value"], h["is1_value"], h["reason"]] for h in HW_CHANGES])
T["BOMLIM_TABLE"] = tab(["Item", "Owner", "Interface limits it must meet"], [[b_["item"], b_["owner"], b_["limits"]] for b_ in BOM_LIMITS])
T["EXTMOD_TABLE"] = tab(["Module", "Interface", "Provides", "Status and cost"], [[m_["id"], m_["interface"], "; ".join(m_["provides"]), m_["status"] + "; cost " + m_["cost_note"]] for m_ in EXTERNAL_MODULES])
T["T1_TABLE"] = tab(["Criterion", "(a) TPS4H160BQPWPRQ1 + external acquisition", "(b) TPS274C65ASRHAR"], T1["rows"])
T["HAL_TABLE"] = tab(["HAL pin", "Type", "Note"], HAL)
T["TEL_TABLE"] = tab(["Quantity", "Report rate", "Source"], TELEMETRY)
T["POWER_TABLE"] = tab(["Consumer", "Rail", "Allocation (A)", "Basis"], [[a, b, "-" if c is None else c, d] for a, b, c, d in POWER])
short_fw = {"PSM": "none", "CMC": "eMMC image", "MC": "gateware (host restore)", "MIA": "none", "MX4": "none", "EIA": "none", "EX8": "none", "XTB": "none",
            "DIC": "STM32G031 loader + app", "DO": "STM32G031 loader + app", "ACC": "STM32G031 loader + app", "ESC": "ESP-IDF, 2 OTA slots", "SCART": "none (records)"}
T["SLOT_TABLE"] = tab(["Slot", "Card", "8-motor unit", "12-motor unit", "Identity", "Firmware"],
                      [[m["slot"], f"{m['id']}: {m['name']}", m["fitted"]["8_motor"], m["fitted"]["12_motor"], m["identity"], short_fw[m["id"]]] for m in MODS]
                      + [["S12", "XS: synchronized expansion slot (reserved)", "empty", "empty", "MIR-1 class 0x50", "set by the future module"]])
T["CONTAIN_TABLE"] = tab(["Card", "Stays on the port", "Stays on the card", "Machine-level (by design)"],
                         [[m["id"], "; ".join(m["fault_containment"]["port"]) or "-", "; ".join(m["fault_containment"]["card"]) or "-", "; ".join(m["fault_containment"]["machine"]) or "-"]
                          for m in MODS if m["id"] != "XTB"])
T["REVERIFY_TABLE"] = tab(["Card", "What its replacement re-verifies before normal operation"], [[m["id"], "; ".join(m["replacement_reverifies"])] for m in MODS])
T["CONTENT_TABLE"] = tab(["Card", "Contents"], [[m["id"], "<br>".join(m["contents"])] for m in MODS])
V = {"LO8": f"{lo8:.0f}", "HI8": f"{hi8:.0f}", "LO12": f"{lo12:.0f}", "HI12": f"{hi12:.0f}", "LO12E": f"{lo12e:.0f}", "HI12E": f"{hi12e:.0f}",
     "R_LO": f"{lo8 / 400:.1f}", "R_HI": f"{hi8 / 400:.1f}", "P_LO": str(price(lo8, GM_CTRL)), "P_HI": str(price(hi8, GM_CTRL)),
     "MX4P_LO": str(spec["pricing"]["mx4_with_xtb"][0]), "MX4P_HI": str(spec["pricing"]["mx4_with_xtb"][1]), "EX8P_LO": str(spec["pricing"]["ex8"][0]), "EX8P_HI": str(spec["pricing"]["ex8"][1]),
     "FPGA_TOTAL": str(FPGA_TOTAL), "FPGA_FIELD": str(FPGA_FIELD), "FPGA_RES": str(FPGA_RESERVED), "FPGA_SPARE": str(189 - FPGA_TOTAL), "FPGA_LVDS": str(FPGA_TOTAL - 137),
     "FPGA_LOCAL": str(FPGA_LOCAL), "MC_USED": str(B["MC"][0]["contacts_used"]), "MC_SPARE": str(B["MC"][0]["contacts_spare"]),
     "STD_T": str(STD_TERMINALS), "XTB_T": str(XTB_TERMINALS), "ALL_T": str(ALL_TERMINALS), "PROC_TOTAL": str(PROC_TOTAL), "PROC_MIN": f"{PROC_TOTAL / 60:.1f}",
     "READY_LO": f"{READY_LO:.0f}", "READY_HI": f"{READY_HI:.0f}", "OPTA_LO": f"{OPTA_LO:.0f}", "OPTA_HI": f"{OPTA_HI:.0f}", "XTB_LO": f"{CS['XTB'][0]:.0f}", "XTB_HI": f"{CS['XTB'][1]:.0f}",
     "BASE_LO": f"{CS['BASE'][0]:.0f}", "BASE_HI": f"{CS['BASE'][1]:.0f}", "PLUG_LO": f"{CS['PLUGS'][0]:.0f}", "PLUG_HI": f"{CS['PLUGS'][1]:.0f}",
     "XTB_USED": str(B["XTB"][0]["contacts_used"]), "DIC_SPARE_NOTE": str(B["DIC"][0]["contacts_spare"])}
text = TEMPLATE.read_text(encoding="utf-8")
for k, v in T.items():
    text = text.replace("{{" + k + "}}", v.rstrip("\n"))
for k, v in V.items():
    text = text.replace("{{" + k + "}}", v)
left = [l for l in text.splitlines() if "{{" in l]
assert not left, left[:5]
with open(WT / "docs" / "interface-spec" / "02-modules-and-boundaries.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print(json.dumps({"lo8": lo8, "hi8": hi8, "lo12": lo12, "hi12": hi12, "lo12e": lo12e, "hi12e": hi12e, "fpga": FPGA_TOTAL, "res": FPGA_RESERVED, "local": FPGA_LOCAL,
                  "mc": [B["MC"][0]["contacts_used"], B["MC"][0]["contacts_total"]], "xtb": B["XTB"][0]["contacts_used"], "ready": [READY_LO, READY_HI], "optA": [OPTA_LO, OPTA_HI],
                  "pricing": spec["pricing"], "cs": CS, "used": {k: [b["contacts_used"] for b in v] for k, v in B.items()}}, indent=0))
