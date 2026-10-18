"""Bounded two-health-cell native Source/reference prototype.

Actual private signal geometry has the frozen .40 mm guard. LED conductors
remain low-current power. U26 Ground connects to the actual U25 Source barrel,
not a name-equivalent unanchored field pocket. Existing Source26 stays frozen.
"""
from pathlib import Path
import argparse,sys,json,shutil,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_zone_motherboard_returns import functional_barrier,split_polygons
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import mm,xy,identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_validate_motherboard_return_planes_r06 import validate
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck

p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--screen-only',action='store_true');a=p.parse_args()
B=a.board;O=a.out;assert not O.exists();O.mkdir()
S=Path('hardware/motherboard')
R20=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-A-r236/receipt.json')
R26=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r235/receipt.json')
AUTH=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb')
assert sha(AUTH)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
assert sha(S/'design.json')=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
inputs={str(q):sha(q)for q in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),R20,R26,AUTH,S/'design.json',S/'netlist.xml',Path(__file__)]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()}
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')}
nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(B));write(O/'before-domain-map.json',mp)
guard=ReferenceGuard(b,mp);shapes={};screen=[];decls={};selected=[];power=[];groundw=[];source_paths=[]

def add(owner,ret,label,item,layer,shape):
 bb=shape.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];hits=[]
 for other,projection in guard.indices[layer].candidates(tuple(bounds[:2]),tuple(bounds[2:]),.3):
  if other==ret:continue
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(projection)
  if hit.OutlineCount():hits.append(dict(foreign=other,exact_intersection=hit.Format(False)))
 for br in mp['barriers']:
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(functional_barrier(br))
  if hit.OutlineCount():hits.append(dict(package_barrier=br['reference'],exact_intersection=hit.Format(False)))
 screen.append(dict(owner=owner,return_net=ret,role=label,uuid=item.m_Uuid.AsString(),layer=b.GetLayerName(layer),bounds_mm=bounds,exact_envelope=shape.Format(False),conflicts=hits))
 shapes.setdefault((ret,layer),pcbnew.SHAPE_POLY_SET()).BooleanAdd(shape)

for owner,rr in [('U11020',R20),('U11026',R26)]:
 pins={q.GetNumber():q for q in fps[owner].Pads()};ret=pins['2'].GetNetname();private={pins['1'].GetNetname(),pins['3'].GetNetname()};assert len(private)==2
 decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4)
 decls.update({n:decl for n in private})
 for t in cu.values():
  if t.GetNetname()not in private:continue
  selected.append(t.m_Uuid.AsString())
  if t.Type()==pcbnew.PCB_VIA_T:
   for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add(owner,ret,'private_input_transfer',t,l,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(.82)))
   for g in cu.values():
    if g.Type()!=pcbnew.PCB_VIA_T or g.GetNetname()!=ret or math.dist(tuple(g.GetPosition()),tuple(t.GetPosition()))>pcbnew.FromMM(1):continue
    groundw.append(dict(owner=owner,signal_via=t.m_Uuid.AsString(),ground_via=g.m_Uuid.AsString(),position_mm=mm(g.GetPosition())))
    for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add(owner,ret,'actual_own_Ground_signal_stitch',g,l,corridor_polygon(tuple(g.GetPosition()),tuple(g.GetPosition()),pcbnew.FromMM(.35)))
  else:
   assert t.GetLayer()in(pcbnew.F_Cu,pcbnew.B_Cu)
   add(owner,ret,'private_input_segment',t,pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.45)))
 receipt=json.loads(rr.read_text());local=[]
 for row in receipt['exact_added_copper']:
  if row['role']not in(owner+'_local_positive_transfer',owner+'_own_positive_F',owner+'_own_positive_B'):continue
  t=cu[row['uuid']];assert t.GetNetname()==pins['5'].GetNetname();local.append(t.m_Uuid.AsString());power.append(t.m_Uuid.AsString())
  if t.Type()==pcbnew.PCB_VIA_T:
   for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add(owner,ret,'actual_local_receiving_positive_transfer',t,l,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(.82)))
  else:add(owner,ret,'actual_local_bypass_positive_path',t,pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.20)))
 recv=cu[next(row['uuid']for row in receipt['exact_added_copper']if row['role']==owner+'_local_Source_return_stitch')]
 for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add(owner,ret,'actual_receiving_Ground_annulus',recv,l,corridor_polygon(tuple(recv.GetPosition()),tuple(recv.GetPosition()),pcbnew.FromMM(.35)))
 if owner=='U11026':
  src=next(t for t in cu.values()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()==ret and mm(t.GetPosition())==(333.4375,191.))
  assert next(q for q in fps['U11025'].Pads()if q.GetNumber()=='2').GetNetname()==ret
  for role in(owner+'_actual_ground_pin_transfer',owner+'_local_Source_return_stitch'):
   t=cu[next(row['uuid']for row in receipt['exact_added_copper']if row['role']==role)]
   start=mm(t.GetPosition());points=[start,(start[0],189.),(333.4375,190.25),mm(src.GetPosition())]
   source_paths.append(dict(role=role,ground_via=t.m_Uuid.AsString(),source_via=src.m_Uuid.AsString(),actual_source='U11025.2/C11080.2',points_mm=points))
   for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):
    for st,en in zip(points,points[1:]):add(owner,ret,'actual_receiving_Ground_to_U25_Source',t,l,corridor_polygon(tuple(xy(st)),tuple(xy(en)),pcbnew.FromMM(.25)))
write(O/'actual-foreign-Source-projection-screen.json',dict(passed=not any(r['conflicts']for r in screen),board_sha256=sha(B),rows=screen,selected_input_UUIDs=selected,actual_Ground_witnesses=groundw,actual_U26_Source_paths=source_paths))
print(json.dumps(dict(screen_rows=len(screen),conflicts=[dict(owner=r['owner'],role=r['role'],uuid=r['uuid'],layer=r['layer'],foreign=[h.get('foreign',h.get('package_barrier'))for h in r['conflicts']])for r in screen if r['conflicts']])),flush=True)
if a.screen_only:sys.exit(0)
assert not any(r['conflicts']for r in screen),'Real foreign SOURCE projection/barrier conflict; no collar adopted'
oldcu={u:identity(t)for u,t in cu.items()};oldpads={q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()};oldz=definitions(B)
ab=pcbnew.LoadBoard(str(AUTH));ab.BuildConnectivity();nets={q.GetNetname()for q in ab.GetPads()if q.GetNumber()};oldclusters=native_pad_clusters(ab,nets)
new=[]
for (ret,l),shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for br in mp['barriers']:blocked.Append(functional_barrier(br))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(l)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify()
 tpl=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==ret and z.IsOnLayer(l));priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(l))+1
 for i,piece in enumerate(split_polygons(shape)):
  z=tpl.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority);z.SetZoneName('ROOT101_REAL_HEALTH_SOURCE_'+b.GetLayerName(l)+'_'+str(i));b.Add(z);new.append(z.m_Uuid.AsString())
dest=O/'motherboard-two-health-Source-reference-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,new_zone_UUIDs=new,selected_private_control_UUIDs=selected,local_bypass_positive_UUIDs=power,actual_U26_Source_paths=source_paths));print('Native exact two-cell Source/reference refill',flush=True)
n=drc(dest,O,'native');write(O/'native-counts.json',dict(errors=sum(r['severity']=='error'for r in n['violations']),warnings=sum(r['severity']=='warning'for r in n['violations']),ignored=len(n['ignored_checks'])));assert not n['violations']and not n['ignored_checks']
b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();assert oldcu=={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}and oldpads=={q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()};az=definitions(dest);assert set(az)==set(oldz)|set(new)and all(az[u]==v for u,v in oldz.items());now=native_pad_clusters(b,nets);assert clusters_survive(oldclusters,now);write(O/'ROOT101-all-Source-cluster-proof.json',dict(passed=True,before=oldclusters,after=now))
mp=positioned(b,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mp);resource=validate(b,mp);resource.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resource)
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};checker=ExactEndpointUnionCheck(b,decls);reviews=[]
for u in selected:
 t=cu[u];row=decls[t.GetNetname()]
 try:v=checker.via(t,row)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,row);reviews.append(dict(uuid=u,passed=True,review=v))
 except ValueError as e:reviews.append(dict(uuid=u,passed=False,error=str(e)))
write(O/'actual-private-input-controls-proof.json',dict(passed=all(r['passed']for r in reviews),board_sha256=sha(dest),literal_declarations=decls,rows=reviews,unchanged_strict_margin_mm=.4,LED_conductors_remain_power=True))
write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=new,reviewed_scope_reason='Actual Source26 health-private control collars and U26 own FIELD_GND Source joining to U25 real Ground barrel, all literal Source projections and frozen .40 margin/annulus/stitch proof preserved; no LED power classified as signal.'))
assert all(sha(q)==h for q,h in inputs.items());passed=resource['passed']and all(r['passed']for r in reviews)
write(O/'receipt.json',dict(passed=passed,before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),input_sha256=inputs,native_errors=0,native_warnings=0,Source26_unchanged=True,Source27_adopted=False,controls_passed=all(r['passed']for r in reviews),full_resource_passed=resource['passed'],manufacturing_ready=False));print(json.dumps(dict(passed=passed,failed=[r for r in reviews if not r['passed']],resources=resource['passed'],board_sha256=sha(dest))),flush=True)
