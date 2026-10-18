"""Frozen exact nonempty checker plus independent original geometric hash guard.

The prior native geometry/annulus implementation is preserved byte-for-byte.
This revision closes the standalone entry-point dependency guard; it does not
change polygons, via exceptions, source anchoring or electrical eligibility.
"""
from pathlib import Path
import hashlib
import hardware_check_return_corridors_r03 as prior
strict=prior.strict
collector=prior.collector
FROZEN_R03_SHA='ce2cadab5d5ce10e7d61bd62cbf42053ed9c7330f3136ea2cc3d48fef15abee0'
def dependencies():
 p=Path(prior.__file__)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=FROZEN_R03_SHA:
  raise ValueError('Frozen exact nonempty checker changed')
 d=prior.dependencies()
 p=Path(strict.prior.__file__)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=strict.FROZEN_GEOMETRIC_CHECKER_SHA:
  raise ValueError('Frozen original geometric return checker changed')
 return dict(**d,frozen_nonempty_checker_r03_sha256=FROZEN_R03_SHA,
  original_geometric_checker_sha256=strict.FROZEN_GEOMETRIC_CHECKER_SHA)
class NativeCollectedAnnulusCheck(prior.NativeCollectedAnnulusCheck):
 def __init__(self,board,rows):
  dependencies();super().__init__(board,rows)
def return_corridor_check(board,added,rows):
 dependencies();r=prior.return_corridor_check(board,added,rows)
 r['independent_original_geometric_dependency_guard']=True
 return r
