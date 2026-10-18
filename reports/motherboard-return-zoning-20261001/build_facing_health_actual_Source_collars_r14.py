"""Exact current health receiving/cap Source collars on the combined native PCB."""
from pathlib import Path
import sys,json,shutil,argparse,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_stitch_owned_return_planes import definitions
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_zone_motherboard_returns import functional_barrier,split_polygons
from hardware_route_selected_additive import corridor_polygon
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_validate_motherboard_return_planes_r06 import validate
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--screen-only',action='store_true');a=p.parse_args();B=a.board;O=a.out;assert not O.exists();O.mkdir()
S=Path('hardware/motherboard');AUTH=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb')
R19=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/receipt.json');R20=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-A-r236/receipt.json');R26=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r235/receipt.json');M=AUTH.parent/'current106-bypass-manifest.json';GEN=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/generation.json');G8=B.parent/'generation.json'
inputs={str(q):sha(q)for q in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),S/'design.json',S/'netlist.xml',AUTH,R19,R20,R26,M,GEN,G8,Path(__file__)]};assert inputs[str(S/'design.json')]=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()}
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];write(O/'before-domain-map.json',dict(mp,actual_board_sha256=sha(B)));guard=ReferenceGuard(b,mp)
shapes={};screen=[];decls={};selected=[];groups={};sourcejoins=[]
def add(ret,label,layer,shape,uid=None):
 bb=shape.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];hits=[]
 for other,project in guard.indices[layer].candidates(tuple(bounds[:2]),tuple(bounds[2:]),.3):
  if other==ret:continue
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(project)
  if hit.OutlineCount():hits.append(dict(foreign=other,exact_intersection=hit.Format(False)))
 for br in mp['barriers']:
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(functional_barrier(br))
  if hit.OutlineCount():hits.append(dict(barrier=br['reference'],exact_intersection=hit.Format(False)))
 screen.append(dict(role=label,uuid=uid,return_net=ret,layer=b.GetLayerName(layer),bounds_mm=bounds,exact_envelope=shape.Format(False),conflicts=hits));shapes.setdefault((ret,layer),pcbnew.SHAPE_POLY_SET()).BooleanAdd(shape)
def around(ret,label,pt,radius,uid=None):
 for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add(ret,label,l,corridor_polygon(tuple(xy(pt)),tuple(xy(pt)),pcbnew.FromMM(radius)),uid)
for owner in('U11020','U11026'):
 ret=pads[owner,'2'].GetNetname();private={pads[owner,n].GetNetname()for n in('1','3')};decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);decls.update({n:decl for n in private})
 for t in cu.values():
  if t.GetNetname()not in private:continue
  selected.append(t.m_Uuid.AsString())
  if t.Type()==pcbnew.PCB_VIA_T:around(ret,owner+'_actual_control_transfer',mm(t.GetPosition()),.82,t.m_Uuid.AsString())
  else:add(ret,owner+'_actual_control_segment',pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.45)),t.m_Uuid.AsString())
manifest=json.loads(M.read_text());r19=json.loads(R19.read_text());r20=json.loads(R20.read_text());r26=json.loads(R26.read_text());gen=json.loads(GEN.read_text());g8=json.loads(G8.read_text())
positive_roles={
 'C11078':(r19,{'U11019_local_positive_transfer','U11019_own_local_VCC_F','U11019_own_local_VCC_B'}),
 'C11079':(r20,{'U11020_local_positive_transfer','U11020_own_positive_F','U11020_own_positive_B'}),
 'C11081':(r26,{'U11026_local_positive_transfer','U11026_own_positive_F','U11026_own_positive_B'})}
for cap,(receipt,roles)in positive_roles.items():
 ids=[row['uuid']for row in receipt['exact_added_copper']if row['role']in roles];assert ids and all(u in cu for u in ids)
 owner={'C11078':'U11019','C11079':'U11020','C11081':'U11026'}[cap];ret=pads[owner,'2'].GetNetname();supply=pads[owner,'5'].GetNetname();assert supply==pads[cap,'1'].GetNetname()
 for uid in ids:
  t=cu[uid];assert t.GetNetname()==supply
  if t.Type()==pcbnew.PCB_VIA_T:around(ret,cap+'_actual_positive_annulus',mm(t.GetPosition()),.82,uid)
  else:add(ret,cap+'_actual_dedicated_bypass_positive',pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.20)),uid)
 groups[cap]=dict(ref=cap,owner=owner,category='local_bypass',new_UUIDs=ids,retained=True,actual_owning_signal_return_pairs_connected=True,disposition='Actual local dedicated positive branch only; receiving Source Ground annuli independently required. Long rail and LED distribution excluded.')
ground_specs=[('C11078','/LOGIC_GND',(342.25,178.85),[(342.25,178.85),(342.4125,178.)]),('C11079','/LOGIC_GND',(337.05,173.75),[(337.05,173.75),(337.15,175.85)]),('C11081','/motherboard_motors/FIELD_GND',(335.3875,186.65),[(335.3875,186.65),(335.8875,187.6)])]
for cap,ret,point,path in ground_specs:
 via=next(t for t in cu.values()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()==ret and mm(t.GetPosition())==point);around(ret,cap+'_actual_short_cap_Ground_annulus',point,.35,via.m_Uuid.AsString());groups[cap]['new_UUIDs'].append(via.m_Uuid.AsString());sourcejoins.append(dict(capacitor=cap,return_net=ret,Ground_via=via.m_Uuid.AsString(),points_mm=path))
 for st,en in zip(path,path[1:]):
  for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add(ret,cap+'_bounded_Source_Ground_piece_join',l,corridor_polygon(tuple(xy(st)),tuple(xy(en)),pcbnew.FromMM(.25)),via.m_Uuid.AsString())
for owner,point in[('U11019',(344.3875,175)),('U11019',(343.84756,176.36006)),('U11020',(337.15,175.85)),('U11020',(340.5875,175)),('U11026',(335.8875,187.6)),('U11026',(331.9125,187.6))]:
 ret=pads[owner,'2'].GetNetname();v=next(t for t in cu.values()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()==ret and mm(t.GetPosition())==point);around(ret,owner+'_actual_receiving_Source_Ground_annulus',point,.35,v.m_Uuid.AsString())
c80=next(g for g in manifest['owned_loops']if g['ref']=='C11080');c80['new_UUIDs']=list(dict.fromkeys(c80['new_UUIDs']+gen['exact_added_Cu_UUIDs']+[g8['added_Cu_UUID']]));c80['exact_modified_Cu_UUIDs']=gen['exact_modified_Cu_UUIDs'];c80['explicit_rebind_reason']='Actual off-land positive/Ground pair and dedicated B cap branch, all bends outside endpoint antipad; shared U13.2 Source return restored. Retained long FIELD5 distribution not credited as local bypass.'
manifest['owned_loops']=[groups['C11078']if g['ref']=='C11078'else g for g in manifest['owned_loops']]+[groups['C11079'],groups['C11081']];manifest.update(board_sha256=sha(B),scope='Current108 actual local receivers:106 with explicit C78/C80 replacements plus new C79/C81. Full new immutable native proof required; remote health producer/LED/timing/power capability remains separately bounded.',actual_filled_supply_branch_return_reviews=[]);assert len([g for g in manifest['owned_loops']if g['retained']])==108
write(O/'projection-screen.json',dict(passed=not any(r['conflicts']for r in screen),rows=screen,actual_Source_ground_joins=sourcejoins));write(O/'current108-bypass-manifest.json',manifest);print(json.dumps(dict(screen_rows=len(screen),conflicts=[r for r in screen if r['conflicts']])),flush=True)
if a.screen_only:sys.exit(0)
assert not any(r['conflicts']for r in screen),'Actual foreign Source projection/barrier conflict remains'
oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B);ab=pcbnew.LoadBoard(str(AUTH));ab.BuildConnectivity();nets={p.GetNetname()for p in ab.GetPads()if p.GetNumber()};oldcl=native_pad_clusters(ab,nets);newzones=[]
for(ret,l),shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for br in mp['barriers']:blocked.Append(functional_barrier(br))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(l)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify();template=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==ret and z.IsOnLayer(l));priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(l))+1
 for i,piece in enumerate(split_polygons(shape)):
  z=template.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority);z.SetZoneName('HEALTH_FACING_ACTUAL_SOURCE_'+b.GetLayerName(l)+'_'+str(i));b.Add(z);newzones.append(z.m_Uuid.AsString())
dest=O/'motherboard-facing-health-Source-collars-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,added_zone_UUIDs=newzones,selected_control_UUIDs=selected,Source_ground_joins=sourcejoins));print('Native Source/collar refill',flush=True);n=drc(dest,O,'native');counts=dict(errors=sum(v['severity']=='error'for v in n['violations']),warnings=sum(v['severity']=='warning'for v in n['violations']),ignored=len(n['ignored_checks']));write(O/'native-counts.json',counts);assert counts['errors']==counts['ignored']==0
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();assert oldcu=={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}and oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()};az=definitions(dest);assert set(az)==set(oldz)|set(newzones)and all(az[u]==v for u,v in oldz.items());now=native_pad_clusters(after,nets);assert clusters_survive(oldcl,now);write(O/'all-ROOT101-Source-clusters.json',dict(passed=True,before=oldcl,after=now));mp=positioned(after,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mp);resource=validate(after,mp);resource.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resource)
cu={t.m_Uuid.AsString():t for t in after.GetTracks()};checker=ExactEndpointUnionCheck(after,decls);reviews=[]
for uid in selected:
 t=cu[uid];d=decls[t.GetNetname()]
 try:r=checker.via(t,d)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,d);reviews.append(dict(uuid=uid,passed=True,review=r))
 except ValueError as e:reviews.append(dict(uuid=uid,passed=False,error=str(e)))
write(O/'actual-controls-proof.json',dict(passed=all(r['passed']for r in reviews),board_sha256=sha(dest),margin_mm=.40,rows=reviews));manifest['board_sha256']=sha(dest);write(O/'current108-final-bypass-manifest.json',manifest);assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=newzones,reviewed_scope_reason='Tightly clipped current actual health-private control, local receiving/short-cap Ground annuli and exact Source-backed joins. Actual foreign metal/barriers screened; no LED power treated as signal, no tolerance/old-zone change. Remote producer and physical current/timing qualification remain separate.'))
write(O/'receipt.json',dict(passed=not counts['warnings']and resource['passed']and all(r['passed']for r in reviews),before_board=str(B),before_sha256=sha(B),board=str(dest),board_sha256=sha(dest),native=counts,controls_passed=all(r['passed']for r in reviews),Source_clusters_preserved=True,resource_passed=resource['passed'],current108_proof_and_global_power_pending=True,Source26_unchanged=True,Source27_adopted=False,manufacturing_ready=False));print(json.dumps(dict(board_sha256=sha(dest),native=counts,controls_failed=[r for r in reviews if not r['passed']],resources=resource['passed'])),flush=True)

