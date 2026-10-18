import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r120/motor-bank-A-control-repaired-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()}
poses={'U11011':((272,187),0),'C11059':((270.2,185),90),'C11060':((275.25,186.5),0),'R11045':((267,189.5),0),'R11046':((267,204),0),'R11047':((267,187),0),'U11023':((254,208),0),'U11024':((254,213),0),'U11029':((266,208),180),'U11030':((266,213),180),'R11069':((248,207.365),0),'R11073':((273,208.635),180),'R11078':((248,201),0)}
refs=set(poses)|{'U11034','C11085','C11086','R11079'}
from hardware_route_local_signals import GeometryIndex
others={pcbnew.F_Cu:[],pcbnew.B_Cu:[]}
for r,f in fs.items():
 if r not in refs:others[f.GetLayer()].append((r,side_box(f)))
found=[]
for x in range(234,276,2):
 for y in range(203,241,2):
  trial=dict(poses);trial.update({'U11034':((x,y),0),'C11085':((x+3.5,y+2.5),0),'C11086':((x,y-3),180),'R11079':((x+5,y+2.5),0)})
  for r,(p,d)in trial.items():fs[r].SetPosition(xy(p));fs[r].SetOrientationDegrees(d)
  boxes={r:side_box(fs[r])for r in trial};ok=True
  for r,box in boxes.items():
   if any(intersects(box,c,0)for _,c in others[fs[r].GetLayer()]):ok=False;break
   if any(s!=r and fs[s].GetLayer()==fs[r].GetLayer() and intersects(box,c,0)for s,c in boxes.items()):ok=False;break
  if ok:found.append(dict(score=((x-252)**2+(y-196)**2)**.5,poses=trial))
found.sort(key=lambda r:r['score']);Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankB-combined-free-r132.json').write_text(json.dumps(found[:80],indent=2));print('FREE',len(found));print(json.dumps(found[:3],indent=2))
