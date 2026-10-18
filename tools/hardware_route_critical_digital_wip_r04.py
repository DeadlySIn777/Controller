"""Frozen critical WIP execution with literal scoped reference enforcement."""
from pathlib import Path
import sys,hashlib
import hardware_route_critical_digital_wip_r03 as prior
import hardware_scope_critical_reference_qualification as scope
FROZEN_WIP_R03_SHA='dcb8788a34f8d2df0168c335fff8a94d3e4047673a962f003db5df088a9b070a'
FROZEN_SCOPE_SHA='1a67cd10ead4a848a1810bf0a0a42cee1fe422c8972b818311fb69cc84e12c42'
def main():
 if scope.sha(scope.__file__)!=FROZEN_SCOPE_SHA:raise ValueError('Frozen literal scope guard changed')
 if hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()!=FROZEN_WIP_R03_SHA:
  raise ValueError('Frozen prior critical WIP executor changed')
 mode=sys.argv[1]
 if mode=='prepare':manifest=Path(sys.argv[sys.argv.index('--manifest')+1])
 else:manifest=Path(sys.argv[sys.argv.index('--prepared')+1])/'manifest.json'
 m=scope.read(manifest);binding=scope.check(scope.read(m['plane_review']['path']),m)
 prior.main()
 out=Path(sys.argv[sys.argv.index('--out')+1]);receipt=out/('prepare.json'if mode=='prepare'else'receipt.json')
 r=scope.read(receipt);r.update(binding,effective_scoped_critical_executor_sha256=scope.sha(__file__),
  scope_guard_sha256=scope.sha(scope.__file__),manufacturing_ready=False)
 prior.prior.write(receipt,r)
if __name__=='__main__':main()
