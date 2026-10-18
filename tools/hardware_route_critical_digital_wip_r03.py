"""Exact critical routing with a separate immutable unfinished-warning ledger.

Existing native warnings remain in every JSON/receipt; no ignored checks,
errors or new warnings are admitted. This permits concrete scoped routing while
unrelated retained feeds/returns are still being finished. Every prior native
source-pad cluster and all frozen additive source/land/copper proofs stay gates.
The clean-baseline critical executors are preserved without changes.
"""
from pathlib import Path
import json,sys,subprocess,hashlib
import pcbnew
import hardware_route_critical_digital_additive_r02 as clean
import hardware_route_owned_bypass_loops_wip_r03 as wip
prior=clean.prior.prior
WIP_GUARD_SHA='8afdeab38cf3a55ab7f8418d4d4f93b14c375f2a704bbd70ac4c7264ca254917'

def source_clusters(board):
 board.BuildConnectivity();found=set();groups=[]
 for p in board.GetPads():
  ident=p.m_Uuid.AsString()
  if not p.GetNumber()or not p.IsOnCopperLayer()or ident in found:continue
  ids={v.m_Uuid.AsString()for v in board.GetConnectivity().GetConnectedItems(p)
   if v.Type()==pcbnew.PCB_PAD_T and v.GetNumber()and v.IsOnCopperLayer()}
  ids.add(ident);found.update(ids);groups.append(ids)
 return groups

def clusters_preserved(before,after):
 after.BuildConnectivity();pads={p.m_Uuid.AsString():p for p in after.GetPads()if p.GetNumber()and p.IsOnCopperLayer()}
 for group in before:
  first=next(iter(group))
  if first not in pads:raise ValueError('Actual retained source pad is missing')
  ids={v.m_Uuid.AsString()for v in after.GetConnectivity().GetConnectedItems(pads[first])if v.Type()==pcbnew.PCB_PAD_T}
  ids.add(first)
  if not group<=ids:raise ValueError('Actual prior joined source-pad cluster fragmented')
 return dict(passed=True,all_prior_native_source_pad_clusters_preserved=True,prior_clusters=len(before))

def configure(disposition,manifest):
 if hashlib.sha256(Path(wip.__file__).read_bytes()).hexdigest()!=WIP_GUARD_SHA:
  raise ValueError('Frozen scoped WIP warning guard changed or is not issued')
 d=prior.read(disposition);m=prior.read(manifest)
 if d.get('board_sha256')!=m['board_sha256']:
  raise ValueError('Exact WIP warning ledger is not bound to the reviewed board')
 # The reviewed routine validates the complete allowed native warning objects,
 # not just counts, categories or a generic permission to tolerate warnings.
 known=wip.reviewed_wip_warnings(dict(violations=d.get('known_unresolved_native_warnings',[]),ignored_checks=[]),d,m['board_sha256'])
 def native_drc(board,out,name,refill=False):
  args=[str(prior.CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all']
  if refill:args+=['--refill-zones','--save-board']
  p=out/(name+'.json');r=subprocess.run(args+['--output',str(p),str(board)],capture_output=True,text=True,encoding='utf8',errors='replace')
  (out/(name+'.txt')).write_text(r.stdout+r.stderr,encoding='utf8')
  if r.returncode or not p.is_file():raise ValueError('Actual native DRC did not execute')
  actual=prior.read(p);new=wip.new_route_defects(actual,known)
  if new:raise ValueError('Actual new native defect or error rejected; full JSON retained')
  return dict(exit_code=r.returncode,regular_violations=len(actual['violations']),
   known_unresolved_native_warnings_retained=actual['violations'],ignored_checks=[],
   complete_board_DRC_pass=not actual['violations'],new_route_DRC_defects=[],
   reported_unconnected_items=len(actual.get('unconnected_items',[])),
   warning_disposition_sha256=prior.sha(disposition),manufacturing_ready=False)
 prior.native_drc=native_drc
 return d

def main():
 if '--baseline-disposition'not in sys.argv:raise ValueError('Exact frozen WIP baseline disposition is required')
 i=sys.argv.index('--baseline-disposition');disposition=Path(sys.argv[i+1]).resolve();del sys.argv[i:i+2]
 mode=sys.argv[1];out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 if mode=='prepare':
  base=Path(sys.argv[sys.argv.index('--board')+1]).resolve()
  manifest=Path(sys.argv[sys.argv.index('--manifest')+1]).resolve()
 else:
  prepared=Path(sys.argv[sys.argv.index('--prepared')+1]).resolve()
  base=prepared/'base.kicad_pcb';manifest=prepared/'manifest.json'
 configure(disposition,manifest);before=source_clusters(pcbnew.LoadBoard(str(base)))
 frozen=dict(disposition=prior.sha(disposition),manifest=prior.sha(manifest),baseline=prior.sha(base))
 clean.main()
 target=out/('prepare.json'if mode=='prepare'else'receipt.json');r=prior.read(target)
 if mode=='import':
  r.update(clusters_preserved(before,pcbnew.LoadBoard(str(out/'additive-route-candidate.kicad_pcb'))))
 if frozen!=dict(disposition=prior.sha(disposition),manifest=prior.sha(manifest),baseline=prior.sha(base)):
  raise ValueError('Frozen critical WIP source/ledger changed during routing')
 r.update(wip_critical_executor_sha256=prior.sha(Path(__file__)),
  frozen_warning_guard_sha256=WIP_GUARD_SHA,exact_warning_disposition_sha256=frozen['disposition'],
  complete_board_DRC_pass=False,all_native_warning_objects_retained=True,
  scoped_prototype_only=True,manufacturing_ready=False)
 prior.write(target,r)
if __name__=='__main__':main()
