"""Literal preflight for actual unused IO3 antipad-tip DFM correction."""
from pathlib import Path
import sys,json,hashlib
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as c
from hardware_route_logic_return import mm,identity
from hardware_check_return_corridors import circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
P=Path(__file__).parent;B=P/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb';O=P/'CCK-IO3-antipad-cleanup-preflight-r09';O.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();f=c.f;bounds=(93.175,43.575,94.025,44.425);region=f.box(*bounds)
pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};actual_vias=[t for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and mm(t.GetPosition())==(93.6,44.)];assert len(actual_vias)==1;via=actual_vias[0]
assert via.GetNetname()=='/LOGIC_GND'and via.GetDrillValue()==pcbnew.FromMM(.2)and via.GetWidth(pcbnew.F_Cu)==pcbnew.FromMM(.5)
failures=[];sourcepads=[];annuli=[];source=pads['R18001','2'];peers={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(source)}|{source.m_Uuid.AsString()}
for k,p in pads.items():
    if p.GetNetname()!='/IO_3V3':continue
    physical=p.GetEffectiveShape(pcbnew.In2_Cu)if p.IsOnLayer(pcbnew.In2_Cu)else p.GetEffectiveShape(pcbnew.F_Cu)
    hit=region.Collide(physical)
    if hit:failures.append(dict(kind='actual_IO3_Source_pad_shape_intersection',reference=k[0],pin=k[1]))
    sourcepads.append(dict(reference=k[0],pin=k[1],xy_mm=mm(p.GetPosition()),actual_source_connected=p.m_Uuid.AsString()in peers,physical_shape_disjoint=not hit))
feeds=json.loads(f.FEEDS.read_text());protected=[]
for r in feeds['actual_receiving_via_checks']:
    t=tracks[r['via_uuid']];guard=circle(tuple(t.GetPosition()),pcbnew.FromMM(1.));hit=f.intersection(region,guard).OutlineCount()
    if hit:failures.append(dict(kind='actual_receiving_1mm_guard_intersection',reference=r['reference'],via_uuid=r['via_uuid']))
    annuli.append(dict(reference=r['reference'],via_uuid=r['via_uuid'],actual_In2_flashing_Source_contact=physical_reference_contact(t,pcbnew.In2_Cu,b.GetConnectivity()),guard_disjoint=not hit))
points=[mm(pads[k].GetPosition())for k in(('U2002','3'),('L2002','2'),('R18001','1'),('R18001','2'),('C2005','1'),('C2010','1'))]
guards=[('converter_damper',f.box(min(x for x,y in points)-3,min(y for x,y in points)-3,max(x for x,y in points)+3,max(y for x,y in points)+3)),('source_via_array',f.box(59.5,22.2,63.3,26.)),('source_seam',f.box(57.6,96.,63.6,104.))]
for name,guard in guards:
    hit=f.intersection(region,guard).OutlineCount();protected.append(dict(name=name,disjoint=not hit))
    if hit:failures.append(dict(kind='retained_protected_power_region',region=name))
active=[]
for z in b.Zones():
    if not z.IsOnLayer(pcbnew.In2_Cu)or z.GetIsRuleArea():continue
    hit=f.intersection(z.GetFilledPolysList(pcbnew.In2_Cu),region)
    if hit.OutlineCount():active.append(dict(zone_uuid=z.m_Uuid.AsString(),net=z.GetNetname(),physical_native_scope_polygon=hit.Format(False),physical_scope_area_mm2=hit.Area()/1e12,minimum_feature_mm=pcbnew.ToMM(z.GetMinThickness()),local_clearance_mm=pcbnew.ToMM(z.GetLocalClearance())))
if not active or any(r['net']!='/IO_3V3'for r in active):failures.append(dict(kind='no_actual_IO3_fill_or_foreign_power_region',actual=active))
report=dict(passed=not failures,adopted=False,scope='Literal In2 pour-only physical collar around unchanged Ground93.6,44 antipad',board_sha256=c.sha(B),source_sha256=c.sha(c.SOURCE),frozen_power_guard_sha256=c.sha(c.FROZEN),literal_bounds_mm=bounds,actual_old_Ground_via_UUID=via.m_Uuid.AsString(),actual_old_via_identity=identity(via),native_In2_effective_shape=via.GetEffectiveShape(pcbnew.In2_Cu).Format(),actual_native_In2_annulus_present=via.FlashLayer(pcbnew.In2_Cu),nominal_old_drill_radius_plus_conservative_clearance_mm=.30,actual_physical_collar_mm=.125,collar_is_engineering_DFM_choice_not_manufacturer_max=True,actual_IO3_source_pad_shapes=sourcepads,actual22_receiver_1mm_regions=annuli,retained_source_and_converter_regions=protected,actual_filled_scope=active,failures=failures,old_thin_feature_failure_preserved=True,native_refill_source_backbone_and_outside_scope_comparison_still_required=True,manufacturing_ready=False)
(O/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],failures=failures,actual_IO3_pads=len(sourcepads),actual_receiver_guards=len(annuli),old_ground_via=via.m_Uuid.AsString())));assert report['passed']
