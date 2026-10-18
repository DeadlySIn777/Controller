import sys,json,shutil,math,collections,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"));import pcbnew
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_zone_motherboard_returns import rectangle,duplicate,inflation,split_polygons
from hardware_route_selected_additive import corridor_polygon
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_validate_return_bridge_sources import review
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_validate_motherboard_return_planes_r06 import validate
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition,sha_text
from hardware_stitch_owned_return_planes import definitions
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
base=Path("reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb");mp=Path("reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json");out=Path("reports/motherboard-return-zoning-20261001/source26-r74-C19042-coupled-source-cell-r01")
if out.exists():raise ValueError("Fresh immutable output required")
out.mkdir();(out/"inputs").mkdir();frozen={str(p):sha(p)for p in(base,mp,Path(__file__))}
for p in(base,mp,Path(__file__)):shutil.copy2(p,out/"inputs"/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets);fps={f.GetReference():f for f in b.GetFootprints()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};new=[];powernew=[];changed=[];ret="/motherboard_do/FIELD_B_0V";power="/motherboard_do/DOB_FIELD_3V3"
for pin in fps["C19042"].Pads():
 if any(t.GetNetname()==pin.GetNetname()and t.IsOnLayer(pcbnew.B_Cu)and(pin.HitTest(t.GetStart())or pin.HitTest(t.GetEnd()))for t in b.GetTracks()):raise ValueError("C19042 now has real attached old copper")
ids=["8afc32f4-2047-4ff3-bf87-aa7153d9627f","c9ad7bff-105f-4b2e-b8a7-94d9c78f2e84","0c5eaaf8-1041-4f68-a66c-19fad00520b1"]
for u in ids:
 if cu[u].GetNetname()!="/motherboard_safety_sensor/DI_SENSOR_AIN2":raise ValueError("Exact AIN2 Source net differs")
q=(124.6,172.9);cu[ids[0]].SetEnd(xy(q));cu[ids[1]].SetPosition(xy(q));cu[ids[2]].SetStart(xy(q));changed+=ids
f=fps["C19042"];f.Flip(f.GetPosition(),False);f.SetPosition(xy((125.75,172.25)));f.SetOrientationDegrees(0)
f=fps["C19037"];old=next(p for p in f.Pads()if p.GetNumber()=="2").GetPosition();f.SetPosition(xy((128,170.5)));after=next(p for p in f.Pads()if p.GetNumber()=="2").GetPosition()
for u in ["2c77f7c6-4286-46f9-a9b1-aa042be96c8f","79efbcbe-58a9-47ce-b3f1-e2cec8f6a14f"]:
 if cu[u].GetEnd()!=old or cu[u].GetNetname()!=ret:raise ValueError("Exact C19037 own Ground shared endpoint differs")
 cu[u].SetEnd(after);changed.append(u)
pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};cr=mm(pads["C19042","2"].GetPosition());cp=mm(pads["C19042","1"].GetPosition());groundvia=(127.625,172.25);positive=[(123.2,171.5),(124.975,171.5),(124.975,172.25)];groundpath=[cr,groundvia];in4=[groundvia,(127.625,174),(123.2,174),(123.2,173.05)]
g=Geometry(b)
if not g.clear(positive,power,pcbnew.F_Cu,.2)or not g.clear(groundpath,ret,pcbnew.F_Cu,.2)or not g.via(groundvia,ret)or not g.clear(in4,ret,pcbnew.In4_Cu,.2):raise ValueError("Bounded actual coupled-cell routes are obstructed")
def line(path,net,layer,group):
 for s,e in zip(path,path[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);new.append(t.m_Uuid.AsString());group.append(t.m_Uuid.AsString())
line(positive,power,pcbnew.F_Cu,powernew);groundnew=[];line(groundpath,ret,pcbnew.F_Cu,groundnew);line(in4,ret,pcbnew.In4_Cu,groundnew)
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(ret));v.SetPosition(xy(groundvia));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new.append(v.m_Uuid.AsString());groundnew.append(v.m_Uuid.AsString());vid=v.m_Uuid.AsString()
# Recompute every Source-side domain envelope after the two exact cap poses.
model=json.load(open("hardware/motherboard/design.json"));parts={r:c for r,c in model["components"].items()if c.get("physical",c.get("role")!="schematic_boundary_not_orderable")};nodes,nc,functions=native(Path("hardware/motherboard/netlist.xml"));domains,barriers,_,_=classify(parts,nodes,nc);mapping=dict(json.load(open(mp)),**positioned(b,parts,nodes,nc,functions,domains,barriers));write(out/"actual-coupled-source-domain-map-before-refill.json",mapping)
ext=pcbnew.SHAPE_POLY_SET()
for path in(positive,groundpath):
 for s,e in zip(path,path[1:]):ext.BooleanAdd(corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.5)))
guard=ReferenceGuard(b,mapping);foreign=[]
for other,shape in guard.indices[pcbnew.In1_Cu].candidates((122.7,171),(128.2,172.9),.5):
 if other!=ret and ext.Collide(shape):foreign.append(other)
if foreign:raise ValueError("Actual own ADC reference extension hits foreign Source projection "+str(foreign))
for z in b.Zones():
 if z.GetIsRuleArea()and z.IsOnLayer(pcbnew.In1_Cu)and z.GetDoNotAllowZoneFills()and ext.Collide(z.Outline()):raise ValueError("Actual ADC extension violates all-layer package/raw/SUB barrier")
# A single bounded higher-priority own-domain collar physically overlaps the
# retained Source FieldB plane; existing Source islands are never replaced.
owner=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==ret and z.GetLayer()==pcbnew.In1_Cu and z.Outline().Collide(ext));nz=owner.Duplicate();nz.Outline().RemoveAllContours();nz.Outline().Append(ext);nz.SetAssignedPriority(max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(pcbnew.In1_Cu))+1);nz.SetZoneName("ADC_C19042_OWN_FIELD_B_IN1_SOURCE_COLLAR");b.Add(nz);addedzones=[nz.m_Uuid.AsString()];cut=inflation(ext,.25);changedzones=[]
for z in list(b.Zones()):
 if z.GetIsRuleArea()or z.GetLayer()!=pcbnew.In1_Cu or z.GetNetname()!="/LOGIC_GND":continue
 hit=duplicate(z.Outline());hit.BooleanIntersection(cut)
 if not hit.Area():continue
 poly=duplicate(z.Outline());poly.BooleanSubtract(cut);pieces=sorted(split_polygons(poly),key=lambda p:p.Area(),reverse=True)
 if not pieces:raise ValueError("ADC own collar would erase a complete old LOGIC resource")
 changedzones.append(z.m_Uuid.AsString());z.Outline().RemoveAllContours();z.Outline().Append(pieces[0])
 for piece in pieces[1:]:
  frag=z.Duplicate();frag.Outline().RemoveAllContours();frag.Outline().Append(piece);b.Add(frag);addedzones.append(frag.m_Uuid.AsString())
dest=out/"motherboard-C19042-source-cell-candidate.kicad_pcb";pcbnew.SaveBoard(str(dest),b)
for suffix in(".kicad_pro",".kicad_dru"):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix==".pretty"or f.name=="3dmodels"):shutil.copytree(f,out/f.name)
 elif f.name=="fp-lib-table":shutil.copy2(f,out/f.name)
write(out/"generation.json",dict(input_sha256=frozen,exact_cap_pose_changes=["C19042","C19037"],exact_old_copper_endpoint_or_pose_changes=changed,new_Cu=new,new_zone_UUIDs=addedzones,existing_zone_outline_changes=changedzones,ADC_power_F_path=positive,ADC_ground_F_path=groundpath,source_bound_In4_ground_contact=in4,reference_guard_margin_mm=.4))
print("C19042 coupled cell native refill starts",flush=True);report=drc(dest,out,"native");b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()}
if set(actual)!=set(oldcu)|set(new)or any(identity(actual[u])!=i for u,i in oldcu.items()if u not in changed):raise ValueError("Unscoped old Cu changed")
if any(pad_identity(p)!=oldpads[p.m_Uuid.AsString()]for p in b.GetPads()if p.GetParentFootprint().GetReference()not in("C19042","C19037")):raise ValueError("Unscoped Source pads/poses changed")
after=native_pad_clusters(b,nets);survive=clusters_survive(before,after);write(out/"all-native-SOURCE-cluster-proof.json",dict(passed=survive,before=before,after=after))
if not survive:raise ValueError("Actual prior Source cluster split")
if any(r["severity"]=="error"for r in report["violations"])or report["ignored_checks"]:raise ValueError("Native errors or ignored checks remain")
mapping=dict(mapping,**positioned(b,parts,nodes,nc,functions,domains,barriers));mapping["actual_board_sha256"]=sha(dest);write(out/"domain-map.json",mapping)
pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};peers=lambda p:{q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)}
if pads["U19026","8"].m_Uuid.AsString()not in peers(pads["C19042","1"])or pads["U19026","3"].m_Uuid.AsString()not in peers(pads["C19042","2"]):raise ValueError("Real ADC owning supply or return path missing")
if not physical_reference_contact(actual[vid],pcbnew.In1_Cu,b.GetConnectivity()):raise ValueError("ADC ground annulus lacks actual Source-connected own In1")
proof=review(b,[dict(net=ret,new_copper_UUIDs=groundnew),dict(net=power,new_copper_UUIDs=powernew)],mapping["pads"]);write(out/"every-new-Cu-Source-proof.json",proof)
checker=NativeCollectedAnnulusCheck(b,{power:dict(return_net=ret,reference_layers={"F.Cu":"In1.Cu"},allow_vias=False,reference_corridor_margin_mm=.4)});strict=[checker.segment(actual[u],checker.rows[power])for u in powernew];write(out/"strict-point40-direct-F-ADC-supply-corridors.json",dict(passed=True,rows=strict,no_supply_vias=True,actual_owning_source_return_native=True))
rawdefs=definitions(dest);reviews=[dict(uuid=u,before_definition_sha256=sha_text(oldzones[u]),after_definition_sha256=sha_text(rawdefs[u]),electrical_outline_correction_reason="Two Source-preserving capacitor poses and the exact short direct-F ADC bypass need a tight own FIELD_B In1 reference collar. Only empty-space LOGIC outline overlap is removed; actual foreign Source metal, all-layer barriers and every old Source cluster remain.")for u in changedzones]
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];delta=[]
for kind in("segment","via","arc"):
 old,nw=[objects(tree,kind)for tree in trees];delta.extend(u for u in set(old)|set(nw)if u not in old or u not in nw or dump(old[u])!=dump(nw[u]))
write(out/"bounded-scope.json",dict(electrical_source_unchanged=True,reviewed_footprint_references=["C19042","C19037"],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=addedzones,reviewed_existing_zone_outline_deltas=reviews,reviewed_scope_reason="Real ADS1115 C19042 direct-F bypass and own Source return closure. Exactly two capacitors move; one already-private AIN2 barrel and its two endpoint leaves shift .4mm, and two existing C19037 Ground branches retain their far endpoints. Strict .40 ADC supply reference, native own Source grounds, all other Source clusters/copper/pads remain. No schematic/value/land/net changes or precision/current qualification claim."))
full=validate(b,mapping);full.update(board_sha256=sha(dest),source_map_sha256=sha(out/"domain-map.json"));write(out/"full-exact-literal-resource-review.json",full)
run=subprocess.run([sys.executable,"tools/motion_card_routing_inventory.py","--board",str(dest),"--netlist","hardware/motherboard/netlist.xml","--source-design","hardware/motherboard/design.json","--out",str(out/"independent-connectivity")],capture_output=True,text=True);(out/"independent-command.txt").write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError("Independent complete Source inventory failed")
ind=json.load(open(out/"independent-connectivity/review.json"));write(out/"receipt.json",dict(passed=True,before_board_sha256=sha(base),board_sha256=sha(dest),new_Cu=len(new),native_errors=0,native_DRC_types=dict(collections.Counter(v["type"]for v in report["violations"])),ignored_checks=[],actual_ADC_supply_and_return_owner_native_connected=True,ADC_ground_actual_Source_backed_In1_annulus=True,no_supply_vias=True,strict_point40_supply_reference_passed=True,all_prior_Source_clusters_preserved=True,uncapped_unconnected=ind["uncapped_unconnected_ratsnest_edges"],independent_missing=ind["independent_physical_cluster_missing_joins"],orphan_copper=ind["orphan_copper_items"],remaining_unanchored_resources=len(full["unanchored_components"]),scope_sha256=sha(out/"bounded-scope.json"),all97retained_loop_proof_pending=True,manufacturing_ready=False));print("Frozen C19042 donor ready for independent existing-loop checks",flush=True)
