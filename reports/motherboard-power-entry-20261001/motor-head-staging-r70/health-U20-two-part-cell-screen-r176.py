import sys,json,shutil,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity,segment_distance
from hardware_route_local_signals import paths
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
P=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-four-loop-gap-r166');bb=pcbnew.LoadBoard(str(P));fs={f.GetReference():f for f in bb.GetFootprints()};ps={p.GetNumber():mm(p.GetPosition())for p in fs['U11020'].Pads()};n={p.GetNumber():p.GetNetname()for p in fs['U11020'].Pads()};ret={t.m_Uuid.AsString()for t in bb.GetTracks()if any(t.GetNetname()==n[pn]and(pt==mm(t.GetStart())or pt==mm(t.GetEnd()))for pn,pt in ps.items())};r=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text());ret|={v['uuid']for v in r['exact_added_copper']if v['role'].startswith('U11020_own')};print('RETIRE',len(ret),flush=True)
t=parse(without_generated_fills(P.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'U20-two-part-local-retired-screen-r176.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(P.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};uf=fs['U11020'];cf=fs['C11079'];g=FastGeometry(b);rows=[]
for pos in[(339,175),(340,175),(339,177),(340,177)]:
 uf.SetPosition(xy(pos));cf.SetPosition(xy((pos[0]+.8375,pos[1]-.775)))
 if any(intersects(side_box(f),side_box(z),0)for f in[uf,cf]for z in fs.values()if z.GetReference()not in['U11020','C11079']and z.GetLayer()==f.GetLayer()):continue
 # index rebuilt once for this actual two-part pose
 g=FastGeometry(b);pmap={p.GetNumber():p for p in uf.Pads()};cap={p.GetNumber():p for p in cf.Pads()};s=mm(pmap['5'].GetPosition());gn=pmap['2'].GetNetname();ng=pmap['5'].GetNetname();go=mm(cap['2'].GetPosition());cand=[]
 for ix,iy in[(i,j)for i in[0,7,8,9,10,11,12,-7,-8,-9,-10,-11,-12]for j in[0,7,8,9,10,11,12,-7,-8,-9,-10,-11,-12]]:
  for unused in[0]:
   z=(s[0]+ix*.1,s[1]+iy*.1)
   if math.dist(s,z)>1.6:continue
   if not all(g.clear([z,z],ng,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
   fpath=next((v for v in paths(s,z)if g.clear(v,ng,pcbnew.F_Cu,.25)),None)
   bpath=next((v for v in paths(mm(cap['1'].GetPosition()),z)if g.clear(v,ng,pcbnew.B_Cu,.25)),None)
   if not(fpath and bpath):continue
   for jx,jy in[(0,.85),(0,-.85),(.85,0),(-.85,0),(.6,.6),(-.6,.6),(.6,-.6),(-.6,-.6)]:
    q=(z[0]+jx,z[1]+jy)
    if not all(g.clear([q,q],gn,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
    grs=[v for v in paths(go,q)if g.clear(v,gn,pcbnew.B_Cu,.25)];gfs=[None]
    def no_cross(a,c):return all(segment_distance(v,w,x,y)>=.4101 for v,w in zip(a,a[1:])for x,y in zip(c,c[1:]))
    pairs=[(gr,gf)for gr in grs for gf in gfs if no_cross(gr,bpath)]
    if pairs:
     gr,gf=pairs[0];cand.append(dict(power=z,ground=q,powerF=fpath,powerB=bpath,groundF=gf,groundB=gr));break
   if cand:break
  if cand:break
 rows.append(dict(owner_pos=pos,cap_pos=mm(cf.GetPosition()),candidates=cand[:1]));print(rows[-1],flush=True)
(O/'U20-two-part-cell-candidates-r176.json').write_text(json.dumps(dict(retired=sorted(ret),rows=rows),indent=2));print('DONE',flush=True)
