"""Validate the actual baseline input netlist and bounded engineering screens."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import uuid
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"hardware/digital_inputs"
NAMESPACE=uuid.UUID("86d2737f-dd12-4428-95b0-38daecf1f8cf")
LOGIC_NETS=[*[f"HOME{i}_FPGA" for i in range(6)],"PROBE_FPGA","TOOLSETTER_FPGA","DOOR_STATUS_FPGA","PROTECTIVE_STATUS_FPGA","SPINDLE_FAULT_FPGA","SPINDLE_READY_FPGA","FEED_HOLD_FPGA","CYCLE_START_FPGA","LUBE_STATUS_FPGA","SPARE_FPGA",*[f"ALM{i}_FPGA" for i in range(6)]]
SPEC_LIMITS={"current_5v_to_falling_a":[.0019,.0025],"current_above_falling_to_30v_a":[.00205,.00275],"current_typical_formula_a":.00225,"current_spec_rsense_tolerance":.01,"threshold_falling_min_v":8.7,"threshold_falling_typ_v":9.2,"threshold_rising_typ_v":10.4,"threshold_rising_max_v":10.95,"intrinsic_falling_min_v":6.5,"intrinsic_rising_max_v":8.55,"icc_max_per_device_a":.0019,"voh_drop_max_v":.4,"vol_max_v":.4,"propagation_lh_max_s":140e-9,"propagation_hl_max_s":15e-9}


def expected_warning_records():
    return [{"reference":f"U{i//2+1}","pin":13 if i%2==0 else 12,"net":f"DI{i:02}_SUB_ISLAND",
             "type":"isolated_pin_label","severity":"warning",
             "label_uuid":str(uuid.uuid5(NAMESPACE,f'U{i//2+1}{13 if i%2==0 else 12}label')),
             "reason":"TI Fig4-2: separate floating substrate island; no connection to any other signal/ground"} for i in range(22)]


def read_netlist(path):
    root=ET.parse(path).getroot();parts={}
    for x in root.findall("components/comp"):
        ref=x.attrib["ref"]
        if ref in parts:raise ValueError("duplicate reference "+ref)
        fields={f.attrib["name"]:f.text or "" for f in x.findall("fields/field")}
        parts[ref]={"value":x.findtext("value",""),"mpn":fields.get("MPN",""),"footprint":x.findtext("footprint",""),"pins":{}}
    for n in root.findall("nets/net"):
        name=n.attrib["name"].removeprefix("/")
        for x in n.findall("node"):
            ref,pin=x.attrib["ref"],x.attrib["pin"]
            if ref.startswith("#"):continue
            if ref not in parts or pin in parts[ref]["pins"]:raise ValueError("unknown or repeated pin "+ref+"."+pin)
            parts[ref]["pins"][pin]=None if name.startswith("unconnected-") else name
    return parts


def calculations(d):
    s=d["source_spec"];p=d["components"];dt=d["analysis"]["temperature_departure_k"]
    def rcorners(ref):
        x=p[ref];return [x["resistance_ohm"]*(1-x["tolerance"])*(1-x["tcr_ppm_k"]*dt/1e6),x["resistance_ohm"]*(1+x["tolerance"])*(1+x["tcr_ppm_k"]*dt/1e6)]
    rth=rcorners("R1");rs=rcorners("R101");rp=rcorners("R201")
    # Published current includes +/-1% Rs initial tolerance; add only external TCR here.
    tcr=p["R101"]["tcr_ppm_k"]*dt/1e6
    ilo=s["current_above_falling_to_30v_a"][0]/(1+tcr);ihi=s["current_above_falling_to_30v_a"][1]/(1-tcr)
    cf=p["C1"];cc=[cf["capacitance_f"]*(1-cf["tolerance"])*(1-cf["tcr_ppm_k"]*dt/1e6),cf["capacitance_f"]*(1+cf["tolerance"])*(1+cf["tcr_ppm_k"]*dt/1e6)]
    vmax=d["interface"]["operating_max_v"];vlogic=max(d["logic_supply_v"])
    return {"active_input_current_screen_a":[ilo,ihi],"all_22_active_field_current_screen_a":22*ihi,
            "all_22_field_power_at_30v_screen_w":22*ihi*vmax,"rthreshold_dc_power_max_w":ihi**2*rth[1],"rsense_dc_power_max_w":ihi**2*rs[1],
            "rthreshold_30v_step_initial_power_screen_w":vmax**2/rth[0],"filter_30v_charge_energy_screen_j":.5*cc[1]*vmax**2,
            "filter_rc_time_constant_screen_s":[rth[0]*cc[0],rth[1]*cc[1]],"filter_cap_max_f":cc[1],
            "rising_threshold_conservative_screen_max_v":s["intrinsic_rising_max_v"]+ihi*rth[1],"falling_threshold_intrinsic_screen_min_v":s["intrinsic_falling_min_v"],
            "logic_static_current_screen_a":11*s["icc_max_per_device_a"]+22*vlogic/rp[0],"output_high_screen_min_v":min(d["logic_supply_v"])-s["voh_drop_max_v"],"output_low_spec_max_v":s["vol_max_v"],
            "per_ic_power_upper_screen_w":2*ihi*vmax+vlogic*s["icc_max_per_device_a"],
            "limitations":["Current/threshold TCR extension is an engineering screen, not a newly guaranteed component specification; intrinsic comparator bounds assumed to remain applicable.",
                           "Published 2.2-2.47mA values describe typical-temperature behavior; use 2.05-2.75mA guaranteed table range at stated Rs conditions for active inputs below30V.",
                           "RTHR*CIN is not propagation delay: source impedance, cable capacitance, nonlinear input current, FPGA synchronization/filtering and latch timing remain outside the model.",
                           "Logic current excludes switching/load-capacitance current. Field input current comes from external sources and is not FIELD_5V consumption.",
                           "Pulse resistor screen is a 30V RC step, not IEC surge/EFT or a cable energy qualification.",
                           "No lifetime resistor drift, connector fault or board thermal/EMC/isolation qualification is implied."]}


def validate(d,netlist=None,erc=None,ledger_path=None):
    errors=[];warnings=[];calc={}
    def check(ok,msg):
        if not ok:errors.append(msg)
    def finite(v):
        if isinstance(v,dict):
            for x in v.values():finite(x)
        elif isinstance(v,list):
            for x in v:finite(x)
        elif type(v) in (int,float):
            try:check(math.isfinite(v),"nonfinite numeric value")
            except OverflowError:errors.append("numeric value too large")
    finite(d)
    try:
        check(d["schema_version"]==1 and d["candidate"]=="baseline-6j-2enc","wrong schema or candidate")
        check(d["manufacturing_ready"] is False and d["physical_qualification"] is False,"unqualified circuit cannot claim release")
        check((d["channel_count"],d["home_count"],d["additional_count"],d["device_count"])==(22,6,16,11),"baseline capacity mismatch")
        ch=d["channels"];p=d["components"]
        check([c["id"] for c in ch]==[f"DI{i:02}" for i in range(22)],"channel IDs duplicate, missing or reordered")
        check([c["logic_net"] for c in ch]==LOGIC_NETS,"baseline logic assignment mismatch")
        check(d["logic_supply_v"]==[3.2,3.4],"logic supply envelope changed")
        check(tuple(d["interface"][k] for k in ("operating_min_v","operating_max_v","guaranteed_low_target_v","guaranteed_high_target_v"))==(0,30,5,15),"port voltage/threshold targets changed")
        check(d["source_spec"]==SPEC_LIMITS,"source specification differs from reviewed TI table")
        check(type(d["analysis"]["temperature_departure_k"]) in (int,float) and d["analysis"]["temperature_departure_k"]==100,"temperature screen changed")
        check(d["logic_ground"]=="LOGIC_GND" and d["field_ground"]=="FIELD_GND","ground domains changed")
        check(d["isolation"]["field_returns_common"] is True and d["isolation"]["channel_to_channel_claim"] is False,"common field return cannot claim channel isolation")
        check(d["isolation"]["pe_capacitor_fitted"] is False,"PE coupling requires whole-system review")
        check(d["output_default"]["brownout_or_unpowered"].startswith("undetermined"),"unpowered default must remain undetermined")
        check(d["analysis"]["threshold_corner_result_is_screen_only"] is True and d["analysis"]["filter_corner_result_is_end_to_end_delay"] is False,"screen misrepresented as qualified result")
        expected={*[f"U{i}" for i in range(1,12)],*[f"R{i+j}" for i in range(1,23) for j in (0,100,200)],*[f"C{i}" for i in range(1,23)],*[f"C{i}" for i in range(101,112)],"JDI0","JDI1","JDI2","JLOG1","JLOG2"}
        check(set(p)==expected,"component set mismatch")
        for pair in range(11):
            i=pair*2;ua=f"U{pair+1}";a=f"DI{i:02}";b=f"DI{i+1:02}"
            pins={"1":"LOGIC_GND","2":"IO_3V3","3":"IO_3V3","4":LOGIC_NETS[i],"5":LOGIC_NETS[i+1],"6":None,"7":None,"8":"LOGIC_GND","9":"FIELD_GND","10":b+"_IN","11":b+"_SENSE","12":b+"_SUB_ISLAND","13":a+"_SUB_ISLAND","14":"FIELD_GND","15":a+"_IN","16":a+"_SENSE"}
            check(p[ua]["mpn"]=="ISO1212DBQR" and p[ua]["pins"]==pins,ua+" exact pin/variant mismatch")
            cv=p[f"C{pair+101}"]
            check(cv["pins"]=={"1":"IO_3V3","2":"LOGIC_GND"} and cv["mpn"]=="06033C104JAT2A" and cv["capacitance_f"]==100e-9 and cv["voltage_rating_v"]>=25,"logic bypass mismatch "+ua)
        for i in range(22):
            cid=f"DI{i:02}";c=ch[i]
            check((c["component"],c["device_channel"],c["schematic_ref"],c["domain"])==(f"DI{i//2}",i%2+1,f"U{i//2+1}","FIELD"),cid+" device assignment mismatch")
            check((c["threshold_ref"],c["sense_ref"],c["filter_ref"],c["output_bias_ref"],c["substrate_net"])==(f"R{i+1}",f"R{i+101}",f"C{i+1}",f"R{i+201}",cid+"_SUB_ISLAND"),cid+" support reference mismatch")
            expected_term={"connector":f"JDI{i//8}","position":i%8+1,"net":cid+"_FIELD","domain":"FIELD"}
            check(c["terminal"]==expected_term,cid+" terminal mismatch")
            checks=[(f"R{i+1}","SMM02040C1001FB300",{"1":cid+"_FIELD","2":cid+"_SENSE"},1000,.01,50),
                    (f"R{i+101}","CRCW0603562RFKEA",{"1":cid+"_SENSE","2":cid+"_IN"},562,.01,100),
                    (f"R{i+201}","CRCW0603100KFKEA",{"1":LOGIC_NETS[i],"2":"LOGIC_GND"},100000,.01,100)]
            for ref,mpn,pins,value,tol,tcr in checks:
                r=p[ref]
                check(r["mpn"]==mpn and r["pins"]==pins,ref+" resistor connection/MPN mismatch")
                check(type(r["resistance_ohm"]) in (int,float) and (r["resistance_ohm"],r["tolerance"],r["tcr_ppm_k"])==(value,tol,tcr),ref+" resistor parameters mismatch")
                check(r["power_screen_w"] >= (.25 if ref==f"R{i+1}" else .1),ref+" resistor power inadequate")
                check(r["voltage_rating_v"] >= (200 if ref==f"R{i+1}" else 75),ref+" resistor voltage inadequate")
            cap=p[f"C{i+1}"]
            check(cap["mpn"]=="C2012C0G2A103J125AA" and cap["pins"]=={"1":cid+"_SENSE","2":"FIELD_GND"},cid+" filter connection/MPN mismatch")
            check((cap["capacitance_f"],cap["tolerance"],cap["tcr_ppm_k"],cap["voltage_rating_v"])==(10e-9,.05,30,100),cid+" filter parameters mismatch")
            island=cid+"_SUB_ISLAND"
            uses=[(ref,pin) for ref,x in p.items() for pin,n in x["pins"].items() if n==island]
            check(uses==[(f"U{i//2+1}",str(13 if i%2==0 else 12))],cid+" substrate must be its own single-pin island")
        for bank in range(3):
            pins={str(i+1):(f"DI{bank*8+i:02}_FIELD" if bank*8+i<22 else "FIELD_GND") for i in range(8)}
            check(p[f"JDI{bank}"]["pins"]==pins,f"JDI{bank} terminal pin mismatch")
        for ref,nets in (("JLOG1",["IO_3V3","LOGIC_GND"]+LOGIC_NETS[:12]),("JLOG2",["IO_3V3","LOGIC_GND"]+LOGIC_NETS[12:])):
            check(p[ref]["pins"]=={str(i+1):v for i,v in enumerate(nets)},ref+" boundary mismatch")
        if ledger_path is not None:
            data=Path(ledger_path).read_bytes();ledger=json.loads(data)
            check(hashlib.sha256(data).hexdigest()==d["ledger_sha256"],"frozen ledger hash mismatch")
            check(d["interface"]==next(x for x in ledger["interfaces"] if x["id"]=="digital_input"),"frozen interface mismatch")
            check(d["terminals"]==[t for t in ledger["terminals"] if t["connector"].startswith("JDI")],"frozen terminals mismatch")
        if not errors:
            calc=calculations(d)
            check(calc["rising_threshold_conservative_screen_max_v"]<d["interface"]["guaranteed_high_target_v"],"high target lacks threshold screen margin")
            check(calc["falling_threshold_intrinsic_screen_min_v"]>d["interface"]["guaranteed_low_target_v"],"low target lacks threshold screen margin")
            check(calc["rthreshold_dc_power_max_w"]<p["R1"]["power_screen_w"],"threshold resistor DC overload")
            check(calc["rsense_dc_power_max_w"]<p["R101"]["power_screen_w"],"sense resistor DC overload")
        if netlist is not None:
            exported=read_netlist(netlist)
            check(set(exported)==set(p),"exported component set mismatch")
            for ref,x in p.items():
                for key in ("value","mpn","footprint","pins"):
                    check(ref in exported and exported[ref][key]==x[key],ref+" exported "+key+" mismatch")
        if erc is not None:
            report=json.loads(Path(erc).read_text(encoding="utf-8"));records=expected_warning_records()
            actual=[v for sheet in report.get("sheets",[]) for v in sheet.get("violations",[])]
            check(report.get("source")=="digital_inputs.kicad_sch" and bool(report.get("sheets")),"ERC source/sheets mismatch")
            check(set(report.get("included_severities",[]))>={"warning","error"},"ERC severities suppressed")
            check(len(actual)==22,"ERC must retain exactly 22 substrate warnings")
            wanted={r["label_uuid"]:r for r in records};seen=[]
            for v in actual:
                item=v.get("items",[]);key=item[0].get("uuid") if len(item)==1 else None
                check(key in wanted and key not in seen,"unexpected/duplicate ERC warning identity")
                seen.append(key)
                if key in wanted:
                    r=wanted[key];check(v.get("severity")=="warning" and v.get("type")=="isolated_pin_label" and item[0].get("description")=="Label '"+r["net"]+"'","ERC violation is not the expected substrate case")
            check({x.get("key") for x in report.get("ignored_checks",[])} <= {"single_global_label","four_way_junction","simulation_model_issue","footprint_filter"},"ERC additional checks suppressed")
        warnings=["22 floating-substrate label warnings are expected and retained; no broad ERC suppression.","Output state during power loss/brownout is undetermined; input-valid masking is required outside this sheet.","0-30V sinking-input study only; neither universal voltage, AC nor NPN mode is qualified.","Field input currents, sensor leakage, cable/filter delay, full-board EMC and isolation require qualification.","Probe/toolsetter accuracy and cycle-start intent cannot be inferred from a raw input level."]
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError,OSError,ET.ParseError) as exc:errors.append("invalid design/evidence: "+str(exc))
    return {"ok":not errors,"errors":errors,"warnings":warnings,"calculations":calc,"manufacturing_ready":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--write",action="store_true");args=ap.parse_args()
    d=json.loads((OUT/"design.json").read_text(encoding="utf-8"));r=validate(d,OUT/"netlist.xml",OUT/"erc.json",OUT/"input-electrical-design.json")
    if args.write:
        (OUT/"validation.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
        (OUT/"expected-erc-warnings.json").write_text(json.dumps(expected_warning_records(),indent=2)+"\n",encoding="utf-8")
        if r["ok"]:
            with (OUT/"bom.csv").open("w",encoding="utf-8",newline="") as f:
                w=csv.writer(f);w.writerow(["reference","quantity","value","mpn","footprint","status"])
                for ref,x in read_netlist(OUT/"netlist.xml").items():w.writerow([ref,1,x["value"],x["mpn"],x["footprint"],"boundary only" if ref.startswith("J") else "proposed; not qualified"])
    print(json.dumps(r,indent=2));raise SystemExit(0 if r["ok"] else 1)


if __name__=="__main__":main()
