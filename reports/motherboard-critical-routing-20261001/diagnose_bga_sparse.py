import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
import hardware_check_return_corridors_r04 as fast
from hardware_check_return_corridors import uid
from hardware_route_selected_additive import corridor_polygon
p=Path('reports/motherboard-critical-routing-20261001/source26-BGA-native-access-r02/sparse_outer')
b=pcbnew.LoadBoard(str(p/'actual-F256-package-access.kicad_pcb'));r=json.loads((p/'review.json').read_text());check=fast.NativeCollectedAnnulusCheck(b,r['manifest_rows']);out=[]
for t in b.GetTracks():
 if t.GetNetname()not in r['manifest_rows']:continue
 row=r['manifest_rows'][t.GetNetname()]
 try:proof=check.via(t,row)if isinstance(t,pcbnew.PCB_VIA)else check.segment(t,row)
 except ValueError as exc:proof={'error':str(exc)}
 out.append({'uuid':uid(t),'net':t.GetNetname(),'via':isinstance(t,pcbnew.PCB_VIA),'start':pcbnew.ToMM(t.GetStart()),'end':pcbnew.ToMM(t.GetEnd()),'layer':b.GetLayerName(t.GetLayer()),'proof':proof})
print(json.dumps(out,indent=2))
