import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT94-health-U26-local-r182/literal-retired-input.kicad_pcb');g=FastGeometry(b);n='/motherboard_motors/FIELD_GND';pv=(329.2,191.2);rows=[]
for ix in range(-20,21):
 for iy in range(-20,21):
  q=(pv[0]+ix*.05,pv[1]+iy*.05);d=math.dist(pv,q)
  if .78<=d<=1. and all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):rows.append((q,d))
Path('reports/motherboard-power-entry-20261001/ROOT94-health-four-loop-gap-r166/U26-local-return-points-r187.json').write_text(json.dumps(rows,indent=2));print('GROUND',len(rows),rows[:25],flush=True)
