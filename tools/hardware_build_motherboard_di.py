"""Build the motherboard's 24 general isolated input frontends.

New source, not a rewritten historical 22 mixed HOME/probe/alarm input study.
Parent references reserve index 8. Native schematic boundaries have no fitted
connector footprint. Sensor supplies, acquisition/validity and final PCB remain
explicit parent work; this sheet is not a controller or manufacturing release.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/motherboard_di"
NS = uuid.UUID("a5d3f6aa-29d9-4d67-8e75-0a7cb6230813")
BASE = ROOT / "tools/hardware_build_digital_inputs.py"
spec = importlib.util.spec_from_file_location("reviewed_di_drawing_helpers", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
q, ef = old.q, old.ef


def uid(name):
    return str(uuid.uuid5(NS, name))


def symbol(name, pins, body, ref="U"):
    return old.symbol(name, pins, body, ref).replace("DIGITALINPUTS:", "MBDI:")


def iso_footprint():
    """TI DBQ0016A 4214846/A example, without an invented SUB pad/ground."""
    pads = []
    for pin in range(1, 17):
        x = -2.7 if pin <= 8 else 2.7
        y = -2.2225 + (pin - 1) * .635 if pin <= 8 else 2.2225 - (pin - 9) * .635
        pads.append(f'(pad "{pin}" smd rect (at {x:g} {y:g}) (size 1.6 0.41) (layers "F.Cu" "F.Paste" "F.Mask"))')
    return '''(footprint "ISO1212_DBQ16_TI" (version 20241229) (generator "pcbnew")
  (layer "F.Cu") (descr "TI ISO1212 DBQ0016A example board lands, drawing 4214846/A; source-reviewed prototype candidate")
  (tags "TI ISO1212 DBQ SSOP16") (attr smd)
  (property "Reference" "REF**" (at 0 -3.3) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "ISO1212_DBQ16_TI" (at 0 3.3) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -1.99 -2.5) (end 1.99 2.5) (stroke (width 0.1) (type default)) (layer "F.Fab"))
  (fp_line (start -1.99 -1.75) (end -1.24 -2.5) (stroke (width 0.1) (type default)) (layer "F.Fab"))
  (fp_rect (start -3.75 -2.75) (end 3.75 2.75) (stroke (width 0.05) (type default)) (layer "F.CrtYd"))
  (fp_circle (center -3.8 -2.8) (end -3.65 -2.8) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))
''' + "\n".join(pads) + '''
  (model "${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/SSOP-16_3.9x4.9mm_P0.635mm.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
)\n'''


def build(out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    baseline = json.loads((ROOT / "hardware/digital_inputs/design.json").read_text(encoding="utf-8"))
    # SLLSEY7G Figure 4-2. Geometry preserved from the reviewed baseline;
    # independent validator keeps a separately transcribed pin/net contract.
    ic = [(16,"SENSE1",-20.32,33.02,0,"input"),(15,"IN1",-20.32,22.86,0,"input"),
          (14,"FGND1",-20.32,12.7,0,"passive"),(13,"SUB1",-20.32,2.54,0,"passive"),
          (11,"SENSE2",-20.32,-12.7,0,"input"),(10,"IN2",-20.32,-22.86,0,"input"),
          (9,"FGND2",-20.32,-33.02,0,"passive"),(12,"SUB2",-20.32,-43.18,0,"passive"),
          (2,"VCC1",20.32,33.02,180,"power_in"),(3,"EN",20.32,22.86,180,"input"),
          (4,"OUT1",20.32,12.7,180,"output"),(5,"OUT2",20.32,-12.7,180,"output"),
          (1,"GND1",20.32,-22.86,180,"power_in"),(8,"GND1",20.32,-33.02,180,"power_in"),
          (6,"NC",20.32,-43.18,180,"no_connect"),(7,"NC",20.32,-53.34,180,"no_connect")]
    two = [(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    rbody = '(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
    cbody = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    body = '(rectangle (start -17.78 38.1) (end 17.78 -58.42) (stroke (width 0.254) (type default)) (fill (type background))) (polyline (pts (xy 0 38.1) (xy 0 -58.42)) (stroke (width 0.3) (type dash)) (fill (type none)))'
    library = [symbol("ISO1212DBQR",ic,body),symbol("R",two,rbody,"R"),symbol("C",two,cbody,"C")]
    connectors = {}
    for count in (12, 26):
        pins = [(i,str(i),-5.08,-(i-1)*5.08,0,"passive") for i in range(1,count+1)]
        connectors[count] = pins
        library.append(symbol(f"Boundary{count}",pins,f'(rectangle (start -2.54 2.54) (end 2.54 {-count*5.08+2.54}) (stroke (width 0.254) (type default)) (fill (type background)))',"J"))
    flagpins = [(1,"pwr",0,0,90,"power_out")]
    library.append(symbol("PWR_FLAG",flagpins,"","#FLG"))
    root = uid("root")
    items, positions, parts, boundaries, channels = [], {}, {}, {}, []

    def place(name, ref, value, x, y, pins, *, mpn="", footprint="", fitted=True, **extra):
        positions[ref] = {str(i):(round(x+px,4),round(y-py,4)) for i,_,px,py,_,_ in pins}
        if name in ("R","C"):
            rx, ry, vy, style = x+3.81, y-2.54, y+1.27, ef(.9,"(justify left)")
        else:
            rx, ry, vy, style = x, y-6.35, y-3.81, ef()
        if name == "ISO1212DBQR":
            ry, vy = y-44.45, y-40.64
        properties = ''.join(f'(property {q(k)} {q(v)} (at {rx if k in ("Reference","Value") else x} {ry if k == "Reference" else vy if k == "Value" else y} 0) {style if k in ("Reference","Value") else ef(extra="hide")})' for k,v in (("Reference",ref),("Value",value),("MPN",mpn),("Footprint",footprint)))
        items.append(f'(symbol (lib_id "MBDI:{name}") (at {x} {y} 0) (unit 1) (in_bom {"yes" if fitted else "no"}) (on_board {"yes" if fitted else "no"}) (dnp no) (uuid "{uid(ref)}") {properties} (instances (project "motherboard_di" (path "/{root}" (reference {q(ref)}) (unit 1)))))')
        if not ref.startswith("#"):
            (parts if fitted else boundaries)[ref] = {"mpn":mpn,"value":value,"footprint":footprint,"pins":{},"fitted":fitted,"status":"source_candidate_not_qualified" if fitted else "unimplemented_parent_boundary_excluded_from_PCB",**extra}

    def label(ref, pin, net, dx=0, dy=0):
        x,y = positions[ref][str(pin)]
        ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {q(net)} (at {ex} {ey} 0) {ef(.9,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')
        for dictionary in (parts,boundaries):
            if ref in dictionary:
                dictionary[ref]["pins"][str(pin)] = net

    def nc(ref,pin):
        x,y = positions[ref][str(pin)]
        items.append(f'(no_connect (at {x} {y}) (uuid "{uid(ref+str(pin)+"nc")}"))')
        parts[ref]["pins"][str(pin)] = None

    def note(x,y,text,size=1.4):
        items.append(f'(text {q(text)} (at {x} {y} 0) {ef(size,"(justify left top)")} (uuid "{uid(text)}"))')

    for pair in range(12):
        bx,by = 20.32+(pair%3)*381, 68.58+(pair//3)*185.42
        ua = f"U{8001+pair}"
        note(bx,by-10.16,f"GENERAL DI{pair*2} / DI{pair*2+1} - FIELD_B to LOGIC",1.5)
        place("ISO1212DBQR",ua,"ISO1212DBQR",bx+223.52,by+63.5,ic,mpn="ISO1212DBQR",footprint="CNC_MB_DI:ISO1212_DBQ16_TI",floating_islands=[13,12],source="TI SLLSEY7G Fig4-2 and DBQ0016A example")
        a,b = pair*2,pair*2+1
        pinmap = {1:"LOGIC_GND",2:"IO_3V3",3:"IO_3V3",4:f"DI{a}_LOGIC",5:f"DI{b}_LOGIC",8:"LOGIC_GND",9:"FIELD_B_0V",10:f"DI{b}_IN",11:f"DI{b}_SENSE",12:f"DI{b}_SUB_ISLAND",13:f"DI{a}_SUB_ISLAND",14:"FIELD_B_0V",15:f"DI{a}_IN",16:f"DI{a}_SENSE"}
        for pin,net in pinmap.items():
            label(ua,pin,net,dx=-40.64 if pin>=9 else 7.62)
        nc(ua,6); nc(ua,7)
        for slot,i in enumerate((a,b)):
            cy = by+12.7+slot*66.04
            rt,rs,rp,cf = f"R{8001+i}",f"R{8101+i}",f"R{8201+i}",f"C{8001+i}"
            for ref,key,x,y in ((rt,"R1",bx+17.78,cy),(rs,"R101",bx+73.66,cy),(rp,"R201",bx+200.66+slot*83.82,by+152.4)):
                copied = {k:v for k,v in baseline["components"][key].items() if k not in ("pins","status","mpn","footprint","value")}
                src = baseline["components"][key]
                place("R",ref,src["value"],x,y,two,mpn=src["mpn"],footprint=src["footprint"],**copied)
            label(rt,1,f"DI{i}_FIELD",dy=-7.62); label(rt,2,f"DI{i}_SENSE",dy=7.62)
            label(rs,1,f"DI{i}_SENSE",dy=-7.62); label(rs,2,f"DI{i}_IN",dy=7.62)
            label(rp,1,f"DI{i}_LOGIC",dy=-7.62); label(rp,2,"LOGIC_GND",dy=7.62)
            src = baseline["components"]["C1"]
            copied = {k:v for k,v in src.items() if k not in ("pins","status","mpn","footprint","value")}
            place("C",cf,src["value"],bx+129.54,cy,two,mpn=src["mpn"],footprint=src["footprint"],**copied)
            label(cf,1,f"DI{i}_SENSE",dy=-7.62); label(cf,2,"FIELD_B_0V",dy=7.62)
            channels.append({"id":f"DI{i}","kind":"general_digital_input","group":i//8,"device_channel":slot+1,"schematic_ref":ua,"logic_net":f"DI{i}_LOGIC","field_net":f"DI{i}_FIELD","terminal":{"connector":f"XDI{i//8}","position":i%8+1,"logical_net":f"DI{i:02}","schematic_net":f"DI{i}_FIELD","domain":"FIELD_B"},"threshold_ref":rt,"sense_ref":rs,"filter_ref":cf,"output_bias_ref":rp,"substrate_net":f"DI{i}_SUB_ISLAND"})
        src = baseline["components"]["C101"]
        copied = {k:v for k,v in src.items() if k not in ("pins","status","mpn","footprint","value")}
        ref = f"C{8101+pair}"
        place("C",ref,src["value"],bx+312.42,by+17.78,two,mpn=src["mpn"],footprint=src["footprint"],**copied)
        label(ref,1,"IO_3V3",dy=-7.62); label(ref,2,"LOGIC_GND",dy=7.62)

    terminals = []
    for bank in range(3):
        ref = f"J{8001+bank}"
        place("Boundary12",ref,f"XDI{bank} FIELD / SENSOR BOUNDARY",50.8+bank*381,863.6,connectors[12],fitted=False,role="unselected_field_terminal_and_unimplemented_sensor_supply",logical_connector=f"XDI{bank}")
        nets = [f"DI{bank*8+i}_FIELD" for i in range(8)] + [f"SENS24_G{bank}"]*2 + ["FIELD_B_0V"]*2
        for i,net in enumerate(nets,1):
            label(ref,i,net,dx=-27.94)
            logical = f"DI{bank*8+i-1:02}" if i<=8 else f"SENS24_G{bank}" + ("b" if i==10 else "") if i<=10 else f"FIELD_B_0V_DI{bank}_{i}"
            terminals.append({"connector":f"XDI{bank}","position":i,"logical_net":logical,"schematic_net":net,"domain":"FIELD_B","fitted_connector":False,"sensor_supply_current_limit_a":.20 if i in (9,10) else None})
    logic_nets = ["IO_3V3","LOGIC_GND"]+[f"DI{i}_LOGIC" for i in range(24)]
    place("Boundary26","J8004","UNIMPLEMENTED ACQUISITION / LOGIC BOUNDARY",1168.4,833.12,connectors[26],fitted=False,role="local_input_controller_not_drawn")
    for i,net in enumerate(logic_nets,1):
        label("J8004",i,net,dx=-66.04)
    for i,(net,x) in enumerate((("IO_3V3",863.6),("LOGIC_GND",960.12)),1):
        ref = f"#FLG8{i}"
        place("PWR_FLAG",ref,"PARENT LOGIC SUPPLY",x,1010.92,flagpins,fitted=False)
        label(ref,1,net,dy=7.62)
    note(20.32,15.24,"MOTHERBOARD: 24 GENERAL DI - 12 ISO1212 - NEW SOURCE r0.1 / NOT A PCB RELEASE",3)
    note(20.32,29.21,"Fixed sinking inputs: PNP or contact to qualified sensor positive. 0-30V, LOW<=5V / HIGH>=15V targets. NPN/12V/AUTO mode not implemented.\nFIELD_B_0V never joins LOGIC_GND here. Each SUB pin needs a separate floating 2x2mm copper island; no ground or inter-island connection.",1.6)
    note(20.32,800.1,"All 24 DI are general channels, independent of 12 motor alarms and 2 fast probes. No PROBE/HOME/ALM assignment is consumed here.\nEN tied to IO_3V3. Powered open reads LOW. Unpowered/brownout is UNDETERMINED; bias is not guaranteed fail-safe.\nAcquisition, rail/freshness/CRC validity, sensor-power limiters/measurement, TVS/cable qualification and connectors are unfinished parent circuits.",1.5)
    note(20.32,980.44,"XDI9/10 supply contacts are one shared 0.20A group, not 0.20A each. Three groups reserve 0.60A total under frozen IS-1.\nSensor supply is an UNIMPLEMENTED boundary: no source/current limiter/telemetry is fitted by this sheet. All boundary symbols excluded from PCB/BOM.\nRTHR*C is a screen, not complete input propagation delay. No board isolation/EMC/temperature or safety certification is established.",1.5)
    (out / "motherboard_di.kicad_sch").write_text(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "User" 1270 1050) (lib_symbols {"".join(library)})\n'+"\n".join(items)+")\n",encoding="utf-8")
    (out / "MBDI.kicad_sym").write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+"\n".join(s.replace('(symbol "MBDI:','(symbol "',1) for s in library)+")\n",encoding="utf-8")
    (out / "sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "MBDI")(type "KiCad")(uri "${KIPRJMOD}/MBDI.kicad_sym")(options "")(descr "Motherboard 24 DI review")))\n',encoding="utf-8")
    (out / "motherboard_di.kicad_pro").write_text(json.dumps({"meta":{"filename":"motherboard_di.kicad_pro","version":1},"erc":{"rule_severities":{k:"warning" for k in ("single_global_label","four_way_junction","simulation_model_issue","footprint_filter")}}},indent=2)+"\n",encoding="utf-8")
    pretty = out / "CNC_MB_DI.pretty"
    pretty.mkdir(exist_ok=True)
    (pretty / "ISO1212_DBQ16_TI.kicad_mod").write_text(iso_footprint(),encoding="utf-8")
    (out / "fp-lib-table").write_text('(fp_lib_table (version 7) (lib (name "CNC_MB_DI")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_DI.pretty")(options "")(descr "Source-backed TI DBQ0016A lands")))\n',encoding="utf-8")
    model = {"schema_version":1,"revision":"motherboard-di-r0.1","parent_reference_index":8,"status":"source_candidate_not_qualified","manufacturing_ready":False,"physical_qualification":False,"channel_count":24,"general_count":24,"motor_alarm_count":0,"probe_count":0,"device_count":12,"fitted_component_count":120,"fitted_pad_count":408,"logic_supply_v":[3.2,3.4],"logic_ground":"LOGIC_GND","field_ground":"FIELD_B_0V","interface":{"operating_min_v":0,"operating_max_v":30,"guaranteed_low_target_v":5,"guaranteed_high_target_v":15,"input_style":"fixed_sinking_PNP_or_dry_contact","NPN_or_auto_mode_implemented":False},"source_spec":baseline["source_spec"],"analysis":baseline["analysis"],"output_default":baseline["output_default"],"isolation":{**baseline["isolation"],"substrates":"24 separate floating copper islands, approximately 2x2mm each; never connect to each other or any ground"},"sensor_supplies":{"implemented":False,"entry":"FIELD_B","per_group_continuous_a":.20,"groups":3,"total_reserved_continuous_a":.60,"shared_supply_contacts":[9,10],"voltage_fault_telemetry_implemented":False,"source":"frozen IS-1 section03 XDI0/1/2.9/.10 and section04 10.2"},"acquisition":{"implemented":False,"intended":"qualified IOL1 local controller; inputs invalid until independent rails/reset/validated fresh frames","output_nets":[f"DI{i}_LOGIC" for i in range(24)]},"channels":channels,"terminals":terminals,"components":parts,"boundaries":boundaries,"sources":{"baseline_design_sha256":hashlib.sha256((ROOT / "hardware/digital_inputs/design.json").read_bytes()).hexdigest(),"baseline_builder_sha256":hashlib.sha256(BASE.read_bytes()).hexdigest(),"iso1212_datasheet_sha256":hashlib.sha256((ROOT / "research/digital-inputs/iso1212.pdf").read_bytes()).hexdigest(),"iso1212_datasheet_url":"https://www.ti.com/lit/ds/symlink/iso1212.pdf","package_drawing":"DBQ0016A, 4214846/A, 03/2014; pads1.6x0.41mm, x-centres +/-2.7mm, pitch0.635mm; prototype process candidate"}}
    (out / "design.json").write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
    return out / "motherboard_di.kicad_sch"


if __name__ == "__main__":
    print(build())
