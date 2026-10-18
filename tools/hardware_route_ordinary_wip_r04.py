"""Exact ordinary112 execution with actual scoped returns and native controls.

The frozen ordinary r03 allowlist and validator remain authoritative. This
separate WIP executor reuses only the reviewed native placement-only control,
immutable restoration, actual-annulus checker and exact unfinished-warning
gate. It never grants whole-board reference or manufacturing qualification.
"""
from pathlib import Path
import sys
import pcbnew
import hardware_route_selected_additive_r03 as ordinary
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as wip
import hardware_scope_critical_reference_qualification as scope
import hardware_check_return_corridors_r04 as fast

engine=ordinary.prior
SOURCE=Path('reports/motherboard-ordinary-routing-20261001/source26-review-r08/ordinary-source-review.json')
SOURCE_SHA='942497c9dd269455e78d485d1e79b35df74f93776661b1df834c41533cdd20b7'
FROZEN_ORDINARY_SHA='ddc052dc21f4cd467e722d51f0010303e7a0a5007d682311897d974f5b50308b'
FROZEN_AUTHORITY_SHA='49dc6e91cd22c227b0f8368b0650c8ec4bd91dfa501774c226ecd6ee19e0b6aa'
FROZEN_SCOPE_SHA='1a67cd10ead4a848a1810bf0a0a42cee1fe422c8972b818311fb69cc84e12c42'
original_frozen_review_check=engine.frozen_review_check

def dependencies():
 for path,expected in [(ordinary.__file__,FROZEN_ORDINARY_SHA),
                       (authority.__file__,FROZEN_AUTHORITY_SHA),
                       (scope.__file__,FROZEN_SCOPE_SHA),(engine.ROOT/SOURCE,SOURCE_SHA)]:
  if engine.sha(path)!=expected:raise ValueError('Frozen ordinary/authority/scope dependency changed')
 return {**ordinary.checked_dependencies(),**fast.dependencies(),
  'ordinary_source_review_sha256':SOURCE_SHA,'authoritative_import_sha256':FROZEN_AUTHORITY_SHA,
  'scoped_reference_guard_sha256':FROZEN_SCOPE_SHA}

def frozen_review_check(manifest,design,netlist):
 dependencies()
 evidence=manifest.get('source_review',{})
 if Path(evidence.get('path','')).resolve()!=(engine.ROOT/SOURCE).resolve()or evidence.get('sha256')!=SOURCE_SHA:
  raise ValueError('Only the exact frozen ordinary112 source26 review is accepted')
 proof=scope.check(scope.read(manifest['plane_review']['path']),manifest)
 return {**original_frozen_review_check(manifest,design,netlist),**proof,**dependencies()}

def install():
 ordinary.install();fast.dependencies()
 engine.frozen_review_check=frozen_review_check
 engine.return_corridor_check=fast.return_corridor_check
 fast.strict.prior.ReturnCheck=fast.NativeCollectedAnnulusCheck
 engine.merge_tree=authority.merge_tree
 engine.dump=authority.dump_native_board

def main():
 dependencies();install()
 if '--baseline-disposition'not in sys.argv:raise ValueError('Exact full native WIP warning disposition is required')
 i=sys.argv.index('--baseline-disposition');disposition=Path(sys.argv[i+1]).resolve();del sys.argv[i:i+2]
 mode=sys.argv[1];out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 if mode=='prepare':
  base=Path(sys.argv[sys.argv.index('--board')+1]).resolve()
  manifest=Path(sys.argv[sys.argv.index('--manifest')+1]).resolve()
 else:
  prepared=Path(sys.argv[sys.argv.index('--prepared')+1]).resolve()
  base=prepared/'base.kicad_pcb';manifest=prepared/'manifest.json'
 m=engine.read(manifest);scoped=scope.check(scope.read(m['plane_review']['path']),m)
 authority.configure(disposition,manifest)
 before=wip.source_clusters(pcbnew.LoadBoard(str(base)))
 frozen={p:engine.sha(p)for p in (base,manifest,disposition)}
 engine.main()
 target=out/('prepare.json'if mode=='prepare'else'receipt.json');r=engine.read(target)
 if mode=='import':r.update(wip.clusters_preserved(before,pcbnew.LoadBoard(str(out/'additive-route-candidate.kicad_pcb'))))
 if frozen!={p:engine.sha(p)for p in frozen}:raise ValueError('Frozen ordinary source/board/warning ledger changed')
 r.update(scoped,scope='Exact frozen ordinary112 subset only',
  exact_ordinary_source_sha256=SOURCE_SHA,effective_ordinary_wip_executor_sha256=engine.sha(__file__),
  dependencies=dependencies(),native_serialization_control_ledger=authority.LEDGER,
  authoritative_objects_never_normalized=True,
  original_ordinary_deny_source_class_and_limits_unchanged=True,
  exact_warning_disposition_sha256=engine.sha(disposition),all_native_warning_objects_retained=True,
  complete_board_DRC_pass=False,manufacturing_ready=False,physical_SI_qualified=False)
 engine.write(target,r)
if __name__=='__main__':main()
