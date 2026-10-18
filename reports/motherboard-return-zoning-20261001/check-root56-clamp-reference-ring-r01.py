import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_logic_return import xy
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');m=json.loads(Path('reports/motherboard-domains-20261001/source26-r56-r01/domain-map.json').read_text());fill=collect_native_reference_fills(b,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);s=(106.9375,286)
print('C14047 source',[(p['pin'],p['copper_layers'],p['copper_aabb_mm'])for p in m['pads']if p['reference']=='C14047'])
for l in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
 print('Layer',b.GetLayerName(l),'centre',fill['/LOGIC_GND',l].Contains(xy(s)))
 for radius in(.5,.7,1.,1.5,2.):
  points=[(round(s[0]+radius*math.cos(k*math.pi/4),6),round(s[1]+radius*math.sin(k*math.pi/4),6))for k in range(8)]
  print(radius,[fill['/LOGIC_GND',l].Contains(xy(q))for q in points])
