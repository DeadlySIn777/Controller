import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r120/motor-bank-A-control-repaired-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()}
poses={'U11011':((272,187),0),'C11059':((270.2,185),90),'C11060':((275.25,186.5),0),'R11045':((267,189.5),0),'R11046':((267,207),0),'R11047':((267,192.5),0),'U11034':((254.5,209),0),'R11077':((254.5,214),0),'C11085':((259,211.5),0),'C11086':((254.5,206),180),'R11078':((269,236.5),0),'R11079':((260.5,211.5),0),'U11023':((274,242),0),'U11024':((274,247),0),'U11029':((286,242),180),'U11030':((286,247),180),'R11069':((268,241.365),0),'R11073':((293,242.635),180)}
for r,(p,d)in poses.items():fs[r].SetPosition(xy(p));fs[r].SetOrientationDegrees(d)
rows=[]
for r in poses:
 clashes=[s for s,f in fs.items()if s!=r and fs[r].GetLayer()==f.GetLayer()and intersects(side_box(fs[r]),side_box(f),0)]
 rows.append(dict(ref=r,point_mm=poses[r][0],angle=poses[r][1],layer=b.GetLayerName(fs[r].GetLayer()),courtyard_conflicts=clashes));print(rows[-1],flush=True)
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankB-initial-pose-screen-r122.json').write_text(json.dumps(dict(rows=rows,source_unchanged=True,placement_only_unaccepted=True),indent=2))
