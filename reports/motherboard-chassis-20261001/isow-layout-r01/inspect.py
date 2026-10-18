import sys,json
sys.path.insert(0,'tools')
import pcbnew as p
from pathlib import Path
from motherboard_mechanical_audit import graphic_box,body_box,xy
b=p.LoadBoard('reports/motherboard-pcb-integration-20260930/complete-mate-access-r25c/motherboard-mate-access-candidate.kicad_pcb');b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
d=json.loads(Path('hardware/motherboard_comms/design.json').read_text())
print('BLOCKS',d['blocks'])
for r in ['U14812','U14813']+[f'C{i}'for i in list(range(14814,14824))+list(range(14825,14835))]+[r for r,c in d['components'].items()if c['kind']=='BEAD']:
 f=fs[r];ids=set()
 for z in f.Pads():
  ids.update(a.m_Uuid.AsString() for a in b.GetConnectivity().GetConnectedItems(z) if a.Type()in[p.PCB_TRACE_T,p.PCB_VIA_T])
 print(r,xy(f.GetPosition()),f.GetOrientationDegrees(),'CY',graphic_box(f,p.F_CrtYd),'attached_clusterCu',len(ids),d['components'][r]['pins'])
