"""Report-only literal native preflight for the U25 local barrel correction."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_local_signals import paths
from hardware_route_logic_return import mm,xy,identity
from hardware_populate_motherboard_pcb import write,sha
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-offland-native-search-r03');assert not O.exists();O.mkdir()
assert sha(B)=='7759cccdb7583e3f195fc89967c73ff6f9e6840b09c76a3cdd405116382332a8'
b=pcbnew.LoadBoard(str(B));cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()}
pin=lambda r,n:next(p for p in fps[r].Pads()if p.GetNumber()==str(n))
pv='0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3';gv='9557a691-472b-4af0-87c3-b0e91cf52409'
ret=cu[gv].GetNetname();supply=cu[pv].GetNetname();removed={}
for u in (pv,gv):
 p=tuple(cu[u].GetPosition())
 for uid,t in cu.items():
  if uid==u or t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname()==cu[u].GetNetname()and(p==tuple(t.GetStart())or p==tuple(t.GetEnd())):removed[uid]=identity(t)
assert set(removed)=={pv,gv,'f05f32fd-1116-432e-afbe-c48a00ed63c0','d5258467-61e7-4fb2-b020-0b89d1d2a04e','501f396f-2ba8-4dcf-980c-3c37bef08384'}
for uid in removed:b.Remove(cu[uid])
g=Geometry(b);os=mm(pin('U11025',5).GetPosition());cs=mm(pin('C11080',1).GetPosition());cr=mm(pin('C11080',2).GetPosition());outputs=[mm(pin('U11025',n).GetPosition())for n in(4,6)]
rows=[];tested=0;stats={'positive_via_clear':0,'positive_F_path_clear':0,'positive_B_path_clear':0,'ground_via_clear':0,'ground_B_path_clear':0}
for x in [round(332.3+i*.05,4)for i in range(31)]:
 for y in [round(191.9+i*.05,4)for i in range(25)]:
  p=(x,y);tested+=1
  if min(math.dist(p,q)for q in outputs)<1.05 or not g.via(p,supply):continue
  stats['positive_via_clear']+=1
  fpath=next((ps for ps in[[os,(x,os[1]),p]]+list(paths(os,p))if g.clear(ps,supply,pcbnew.F_Cu,.25)),None)
  if not fpath:continue
  stats['positive_F_path_clear']+=1
  bpath=next((ps for ps in paths(p,cs)if g.clear(ps,supply,pcbnew.B_Cu,.25)),None)
  if not bpath:continue
  stats['positive_B_path_clear']+=1
  for dx,dy in [(a*.05,z*.05)for a in range(-19,20)for z in range(-19,20)if .7<=math.hypot(a*.05,z*.05)<=1.]:
   q=(round(x+dx,5),round(y+dy,5))
   if math.dist(q,cr)>2 or not g.via(q,ret):continue
   stats['ground_via_clear']+=1
   if math.dist(p,q)<.45:continue
   rp=next((ps for ps in paths(q,cr)if g.clear(ps,ret,pcbnew.B_Cu,.25)),None)
   if not rp:continue
   stats['ground_B_path_clear']+=1
   # Newly proposed leaves and barrels must also clear one another.
   pair_clear=all(__import__('hardware_route_logic_return').distance(q,a,z)>=.25+.125+.15 for a,z in zip(bpath,bpath[1:])) and all(__import__('hardware_route_logic_return').distance(p,a,z)>=.25+.125+.15 for a,z in zip(rp,rp[1:]))
   if not pair_clear:continue
   length=lambda ps:sum(math.dist(a,z)for a,z in zip(ps,ps[1:]))
   rows.append(dict(positive=p,Ground=q,positive_F_path=fpath,positive_B_path=bpath,Ground_B_path=rp,score=length(fpath)+length(bpath)+length(rp),pair_mm=math.dist(p,q),output_pad_min_distance_mm=min(math.dist(p,v)for v in outputs)))
rows.sort(key=lambda r:r['score']);write(O/'search.json',dict(passed=bool(rows),board_sha256=sha(B),removed_for_preflight=removed,tested=tested,stats=stats,actual_pad_positions=dict(owner_positive=os,cap_positive=cs,cap_Ground=cr,actual_outputs=outputs),candidates=rows[:30],native_DRC_required=True,Source_and_reference_and_power_required=True));print(json.dumps(dict(passed=bool(rows),tested=tested,stats=stats,best=rows[:3])),flush=True)
