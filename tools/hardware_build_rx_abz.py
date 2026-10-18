"""Editable baseline six-channel/two-ABZ receiver block, not a released board."""
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/rx_abz"
NS = uuid.UUID("ae9c4e3e-c0db-47d2-9ac2-1ad57f80f5e2")


def uid(name):
    return str(uuid.uuid5(NS,name))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    design = json.loads((ROOT / "hardware/electrical-design.json").read_text(encoding="utf-8"))
    channels = [channel for channel in design["channels"] if channel["kind"] == "encoder"]
    if [channel["id"] for channel in channels] != [f"ENC{enc}_{sig}" for enc in range(2) for sig in "ABZ"]:
        raise ValueError("Receiver block requires the separate baseline two-ABZ allocation")
    root_id = uid("two-abz-root")
    pins = [
        (1,"1B",-12.7,20.32,0,"input"),(2,"1A",-12.7,25.4,0,"input"),(3,"1Y",12.7,25.4,180,"tri_state"),
        (4,"G",-12.7,40.64,0,"input"),(5,"2Y",12.7,10.16,180,"tri_state"),
        (6,"2A",-12.7,10.16,0,"input"),(7,"2B",-12.7,5.08,0,"input"),(8,"GND",0,-45.72,90,"power_in"),
        (9,"3B",-12.7,-10.16,0,"input"),(10,"3A",-12.7,-5.08,0,"input"),(11,"3Y",12.7,-5.08,180,"tri_state"),
        (12,"~{G}",-12.7,35.56,0,"input"),(13,"4Y",12.7,-20.32,180,"tri_state"),
        (14,"4A",-12.7,-20.32,0,"input"),(15,"4B",-12.7,-25.4,0,"input"),(16,"VCC",0,50.8,270,"power_in")]
    rectangle = '(rectangle (start -10.16 48.26) (end 10.16 -43.18) (stroke (width 0.254) (type default)) (fill (type background)))'
    passive = [(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    resistor = '(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
    capacitor = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
                '(polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
                '(polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))' \
                '(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    library = [symbol("AM26LV32EIPWR",pins,rectangle),symbol("R",passive,resistor,"R"),symbol("C",passive,capacitor,"C")]
    connectors = {}
    for count in (4,8):
        cpins = [(index,str(index),-5.08,-(index-1)*2.54,0,"passive") for index in range(1,count+1)]
        body = f'(rectangle (start -2.54 2.54) (end 2.54 {-count*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        library.append(symbol(f"Conn{count}",cpins,body,"J"))
        connectors[count] = cpins
    library.append(symbol("PWR_FLAG",[(1,"pwr",0,0,90,"power_out")],"","#FLG"))
    items,pins_by_ref = [],{}

    def place(name,ref,value,x,y,pinlist,footprint="",mpn=""):
        pins_by_ref[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pinlist}
        props = f'(property "Reference" {quote(ref)} (at {x+4} {y-5} 0) {effects()})' \
                f'(property "Value" {quote(value)} (at {x+4} {y-2.5} 0) {effects()})' \
                f'(property "Footprint" {quote(footprint)} (at {x} {y} 0) {effects(extra="hide")})' \
                f'(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) '
                     f'(in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) '
                     f'(dnp no) (uuid "{uid(ref)}") {props}'
                     f'(instances (project "rx_abz" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')

    def label(ref,pin,net,dx=0,dy=0):
        x,y = pins_by_ref[ref][str(pin)]
        ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')

    def note(x,y,value,size=1.25):
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value)}"))')

    groups = ((2,1,3),(6,7,5),(10,9,11),(14,15,13))
    mapping = []
    for bank in range(2):
        ref = f"U{bank+1}"
        x,y = 170.18+bank*198.12,175.26
        place("AM26LV32EIPWR",ref,"AM26LV32EIPWR",x,y,pins,"Package_SO:TSSOP-16_4.4x5mm_P0.65mm","AM26LV32EIPWR")
        netmap = {4:"IO_3V3",12:"IO_3V3",16:"IO_3V3",8:"LOGIC_GND"}
        for local,(positive,negative,output) in enumerate(groups):
            channel = next((c for c in channels if (c["component"],c["device_channel"]) == (f"RX{bank}",local+1)),None)
            if channel:
                netmap.update({positive:channel["id"]+"_P",negative:channel["id"]+"_N",output:channel["logic_net"]})
                mapping.append({"channel":channel["id"],"ledger_component":channel["component"],"receiver":ref,
                                "device_channel":local+1,"positive_pin":positive,"negative_pin":negative,
                                "output_pin":output,"logic_net":channel["logic_net"]})
            else:
                netmap.update({positive:"IO_3V3",negative:"LOGIC_GND"})
                px,py = pins_by_ref[ref][str(output)]
                items.append(f'(no_connect (at {px} {py}) (uuid "{uid(ref+str(output)+"nc")}"))')
        for pin,net in netmap.items():
            label(ref,pin,net,0 if pin in (8,16) else 7.62 if pin in (3,5,11,13) else -22.86,
                  -5.08 if pin == 16 else 5.08 if pin == 8 else 0)
        for local,(value,cx) in enumerate((("100nF 25V X7R",x-40.64),("1uF 25V X7R",x+5.08))):
            cap = f"C{bank*2+local+1}"
            place("C",cap,value,cx,83.82,passive,"Capacitor_SMD:C_0603_1608Metric")
            label(cap,1,"IO_3V3",dy=-5.08)
            label(cap,2,"LOGIC_GND",dy=5.08)
        note(x-71.12,45.72,f"U{bank+1} = LEDGER RX{bank}",1.8)
        note(x-71.12,55.88,"AM26LV32EIPWR / PW16 / 3.0–3.6V supply\nG=/G=3.3V: always enabled; receiver state does not grant motion.")
    for encoder in range(2):
        connector = f"JENC{encoder}"
        y = 66.04+encoder*121.92
        place("Conn8",connector,"ENCODER / MPN TBD",68.58,y,connectors[8])
        for term in (t for t in design["terminals"] if t["connector"] == connector):
            label(connector,term["position"],term["net"],dx=-30.48)
    for index,channel in enumerate(channels):
        row,column = divmod(index,3)
        x,y = 256.54+column*81.28,264.16+row*50.8
        resistor_ref = f"R{index+1}"
        place("R",resistor_ref,"120R 1% 0.5W / FIT",x,y,passive,"Resistor_SMD:R_1210_3225Metric","CRCW1210120RFKEA")
        label(resistor_ref,1,channel["id"]+"_P",dy=-5.08)
        label(resistor_ref,2,channel["id"]+"_N",dy=5.08)
        mapping[index]["termination"] = resistor_ref
    logic_nets = ["IO_3V3","LOGIC_GND"]+[c["logic_net"] for c in channels]
    place("Conn8","JLOGIC1","3V3 LOGIC BOUNDARY",66.04,284.48,connectors[8])
    for position,net in enumerate(logic_nets,1):
        label("JLOGIC1",position,net,dx=-33.02)
    place("Conn4","JPWR1","PROTECTED SUPPLY BOUNDARY",172.72,284.48,connectors[4])
    for position,net in enumerate(("ENC0_5V_LIMITED","LOGIC_GND","ENC1_5V_LIMITED","LOGIC_GND"),1):
        label("JPWR1",position,net,dx=-38.1)
    for index,(net,x) in enumerate((("IO_3V3",124.46),("LOGIC_GND",177.8)),1):
        ref = f"#FLG0{index}"
        place("PWR_FLAG",ref,"EXTERNAL SUPPLY",x,345.44,[(1,"pwr",0,0,90,"power_out")])
        label(ref,1,net,dy=5.08)
    note(17.78,15.24,"BASELINE TWO-ABZ DIFFERENTIAL RECEIVER - SCHEMATIC BLOCK r0.1",2.1)
    note(17.78,27.94,"Six receiver channels, exact ledger allocation; no encoder supply limiter, line protection, FPGA pin assignment or board release.")
    note(447.04,157.48,"Unused U2 channels 3/4:\nA tied IO_3V3; B tied LOGIC_GND.\nOutputs 11/13 deliberately NC.\nNo floating or shorted unused inputs.")
    note(17.78,246.38,"JENC pin1/2=A+/−; 3/4=B+/−; 5/6=Z+/−; 7=protected5V; 8=logic ground.\nSupply limiters are absent: JPWR1 passes separately supplied, already protected rails.\nJLOGIC1/JPWR1 are circuit boundaries only; connector MPNs remain unselected.")
    note(236.22,236.22,"TERMINATION: fitted 120R per pair; DNP = open. Never substitute a short.\nLocation is receiver end only; encoder/cable profile must qualify the load.")
    note(17.78,368.3,"TI SLLS849E: Fig5-1 / Table8-1 / Section10. Place C1/C3 close to U1/U2 pins16/8.\nOpen-circuit fail-safe does NOT guarantee a valid state for a shorted or terminated disconnected cable.\nNo galvanic isolation, independent cable-loss detection or measured encoder timing here.")
    note(236.22,342.9,"Termination reference: CRCW1210120RFKEA (1210,0.5W at70C).\nDeclared applied differential bound:5.5V; worst allowance ~0.259W/channel.\nInitial localambient<=70C; PCB/film temperature and load still require measurement.\nReceiver +/-7V common mode does not rate termination for14V differential.\nESD component ratings do not qualify the complete controller.")
    schematic = f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A2")\n' \
                '(title_block (title "Baseline two-ABZ differential receiver") (date "2026-09-28") (rev "r0.1") (comment 1 "Partial schematic; no physical qualification or manufacturing release"))\n' \
                f'(lib_symbols {"".join(library)})\n'+"\n".join(items)+"\n)\n"
    (OUT / "rx_abz.kicad_sch").write_text(schematic,encoding="utf-8")
    libtext = "\n".join(value.replace('(symbol "CNC:', '(symbol "',1) for value in library)
    (OUT / "CNC.kicad_sym").write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding="utf-8")
    (OUT / "sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Reviewed receiver block symbols")))\n',encoding="utf-8")
    (OUT / "rx_abz.kicad_pro").write_text('{"meta":{"filename":"rx_abz.kicad_pro","version":1}}\n',encoding="utf-8")
    minimum_resistance = 120*(1-0.01)*(1-100e-6*150)
    (OUT / "channel-map.json").write_text(json.dumps({"schema_version":1,"scope":"baseline-2abz-receiver-only",
        "manufacturing_ready":False,"channels":mapping,"logic_boundary":dict(enumerate(logic_nets,1)),
        "termination":{"state":"fitted_120R","alternate":"DNP_open_only_not_a_bypass","mpn_reference":"CRCW1210120RFKEA",
            "ohms":120,"tolerance":0.01,"tcr_ppm_per_k":100,"conservative_temperature_excursion_k":150,
            "minimum_ohms_with_tolerance_and_tcr":minimum_resistance,"maximum_applied_differential_v":5.5,
            "calculated_worst_case_w_per_channel":5.5**2/minimum_resistance,
            "calculated_worst_case_w_all_six":6*5.5**2/minimum_resistance,
            "nominal_rating_w_at_70c":0.5,"initial_local_ambient_max_c":70,
            "physical_thermal_qualified":False},
        "unused_channels":[{"receiver":"U2","device_channel":i,"positive_net":"IO_3V3","negative_net":"LOGIC_GND",
                            "output":"explicit_no_connect"} for i in (3,4)]},indent=2)+"\n",encoding="utf-8")
    print(OUT / "rx_abz.kicad_sch")


if __name__ == "__main__":
    main()
