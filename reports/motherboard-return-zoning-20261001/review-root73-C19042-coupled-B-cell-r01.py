"""Read-only exact bypass/AIN2 coupled-cell feasibility, no Source mutation."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm
from hardware_route_owned_bypass_loops import Geometry

bp=Path('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/source26-r73-C19042-coupled-B-cell-feasibility-r01.json')
if out.exists():raise ValueError('Fresh review required')
b=pcbnew.LoadBoard(str(bp));objects={t.m_Uuid.AsString():t for t in b.GetTracks()}
ids=['8afc32f4-2047-4ff3-bf87-aa7153d9627f','c9ad7bff-105f-4b2e-b8a7-94d9c78f2e84','0c5eaaf8-1041-4f68-a66c-19fad00520b1']
for uid in ids:
 if objects[uid].GetNetname()!='/motherboard_safety_sensor/DI_SENSOR_AIN2':raise ValueError('Exact reviewed private Source AIN2 net differs')
q=(124.6,172.9)
objects[ids[0]].SetEnd(xy(q));objects[ids[1]].SetPosition(xy(q));objects[ids[2]].SetStart(xy(q))
f=next(f for f in b.GetFootprints()if f.GetReference()=='C19042');old=mm(f.GetPosition());clone=pcbnew.Cast_to_FOOTPRINT(f.Duplicate(False));b.Remove(f);clone.SetPosition(xy((126.25,171.6)));results=[]
for angle in(0,180):
 clone.SetOrientationDegrees(angle);p={p.GetNumber():p for p in clone.Pads()};power=mm(p['1'].GetPosition());ground=mm(p['2'].GetPosition());g=Geometry(b)
 checks={}
 checks['AIN2_relocated_barrel_legal']=g.via(q,objects[ids[1]].GetNetname())
 # Ignore the moved barrel's own same-net geometry; all foreign clearances
 # remain in the spatial index. No proposal is adopted by this screen.
 checks['AIN2_F_private_endpoint_clear']=g.clear([mm(objects[ids[0]].GetStart()),q],objects[ids[0]].GetNetname(),pcbnew.F_Cu,.2)
 checks['AIN2_B_private_endpoint_clear']=g.clear([q,mm(objects[ids[2]].GetEnd())],objects[ids[2]].GetNetname(),pcbnew.B_Cu,.2)
 checks['positive_via_free_standing']=g.via((124.35,171.5),'/motherboard_do/DOB_FIELD_3V3')
 checks['F_VDD_escape_clear']=g.clear([(123.2,171.5),(124.35,171.5)],'/motherboard_do/DOB_FIELD_3V3',pcbnew.F_Cu,.2)
 checks['B_cap_power_path_clear']=g.clear([(124.35,171.5),power],'/motherboard_do/DOB_FIELD_3V3',pcbnew.B_Cu,.2)
 checks['source_positive_nearby_ground_stitch_free_standing']=g.via((125.2,171.5),'/motherboard_do/FIELD_B_0V')
 checks['cap_ground_barrel_free_standing']=g.via((127.775,172.4),'/motherboard_do/FIELD_B_0V')
 checks['B_cap_ground_escape_clear']=g.clear([ground,(127.775,172.4)],'/motherboard_do/FIELD_B_0V',pcbnew.B_Cu,.2)
 checks['In4_old_FieldB_piece_contact_clear']=g.clear([(127.775,172.4),(127.775,174),(123.2,174),(123.2,173.05)],'/motherboard_do/FIELD_B_0V',pcbnew.In4_Cu,.2)
 results.append(dict(cap_pose_mm=[126.25,171.6,angle],cap_power_mm=list(power),cap_ground_mm=list(ground),checks=checks,geometry_screen_passed=all(checks.values()),actual_refill_DRC_courtyards_Source_cluster_and_strict_corridor_still_required=True))
 print(angle,checks,flush=True)
write(out,dict(board_sha256=sha(bp),read_only=True,no_native_candidate_saved=True,no_source_pin_net_land_value_or_part_change=True,reviewed_coupled_private_AIN2_UIDs=ids,old_AIN2_via_mm=[124.6,172.5],proposed_AIN2_via_mm=list(q),old_C19042_center_mm=list(old),rows=results,manufacturing_ready=False))
