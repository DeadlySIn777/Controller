"""Search actual two-section In2 path around the rejected old IO3 feature."""
from pathlib import Path
import sys,json,math,copy,uuid,shutil,subprocess
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent)]
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r05 as authority
import check_io3_backbone_preservation_r07 as power
from hardware_route_owned_bypass_loops_wip_r03 import Geometry
from hardware_route_logic_return import mm,xy,segment_distance
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import corridor_polygon
e=o.engine;root=Path(__file__).parent
source=root/'actual-source26-root87-In2-extended-r20'
src=source/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
assert e.sha(src)=='52a11507a617c76bd369163d748dda760271ebaf9aad8e74aa1c96113d479d79'
base=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb')
out=root/'actual-source26-root87-DI7-detour-r24';out.mkdir(exist_ok=False)
plan=e.read(source/'proposed-groups.json');manifest=e.read(source/'manifest.json');assert len(plan['groups'])==1
g=plan['groups'][0];name=g['net'];row=manifest['nets'][name]
b=pcbnew.LoadBoard(str(src));b.BuildConnectivity();geo=Geometry(b)
o.MAPPING=e.read('reports/motherboard-domains-20261001/source26-root87-In2-r20-r01/domain-map.json');check=o.LiteralPieces(b,manifest['nets'])
original=pcbnew.LoadBoard(str(base))
fill=collect_native_reference_fills(original,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]
core=power.duplicate(fill);core.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
opening=power.duplicate(core);opening.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opening.BooleanIntersection(fill);opening.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
narrow=power.subtract(fill,opening)
wire='bce4f002-c30b-46ab-8381-2582466642d8';old=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==wire)
start,end=mm(old.GetStart()),mm(old.GetEnd());assert old.GetNetname()==name and old.GetLayer()==pcbnew.In2_Cu
def clear(points):
 for p,q in zip(points,points[1:]):
  segment=pcbnew.SEG(xy(p),xy(q))
  for pad,_ in geo.pads.candidates(p,q,.4):
   if pad.IsOnLayer(pcbnew.In2_Cu)and pad.GetNetname()!=name and pad.GetEffectiveShape(pcbnew.In2_Cu).Collide(segment,pcbnew.FromMM(.30)):return False
  for other,a,z,w in geo.tracks[pcbnew.In2_Cu].candidates(p,q,.8):
   if other!=name and segment_distance(p,q,a,z)<.1+w/2+.20-1e-6:return False
  proposed=corridor_polygon(tuple(xy(p)),tuple(xy(q)),pcbnew.FromMM(.31));proposed.BooleanIntersection(narrow)
  if proposed.OutlineCount():return False
  for zone in geo.keepouts:
   if zone.IsOnLayer(pcbnew.In2_Cu)and zone.GetDoNotAllowTracks():
    hit=corridor_polygon(tuple(xy(p)),tuple(xy(q)),pcbnew.FromMM(.1));hit.BooleanIntersection(zone.Outline())
    if hit.OutlineCount():return False
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(pcbnew.In2_Cu);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(xy(p));t.SetEnd(xy(q))
  try:check.segment(t,row)
  except ValueError:return False
 return True
candidates=[]
for x in(112.,112.5,113.,113.5,114.,114.5,115.,115.5,116.,110.,109.,108.):
 for y in(205.545183,205.,204.5,204.,203.5,203.,202.5,202.,201.):
  path=[start,(x,y),end]
  if min(math.dist(start,(x,y)),math.dist(end,(x,y)))>.8:candidates.append(path)
candidates.sort(key=lambda path:sum(math.dist(p,q)for p,q in zip(path,path[1:])))
chosen=next((path for path in candidates if clear(path)),None)
e.write(out/'search.json',dict(before_board_sha256=e.sha(src),actual_old_narrow_feature_avoidance_mm=.31,actual_candidate_count=len(candidates),chosen=chosen,full_refill_and_power_proof_required=True))
if chosen is None:raise ValueError('No actual clear two-section detour; no native candidate emitted')
tree=e.parse(src.read_text());node=next(t for t in e.children(tree,'segment')if e.value(e.child(t,'uuid')[1])==wire)
newid=str(uuid.uuid4());second=copy.deepcopy(node)
def point(node,which,p):e.child(node,which)[1:]=[format(v,'.6f')for v in p]
point(node,'end',chosen[1]);point(second,'start',chosen[1]);e.child(second,'uuid')[1]=e.q(newid);tree.append(second)
dest=out/src.name;dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in source.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
g['signal_UUIDs'].append(newid);g['new_copper_UUIDs'].append(newid);plan['new_copper_UUIDs'].append(newid);g['back_path_mm']=chosen
plan['bounded_proposed_repair']=dict(prior_candidate_sha256=e.sha(src),changed_proposed_UUID=wire,added_UUID=newid,source_base_unchanged=True,power_guard_unchanged=True)
e.write(out/'proposed-groups.json',plan);shutil.copyfile(source/'manifest.json',out/'manifest.json')
with(out/'drc-command.txt').open('w')as log:
 r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--all-track-errors','--severity-all','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
print(json.dumps(dict(command_exit=0,chosen=chosen,new_copper=8,board_sha256=e.sha(dest),adopted=False)))
