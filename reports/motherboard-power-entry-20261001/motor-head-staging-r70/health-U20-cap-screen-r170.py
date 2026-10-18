import sys,json,shutil,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy
from hardware_route_local_signals import paths
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
P=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-four-loop-gap-r166')
ret={'14852c03-c097-494f-ae1f-0b48afe42f38','2e2763c2-a9c8-4db6-ba48-8748c2edf88b','6479a195-f570-4bd6-a72a-1b4346f69d2a','a7557b84-57f6-401c-8a4b-ffca5422696e','84200ca9-1f0b-4001-9194-b02b62125f07'}
t=parse(without_generated_fills(P.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'U20-cap-local-retired-screen.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(P.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));g=FastGeometry(b);fs={f.GetReference():f for f in b.GetFootprints()};f=fs['C11079'];f.Flip(f.GetPosition(),False);assert f.GetLayer()==pcbnew.F_Cu
u={p.GetNumber():p for p in fs['U11020'].Pads()};s=mm(u['5'].GetPosition());sg=mm(u['2'].GetPosition());res=[]
for ix in range(-16,17):
 for iy in range(-16,17):
  pos=(344+ix*.25,175+iy*.25)
  for a in[0,90,180,270]:
   f.SetOrientationDegrees(a);f.SetPosition(xy(pos));box=side_box(f)
   if any(intersects(box,side_box(z),0)for z in fs.values()if z.GetReference()!='C11079'and z.GetLayer()==f.GetLayer()):continue
   pads={p.GetNumber():p for p in f.Pads()};p,q=mm(pads['1'].GetPosition()),mm(pads['2'].GetPosition())
   if math.dist(s,p)>3.5 or math.dist(sg,q)>4.:continue
   src=next((v for v in paths(s,p)if g.clear(v,u['5'].GetNetname(),pcbnew.F_Cu,.25)),None)
   ground=next((v for v in paths(sg,q)if g.clear(v,u['2'].GetNetname(),pcbnew.F_Cu,.25)),None)
   if src and ground:res.append(dict(pos=pos,angle=a,power=src,ground=ground))
print('CANDIDATES',len(res),flush=True);print(json.dumps(res[:10],indent=2),flush=True);(O/'U20-same-side-cap-candidates.json').write_text(json.dumps(res,indent=2))
