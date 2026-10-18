import sys,json,math,time
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r326/debug.kicad_pcb');g=FastGeometry(b);n='/motherboard_power_entry/MOTOR_FEED_CLEAR_SOURCE_B';s=(271.075,150);e=(353.15,178.385)
print('VIA',[(pt,all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]))for pt in[s,e]],flush=True)
for l in[pcbnew.In2_Cu,pcbnew.In3_Cu]:
 t=time.time();pp=g.grid(s,e,n,l,.2,step=.5,padding=25,max_nodes=140000);print(b.GetLayerName(l),round(time.time()-t,1),pp,flush=True)
