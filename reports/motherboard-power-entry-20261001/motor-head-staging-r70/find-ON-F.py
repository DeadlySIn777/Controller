import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-head-feed-r74/rejected-debug.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()};p={(r,v.GetNumber()):v for r,f in fs.items()for v in f.Pads()};g=FastGeometry(b)
for r,s in [('U11010','U11032'),('U11011','U11034')]:
 n=p[r,'5'].GetNetname();start=mm(p[s,'5'].GetPosition());end=mm(p[r,'5'].GetPosition());print('TRYF',r,start,end,flush=True);pp=g.grid(start,end,n,pcbnew.F_Cu,.2,step=.5,padding=35,max_nodes=65000);print('RESULT',r,pp,flush=True)
 if pp:Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/'+r+'-F-path.json').write_text(json.dumps(pp))
