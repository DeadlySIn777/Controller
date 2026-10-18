"""Retire exact native-confirmed dangling branches while retaining every pad cluster.

Required schematic nets remain required. No pad is changed or marked NC. Only
explicitly reviewed old dangling track/via branches may be removed; all actual
stationary physical-pad connectivity and every other native copper item stay
exact, with fresh native DRC proof after each bounded pruning iteration.
"""
import argparse,json,shutil,subprocess,collections
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value
from hardware_route_logic_return import identity
from hardware_apply_probe_pin_delta import clusters
from hardware_populate_motherboard_pcb import sha,write
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in('board','review','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();review=json.loads(a.review.read_text())
 if review['board_sha256']!=sha(a.board)or not review['reviewed_reason']or not review['initial_dangling_UUIDs']:raise ValueError('Exact current native branch review required')
 if a.out.exists():raise ValueError('Fresh immutable output required')
 b=pcbnew.LoadBoard(str(a.board));old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};allowed=set(review['affected_native_nets']);before=clusters(b,set(),allowed);removed=set();proof=[]
 a.out.mkdir(parents=True);dest=a.out/'native-dangling-cleared-candidate.kicad_pcb';shutil.copyfile(a.board,dest)
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(a.board.with_suffix(suffix),dest.with_suffix(suffix))
 for f in a.board.parent.iterdir():
  if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
  elif f.name=='fp-lib-table':shutil.copy2(f,a.out/f.name)
 for attempt in range(24):
  report=a.out/('drc-'+str(attempt)+'.json');run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(report),str(dest)],capture_output=True,text=True);(a.out/('drc-'+str(attempt)+'.txt')).write_text(run.stdout+run.stderr)
  if run.returncode:raise ValueError('Native DRC did not execute')
  d=json.loads(report.read_text())
  if d.get('ignored_checks')or any(v['type']not in('track_dangling','via_dangling')for v in d['violations']):raise ValueError('Native issue outside reviewed dangling scope')
  ids={i['uuid']for v in d['violations']for i in v['items']}
  if not ids:break
  if attempt==0 and ids!=set(review['initial_dangling_UUIDs']):raise ValueError('Initial native flagged scope differs')
  current=pcbnew.LoadBoard(str(dest));actual={t.m_Uuid.AsString():identity(t)for t in current.GetTracks()}
  for uid in ids:
   if uid not in old or actual.get(uid)!=old[uid]or old[uid][1]not in allowed:raise ValueError('Flagged item is not exact reviewed old affected-net copper')
  proof.extend(dict(uuid=i['uuid'],native_type=v['type'],description=v['description'],iteration=attempt,before=old[i['uuid']])for v in d['violations']for i in v['items'])
  tree=parse(dest.read_text());tree[:]=[v for v in tree if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and value(child(v,'uuid')[1])in ids)];dest.write_text(dump(tree)+'\n');removed.update(ids)
  if clusters(pcbnew.LoadBoard(str(dest)),set(),allowed)!=before:raise ValueError('Native branch retirement changes a stationary actual-pad cluster')
 else:raise ValueError('Native branch retirement bound exceeded')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
 if set(old)-set(actual)!=removed or any(actual.get(u)!=v for u,v in old.items()if u not in removed):raise ValueError('Unrelated copper changed')
 if clusters(fresh,set(),allowed)!=before:raise ValueError('Final stationary pad cluster differs')
 write(a.out/'receipt.json',dict(input_sha256={str(a.board):sha(a.board),str(a.review):sha(a.review)},board_sha256=sha(dest),exact_removed_old_copper=proof,all_stationary_actual_pad_clusters_and_other_copper_retained=True,no_pad_net_or_NC_changed=True,native_DRC_regular=len(d['violations']),ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False))
 print(dict(old_dangling_pieces_retired=len(removed),native_DRC_regular=len(d['violations']),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),board_sha256=sha(dest)))
if __name__=='__main__':main()
