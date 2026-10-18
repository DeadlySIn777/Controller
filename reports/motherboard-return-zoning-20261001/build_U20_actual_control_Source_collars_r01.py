"""Actual U20 two-input tightly clipped Source-owned reference collars."""
from pathlib import Path
import sys,json,shutil
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write,native,classify,positioned
from hardware_build_assembly import parse
from hardware_merge_bounded_pcb_delta import objects,zone_definition,without_generated_fills
from hardware_stitch_owned_return_planes import definitions
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import functional_barrier,split_polygons
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_validate_motherboard_return_planes_r06 import validate
B=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r202/motor-health-U20-cell-candidate.kicad_pcb');R=B.parent/'receipt.json';SCR=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U20-control-screen-r01');O=SCR.with_name('ROOT94-health-U20-control-collars-r01');S=Path('hardware/motherboard');C=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94');assert not O.exists();O.mkdir();inputs={str(p):sha(p)for p in[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),R,SCR/'screen.json',SCR/'domain-map.json',S/'design.json',S/'netlist.xml',Path(__file__)]};screen=json.loads((SCR/'screen.json').read_text());assert screen['passed']and screen['board_sha256']==sha(B);b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldz=definitions(B);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets);mp=json.loads((SCR/'domain-map.json').read_text());receipt=json.loads(R.read_text());cu={t.m_Uuid.AsString():t for t in b.GetTracks()};selected=[r for r in receipt['exact_added_copper']if r['role'].startswith('U11020_input_')and'Ground'not in r['role']];assert len(selected)==18;shapes={}
for r in screen['rows']:
 layer=b.GetLayerID(r['reference_layer']);shape=pcbnew.SHAPE_POLY_SET();shape.Parse(r['exact_envelope']);shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(shape)
# Include only actual SOURCE-connected Ground stitches belonging to the two controls.
for row in receipt['exact_added_copper']:
 if'Ground'not in row['role']or not row['role'].startswith('U11020_input_'):continue
 t=cu[row['uuid']]
 if t.Type()!=pcbnew.PCB_VIA_T:continue
 assert t.GetNetname()=='/LOGIC_GND'and any(x.Type()==pcbnew.PCB_PAD_T for x in b.GetConnectivity().GetConnectedItems(t))
 for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(.35)))
new=[]
for layer,shape in shapes.items():
 blocked=pcbnew.SHAPE_POLY_SET()
 for barrier in mp['barriers']:blocked.Append(functional_barrier(barrier))
 for z in b.Zones():
  if z.GetIsRuleArea()and z.IsOnLayer(layer)and z.GetDoNotAllowZoneFills():blocked.Append(z.Outline())
 blocked.Simplify();shape.BooleanSubtract(blocked);shape.Simplify();template=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()=='/LOGIC_GND'and z.IsOnLayer(layer));priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(layer))+1
 for i,piece in enumerate(split_polygons(shape)):
  z=template.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority);z.SetZoneName('U11020_ACTUAL_INPUT_CONTROL_REFERENCE_'+b.GetLayerName(layer)+'_'+str(i));b.Add(z);new.append(z.m_Uuid.AsString())
dest=O/'motherboard-U20-two-control-reference-candidate.kicad_pcb'
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(suffix),dest.with_suffix(suffix))
for f in C.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,O/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,O/f.name)
pcbnew.SaveBoard(str(dest),b);write(O/'generation.json',dict(input_sha256=inputs,new_zone_UUIDs=new,selected_actual_control_UUIDs=[r['uuid']for r in selected],actual_Ground_rows_not_scored_as_signals=[r for r in receipt['exact_added_copper']if r['role'].startswith('U11020_input_')and'Ground'in r['role']]))
print('Native U20 tightly clipped control reference refill',flush=True);n=drc(dest,O,'native');assert not n['violations']and not n['ignored_checks'];a=pcbnew.LoadBoard(str(dest));a.BuildConnectivity();assert oldcu=={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()}and oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in a.GetPads()};az=definitions(dest);assert set(az)==set(oldz)|set(new)and all(az[u]==v for u,v in oldz.items());now=native_pad_clusters(a,nets);assert clusters_survive(oldclusters,now);write(O/'all-native-Source-cluster-proof.json',dict(passed=True,before=oldclusters,after=now))
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(S/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc);mapping=positioned(a,parts,nodes,nc,functions,domains,barriers);assert not mapping['errors'];mapping.update(actual_board_sha256=sha(dest));write(O/'domain-map.json',mapping);resource=validate(a,mapping);resource.update(board_sha256=sha(dest));write(O/'full-native-resource-review.json',resource)
tracks={t.m_Uuid.AsString():t for t in a.GetTracks()};decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);checker=NativeCollectedAnnulusCheck(a,{tracks[r['uuid']].GetNetname():decl for r in selected});reviews=[]
for r in selected:
 t=tracks[r['uuid']]
 try:result=checker.via(t,decl)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,decl);reviews.append(dict(uuid=r['uuid'],role=r['role'],passed=True,review=result))
 except ValueError as e:reviews.append(dict(uuid=r['uuid'],role=r['role'],passed=False,error=str(e)))
passed=all(r['passed']for r in reviews);write(O/'actual-two-input-controls-proof.json',dict(passed=passed,board_sha256=sha(dest),selected_actual_control_items=18,Source_Ground_roles_preserved_excluded_only_from_signal_scoring=True,reviews=reviews,strict_Source_annuli_radius_and_margin_unchanged=True));write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=new,reviewed_scope_reason='Tightly clipped actualU20 Source-backed LOGIC In1/In4 reference collars for exactly18 physical two-input control items, with real Source/Ground witnesses and foreign Source/package/barrier exclusions. No source/pad/land/pose/Cu/old-zone change.'))
assert all(sha(p)==h for p,h in inputs.items());write(O/'receipt.json',dict(passed=passed and resource['passed'],before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),native_errors=0,native_warnings=0,ignored_checks=[],actual_18_control_proof=passed,full_native_resources=resource['passed'],all_previous_Source_clusters_Cu_lands_poses_preserved=True,manufacturing_ready=False));print(json.dumps(dict(control_passed=passed,failed=[dict(uuid=r['uuid'],role=r['role'],error=r.get('error'))for r in reviews if not r['passed']],resource_passed=resource['passed'],board_sha256=sha(dest))),flush=True)
