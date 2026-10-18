"""Generate all 22 baseline isolated inputs as an editable KiCad review sheet."""
from pathlib import Path
import hashlib
import json
import uuid

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"hardware/digital_inputs"
NS=uuid.UUID("86d2737f-dd12-4428-95b0-38daecf1f8cf")


def uid(s):return str(uuid.uuid5(NS,s))


def q(v):return '"'+str(v).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'


def ef(size=1,extra=""):return f'(effects (font (size {size} {size})) {extra})'


def symbol(name,pins,body,ref="U"):
    props=''.join(f'(property {q(k)} {q(v)} (at 0 0 0) {ef(extra="hide")})' for k,v in (("Reference",ref),("Value",name)))
    p=''.join(f'(pin {t} line (at {x} {y} {a}) (length 2.54) (name {q(n)} {ef()}) (number {q(i)} {ef()}))' for i,n,x,y,a,t in pins)
    return f'(symbol "DIGITALINPUTS:{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) {props} (symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {p}))'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    frozen=OUT/"input-electrical-design.json"
    ledger=json.loads(frozen.read_text(encoding="utf-8"))
    channels=[c for c in ledger["channels"] if c["kind"]=="digital_input"]
    terminals=[t for t in ledger["terminals"] if t["connector"].startswith("JDI")]
    if [c["id"] for c in channels]!=[f"DI{i:02}" for i in range(22)]:raise ValueError("Baseline 22-channel identity changed")
    root=uid("root")
    # TI SLLSEY7G Fig 4-2: independent floating SUB islands; pins 6/7 are NC.
    ic=[(16,"SENSE1",-20.32,33.02,0,"input"),(15,"IN1",-20.32,22.86,0,"input"),(14,"FGND1",-20.32,12.7,0,"passive"),(13,"SUB1",-20.32,2.54,0,"passive"),
        (11,"SENSE2",-20.32,-12.7,0,"input"),(10,"IN2",-20.32,-22.86,0,"input"),(9,"FGND2",-20.32,-33.02,0,"passive")]
    ic += [(12,"SUB2",-20.32,-43.18,0,"passive"),(2,"VCC1",20.32,33.02,180,"power_in"),(3,"EN",20.32,22.86,180,"input"),
           (4,"OUT1",20.32,12.7,180,"output"),(5,"OUT2",20.32,-12.7,180,"output"),(1,"GND1",20.32,-22.86,180,"power_in"),(8,"GND1",20.32,-33.02,180,"power_in"),
           (6,"NC",20.32,-43.18,180,"no_connect"),(7,"NC",20.32,-53.34,180,"no_connect")]
    two=[(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    cap='(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    body='(rectangle (start -17.78 38.1) (end 17.78 -58.42) (stroke (width 0.254) (type default)) (fill (type background))) (polyline (pts (xy 0 38.1) (xy 0 -58.42)) (stroke (width 0.3) (type dash)) (fill (type none)))'
    library=[symbol("ISO1212DBQR",ic,body),symbol("R",two,'(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))',"R"),symbol("C",two,cap,"C")]
    conns={}
    for n in (8,12,14):
        pins=[(i,str(i),-5.08,-(i-1)*5.08,0,"passive") for i in range(1,n+1)];conns[n]=pins
        library.append(symbol(f"Conn{n}",pins,f'(rectangle (start -2.54 2.54) (end 2.54 {-n*5.08+2.54}) (stroke (width 0.254) (type default)) (fill (type background)))',"J"))
    flags=[(1,"pwr",0,0,90,"power_out")];library.append(symbol("PWR_FLAG",flags,"","#FLG"))
    items=[];pos={};parts={};mapping=[]

    def place(name,ref,value,x,y,pins,mpn="",fp="",**extra):
        pos[ref]={str(i):(round(x+px,4),round(y-py,4)) for i,_,px,py,_,_ in pins}
        rx,ry,vy,sty=(x+3.81,y-2.54,y+1.27,ef(.9,"(justify left)")) if name in ("R","C") else (x,y-6.35,y-3.81,ef())
        if name=="ISO1212DBQR":ry,vy=y-44.45,y-40.64
        props=f'(property "Reference" {q(ref)} (at {rx} {ry} 0) {sty}) (property "Value" {q(value)} (at {rx} {vy} 0) {sty}) (property "MPN" {q(mpn)} (at {x} {y} 0) {ef(extra="hide")}) (property "Footprint" {q(fp)} (at {x} {y} 0) {ef(extra="hide")})'
        items.append(f'(symbol (lib_id "DIGITALINPUTS:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{uid(ref)}") {props} (instances (project "digital_inputs" (path "/{root}" (reference {q(ref)}) (unit 1)))))')
        if not ref.startswith("#"):parts[ref]={"mpn":mpn,"value":value,"footprint":fp,"pins":{},"status":"proposed_not_qualified",**extra}

    def label(ref,pin,net,dx=0,dy=0):
        x,y=pos[ref][str(pin)];ex,ey=round(x+dx,4),round(y+dy,4)
        if dx or dy:items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {q(net)} (at {ex} {ey} 0) {ef(.9,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')
        if ref in parts:parts[ref]["pins"][str(pin)]=net

    def nc(ref,pin):
        x,y=pos[ref][str(pin)];items.append(f'(no_connect (at {x} {y}) (uuid "{uid(ref+str(pin)+"nc")}"))');parts[ref]["pins"][str(pin)]=None

    def note(x,y,text,size=1.4):items.append(f'(text {q(text)} (at {x} {y} 0) {ef(size,"(justify left top)")} (uuid "{uid(text)}"))')

    for pair in range(11):
        bx=20.32+(pair%3)*381;by=68.58+(pair//3)*185.42
        ua=f"U{pair+1}";a,b=channels[pair*2:pair*2+2]
        note(bx,by-10.16,f'{a["component"]}: {a["id"]} / {b["id"]} - FIELD inputs -> LOGIC',1.5)
        place("ISO1212DBQR",ua,"ISO1212DBQR",bx+223.52,by+63.5,ic,"ISO1212DBQR","Package_SO:SSOP-16_3.9x4.9mm_P0.635mm",ledger_component=a["component"],floating_islands=[13,12],footprint_status="candidate; TI DBQ land pattern and SUB islands need final layout review")
        umap={1:"LOGIC_GND",2:"IO_3V3",3:"IO_3V3",4:a["logic_net"],5:b["logic_net"],8:"LOGIC_GND",9:"FIELD_GND",10:b["id"]+"_IN",11:b["id"]+"_SENSE",12:b["id"]+"_SUB_ISLAND",13:a["id"]+"_SUB_ISLAND",14:"FIELD_GND",15:a["id"]+"_IN",16:a["id"]+"_SENSE"}
        for pin,net in umap.items():label(ua,pin,net,dx=-40.64 if pin>=9 else 7.62)
        nc(ua,6);nc(ua,7)
        for slot,ch in enumerate((a,b)):
            index=pair*2+slot;cid=ch["id"];cy=by+12.7+slot*66.04
            rt=f"R{index+1}";rs=f"R{index+101}";rp=f"R{index+201}";cf=f"C{index+1}"
            place("R",rt,"1k MELF 1%",bx+17.78,cy,two,"SMM02040C1001FB300","Resistor_SMD:R_MiniMELF_MMA-0204",role="threshold_pulse",resistance_ohm=1000,tolerance=.01,tcr_ppm_k=50,power_screen_w=.25,voltage_rating_v=200)
            label(rt,1,cid+"_FIELD",dy=-7.62);label(rt,2,cid+"_SENSE",dy=7.62)
            place("R",rs,"562R 1%",bx+73.66,cy,two,"CRCW0603562RFKEA","Resistor_SMD:R_0603_1608Metric",role="sense",resistance_ohm=562,tolerance=.01,tcr_ppm_k=100,power_screen_w=.1,voltage_rating_v=75)
            label(rs,1,cid+"_SENSE",dy=-7.62);label(rs,2,cid+"_IN",dy=7.62)
            place("C",cf,"10nF 100V C0G",bx+129.54,cy,two,"C2012C0G2A103J125AA","Capacitor_SMD:C_0805_2012Metric",role="field_filter",capacitance_f=10e-9,tolerance=.05,tcr_ppm_k=30,voltage_rating_v=100)
            label(cf,1,cid+"_SENSE",dy=-7.62);label(cf,2,"FIELD_GND",dy=7.62)
            place("R",rp,"100k 1%",bx+200.66+slot*83.82,by+152.4,two,"CRCW0603100KFKEA","Resistor_SMD:R_0603_1608Metric",role="output_bias",resistance_ohm=100000,tolerance=.01,tcr_ppm_k=100,power_screen_w=.1,voltage_rating_v=75)
            label(rp,1,ch["logic_net"],dy=-7.62);label(rp,2,"LOGIC_GND",dy=7.62)
            term=next(t for t in terminals if t["net"]==cid+"_FIELD")
            mapping.append({**ch,"schematic_ref":ua,"terminal":{k:term[k] for k in ("connector","position","net","domain")},"threshold_ref":rt,"sense_ref":rs,"filter_ref":cf,"output_bias_ref":rp,"substrate_net":cid+"_SUB_ISLAND"})
        cv=f"C{pair+101}"
        place("C",cv,"100nF 25V X7R",bx+312.42,by+17.78,two,"06033C104JAT2A","Capacitor_SMD:C_0603_1608Metric",role="logic_bypass",capacitance_f=100e-9,tolerance=.05,voltage_rating_v=25)
        label(cv,1,"IO_3V3",dy=-7.62);label(cv,2,"LOGIC_GND",dy=7.62)
    # Preserve field terminal identifiers and positions exactly. Other connectors are internal boundaries.
    for bank in range(3):
        ref=f"JDI{bank}";x=825.5+bank*104.14;y=647.7
        place("Conn8",ref,ref+" / LEDGER",x,y,conns[8],role="field_terminal_boundary_not_connector_selection")
        for t in terminals:
            if t["connector"]==ref:label(ref,t["position"],t["net"],dx=-35.56)
    for ref,nets,x in [("JLOG1",["IO_3V3","LOGIC_GND"]+[c["logic_net"] for c in channels[:12]],863.6),("JLOG2",["IO_3V3","LOGIC_GND"]+[c["logic_net"] for c in channels[12:]],1059.18)]:
        place("Conn"+str(len(nets)),ref,"INTERNAL LOGIC BOUNDARY",x,713.74,conns[len(nets)],role="logic_boundary_not_user_terminal")
        for i,n in enumerate(nets,1):label(ref,i,n,dx=-66.04)
    for i,(n,x) in enumerate((("IO_3V3",1000.76),("LOGIC_GND",1092.2)),1):
        ref=f"#FLG0{i}";place("PWR_FLAG",ref,"LOGIC SUPPLY",x,591.82,flags);label(ref,1,n,dy=7.62)
    note(20.32,15.24,"BASELINE 22 ISOLATED SINKING DIGITAL INPUTS - 6 HOME + 16 AUXILIARY - REVIEW r0.1",3)
    note(20.32,29.21,"0-30V input study; low<=5V / high>=15V targets. PNP source or dry contact to field positive. Common FIELD_GND; no per-channel isolation.\n11 ISO1212 devices require IO_3V3 only. Do not join FIELD_GND to LOGIC_GND. SUB pins get separate floating copper islands; never ground or join them.",1.6)
    note(790,533.4,"All JDI names/positions match frozen ledger.\nJDI0/1 have no local common terminal: use JDI2.7/.8.\nNo sensor positive supply is provided by this sheet.\nBoundary symbols are not approved connector MPNs.\nNo PE capacitor fitted: whole-system coupling/EMC is open.",1.5)
    note(20.32,808,"EN is tied to IO_3V3. Powered open input reads LOW. Unpowered/brownout output is UNDETERMINED; pull-down is bias, not a fail-safe guarantee.\nMask all inputs until qualified rail/FPGA readiness. PROBE/TOOLSETTER filters need latency qualification. No safety input certification, physical EMC result or PCB release.",1.5)
    (OUT/"digital_inputs.kicad_sch").write_text(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "A0") (lib_symbols {"".join(library)})\n'+"\n".join(items)+")\n",encoding="utf-8")
    (OUT/"DIGITALINPUTS.kicad_sym").write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+"\n".join(s.replace('(symbol "DIGITALINPUTS:','(symbol "',1) for s in library)+")\n",encoding="utf-8")
    (OUT/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "DIGITALINPUTS")(type "KiCad")(uri "${KIPRJMOD}/DIGITALINPUTS.kicad_sym")(options "")(descr "Baseline digital input review")))\n',encoding="utf-8")
    (OUT/"digital_inputs.kicad_pro").write_text('{"meta":{"filename":"digital_inputs.kicad_pro","version":1}}\n',encoding="utf-8")
    model={"schema_version":1,"revision":"digital-inputs-r0.1","candidate":"baseline-6j-2enc","status":"review_circuit_not_qualified","manufacturing_ready":False,"physical_qualification":False,
           "ledger_sha256":hashlib.sha256(frozen.read_bytes()).hexdigest(),"channel_count":22,"home_count":6,"additional_count":16,"device_count":11,
           "interface":next(i for i in ledger["interfaces"] if i["id"]=="digital_input"),"logic_supply_v":[3.2,3.4],"logic_ground":"LOGIC_GND","field_ground":"FIELD_GND",
           "source_spec":{"current_5v_to_falling_a":[.0019,.0025],"current_above_falling_to_30v_a":[.00205,.00275],"current_typical_formula_a":.00225,"current_spec_rsense_tolerance":.01,"threshold_falling_min_v":8.7,"threshold_falling_typ_v":9.2,"threshold_rising_typ_v":10.4,"threshold_rising_max_v":10.95,"intrinsic_falling_min_v":6.5,"intrinsic_rising_max_v":8.55,"icc_max_per_device_a":.0019,"voh_drop_max_v":.4,"vol_max_v":.4,"propagation_lh_max_s":140e-9,"propagation_hl_max_s":15e-9},
           "analysis":{"temperature_departure_k":100,"threshold_corner_result_is_screen_only":True,"filter_corner_result_is_end_to_end_delay":False,"filter_model":"RTHR*CIN only; source/cable impedance and nonlinear input current omitted","resistor_drift_after_initial_tolerance":"additional TCR allowance; lifetime drift not established"},
           "output_default":{"powered_open_input":"low","powered_valid_input":"follows input","brownout_or_unpowered":"undetermined; weak bias is not a guarantee","en_connection":"IO_3V3","validity_requirement":"FPGA must ignore until independent rail/reset readiness; not implemented here"},
           "isolation":{"type":"component basic isolation FIELD-to-LOGIC; no complete-board rating","field_returns_common":True,"channel_to_channel_claim":False,"substrates":"22 separate floating copper islands, approximately 2x2mm each; never connect to each other or any ground","pe_capacitor_fitted":False,"total_field_to_other_ground_capacitance_verified":False},
           "channels":mapping,"terminals":terminals,"components":parts}
    (OUT/"design.json").write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
    print(OUT/"digital_inputs.kicad_sch")


if __name__=="__main__":main()
