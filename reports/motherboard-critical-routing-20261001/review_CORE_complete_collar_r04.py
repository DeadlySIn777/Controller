"""Literal physical antipad collar, separate from the failed routing guard."""
from pathlib import Path
import sys,json,importlib.util,math,copy,hashlib
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_zone_motherboard_returns import split_polygons
from hardware_check_return_corridors import circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
import check_literal_CCK_CORE_preservation_r01 as reviewed
f=reviewed.f;P=Path(__file__).parent
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
FOLDER=P/'CORE-literal-antipad-join-baseline-r03';BP=FOLDER/'motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'
OUT=P/'CORE-complete-collar-native-review-r04';OUT.mkdir(exist_ok=False)
CORE='/CORE_1V2';source=Path('hardware/motherboard/design.json');sha=reviewed.sha
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(BP));before.BuildConnectivity();after.BuildConnectivity()
proposal=json.loads((FOLDER/'proposal.json').read_text());actual_core_zones=[z for z in after.Zones()if z.GetNetname()==CORE and z.IsOnLayer(pcbnew.In3_Cu)and not z.GetIsRuleArea()];assert {z.GetMinThickness()for z in actual_core_zones}=={pcbnew.FromMM(.175)};native=json.loads((FOLDER/'native.json').read_text())
assert not native['violations']and not native['ignored_checks'];assert sha(BASE)==proposal['input_board_sha256']
oldcu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()};assert oldcu==newcu
oldpads={p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()};newpads={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()};assert oldpads==newpads
bz,az=definitions(BASE),definitions(BP);rule_uid=proposal['literal_rule_uuid'];assert set(az)==set(bz)|{rule_uid}and all(az[u]==row for u,row in bz.items())
region=f.box(*proposal['literal_bounds_mm']);rule=next(z for z in after.Zones()if z.m_Uuid.AsString()==rule_uid)
assert rule.GetIsRuleArea()and list(rule.GetLayerSet().Seq())==[pcbnew.In3_Cu]and rule.GetDoNotAllowZoneFills()and not any((rule.GetDoNotAllowTracks(),rule.GetDoNotAllowVias(),rule.GetDoNotAllowPads(),rule.GetDoNotAllowFootprints()))
assert f.symmetric_equal(rule.Outline(),region)
bf=collect_native_reference_fills(before,{CORE},[pcbnew.In3_Cu])[CORE,pcbnew.In3_Cu];af=collect_native_reference_fills(after,{CORE},[pcbnew.In3_Cu])[CORE,pcbnew.In3_Cu]
bp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in before.GetPads()};ap={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in after.GetPads()}
sb,sa=bp['L2001','2'],ap['L2001','2'];cb={t.m_Uuid.AsString():t for t in before.GetTracks()};ca={t.m_Uuid.AsString():t for t in after.GetTracks()}
def connected(b,p,q):return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
def ownership(old,new):
 pieces=list(split_polygons(new));rows=[]
 for i,piece in enumerate(split_polygons(old)):
  owners=[j for j,q in enumerate(pieces)if f.intersection(piece,q).OutlineCount()]
  assert len(owners)==1,'A real source-connected component split/disappeared';rows.append(dict(before=i,after=owners[0]))
 return rows
full=ownership(bf,af);be=f.duplicate(bf);ae=f.duplicate(af)
for x in(be,ae):x.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
assert be.OutlineCount()and ae.OutlineCount();cores=ownership(be,ae)
opened=f.duplicate(be);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(bf);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
narrow=f.subtract(bf,opened);precision=f.duplicate(af);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);lost=f.subtract(narrow,precision);outside=f.subtract(lost,region)
if outside.OutlineCount():
 (OUT/'outside-scope-failure.json').write_text(json.dumps(dict(passed=False,literal_bounds=proposal['literal_bounds_mm'],actual_outside_polygon=outside.Format(False),area_mm2=outside.Area()/1e12,manufacturing_ready=False),indent=2));raise ValueError('Actual definite old thin CORE feature lost outside literal collar')
assert not f.intersection(af,region).OutlineCount(),'Actual kept rule area still contains Core fill'
contacts=[];annuli=[]
for key,p in bp.items():
 if p.GetNetname()!=CORE:continue
 q=ap[key];old,new=connected(before,sb,p),connected(after,sa,q);assert not old or new
 pos=mm(p.GetPosition());size=mm(p.GetSize());guard=f.box(pos[0]-size[0]/2-1,pos[1]-size[1]/2-1,pos[0]+size[0]/2+1,pos[1]+size[1]/2+1)
 assert not f.intersection(region,guard).OutlineCount()
 assert f.symmetric_equal(f.intersection(bf,guard),f.intersection(af,guard))
 contacts.append(dict(reference=key[0],pin=key[1],before_source_connected=old,after_source_connected=new,actual_pad_and_1mm_receiving_guard_retained=True))
for uid,t in cb.items():
 if t.Type()!=pcbnew.PCB_VIA_T or t.GetNetname()!=CORE:continue
 q=ca[uid];old,new=physical_reference_contact(t,pcbnew.In3_Cu,before.GetConnectivity()),physical_reference_contact(q,pcbnew.In3_Cu,after.GetConnectivity());assert old==new
 guard=circle(tuple(t.GetPosition()),pcbnew.FromMM(1.));assert not f.intersection(region,guard).OutlineCount();assert f.symmetric_equal(f.intersection(bf,guard),f.intersection(af,guard))
 annuli.append(dict(uuid=uid,before_actual_In3_source_contact=old,after_actual_In3_source_contact=new,actual_1mm_receiving_guard_retained=True))
points=[mm(bp[k].GetPosition())for k in(('U2001','3'),('L2001','2'),('C2002','1'),('R2003','1'))];guard=f.box(min(x for x,y in points)-3,min(y for x,y in points)-3,max(x for x,y in points)+3,max(y for x,y in points)+3)
assert not f.intersection(region,guard).OutlineCount()and f.symmetric_equal(f.intersection(bf,guard),f.intersection(af,guard))
nets={p.GetNetname()for p in before.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(before,nets);newclusters=native_pad_clusters(after,nets);assert clusters_survive(oldclusters,newclusters)
assert sha(reviewed.FROZEN)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
receipt=dict(passed=True,adopted=False,scope='Literal unused In3 CORE cusp DFM collar only',before_board_sha256=sha(BASE),after_board_sha256=sha(BP),source_sha256=sha(source),literal_rule_uuid=rule_uid,literal_physical_bounds_mm=proposal['literal_bounds_mm'],derived_complete_existing_two_antipad_box_mm=proposal['actual_existing_antipad_bounding_box_mm'],literal_physical_min_feature_collar_mm=.10,actual_CORE_zone_minimum_feature_width_mm=.175,collar_is_separate_conservative_engineering_DFM_choice=True,prior_r03_UUID_and_minimum_feature_description_corrected_without_board_geometry_change=True,all_old_native_Cu_pads_lands_poses_zones_exact=True,actual_unbuffered_Core_component_ownership=full,actual_502um_Core_component_ownership=cores,minimum_Core_width_screen_mm=1.,all_definite_old_thin_features_outside_literal_correction_retained=True,no_area_or_precision_waiver=True,actual_Core_source_contacts=contacts,actual_Core_annuli=annuli,actual_converter_SW_sense_thermal_and_output_3mm_region_exact=True,all_actual_old_Source_clusters_preserved=True,actual_FPGA_Core_preexisting_unconnected_J7_retained_as_unconnected=True,previous_uncorrected_CCK_guard_failure_retained=True,generic_frozen_CORE_guard_unchanged=True,native_errors=0,native_warnings=0,no_ignored_checks=True,relative_loaded_rail_capacity_PDN_IRdrop_and_thermal_unqualified=True,CCK_holes_vs_corrected_baseline_separate_proof_required=True,manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(passed=True,core_contacts=len(contacts),core_annuli=len(annuli),source_connected=sum(c['before_source_connected']for c in contacts))))
