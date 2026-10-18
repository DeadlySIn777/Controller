"""Independent exact-net, part, footprint and analytical checks for logic rails."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/logic_power"
RAILS = (("CORE_1V2",1.2,.8,"fpga_core",1.17,1.23),
         ("IO_3V3",3.3,.4,"fpga_io_rx_isolators",3.2,3.4),
         ("ESP_3V3",3.3,.7,"esp_peak",3.2,3.4))


def validate(tree, design, model, footprints=None):
    errors=[]
    inputs=[row for row in design["rails"] if row["id"]=="CORE_5V"]
    if len(inputs)!=1 or (inputs[0]["nominal_v"],inputs[0]["min_v"],inputs[0]["max_v"])!=(5,4.85,5.15):
        errors.append("Frozen CORE_5V input envelope changed")
    expected=defaultdict(set)
    def wire(net,*nodes):
        expected[net].update((ref,str(pin)) for ref,pin in nodes)
    boundary={"JIN1":["CORE_5V","LOGIC_GND"],
              "JOUT1":["CORE_1V2","LOGIC_GND","IO_3V3","LOGIC_GND","ESP_3V3","LOGIC_GND"],
              "JCTRL1":["CORE_1V2_EN","CORE_1V2_PG_OD","LOGIC_GND","IO_3V3_EN","IO_3V3_PG_OD","LOGIC_GND","ESP_3V3_EN","ESP_3V3_PG_OD","LOGIC_GND"]}
    for ref,nets in boundary.items():
        for pin,net in enumerate(nets,1):wire(net,(ref,pin))
    wanted={}
    def part(ref,value,footprint,mpn):
        wanted[ref]={"value":value,"mpn":mpn,"footprint":footprint}
    for i,(rail,voltage,current,load,vlow,vhigh) in enumerate(RAILS):
        u=f"U{i+1}";r=i*4;c=i*3
        part(u,"TPS62901RPJR","CNC_Power:TPS62901_RPJ9","TPS62901RPJR")
        part(f"L{i+1}","2.2uH","CNC_Power:XGL4020","XGL4020-222MEC")
        # Independent RPJ9 physical pin table; pin 9 is not an exposed ground pad.
        wire(rail+"_PG_OD",(u,1))
        wire(rail+"_SW",(u,2),(f"L{i+1}",1))
        wire(rail,(u,3),(f"L{i+1}",2),(f"C{c+2}",1),(f"R{r+3}",1))
        wire("LOGIC_GND",(u,4),(f"C{c+1}",2),(f"C{c+2}",2),(f"C{c+3}",2),
             (f"R{r+1}",2),(f"R{r+2}",2),(f"R{r+3}",2))
        wire(rail+"_EN",(u,5),(f"R{r+2}",1))
        wire("CORE_5V",(u,6),(f"C{c+1}",1))
        wire(rail+"_MODE",(u,7),(f"R{r+1}",1))
        wire(rail+"_SS",(u,8),(f"C{c+3}",1))
        if i:
            wire(rail+"_VSET",(u,9),(f"R{r+4}",1));wire("LOGIC_GND",(f"R{r+4}",2))
            part(f"R{r+4}","301k 1%","Resistor_SMD:R_0603_1608Metric","CRCW0603301KFKEA")
        else:wire("LOGIC_GND",(u,9))
        for j,value,mpn in ((1,"76.8k 1%","CRCW060376K8FKEA"),(2,"10k 1%","CRCW060310K0FKEA"),(3,"100k 1%","CRCW0603100KFKEA")):
            part(f"R{r+j}",value,"Resistor_SMD:R_0603_1608Metric",mpn)
        for j,value,fp,mpn in ((1,"10uF 25V X7R","Capacitor_SMD:C_1206_3216Metric","C3216X7R1E106K160AB"),
                               (2,"22uF 10V X7S","Capacitor_SMD:C_0805_2012Metric","C2012X7S1A226M125AC"),
                               (3,"6.8nF 50V C0G","Capacitor_SMD:C_0603_1608Metric","GRM1885C1H682JA01D")):
            part(f"C{c+j}",value,fp,mpn)
        rows=[row for row in design["rails"] if row["id"]==rail]
        loads=[row for row in design["power_loads"] if row["id"]==load]
        if len(rows)!=1 or (rows[0]["nominal_v"],rows[0]["min_v"],rows[0]["max_v"],rows[0]["capacity_a"])!=(voltage,vlow,vhigh,1):
            errors.append(f"Frozen ledger voltage/capacity changed: {rail}")
        if len(loads)!=1 or (loads[0]["rail"],loads[0]["budget_a"])!=(rail,current):
            errors.append(f"Frozen ledger load changed: {load}")
    for ref,value in (("JIN1","5V INPUT"),("JOUT1","LOGIC RAILS"),("JCTRL1","EXTERNAL SEQUENCER")):
        part(ref,value,"","")
    actual,seen={},set()
    for net in tree.findall(".//nets/net"):
        name=net.attrib["name"].lstrip("/")
        if name in actual:errors.append(f"Duplicate net {name}")
        actual[name]=set()
        for node in net.findall("node"):
            item=(node.attrib["ref"],node.attrib["pin"])
            if item in seen:errors.append(f"Repeated pin {item}")
            seen.add(item);actual[name].add(item)
    for net in sorted(set(actual)|set(expected)):
        if actual.get(net,set())!=expected.get(net,set()):
            errors.append(f"Net {net}: missing={sorted(expected.get(net,set())-actual.get(net,set()))}; extra={sorted(actual.get(net,set())-expected.get(net,set()))}")
    comps=tree.findall(".//components/comp")
    if len(comps)!=len(wanted) or {c.attrib["ref"] for c in comps}!=set(wanted):errors.append("Unexpected or missing fitted component")
    for comp in comps:
        ref=comp.attrib["ref"]
        values={"value":comp.findtext("value"),"footprint":comp.findtext("footprint") or "", "mpn":comp.findtext("./fields/field[@name='MPN']") or ""}
        if values!=wanted.get(ref):errors.append(f"Wrong value/MPN/package: {ref}")
        if any(p.attrib.get("name","").lower()=="dnp" for p in comp.findall("property")):errors.append(f"Required part marked DNP: {ref}")
    libpins=tree.findall(".//libpart[@part='TPS62901RPJR']/pins/pin")
    expectedpins={"1":("PG","open_collector"),"2":("SW","power_out"),"3":("VOS","input"),"4":("GND","power_in"),
                  "5":("EN","input"),"6":("VIN","power_in"),"7":("MODE/S-CONF","input"),"8":("SS/TR","input"),"9":("FB/VSET","input")}
    if len(libpins)!=9 or {p.attrib["num"]:(p.attrib["name"],p.attrib["type"]) for p in libpins}!=expectedpins:errors.append("RPJ9 pin functions/types differ")
    checks={"schema_version":1,"manufacturing_ready":False,"candidate_mpn":"TPS62901RPJR","replaces_study_candidate":"TPS62160DSGR",
            "pin_map":{p:v[0] for p,v in expectedpins.items()},"boundary":boundary,"components":wanted,"input_min_v":4.85,"input_max_v":5.15,
            "mode":{"setting":14,"resistor_ohm":76800,"frequency_hz_nominal":1000000,"forced_pwm":True,"vset":True,"discharge_selected":True},
            "boundaries":{"complete_fpga_sequence":False,"pg_is_machine_permission":False,"external_pg_pullups_required":True,"pg_valid_below_vin_1v8":False,
                          "discharge_guaranteed_without_input":False,"discharge_requires_previous_enable":True,"thermal_auto_restart":True,"independent_esp_input_isolation":False,"physical_qualification":False},
            "magnetics":{"inductance_uh":2.2,"initial_tolerance":.2,"dc_inductance_drop_allowance":.2,"effective_l_model_min_uh":1.408,
                         "dcr_max_ohm_at_25c":.0215,"isat_20pct_drop_a_at_25c":4.4,"frequency_lower_bound_qualified":False},
            "capacitors":{"input_nominal_uf":10,"input_effective_min_required_uf":3,"output_nominal_uf":22,"output_effective_min_required_uf":6,
                          "output_effective_max_allowed_uf":50,"output_local_max_uf_tolerance_temperature":32.208,"external_load_capacitance_qualified":False,"dc_bias_temperature_aging_qualified":False}}
    for key,target in checks.items():
        if model.get(key)!=target:errors.append(f"Unreviewed model change: {key}")
    ss=model.get("soft_start",{})
    fixed={"capacitance_pf":6800,"tolerance":.05,"tcr_ppm_per_k":30,"excursion_k":150,"k_us_conservative_graph_bound":700,
           "includes_datasheet_min_max_equations":True,"includes_loaded_ramp_or_startup_delay":False,"physically_qualified":False}
    if any(ss.get(k)!=v for k,v in fixed.items()):errors.append("Soft-start assumptions changed")
    def numerical(value,target,label):
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value-target)>1e-8:errors.append(f"Calculation mismatch: {label}")
    vref_min=(.6*.9875-.008)/.75;vref_max=(.6*1.0125+.008)/.75
    tss_min=6800*.95*.9955/2.7*vref_min-700;tss_max=6800*1.05*1.0045/2.3*vref_max+160
    for key,value in (("nominal_us",6800/2.5*.8+55),("model_min_us",tss_min),("model_max_us",tss_max),
                      ("reference_min_v_model",vref_min),("reference_max_v_model",vref_max)):
        numerical(ss.get(key),value,key)
    if len(model.get("rails",[]))!=3:errors.append("Three separate rail models required")
    for index,(rail,voltage,current,load,minimum,maximum) in enumerate(RAILS):
        rows=[r for r in model.get("rails",[]) if r.get("rail")==rail]
        if len(rows)!=1:errors.append(f"Missing/duplicate model {rail}");continue
        row=rows[0]
        for key,value in (("regulator",f"U{index+1}"),("ledger_load_id",load),("regulation_includes_transient_or_layout",False)):
            if row.get(key)!=value:errors.append(f"Wrong rail assumption: {rail}.{key}")
        vmax=voltage*1.0125;vmin=voltage*.9875
        values={"output_nominal_v":voltage,"load_a":current,"regulation_only_min_v":vmin,"regulation_only_max_v":vmax,
                "input_a_at_85pct_efficiency_plus_50ma":current*vmax/(4.85*.85)+.05,
                "normal_ripple_a_at_nominal_frequency":vmax*(1-vmax/5.15)/(1.408e-6*1e6),
                "startup_local_cap_current_a_model":32.208e-6*vmax/tss_min*1e6}
        for key,value in values.items():numerical(row.get(key),value,rail+"."+key)
        if vmin<minimum or vmax>maximum:errors.append(f"Static regulation exceeds frozen rail window: {rail}")
        if current+values["startup_local_cap_current_a_model"]>=1:errors.append(f"Local startup current model exceeds 1 A: {rail}")
    if footprints is not None:
        expectedpads={"TPS62901_RPJ9": {"1":(-.625,-.25,.65,.2),"2":(-.625,.25,.65,.2),"3":(-.625,.75,.65,.2),
                        "4":(.45,.75,1,.2),"5":(.625,.25,.65,.2),"6":(.45,-.25,1,.2),"7":(.5,-.925,.25,.55),"8":(0,-.925,.25,.55),"9":(-.5,-.925,.25,.55)},
                      "XGL4020":{"1":(-1.185,0,.98,3.4),"2":(1.185,0,.98,3.4)}}
        for name,target in expectedpads.items():
            pads=re.findall(r'\(pad "(\d+)" smd roundrect \(at ([^ ]+) ([^)]+)\) \(size ([^ ]+) ([^)]+)\)',footprints.get(name,""))
            try:actualpads={p[0]:tuple(float(v) for v in p[1:]) for p in pads}
            except ValueError:actualpads={}
            if len(pads)!=len(target) or actualpads!=target:errors.append(f"Manufacturer copper pad map differs: {name}")
    return errors


def main():
    frozen=OUT/"input-electrical-design.json"
    design=json.loads(frozen.read_text(encoding="utf-8"));model=json.loads((OUT/"design-envelope.json").read_text(encoding="utf-8"))
    tree=ET.parse(OUT/"netlist.xml")
    footprints={p.stem:p.read_text(encoding="utf-8") for p in (OUT/"CNC_Power.pretty").glob("*.kicad_mod")}
    errors=validate(tree,design,model,footprints)
    if model["source_ledger_sha256"]!=hashlib.sha256(frozen.read_bytes()).hexdigest():errors.append("Frozen ledger changed after generation")
    erc=json.loads((OUT/"erc.json").read_text(encoding="utf-8"));violations=[v for s in erc["sheets"] for v in s["violations"]]
    if violations:errors.append(f"ERC contains {len(violations)} violations")
    paths=[ROOT/p for p in ("tools/hardware_build_tx_schematic.py","tools/hardware_build_logic_power.py","tools/hardware_validate_logic_power.py","tests/test_logic_power.py","reports/LOGIC_POWER.md")]
    paths += [p for p in OUT.rglob("*") if p.is_file() and p.name!="validation.json"]
    paths += [p for p in (ROOT/"research/logic-power").rglob("*") if p.is_file()]
    result={"schema_version":1,"scope":"three low-voltage regulators; external sequencing required","consistency_pass":not errors,"manufacturing_ready":False,
            "errors":errors,"component_count":len(tree.findall('.//components/comp')),"net_count":len(tree.findall('.//nets/net')),
            "kicad_version":erc["kicad_version"],"erc_violations":len(violations),"erc_ignored_checks":erc["ignored_checks"],
            "source_sha256":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
            "boundary":"ERC, exact connectivity, manufacturer pad coordinates and bounded models; no board DRC, transient/thermal test or completed sequencing"}
    (OUT/"validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"Logic power: {'PASS' if not errors else 'FAIL'}; {len(errors)} issues; manufacturing blocked")
    for error in errors:print(error)
    return bool(errors)


if __name__=="__main__":sys.exit(main())
