import sys,json,math,hashlib,argparse
from pathlib import Path
sys.path.insert(0,str(Path("tools").resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_route_current_delivery_native import sha
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();P=args.board
D=Path("reports/motherboard-pcb-integration-20261001/source26-motor-bank-A-RAW-repair-trial-r89/proposed-exact-delta.json");d=json.loads(D.read_text());b=pcbnew.LoadBoard(str(P));b.BuildConnectivity();c=b.GetConnectivity();ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};ts={t.m_Uuid.AsString():t for t in b.GetTracks()};n="/motherboard_power_entry/MOTION_5V_RAW"
checks=[]
for row in d["changed_copper"]:
 assert json.loads(json.dumps(identity(ts[row["uuid"]])))==row["after"],row["uuid"]
checks.append(dict(exact_changed_copper=len(d["changed_copper"]),all_native_identities_match=True))
via_points=[(272.2,177.7),(272,178.3),(272,179)]
for pt in via_points:
 vs=[t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and math.dist(mm(t.GetPosition()),pt)<1e-6]
 assert len(vs)==1 and vs[0].GetNetname()==n
 v=vs[0];assert v.GetWidth(pcbnew.F_Cu)==500000 and v.GetDrillValue()==200000 and v.GetIsFree()
 con={t.m_Uuid.AsString()for t in c.GetConnectedItems(v)}
 assert ps["U11010","11"].m_Uuid.AsString()in con and ps["C11046","1"].m_Uuid.AsString()in con
 sep=[]
 for q in b.GetTracks():
  if isinstance(q,pcbnew.PCB_VIA)and q!=v:
   gap=math.dist(mm(v.GetPosition()),mm(q.GetPosition()))-(v.GetDrillValue()+q.GetDrillValue())/2e6
   sep.append((gap,q.m_Uuid.AsString()))
 mingap,other=min(sep);assert mingap>=.2495-1e-6,(pt,mingap,other)
 checks.append(dict(actual_barrel_uuid=v.m_Uuid.AsString(),point_mm=pt,source_EP_and_converter_cap_connected=True,native_min_hole_gap_mm=mingap,nearest_other_barrel_uuid=other))
for r,pn in[("C11057","1"),("U11010","3"),("U11010","4"),("U11010","11")]:
 a=ps[r,pn];assert ps["C11046","1"].m_Uuid.AsString()in {t.m_Uuid.AsString()for t in c.GetConnectedItems(a)}
rawlinks=[row for row in d["changed_copper"]if row["after"][6]is None]
rho=1.724e-8*(1+.00393*(85-20));all_current=.9136062160062159;screen=[]
for row in rawlinks:
 def res(v):return rho*math.dist(v[2],v[3])/1e9/((v[5]/1e9)*63e-6)
 before,after=res(row["before"]),res(row["after"]);screen.append(dict(uuid=row["uuid"],width_mm=row["after"][5]/1e6,resistance_before_ohm=before,resistance_after_ohm=after,extra_drop_if_entire_bank_current_a=all_current,extra_drop_v=(after-before)*all_current))
# These two F pieces are low-current input-cap leaves. The B600um join is the
# third loaded branch. Conservatively screen the full bank current in it.
loaded=[s for s in screen if s["width_mm"]>=.6];assert len(loaded)==1
review=dict(board=str(P),board_sha256=sha(P),exact_delta_sha256=sha(D),checks=checks,source_EP_VIN_VBIAS_cap_native_continuity=True,exact_changed_copper_screen=screen,loaded_B_branch_extra_drop_v=loaded[0]["extra_drop_v"],current_screen_conditions={"outer_copper_um":63,"copper_temperature_c":85,"bank_A_current_a":all_current,"physical_DFM_thermal_loaded_qualification":False},all_three_original_power_transitions_preserved=True,physical_guarantee=False)
O=args.out;O.mkdir(exist_ok=False);(O/"receipt.json").write_text(json.dumps(review,indent=2)+"\n");print(json.dumps(review,indent=2))
