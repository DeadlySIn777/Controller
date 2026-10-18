import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle,covered
p=argparse.ArgumentParser();p.add_argument('--board',required=True);p.add_argument('--receipt',required=True);p.add_argument('--case',required=True);a=p.parse_args()
b=pcbnew.LoadBoard(a.board);r=json.load(open(a.receipt));ids=r['new_copper_UUIDs'];net='/motherboard_analog_output/AO1_COM';tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};v=tracks[ids[1]];p5=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='U14626'and p.GetNumber()=='5')
if a.case=='missing-return-via':b.Remove(v)
elif a.case=='wrong-domain-via':v.SetNet(b.FindNet('/LOGIC_GND'))
elif a.case=='missing-GND5-branch':b.Remove(tracks[ids[0]])
elif a.case=='wrong-GND5-source-net':p5.SetNet(b.FindNet('/LOGIC_GND'))
elif a.case!='healthy':raise ValueError('Unreviewed case')
def qualified():
 if a.case=='missing-return-via'or v.GetNetname()!=net or p5.GetNetname()!=net:return False
 b.BuildConnectivity();conn=b.GetConnectivity();peers={q.m_Uuid.AsString()for q in conn.GetConnectedItems(v)}
 if p5.m_Uuid.AsString()not in peers or not physical_reference_contact(v,pcbnew.In1_Cu,conn):return False
 fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu]).get((net,pcbnew.In1_Cu))
 return bool(fill and covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),fill))
result=qualified();expected=a.case=='healthy';print(json.dumps(dict(case=a.case,qualified=result,expected=expected,passed=result==expected,no_saved_native_SOURCE_or_PCB_mutation=True)))
raise SystemExit(result!=expected)
