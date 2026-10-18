import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
from hardware_route_current_delivery_native import sha
P=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r216/motor-health-U26-cell-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-drill-review-r220.json');assert not O.exists();b=pcbnew.LoadBoard(str(P));r=json.loads((P.parent/'receipt.json').read_text());ts={t.m_Uuid.AsString():t for t in b.GetTracks()};rows=[]
for row in r['exact_added_copper']:
 t=ts[row['uuid']]
 if not isinstance(t,pcbnew.PCB_VIA):continue
 v=mm(t.GetPosition());radius=pcbnew.ToMM(t.GetDrillValue())/2;hits=[];nearest=None
 for pad in b.GetPads():
  if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  c=mm(pad.GetPosition());an=math.radians(pad.GetOrientationDegrees());dx=v[0]-c[0];dy=v[1]-c[1];lx=dx*math.cos(an)+dy*math.sin(an);ly=-dx*math.sin(an)+dy*math.cos(an);s=mm(pad.GetSize());gap=math.hypot(max(abs(lx)-s[0]/2,0),max(abs(ly)-s[1]/2,0))-radius
  if nearest is None or gap<nearest['drill_edge_gap_mm']:nearest=dict(ref=pad.GetParentFootprint().GetReference(),pin=pad.GetNumber(),drill_edge_gap_mm=gap)
  if gap<0:hits.append([pad.GetParentFootprint().GetReference(),pad.GetNumber(),gap])
 rows.append(dict(uuid=row['uuid'],role=row['role'],point_mm=v,nearest_conservative_SMD_land=nearest,drilled_barrel_intersections=hits))
res=dict(board_sha256=sha(P),all_added_conventional_drills_outside_fitted_SMD_lands=all(not r['drilled_barrel_intersections']for r in rows),rows=rows,Source_ground_continuity_explicitly_pending=True);O.write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2));assert res['all_added_conventional_drills_outside_fitted_SMD_lands']
