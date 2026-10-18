"""Native path-clipped Logic references after exact supply-barrel repairs.

Eight actual series LED POWER rows are separately frozen and receive no
signal-reference credit. Eighteen logical control roles retain full .40 mm
coverage, actual Source-backed Ground stitches and native annuli.
"""
import sys,json,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_zone_motherboard_returns import split_polygons,functional_barrier
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_route_owned_bypass_loops import drc
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_validate_motherboard_return_planes_r06 import validate
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard

base=Path('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r120/motor-bank-A-control-repaired-candidate.kicad_pcb')
manifest=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r121/actual-control-segment-manifest.json')
power=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-eight-LED-power-classification-r02/classification.json')
out=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r120-logic-reference-collars-r03')
source=Path('hardware/motherboard');inputs=[base,base.with_suffix('.kicad_pro'),base.with_suffix('.kicad_dru'),manifest,power,source/'design.json',source/'netlist.xml',Path(__file__)]
if out.exists():raise ValueError('Fresh immutable native output required')
out.mkdir();(out/'inputs').mkdir()
frozen={str(p):sha(p)for p in inputs}
for p in inputs:shutil.copy2(p,out/'inputs'/p.name)
data=json.loads(manifest.read_text());classification=json.loads(power.read_text())
if data['source_board_sha256']!=sha(base)or not classification['passed']:raise ValueError('Exact reviewed control/power inputs required')
rows=data['rows']
if len(rows)!=82 or len(data['logical_original_control_roles'])!=18 or not data['all_five_source_ground_stitches_native_connected']:raise ValueError('Exact82 segments/18 roles/5 actual Ground witnesses required')
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity()
model=json.loads((source/'design.json').read_text());parts={r:c for r,c in model['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')}
nodes,nc,functions=native(source/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc)
mapping=positioned(b,parts,nodes,nc,functions,domains,barriers)
if mapping['errors']:raise ValueError('Actual native source map mismatch')
mapping.update(actual_board_sha256=sha(base),input_sha256=frozen)
write(out/'actual-moved-source-domain-map.json',mapping)
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base)
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
actual={t.m_Uuid.AsString():t for t in b.GetTracks()};guard=ReferenceGuard(b,mapping)
shapes={};conflicts=[]
for row in rows:
 if row['own_return']!='/LOGIC_GND' or row['net']in {r['net']for r in classification['exact_power_rows']}:raise ValueError('A power row cannot enter strict Logic control scope')
 if len(row['actual_copper_UUIDs'])!=1 or len(row['literal_points_mm'])!=2:raise ValueError('One exact actual native segment required per row')
 ident=row['actual_copper_UUIDs'][0];item=actual[ident]
 if item.Type()!=pcbnew.PCB_TRACE_T or item.GetNetname()!=row['net']or b.GetLayerName(item.GetLayer())!=row['layer']or [list(mm(item.GetStart())),list(mm(item.GetEnd()))]!=row['literal_points_mm']:raise ValueError('Native control segment identity drift '+ident)
 a,c=row['literal_points_mm'];layer=b.GetLayerID(row['reference_layer'])
 projected=corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(row['width_mm']/2+.4))
 for foreign,other in guard.indices[layer].candidates(a,c,row['width_mm']/2+.7):
  if foreign=='/LOGIC_GND':continue
  hit=pcbnew.SHAPE_POLY_SET();hit.Append(projected);hit.BooleanIntersection(other)
  if hit.Area():conflicts.append(dict(uuid=ident,role=row['role'],foreign_return=foreign,intersection_mm2=hit.Area()/1e12))
 for barrier in mapping['barriers']:
  hit=pcbnew.SHAPE_POLY_SET();hit.Append(projected);hit.BooleanIntersection(functional_barrier(barrier))
  if hit.Area():conflicts.append(dict(uuid=ident,actual_package_barrier=barrier['reference'],intersection_mm2=hit.Area()/1e12))
 shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(row['width_mm']/2+.5)))
write(out/'actual-foreign-source-projection-review.json',dict(passed=not conflicts,exact_segments=len(rows),conflicts=conflicts))
if conflicts:raise ValueError('Actual foreign Source/barrier projection cannot receive Logic reference')
transfers=data['actual_control_transfers']
write(out/'literal-control-transfers.json',transfers)
for transfer in transfers:
 # The peer manifest records actual signal-via identity and a real physical
 # Ground witness; no synthetic tie or package-internal bridge is accepted.
 ident=transfer.get('signal_via_uuid',transfer.get('signal_via',{}).get('uuid'))
 if ident is None:raise ValueError('Exact signal-via UUID field required')
 item=actual[ident]
 if item.Type()!=pcbnew.PCB_VIA_T:raise ValueError('Actual native signal transfer required')
 for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):
  shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(corridor_polygon(tuple(item.GetPosition()),tuple(item.GetPosition()),pcbnew.FromMM(1.1)))
new=[]
for layer,shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for barrier in mapping['barriers']:blocked.Append(functional_barrier(barrier))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(layer)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify()
 owner=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()=='/LOGIC_GND'and z.GetLayer()==layer)
 priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(layer))+1
 for index,piece in enumerate(split_polygons(shape)):
  z=owner.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority)
  z.SetZoneName('MOTOR_BANK_A_ACTUAL_CONTROL_'+b.GetLayerName(layer)+'_'+str(index));b.Add(z);new.append(z.m_Uuid.AsString())
dest=out/'motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(input_sha256=frozen,new_zone_UUIDs=new,exact82_actual_control_segments=rows,exact5_control_transfer_Source_Ground_witnesses=transfers,eight_LED_power_rows_excluded_with_frozen_classification=str(power)))
print('Actual Logic-only motor control collar refill starts',flush=True)
native_report=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
if oldcu!=now or oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}:raise ValueError('Actual old Source/Cu/pose drift')
actualzones=definitions(dest)
if set(actualzones)!=set(oldzones)|set(new)or any(actualzones[u]!=s for u,s in oldzones.items()):raise ValueError('Old Source-zone definition drift')
after=native_pad_clusters(b,nets);survive=clusters_survive(oldclusters,after)
write(out/'all-native-Source-cluster-proof.json',dict(passed=survive,before=oldclusters,after=after))
if not survive:raise ValueError('Native Source cluster lost')
full=validate(b,mapping);full.update(board_sha256=sha(dest),source_map_sha256=sha(out/'actual-moved-source-domain-map.json'));write(out/'full-native-resource-review.json',full)
if any(r['severity']=='error'for r in native_report['violations'])or native_report['ignored_checks']:raise ValueError('Native reference collision')
actual={t.m_Uuid.AsString():t for t in b.GetTracks()};checker=NativeCollectedAnnulusCheck(b,{})
passed=[];failed=[]
for row in rows:
 declaration=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
 checker.rows[row['net']]=declaration;ident=row['actual_copper_UUIDs'][0]
 try:passed.append(dict(uuid=ident,review=checker.segment(actual[ident],declaration)))
 except ValueError as e:failed.append(dict(uuid=ident,role=row['role'],reason=str(e)))
write(out/'actual82-control-segment-reference-reviews.json',dict(passed=not failed,rows=passed,failed=failed))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=new,reviewed_scope_reason='Exact82 actual control-segment/18-role Logic In1/In4 clipped reference collars and5 real Source-ground transfer witnesses. Eight LED POWER rows explicitly excluded; no Source/pad/Cu/pose/old-zone change. No whole-current/20ms/manufacturing claim.'))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist',str(source/'netlist.xml'),'--source-design',str(source/'design.json'),'--out',str(out/'independent-connectivity')],capture_output=True,text=True)
(out/'independent-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent Source connectivity failed')
ind=json.loads((out/'independent-connectivity/review.json').read_text())
for p,h in frozen.items():
 if sha(Path(p))!=h:raise ValueError('Frozen input changed')
write(out/'receipt.json',dict(passed=not failed and full['passed'],input_sha256=frozen,before_board_sha256=sha(base),board_sha256=sha(dest),new_zones=len(new),native_errors=0,ignored_checks=[],all_prior_Source_clusters_pads_Cu_poses_oldzones_retained=True,strict_segment_failures=failed,full_resource_passed=full['passed'],uncapped_native=ind['uncapped_unconnected_ratsnest_edges'],independent_Source_missing=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],manufacturing_ready=False))
print('Exact82 segments reviewed; strict failures',len(failed),'full resources passed',full['passed'],flush=True)
