"""Necessary U25 local bypass barrel correction, exact native UUID ledger.

The old cap Ground drill intersects fitted C80.2 SMD metal. The old positive
barrel also shadows both true U25 health-source output-pad reference collars.
Only the two low-current conventional barrels and exact attached endpoints
move. No Source, manufacturer land, pose, rated array or older zone changes.
"""
from pathlib import Path
import sys,json,shutil
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_stitch_owned_return_planes import definitions
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import functional_barrier,split_polygons
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r01');assert not O.exists();O.mkdir();assert sha(B)=='7759cccdb7583e3f195fc89967c73ff6f9e6840b09c76a3cdd405116382332a8'
S=Path('hardware/motherboard');inputs={str(q):sha(q)for q in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),S/'design.json',S/'netlist.xml',Path(__file__)]};assert sha(S/'design.json')=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets);changes=[]
spec=[('0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3',(332.5875,191.),(333.,190.5),'/motherboard_power_entry/FIELD_5V'),('9557a691-472b-4af0-87c3-b0e91cf52409',(333.4375,191.),(333.84,190.7),'/motherboard_motors/FIELD_GND')]
for uid,old,new,net in spec:
 v=cu[uid];assert v.Type()==pcbnew.PCB_VIA_T and mm(v.GetPosition())==old and v.GetNetname()==net;v.SetPosition(xy(new));v.SetIsFree(True);changes.append(uid)
 for t in cu.values():
  if t.Type()!=pcbnew.PCB_TRACE_T:continue
  moved=False
  if tuple(t.GetStart())==tuple(xy(old)):assert t.GetNetname()==net;t.SetStart(xy(new));moved=True
  if tuple(t.GetEnd())==tuple(xy(old)):assert t.GetNetname()==net;t.SetEnd(xy(new));moved=True
  if moved:changes.append(t.m_Uuid.AsString())
assert len(changes)==len(set(changes))
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];guard=ReferenceGuard(b,mp);ret='/motherboard_motors/FIELD_GND';shapes={};screen=[]
def add(label,layer,shape):
 bb=shape.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];hits=[]
 for other,project in guard.indices[layer].candidates(tuple(bounds[:2]),tuple(bounds[2:]),.3):
  if other==ret:continue
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(project)
  if hit.OutlineCount():hits.append(dict(foreign=other,exact_intersection=hit.Format(False)))
 for br in mp['barriers']:
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(functional_barrier(br))
  if hit.OutlineCount():hits.append(dict(barrier=br['reference'],exact_intersection=hit.Format(False)))
 screen.append(dict(role=label,layer=b.GetLayerName(layer),bounds_mm=bounds,exact_envelope=shape.Format(False),conflicts=hits));shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(shape)
for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):
 add('moved_actual_positive_annulus',l,corridor_polygon(tuple(xy((333.,190.5))),tuple(xy((333.,190.5))),pcbnew.FromMM(.82)))
 add('moved_actual_Ground_annulus',l,corridor_polygon(tuple(xy((333.84,190.7))),tuple(xy((333.84,190.7))),pcbnew.FromMM(.35)))
 add('actual_Source_join_to_existing_same_field_resource',l,corridor_polygon(tuple(xy((333.4375,191.))),tuple(xy((333.84,190.7))),pcbnew.FromMM(.25)))
for uid in changes:
 t=cu[uid]
 if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname()=='/motherboard_power_entry/FIELD_5V':add('exact_moved_own_positive_leaf',pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.20)))
write(O/'actual-Source-projection-screen.json',dict(passed=not any(r['conflicts']for r in screen),rows=screen));assert not any(r['conflicts']for r in screen)
newzones=[]
for l,shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for br in mp['barriers']:blocked.Append(functional_barrier(br))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(l)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify();tpl=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==ret and z.IsOnLayer(l));priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(l))+1
 for i,piece in enumerate(split_polygons(shape)):
  z=tpl.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority);z.SetZoneName('U25_OFF_LAND_LOCAL_SOURCE_'+b.GetLayerName(l)+'_'+str(i));b.Add(z);newzones.append(z.m_Uuid.AsString())
dest=O/'motherboard-U25-two-local-barrels-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,exact_modified_Cu_UUIDs=changes,added_zone_UUIDs=newzones,exact_copper_ledger=[dict(uuid=u,before=oldcu[u],after=identity(cu[u]))for u in changes],Source_unchanged=True,manufacturer_lands_unchanged=True,no_rated_power_array_changes=True));print('Native exact two-barrel correction refill',flush=True)
n=drc(dest,O,'native');write(O/'native-counts.json',dict(errors=sum(r['severity']=='error'for r in n['violations']),warnings=sum(r['severity']=='warning'for r in n['violations']),ignored=len(n['ignored_checks'])));assert not n['violations']and not n['ignored_checks']
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();ac={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()};assert set(ac)==set(oldcu)and all(ac[u]==v for u,v in oldcu.items()if u not in changes);assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()};az=definitions(dest);assert set(az)==set(oldz)|set(newzones)and all(az[u]==v for u,v in oldz.items());now=native_pad_clusters(after,nets);assert clusters_survive(oldclusters,now);write(O/'actual-native-Source-cluster-proof.json',dict(passed=True,before=oldclusters,after=now));assert all(sha(q)==h for q,h in inputs.items())
write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=changes,reviewed_added_zone_UUIDs=newzones,reviewed_scope_reason='Necessary exact U25 low-current positive/return barrel shift and exact attached leaves; remove real C80 Ground via drill from fitted SMD land and restore intrinsic U25 Source output-pad reference envelope. No Source/pad/pose/rated-array or older outline changes; current106 C80 manifest must be rechecked.'))
write(O/'receipt.json',dict(passed=False,native_geometry_passed=True,remaining_current_controls_resources_and_power_proof_required=True,before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),modified_Cu_UUIDs=changes,added_zone_UUIDs=newzones,Source26_unchanged=True,Source27_adopted=False,manufacturing_ready=False));print(json.dumps(dict(native_passed=True,board_sha256=sha(dest),changes=changes)),flush=True)
