"""Build the standalone FIELD 5 V review circuit. No PCB or fabrication output."""
from pathlib import Path
import hashlib
import json
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/field_power"
NS = uuid.UUID("7ac9b8f9-a11e-4081-b136-aea554cc9d75")


def uid(key):
    return str(uuid.uuid5(NS, key))


def q(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def ef(size=1, extra=""):
    return f"(effects (font (size {size} {size})) {extra})"


def lib_symbol(name, pins, body, reference="U"):
    props = ''.join(f'(property {q(k)} {q(v)} (at 0 0 0) {ef(extra="hide")})'
                    for k, v in (("Reference", reference), ("Value", name)))
    ps = ''.join(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) '
                 f'(name {q(label)} {ef()}) (number {q(number)} {ef()}))'
                 for number, label, x, y, angle, kind in pins)
    return f'(symbol "FIELDPOWER:{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) {props}' \
           f'(symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {ps}))'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((OUT / "input-electrical-design.json").read_text(encoding="utf-8"))
    rail = next(r for r in frozen["rails"] if r["id"] == "FIELD_5V")
    if (rail["nominal_v"], rail["min_v"], rail["max_v"], rail["capacity_a"]) != (5, 4.85, 5.15, .1):
        raise ValueError("Frozen FIELD_5V envelope changed; review before generation")
    root_id = uid("root")
    # TI SNVSBB6C Figure 5-1 and Table 5-1. Pin 9 IS the ground pad, not pin 10.
    # BOOT is passive in ERC because it is a floating bootstrap network, not a DC rail.
    ic = [(1,"RT",-15.24,-12.7,0,"input"), (2,"PGOOD",15.24,-25.4,180,"open_collector"),
          (3,"EN/UVLO",-15.24,2.54,0,"input"), (4,"VIN",-15.24,22.86,0,"power_in"),
          (5,"SW",15.24,22.86,180,"power_out"), (6,"BOOT",15.24,7.62,180,"passive"),
          (7,"VCC",-15.24,-27.94,0,"power_out"), (8,"VOUT/BIAS",15.24,-10.16,180,"input"),
          (9,"GND",0,-43.18,90,"power_in")]
    passive = [(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    coil = [(1,"",-5.08,0,0,"passive"),(2,"",5.08,0,180,"passive")]
    conn = [(i,str(i),-5.08,-(i-1)*5.08,0,"passive") for i in range(1,5)]
    flag = [(1,"pwr",0,0,90,"power_out")]
    rect = '(rectangle (start -12.7 30.48) (end 12.7 -40.64) (stroke (width 0.254) (type default)) (fill (type background)))'
    cap = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    library = [lib_symbol("LMR36506R5RPER",ic,rect), lib_symbol("C",passive,cap,"C"),
               lib_symbol("R",passive,'(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))',"R"),
               lib_symbol("L",coil,'(rectangle (start -2.54 1.27) (end 2.54 -1.27) (stroke (width 0.254) (type default)) (fill (type none)))',"L"),
               lib_symbol("Conn4",conn,'(rectangle (start -2.54 2.54) (end 2.54 -17.78) (stroke (width 0.254) (type default)) (fill (type background)))',"J"),
               lib_symbol("PWR_FLAG",flag,"","#FLG")]
    items, positions, parts = [], {}, {}

    def place(name, ref, value, x, y, pins, mpn="", footprint="", **details):
        positions[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        rx, ry, vy = (x+4, y-2.54, y+1.27) if name in ("R","C") else (x,y-6.35,y-3.81)
        style = ef(1,"(justify left)") if name in ("R","C") else ef()
        if ref == "U1": rx, ry, vy = x,y-36.83,y-33.02
        props = f'(property "Reference" {q(ref)} (at {rx} {ry} 0) {style}) (property "Value" {q(value)} (at {rx} {vy} 0) {style})' \
                f'(property "Footprint" {q(footprint)} (at {x} {y} 0) {ef(extra="hide")}) (property "MPN" {q(mpn)} (at {x} {y} 0) {ef(extra="hide")})'
        items.append(f'(symbol (lib_id "FIELDPOWER:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{uid(ref)}") {props} (instances (project "field_power" (path "/{root_id}" (reference {q(ref)}) (unit 1)))))')
        if not ref.startswith("#"):
            parts[ref] = {"value":value,"mpn":mpn,"footprint":footprint,"pins":{},"status":"proposed_not_qualified",**details}

    def label(ref, pin, net, dx=0, dy=0):
        x,y = positions[ref][str(pin)]; ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {q(net)} (at {ex} {ey} 0) {ef(.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')
        if ref in parts: parts[ref]["pins"][str(pin)] = net

    def note(x,y,value,size=1.3):
        items.append(f'(text {q(value)} (at {x} {y} 0) {ef(size,"(justify left top)")} (uuid "{uid(value)}"))')

    place("LMR36506R5RPER","U1","LMR36506R5RPER / FIXED 5V",320.04,119.38,ic,
          "LMR36506R5RPER",package="RPE0009A VQFN-HR 2x2mm; ground pad 9",footprint_status="missing_verified_custom_land_pattern")
    unets={1:"FIELD_VCC",2:"FIELD_5V_PGOOD",3:"F_PGOOD",4:"FIELD_24V_PROTECTED",5:"FIELD_SW",6:"FIELD_BOOT",7:"FIELD_VCC",8:"FIELD_5V",9:"FIELD_GND"}
    for pin,net in unets.items():
        label("U1",pin,net,dx=-55.88 if pin in (1,3,4,7) else 7.62 if pin!=9 else 0,dy=7.62 if pin==9 else 0)
    place("L","L1","22uH / 20%",464.82,81.28,coil,"LPS6235-223MRC",package="6.0x6.0mm shielded inductor",inductance_h=22e-6,tolerance=.2,isat_10pct_25c_a=1.6,irms_20c_rise_a=1.1,dcr_25c_max_ohm=.15,footprint_status="missing_verified_custom_land_pattern")
    label("L1",1,"FIELD_SW",dx=-17.78);label("L1",2,"FIELD_5V",dx=7.62)
    cin_mpn="CGA5L3X7S2A225K160AB"
    for index in range(4):
        ref=f"C{index+1}"
        place("C",ref,"2.2uF 100V X7S",45.72+index*50.8,78.74,passive,cin_mpn,"Capacitor_SMD:C_1206_3216Metric",capacitance_f=2.2e-6,voltage_v=100,tolerance=.1,temp_change=.22)
        label(ref,1,"FIELD_24V_PROTECTED",dy=-5.08);label(ref,2,"FIELD_GND",dy=5.08)
    caps=[("C5",.1e-6,100,"100nF 100V X7R","GRM188R72A104KA35D","0603_1608",45.72,129.54,"FIELD_24V_PROTECTED","FIELD_GND"),
          ("C6",.1e-6,16,"100nF 16V X7R","GCM155R71C104KA55D","0402_1005",421.64,124.46,"FIELD_BOOT","FIELD_SW"),
          ("C7",1e-6,16,"1uF 16V X7R","885012206052","0603_1608",365.76,228.6,"FIELD_VCC","FIELD_GND"),
          ("C8",22e-6,10,"22uF 10V X7R","GCM31CR71A226KE02L","1206_3216",464.82,172.72,"FIELD_5V","FIELD_GND"),
          ("C9",22e-6,10,"22uF 10V X7R","GCM31CR71A226KE02L","1206_3216",518.16,172.72,"FIELD_5V","FIELD_GND"),
          ("C10",.1e-6,16,"100nF 16V X7R","GCM155R71C104KA55D","0402_1005",518.16,228.6,"FIELD_5V","FIELD_GND")]
    for ref,c,v,value,mpn,package,x,y,n1,n2 in caps:
        place("C",ref,value,x,y,passive,mpn,"Capacitor_SMD:C_"+package+"Metric",capacitance_f=c,voltage_v=v,tolerance=.1,temp_change=.15)
        label(ref,1,n1,dy=-5.08);label(ref,2,n2,dy=5.08)
    for ref,r,x,y,n1,n2 in [("R1",100000,106.68,180.34,"FIELD_24V_PROTECTED","F_PGOOD"),("R2",10000,175.26,180.34,"F_PGOOD","FIELD_GND"),
                           ("R3",10000,236.22,228.6,"FIELD_5V","FIELD_5V_PGOOD"),("R4",100000,452.12,228.6,"FIELD_5V","FIELD_GND")]:
        mpn="CRCW0603100KFKEA" if r==100000 else "CRCW060310K0FKEA"
        place("R",ref,("100k" if r==100000 else "10k")+" 1%",x,y,passive,mpn,"Resistor_SMD:R_0603_1608Metric",resistance_ohm=r,tolerance=.01,tcr_ppm_k=100,working_voltage_v=75,power_70c_w=.1)
        label(ref,1,n1,dy=-5.08);label(ref,2,n2,dy=5.08)
    place("Conn4","J1","ENTRY BOUNDARY / NOT CONNECTOR MPN",137.16,294.64,conn,role="boundary_not_orderable")
    place("Conn4","J2","LOAD BOUNDARY / NOT CONNECTOR MPN",373.38,294.64,conn,role="boundary_not_orderable")
    for ref,nets in [("J1",["FIELD_24V_PROTECTED","FIELD_GND","F_PGOOD","FIELD_GND"]),("J2",["FIELD_5V","FIELD_GND","FIELD_5V_PGOOD","FIELD_GND"])]:
        for i,net in enumerate(nets,1):label(ref,i,net,dx=-55.88)
    for i,(net,x) in enumerate([("FIELD_24V_PROTECTED",43.18),("FIELD_GND",200.66)],1):
        place("PWR_FLAG",f"#FLG0{i}","ENTRY SUPPLIED",x,340.36,flag);label(f"#FLG0{i}",1,net,dy=5.08)
    note(20.32,15.24,"FIELD 24V -> 5V / 100mA - STANDALONE REVIEW CIRCUIT r0.1",2)
    note(20.32,28,"All returns are FIELD_GND. This buck is NOT an isolation barrier. No LOGIC_GND connection.\n18-30V local-input study; entry chain currently proposes 19-30V. Negative input / retained-output backfeed NOT qualified.")
    note(20.32,49,"Input effective capacitance >=4.7uF is a qualification gate, not proved by nominal sum. C1-C5 close to VIN/GND.\nU1 RT tied to internal VCC selects 1MHz. VCC powers no external load; C6 connects BOOT to SW, never ground.")
    note(20.32,220,"STARTUP: R1/R2 bias F_PGOOD from protected input.\nEntry TPS26630 PGOOD sinks this node until ready.\nREMOVE entry R29; no parallel 5V pull-up or DNP path.\nJ1.3 is an analog power-enable node, not GPIO.")
    note(395,260,"PGOOD below valid VIN is UNKNOWN.\nFIELD_5V_PGOOD is diagnostic only.\nR4 is a weak bleed; no rapid discharge guarantee.")
    note(20.32,362,"Release blockers: input/output capacitor derating; fixed-5V PFM accuracy; custom U1/L1 footprints; entry integration; load/inrush; EMC; layout/thermal/bench tests.\nField output loads MUST remain held off through entry ramp and rail startup; driver/inhibit circuit still required. This supply grants no machine permission.\nBoundary connectors are schematic interfaces only. No PCB, DRC, Gerbers, assembly placement, isolation rating or physical qualification is claimed.",1.3)
    sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A2")\n(lib_symbols {"".join(library)})\n'+"\n".join(items)+"\n)\n"
    (OUT/"field_power.kicad_sch").write_text(sch,encoding="utf-8")
    (OUT/"FIELDPOWER.kicad_sym").write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+"\n".join(s.replace('(symbol "FIELDPOWER:', '(symbol "',1) for s in library)+')\n',encoding="utf-8")
    (OUT/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "FIELDPOWER")(type "KiCad")(uri "${KIPRJMOD}/FIELDPOWER.kicad_sym")(options "")(descr "Field converter review symbols")))\n',encoding="utf-8")
    (OUT/"field_power.kicad_pro").write_text('{"meta":{"filename":"field_power.kicad_pro","version":1}}\n',encoding="utf-8")
    model={"schema_version":1,"revision":"field-power-r0.1","status":"review_circuit_not_qualified","manufacturing_ready":False,
           "frozen_inputs":{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ("input-electrical-design.json","input-entry-requirements.json")},
           "ground_domain":"FIELD_GND","input_local_v":[18,30],"output_target_v":[4.85,5.15],"output_nominal_v":5,
           "external_capacity_target_a":.1,"baseline_reserved_load_a":.05,"switching_hz":[930000,1050000],
           "input_surge_screen_v":60,"surge_screen_is_qualification":False,"resistor_temperature_departure_k":100,
           "entry_pg_max_rdson_ohm":130,"entry_pg_leakage_abs_a":150e-9,"buck_en_leakage_assumed_abs_a":8e-9,
           "buck_en_leakage_limitation":"8nA is specified at 3.3V only; applying across divider operating range requires validation",
           "en_rising_max_v":1.36,"en_falling_min_screen_v":.76,"entry_ramp_max_v_s":608.947368421,
           "input_effective_capacitance_floor_f":4.7e-6,"output_effective_capacitance_floor_f":22e-6,
           "effective_capacitance_verified":False,"high_side_fault_current_reference_a":1.11,
           "full_output_accuracy_verified":False,"physical_qualification":False,
           "integration":{"entry_pullup_to_remove":"hardware/power_entry R29; remove physically, not parallel/DNP","entry_pg_net":"F_PGOOD","entry_pg_pin":16,"entry_pg_unpowered":"unknown; retained protected input may allow restart","field_5v_pgood":"diagnostic only, no isolated host input in this sheet","field_load_holdoff":"4.3A output loads must remain disabled during ramp; actual driver/inhibit circuit is outside this block","negative_input":"not allowed below -0.3V; upstream clamp qualification unresolved","retained_output":"no qualified output reverse-current barrier; do not externally power FIELD_5V","entry_18v_requirement":"unresolved system startup at 18V; do not call 19-30V entry draft equivalent"},
           "components":parts}
    (OUT/"design.json").write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
    print(OUT/"field_power.kicad_sch")


if __name__ == "__main__":
    main()
