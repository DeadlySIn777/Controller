import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy
from hardware_route_current_delivery_native import sha
path=Path('reports/motherboard-power-entry-20261001/entry-return-barrel-jog-r33/entry-return-jog-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(path));b.BuildConnectivity();z=next(z for z in b.Zones()if z.GetZoneName()=='FA_RETURN_ACTUAL_CMOS_BARREL_SLOT');poly=z.GetFilledPolysList(pcbnew.B_Cu);rows=[]
for i in range(35):
 x=376.825+(i-17)*.05;segments=[];start=None
 for j in range(2001):
  y=143+j*.002;active=poly.Contains(xy((x,y)))
  if active and start is None:start=y
  if not active and start is not None:segments.append((start,y-.002));start=None
 if start is not None:segments.append((start,147))
 ws=[v[1]-v[0]for v in segments];a=[(w/25.4*1000)*(63/25.4)for w in ws];amps=[.048*10**.44*v**.725 for v in a];rows.append(dict(x=x,actual_ligaments_y=segments,widths_mm=ws,total_width_mm=sum(ws),ipc2221_conditional_each_a=amps,parallel_sum_current_screen_a=sum(amps)))
print(json.dumps(dict(board_sha256=sha(path),zone_uuid=z.m_Uuid.AsString(),profile=rows,min_total_width_mm=min(v['total_width_mm']for v in rows),min_parallel_sum_a=min(v['parallel_sum_current_screen_a']for v in rows)),indent=2))
