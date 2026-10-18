"""Exact SOURCE-reviewed two-input CMOS receiving reference collars.

Only the two literal private signal nets are scored as controls. LED currents
remain explicitly power. Source-own existing Ground stitches and full annuli,
not net names, determine via eligibility after the native refill.
"""
from pathlib import Path
import argparse,sys,json,shutil,subprocess,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_stitch_owned_return_planes import definitions
from hardware_zone_motherboard_returns import functional_barrier,split_polygons
from hardware_route_selected_additive import corridor_polygon
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
from hardware_validate_motherboard_return_planes_r06 import validate
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--peer-receipt',type=Path,required=True);p.add_argument('--owner',choices=['U11020','U11026'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();B=a.board;O=a.out;assert not O.exists();O.mkdir();S=Path('hardware/motherboard');inputs={str(p):sha(p)for p in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),a.peer_receipt,S/'design.json',S/'netlist.xml',Path(__file__)]};assert sha(S/'design.json')=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8';b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};pins={p.GetNumber():p for p in fps[a.owner].Pads()};ret=pins['2'].GetNetname();private={pins['1'].GetNetname(),pins['3'].GetNetname()};assert len(private)==2;cu={t.m_Uuid.AsString():t for t in b.GetTracks()};selected=[t for t in cu.values()if t.GetNetname()in private];assert selected and all(t.Type()in(pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T)for t in selected);oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,f=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,f,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(B));write(O/'before-domain-map.json',mp);guard=ReferenceGuard(b,mp);shapes={};screen=[];groundw=[]
def add(label,t,l,shape):
 bb=shape.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];hits=[]
 for foreign,poly in guard.indices[l].candidates(tuple(bounds[:2]),tuple(bounds[2:]),1.3):
  if foreign==ret:continue
  h=pcbnew.SHAPE_POLY_SET(shape);h.BooleanIntersection(poly)
  if h.OutlineCount():hits.append(dict(foreign=foreign,exact_intersection=h.Format(False)))
 for br in mp['barriers']:
  h=pcbnew.SHAPE_POLY_SET(shape);h.BooleanIntersection(functional_barrier(br))
  if h.OutlineCount():hits.append(dict(package_barrier=br['reference'],exact_intersection=h.Format(False)))
 screen.append(dict(uuid=t.m_Uuid.AsString(),role=label,layer=b.GetLayerName(l),exact_envelope=shape.Format(False),bounds_mm=bounds,conflicts=hits));shapes.setdefault(l,pcbnew.SHAPE_POLY_SET()).BooleanAdd(shape)
for t in selected:
 if t.Type()==pcbnew.PCB_VIA_T:
  for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add('actual_private_input_signal_transfer',t,l,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.2)))
  for g in cu.values():
   if g.Type()!=pcbnew.PCB_VIA_T or g.GetNetname()!=ret:continue
   if math.dist(tuple(g.GetPosition()),tuple(t.GetPosition()))>pcbnew.FromMM(1):continue
   witness=dict(signal_via=t.m_Uuid.AsString(),ground_via=g.m_Uuid.AsString(),position_mm=mm(g.GetPosition()));groundw.append(witness)
   for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):add('actual_own_Ground_stitch',g,l,corridor_polygon(tuple(g.GetPosition()),tuple(g.GetPosition()),pcbnew.FromMM(.5)))
 else:add('actual_private_input_segment',t,pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.5)))
write(O/'actual-foreign-Source-projection-screen.json',dict(passed=not any(r['conflicts']for r in screen),board_sha256=sha(B),literal_signal_nets=sorted(private),return_net=ret,rows=screen,actual_Ground_witness_proposals=groundw));assert not any(r['conflicts']for r in screen),'Actual foreign physical Source/barrier obstruction: retain failed screen'
new=[]
for l,shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for br in mp['barriers']:blocked.Append(functional_barrier(br))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(l)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify();tpl=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(l)and z.GetNetname()==ret);priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(l))+1
 for i,piece in enumerate(split_polygons(shape)):
  z=tpl.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority);z.SetZoneName(a.owner+'_ACTUAL_PRIVATE_INPUT_REFERENCE_'+b.GetLayerName(l)+'_'+str(i));b.Add(z);new.append(z.m_Uuid.AsString())
dest=O/'motherboard-own-input-reference-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,O/p.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,new_zone_UUIDs=new,selected_actual_control_UUIDs=[t.m_Uuid.AsString()for t in selected],literal_private_signal_nets=sorted(private),actual_Ground_witness_proposals=groundw));print('Native exact SOURCE private-control collar refill',flush=True);n=drc(dest,O,'native');assert not n['violations']and not n['ignored_checks'];b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();assert oldcu=={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}and oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};az=definitions(dest);assert set(az)==set(oldz)|set(new)and all(az[u]==v for u,v in oldz.items());now=native_pad_clusters(b,nets);assert clusters_survive(oldclusters,now);write(O/'all-native-Source-cluster-proof.json',dict(passed=True,before=oldclusters,after=now));mp=positioned(b,parts,nodes,nc,f,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mp);resources=validate(b,mp);resources.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resources);decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);cu={t.m_Uuid.AsString():t for t in b.GetTracks()};ch=ExactEndpointUnionCheck(b,{net:decl for net in private});rev=[]
for t in selected:
 t=cu[t.m_Uuid.AsString()]
 try:v=ch.via(t,decl)if t.Type()==pcbnew.PCB_VIA_T else ch.segment(t,decl);rev.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=v))
 except ValueError as e:rev.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
passed=all(r['passed']for r in rev);write(O/'actual-private-input-controls-proof.json',dict(passed=passed,board_sha256=sha(dest),return_net=ret,literal_signal_nets=sorted(private),rows=rev,guard_margin_mm=.4,exact_same_Source_annulus_stitch_radius_and_endpoint_exceptions=True,LED_sink_Ground_and_supply_rows_not_misclassified_as_signals=True));write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=new,reviewed_scope_reason='Tightly clipped real native two-input private CMOS control references; preserve all existing source/lands/poses/copper/old zones; unchanged .40 margins, exact endpoint exceptions, actual Source/flashed/native-connected annuli. LED circuits stay power.'));assert all(sha(p)==h for p,h in inputs.items());write(O/'receipt.json',dict(passed=passed and resources['passed'],before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),Source_unchanged=True,full_resources_passed=resources['passed'],control_passed=passed,native_errors=0,native_warnings=0,manufacturing_ready=False));print(json.dumps(dict(passed=passed,resource=resources['passed'],failed=[r for r in rev if not r['passed']],board_sha256=sha(dest))),flush=True)
