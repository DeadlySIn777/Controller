"""Independent 24-general-DI pin/domain/default/native-export checks.

The expected ISO1212 map below is transcribed from TI Figure 4-2, not imported
from the generator. Calculation screens do not prove end-to-end timing, EMC,
full-board isolation or a sensor-supply circuit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/motherboard_di"
NS = uuid.UUID("a5d3f6aa-29d9-4d67-8e75-0a7cb6230813")
SPEC_LIMITS = {"current_5v_to_falling_a":[.0019,.0025],"current_above_falling_to_30v_a":[.00205,.00275],"current_typical_formula_a":.00225,"current_spec_rsense_tolerance":.01,"threshold_falling_min_v":8.7,"threshold_falling_typ_v":9.2,"threshold_rising_typ_v":10.4,"threshold_rising_max_v":10.95,"intrinsic_falling_min_v":6.5,"intrinsic_rising_max_v":8.55,"icc_max_per_device_a":.0019,"voh_drop_max_v":.4,"vol_max_v":.4,"propagation_lh_max_s":140e-9,"propagation_hl_max_s":15e-9}


def read_netlist(path):
    root = ET.parse(path).getroot()
    parts = {}
    for node in root.findall("components/comp"):
        ref = node.attrib["ref"]
        if ref.startswith("#"):
            continue
        if ref in parts:
            raise ValueError("duplicate native reference " + ref)
        fields = {n.attrib["name"]:n.text or "" for n in node.findall("fields/field")}
        parts[ref] = {"value":node.findtext("value",""),"mpn":fields.get("MPN",""),"footprint":node.findtext("footprint",""),"pins":{}}
    for net in root.findall("nets/net"):
        name = net.attrib["name"].removeprefix("/")
        for node in net.findall("node"):
            ref,pin = node.attrib["ref"],node.attrib["pin"]
            if ref.startswith("#"):
                continue
            if ref not in parts or pin in parts[ref]["pins"]:
                raise ValueError("repeated or unknown native pin")
            parts[ref]["pins"][pin] = None if name.startswith("unconnected-") else name
    return parts


def expected_substrate_warnings():
    return [{"reference":f"U{8001+i//2}","pin":13 if i%2==0 else 12,"net":f"DI{i}_SUB_ISLAND","type":"isolated_pin_label","severity":"warning","label_uuid":str(uuid.uuid5(NS,f'U{8001+i//2}{13 if i%2==0 else 12}label')),"reason":"TI SLLSEY7G Fig4-2: this SUB net is one isolated floating copper island; no ground or other-pin connection"} for i in range(24)]


def footprint_check(text):
    pads = re.findall(r'\(pad "(\d+)" smd (\w+) \(at (-?[0-9.]+) (-?[0-9.]+)\) \(size ([0-9.]+) ([0-9.]+)\) \(layers "F.Cu" "F.Paste" "F.Mask"\)\)',text)
    if len(re.findall(r'\(pad\b',text)) != 16 or len(pads) != 16 or len({p[0] for p in pads}) != 16:
        return False
    for num,shape,x,y,w,h in pads:
        i = int(num)
        expected_x = -2.7 if i<=8 else 2.7
        expected_y = -2.2225+(i-1)*.635 if i<=8 else 2.2225-(i-9)*.635
        if i not in range(1,17) or shape != "rect" or abs(float(x)-expected_x)>1e-8 or abs(float(y)-expected_y)>1e-8 or (float(w),float(h)) != (1.6,.41):
            return False
    return True


def calculations(d):
    # Published current includes +/-1% Rs initial tolerance. Additional TCR
    # extension remains a screen over 100 K, not a new TI guarantee.
    dt = d["analysis"]["temperature_departure_k"]
    ilo,ihi = .00205/(1+100*dt/1e6), .00275/(1-100*dt/1e6)
    rlo,rhi = 1000*.99*(1-50*dt/1e6),1000*1.01*(1+50*dt/1e6)
    clo,chi = 10e-9*.95*(1-30*dt/1e6),10e-9*1.05*(1+30*dt/1e6)
    rpmin = 100000*.99*(1-100*dt/1e6)
    return {"active_input_current_screen_a":[ilo,ihi],"all_24_active_field_current_screen_a":24*ihi,"all_24_field_power_at_30v_screen_w":24*ihi*30,"rthreshold_dc_power_max_w":ihi**2*rhi,"rsense_dc_power_max_w":ihi**2*562*1.01*(1+100*dt/1e6),"rthreshold_30v_step_initial_power_screen_w":900/rlo,"filter_30v_charge_energy_screen_j":.5*chi*900,"filter_rc_time_constant_screen_s":[rlo*clo,rhi*chi],"rising_threshold_conservative_screen_max_v":8.55+ihi*rhi,"falling_threshold_intrinsic_screen_min_v":6.5,"logic_static_current_screen_a":12*.0019+24*max(d["logic_supply_v"])/rpmin,"output_high_screen_min_v":min(d["logic_supply_v"])-.4,"output_low_spec_max_v":.4,"sensor_supply_reserved_a":3*.20,"limitations":["RTHR*C is not complete input propagation delay; source/cable impedance, nonlinear input current and later acquisition/filtering are outside this model.","Current/threshold TCR extension is a screen, not a new guaranteed component specification.","Logic static current excludes switching/load capacitance; input field current comes from external sources.","Sensor supplies/current limiters/voltage and fault telemetry are not fitted or measured by these frontends.","30V RC-step pulse/energy screens are not surge/EFT/cable-energy or full-board thermal/EMC/isolation qualification.","No lifetime resistor drift or qualified NPN/12V/AUTO sensor mode is established."]}


def validate(d, netlist=None, erc=None, footprint=None):
    errors = []
    def check(ok,msg):
        if not ok:
            errors.append(msg)
    try:
        check(d["schema_version"]==1 and d["revision"]=="motherboard-di-r0.1","wrong schema/revision")
        check(d["parent_reference_index"]==8,"parent reference index changed")
        check(d["manufacturing_ready"] is False and d["physical_qualification"] is False,"unqualified source cannot claim release")
        check((d["channel_count"],d["general_count"],d["motor_alarm_count"],d["probe_count"],d["device_count"],d["fitted_component_count"],d["fitted_pad_count"])==(24,24,0,0,12,120,408),"24 general DI capacity/independence mismatch")
        check(d["logic_supply_v"]==[3.2,3.4] and d["logic_ground"]=="LOGIC_GND" and d["field_ground"]=="FIELD_B_0V","logic/field supply domain mismatch")
        check(d["source_spec"]==SPEC_LIMITS,"TI source specification differs from reviewed table")
        check(d["analysis"]["temperature_departure_k"]==100 and d["analysis"]["threshold_corner_result_is_screen_only"] is True and d["analysis"]["filter_corner_result_is_end_to_end_delay"] is False,"calculation scope changed")
        check(d["interface"]=={"operating_min_v":0,"operating_max_v":30,"guaranteed_low_target_v":5,"guaranteed_high_target_v":15,"input_style":"fixed_sinking_PNP_or_dry_contact","NPN_or_auto_mode_implemented":False},"input voltage/mode contract changed")
        check(d["output_default"]["en_connection"]=="IO_3V3" and d["output_default"]["powered_open_input"]=="low" and d["output_default"]["brownout_or_unpowered"].startswith("undetermined"),"output default/brownout claim mismatch")
        check(d["isolation"]["field_returns_common"] is True and d["isolation"]["channel_to_channel_claim"] is False and d["isolation"]["pe_capacitor_fitted"] is False,"isolation/PE claim mismatch")
        supply = d["sensor_supplies"]
        check(supply["implemented"] is False and supply["voltage_fault_telemetry_implemented"] is False and supply["entry"]=="FIELD_B" and (supply["groups"],supply["per_group_continuous_a"],supply["total_reserved_continuous_a"],supply["shared_supply_contacts"])==(3,.20,.60,[9,10]),"unimplemented sensor supply/0.20A shared-group envelope mismatch")
        check(d["acquisition"]["implemented"] is False and d["acquisition"]["output_nets"]==[f"DI{i}_LOGIC" for i in range(24)],"acquisition validity not implemented or wrong outputs")
        p = d["components"]
        expected_refs = {*[f"U{8001+i}" for i in range(12)],*[f"R{8001+i+j}" for i in range(24) for j in (0,100,200)],*[f"C{8001+i}" for i in range(24)],*[f"C{8101+i}" for i in range(12)]}
        check(set(p)==expected_refs,"fitted component set mismatch")
        check(all(x["fitted"] is True and x["footprint"] and x["mpn"] for x in p.values()),"fitted part missing MPN/footprint or boundary included")
        check(sum(len(x["pins"]) for x in p.values())==408,"physical fitted pin count mismatch")
        ch = d["channels"]
        check([c["id"] for c in ch]==[f"DI{i}" for i in range(24)],"general DI IDs missing/duplicate/reordered")
        for pair in range(12):
            ua = f"U{8001+pair}"
            a,b = 2*pair,2*pair+1
            # Datasheet pins: logic1/8GND,2VCC,3EN,4/5OUT; field9FGND2,
            #10IN2,11SENSE2,12SUB2,13SUB1,14FGND1,15IN1,16SENSE1.
            pins = {"1":"LOGIC_GND","2":"IO_3V3","3":"IO_3V3","4":f"DI{a}_LOGIC","5":f"DI{b}_LOGIC","6":None,"7":None,"8":"LOGIC_GND","9":"FIELD_B_0V","10":f"DI{b}_IN","11":f"DI{b}_SENSE","12":f"DI{b}_SUB_ISLAND","13":f"DI{a}_SUB_ISLAND","14":"FIELD_B_0V","15":f"DI{a}_IN","16":f"DI{a}_SENSE"}
            check((p[ua]["mpn"],p[ua]["footprint"],p[ua]["pins"])==("ISO1212DBQR","CNC_MB_DI:ISO1212_DBQ16_TI",pins),ua+" ISO1212 physical pin/net/footprint mismatch")
            cap = p[f"C{8101+pair}"]
            check(cap["mpn"]=="06033C104JAT2A" and cap["pins"]=={"1":"IO_3V3","2":"LOGIC_GND"} and cap["capacitance_f"]==100e-9 and cap["voltage_rating_v"]>=25,"logic bypass mismatch "+ua)
        for i,c in enumerate(ch):
            check(c["kind"]=="general_digital_input" and (c["group"],c["device_channel"],c["schematic_ref"],c["logic_net"],c["field_net"])==(i//8,i%2+1,f"U{8001+i//2}",f"DI{i}_LOGIC",f"DI{i}_FIELD"),f"DI{i} channel/logic assignment mismatch")
            check(c["terminal"]=={"connector":f"XDI{i//8}","position":i%8+1,"logical_net":f"DI{i:02}","schematic_net":f"DI{i}_FIELD","domain":"FIELD_B"},f"DI{i} terminal mapping mismatch")
            check((c["threshold_ref"],c["sense_ref"],c["filter_ref"],c["output_bias_ref"],c["substrate_net"])==(f"R{8001+i}",f"R{8101+i}",f"C{8001+i}",f"R{8201+i}",f"DI{i}_SUB_ISLAND"),f"DI{i} support reference mismatch")
            for ref,mpn,pins,value,tol,tcr,power,voltage in (
                (f"R{8001+i}","SMM02040C1001FB300",{"1":f"DI{i}_FIELD","2":f"DI{i}_SENSE"},1000,.01,50,.25,200),
                (f"R{8101+i}","CRCW0603562RFKEA",{"1":f"DI{i}_SENSE","2":f"DI{i}_IN"},562,.01,100,.1,75),
                (f"R{8201+i}","CRCW0603100KFKEA",{"1":f"DI{i}_LOGIC","2":"LOGIC_GND"},100000,.01,100,.1,75)):
                r = p[ref]
                check(r["mpn"]==mpn and r["pins"]==pins,ref+" resistor MPN/connection mismatch")
                check(type(r["resistance_ohm"]) in (int,float) and (r["resistance_ohm"],r["tolerance"],r["tcr_ppm_k"],r["power_screen_w"],r["voltage_rating_v"])==(value,tol,tcr,power,voltage),ref+" resistor rating/value mismatch")
            cf = p[f"C{8001+i}"]
            check(cf["mpn"]=="C2012C0G2A103J125AA" and cf["pins"]=={"1":f"DI{i}_SENSE","2":"FIELD_B_0V"} and (cf["capacitance_f"],cf["tolerance"],cf["tcr_ppm_k"],cf["voltage_rating_v"])==(10e-9,.05,30,100),f"DI{i} field filter mismatch")
            uses = [(ref,pin) for ref,x in p.items() for pin,net in x["pins"].items() if net==f"DI{i}_SUB_ISLAND"]
            check(uses==[(f"U{8001+i//2}",str(13 if i%2==0 else 12))],f"DI{i} substrate must be a separate single-pin floating island")
        b = d["boundaries"]
        check(set(b)=={"J8001","J8002","J8003","J8004"},"boundary set mismatch")
        check(all(x["fitted"] is False and not x["footprint"] and not x["mpn"] for x in b.values()),"unimplemented boundary became fitted connector")
        expected_terminals = []
        for bank in range(3):
            nets = [f"DI{bank*8+i}_FIELD" for i in range(8)]+[f"SENS24_G{bank}"]*2+["FIELD_B_0V"]*2
            check(b[f"J{8001+bank}"]["pins"]=={str(i+1):net for i,net in enumerate(nets)},f"XDI{bank} native boundary mapping mismatch")
            for i,net in enumerate(nets,1):
                logical = f"DI{bank*8+i-1:02}" if i<=8 else f"SENS24_G{bank}"+("b" if i==10 else "") if i<=10 else f"FIELD_B_0V_DI{bank}_{i}"
                expected_terminals.append({"connector":f"XDI{bank}","position":i,"logical_net":logical,"schematic_net":net,"domain":"FIELD_B","fitted_connector":False,"sensor_supply_current_limit_a":.20 if i in (9,10) else None})
        check(d["terminals"]==expected_terminals,"36 logical field positions/aliases mismatch")
        check(b["J8004"]["pins"]=={str(i+1):net for i,net in enumerate(["IO_3V3","LOGIC_GND"]+[f"DI{i}_LOGIC" for i in range(24)])},"local acquisition boundary mismatch")
        if netlist:
            exported = read_netlist(netlist)
            expected = {**p,**b}
            check(set(exported)==set(expected),"native component/boundary set mismatch")
            for ref,x in expected.items():
                for key in ("value","mpn","footprint","pins"):
                    check(ref in exported and exported[ref][key]==x[key],ref+" native "+key+" mismatch")
        if footprint:
            check(footprint_check(Path(footprint).read_text(encoding="utf-8")),"TI DBQ0016A native footprint pad geometry/number mismatch")
        if erc:
            report = json.loads(Path(erc).read_text(encoding="utf-8"))
            records = expected_substrate_warnings()
            actual = [v for sheet in report.get("sheets",[]) for v in sheet.get("violations",[])]
            check(report.get("source")=="motherboard_di.kicad_sch" and bool(report.get("sheets")),"ERC source/sheets mismatch")
            check(set(report.get("included_severities",[]))>={"warning","error"},"ERC severities suppressed")
            check(report.get("ignored_checks")==[],"ERC checks must not be ignored")
            check(len(actual)==24,"ERC must retain exactly 24 documented SUB label warnings")
            wanted = {r["label_uuid"]:r for r in records}
            seen = set()
            for v in actual:
                items = v.get("items",[])
                key = items[0].get("uuid") if len(items)==1 else None
                check(key in wanted and key not in seen,"unexpected or duplicate ERC warning")
                seen.add(key)
                if key in wanted:
                    r = wanted[key]
                    check(v.get("severity")=="warning" and v.get("type")=="isolated_pin_label" and items[0].get("description")=="Label '"+r["net"]+"'","ERC case is not a separately floating SUB net")
        calc = calculations(d) if not errors else {}
        if calc:
            check(calc["rising_threshold_conservative_screen_max_v"]<15 and calc["falling_threshold_intrinsic_screen_min_v"]>5,"threshold screen margin failed")
            check(calc["rthreshold_dc_power_max_w"]<.25 and calc["rsense_dc_power_max_w"]<.1,"input resistor DC power screen failed")
    except (KeyError,TypeError,ValueError,OSError,ET.ParseError,OverflowError,ZeroDivisionError) as exc:
        errors.append("invalid design/evidence: "+str(exc))
        calc = {}
    return {"ok":not errors,"errors":errors,"warnings":["24 isolated_pin_label warnings are exact retained floating SUB islands, not broad ERC suppression.","Sensor power/current limiting/telemetry, local input controller, validity/freshness, terminal selection and final PCB isolation are unimplemented parent circuits.","Powered-open LOW is not an unpowered/brownout guarantee; weak output bias cannot establish fail-safe validity.","Physical qualification, complete input latency and 12V/NPN/AUTO mode are unproved."],"calculations":calc,"manufacturing_ready":False,"physical_qualification":False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true")
    args = parser.parse_args()
    d = json.loads((OUT / "design.json").read_text(encoding="utf-8"))
    result = validate(d,OUT/"netlist.xml",OUT/"erc.json",OUT/"CNC_MB_DI.pretty/ISO1212_DBQ16_TI.kicad_mod")
    if args.write:
        (OUT / "validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        (OUT / "expected-erc-warnings.json").write_text(json.dumps(expected_substrate_warnings(),indent=2)+"\n",encoding="utf-8")
        if result["ok"]:
            with (OUT / "bom.csv").open("w",encoding="utf-8",newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["reference","quantity","value","mpn","footprint","status"])
                for ref,x in d["components"].items():
                    writer.writerow([ref,1,x["value"],x["mpn"],x["footprint"],"source candidate; not physically qualified"])
            (OUT / "boundary-map.json").write_text(json.dumps({"fitted":False,"excluded_from_PCB_and_BOM":True,"boundaries":d["boundaries"],"terminals":d["terminals"],"sensor_supplies":d["sensor_supplies"]},indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
