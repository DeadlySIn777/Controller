"""Generate the six-joint transmitter schematic; retain the original tx_bank evidence."""
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "tx_six"
NS = uuid.UUID("a3ec4094-db60-40ac-9f5d-e3f30c04641a")


def uid(name):
    return str(uuid.uuid5(NS, name))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    design = json.loads((ROOT / "hardware/electrical-design.json").read_text(encoding="utf-8"))
    channels = [c for c in design["channels"] if c["kind"] == "step_dir"]
    if len(channels) != 12:
        raise ValueError("This schematic implements exactly the baseline six-joint transmitter allocation")
    root_id = uid("six-joint-transmitter")
    driver_pins = [
        (1,"1A",-12.7,15.24,0,"input"),(2,"1Y",12.7,15.24,180,"tri_state"),
        (3,"1Z",12.7,10.16,180,"tri_state"),(4,"G",-12.7,25.4,0,"input"),
        (5,"2Z",12.7,-5.08,180,"tri_state"),(6,"2Y",12.7,0,180,"tri_state"),
        (7,"2A",-12.7,0,0,"input"),(8,"GND",0,-45.72,90,"power_in"),
        (9,"3A",-12.7,-15.24,0,"input"),(10,"3Y",12.7,-15.24,180,"tri_state"),
        (11,"3Z",12.7,-20.32,180,"tri_state"),(12,"~{G}",-12.7,30.48,0,"input"),
        (13,"4Z",12.7,-35.56,180,"tri_state"),(14,"4Y",12.7,-30.48,180,"tri_state"),
        (15,"4A",-12.7,-30.48,0,"input"),(16,"VCC",0,40.64,270,"power_in")]
    rectangle = '(rectangle (start -10.16 38.1) (end 10.16 -43.18) (stroke (width 0.254) (type default)) (fill (type background)))'
    two_pins = [(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    resistor = '(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
    capacitor = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
                '(polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
                '(polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))' \
                '(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    library = [symbol("AM26C31IPWR",driver_pins,rectangle), symbol("R",two_pins,resistor,"R"),
               symbol("C",two_pins,capacitor,"C")]
    connectors = {}
    for count in (3,8,16):
        pins = [(i,str(i),-5.08,-(i-1)*2.54,0,"passive") for i in range(1,count+1)]
        body = f'(rectangle (start -2.54 2.54) (end 2.54 {-count*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        library.append(symbol(f"Conn{count}",pins,body,"J"))
        connectors[count] = pins
    library.append(symbol("PWR_FLAG",[(1,"pwr",0,0,90,"power_out")],"","#FLG"))
    items, pins_by_ref = [], {}

    def place(name, ref, value, x, y, pins, footprint="", mpn=""):
        pins_by_ref[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        props = f'(property "Reference" {quote(ref)} (at {x+4} {y-5} 0) {effects()})' \
                f'(property "Value" {quote(value)} (at {x+4} {y-2.5} 0) {effects()})' \
                f'(property "Footprint" {quote(footprint)} (at {x} {y} 0) {effects(extra="hide")})' \
                f'(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) '
                     f'(in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) '
                     f'(dnp no) (uuid "{uid(ref)}") {props}'
                     f'(instances (project "tx_six" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')

    def label(ref, pin, net, dx=0, dy=0):
        x,y = pins_by_ref[ref][str(pin)]
        ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')

    def note(x,y,value,size=1.25):
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value)}"))')

    mapping = []
    # Real PW16 pin groups: A, noninverting Y, inverting Z.
    pin_groups = ((1,2,3),(7,6,5),(9,10,11),(15,14,13))
    for bank in range(3):
        offset = bank * 190.5
        dx,dy = offset + 116.84,160.02
        driver = f"U{bank+1}"
        place("AM26C31IPWR",driver,"AM26C31IPWR",dx,dy,driver_pins,
              "Package_SO:TSSOP-16_4.4x5mm_P0.65mm","AM26C31IPWR")
        driver_nets = {4:"TX_PERMIT",8:"LOGIC_GND",12:"SIGNAL_5V",16:"SIGNAL_5V"}
        bank_channels = sorted((c for c in channels if c["component"] == f"TX{bank}"), key=lambda c:c["device_channel"])
        if [c["device_channel"] for c in bank_channels] != [1,2,3,4]:
            raise ValueError("Each baseline transmitter must use channels 1–4 exactly once")
        for local, channel in enumerate(bank_channels):
            index = bank*4+local
            net = channel["id"]
            a,y,z = pin_groups[local]
            driver_nets.update({a:net+"_D", y:net+"_P", z:net+"_N"})
            x = offset+22.86+local*27.94
            series, pull = f"R{index+1}", f"R{index+13}"
            place("R",series,"33R 1%",x,66.04,two_pins,"Resistor_SMD:R_0603_1608Metric")
            label(series,1,channel["logic_net"],dy=-5.08)
            label(series,2,net+"_D",dy=5.08)
            place("R",pull,"10k 1%",x,96.52,two_pins,"Resistor_SMD:R_0603_1608Metric")
            label(pull,1,net+"_D",dy=-5.08)
            label(pull,2,"LOGIC_GND",dy=5.08)
            mapping.append({"channel":net,"ledger_component":channel["component"],"driver":driver,
                            "device_channel":local+1,"input_pin":a,"positive_pin":y,"negative_pin":z,
                            "series_resistor":series,"input_pulldown":pull,"logic_net":channel["logic_net"],
                            "terminal_positive":f"JTX{bank}.{local*2+1}","terminal_negative":f"JTX{bank}.{local*2+2}"})
        for pin,net in driver_nets.items():
            px = pins_by_ref[driver][str(pin)][0]
            label(driver,pin,net,0 if pin in (8,16) else -15.24 if px<dx else 7.62,
                  -5.08 if pin == 16 else 5.08 if pin == 8 else 0)
        permit = f"R{25+bank}"
        place("R",permit,"10k 1%",offset+48.26,167.64,two_pins,"Resistor_SMD:R_0603_1608Metric")
        label(permit,1,"TX_PERMIT",dy=-5.08)
        label(permit,2,"LOGIC_GND",dy=5.08)
        for local,(value,x) in enumerate((("100nF 25V X7R",offset+142.24),("1uF 25V X7R",offset+165.1))):
            ref = f"C{bank*2+local+1}"
            place("C",ref,value,x,66.04,two_pins,"Capacitor_SMD:C_0603_1608Metric")
            label(ref,1,"SIGNAL_5V",dy=-5.08)
            label(ref,2,"LOGIC_GND",dy=5.08)
        connector = f"JTX{bank}"
        place("Conn8",connector,"FIELD TERMINALS / MPN TBD",offset+142.24,231.14,connectors[8])
        terms = sorted((t for t in design["terminals"] if t["connector"] == connector),key=lambda t:t["position"])
        if [t["position"] for t in terms] != list(range(1,9)):
            raise ValueError("Transmitter terminal allocation must contain positions 1–8")
        for term in terms:
            label(connector,term["position"],term["net"],dx=-20.32)
        note(offset+17.78,38.1,f"BANK TX{bank} / {driver}: JOINTS {bank*2} AND {bank*2+1}",1.8)
        note(offset+17.78,218.44,f"Place C{bank*2+1} close to {driver} pins 16/8.\nJTX{bank} matches ledger positions 1–8; reference is separate.")

    logic_nets = ["SIGNAL_5V","LOGIC_GND","TX_PERMIT"]+[c["logic_net"] for c in channels]+["LOGIC_GND"]
    place("Conn16","JLOGIC1","LOGIC / SUPPLY BOUNDARY",60.96,299.72,connectors[16])
    for pin,net in enumerate(logic_nets,1):
        label("JLOGIC1",pin,net,dx=-30.48)
    place("Conn3","JREF1","REFERENCE BOUNDARY",228.6,299.72,connectors[3])
    for pin in range(1,4):
        label("JREF1",pin,"LOGIC_GND",dx=-20.32)
    for index,net in enumerate(("SIGNAL_5V","LOGIC_GND"),1):
        ref = f"#FLG0{index}"
        place("PWR_FLAG",ref,"EXT SUPPLY",330.2+(index-1)*35.56,342.9,[(1,"pwr",0,0,90,"power_out")])
        label(ref,1,net,dy=5.08)
    note(17.78,15.24,"BASELINE SIX-JOINT DIFFERENTIAL TRANSMITTER - SCHEMATIC BLOCK r0.2",2.1)
    note(17.78,25.4,"12 STEP/DIR signals / 3 AM26C31IPWR banks. No PCB, line protection, external permission latch or machine qualification.")
    note(17.78,271.78,"TX_PERMIT must be a hardware-qualified 3.3V permission signal. /G is tied high; G has three 10k pulldowns.\nAbsent permission means HIGH-Z, not a guaranteed low at the remote receiver. Independent drive inhibit and receiver bias are required.")
    note(81.28,299.72,"JLOGIC1 is an internal circuit boundary,\nnot an assigned FPGA package or connector.\n3.3V logic; no 5V pull-ups on FPGA nets.\nDo not drive inputs while drivers are unpowered.\nSIGNAL_5V is externally supplied at 4.5–5.5V.\nNo current, thermal or partial-power proof.")
    note(198.12,322.58,"JREF1.1/2/3 map to ledger JPOWER.5/6/7:\nTX0/1/2_REFERENCE, each bonded to LOGIC_GND.\nJREF1 is only a review boundary, not a new final connector.\nLine pairs are not galvanically isolated; qualify common mode.")
    note(391.16,299.72,"TI SLLS103P: Fig 4-1, Table 7-1, Sections 5.3/8.3.\n33R damping and 10k defaults remain provisional.\nThree permission pulldowns load the source in parallel.\nAll capacitor/resistor MPNs and connector footprints TBD.\nNo fabrication files or manufacturing release.\nOriginal two-joint tx_bank evidence is retained separately.")
    schematic = f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A2")\n' \
                '(title_block (title "Baseline six-joint differential transmitter") (date "2026-09-28") (rev "r0.2") (comment 1 "Partial schematic only; not released for manufacture"))\n' \
                f'(lib_symbols {"".join(library)})\n'+"\n".join(items)+"\n)\n"
    (OUT / "tx_six.kicad_sch").write_text(schematic,encoding="utf-8")
    libtext = "\n".join(value.replace('(symbol "CNC:', '(symbol "',1) for value in library)
    (OUT / "CNC.kicad_sym").write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding="utf-8")
    (OUT / "sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Project-local reviewed transmitter symbols")))\n',encoding="utf-8")
    (OUT / "tx_six.kicad_pro").write_text('{"meta":{"filename":"tx_six.kicad_pro","version":1}}\n',encoding="utf-8")
    (OUT / "channel-map.json").write_text(json.dumps({"schema_version":1,"scope":"baseline-6j-transmitter-only",
        "manufacturing_ready":False,"channels":mapping,"logic_boundary":dict(enumerate(logic_nets,1)),
        "references":[{"boundary":f"JREF1.{bank+1}","ledger_terminal":f"JPOWER.{bank+5}",
                       "ledger_name":f"TX{bank}_REFERENCE","net":"LOGIC_GND"} for bank in range(3)]},indent=2)+"\n",encoding="utf-8")
    print(OUT / "tx_six.kicad_sch")


if __name__ == "__main__":
    main()
