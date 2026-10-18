"""Repair only proposed ordinary-route bends against actual filled SOURCE reference."""
from pathlib import Path
import sys,json,math,copy,shutil,uuid
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r05 as authority
from hardware_route_owned_bypass_loops_wip_r03 import Geometry
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,segment_distance
e=o.engine;p=Path(__file__).parent;old=p/'actual-source26-root83-In2-batch-r09';out=p/'actual-source26-root83-In2-batch-r11'
out.mkdir(exist_ok=False);src=old/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
b=pcbnew.LoadBoard(str(src));b.BuildConnectivity();o.MAPPING=e.read(old/'fresh-domain-map/domain-map.json');man=e.read(old/'manifest.json');plan=e.read(old/'proposed-groups.json')
check=o.LiteralPieces(b,man['nets']);geo=Geometry(b);native={t.m_Uuid.AsString():t for t in b.GetTracks()};tree=e.parse(src.read_text());nodes={e.value(e.child(n,'uuid')[1]):n for n in e.children(tree,'segment')}
ledger=[];kept=[]
def valid(path,net,layer):
 for a,z in zip(path,path[1:]):
  if math.dist(a,z)<.05:return False
  seg=pcbnew.SEG(xy(a),xy(z))
  for pad,_ in geo.pads.candidates(a,z,.4):
   if pad.IsOnLayer(layer)and pad.GetNetname()!=net and pad.GetEffectiveShape(layer).Collide(seg,pcbnew.FromMM(.30-1e-6)):return False
  for other,s,t,w in geo.tracks[layer].candidates(a,z,.6):
   if other!=net and segment_distance(a,z,s,t)<.1+w/2+.20-1e-6:return False
  track=pcbnew.PCB_TRACK(b);track.SetStart(xy(a));track.SetEnd(xy(z));track.SetWidth(pcbnew.FromMM(.2));track.SetLayer(layer);track.SetNet(b.FindNet(net));kept.append(track)
  try:check.segment(track,man['nets'][net])
  except Exception:return False
 return True
jobs=[(0,'start'),(0,'end'),(1,'end'),(3,'start'),(3,'back'),(5,'back')]
for gi,key in jobs:
 g=plan['groups'][gi];layer=pcbnew.In2_Cu if key=='back'else pcbnew.F_Cu;original=g['back_path_mm']if key=='back'else g[key]['front_path_mm'];start,end=original[0],original[-1]
 candidates=list(paths(start,end))
 # Preserve the pad's first escape direction, then take a diagonal final leg
 # outside the actual receiving via's antipad. No clearance exception added.
 if len(original)>=3:
  first=original[1];d=math.dist(start,first)
  for step in range(1,max(2,int(d/.05))):
   f=step*.05/d
   if f>=1:break
   bend=tuple(round(start[i]+f*(first[i]-start[i]),6)for i in(0,1));candidates.append([start,bend,end])
  last=original[-2];d=math.dist(end,last)
  for extension in(.2,.4,.6,.8,1,1.5,2):
   bend=tuple(round(end[i]+(d+extension)/d*(last[i]-end[i]),6)for i in(0,1))
   candidates.extend([line+[end]for line in paths(start,bend)])
 candidates=[line for line in candidates if line[-1]==end and sum(math.dist(a,z)for a,z in zip(line,line[1:]))<=50]
 chosen=next((line for line in candidates if valid(line,g['net'],layer)),None)
 if chosen is None:raise ValueError(f'No exact-return-safe repair for {g["source_pair"]} {key}')
 ids=[]
 for a,z in zip(original,original[1:]):
  matches=[u for u in g['signal_UUIDs']if u in native and native[u].Type()!=pcbnew.PCB_VIA_T and native[u].GetLayer()==layer and (tuple(native[u].GetStart()),tuple(native[u].GetEnd()))==(tuple(xy(a)),tuple(xy(z)))]
  assert len(matches)==1,(g['source_pair'],a,z,matches);ids.extend(matches)
 template=copy.deepcopy(nodes[ids[0]]);newids=[]
 for index,(a,z)in enumerate(zip(chosen,chosen[1:])):
  node=copy.deepcopy(template);uid=ids[index]if index<len(ids)else str(uuid.uuid4());e.child(node,'uuid')[1]=e.q(uid);e.child(node,'start')[1:]=[str(v)for v in a];e.child(node,'end')[1:]=[str(v)for v in z]
  if uid in nodes:tree[tree.index(nodes[uid])]=node
  else:tree.append(node)
  newids.append(uid)
 for uid in ids[len(newids):]:tree.remove(nodes[uid])
 g['signal_UUIDs']=[u for u in g['signal_UUIDs']if u not in ids]+newids;g['new_copper_UUIDs']=g['signal_UUIDs']+g['ground_UUIDs']
 if key=='back':g['back_path_mm']=chosen
 else:g[key]['front_path_mm']=chosen
 ledger.append(dict(pair=g['source_pair'],section=key,old_path_mm=original,new_path_mm=chosen,old_UUIDs=ids,new_UUIDs=newids,actual_reference_and_geometry_precheck=True))
dest=out/src.name;dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in old.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name in('fp-lib-table','manifest.json','piece-eligibility.json'):shutil.copyfile(f,out/f.name)
plan['new_copper_UUIDs']=[u for g in plan['groups']for u in g['new_copper_UUIDs']];plan['return_bend_repairs']=ledger;plan['repair_source_board_sha256']=e.sha(src)
e.write(out/'proposed-groups.json',plan);e.write(out/'bounded-bend-repairs.json',dict(passed=True,input_board_sha256=e.sha(src),proposed_board_sha256=e.sha(dest),repairs=ledger,only_unadopted_proposed_segments_changed=True,native_DRC_and_refill_pending=True,manufacturing_ready=False))
print(json.dumps(dict(repaired_paths=len(ledger),newCu=len(plan['new_copper_UUIDs']))))

