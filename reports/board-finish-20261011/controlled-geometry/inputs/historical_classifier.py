"""Classify every candidate controlled-impedance net on ROOT104 -> Z:/pcb-runs/impedance/controlled-nets.json

Inputs (read-only): Controller netlist.xml, work/candidates.json, work/board_geom.json (pads, MST, routed length,
missing joins, reference-plane samples measured on a byte-identical copy of ROOT104), work/citations.json
(file/line/page of every datasheet statement used), impedance_calc.py (propagation delay of the routing layers).

Decision rules (Claude-authored draft spec, recorded per the operator's 2026-10-03 instruction; numbers derived):
  R1  Spec-mandated interfaces: the interface owner's datasheet names the impedance (CM5: USB2 90 ohm diff,
      HDMI 100 ohm diff, Ethernet MDI 100 ohm diff). Class follows the datasheet; no length test.
  R2  Electrical-length test for everything else: a line needs a controlled impedance when its estimated
      routed length L_est exceeds L_crit = 0.1 * t_r / t_pd  (TI ISOW1432 Eq. 3 stub criterion, cited:
      one-way delay < t_r / 10). t_pd is the SLOWER routing layer (In3 stripline), so L_crit is the shorter one.
      L_est = routed length when the net is already fully joined, else max(1.3 * MST, min daisy-chain path)
      (1.3 detour allowance = inference). t_r = fastest datasheet value of the driving part (typ when no min is
      listed); parts without an output rise-time spec use 1.0 ns (inference, conservative).
  R3  Differential field interfaces failing R2 get the impedance of the line (cable) they belong to:
      - RS-485: ISOW1432 says RT matches the cable Z0, and the on-board RT is 120 ohm -> PCB pair 120 ohm.
      - Encoder / MPG / FREQ inputs (AM26LV32E): the datasheet requires RT within 20 % of the CABLE impedance and
        characterises with 100-ohm twisted pair. The on-board RT = 120 ohm is +20 % of 100 ohm, inside that window.
        The PCB pair follows the 100-ohm cable (DIFF_100), NOT the 120-ohm RT.
      - STEP/DIR outputs (AM26C31, no on-board termination): the datasheet states no line-impedance requirement.
        Its only differential load is the RL = 100 ohm TEST CONDITION of the VOD specification. DIFF_100 is
        therefore an INFERENCE: the 100-ohm twisted pair that test load represents.
      The whole interface group gets one class when any member fails R2 (uniform routing).
  R4  Single-ended lines: IMP_50 only when the chain is edge-sensitive (clock / counted pulse / edge-captured
      input; series-terminated chain members inherit) AND fails R2. Evidence is recorded per net in three tiers:
      'pin'  - a netlist pin function on the chain names a clock (CLK/SCK/SCLK/TCK..., any pin type);
      'spec' - the project's interface specification (IS-1 01-protocol-and-schedule.md) or a part datasheet
               states the function (counted step pulses, x4 quadrature counting, edge capture, SPI clock);
      'name' - only the net name (clock/strobe/counted-pulse pattern).
      Level-sampled lines are NONE; their reflection settling time (6 one-way delays) gives a maximum clock or
      bit rate (settle <= half a period). Every level-sampled net on a clocked serial bus is checked against
      that bus's clock: the rate stated in the interface specification, or the maximum SCLK / bit rate of the
      slowest device on the bus (the bus cannot legally run faster). Result in 'bus_clock_check'.
  R5  I2C / SMBus: NONE - receivers suppress spikes < 50 ns (cited) and the open-drain edges are >= 8 ns.
  R6  1-Wire identity line: NONE - read only at qualification and after module replacement (IS-1); 1-Wire bit
      timing is in microseconds (1-Wire specification is not in the project sources: inference).
Output fields per net: interface, group, pair_partner, class, target/tolerance, citations, end parts,
MST (lower bound), L_est, L_crit, t_r basis, skew target + source, reference-plane samples, rationale.
"""
import itertools
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = "Z:/pcb-runs/impedance/"
sys.path.insert(0, HERE)
import impedance_calc as ic  # noqa: E402

NETLIST = r"C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/hardware/motherboard/netlist.xml"
CIT = json.load(open(HERE + "work/citations.json", encoding="utf-8"))
CAND = json.load(open(HERE + "work/candidates.json", encoding="utf-8"))
GEOM = json.load(open(HERE + "work/board_geom.json", encoding="utf-8"))
ASE_PDF = ("C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-completion-20260930/mc-integrated-r04/source/"
           "reports/board-completion-20260930/oscillator-footprint-promotion/sources/ase-current-20260930.pdf")

# ---------------------------------------------------------------- layer delays (method B at the provisional geometry)
STRIP = ic.Layer("In3.Cu", "stripline", t=0.035, h1=0.22, er1=4.45, h2=0.33, er2=4.6)
MICRO = ic.Layer("F.Cu", "microstrip", t=0.07, h=0.22, er=4.45)
_, _, EE_STRIP = ic.se_methods(STRIP, 0.20)
_, _, EE_MICRO = ic.se_methods(MICRO, 0.36)
TPD_STRIP = ic.tpd_ps_per_mm(EE_STRIP)
TPD_MICRO = ic.tpd_ps_per_mm(EE_MICRO)
TPD = max(TPD_STRIP, TPD_MICRO)
# largest differential impedance on In3.Cu at the board's 0.20 mm track minimum (method B, loosest gap)
ZMAX_IN3_W020 = ic.diff_methods(STRIP, 0.20, 6.0)[1]["zdiff"]
DETOUR = 1.3
DEFAULT_TR_NS = 1.0


def cite(key, idx=None, note=None):
    hs = CIT[key] if idx is None else [CIT[key][i] for i in idx]
    out = [{"file": h["file"], "line": h["line"], "pdf": h["pdf"], "pdf_page": h["pdf_page"], "text": h["text"]} for h in hs]
    if note:
        for o in out:
            o["note"] = note
    return out


def lcrit_mm(tr_ns):
    return 0.1 * tr_ns * 1000.0 / TPD


# ---------------------------------------------------------------- netlist
root = ET.parse(NETLIST).getroot()
COMPS = {}
for c in root.iter("comp"):
    mpn = ""
    for f in c.iter("field"):
        if f.get("name") == "MPN":
            mpn = (f.text or "").strip()
    COMPS[c.get("ref")] = {"value": (c.findtext("value") or "").strip(), "mpn": mpn}
NETS = {}
for n in root.iter("net"):
    NETS[n.get("name")] = [{"ref": nd.get("ref"), "pin": nd.get("pin"), "pintype": nd.get("pintype"),
                            "pinfunction": nd.get("pinfunction") or ""} for nd in n.iter("node")]
PIN_NET = {(nd["ref"], nd["pin"]): name for name, nodes in NETS.items() for nd in nodes}
VIRTUAL = re.compile(r"^(B|BT|BM)\d")   # schematic boundary symbols: no footprint on the board


def part(ref):
    c = COMPS.get(ref, {})
    return c.get("mpn") or c.get("value") or ""


def r_ohm(ref):
    c = COMPS.get(ref, {})
    m = re.match(r"CRCW\d{4}(\d+)R(\d)", c.get("mpn", ""))
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m = re.match(r"CRCW\d{4}(\d+)K(\d)", c.get("mpn", ""))
    if m:
        return float(f"{m.group(1)}.{m.group(2)}") * 1e3
    return None


# ---------------------------------------------------------------- driver rise times
PART_TR = [
    (r"^T20F", 1.02, "T20_TR", "Trion T20 Table 81: 3.3 V LVCMOS rise 1.02 ns (weakest drive, slow slew disabled; "
                                "stronger drive is faster -> L_crit is an upper bound)"),
    (r"AM26LV32E", 5.0, "AM26LV32E_TT", "AM26LV32E output transition time 5 ns (single listed value)"),
    (r"AM26C31", 5.0, "AM26C31_TR", "AM26C31 tr(OD) typ 5 ns (max 10 ns; no min listed -> typ used)"),
    (r"ISO776\d", 1.0, "ISO7761_TR", "ISO776x output rise time typ 1.0 ns at 3.3 V (max 3 ns)"),
    (r"ISO7720", 0.7, "ISO7720_TR", "ISO7720 output rise time, fastest listed typ 0.7 ns"),
    (r"ISO1212", 3.0, "ISO1212_TR", "ISO1212 OUTx rise/fall typ 3 ns"),
    (r"ISOW1044", 1.0, "ISOW1044_RXD_TR", "ISOW1044 RXD output rise typ 1 ns"),
    (r"ISOW1432", 4.0, "ISOW1432_RX_TR", "ISOW1432 receiver R output rise typ 4 ns"),
    (r"^ASE-", 2.4, None, "Abracon ASE datasheet p1 'Rise and Fall Time (Tr/Tf)': 2.4-2.5 ns typ, 4.0 ns max "
                          "(column alignment of the text extraction is ambiguous; fastest listed value used)"),
]
LVDS_PIN = re.compile(r"GPIOB_(TX|RX)[PN]")


def driver_tr(ref, pinfunction):
    p = part(ref)
    if p.startswith("T20F") and LVDS_PIN.search(pinfunction or ""):
        return 0.44, cite("T20_TR", [0, 3]), "Trion T20 Table 81: LVDS pin used as 3.3 V LVCMOS rise 0.44 ns"
    for rx, tr, key, note in PART_TR:
        if re.search(rx, p):
            if key is None:
                return tr, [{"file": ASE_PDF, "line": None, "pdf": ASE_PDF, "pdf_page": 1, "text": "Rise and Fall Time (Tr/Tf)"}], note
            return tr, cite(key), note
    return DEFAULT_TR_NS, cite("LVC_NO_TR"), (f"{p or ref}: no output rise-time specification in the project's sources "
                                               f"(LVC datasheets point to input transition only) -> 1.0 ns assumed (inference, conservative)")


# ---------------------------------------------------------------- geometry
def gnet(n):
    return GEOM["nets"].get(n)


def daisy_mm(n):
    g = gnet(n)
    if not g or g["pad_count"] < 2:
        return 0.0
    pts = [(p["x"], p["y"]) for p in g["pads"]]
    if len(pts) > 7:
        return g["mst_mm"]
    best = float("inf")
    for perm in itertools.permutations(range(len(pts))):
        if perm[0] > perm[-1]:
            continue
        d = sum(math.dist(pts[a], pts[b]) for a, b in zip(perm, perm[1:]))
        best = min(best, d)
    return round(best, 2)


def l_est(n):
    g = gnet(n)
    if not g:
        return 0.0, "no pads on board"
    if g["missing_joins"] == 0 and g["routed_len_mm"] > 0:
        return g["routed_len_mm"], "routed length (net fully joined)"
    est = max(DETOUR * g["mst_mm"], daisy_mm(n), g["routed_len_mm"])
    return round(est, 2), f"max(1.3 x MST, min daisy chain, routed so far)"


def ends(n):
    out = []
    for nd in NETS.get(n, []):
        if VIRTUAL.match(nd["ref"]):
            continue
        out.append({"ref": nd["ref"], "pin": nd["pin"], "part": part(nd["ref"]), "pintype": nd["pintype"],
                    "pinfunction": nd["pinfunction"]})
    return out


def refsamples(n):
    g = gnet(n)
    return g["mst_reference_samples"] if g else None


# ---------------------------------------------------------------- series-terminated chains (22..47 ohm)
def damping_links(n):
    links = []
    for nd in NETS.get(n, []):
        if not nd["ref"].startswith("R"):
            continue
        ohm = r_ohm(nd["ref"])
        if ohm is None or not (22.0 <= ohm <= 47.0):
            continue
        other = PIN_NET.get((nd["ref"], "2" if nd["pin"] == "1" else "1"))
        if other and not other.startswith("unconnected-") and not re.search(r"VREF|GND|3V3|5V|_COM$", other):
            links.append((other, nd["ref"], ohm))
    return links


def chain_of(n):
    seen, stack, res = {n}, [n], []
    while stack:
        x = stack.pop()
        for other, rref, ohm in damping_links(x):
            res.append({"from": x, "to": other, "resistor": rref, "ohm": ohm})
            if other not in seen:
                seen.add(other)
                stack.append(other)
    return sorted(seen), res


OPERATOR_50 = {"file": "Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md", "line": 82, "pdf": None, "pdf_page": None,
               "text": "lines at 50 ohm only where warranted; encoder differential at 100 ohm only if the interface",
               "note": "operator decision 2026-10-03 (Controlled-impedance process, lines 79-83): the 50 ohm value for "
                       "fast single-ended lines; 'warranted' is decided by the R2 electrical-length test"}
SE_SKEW = {"intra_pair_mm": None, "source": "single-ended net: no length-match requirement found in the driver/receiver "
                                            "datasheets; bus timing budgets were not analysed here (inference)"}
DRIVER_TYPES = ("output", "tri_state", "open_collector")
OSC = re.compile(r"^(ASE-|ASV-)")


def chain_drivers(members):
    """Explicit driver pins (output / tri_state / open_collector) win; an oscillator output wins over everything;
    'bidirectional' pins (all FPGA/MCU GPIO are typed bidirectional in the netlist) count only when no explicit
    driver exists in the chain."""
    explicit, bidir = [], []
    for m in members:
        for nd in NETS.get(m, []):
            if re.match(r"^(J|B|BT|BM|TP)\d", nd["ref"]):
                continue
            if nd["pintype"] in DRIVER_TYPES:
                explicit.append((m, nd))
            elif nd["pintype"] == "bidirectional":
                bidir.append((m, nd))
    osc = [x for x in explicit if OSC.search(part(x[1]["ref"]))]
    return osc or explicit or bidir


def offboard_driver(members):
    for m in members:
        for nd in NETS.get(m, []):
            if nd["ref"] in ("J15001", "J15002"):
                return f"Raspberry Pi CM5 pin via {nd['ref']}.{nd['pin']} ({nd['pinfunction'] or 'connector'}); CM5 GPIO rise time not specified"
            if nd["ref"] == "J1002":
                return "external JTAG programmer via J1002 (service header); driver unknown"
            if nd["ref"].startswith("J"):
                return f"off-board driver via {nd['ref']}.{nd['pin']}"
    return "no on-board driver pin"


# ---------------------------------------------------------------- name rules
EDGE_NAME = re.compile(r"(SCLK|(^|_)CLK(_|$)|CLK_|CCK|TCK|_OSC$|STROBE|FALL_CLK|"
                       r"STEP\d+_(FPGA|BUFFER_OUT|TO_MIA|TO_MX4)$|(ENC\d_[ABZ]|MPG_[AB]|FREQ\d)_FPGA$|"
                       r"(PROBE|TOOLSETTER)_FPGA$)")
CLOCK_PIN = re.compile(r"(^|[_\d])(CLK|SCK|SCLK|CCLK|TCK|OSC1|CLKIN)([_\d]|$)", re.I)
I2C = re.compile(r"(I2C|_SCL\d*$|_SDA\d*$|_SCL_|_SDA_|HDMI0?_?(PORT_)?(SCL|SDA))")
ONEWIRE = re.compile(r"1WIRE")

# functional evidence from the interface specification / datasheets (tier 'spec'); leaf-name regex -> (statement, keys)
FUNC_EVIDENCE = [
    (r"^STEP\d+_(FPGA|BUFFER_OUT|TO_MIA|TO_MX4)$", "step pulses are counted (FPGA step counters, IS-1 D01-2)", ["SPEC01_COUNTS"]),
    (r"^ENC\d+_[AB]_FPGA$", "x4 quadrature counting: every A/B edge is counted (IS-1 CNF3 encoder_count)", ["SPEC01_QUAD"]),
    (r"^ENC\d+_Z_FPGA$", "index captured at the synchronized rising edge (IS-1 INDEX_CAPTURE)", ["SPEC01_INDEX"]),
    (r"^MPG_[AB]_FPGA$", "handwheel counts (IS-1 D01-2)", ["SPEC01_COUNTS"]),
    (r"^(PROBE|TOOLSETTER)_FPGA$", "probe capture latched on the qualified edge (IS-1 PROBE_CAPTURE)", ["SPEC01_PROBE"]),
    (r"^FREQ\d+_FPGA$", "reciprocal frequency measurement times input edges (IS-1 io_feature_bitmap b5)", ["SPEC01_FREQ"]),
    (r"^(HOST_SPI_SCLK|CM_HOST_SPI_SCLK|CM_FWD_SCLK)$", "host-link SCLK: frames are exact counts of rising SCLK edges (IS-1 host link)",
     ["SPEC01_HOST_EDGES"]),
    (r"^(IOL1_L\d_SCLK(_COUNT)?|(ACC|DIC|DOA|DOB)_IOL1_CLK_(BUFFER|MCU))$", "IOL1 card-link SCLK, SPI mode 0, 8.333 MHz (IS-1 4.1)",
     ["SPEC01_IOL1_SCLK"]),
    (r"^(CAN_SPI_SCLK_HOST|CM_CAN_SPI_SCLK|CM_COMMS_FWD_CAN_SPI_SCLK)$", "SPI clock of the MCP2518FD CAN controller", ["MCP2518FD_SCK"]),
    (r"^AI_SCLK_HOST$", "SPI clock of the ADS8684A ADC (through ISO7761)", ["ADS8684_SCLK"]),
    (r"^DO[AB]_SCLK_HOST$", "SPI clock of the TPS274C65 output driver (through ISO7762)", ["TPS274C65_TSPI"]),
    (r"^(CM_SD_CLK|SD_CLK_DAMPED|SD_PORT_CLK)$", "SDIO clock of the CM5 SDIO 2.0 interface", ["CM5_SDIO"]),
]
FUNC_RX = [(re.compile(rx), why, keys) for rx, why, keys in FUNC_EVIDENCE]


def is_edge_sensitive(members):
    """Return (reasons, tiers). tiers: set of 'pin' / 'spec' / 'name' (see R4)."""
    why, tiers, cites = [], set(), []
    for m in members:
        leaf = m.split("/")[-1]
        if I2C.search(leaf) or ONEWIRE.search(leaf):
            continue
        if EDGE_NAME.search(leaf):
            why.append(f"{leaf}: clock/strobe/counted-pulse name")
            tiers.add("name")
        for rx, what, keys in FUNC_RX:
            if rx.search(leaf):
                why.append(f"{leaf}: {what} [spec]")
                tiers.add("spec")
                for k in keys:
                    cites.extend(cite(k, note=f"functional edge evidence for {leaf}"))
        for nd in NETS.get(m, []):
            if not CLOCK_PIN.search(nd["pinfunction"]) or "INH" in nd["pinfunction"]:
                continue
            # input pins named as clocks (original rule), plus CM5 connector pins named as clocks (e.g. SD_CLK);
            # FPGA 'CLKn' clock-capable GPIO names are deliberately NOT evidence (they are bidirectional GPIO)
            if nd["pintype"] == "input":
                why.append(f"{leaf}: drives clock input {nd['ref']}.{nd['pin']} ({nd['pinfunction']}) [pin]")
                tiers.add("pin")
            elif nd["pintype"] == "passive" and nd["ref"] in ("J15001", "J15002"):
                why.append(f"{leaf}: CM5 connector clock pin {nd['ref']}.{nd['pin']} ({nd['pinfunction']}) [pin]")
                tiers.add("pin")
    return why, tiers, cites


# clocked serial buses: level-sampled data / select nets are checked against the bus clock (R4)
def _bus(rx, name, rate, keys, note):
    return (re.compile(rx), name, rate, keys, note)


BUSES = [
    _bus(r"^(HOST_SPI_(MISO|MOSI|CS_N|CS_CMD_N)|CM_HOST_SPI_(MISO|MOSI|CS_CMD_N|CS_FB_N)|CM_FWD_(MOSI|CS_FB_N|CS_CMD_N)|CM_RET_MISO)$",
         "host-link SPI (CM5 -> FPGA)", 6.25, ["SPEC01_HOST_SCLK"], "IS-1: SCLK <= core/8 = 6.25 MHz (budget 5 MHz)"),
    _bus(r"^(IOL1_L\d_(MISO|MOSI|CS_N)|(ACC|DIC|DOA|DOB)_IOL1_(CS|RSP|CMD)_(BUFFER|MCU))$", "IOL1 card link", 8.333,
         ["SPEC01_IOL1_SCLK"], "IS-1 4.1: SCLK = core/6 = 8.333 MHz"),
    _bus(r"^FAST_SR_(DATA|DATA_SOURCE|LOAD_N|LOAD_BUFFER)$", "FPGA status shift register (SN74LV165A)", 8.33, ["SPEC01_SR_SCLK"],
         "IS-1 status registers: 6.25 MHz (EIA/EX8) or 8.33 MHz (MC_slot); the faster rate is used because the FAST_SR -> "
         "register mapping is not stated (inference)"),
    _bus(r"^(CAN_SPI_(MISO|MOSI|CS_N)_HOST|CM_COMMS_(FWD|RET)_CAN_SPI_(MISO|MOSI|CS_N)|CM_CAN_SPI_(MISO|MOSI|CS_N)|CAN_CTRL_(MOSI|MOSI_RAW|CS_N|CS_RAW|MISO))$",
         "CAN controller SPI (MCP2518FD)", 20.0, ["MCP2518FD_SCK"], "MCP2518FD: up to 20 MHz SPI clock"),
    _bus(r"^(AI_(SDO|SDI|CS_N)_HOST|AI_ADC_(SDO|SDI|CS_N)|AI_SDO_ISOLATED)$", "AI SPI (ADS8684A via ISO7761)", 17.0, ["ADS8684_SCLK"],
         "ADS8684A: serial clock frequency max 17 MHz (value on the line after the cited row)"),
    _bus(r"^DO[AB]_(SDI|SDO|CS_N)_(HOST|FIELD)$", "DO SPI (TPS274C65 via ISO7762)", 10.0, ["TPS274C65_TSPI"],
         "TPS274C65: SCLK period min 100 ns (next line) -> 10 MHz"),
    _bus(r"^(AO\d_(CS_N_HOST|DAC_CS_N|DAC_SDI|DAC_SDO|SDO_ISOLATED))$", "AO SPI (AD5683R via ISO7761, STM32G031 master)", 32.0,
         ["SPEC01_STM32_SPI"], "bounded by the STM32G031 32 Mbit/s SPI rating quoted in IS-1 (the AD5683R datasheet is not in "
                               "the project sources; inference that the STM32 rate bounds this bus)"),
    _bus(r"^(FPGA_FLASH_(MISO|MOSI|CS_N)|FPGA_CFG_CSI)$", "FPGA configuration flash (W25Q32JV)", 133.0, ["W25Q32_CLK"],
         "W25Q32JV: up to 133 MHz SPI clock"),
    _bus(r"^(RS485_UART_(TX|RX)_HOST|CM_COMMS_FWD_RS485_(TX|DE)|CM_COMMS_RET_RS485_RX|CM_RS485_(TX|RX)|RS485_DE_HOST)$", "RS-485 UART (ISOW1432)", 12.0, ["ISOW1432_RATE"],
         "ISOW1432: maximum 12 Mbps (bit rate compared with the settle-limited rate: settle <= half a bit)"),
    _bus(r"^(CAN_(TXD|RXD)(_HOST)?|CM_COMMS_FWD_CAN_TXD|CM_COMMS_RET_CAN_RXD)$", "CAN FD transceiver logic (ISOW1044)", 5.0,
         ["ISOW1044_RATE"], "ISOW1044: CAN FD up to 5 Mbps"),
]


def bus_check(leaf, limit_mhz):
    for rx, name, rate, keys, note in BUSES:
        if rx.search(leaf):
            src = [c for k in keys for c in cite(k)]
            return {"bus": name, "bus_clock_or_bit_rate_MHz": rate, "basis": note, "source": src,
                    "settle_limit_MHz": limit_mhz, "margin_x": round(limit_mhz / rate, 2) if limit_mhz else None,
                    "pass": bool(limit_mhz is not None and limit_mhz >= rate)}
    return None


def partner(n):
    for a, b in (("_P", "_N"), ("_N", "_P")):
        if n.endswith(a):
            return n[: -len(a)] + b
    if n.endswith("RS485_A"):
        return n[:-1] + "B"
    if n.endswith("RS485_B"):
        return n[:-1] + "A"
    if n.endswith("CAN_H"):
        return n[:-1] + "L"
    if n.endswith("CAN_L"):
        return n[:-1] + "H"
    return None


# ---------------------------------------------------------------- interface groups
NOTE_SKEW_DRAFT = ("Claude-authored draft (no datasheet value): intra-pair length difference <= 2.5 mm "
                   f"(= {2.5 * TPD_STRIP:.1f} ps on In3, < 1 % of the 4-5 ns driver edge)")


def skew_note_for(tr_ns):
    """Same 2.5 mm draft limit, stated against the group's own driver edge (17.7 ps vs t_r)."""
    ps = 2.5 * TPD_STRIP
    return ("Claude-authored draft (no datasheet value): intra-pair length difference <= 2.5 mm "
            f"(= {ps:.1f} ps on In3 = {100.0 * ps / (tr_ns * 1000.0):.2f} % of this group's {tr_ns:g} ns driver edge)")
GROUPS = [
    {"id": "USB2", "rx": r"/motherboard_compute/(CM_USB2|USB_HOST|USB_RECOVERY)_[PN]$", "interface": "USB 2.0 High-Speed (480 Mb/s)",
     "class": "DIFF_90", "target": 90, "tol_pct": 10, "rule": "R1",
     "source": cite("CM5_USB2_90", [0]) + cite("FSUSB42_HS") + cite("R41B_IMPEDANCE", [1, 3], "tolerance source (r41b stackup request)"),
     "skew": {"intra_pair_mm": 0.15, "source": cite("CM5_USB2_90", [1])},
     "why": "CM5 datasheet requires 90 ohm differential for the USB 2.0 pair; FSUSB42 is a 480 Mb/s HS switch, so both "
            "sides of the mux carry HS signalling (USB-A J15005 and USB-C J15006 legs included)."},
    {"id": "HDMI_TMDS", "rx": r"/motherboard_compute/CM_HDMI0_(TX[0-2]|CLK)_[PN]$", "interface": "HDMI 2.0 TMDS (HDMI0)",
     "class": "DIFF_100", "target": 100, "tol_pct": 10, "rule": "R1",
     "source": cite("CM5_HDMI_100", [0]) + cite("TPD12S016_SKEW") + cite("R41B_IMPEDANCE", [2, 3], "tolerance source (r41b stackup request)"),
     "skew": {"intra_pair_mm": 0.15, "inter_pair_mm": 25.0, "source": cite("CM5_HDMI_100", [1, 2])},
     "why": "CM5 datasheet: HDMI signals must be routed as 100 ohm differential pairs."},
    {"id": "ETH_MDI", "rx": r"/motherboard_compute/CM_Ethernet_Pair[0-3]_[PN]$", "interface": "Ethernet 1000BASE-T MDI (CM5 PHY to MagJack)",
     "class": "DIFF_100", "target": 100, "tol_pct": 10, "rule": "R1",
     "source": cite("CM5_ETH_100", [0]) + cite("R41B_IMPEDANCE", [2, 3], "tolerance source (r41b stackup request)"),
     "skew": {"intra_pair_mm": 0.15, "inter_pair_mm": 50.0, "source": cite("CM5_ETH_100", [1, 2])},
     "why": "CM5 datasheet: route the Ethernet signals as 100 ohm differential pairs."},
]


def classify():
    out = {}
    tr_strip_note = (f"t_pd(In3 stripline, Cohn) = {TPD_STRIP:.3f} ps/mm, t_pd(outer microstrip, H&J) = {TPD_MICRO:.3f} ps/mm; "
                     f"L_crit uses the slower {TPD:.3f} ps/mm")
    done = set()

    def put(n, rec):
        rec.setdefault("net", n)
        g = gnet(n)
        rec.setdefault("mst_mm", g["mst_mm"] if g else None)
        rec.setdefault("routed_mm", g["routed_len_mm"] if g else None)
        rec.setdefault("missing_joins", g["missing_joins"] if g else None)
        rec.setdefault("routed_by_layer_mm", g["routed_len_by_layer_mm"] if g else None)
        le, basis = l_est(n)
        rec.setdefault("l_est_mm", le)
        rec.setdefault("l_est_basis", basis)
        rec.setdefault("daisy_chain_mm", daisy_mm(n))
        rec.setdefault("end_parts", ends(n))
        rec.setdefault("reference_samples_on_mst", refsamples(n))
        rec.setdefault("candidate_sources", CAND.get(n, []))
        out[n] = rec
        done.add(n)

    # R1 spec-mandated groups
    for G in GROUPS:
        for n in CAND:
            if re.search(G["rx"], n):
                put(n, {"interface": G["interface"], "group": G["id"], "pair_partner": partner(n), "class": G["class"],
                        "target_ohm": G["target"], "tolerance_pct": G["tol_pct"], "rule": G["rule"],
                        "source_citations": G["source"], "skew": G["skew"], "rationale": G["why"]})

    # R3 field differential groups (R2 length test, group-wide)
    def field_group(gid, rx, interface, tr, tr_cite, tr_note, cls_if, target_if, req_cite, why_if, skew_if, extra=None):
        members = [n for n in CAND if re.search(rx, n)]
        lc = lcrit_mm(tr)
        worst = max(members, key=lambda m: l_est(m)[0])
        need = any(l_est(m)[0] > lc for m in members)
        if skew_if is not None and skew_if.get("source") == NOTE_SKEW_DRAFT:
            skew_if = dict(skew_if, source=skew_note_for(tr))
        for n in members:
            le = l_est(n)[0]
            rec = {"interface": interface, "group": gid, "pair_partner": partner(n), "rule": "R2+R3",
                   "t_r_ns": tr, "t_r_basis": tr_note, "t_r_citation": tr_cite,
                   "l_crit_mm": round(lc, 1), "l_crit_basis": "0.1 * t_r / t_pd (ISOW1432 Eq. 3); " + tr_strip_note,
                   "l_crit_citation": cite("ISOW1432_STUB"),
                   "group_worst_net": worst, "group_worst_l_est_mm": l_est(worst)[0], "net_exceeds_l_crit": le > lc}
            if need:
                rec.update({"class": cls_if, "target_ohm": target_if, "tolerance_pct": 10, "source_citations": req_cite,
                            "skew": skew_if, "rationale": why_if.format(lc=lc, worst=worst.split('/')[-1], wl=l_est(worst)[0])})
            else:
                rec.update({"class": "NONE", "target_ohm": None, "tolerance_pct": None, "source_citations": req_cite,
                            "skew": skew_if, "rationale": f"no controlled impedance required: worst L_est {l_est(worst)[0]:.0f} mm "
                                                         f"<= L_crit {lc:.0f} mm for t_r {tr} ns. Route as a symmetric coupled pair."})
            if extra:
                rec.update(extra)
            put(n, rec)

    skew_draft = {"intra_pair_mm": 2.5, "source": NOTE_SKEW_DRAFT}
    # RS-485: ISOW1432 driver t_r min 4 ns (5 V block) / 6 ns (3.3 V block); VISOOUT mode not fixed here -> 4 ns
    field_group("RS485", r"/motherboard_comms/RS485_[AB]$", "RS-485 half-duplex field bus (ISOW1432, 12 Mb/s)",
                4.0, cite("ISOW1432_TR"), "ISOW1432 12-Mb/s driver differential output rise time, min 4 ns (VISOOUT = 5 V block; "
                "6 ns min at 3.3 V); the lower value is used because the MODE strap is not part of this analysis",
                "DIFF_120", 120,
                cite("ISOW1432_RT_Z0") + cite("ISOW1432_STUB") + cite("SLLU337_CTRL_Z", None, "TI EVM schematic marks A/B as a controlled impedance line"),
                "on-board RT = 120 ohm (R14832 CRCW2512120R) and ISOW1432: RT matches the cable Z0 -> line Z0 = 120 ohm; "
                "the PCB run (worst {worst} L_est {wl:.0f} mm) exceeds the ISOW1432 stub limit L_crit {lc:.0f} mm, so the "
                "PCB pair is part of the transmission line and is matched to 120 ohm. Buildable only on F.Cu/B.Cu inside "
                f"the board's 0.20 mm track minimum (In3.Cu method B maximum {ZMAX_IN3_W020:.1f} ohm at w 0.20; "
                "provisional-geometry.json); the A/B nets do not end "
                "in _P/_N, so KiCad does not treat them as a diff pair (width + a custom A-B clearance rule only).",
                skew_draft)
    # CAN: ISOW1044 tR typ 27 ns (only value listed)
    field_group("CAN", r"/motherboard_comms/CAN_[HL]$", "CAN / CAN FD field bus (ISOW1044)",
                27.0, cite("ISOW1044_TR"), "ISOW1044 differential output signal rise time 27 ns (only value listed, typ)",
                "DIFF_120", 120, cite("ISOW1044_TR") + cite("ISOW1044_TERM"),
                "worst {worst} L_est {wl:.0f} mm exceeds L_crit {lc:.0f} mm", skew_draft)
    # Encoder / MPG / FREQ inputs: remote RS-422 driver, t_r assumed = AM26C31 typ 5 ns (inference)
    field_group("RS422_RX", r"/motherboard_fast_inputs/(ENC\d_[ABZ]|MPG_[AB]|FREQ\d)_[PN]$",
                "RS-422 differential inputs (encoders, MPG, frequency) into AM26LV32E",
                5.0, cite("AM26C31_TR"), "remote line driver unknown: assumed RS-422 class with the AM26C31 typ 5 ns edge "
                "(inference; the project's own RS-422 driver datasheet)",
                "DIFF_100", 100, cite("AM26LV32E_RT") + cite("AM26LV32E_RATE"),
                "worst {worst} L_est {wl:.0f} mm > L_crit {lc:.0f} mm, so the PCB pair is part of the terminated line. "
                "AM26LV32E: RT must be within 20 % of the cable impedance and can vary from about 80 to 120 ohm (for the "
                "100-ohm twisted pair the datasheet characterises with); the on-board RT = 120 ohm (R7001..R7016 "
                "CRCW1210120R) is +20 % of a 100-ohm cable, at the edge of that window. The PCB pair follows the 100-ohm "
                "CABLE, not the 120-ohm RT -> PCB pair 100 ohm differential. A 120-ohm pair was considered and rejected: "
                f"it is not buildable on In3.Cu inside the board's 0.20 mm track minimum (method B maximum {ZMAX_IN3_W020:.1f} "
                "ohm, provisional-geometry.json) and would confine 32 nets to the outer layers.",
                skew_draft)
    # STEP/DIR outputs: AM26C31 t_r typ 5 ns, specified into RL = 100 ohm, no on-board termination
    field_group("RS422_TX", r"/motherboard_motors/(STEP|DIR)\d+_[PN]$", "RS-422 STEP/DIR outputs (AM26C31) to motor drives",
                5.0, cite("AM26C31_TR"), "AM26C31 tr(OD) typ 5 ns (max 10 ns; no min listed)",
                "DIFF_100", 100, cite("AM26C31_RL100"),
                "INFERENCE (not a datasheet requirement): no on-board termination, and the AM26C31 datasheet states no line "
                "impedance. It describes driving balanced lines such as twisted pair, and its only differential load is "
                "the RL = 100 ohm TEST CONDITION of the VOD specification (am26c31.txt l637). The PCB pair is set to the "
                "100-ohm twisted pair that test load represents. Worst {worst} L_est {wl:.0f} mm > L_crit {lc:.0f} mm, so "
                "the PCB run is part of the line -> PCB pair at 100 ohm differential (inference).", skew_draft)

    # sideband / termination nodes of differential interfaces
    SIDE = {
        r"/motherboard_comms/(CAN|RS485)_TERM$": "termination-resistor node (static, switched by the field jumper); not part of the signal path when open",
        r"/motherboard_compute/ETH_PHY_CT$": "PHY centre tap, AC-returned by C15047; common-mode node, 3.75 mm",
        r"/motherboard_compute/CM_Ethernet_nLED\d$": "MagJack LED drive, static/slow",
        r"/motherboard_compute/(CM_HDMI0_HOTPLUG|HDMI_PORT_HPD)$": "HDMI hot-plug detect: static level",
        r"/motherboard_compute/(CM_HDMI0_CEC|HDMI_PORT_CEC)$": "HDMI CEC: single-wire bus with ms bit times",
        r"/motherboard_compute/HDMI_PORT_5V$": "HDMI +5 V supply pin",
        r"/motherboard_compute/(USB_CC\d|CM_USB_OTG_ID|USB_ID_BUFFERED)$": "USB-C CC / OTG ID: DC configuration signalling",
        r"/motherboard_compute/HDMI_ENABLE$": "TPD12S016 enable: static level",
    }
    for n in CAND:
        if n in done:
            continue
        for rx, why in SIDE.items():
            if re.search(rx, n):
                put(n, {"interface": "differential-interface sideband", "group": "SIDEBAND", "pair_partner": None, "class": "NONE",
                        "target_ohm": None, "tolerance_pct": None, "rule": "R4", "rationale": "no controlled impedance required: " + why,
                        "source_citations": cite("CM5_HDMI_SIDEBAND") if "HDMI" in n else [], "skew": None})
                break

    # R6 1-Wire identity line (handled before I2C: it is buffered by an I2C repeater but it is not an I2C bus)
    for n in CAND:
        if n in done:
            continue
        leaf = n.split("/")[-1]
        if ONEWIRE.search(leaf):
            le = l_est(n)[0]
            settle = 6 * le * TPD / 1000.0
            put(n, {"interface": "1-Wire identity line (open drain, through the TCA9517A repeater)", "group": "ONE_WIRE",
                    "pair_partner": None, "class": "NONE", "target_ohm": None, "tolerance_pct": None, "rule": "R6",
                    "settle_ns": round(settle, 1),
                    "rationale": f"no controlled impedance required: XF module 1-Wire identity line, read by the host only at "
                                 f"qualification and after module replacement (IS-1); 1-Wire bit timing is in microseconds "
                                 f"(1-Wire specification not in the project sources: inference); reflections on this line "
                                 f"settle in {settle:.1f} ns (6 one-way delays of L_est {le:.0f} mm), several orders of "
                                 f"magnitude shorter.",
                    "source_citations": cite("SPEC01_ONEWIRE") + cite("SPEC03_MOD_ID"), "skew": None})

    # R5 I2C
    for n in CAND:
        if n in done:
            continue
        leaf = n.split("/")[-1]
        if I2C.search(leaf):
            le = l_est(n)[0]
            settle = 6 * le * TPD / 1000.0
            put(n, {"interface": "I2C / SMBus (open drain)", "group": "I2C", "pair_partner": None, "class": "NONE",
                    "target_ohm": None, "tolerance_pct": None, "rule": "R5",
                    "settle_ns": round(settle, 1),
                    "rationale": f"no controlled impedance required: I2C receivers suppress spikes < 50 ns and the fastest "
                                 f"open-drain edge on the board is the ISO1540 fall time (>= 8 ns); reflections on this line "
                                 f"settle in {settle:.1f} ns (6 one-way delays of L_est {le:.0f} mm), inside the 50 ns filter.",
                    "source_citations": cite("TLC59116_SPIKE") + cite("TCA9534_SPIKE") + cite("ISO1540_TF", [0]), "skew": None})

    # R4 single-ended chains
    for n in sorted(CAND):
        if n in done:
            continue
        members, links = chain_of(n)
        members = [m for m in members if m not in done or m == n]
        drvs = chain_drivers(members)
        trs = [(driver_tr(nd["ref"], nd["pinfunction"]), m, nd) for m, nd in drvs]
        if trs:
            (tr, trc, trn), dnet, dnd = min(trs, key=lambda x: x[0][0])
            drv_desc = f"{dnd['ref']}.{dnd['pin']} {part(dnd['ref'])} on {dnet.split('/')[-1]}"
        else:
            drv_desc = offboard_driver(members)
            tr, trc, trn = DEFAULT_TR_NS, cite("LVC_NO_TR"), (drv_desc + " -> 1.0 ns assumed (inference, conservative)")
        lc = lcrit_mm(tr)
        le_chain = round(sum(l_est(m)[0] for m in members), 2)
        edge, tiers, fcites = is_edge_sensitive(members)
        settle = 6 * le_chain * TPD / 1000.0
        tier = "pin" if "pin" in tiers else ("spec" if "spec" in tiers else ("name" if "name" in tiers else None))
        base = {"group": "SE_CHAIN", "pair_partner": None, "rule": "R2+R4", "chain_members": members, "chain_series_resistors": links,
                "chain_driver": drv_desc, "t_r_ns": tr, "t_r_basis": trn, "t_r_citation": trc, "l_crit_mm": round(lc, 1),
                "l_crit_basis": "0.1 * t_r / t_pd (ISOW1432 Eq. 3); " + tr_strip_note, "l_crit_citation": cite("ISOW1432_STUB"),
                "chain_l_est_mm": le_chain, "edge_sensitive_evidence": edge, "edge_evidence_tiers": sorted(tiers),
                "edge_evidence_strongest": tier, "settle_ns": round(settle, 1),
                "level_sampled_max_clock_MHz": round(1000.0 / (2 * settle), 1) if settle > 0 else None, "skew": SE_SKEW}
        if edge and le_chain > lc:
            cls, tgt, tol = "IMP_50", 50, 10
            src = ([OPERATOR_50] + [dict(c, note="driver rise time used for L_crit") for c in trc]
                   + [dict(c, note="L_crit criterion (one-way delay < t_r / 10)") for c in cite("ISOW1432_STUB")]
                   + fcites
                   + (cite("LVC1G125_VOL", None, "derived: LVC output R <= 0.55 V / 24 mA = 22.9 ohm; with the 33 ohm series "
                                                 "resistor the source is <= 55.9 ohm, i.e. a 50 ohm line (+12 %)") if links else []))
            why = (f"edge-sensitive ({edge[0]}; strongest evidence tier: {tier}); chain L_est {le_chain:.0f} mm > L_crit "
                   f"{lc:.0f} mm for t_r {tr} ns -> controlled 50 ohm single-ended (operator: fast single-ended lines at 50 ohm "
                   f"where warranted; the 50 ohm value is operator policy, not a datasheet requirement)"
                   + ("; series-terminated chain: the 22-47 ohm source resistor only damps reflections against a defined Z0" if links else ""))
            iface = "fast single-ended (clock / counted pulse / edge capture)"
        elif edge:
            cls, tgt, tol, src = "NONE", None, None, []
            why = f"no controlled impedance required: edge-sensitive but lumped, chain L_est {le_chain:.0f} mm <= L_crit {lc:.0f} mm (t_r {tr} ns)"
            iface = "single-ended clock / pulse (short)"
        else:
            cls, tgt, tol, src = "NONE", None, None, []
            why = (f"no controlled impedance required: level-sampled/static signal (no clock or counted-edge receiver); "
                   f"reflections settle in {settle:.1f} ns (6 one-way delays over chain L_est {le_chain:.0f} mm), "
                   f"adequate for synchronous sampling up to {1000.0 / (2 * settle):.0f} MHz bus clock" if settle > 0 else
                   "no controlled impedance required: level-sampled/static signal, no on-board length")
            iface = "single-ended level/static"
        def with_bus(m, rec):
            if iface != "single-ended level/static":
                return rec
            leaf = m.split("/")[-1]
            lim = base["level_sampled_max_clock_MHz"]
            bc = bus_check(leaf, lim)
            if bc is None:
                uart = bool(re.search(r"(^|_)(TX|RX)(_SOURCE|_BUFFER|_HOST)?$|UART|SERVICE_(TX|RX)", leaf))
                bc = {"bus": None, "settle_limit_MHz": lim,
                      "note": ("UART line: bit rate not stated in the project sources; the settle limit is the maximum safe "
                               "bit rate (open item for firmware)" if uart else
                               "not on an identified clocked serial bus (level / enable / alarm / direction / reset / status "
                               "line): no bus clock applies; the settle limit is reported for reference")}
                rec["rationale"] += "; " + bc["note"]
            else:
                rec["rationale"] += (f"; bus clock check: {bc['bus']} at {bc['bus_clock_or_bit_rate_MHz']:g} MHz vs settle limit "
                                     f"{lim} MHz -> {'PASS' if bc['pass'] else 'FAIL'} (margin x{bc['margin_x']})")
            rec["bus_clock_check"] = bc
            return rec

        for m in members:
            if m in done or m not in CAND and m != n:
                continue
            rec = dict(base)
            rec.update({"interface": iface, "class": cls, "target_ohm": tgt, "tolerance_pct": tol, "source_citations": src,
                        "rationale": why})
            put(m, with_bus(m, rec))
        # chain members that are not candidates are added too (they share the decision)
        for m in members:
            if m not in out and m in NETS:
                rec = dict(base)
                rec.update({"interface": iface, "class": cls, "target_ohm": tgt, "tolerance_pct": tol, "source_citations": src,
                            "rationale": why + " (added as a series-terminated chain member)"})
                put(m, with_bus(m, rec))
    return out


def main():
    out = classify()
    summary = {}
    for n, r in out.items():
        summary.setdefault(r["class"], []).append(n)
    groups = {}
    for n, r in out.items():
        if r["class"] != "NONE":
            groups.setdefault(f"{r['class']}:{r['group']}:{r['interface']}", []).append(n)
    interfaces = {}
    for n, r in out.items():
        key = r["group"] if r["group"] != "SE_CHAIN" else f"SE_CHAIN:{r['class']}"
        it = interfaces.setdefault(key, {"interface": set(), "classes": set(), "target_ohm": set(), "nets": 0,
                                         "parts": set(), "datasheets": set(), "t_r_ns": set(), "l_crit_mm": set(),
                                         "worst_l_est_mm": 0.0})
        it["interface"].add(r["interface"])
        it["classes"].add(r["class"])
        if r.get("target_ohm"):
            it["target_ohm"].add(r["target_ohm"])
        it["nets"] += 1
        for e in r["end_parts"]:
            it["parts"].add(e["part"][:40])
        for c in (r.get("source_citations") or []) + (r.get("t_r_citation") or []):
            it["datasheets"].add(c["file"])
        if r.get("t_r_ns") is not None:
            it["t_r_ns"].add(r["t_r_ns"])
        if r.get("l_crit_mm") is not None:
            it["l_crit_mm"].add(r["l_crit_mm"])
        it["worst_l_est_mm"] = max(it["worst_l_est_mm"], r.get("chain_l_est_mm") or r.get("l_est_mm") or 0.0)
    interfaces = {k: {kk: (sorted(vv) if isinstance(vv, set) else vv) for kk, vv in v.items()} for k, v in sorted(interfaces.items())}
    doc = {
        "title": "ROOT104 controlled-impedance net inventory",
        "interfaces": interfaces,
        "stamp": "PROVISIONAL - FAB STACKUP CONFIRMATION REQUIRED",
        "board": "C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/motherboard-bounded-merged-candidate.kicad_pcb",
        "board_sha256": "70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc",
        "netlist": NETLIST,
        "rules": __doc__,
        "constants": {"tpd_in3_ps_per_mm": round(TPD_STRIP, 4), "tpd_outer_ps_per_mm": round(TPD_MICRO, 4),
                      "eeff_in3": round(EE_STRIP, 4), "eeff_outer_w0.36": round(EE_MICRO, 4), "detour_factor": DETOUR,
                      "default_tr_ns": DEFAULT_TR_NS, "lcrit_formula": "0.1 * t_r / t_pd"},
        "unconnected_cm5_high_speed_pins": "54 CM5 MIPI0/1, PCIe, USB3 and HDMI1 pins on J15001/J15002 are 'unconnected-' nets (no copper) -> no class",
        "counts": {k: len(v) for k, v in summary.items()},
        "edge_evidence_summary_IMP_50": dict(sorted(
            {t: sum(1 for r in out.values() if r["class"] == "IMP_50" and r.get("edge_evidence_strongest") == t)
             for t in ("pin", "spec", "name")}.items())),
        "bus_clock_check_summary": {
            "level_sampled_nets": sum(1 for r in out.values() if r.get("bus_clock_check")),
            "on_identified_clocked_bus": sum(1 for r in out.values() if (r.get("bus_clock_check") or {}).get("bus")),
            "pass": sum(1 for r in out.values() if (r.get("bus_clock_check") or {}).get("pass")),
            "fail": sorted(n for n, r in out.items() if (r.get("bus_clock_check") or {}).get("bus")
                           and not r["bus_clock_check"]["pass"]),
            "per_bus": {b: {"nets": sum(1 for r in out.values() if (r.get("bus_clock_check") or {}).get("bus") == b),
                            "clock_MHz": next(r["bus_clock_check"]["bus_clock_or_bit_rate_MHz"] for r in out.values()
                                              if (r.get("bus_clock_check") or {}).get("bus") == b),
                            "min_settle_limit_MHz": min(r["bus_clock_check"]["settle_limit_MHz"] for r in out.values()
                                                        if (r.get("bus_clock_check") or {}).get("bus") == b),
                            "min_margin_x": min(r["bus_clock_check"]["margin_x"] for r in out.values()
                                                if (r.get("bus_clock_check") or {}).get("bus") == b)}
                        for b in sorted({r["bus_clock_check"]["bus"] for r in out.values()
                                         if (r.get("bus_clock_check") or {}).get("bus")})},
            "uart_rate_open_items": sorted(n for n, r in out.items() if (r.get("bus_clock_check") or {}).get("bus") is None
                                           and "UART" in (r.get("bus_clock_check") or {}).get("note", "")),
        },
        "line_convention": "every citation 'line' counts LF characters only (the numbering of grep -n / sed -n); a lone CR "
                           "is not a line break (repair 2026-10-03: isow1044.txt has 15 lone CRs)",
        "controlled_groups": {k: sorted(v) for k, v in sorted(groups.items())},
        "nets": dict(sorted(out.items())),
    }
    json.dump(doc, open(HERE + "controlled-nets.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("counts", doc["counts"])
    for k, v in sorted(groups.items()):
        print(f"{len(v):3d}  {k}")


if __name__ == "__main__":
    main()
