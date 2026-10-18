import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_logic_return import xy,mm
from hardware_zone_motherboard_returns import reference_envelopes,return_net
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r04/motherboard-AO1-secondary-return-candidate.kicad_pcb');m=json.loads(Path('reports/motherboard-domains-20261001/source26-r56-AO1-closed-r01/domain-map.json').read_text());pts=[(399.6,249),(395.4,248.5),(385.6,225)]
for q in pts:
 print('POINT',q,flush=True)
 for z in b.Zones():
  if z.IsOnLayer(pcbnew.In1_Cu)and z.Outline().Contains(xy(q)):
   print('zone',z.m_Uuid.AsString(),z.GetZoneName(),z.GetNetname(),'priority',z.GetAssignedPriority(),'rule',z.GetIsRuleArea(),'fill',z.HasFilledPolysForLayer(pcbnew.In1_Cu)and z.GetFilledPolysList(pcbnew.In1_Cu).Contains(xy(q)),flush=True)
 for p in m['pads']:
  a,y,c,d=p['copper_aabb_mm']
  if a<q[0]+.5 and c>q[0]-.5 and y<q[1]+.5 and d>q[1]-.5:print('local',p['reference'],p['pin'],p['domain'],p['net'],p['copper_layers'],p['copper_aabb_mm'],flush=True)
