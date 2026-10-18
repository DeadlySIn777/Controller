import sys,json,math,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_route_local_signals import paths
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=Path('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r502/new-private-B-controls-retired.kicad_pcb');b=pcbnew.LoadBoard(str(p));g=m.InnerGeometry(b);ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};a=mm(ps['U11034','6'].GetPosition());n=ps['U11034','6'].GetNetname();hits=[]
for ix in range(-20,21):
 for iy in range(-20,21):
  q=(round(a[0]+ix*.1,6),round(a[1]+iy*.1,6))
  if math.dist(q,a)>.2 and math.dist(q,a)<1.8:
   sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
   if any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()):continue
   if not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
   if any(isinstance(t,pcbnew.PCB_VIA)and math.dist(q,mm(t.GetPosition()))<.4495 for t in b.GetTracks()):continue
   direct=next((p for p in paths(q,a)if g.clear(p,n,pcbnew.F_Cu,.25)),None)
   if direct is None:continue
   hits.append(dict(position=q,distance=math.dist(q,a),Fpath=direct))
hits.sort(key=lambda x:x['distance']);o=Path('reports/motherboard-power-entry-20261001/Source27-fast-receiving-search-r504');o.mkdir(exist_ok=False);(o/'candidates.json').write_text(json.dumps(hits,indent=2));print(json.dumps(hits[:30],indent=2))
