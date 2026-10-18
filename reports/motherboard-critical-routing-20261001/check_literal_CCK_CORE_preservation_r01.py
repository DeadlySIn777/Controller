"""Literal CCK donor's relative CORE geometry; no ampacity or voltage promise.

The frozen general IO3/CORE equality helper is never modified. Its identical
unbuffered membership, 502um backbone and narrow-feature code is reused on the
actual CORE1V2 plane, with all source and receiver contacts separately checked.
"""
from pathlib import Path
import sys,importlib.util,json,copy,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_logic_return import identity,mm,xy
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_check_return_corridors import circle,covered
P=Path('reports/motherboard-critical-routing-20261001/actual-source26-root84-FPGA-CCK-C1022-F-In2-r06')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
SOURCE=Path('hardware/motherboard/design.json');FROZEN=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py')
import hashlib
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(FROZEN)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
spec=importlib.util.spec_from_file_location('exact_frozen_r07',FROZEN);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
CORE='/CORE_1V2';PINS=('E9','F7','F8','F9','G11','J6','J7','K11','K9')
def connected(board,p,q):return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
def review(before,after):
 model=json.loads(SOURCE.read_text());assert model['components']['U2001']['mpn']=='TPS62901RPJR'
 plan=json.loads((P/'proposed-delta.json').read_text());expected=set(plan['new_signal_UUIDs']+plan['new_SOURCE_ground_UUIDs']+plan['new_C1022_local_power_UUIDs'])
 before.BuildConnectivity();after.BuildConnectivity();bc={t.m_Uuid.AsString():t for t in before.GetTracks()};ac={t.m_Uuid.AsString():t for t in after.GetTracks()}
 if set(ac)-set(bc)!=expected or any(u not in ac or identity(t)!=identity(ac[u])for u,t in bc.items()):raise ValueError('Literal retained/additive conductor scope changed')
 bp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in before.GetPads()};ap={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in after.GetPads()}
 # Source/regulator/SW/sense/softstart/thermal lands are not moved or edited.
 protected_parts=('U2001','L2001','C2002','C2003','C2004','R2001','R2002','R2003','U1001')
 for r in protected_parts:
  for key,p in bp.items():
   if key[0]!=r:continue
   q=ap[key]
   if p.m_Uuid.AsString()!=q.m_Uuid.AsString()or p.GetNetname()!=q.GetNetname()or mm(p.GetPosition())!=mm(q.GetPosition())or tuple(p.GetSize())!=tuple(q.GetSize())or p.GetShape()!=q.GetShape():raise ValueError('Actual protected source/receiver land changed')
 bf=collect_native_reference_fills(before,{CORE},[pcbnew.In3_Cu])[CORE,pcbnew.In3_Cu];af=collect_native_reference_fills(after,{CORE},[pcbnew.In3_Cu])[CORE,pcbnew.In3_Cu]
 geometry=f.backbone(bf,af)
 source_before,source_after=bp['L2001','2'],ap['L2001','2']
 endpoints=[]
 for key,p in bp.items():
  if p.GetNetname()!=CORE:continue
  q=ap[key];old=connected(before,source_before,p);new=connected(after,source_after,q)
  if old and not new:raise ValueError('An actual prior CORE Source endpoint is disconnected')
  endpoints.append(dict(reference=key[0],pin=key[1],before_actual_source_connected=old,after_actual_source_connected=new,already_unconnected_before=not old))
 receivers=[]
 for pin in PINS:
  p,q=bp['U1001',pin],ap['U1001',pin]
  assert p.GetNetname()==q.GetNetname()==CORE
  old_peer={x.m_Uuid.AsString()for x in before.GetConnectivity().GetConnectedItems(p)}
  candidate_vias=[t for u,t in bc.items()if u in old_peer and t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()==CORE and math.dist(mm(t.GetPosition()),mm(p.GetPosition()))<=2.]
  annuli=[]
  for t in candidate_vias:
   u=t.m_Uuid.AsString();v=ac[u];old_contact=physical_reference_contact(t,pcbnew.In3_Cu,before.GetConnectivity());new_contact=physical_reference_contact(v,pcbnew.In3_Cu,after.GetConnectivity())
   if old_contact and not new_contact:raise ValueError('An actual prior receiver CORE annulus lost inner contact')
   if old_contact:
    roi=circle(tuple(t.GetPosition()),pcbnew.FromMM(1.))
    if not f.symmetric_equal(f.intersection(bf,roi),f.intersection(af,roi)):raise ValueError('Actual CORE native copper changed inside receiving tab guard')
   annuli.append(dict(via_uuid=u,xy=mm(v.GetPosition()),before_flashing_Source_connected_on_In3=old_contact,after_flashing_Source_connected_on_In3=new_contact))
  receivers.append(dict(pin=pin,actual_xy_mm=mm(q.GetPosition()),before_source_connected=connected(before,source_before,p),after_source_connected=connected(after,source_after,q),actual_retained_receiving_annuli=annuli))
 points=[mm(bp[key].GetPosition())for key in(('U2001','3'),('L2001','2'),('C2002','1'),('R2003','1'))];roi=f.box(min(x for x,y in points)-3,min(y for x,y in points)-3,max(x for x,y in points)+3,max(y for x,y in points)+3)
 if not f.symmetric_equal(f.intersection(bf,roi),f.intersection(af,roi)):raise ValueError('Regulator/sense/output regional filled CORE copper changed')
 # Every removed physical polygon must lie inside actual added via copper+
 # the retained 0.20mm native clearance. This is derived from actual objects,
 # not a broad arbitrary hole/mask permission.
 removed=f.subtract(bf,af);literal_antipads=pcbnew.SHAPE_POLY_SET();audits=[]
 for u in sorted(expected):
  t=ac[u]
  if t.Type()!=pcbnew.PCB_VIA_T:continue
  radius=t.GetWidth(pcbnew.In3_Cu)//2+pcbnew.FromMM(.20)
  actual=circle(tuple(t.GetPosition()),radius);overlap=f.intersection(removed,actual)
  if overlap.OutlineCount():
   literal_antipads.BooleanAdd(actual);audits.append(dict(via_uuid=u,net=t.GetNetname(),xy=mm(t.GetPosition()),native_Cu_radius_mm=pcbnew.ToMM(t.GetWidth(pcbnew.In3_Cu)//2),retained_native_clearance_mm=.20,removed_actual_CORE_area_mm2=overlap.Area()/1e12,removed_actual_CORE_polygon=overlap.Format(False)))
 residual=f.subtract(removed,literal_antipads)
 if residual.OutlineCount():raise ValueError('CORE removal extends outside literal added-via antipads')
 return dict(passed=True,scope='Only the exact CCK+C1022 candidate relative CORE change',source_mpn='TPS62901RPJR',manufacturer_IC_current_rating_a=1.,source_rating_is_not_board_capacity_proof=True,source_input_sha256=sha(SOURCE),frozen_original_power_helper_sha256=sha(FROZEN),generic_CORE_equality_guard_unchanged=True,actual_CORE_backbone=geometry,actual_CORE_SOURCE_endpoint_inventory=endpoints,actual_nine_FPGA_receiver_status=receivers,converter_SW_sense_softstart_thermal_pad_poses_and_old_Cu_exact=True,converter_output_region_filled_geometry_exact=True,actual_literal_antipad_ledger=audits,remaining_outside_antipad_removal_mm2=0.,all_old_actual_Core_Source_contacts_preserved=True,no_prior_disconnected_receiver_promoted_without_native_evidence=True,relative_geometry_only=True,full_load_IRdrop_PDN_thermal_unqualified=True,manufacturing_ready=False)
if __name__=='__main__':
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(P/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'))
 try:r=review(before,after)
 except Exception as ex:r=dict(passed=False,error=str(ex),actual_board_sha256=sha(P/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'),generic_CORE_equality_guard_unchanged=True,manufacturing_ready=False)
 (out/'review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k in('passed','error','actual_literal_antipad_ledger')}));raise SystemExit(not r['passed'])
