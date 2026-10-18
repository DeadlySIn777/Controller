"""Generate an editable, self-contained KiCad review circuit; not PCB fabrication data."""
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "tx_bank"
NS = uuid.UUID("d252ff62-d246-4b08-bc87-c8b51f35d357")


def uid(name):
    return str(uuid.uuid5(NS, name))


def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def effects(size=1.0, extra=""):
    return f"(effects (font (size {size} {size})) {extra})"


def symbol(name, pins, body, reference="U"):
    props = "".join(f'(property {quote(k)} {quote(v)} (at 0 0 0) {effects(extra="hide")})'
                    for k, v in [("Reference", reference), ("Value", name)])
    ps = "".join(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) '
                 f'(name {quote(label)} {effects()}) (number {quote(number)} {effects()}))'
                 for number, label, x, y, angle, kind in pins)
    return f'(symbol "CNC:{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) {props}' \
           f'(symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {ps}))'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    root_id = uid("tx-bank-root")
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
    for n in (8,10):
        pins = [(i,str(i),-5.08, -(i-1)*2.54,0,"passive") for i in range(1,n+1)]
        body = f'(rectangle (start -2.54 2.54) (end 2.54 {-n*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        library.append(symbol(f"Conn{n}",pins,body,"J")); connectors[n] = pins
    library.append(symbol("PWR_FLAG",[(1,"pwr",0,0,90,"power_out")],"","#FLG"))
    items = []
    pins_by_ref = {}

    def place(name,ref,value,x,y,pins,footprint="",mpn=""):
        sid=uid(ref); pins_by_ref[ref]={str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        props=f'(property "Reference" {quote(ref)} (at {x+4} {y-5} 0) {effects()})' \
              f'(property "Value" {quote(value)} (at {x+4} {y-2.5} 0) {effects()})' \
              f'(property "Footprint" {quote(footprint)} (at {x} {y} 0) {effects(extra="hide")})' \
              f'(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{sid}") {props}'
                     f'(instances (project "tx_bank" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')

    def wire_label(ref,pin,net,dx=0,dy=0):
        x,y=pins_by_ref[ref][str(pin)]; ex=round(x+dx,4);ey=round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')

    def note(x,y,text,size=1.25):
        items.append(f'(text {quote(text)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(text)}"))')

    place("AM26C31IPWR","U1","AM26C31IPWR",160.02,109.22,driver_pins,
          "Package_SO:TSSOP-16_4.4x5mm_P0.65mm","AM26C31IPWR")
    driver_nets={1:"STEP0_D",2:"STEP0_P",3:"STEP0_N",4:"TX_PERMIT",5:"DIR0_N",6:"DIR0_P",7:"DIR0_D",8:"LOGIC_GND",9:"STEP1_D",10:"STEP1_P",11:"STEP1_N",12:"SIGNAL_5V",13:"DIR1_N",14:"DIR1_P",15:"DIR1_D",16:"SIGNAL_5V"}
    for pin,net in driver_nets.items():
        px=pins_by_ref["U1"][str(pin)][0]
        wire_label("U1",pin,net,-15.24 if px<160 else 7.62 if px>160 else 0,-5.08 if pin==16 else 5.08 if pin==8 else 0)
    for i,net in enumerate(("STEP0","DIR0","STEP1","DIR1")):
        x=35.56+i*27.94
        place("R",f"R{i+1}","33R 1%",x,73.66,two_pins,"Resistor_SMD:R_0603_1608Metric")
        wire_label(f"R{i+1}",1,net+"_FPGA",dy=-5.08)
        wire_label(f"R{i+1}",2,net+"_D",dy=5.08)
        place("R",f"R{i+5}","10k 1%",x,104.14,two_pins,"Resistor_SMD:R_0603_1608Metric")
        wire_label(f"R{i+5}",1,net+"_D",dy=-5.08)
        wire_label(f"R{i+5}",2,"LOGIC_GND",dy=5.08)
    place("R","R9","10k 1%",73.66,144.78,two_pins,"Resistor_SMD:R_0603_1608Metric")
    wire_label("R9",1,"TX_PERMIT",dy=-5.08); wire_label("R9",2,"LOGIC_GND",dy=5.08)
    for ref,value,x in [("C1","100nF 25V X7R",205.74),("C2","1uF 25V X7R",243.84)]:
        place("C",ref,value,x,76.2,two_pins,"Capacitor_SMD:C_0603_1608Metric")
        wire_label(ref,1,"SIGNAL_5V",dy=-5.08);wire_label(ref,2,"LOGIC_GND",dy=5.08)
    place("Conn8","J1","LOGIC BOUNDARY / MPN TBD",40.64,190.5,connectors[8])
    for i,net in enumerate(["SIGNAL_5V","LOGIC_GND","TX_PERMIT","STEP0_FPGA","DIR0_FPGA","STEP1_FPGA","DIR1_FPGA","LOGIC_GND"],1):
        wire_label("J1",i,net,dx=-15.24)
    place("Conn10","J2","DIFFERENTIAL BOUNDARY / MPN TBD",172.72,190.5,connectors[10])
    for i,net in enumerate(["STEP0_P","STEP0_N","DIR0_P","DIR0_N","STEP1_P","STEP1_N","DIR1_P","DIR1_N","LOGIC_GND","LOGIC_GND"],1):
        wire_label("J2",i,net,dx=-15.24)
    for i,(net,x) in enumerate([("SIGNAL_5V",220.98),("LOGIC_GND",259.08)]):
        place("PWR_FLAG",f"#FLG0{i+1}","EXT SUPPLY",x,109.22,[(1,"pwr",0,0,90,"power_out")])
        wire_label(f"#FLG0{i+1}",1,net,dy=5.08)
    note(20.32,15.24,"TWO-JOINT DIFFERENTIAL TX BANK - REVIEW CIRCUIT r0.1",2)
    note(20.32,25.4,"Repeat 3x for six joints. No PCB, external protection or system inhibit circuit is released.\nU1 pin map checked against TI SLLS103P Figure4-1 (PW16). Supply4.5-5.5V; logic VIH>=2V/VIL<=0.8V.")
    note(20.32,40.64,"3.3V source required; no 5V pull-up on FPGA-connected nets. Inputs must not drive an unpowered U1.\nR1-R4 are initial source-damping provisions; R5-R9 force low with upstream high-Z. Re-evaluate SI in layout.")
    note(195.58,127,"Place C1 at U1 pins16/8.\nExternal SIGNAL_5V and GND\nare declared powered at J1.\nNo isolation in this circuit.")
    note(20.32,165.1,"G=0 and /G=1 -> differential outputs HIGH-Z. TX_PERMIT must come from qualified hardware permission.\nHIGH-Z is not guaranteed STEP-low at the remote drive: qualified receiver bias and drive inhibit are mandatory.")
    note(203.2,190.5,"J1/J2 are circuit boundaries,\nnot approved connector MPNs.\nMissing line protection,\nremote bias, power sequencing\nand cable qualification block release.")
    sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A3")\n(lib_symbols {"".join(library)})\n' + "\n".join(items)+"\n)\n"
    (OUT/"tx_bank.kicad_sch").write_text(sch,encoding="utf-8")
    # The embedded definitions are authoritative; library copy supports editing and ERC resolution.
    libtext="\n".join(x.replace('(symbol "CNC:', '(symbol "',1) for x in library)
    (OUT/"CNC.kicad_sym").write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding="utf-8")
    (OUT/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Reviewed project-local symbols")))\n',encoding="utf-8")
    (OUT/"tx_bank.kicad_pro").write_text('{"meta":{"filename":"tx_bank.kicad_pro","version":1}}\n',encoding="utf-8")
    print(OUT / "tx_bank.kicad_sch")


if __name__ == "__main__":
    main()
