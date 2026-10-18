import sys,json,hashlib,shutil,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_route_logic_return import identity,pad_identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
B=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r350/motor-bank-B-receiving-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-exact-private-retirement-r376');assert not O.exists();O.mkdir();base=pcbnew.LoadBoard(str(B));base.BuildConnectivity();expected=source_clusters(base);tracks={t.m_Uuid.AsString():identity(t)for t in base.GetTracks()};pad={p.m_Uuid.AsString():pad_identity(p)for p in base.GetPads()};R=json.loads((B.parent/'receipt.json').read_text());added={v['uuid']for v in R['exact_added_copper']};frozen={str(v):sha(v)for v in[B,B.parent/'receipt.json',Path(__file__)]}
new='51f0477f-25ec-4b67-9348-1e886ebb3f7b';keeper='e3d2be03-43de-4635-bcb5-00e0a0924196';assert new in added and keeper not in added and tracks[new][1:]==tracks[keeper][1:];ret={new};old_ret=set();proof=[dict(uuid=new,reason='Exact coincident new IO3 via duplicates retained .50/.20 barrel; retain actual old barrel',identity=tracks[new],retained_exact_peer=keeper)]
allowed_nets={'/LOGIC_GND','/motherboard_power_entry/MOTION_5V_RAW','/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B'};known_base_C79='4b393b84-561e-44d7-a13c-f7dd8ec81ce5';allowed_old_initial={'0431f79d-14ab-4eae-8249-eafbdccc0fe7','8bc78829-90a6-4e9c-a190-9bcaaa46fd1f','a0a9b844-54c1-4d39-bf7b-90a5247eec36','ce228d75-afc6-450a-a6a9-25fa6a65a52b'}
dest=O/'motor-bank-B-native-cleared-candidate.kicad_pcb'
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for f in B.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,O/f.name)
 elif f.name=='fp-lib-table':(O/f.name).write_text(f.read_text().replace('${KIPRJMOD}',B.parent.resolve().as_posix()))
# Retire the complete old dedicated CLR graph once its four exact fitted
# endpoints are confirmed, rather than iterating one obsolete leaf per refill.
original=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/motherboard-health-U19-facing-cell-candidate.kicad_pcb');ob=pcbnew.LoadBoard(str(original));nn='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B';pp={(p.GetParentFootprint().GetReference(),p.GetNumber())for p in ob.GetPads()if p.GetNetname()==nn};assert pp=={('U11029','4'),('R11079','1'),('C11085','1'),('U11034','6')};oldids={t.m_Uuid.AsString()for t in ob.GetTracks()if t.GetNetname()==nn};oldgraphs={u for u in oldids if u in tracks};assert oldgraphs and not oldgraphs&added
for u in sorted(oldgraphs|{'0431f79d-14ab-4eae-8249-eafbdccc0fe7','8bc78829-90a6-4e9c-a190-9bcaaa46fd1f'}):
 ret.add(u);old_ret.add(u);proof.append(dict(uuid=u,reason='Exact old four-endpoint dedicated CLR graph replaced by full actual relocated graph'if u in oldgraphs else'Native r350 explicitly flagged obsolete moved-cell leaf',identity=tracks[u],native_type='reviewed_private_graph_or_explicit_old_leaf'))
frozen[str(original)]=sha(original)
for step in range(3):
 tree=parse(without_generated_fills(B.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];dest.write_text(dump_board(tree));q=pcbnew.LoadBoard(str(dest));pcbnew.ZONE_FILLER(q).Fill(q.Zones());pcbnew.SaveBoard(str(dest),q);q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();assert {p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==pad;clusters_preserved(expected,q)
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/('native-'+str(step)+'.json')),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((O/('native-'+str(step)+'.json')).read_text());issues=[]
 for v in d['violations']:
  ids={i['uuid']for i in v['items']}
  if ids=={known_base_C79}:assert v['type']=='via_dangling';continue
  assert v['type']in['track_dangling','via_dangling'],('Outside physical leaf scope',v)
  for u in ids:assert u in tracks and u not in added and tracks[u][1]in allowed_nets,(u,tracks.get(u));issues.append((u,v['type']))
 if step==0:assert not issues,issues
 if not issues:break
 for u,t in issues:ret.add(u);old_ret.add(u);proof.append(dict(uuid=u,reason='Native explicit obsolete moved-cell leaf; all actual stationary pad clusters separately preserved',identity=tracks[u],native_type=t,iteration=step))
else:raise AssertionError('Bounded old-leaf pruning incomplete')
actual={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert set(tracks)-set(actual)==ret and all(actual.get(u)==v for u,v in tracks.items()if u not in ret);assert all(sha(Path(v))==h for v,h in frozen.items());receipt=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_removed_Cu=proof,exact_removed_old_Cu_count=len(old_ret),all_Source_pad_clusters_and_other_Cu_preserved=True,no_Source_pad_land_pose_or_net_changes=True,native_types=dict(collections.Counter(v['type']for v in d['violations'])),explicit_retained_C79_warning=known_base_C79,native_missing_joins=q.GetConnectivity().GetUnconnectedCount(False),strict_receiving_and_signal_reference_pending=True,manufacturing_ready=False);(O/'receipt.json').write_text(json.dumps(receipt,indent=2));print('PASS',len(old_ret),receipt['native_types'],receipt['native_missing_joins'],flush=True)
