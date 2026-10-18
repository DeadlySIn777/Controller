"""Native independent review of one exact, separately scoped DFM cut.

The frozen r07 routing guard is not changed. This transaction permits only
the declared rectangular removal of three unused inter-antipad tips; its
full native component ownership and 502um backbone ownership remain exact.
All other definite thin features retain r07's existing 1um boundary screen.
"""
import json,sys,hashlib,inspect,subprocess
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-ordinary-routing-20261001')]
import pcbnew
import check_io3_backbone_preservation_r07 as power
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_stitch_owned_return_planes import definitions
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area

base=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
folder=Path('reports/motherboard-ordinary-routing-20261001/IO3-literal-unused-tip-cleanup-r02')
candidate=folder/'motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb'
proposal=folder/'proposal.json';native_path=folder/'native.json'
out=Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r08')
if out.exists():raise ValueError('Fresh immutable independent cleanup review required')
if not native_path.exists():raise ValueError('Actual native refill/DRC must finish before review')
out.mkdir();inputs=[base,candidate,proposal,native_path,Path(power.__file__),Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'),power.FEEDS]
frozen={str(p):sha(p)for p in inputs};p=json.loads(proposal.read_text());native=json.loads(native_path.read_text())
if sha(base)!=p['input_board_sha256']or p['exact_bounds_mm']!=[90.3,210.25,91.75,212.025]:raise ValueError('Exact source baseline/bounded cleanup proposal drift')
if native['violations']or native['ignored_checks']:raise ValueError('Native cleanup must be completely DRC-clean without exclusions')
before=pcbnew.LoadBoard(str(base));after=pcbnew.LoadBoard(str(candidate));before.BuildConnectivity();after.BuildConnectivity()
oldcu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};oldpads={pad.m_Uuid.AsString():pad_identity(pad)for pad in before.GetPads()}
if oldcu!={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}or oldpads!={pad.m_Uuid.AsString():pad_identity(pad)for pad in after.GetPads()}:raise ValueError('Actual Source/copper/manufacturer lands changed')
bzones=definitions(base);azones=definitions(candidate);uid=p['zone_uuid']
if set(azones)!=set(bzones)|{uid}or any(azones[u]!=d for u,d in bzones.items()):raise ValueError('Existing zone/plane/rule definition changed')
rule=next(z for z in after.Zones()if z.m_Uuid.AsString()==uid)
if not(rule.GetIsRuleArea()and list(rule.GetLayerSet().Seq())==[pcbnew.In2_Cu]and rule.GetDoNotAllowZoneFills()and not rule.GetDoNotAllowTracks()and not rule.GetDoNotAllowVias()and not rule.GetDoNotAllowPads()and not rule.GetDoNotAllowFootprints()):raise ValueError('Cleanup is not exactly an In2 copper-pour-only rule area')
region=power.box(*p['exact_bounds_mm'])
if not power.symmetric_equal(rule.Outline(),region):raise ValueError('Literal native bounded cleanup outline differs')
hits=[]
for z in before.Zones():
 if z.GetIsRuleArea()or not z.IsOnLayer(pcbnew.In2_Cu):continue
 hit=power.intersection(z.GetFilledPolysList(pcbnew.In2_Cu),region)
 if exact_twice_area(hit)>0:hits.append(dict(zone_uuid=z.m_Uuid.AsString(),net=z.GetNetname(),exact_intersection_twice_area_nm2=exact_twice_area(hit)))
if not hits or any(r['net']!='/IO_3V3'for r in hits):raise ValueError('The exact cleanup reaches foreign filled native copper')
for pad in before.GetPads():
 if pad.GetNetname()!='/IO_3V3':continue
 for layer in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu):
  if pad.IsOnLayer(layer)and region.Collide(pad.GetEffectiveShape(layer)):raise ValueError('Cleanup reaches actual IO3 Source/receiver land')
for item in before.GetTracks():
 if item.GetNetname()=='/IO_3V3'and item.IsOnLayer(pcbnew.In2_Cu)and region.Collide(item.GetEffectiveShape(pcbnew.In2_Cu)):raise ValueError('Cleanup reaches real IO3 conductor/barrel')

def exact_owned_components(old,new,label):
 result=[];pieces=list(split_polygons(new))
 for index,piece in enumerate(split_polygons(old)):
  if not power.intersection(piece,new).OutlineCount():raise ValueError(label+' loses a complete native component')
  owners=[j for j,current in enumerate(pieces)if power.intersection(piece,current).OutlineCount()]
  if len(owners)!=1:raise ValueError(label+' splits or merges away an old component ownership')
  result.append(dict(before_component=index,after_component=owners[0]))
 return result

def cleanup_geometry(old,new):
 full=exact_owned_components(old,new,'Unbuffered native IO3 fill')
 core_before=power.duplicate(old);core_after=power.duplicate(new)
 for core in(core_before,core_after):core.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
 if not core_before.OutlineCount()or not core_after.OutlineCount():raise ValueError('Empty 502um power core cannot be accepted')
 cores=exact_owned_components(core_before,core_after,'Literal 502um IO3 core')
 opened=power.duplicate(core_before);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(old)
 classified=power.duplicate(opened);classified.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 narrow=power.subtract(old,classified);precision_after=power.duplicate(new);precision_after.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 escaped=power.subtract(narrow,precision_after);outside=power.subtract(escaped,region)
 if outside.OutlineCount():
  lost=[]
  for piece in split_polygons(outside):
   box=piece.BBox();lost.append(dict(bounds_mm=[pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())],exact_twice_area_nm2=exact_twice_area(piece),native_polygon=piece.Format(False)))
  write(out/'outside-region-failure.json',dict(passed=False,input_sha256=frozen,board_sha256=sha(candidate),exact_authorized_region_mm=p['exact_bounds_mm'],unbuffered_native_topology=full,actual_502um_core_mapping=cores,all_literal_outside_loss_polygons=lost,no_precision_or_area_waiver=True))
  raise ValueError('A definite old thin feature outside the exact DFM region changed beyond frozen1um precision')
 removed=power.subtract(old,new)
 removed_outside=power.subtract(removed,region)
 # This uses the same bounded native1um contour comparison for literal
 # outside-region boundary differences; no area filter or widened margin.
 beyond=power.subtract(removed_outside,precision_after)
 if beyond.OutlineCount():raise ValueError('Unexpected real IO3 cut outside the literal DFM region')
 if exact_twice_area(power.intersection(new,region))>0:raise ValueError('The literal rule area still contains manufactured IO3 fill')
 return dict(passed=True,cleanup_specific=True,exact_DFM_region_mm=p['exact_bounds_mm'],actual_unbuffered_component_mapping=full,native_erosion_radius_mm=.502,minimum_screened_core_width_mm=1.,native_maximum_offset_error_mm=.001,exact_502um_core_component_mapping=cores,all_definite_old_thin_features_outside_literal_region_preserved=True,maximum_boundary_comparison_uncertainty_um=1,no_area_filter=True,exact_removed_native_polygons=removed.Format(False),exact_permitted_cleanup_thin_polygons=escaped.Format(False),ampacity_IR_drop_or_thermal_qualified=False)

# Reuse unchanged r07 Source44/receiver22/protected-region checks, with the
# separately declared literal cleanup geometry rule rather than pretending
# that an intentional DFM removal passed the unmodified routing-only rule.
original=power.backbone
try:
 power.backbone=cleanup_geometry
 proof=power.review(before,after)
finally:power.backbone=original
if sha(Path(power.__file__))!=frozen[str(Path(power.__file__))]:raise ValueError('Frozen r07 routing helper changed')
nets={pad.GetNetname()for pad in before.GetPads()if pad.GetNumber()};oldclusters=native_pad_clusters(before,nets);newclusters=native_pad_clusters(after,nets)
if not clusters_survive(oldclusters,newclusters):raise ValueError('Native physical Source pad cluster lost')
write(out/'complete-native-Source-cluster-proof.json',dict(passed=True,before=oldclusters,after=newclusters))
write(out/'cleanup-specific-power-proof.json',proof)
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(candidate),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True)
(out/'independent-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent actual complete Source connectivity failed')
inventory=json.loads((out/'independent-connectivity/review.json').read_text())
if inventory['orphan_copper_items']or inventory['uncapped_unconnected_ratsnest_edges']!=inventory['independent_physical_cluster_missing_joins']:raise ValueError('Native/independent Source connectivity discrepancy')
if any(sha(Path(path))!=h for path,h in frozen.items()):raise ValueError('Frozen independent inputs changed')
write(out/'receipt.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(candidate),exact_new_rule_area_uuid=uid,exact_bounded_native_IO3_fill_intersection=hits,existing_Cu_pads_lands_poses_zone_rules_preserved=True,actual_full_native_IO3_topology_502um_cores_Source44_feeds22_proved=True,all_definite_old_thin_features_outside_exact_region_retained=True,native_errors=0,native_warnings=0,ignored_checks=[],all_Source_clusters_retained=True,uncapped_native=inventory['uncapped_unconnected_ratsnest_edges'],independent_Source_missing=inventory['independent_physical_cluster_missing_joins'],orphan_copper=0,original_r07_routing_guard_bytes_unchanged=True,all_retained_reference_circuit_checks_separately_required=True,manufacturing_ready=False))
print('Independent literal DFM/source/topology/502um/44/22 proof passed',flush=True)
