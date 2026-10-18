"""Actual C78 local pose correction plus two literal source-free outline cuts."""
import sys,json,shutil,subprocess,hashlib
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew as p
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_route_logic_return import identity,pad_identity,xy
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_zone_motherboard_returns import split_polygons
from hardware_validate_motherboard_return_planes_r06 import validate,exact_twice_area
from hardware_build_assembly import parse
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-health-C78-registration-literal-cuts-r23/motherboard-health-composed-candidate.kicad_pcb');D=B.parent;O=D.with_name('ROOT101-health-C78-robust-cap-clearance-r27');assert not O.exists();O.mkdir();assert sha(B)=='8015ebe8fef2c447db9126cdd44604e944186e60ebd52def8dbbc45d6060c03b'
M=D/'current108-final-bypass-manifest.json';R=D/'full-native-resource-review.json';S=Path('hardware/motherboard');inputs={str(q):sha(q)for q in(B,M,R,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),Path(__file__),S/'design.json',S/'netlist.xml')}
b=p.LoadBoard(str(B));b.BuildConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()};nets={q.GetNetname()for q in b.GetPads()if q.GetNumber()};oldcl=native_pad_clusters(b,nets);cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
barrel='9d7ff79f-eaf2-47e4-b28d-6b7138e8acf8';back='2c3fb5ed-2496-489e-9df0-6ddc143bd63b';capreturn='f6764397-e74d-42d7-96dc-081b7f509a8e';ids=[back,capreturn]
assert tuple(cu[barrel].GetPosition())==tuple(xy((343,176.65)))
cap=next(f for f in b.GetFootprints()if f.GetReference()=='C11078');assert tuple(cap.GetPosition())==tuple(xy((343.25,178.075)))and cap.GetOrientationDegrees()==-90
oldcapids={q.m_Uuid.AsString()for q in cap.Pads()};cap.SetPosition(xy((343.25,178.175)))
assert tuple(cu[back].GetStart())==tuple(xy((343.25,177.3)));cu[back].SetStart(xy((343.25,177.4)))
assert tuple(cu[capreturn].GetStart())==tuple(xy((343.25,178.85)));cu[capreturn].SetStart(xy((343.25,178.95)))
for pad in b.GetPads():
 if pad.GetAttribute()==p.PAD_ATTRIB_SMD:
  assert not any(pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(p.SHAPE_CIRCLE(cu[barrel].GetPosition(),cu[barrel].GetDrillValue()//2+p.FromMM(.15)+1),0)for layer in(p.F_Cu,p.B_Cu)),(pad.GetParentFootprint().GetReference(),pad.GetNumber())
resource_before=json.loads(R.read_text());assert resource_before['board_sha256']==sha(B);pending=resource_before['unanchored_components'];assert len(pending)==2
zones={z.m_Uuid.AsString():z for z in b.Zones()};cuts={};rows=[]
for row in pending:
 witness=row['literal_native_positive_metal_provenance'];uid=witness['zone_uuid'];z=zones[uid];layer=b.GetLayerID(row['reference_layer']);assert z.GetNetname()=='/LOGIC_GND'and row['net']=='/LOGIC_GND'
 piece=list(split_polygons(z.GetFilledPolysList(layer)))[witness['literal_filled_piece']];assert exact_twice_area(piece)==witness['literal_native_twice_area_nm2']==41160
 cut=p.SHAPE_POLY_SET();cut.Append(piece);cut.Inflate(p.FromMM(.014),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.001));assert cut.OutlineCount()==1
 assert not any(q.IsOnLayer(layer)and cut.Collide(q.GetEffectiveShape(layer),0)for q in b.GetPads())
 assert not any(t.IsOnLayer(layer)and cut.Collide(t.GetEffectiveShape(layer),0)for t in b.GetTracks())
 cuts[uid]=cut;rows.append(dict(zone_uuid=uid,net=z.GetNetname(),layer=row['reference_layer'],literal_filled_piece=witness['literal_filled_piece'],exact_twice_area_nm2=exact_twice_area(piece),exact_literal_polygon=piece.Format(False),exact_14um_capsule_cut=cut.Format(False),no_source_pad_or_conductor_on_cut=True))
for uid,cut in cuts.items():
 z=zones[uid];shape=p.SHAPE_POLY_SET();shape.Append(z.Outline());shape.BooleanSubtract(cut);assert shape.OutlineCount()==1;z.Outline().RemoveAllContours();z.Outline().Append(shape)
dest=O/'motherboard-health-final-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in D.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
p.SaveBoard(str(dest),b)
def zd(path):return{u:zone_definition(t)for u,t in objects(parse(without_generated_fills(path.read_text())),'zone').items()}
oldz,newz=zd(B),zd(dest);assert set(oldz)==set(newz)and all(oldz[u]==newz[u]for u in oldz if u not in cuts)
ledger=[dict(uuid=u,before_definition_sha256=hashlib.sha256(oldz[u].encode()).hexdigest(),after_definition_sha256=hashlib.sha256(newz[u].encode()).hexdigest(),electrical_outline_correction_reason='Remove only the exact positively proven unused Source-free native triangle using its exact 14um capsule, with all actual Source pads, current loop/control corridors and old Source clusters independently preserved. No area exemption.')for u in cuts]
write(O/'generation.json',dict(input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),exact_unused_literal_triangles=rows,modified_Cu_UUIDs=ids,cap_before_pose_mm=[343.25,178.075,-90],cap_after_pose_mm=[343.25,178.175,-90],positive_barrel_preserved_mm=[343,176.65],actual_drill_SMD_nominal_gap_mm=.2,reason='Move only the local cap100um downward and rejoin its two exact endpoint leaves, preserving the already proven positive barrel/SC6 escape with50um margin above the.15mm drill registration screen.'))
write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=['C11078'],reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[],reviewed_existing_zone_outline_deltas=ledger,reviewed_scope_reason='One C78 local100um pose correction/two exact endpoint leaves and two exact unused triangle outline cuts only. Every old Source pad/cluster, actual control/loop/annulus and unchanged global power guard required.'))
print('Native robust C78 cap/endpoint and exact two triangle refill',flush=True);n=drc(dest,O,'native');assert not n['violations']and not n['ignored_checks']
a=p.LoadBoard(str(dest));a.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};assert set(now)==set(oldcu)and all(now[u]==v for u,v in oldcu.items()if u not in ids);assert {u:v for u,v in oldpads.items()if u not in oldcapids}=={q.m_Uuid.AsString():pad_identity(q)for q in a.GetPads()if q.m_Uuid.AsString()not in oldcapids};assert next(f for f in a.GetFootprints()if f.GetReference()=='C11078').GetPosition()==xy((343.25,178.175));newcl=native_pad_clusters(a,nets);assert clusters_survive(oldcl,newcl);write(O/'all-prior-Source-clusters.json',dict(passed=True,before=oldcl,after=newcl))
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(a,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mp);resource=validate(a,mp);resource.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resource)
pads={(f.GetReference(),q.GetNumber()):q for f in a.GetFootprints()for q in f.Pads()if q.GetNumber()};decls={}
for owner in('U11020','U11026'):
 d=dict(return_net=pads[owner,'2'].GetNetname(),reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);decls.update({pads[owner,q].GetNetname():d for q in('1','3')})
checker=ExactEndpointUnionCheck(a,decls);proof=[]
for t in a.GetTracks():
 if t.GetNetname()not in decls:continue
 try:r=checker.via(t,decls[t.GetNetname()])if t.Type()==p.PCB_VIA_T else checker.segment(t,decls[t.GetNetname()]);proof.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=r))
 except ValueError as e:proof.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
write(O/'actual-controls-proof.json',dict(passed=all(r['passed']for r in proof),board_sha256=sha(dest),margin_mm=.4,rows=proof))
manifest=json.loads(M.read_text());manifest['board_sha256']=sha(dest);write(O/'current108-final-bypass-manifest.json',manifest)
run=subprocess.run([sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(dest),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt',str(O/'current108-final-bypass-manifest.json'),'--out',str(O/'current108-actual-strict-loop-proof.json')],capture_output=True,text=True);(O/'current108-command.txt').write_text(run.stdout+run.stderr)
assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'receipt.json',dict(passed=resource['passed']and all(r['passed']for r in proof)and run.returncode==0,board=str(dest),board_sha256=sha(dest),before_board=str(B),before_board_sha256=sha(B),native_errors=0,native_warnings=0,Source_Cu_pad_pose_preservation=True,resource_passed=resource['passed'],actual_controls_passed=all(r['passed']for r in proof),current108_passed=run.returncode==0,combined_registration_and_global_power_pending=True,ROOT102_two_cap_composition_pending=True,manufacturing_ready=False));print(json.dumps(dict(board_sha256=sha(dest),resources=resource['passed'],controls=all(r['passed']for r in proof),current108=run.returncode==0)),flush=True)
