"""Apply the two frozen ISO1212 RTHR source corrections to a native PCB copy.

Only those actual resistor pad nets and their invalid one-ended old branches
may change. Every other physical-pad cluster, land, pose and copper item stays
exact. Corrected required field loops remain explicit unrouted work.
"""
import argparse,json,collections,copy,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_route_logic_return import identity
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def clusters(b,excluded,nets):
 b.BuildConnectivity();ps={p.m_Uuid.AsString():p for p in b.GetPads()if p.m_Uuid.AsString()not in excluded and p.GetNetname()in nets}
 return{u:sorted({u}|{q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)if isinstance(q,pcbnew.PAD)and q.m_Uuid.AsString()in ps})for u,p in ps.items()}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in('board','adoption','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 source=json.loads(a.adoption.read_text());rows=source['exact_native_pin_changes']
 if {(v['ref'],v['pin'])for v in rows}!={('R14069','2'),('R14072','2')}or not source['all_other_native_pin_nets_preserved']:raise ValueError('Exact frozen source24 two-pad correction required')
 b=pcbnew.LoadBoard(str(a.board));fps={f.GetReference():f for f in b.GetFootprints()};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in b.GetPads()};changes=[];excluded=set();nets=set();removed=set()
 for row in rows:
  p=next(p for p in fps[row['ref']].Pads()if p.GetNumber()==row['pin'])
  if p.GetNetname()!=row['old']or not b.FindNet(row['new']):raise ValueError('Exact actual old/new probe nets differ')
  excluded.add(p.m_Uuid.AsString());nets.update((row['old'],row['new']))
  attached=[t for t in b.GetTracks()if t.GetNetname()==row['old']and(p.HitTest(t.GetStart())or p.HitTest(t.GetEnd())or t.HitTest(p.GetPosition()))]
  # The independent all-stationary-pad cluster proof below prevents a shared
  # trunk from being retired merely because it touches the changed resistor.
  if len(attached)!=1 or isinstance(attached[0],pcbnew.PCB_VIA):raise ValueError('Probe branch requires a separate reviewed shared-copper transaction')
  removed.add(attached[0].m_Uuid.AsString());changes.append(dict(**row,pad_uuid=p.m_Uuid.AsString(),retired_invalid_branch_uuid=attached[0].m_Uuid.AsString()))
 before=clusters(b,excluded,nets)
 tree=parse(a.board.read_text())
 for f in children(tree,'footprint'):
  ref=value(next(v[2]for v in children(f,'property')if value(v[1])=='Reference'))
  for row in changes:
   if ref!=row['ref']:continue
   p=next(v for v in children(f,'pad')if value(v[1])==row['pin'])
   child(p,'net')[1]=json.dumps(row['new'])
 tree[:]=[v for v in tree if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and value(child(v,'uuid')[1])in removed)]
 a.out.mkdir(parents=True);dest=a.out/'probe-source-reconciled-candidate.kicad_pcb';dest.write_text(dump(tree)+'\n')
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(a.board.with_suffix(suffix),dest.with_suffix(suffix))
 for f in a.board.parent.iterdir():
  if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
  elif f.name=='fp-lib-table':shutil.copy2(f,a.out/f.name)
 run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);(a.out/'drc.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native DRC did not execute')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
 if clusters(fresh,excluded,nets)!=before:raise ValueError('Source correction changes any stationary actual-pad cluster')
 actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
 if set(old)-set(actual)!=removed or any(actual.get(u)!=v for u,v in old.items()if u not in removed):raise ValueError('Unrelated actual copper changed')
 for p in fresh.GetPads():
  u=p.m_Uuid.AsString();ref,pin,net,position,land=pads[u]
  wanted=next((r['new']for r in changes if r['pad_uuid']==u),net)
  if (p.GetNetname(),tuple(p.GetPosition()),pad_template(p))!=(wanted,position,land):raise ValueError('Actual source land/position/net outside two-pad correction')
 d=json.loads((a.out/'drc.json').read_text())
 if d.get('ignored_checks'):raise ValueError('Ignored native checks')
 write(a.out/'receipt.json',dict(input_sha256={str(a.board):sha(a.board),str(a.adoption):sha(a.adoption)},board_sha256=sha(dest),exact_two_probe_source_pin_changes=changes,exact_retired_old_copper=sorted(removed),all_other_physical_pad_clusters_lands_poses_and_copper_preserved=True,native_DRC_regular=len(d['violations']),native_DRC_types=dict(collections.Counter(v['type']for v in d['violations'])),ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False))
 print(dict(source_pins_changed=2,old_invalid_branches_removed=len(removed),native_DRC_regular=len(d['violations']),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),board_sha256=sha(dest)))
if __name__=='__main__':main()
