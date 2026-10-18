from pathlib import Path
import sys,json,shutil,csv,subprocess,copy,hashlib,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path("tools").resolve()))
from hardware_build_assembly import parse,dump,child,children,value,q
from hardware_apply_motherboard_health_source import apply_health_source
from hardware_apply_motor_feed_reset import apply_feed_reset,feed_reset_screen,added_components
BASE=Path("hardware/motherboard");OUT=Path("reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r02");assert not OUT.exists();OUT.mkdir();dst=OUT/"motherboard";shutil.copytree(BASE,dst,ignore=shutil.ignore_patterns("*.kicad_pcb","*.kicad_prl","*.zip","*-backups","~*"))
model=json.loads((BASE/"design.json").read_text());orig=copy.deepcopy(model);trees={k:parse((BASE/(k+".kicad_sch")).read_text())for k in["mc_local_power","motherboard_power_entry"]};ht,hm,health=apply_health_source(trees,model);t,m,receipt=apply_feed_reset(ht,hm)
for k,tr in t.items():(dst/(k+".kicad_sch")).write_text(dump(tr)+"\n")
(dst/"design.json").write_text(json.dumps(m,indent=2)+"\n")
libdefs=[]
for d in children(child(t["motherboard_power_entry"],"lib_symbols"),"symbol"):
 if value(d[1]).startswith("CNC_MB_FeedReset:"):
  d=copy.deepcopy(d);d[1]=q(value(d[1]).split(":")[1]);libdefs.append(d)
(dst/"CNC_MB_FeedReset.kicad_sym").write_text(dump(["kicad_symbol_lib",["version","20241209"],["generator",q("motherboard_feed_reset")]]+libdefs)+"\n")
slt=parse((dst/"sym-lib-table").read_text());slt.append(parse('(lib(name "CNC_MB_FeedReset")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_FeedReset.kicad_sym")(options "")(descr "Actual receiving reset manufacturer pin contracts"))'));(dst/"sym-lib-table").write_text(dump(slt)+"\n")
with (dst/"bom.csv").open("w",encoding="utf8",newline="")as f:
 w=csv.writer(f);w.writerow(["Reference","Value","MPN","Footprint","Status","DNP","Scope"])
 for r,p in m["components"].items():w.writerow([r,p["value"],p.get("mpn",""),p.get("footprint",""),p.get("status","candidate_not_qualified"),str(bool(p.get("dnp",False))).lower(),"actual_on_motherboard_component_candidate"])
CLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
for args in[["sch","export","netlist","--format","kicadxml","-o",str(dst/"netlist.xml"),str(dst/"motherboard.kicad_sch")],["sch","erc","--format","json","--severity-all","-o",str(OUT/"erc.json"),str(dst/"motherboard.kicad_sch")]]:
 run=subprocess.run([CLI]+args,capture_output=True,text=True);assert run.returncode==0,(args,run.stdout,run.stderr)
def pin_nets(path):
 x=ET.parse(path);return{(v.get("ref"),v.get("pin")):n.get("name")for n in x.findall(".//nets/net")for v in n.findall("node")}
a=pin_nets(BASE/"netlist.xml");b=pin_nets(dst/"netlist.xml");changes={k:(v,b.get(k))for k,v in a.items()if b.get(k)!=v};assert changes=={("U11032","6"):("/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A","/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_A"),("U11034","6"):("/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B","/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B")},changes
newpins={k:v for k,v in b.items()if k not in a};assert set(k[0]for k in newpins)==set(added_components())
for r,p in added_components().items():
 for pin,net in p["pins"].items():
  if net is not None:
   expected="/LOGIC_GND"if net=="LOGIC_GND"else"/motherboard_power_entry/"+net
   assert b[r,pin]==expected,(r,pin,b[r,pin],expected)
erc=json.loads((OUT/"erc.json").read_text());v=[v for sh in erc.get("sheets",[])for v in sh.get("violations",[])];errors=[v for v in v if v["severity"]=="error"];assert not errors,errors
s=feed_reset_screen();assert s["healthy_old_CLR_node_screen_v"]>s["highest_schmitt_VTplus_discrete_screen_v"]and s["off_node_screen_v"]<s["lowest_steady_schmitt_VTminus_discrete_screen_v"]and s["source_min_ohm"]>=10000 and s["reset_sink_at_raw1V65_a"]<.0004 and s["reset_sink_at_raw5V25_a"]<.001 and s["fast_CLR_load_screen_a"]<100e-6
neg=[]
for ref,key,bad in[("U11032","pins",{**hm["components"]["U11032"]["pins"],"6":"MOTOR_FEED_CLEAR_N_B"}),("R11074","mpn","CRCW060310K0FKEA"),("U11034","footprint","Package_SO:TSSOP-8"),("U11034","mpn","SN74LVC2G74DCUR")]:
 mm=copy.deepcopy(hm);mm["components"][ref][key]=bad
 try:apply_feed_reset(ht,mm)
 except ValueError:neg.append(dict(ref=ref,field=key,rejected=True))
 else:raise AssertionError(("MUTATION_ACCEPTED",ref,key))
negative_screens=[dict(test="original1k reset pullup violates mandatory10k",rejected=feed_reset_screen(1000)["source_min_ohm"]<10000),dict(test="injected excessive off leakage prevents safe SchmittLOW",rejected=feed_reset_screen(off_leak=20e-6)["off_node_screen_v"]>=1.51)]
assert all(x["rejected"]for x in negative_screens)
receipt.update(source26_existing_health_correction=health,exact_existing_native_changes=[dict(ref=k[0],pin=k[1],old=v[0],new=v[1])for k,v in changes.items()],all_other_existing_pin_nets_unchanged=True,new_connected_native_pin_count=len(newpins),native_erc_errors=errors,native_erc_warnings=sum(x["severity"]=="warning"for x in v),static_conditional_screen=s,meaningful_source_negative_controls=neg,meaningful_electrical_negative_controls=negative_screens,actual_fitted_parts=m["physical_footprints"],candidate_only=True,manufacturing_ready=False)
(OUT/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
print("FEED_RESET_SOURCE_NATIVE",len(newpins),len(errors),receipt["native_erc_warnings"],s,flush=True)
