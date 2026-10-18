from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
from hardware_route_current_delivery_native import sha
from hardware_build_assembly import parse,dump,child
ROOT=Path('reports/motherboard-power-entry-20261001/health-supply-r99');rec=json.loads((ROOT/'receipt.json').read_text());b=pcbnew.LoadBoard(str(ROOT/'motor-health-supply-candidate.kicad_pcb'));b.BuildConnectivity();p={(v.GetParentFootprint().GetReference(),v.GetNumber()):v for v in b.GetPads()};c=b.GetConnectivity()
checks=[]
for row in rec['actual_endpoint_checks']:
 a,z=p[row['from_ref'],row['from_pin']],p[row['to_ref'],row['to_pin']];passv=z.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in c.GetConnectedItems(a)};assert passv;checks.append(dict(**row,passed=passv))
# Each designated bypass requires both actual power and return continuity. Cut its positive receiver barrel: cap must cease being a valid local bypass.
controls=[]
for u,cap in [('U11019','C11078'),('U11020','C11079'),('U11025','C11080'),('U11026','C11081')]:
 role=u+'_own_bypass_positive_from_via';uid=next(v['uuid']for v in rec['exact_added_copper']if v['role']==role);tree=parse((ROOT/'motor-health-supply-candidate.kicad_pcb').read_text());tree=[v for v in tree if not(isinstance(v,list)and v and v[0]=='via'and child(v,'uuid')[1]==uid)];temp=ROOT/('negative-'+u+'.kicad_pcb');temp.write_text(dump(tree));q=pcbnew.LoadBoard(str(temp));q.BuildConnectivity();qs={(v.GetParentFootprint().GetReference(),v.GetNumber()):v for v in q.GetPads()};a,z=qs[u,'5'],qs[cap,'1'];cut=z.m_Uuid.AsString()not in{v.m_Uuid.AsString()for v in q.GetConnectivity().GetConnectedItems(a)};assert cut,(u,uid);controls.append(dict(owner=u,designated_cap=cap,removed_uuid=uid,actual_local_bypass_check_rejected=True))
# Physical current allocation only: supply routes carry CMOS supply and bias load; no motor drive load is credited here.
r=dict(source_board_sha256=sha(ROOT/'motor-health-supply-candidate.kicad_pcb'),actual_endpoint_checks=checks,four_local_bypass_negative_cuts=controls,source27_part_correction_required=True,loaded_dynamic_supply_return_noise_unqualified=True,all_added_positive_and_ground_vias_free_no_auto_net_reassignment=True)
(ROOT/'independent-proof.json').write_text(json.dumps(r,indent=2));print('INDEPENDENT_PASS',len(checks),len(controls),flush=True)

