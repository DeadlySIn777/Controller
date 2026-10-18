import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board
from hardware_route_logic_return import mm,xy
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_local_signals import paths
B=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-pose-screen-r274/literal-retired-U19-local-input.kicad_pcb');t=parse(B.read_text());t=[v for v in t if not(isinstance(v,list)and v and v[0]=='via'and value(child(v,'uuid')[1])=='448060d2-6859-4acf-bfe0-75f7029b605a')];D=B.parent/'literal-retired-U19-obsolete-source-Ground.kicad_pcb';D.write_text(dump_board(t));b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};fs['U11019'].SetPosition(xy((343,175)));fs['U11019'].SetOrientationDegrees(180);fs['C11078'].SetPosition(xy((342.1625,175.775)));fs['C11078'].SetOrientationDegrees(-90);ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};g=FastGeometry(b);ground=ps['U11019','2'].GetNetname();positive=ps['U11019','5'].GetNetname()
for q,n in [((343.2,176.8),positive),((344,176.8),ground),((344.5875,175),ground),((341.4125,176.55),ground)]:print('VIA',q,all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]))
for a,z,n,l in[((342.1625,175),(343,176.8),positive,pcbnew.F_Cu),((342.1625,175),(343,176.8),positive,pcbnew.B_Cu),((343,176.8),(345.85,178),positive,pcbnew.B_Cu),((342.1625,176.55),(341.4125,176.55),ground,pcbnew.B_Cu)]:print('PATH',a,z,b.GetLayerName(l),[p for p in paths(a,z)if g.clear(p,n,l,.25)][:2])
for cap in ['C11081']:
 p=ps[cap,'2'];n=p.GetNetname();x,y=mm(p.GetPosition());good=[]
 for dx,dy in[(.9625,.60),(1.05,.60),(1.1,.5),(1.2,.75),(-1.1,.75)]:
  q=(x+dx,y+dy)
  if all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):good.append(dict(point=q,paths=[s for s in paths((x,y),q)if g.clear(s,n,pcbnew.B_Cu,.25)][:1]))
 print('CAP',cap,good)


