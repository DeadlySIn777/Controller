"""Generate the twelve-channel STEP/DIR candidate; preserve historical six-channel evidence."""
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "tx_twelve"
NS = uuid.UUID("81111b4d-f73a-4ae5-b91b-80571adff4e2")


def uid(name):
    return str(uuid.uuid5(NS, name))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # This new allocation does not modify or inherit the six-joint ledger.
    channels = [{"id":f"{kind}{joint}","kind":"step_dir", "component":f"TX{joint//2}",
                 "device_channel":(joint%2)*2+offset+1,"logic_net":f"{kind}{joint}_FPGA","domain":"LOGIC"}
                for joint in range(12) for offset,kind in enumerate(("STEP","DIR"))]
    terms = [{"connector":f"JTX{index//4}","position":(index%4)*2+offset+1,
              "net":channel["id"]+"_"+polarity,"domain":"LOGIC"}
             for index,channel in enumerate(channels) for offset,polarity in enumerate(("P","N"))]
    design = {"schema_version":1,"scope":"twelve-channel-transmitter-candidate", "manufacturing_ready":False,
              "motor_channels":12,"minimum_product_channels":8,"channels":channels,"terminals":terms,
              "population":"All six banks fitted for this circuit. Eight-channel variant needs its own BOM/export.",
              "supply_reservation_a":1.2,"reservation_is_measured":False,
              "firmware_boundary":"Existing CNC1 endpoint remains six-channel; this drawing does not expand firmware.",
              "enable_alarm_boundary":"Drive enables and alarms are separate incomplete circuits."}
    (OUT/'allocation.json').write_text(json.dumps(design,indent=2)+'\n')
    root_id = uid("twelve-channel-transmitter")
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
    for count in (6,8,28):
        pins = [(i,str(i),-5.08,-(i-1)*2.54,0,"passive") for i in range(1,count+1)]
        body = f'(rectangle (start -2.54 2.54) (end 2.54 {-count*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        library.append(symbol(f"Conn{count}",pins,body,"J"))
        connectors[count] = pins
    library.append(symbol("PWR_FLAG",[(1,"pwr",0,0,90,"power_out")],"","#FLG"))
    items, pins_by_ref = [], {}
    base_y = 0

    def place(name, ref, value, x, y, pins, footprint="", mpn=""):
        y += base_y
        pins_by_ref[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        props = f'(property "Reference" {quote(ref)} (at {x+4} {y-5} 0) {effects()})' \
                f'(property "Value" {quote(value)} (at {x+4} {y-2.5} 0) {effects()})' \
                f'(property "Footprint" {quote(footprint)} (at {x} {y} 0) {effects(extra="hide")})' \
                f'(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) '
                     f'(in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) '
                     f'(dnp no) (uuid "{uid(ref)}") {props}'
                     f'(instances (project "tx_twelve" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')

    def label(ref, pin, net, dx=0, dy=0):
        x,y = pins_by_ref[ref][str(pin)]
        ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')

    def note(x,y,value,size=1.25):
        y += base_y
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value)}"))')

    mapping = []
    # Real PW16 pin groups: A, noninverting Y, inverting Z.
    pin_groups = ((1,2,3),(7,6,5),(9,10,11),(15,14,13))
    for bank in range(6):
        offset = (bank % 3) * 228.6
        base_y = (bank // 3) * 240.03
        dx,dy = offset + 116.84,160.02
        driver = f"U{bank+1}"
        place("AM26C31IPWR",driver,"AM26C31IPWR",dx,dy,driver_pins,
              "Package_SO:TSSOP-16_4.4x5mm_P0.65mm","AM26C31IPWR")
        driver_nets = {4:"TX_PERMIT",8:"LOGIC_GND",12:"CORE_5V",16:"CORE_5V"}
        bank_channels = sorted((c for c in channels if c["component"] == f"TX{bank}"), key=lambda c:c["device_channel"])
        if [c["device_channel"] for c in bank_channels] != [1,2,3,4]:
            raise ValueError("Each candidate transmitter must use channels 1–4 exactly once")
        for local, channel in enumerate(bank_channels):
            index = bank*4+local
            net = channel["id"]
            a,y,z = pin_groups[local]
            driver_nets.update({a:net+"_D", y:net+"_P", z:net+"_N"})
            x = offset+22.86+local*27.94
            series, pull = f"R{index+1}", f"R{index+25}"
            place("R",series,"33R 1%",x,66.04,two_pins,"Resistor_SMD:R_0603_1608Metric")
            label(series,1,channel["logic_net"],dy=-5.08)
            label(series,2,net+"_D",dy=5.08)
            place("R",pull,"10k 1%",x,96.52,two_pins,"Resistor_SMD:R_0603_1608Metric")
            label(pull,1,net+"_D",dy=-5.08)
            label(pull,2,"LOGIC_GND",dy=5.08)
            mapping.append({"channel":net,"allocation_component":channel["component"],"driver":driver,
                            "device_channel":local+1,"input_pin":a,"positive_pin":y,"negative_pin":z,
                            "series_resistor":series,"input_pulldown":pull,"logic_net":channel["logic_net"],
                            "terminal_positive":f"JTX{bank}.{local*2+1}","terminal_negative":f"JTX{bank}.{local*2+2}"})
        for pin,net in driver_nets.items():
            px = pins_by_ref[driver][str(pin)][0]
            label(driver,pin,net,0 if pin in (8,16) else -15.24 if px<dx else 7.62,
                  -5.08 if pin == 16 else 5.08 if pin == 8 else 0)
        permit = f"R{49+bank}"
        place("R",permit,"10k 1%",offset+48.26,167.64,two_pins,"Resistor_SMD:R_0603_1608Metric")
        label(permit,1,"TX_PERMIT",dy=-5.08)
        label(permit,2,"LOGIC_GND",dy=5.08)
        for local,(value,x) in enumerate((("100nF 25V X7R",offset+142.24),("1uF 25V X7R",offset+165.1))):
            ref = f"C{bank*2+local+1}"
            place("C",ref,value,x,66.04,two_pins,"Capacitor_SMD:C_0603_1608Metric")
            label(ref,1,"CORE_5V",dy=-5.08)
            label(ref,2,"LOGIC_GND",dy=5.08)
        connector = f"JTX{bank}"
        place("Conn8",connector,"FIELD TERMINALS / MPN TBD",offset+142.24,231.14,connectors[8])
        terms = sorted((t for t in design["terminals"] if t["connector"] == connector),key=lambda t:t["position"])
        if [t["position"] for t in terms] != list(range(1,9)):
            raise ValueError("Transmitter terminal allocation must contain positions 1–8")
        for term in terms:
            label(connector,term["position"],term["net"],dx=-20.32)
        note(offset+17.78,38.1,f"BANK TX{bank} / {driver}: JOINTS {bank*2} AND {bank*2+1}",1.8)
        note(offset+17.78,218.44,f"Place C{bank*2+1} close to {driver} pins 16/8.\nJTX{bank} matches allocation positions 1–8; reference is separate.")

    base_y = 0
    logic_nets = ["CORE_5V","LOGIC_GND","TX_PERMIT"]+[c["logic_net"] for c in channels]+["LOGIC_GND"]
    place("Conn28","JLOGIC1","INTERNAL LOGIC BOUNDARY",756.92,88.9,connectors[28])
    for pin,net in enumerate(logic_nets,1):
        label("JLOGIC1",pin,net,dx=-30.48)
    place("Conn6","JREF1","SIGNAL RETURNS",756.92,223.52,connectors[6])
    for pin in range(1,7): label("JREF1",pin,"LOGIC_GND",dx=-20.32)
    for index,net in enumerate(("CORE_5V","LOGIC_GND"),1):
        ref = f"#FLG0{index}"
        place("PWR_FLAG",ref,"SUPPLY",736.6+(index-1)*35.56,279.4,[(1,"pwr",0,0,90,"power_out")])
        label(ref,1,net,dy=5.08)
    note(17.78,15.24,"TWELVE-MOTOR STEP/DIR TRANSMITTER CANDIDATE",2.1)
    note(17.78,25.4,"24 differential signals / 6 AM26C31IPWR banks. New electrical scope; current firmware remains six-channel.")
    note(700,38.1,"Engineering circuit only.\nAll twelve channels populated.\n8-channel population needs\nseparate BOM and export.\nNo price or speed approval.")
    note(700,322.58,"JLOGIC1 is an internal boundary.\n3.3V logic; no 5V GPIO pullups.\nNo inputs driven with VCC off.\nSix enable pulldowns in parallel.\nTX_PERMIT requires >=2V high.\nNo line protection or PCB yet.\nNo automatic receiver fail state.\nDrive enables/alarms separate.")
    note(17.78,535.94,"TX_PERMIT low makes differential outputs HIGH-Z. A remote drive may interpret floating lines incorrectly; receiver bias and independent drive inhibit need qualification.\n1.2A reservation on CORE_5V is a conservative design allowance, not a measured load. Existing six-channel converter budget cannot be reused without recalculation.\nTwelve motor channels are not twelve Cartesian axes. No gateware expansion, cable qualification, thermal proof or manufacturing release follows from this drawing.")
    note(17.78,564,"Source: TI AM26C31 SLLS103P, pin Table4-1, operating Section5.3, electrical Section5.5, function Table7-1.\nInput33R damping,10k defaults, capacitor MPNs, connector selections and final protection remain open.",1.1)
    schematic = f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A1")\n' \
                '(title_block (title "Twelve-channel differential transmitter candidate") (date "2026-09-28") (rev "r0.2") (comment 1 "Partial schematic only; not released for manufacture"))\n' \
                f'(lib_symbols {"".join(library)})\n'+"\n".join(items)+"\n)\n"
    (OUT / "tx_twelve.kicad_sch").write_text(schematic,encoding="utf-8")
    libtext = "\n".join(value.replace('(symbol "CNC:', '(symbol "',1) for value in library)
    (OUT / "CNC.kicad_sym").write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding="utf-8")
    (OUT / "sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Project-local reviewed transmitter symbols")))\n',encoding="utf-8")
    (OUT / "tx_twelve.kicad_pro").write_text('{"meta":{"filename":"tx_twelve.kicad_pro","version":1}}\n',encoding="utf-8")
    (OUT / "channel-map.json").write_text(json.dumps({"schema_version":1,"scope":"candidate-12motor-transmitter-only",
        "manufacturing_ready":False,"channels":mapping,"logic_boundary":dict(enumerate(logic_nets,1)),
        "references":[{"boundary":f"JREF1.{bank+1}","reference_name":f"TX{bank}_REFERENCE","net":"LOGIC_GND"} for bank in range(6)]},indent=2)+"\n",encoding="utf-8")
    print(OUT / "tx_twelve.kicad_sch")


if __name__ == "__main__":
    main()
