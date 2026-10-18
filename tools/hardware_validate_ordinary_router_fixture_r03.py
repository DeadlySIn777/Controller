"""Run the frozen actual DSN/SES fixture with the reviewed annulus guard.

The prior implementation stays immutable. This wrapper installs only the
reviewed stronger return checker and records its exact dependencies alongside
the real native routing receipt. A toy fixture is not full-board routing proof.
"""
from pathlib import Path
import hashlib,json,sys
import hardware_route_selected_additive_r03 as router
import hardware_validate_ordinary_router_fixture as prior

FROZEN_FIXTURE_SHA='db76593d9d90e372fcc184306f528872f507e22889b71e1a4f254c4ce102dbd6'

def main():
    frozen=Path(prior.__file__)
    if hashlib.sha256(frozen.read_bytes()).hexdigest()!=FROZEN_FIXTURE_SHA:
        raise ValueError('Frozen actual interchange fixture changed')
    dependencies=router.checked_dependencies();router.install()
    prior.main()
    out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
    path=out/'receipt.json';receipt=json.loads(path.read_text(encoding='utf8'))
    current=[Path(__file__),Path(router.__file__),
             Path(__file__).with_name('hardware_check_return_corridors_r02.py')]
    receipt['input_hashes'].update({str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in current})
    receipt.update(router_version='r03 actual annuli wrapper',
        stronger_return_dependencies=dependencies,
        actual_flashed_and_native_connected_reference_annuli_required=True,
        unchanged_frozen_fixture_tool_sha256=FROZEN_FIXTURE_SHA)
    path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
