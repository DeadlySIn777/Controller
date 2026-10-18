"""Issued critical prototype executor with independently guarded fast references."""
from pathlib import Path
import hashlib,sys
import hardware_route_critical_digital_additive as prior
import hardware_check_return_corridors_r04 as fast
FROZEN_CRITICAL_R01_SHA='d1d4a4fab9d449bdf6703fac66fa82ad5a6731ca826a402c40cb78e9f5102216'
def main():
 if hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()!=FROZEN_CRITICAL_R01_SHA:
  raise ValueError('Frozen exact critical prototype executor changed')
 fast.dependencies()
 # Isolated process substitutions, never changes to historical files.
 prior.fast=fast
 prior.main()
 out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 p=out/('prepare.json'if sys.argv[1]=='prepare'else'receipt.json')
 r=prior.prior.read(p);r.update(effective_critical_executor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  frozen_critical_executor_r01_sha256=FROZEN_CRITICAL_R01_SHA,
  original_geometric_dependency_independently_guarded=True)
 prior.prior.write(p,r)
if __name__=='__main__':main()
