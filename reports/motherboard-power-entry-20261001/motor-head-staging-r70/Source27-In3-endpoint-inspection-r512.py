import sys,json,importlib.util,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r510/debug.kicad_pcb');g=m.InnerGeometry(b);n='/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B';p=(263.199999,155.4);q=(267.9,155.05)
for a in[p,q]:
 print('POINT',a)
 print('LAYERS',[(b.GetLayerName(l),g.clear([a,a],n,l,.25))for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]])
 for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:print('LEG',dx,dy,g.clear([a,(a[0]+dx*.5,a[1]+dy*.5)],n,pcbnew.In3_Cu,.25))
 print('NEAR',[(t.m_Uuid.AsString(),t.GetNetname(),b.GetLayerName(t.GetLayer()),mm(t.GetStart()),mm(t.GetEnd()),pcbnew.ToMM(t.GetWidth()))for t in b.GetTracks()if t.IsOnLayer(pcbnew.In3_Cu)and min(math.dist(mm(t.GetStart()),a),math.dist(mm(t.GetEnd()),a))<1.5])
