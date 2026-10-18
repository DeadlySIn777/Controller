"""Exact path-clipped own reference collars; no broad allocation or borrowed fill."""
import sys,json,shutil,collections,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import split_polygons,duplicate,rectangle,inflation,functional_barrier
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import identity,pad_identity,xy
from hardware_route_owned_bypass_loops import drc
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_validate_motherboard_return_planes_r06 import validate
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck

base=Path('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb')
logic=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-source-collar-screen-r02/screen.json')
field=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-field-collar-screen-r03/screen.json')
mp=logic.parent/'actual-moved-source-domain-map.json'
out=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-clipped-reference-collars-r01')
if out.exists():raise ValueError('Fresh immutable native output required')
out.mkdir();(out/'inputs').mkdir()
frozen={str(p):sha(p)for p in(base,logic,field,mp,Path(__file__))}
for p in(base,logic,field,mp,Path(__file__)):shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();mapping=json.loads(mp.read_text())
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base)
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
rows=[dict(r,own_return='/LOGIC_GND')for r in json.loads(logic.read_text())['rows']]
blocked=[r for r in json.loads(field.read_text())['rows']if r['actual_source_projection_conflicts']]
rows += [dict(r,own_return='/motherboard_motors/FIELD_GND')for r in json.loads(field.read_text())['rows']if not r['actual_source_projection_conflicts']]
shapes={};included=[]
for row in rows:
    key=row['own_return'],b.GetLayerID(row['reference_layer']);ext=shapes.setdefault(key,pcbnew.SHAPE_POLY_SET())
    if row['actual_source_projection_conflicts']:raise ValueError('Foreign-source rejected control cannot receive own fill')
    for a,c in zip(row['literal_points_mm'],row['literal_points_mm'][1:]):
        ext.BooleanAdd(corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(row['width_mm']/2+.5)))
    included.append(dict(role=row['role'],net=row['net'],own_return=row['own_return'],reference_layer=row['reference_layer'],actual_source_copper_UUIDs=row['actual_copper_UUIDs']))
# True control transfers receive a tightly bounded collar on both adjacent
# layers; a Ground stitch/source-annulus proof is still separately required.
controlnets={r['net']for r in rows if r['own_return']=='/LOGIC_GND'}
addedcu=json.loads((base.parent/'debug.json').read_text())['exact_added_copper']
addedset={r['uuid']for r in addedcu};transfers=[]
for item in b.GetTracks():
    if item.m_Uuid.AsString()not in addedset or item.Type()!=pcbnew.PCB_VIA_T or item.GetNetname()not in controlnets:continue
    transfers.append(item.m_Uuid.AsString())
    for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):
        ext=shapes.setdefault(('/LOGIC_GND',layer),pcbnew.SHAPE_POLY_SET())
        ext.BooleanAdd(corridor_polygon(tuple(item.GetPosition()),tuple(item.GetPosition()),pcbnew.FromMM(1.1)))
new=[];shape_reviews=[]
for (net,layer),shape in shapes.items():
    # Actual all-Cu package barriers and every raw/SUB/contact keepout remain.
    blockedshape=pcbnew.SHAPE_POLY_SET()
    for barrier in mapping['barriers']:blockedshape.Append(functional_barrier(barrier))
    for z in b.Zones():
        if z.GetIsRuleArea()and z.IsOnLayer(layer)and z.GetDoNotAllowZoneFills():blockedshape.Append(z.Outline())
    blockedshape.Simplify();shape.BooleanSubtract(blockedshape)
    shape.Simplify()
    owner=next(z for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==net and z.GetLayer()==layer)
    priority=max(z.GetAssignedPriority()for z in b.Zones()if not z.GetIsRuleArea()and z.IsOnLayer(layer))+1
    for index,piece in enumerate(split_polygons(shape)):
        z=owner.Duplicate();z.Outline().RemoveAllContours();z.Outline().Append(piece);z.SetAssignedPriority(priority)
        z.SetZoneName('MOTOR_BANK_A_PATH_CLIPPED_'+b.GetLayerName(layer)+'_'+net.rsplit('/',1)[-1]+'_'+str(index));b.Add(z);new.append(z.m_Uuid.AsString())
    shape_reviews.append(dict(net=net,reference_layer=b.GetLayerName(layer),exact_path_collar_area_mm2=shape.Area()/1e12))
dest=out/'motherboard-motor-bank-A-clipped-reference-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
    if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
    elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(input_sha256=frozen,new_zone_UUIDs=new,exact_path_clipped_shapes=shape_reviews,included_source_paths=included,actual_control_transfer_via_UUIDs=transfers,explicit_rejected_foreign_reference_paths=blocked,ground_stitch_and_full_source_qualification_pending=True))
print('MotorA actual clipped reference native refill starts',flush=True)
native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
if now!=oldcu or oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}:raise ValueError('Old SOURCE/Cu/poses changed')
actualzones=definitions(dest)
if set(actualzones)!=set(oldzones)|set(new)or any(actualzones[u]!=s for u,s in oldzones.items()):raise ValueError('Old Source zone definitions changed')
survive=clusters_survive(oldclusters,native_pad_clusters(b,nets));write(out/'all-native-SOURCE-cluster-proof.json',dict(passed=survive,before=oldclusters,after=native_pad_clusters(b,nets)))
if not survive:raise ValueError('Actual old SOURCE cluster lost')
full=validate(b,mapping);full.update(board_sha256=sha(dest),source_map_sha256=sha(mp));write(out/'full-native-resource-review.json',full)
if any(v['severity']=='error'for v in native['violations'])or native['ignored_checks']:raise ValueError('Actual native reference collision')
actual={t.m_Uuid.AsString():t for t in b.GetTracks()};checker=NativeCollectedAnnulusCheck(b,{})
checks=[];failed=[]
for row in rows:
    declaration=dict(return_net=row['own_return'],reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
    checker.rows[row['net']]=declaration
    for ident in row['actual_copper_UUIDs']:
        try:checks.append(dict(uuid=ident,review=checker.segment(actual[ident],declaration)))
        except ValueError as error:failed.append(dict(uuid=ident,role=row['role'],reason=str(error)))
write(out/'actual-source-path-reference-reviews.json',dict(passed=not failed,rows=checks,failed=failed,actual_control_transfer_and_Ground_stitch_proof_separate=True))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=new,reviewed_scope_reason='Literal path-clipped own-domain In1/In4 collars for18 actual motor Q/CLK/CLR/PG/OPI control rows and7 projection-clean local field-LED power rows. No SOURCE pad/Cu/pose/old-zone change. Actual transfer Ground stitches remain separately required; long foreign-projection field LED sink row is explicitly excluded. No blanket rectangle/reference/ampacity claim.'))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True);(out/'independent-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent full Source inventory failed')
ind=json.loads((out/'independent-connectivity/review.json').read_text())
for p,h in frozen.items():
    if sha(Path(p))!=h:raise ValueError('Frozen input changed')
write(out/'receipt.json',dict(passed=not failed,input_sha256=frozen,before_board_sha256=sha(base),board_sha256=sha(dest),new_zones=len(new),native_errors=0,ignored_checks=[],all_old_Source_clusters_pads_Cu_poses_zone_definitions_preserved=True,source_path_reference_failures=failed,uncapped_native=ind['uncapped_unconnected_ratsnest_edges'],independent_Source_missing=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],full_signal_transfer_reference_qualification=False,manufacturing_ready=False))
print('MotorA reference collar native candidate reviewed, segment failures',len(failed),flush=True)
