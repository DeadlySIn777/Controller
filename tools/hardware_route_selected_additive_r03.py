"""Selected additive router with strict actual return-annulus qualification.

Frozen r02 remains unchanged. The scoped wrapper retains its native identity,
source/plane hash, DRC, endpoint, ordinary allowlist and stitch-geometry gates.
"""
from pathlib import Path
import hardware_route_selected_additive_r02 as prior
from hardware_check_return_corridors_r02 import return_corridor_check
FROZEN_R02_SHA='cd2e65be1819c1de7eae628dea2f65ec2f12b290eb283d01bc562174f4190908'
STRICT_CHECKER_SHA='3496b5598390833c3cf71fd8dade26817a28ca1a7b208bba6af80fd1a0e00682'
original_dependencies=prior.checked_dependencies

def checked_dependencies():
    d=original_dependencies()
    if prior.sha(Path(prior.__file__))!=FROZEN_R02_SHA:
        raise ValueError('Frozen additive router r02 changed')
    checker=Path(__file__).with_name('hardware_check_return_corridors_r02.py')
    if prior.sha(checker)!=STRICT_CHECKER_SHA:
        raise ValueError('Reviewed actual-annulus return checker changed')
    return {**d,'actual_annulus_checker_sha256':STRICT_CHECKER_SHA,'frozen_r02_router_sha256':FROZEN_R02_SHA}

def install():
    checked_dependencies()
    prior.checked_dependencies=checked_dependencies
    prior.return_corridor_check=return_corridor_check

def main():
    install();prior.main()

if __name__=='__main__':main()
