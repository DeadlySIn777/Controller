"""Frozen ordinary112 routing on only actual SOURCE-anchored filled pieces.

The WIP r04/native import, source allowlist and warning ledger remain unchanged.
The complete failed reference ledger is retained; this grants no whole-net or
whole-board pass. A smaller verified native fill union reaches the same exact
geometric/annulus guard, never an outline or an unanchored same-named island.
"""
from pathlib import Path
import sys,hashlib
import pcbnew
import hardware_route_ordinary_wip_r04 as prior
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_critical_digital_wip_r05 as authority
engine=prior.engine
SOURCE,SOURCE_SHA=prior.SOURCE,prior.SOURCE_SHA
FROZEN_PRIOR_SHA='e2e52046c24f82daa873edf1a202109afe40d2d4e26a3c5d5c408eeb57e722c2'
FROZEN_PIECES_SHA='689736822ad64a0100df56b8102a247c56951931a62c732d80dcde2ca3e3a9ae'
MAPPING=None
AUDITS=[]

def dependencies():
 if engine.sha(prior.__file__)!=FROZEN_PRIOR_SHA or engine.sha(pieces.__file__)!=FROZEN_PIECES_SHA:
  raise ValueError('Frozen ordinary WIP or literal native piece helper changed')
 return {**prior.dependencies(),'literal_native_piece_helper_sha256':FROZEN_PIECES_SHA,'frozen_ordinary_wip_r04_sha256':FROZEN_PRIOR_SHA}

def frozen_review_check(manifest,design,netlist):
 dependencies();evidence=manifest.get('source_review',{})
 if Path(evidence.get('path','')).resolve()!=(engine.ROOT/SOURCE).resolve()or evidence.get('sha256')!=SOURCE_SHA:
  raise ValueError('Only the exact frozen ordinary112 source26 review is accepted')
 proof=pieces.verify_receipt(manifest['plane_review']['path'],INPUT_BOARD,manifest['nets'])
 return {**prior.original_frozen_review_check(manifest,design,netlist),
  'source_anchored_piece_eligibility_only':True,'whole_board_reference_qualification':False,'whole_return_net_qualification':False,
  'full_plane_report_sha256':proof['full_plane_review']['sha256'],'complete_failed_piece_count':len(proof['complete_unanchored_components']),**dependencies()}

class LiteralPieces(pieces.SourceAnchoredPiecesCheck):
 def __init__(self,board,rows):
  if MAPPING is None:raise ValueError('Actual complete source map is not bound')
  super().__init__(board,rows,MAPPING)

def actual_return_check(board,added,rows):
 check=LiteralPieces(board,rows);exact={t.m_Uuid.AsString():t for t in board.GetTracks()};records=[]
 if not set(added)<=set(exact):raise ValueError('Actual added copper UUID absent')
 for u in sorted(added):
  item=exact[u]
  if item.GetNetname()not in rows:raise ValueError('Unreviewed actual route net')
  row=rows[item.GetNetname()];records.append(check.via(item,row)if isinstance(item,pcbnew.PCB_VIA)else check.segment(item,row))
 audit=dict(passed=True,new_copper_items_checked=len(records),items=records,
  actual_signal_via_reference_audits=list(check.audits.values()),eligible_native_pieces_used=check.eligible_piece_audit,
  full_failed_reference_piece_ledger=check.full_native_report['unanchored_components'],
  whole_board_reference_qualification=False,whole_return_net_qualification=False,actual_SOURCE_annuli_required=True,
  physical_signal_integrity_qualified=False,manufacturing_ready=False)
 AUDITS.append(audit);return audit

def install():
 prior.install();engine.frozen_review_check=frozen_review_check;engine.return_corridor_check=actual_return_check
 # The unchanged prepare/stitch algorithms now receive only the smaller set
 # of actual native filled polygons, qualified afresh on each board object.
 prior.fast.strict.prior.ReturnCheck=LiteralPieces

def main():
 global MAPPING,INPUT_BOARD
 dependencies();install()
 if '--baseline-disposition'not in sys.argv:raise ValueError('Exact WIP warning disposition required')
 i=sys.argv.index('--baseline-disposition');disposition=Path(sys.argv[i+1]).resolve();del sys.argv[i:i+2]
 mode=sys.argv[1];out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 if mode=='prepare':
  base=Path(sys.argv[sys.argv.index('--board')+1]).resolve();manifest=Path(sys.argv[sys.argv.index('--manifest')+1]).resolve()
 else:
  prepared=Path(sys.argv[sys.argv.index('--prepared')+1]).resolve();base=prepared/'base.kicad_pcb';manifest=prepared/'manifest.json'
 INPUT_BOARD=base;m=engine.read(manifest);proof=pieces.verify_receipt(m['plane_review']['path'],base,m['nets']);MAPPING=engine.read(proof['source_map']['path'])
 authority.configure(disposition,manifest)
 before=prior.wip.source_clusters(pcbnew.LoadBoard(str(base)));frozen={p:engine.sha(p)for p in(base,manifest,disposition)}
 engine.main();target=out/('prepare.json'if mode=='prepare'else'receipt.json');r=engine.read(target)
 if mode=='import':r.update(prior.wip.clusters_preserved(before,pcbnew.LoadBoard(str(out/'additive-route-candidate.kicad_pcb'))))
 if frozen!={p:engine.sha(p)for p in frozen}:raise ValueError('Actual source/board/warning ledger changed')
 r.update(scope='Exact ordinary112 on SOURCE-anchored native filled pieces only',source_anchored_piece_eligibility_only=True,
  complete_failed_reference_piece_ledger=proof['complete_unanchored_components'],whole_board_reference_qualification=False,whole_return_net_qualification=False,
  dependencies=dependencies(),native_serialization_control_ledger=authority.LEDGER,actual_piece_route_audits=AUDITS,
  exact_warning_disposition_sha256=engine.sha(disposition),original_ordinary_deny_source_class_and_limits_unchanged=True,
  all_native_warning_objects_retained=True,complete_board_DRC_pass=False,manufacturing_ready=False)
 engine.write(target,r)
if __name__=='__main__':main()
