"""Check the field buck's proposed topology and bounded screens, not physical safety."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/field_power"
U1_PINS = {"1":"FIELD_VCC","2":"FIELD_5V_PGOOD","3":"F_PGOOD","4":"FIELD_24V_PROTECTED",
           "5":"FIELD_SW","6":"FIELD_BOOT","7":"FIELD_VCC","8":"FIELD_5V","9":"FIELD_GND"}
PAIR_PINS = {**{f"C{i}":("FIELD_24V_PROTECTED","FIELD_GND") for i in range(1,6)},
             "C6":("FIELD_BOOT","FIELD_SW"),"C7":("FIELD_VCC","FIELD_GND"),
             **{f"C{i}":("FIELD_5V","FIELD_GND") for i in (8,9,10)},
             "L1":("FIELD_SW","FIELD_5V"),"R1":("FIELD_24V_PROTECTED","F_PGOOD"),
             "R2":("F_PGOOD","FIELD_GND"),"R3":("FIELD_5V","FIELD_5V_PGOOD"),"R4":("FIELD_5V","FIELD_GND")}
BOUNDARIES = {"J1":{"1":"FIELD_24V_PROTECTED","2":"FIELD_GND","3":"F_PGOOD","4":"FIELD_GND"},
              "J2":{"1":"FIELD_5V","2":"FIELD_GND","3":"FIELD_5V_PGOOD","4":"FIELD_GND"}}
MPNS = {"U1":"LMR36506R5RPER","L1":"LPS6235-223MRC",**{f"C{i}":"CGA5L3X7S2A225K160AB" for i in range(1,5)},
        "C5":"GRM188R72A104KA35D","C6":"GCM155R71C104KA55D","C7":"885012206052",
        "C8":"GCM31CR71A226KE02L","C9":"GCM31CR71A226KE02L","C10":"GCM155R71C104KA55D",
        "R1":"CRCW0603100KFKEA","R2":"CRCW060310K0FKEA","R3":"CRCW060310K0FKEA","R4":"CRCW0603100KFKEA","J1":"","J2":""}


def read_netlist(path):
    tree = ET.parse(path).getroot()
    parts = {}
    for part in tree.findall("components/comp"):
        ref = part.attrib["ref"]
        if ref in parts: raise ValueError("duplicate exported reference: "+ref)
        fields = {f.attrib["name"]:f.text or "" for f in part.findall("fields/field")}
        parts[ref] = {"value":part.findtext("value", ""),"mpn":fields.get("MPN",""),
                      "footprint":part.findtext("footprint",""),"pins":{}}
    for net in tree.findall("nets/net"):
        name = net.attrib["name"].removeprefix("/")
        for node in net.findall("node"):
            ref,pin = node.attrib["ref"],node.attrib["pin"]
            if ref.startswith("#"): continue
            if ref not in parts: raise ValueError("unknown netlist reference: "+ref)
            if pin in parts[ref]["pins"]: raise ValueError("duplicate exported pin: "+ref+"."+pin)
            parts[ref]["pins"][pin] = name
    return parts


def bounded_calculations(d):
    p=d["components"]
    def r_corners(ref):
        part=p[ref]; t=part["tolerance"]; dt=part["tcr_ppm_k"]*1e-6*d["resistor_temperature_departure_k"]
        return (part["resistance_ohm"]*(1-t)*(1-dt),part["resistance_ohm"]*(1+t)*(1+dt))
    rtop,rbot = r_corners("R1"),r_corners("R2")
    leak=d["entry_pg_leakage_abs_a"]+d["buck_en_leakage_assumed_abs_a"]
    enable=[]; off=[]; current=[]; diss=[]
    for vin,rt,rb,il in itertools.product(d["input_local_v"],rtop,rbot,(-leak,leak)):
        enable.append((vin/rt-il)/(1/rt+1/rb))
    for vin,rt,rb,il in itertools.product([d["input_surge_screen_v"]],rtop,rbot,(-d["buck_en_leakage_assumed_abs_a"],d["buck_en_leakage_assumed_abs_a"])):
        v=(vin/rt-il)/(1/rt+1/rb+1/d["entry_pg_max_rdson_ohm"])
        off.append(v);current.append(v/d["entry_pg_max_rdson_ohm"]);diss.append((vin-v)**2/rt)
    surge=max((d["input_surge_screen_v"]/rt+leak)/(1/rt+1/rb) for rt,rb in itertools.product(rtop,rbot))
    def cmax(ref):
        c=p[ref];return c["capacitance_f"]*(1+c["tolerance"])*(1+c["temp_change"])
    cinmax=sum(cmax(f"C{i}") for i in range(1,6));coutmax=sum(cmax(f"C{i}") for i in (8,9,10))
    lmin=p["L1"]["inductance_h"]*(1-p["L1"]["tolerance"])
    lmax=p["L1"]["inductance_h"]*(1+p["L1"]["tolerance"])
    ripple=[vo*(1-vo/vi)/(l*f) for vi,vo,l,f in itertools.product(d["input_local_v"],d["output_target_v"],(lmin,lmax),d["switching_hz"])]
    bleeder_max=max(r_corners("R4"));vmax=max(d["output_target_v"])
    localmax=vmax/min(r_corners("R3"))+vmax/min(r_corners("R4"))
    powmax=vmax*(d["external_capacity_target_a"]+localmax)
    return {"en_released_normal_v":[min(enable),max(enable)],"en_released_surge_screen_max_v":surge,
            "en_asserted_surge_screen_max_v":max(off),"entry_pg_sink_screen_max_a":max(current),
            "r1_surge_screen_max_w":max(diss),"minimum_l_guideline_h":1.5*vmax/min(d["switching_hz"]),
            "selected_l_min_h":lmin,"ccm_ripple_screen_a":[min(ripple),max(ripple)],
            "ccm_peak_at_100ma_screen_a":d["external_capacity_target_a"]+max(ripple)/2,
            "input_cap_max_no_bias_f":cinmax,"output_cap_max_no_bias_f":coutmax,
            "input_charge_at_entry_max_ramp_a":cinmax*d["entry_ramp_max_v_s"],
            "output_charge_equivalent_average_a":coutmax*.9*vmax/.00195,
            "local_pg_pullup_and_bleed_max_a":localmax,"output_power_screen_max_w":powmax,
            "input_power_if_70pct_efficiency_w":powmax/.7,"loss_if_70pct_efficiency_w":powmax*(1/.7-1),
            "input_current_if_70pct_efficiency_at_18v_a":powmax/.7/min(d["input_local_v"]),
            "enable_divider_normal_max_a":max(d["input_local_v"])/(min(rtop)+min(rbot)),
            "ideal_unpowered_bleed_to_1v_s":coutmax*bleeder_max*math.log(vmax),
            "limitations":["Resistor corner model: initial tolerance times TCR over +/-100K; long-term drift unbounded.",
                           "EN leakage limit is specified at 3.3V; using it over divider range is an assumption.",
                           "60V is only a voltage stress screen; no surge waveform/clamp/energy qualification.",
                           "CCM ripple does not predict 100mA PFM/DCM waveform, burst ripple or actual current limit.",
                           "Capacitance maxima combine positive initial and temperature tolerances; DC-bias/aging minima remain open.",
                           "Charge current is an equivalent average for a linear ramp, not a switch-current peak bound.",
                           "70% efficiency is a budgeting assumption, not a measured or guaranteed minimum; add EN divider input current separately.",
                           "Bleed estimate assumes no external source and no other loads, not a safe-off deadline."]}


def validate(d, netlist=None, erc=None, evidence_dir=None):
    errors=[]; warnings=[]; calc={}
    def need(condition,message):
        if not condition:errors.append(message)
    def numbers(value,path="design"):
        if isinstance(value,dict):
            for k,v in value.items():numbers(v,path+"."+k)
        elif isinstance(value,list):
            for i,v in enumerate(value):numbers(v,path+f"[{i}]")
        elif isinstance(value,(int,float)) and not isinstance(value,bool):
            try:need(math.isfinite(value),path+" is not finite")
            except OverflowError:errors.append(path+" is too large")
    numbers(d)
    if errors:return {"ok":False,"errors":errors,"warnings":warnings,"calculations":calc,"manufacturing_ready":False}
    try:
        need(d["schema_version"]==1,"unsupported schema")
        need(d["manufacturing_ready"] is False and d["physical_qualification"] is False,"qualification status must remain false")
        need(d["effective_capacitance_verified"] is False and d["full_output_accuracy_verified"] is False,"unclosed qualification gate marked verified")
        need(d["ground_domain"]=="FIELD_GND","ground domain mismatch")
        need(d["input_local_v"]==[18,30] and d["output_target_v"]==[4.85,5.15],"voltage envelope changed without review")
        need(type(d["external_capacity_target_a"]) in (int,float) and d["external_capacity_target_a"]==.1,"external load target must remain 100mA")
        need(d["baseline_reserved_load_a"]==.05,"baseline load reservation changed")
        need(d["switching_hz"]==[930000,1050000],"frequency corners must match RT to VCC selection")
        p=d["components"]
        need(set(p)==set(MPNS),"component set differs from reviewed circuit")
        for ref,mpn in MPNS.items():
            need(p[ref]["mpn"]==mpn,ref+" MPN differs from reviewed variant")
            need(p[ref]["status"]=="proposed_not_qualified",ref+" status changed")
        need(p["U1"]["pins"]==U1_PINS,"U1 exact pin-to-net map differs from TI fixed-5V map")
        for ref,pair in PAIR_PINS.items():
            need(p[ref]["pins"]==dict(zip(("1","2"),pair)),ref+" connection mismatch")
        for ref,pins in BOUNDARIES.items():need(p[ref]["pins"]==pins,ref+" boundary mismatch")
        allnets={n for part in p.values() for n in part["pins"].values()}
        need(allnets==set(U1_PINS.values()),"unexpected rail or ground in FIELD domain")
        for ref in ("R1","R2","R3","R4"):
            for k in ("resistance_ohm","tolerance","tcr_ppm_k","working_voltage_v","power_70c_w"):
                need(type(p[ref][k]) in (int,float) and p[ref][k]>0,ref+" invalid "+k)
            need(p[ref]["tolerance"]<=.01 and p[ref]["tcr_ppm_k"]<=100,ref+" resistor drift exceeds model")
            need(p[ref]["working_voltage_v"]>=60 and p[ref]["power_70c_w"]>=.1,ref+" rating below screen")
        # MPN numeric attributes are fixed; substitutions require primary-source review.
        for i in range(1,11):
            ref=f"C{i}"; c=p[ref]
            expected_c=2.2e-6 if i<=4 else 22e-6 if i in (8,9) else 1e-6 if i==7 else .1e-6
            need(type(c["capacitance_f"]) in (int,float) and c["capacitance_f"]==expected_c,ref+" capacitance inconsistent with MPN")
            need(c["voltage_v"] >= (100 if i<=5 else 10 if i in (8,9) else 16),ref+" voltage rating insufficient")
            need(c["tolerance"]==.1 and c["temp_change"]==(.22 if i<=4 else .15),ref+" capacitor corner model mismatch")
        need(p["L1"]["inductance_h"]==22e-6 and p["L1"]["tolerance"]==.2,"inductor value differs from reviewed MPN")
        need(p["L1"]["isat_10pct_25c_a"]>=d["high_side_fault_current_reference_a"],"inductor 25C saturation margin below fault reference")
        if errors:return {"ok":False,"errors":errors,"warnings":warnings,"calculations":calc,"manufacturing_ready":False}
        calc=bounded_calculations(d)
        need(calc["en_released_normal_v"][0]>d["en_rising_max_v"],"EN lacks startup threshold margin")
        need(calc["en_asserted_surge_screen_max_v"]<d["en_falling_min_screen_v"],"PG sink does not hold EN below off threshold")
        need(calc["en_released_surge_screen_max_v"]<60,"entry PGOOD node over rating")
        need(calc["r1_surge_screen_max_w"]<p["R1"]["power_70c_w"],"R1 dissipation above declared screen")
        need(calc["selected_l_min_h"]>calc["minimum_l_guideline_h"],"inductance below minimum guideline")
        need(calc["ccm_ripple_screen_a"][0]>.06,"inductor too large for 10% ripple guideline")
        need(calc["local_pg_pullup_and_bleed_max_a"]+d["external_capacity_target_a"]<.6,"load exceeds device nominal current")
        if netlist is not None:
            exported=read_netlist(netlist)
            need(set(exported)==set(p),"exported component set mismatch")
            for ref,part in p.items():
                if ref not in exported:continue
                for field in ("mpn","value","footprint","pins"):
                    need(exported[ref][field]==part[field],ref+" exported "+field+" differs")
        if erc is not None:
            report=json.loads(Path(erc).read_text(encoding="utf-8"))
            need(report.get("source")=="field_power.kicad_sch","ERC source mismatch")
            need(set(report.get("included_severities",[])) >= {"error","warning"},"ERC omitted severities")
            need(bool(report.get("sheets")),"ERC has no sheets")
            need(not any(s.get("violations") for s in report.get("sheets",[])),"ERC violations present")
            default_ignored={"single_global_label","four_way_junction","simulation_model_issue","footprint_filter"}
            need({x.get("key") for x in report.get("ignored_checks",[])} <= default_ignored,"ERC additional checks suppressed")
        if evidence_dir is not None:
            for filename,digest in d["frozen_inputs"].items():
                need(hashlib.sha256((Path(evidence_dir)/filename).read_bytes()).hexdigest()==digest,"frozen input hash mismatch: "+filename)
        warnings += ["Review circuit passes bounded checks only; physical qualification is false.",
                     "U1 RPE9 and L1 footprints are not assigned; board layout/release blocked.",
                     "Effective input/output capacitance and 4.85-5.15V PFM accuracy remain unverified.",
                     "Entry R29 must be removed; F_PGOOD is an analog power-control net, not GPIO.",
                     "Unpowered entry PGOOD may release with retained FIELD input; startup is not a safety interlock.",
                     "Negative input, retained-output reverse current, all field loads and holdoff remain system gates."]
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError,OSError,ET.ParseError) as exc:
        errors.append("invalid design/evidence: "+str(exc))
    return {"ok":not errors,"errors":errors,"warnings":warnings,"calculations":calc,"manufacturing_ready":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true",help="Write review checks and BOM from exported netlist")
    args=parser.parse_args()
    d=json.loads((OUT/"design.json").read_text(encoding="utf-8"))
    result=validate(d,OUT/"netlist.xml",OUT/"erc.json",OUT)
    if args.write:
        (OUT/"validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        if result["ok"]:
            rows=read_netlist(OUT/"netlist.xml")
            with (OUT/"bom.csv").open("w",encoding="utf-8",newline="") as f:
                writer=csv.writer(f);writer.writerow(["reference","quantity","value","mpn","footprint","status"])
                for ref,p in rows.items():writer.writerow([ref,1,p["value"],p["mpn"],p["footprint"],"boundary only" if ref.startswith("J") else "proposed; not qualified"])
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
