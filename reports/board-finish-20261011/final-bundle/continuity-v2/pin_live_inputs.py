"""Freeze hashes of the current saved r07/r08/native continuity evidence."""
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import qualify_bundle as v1
from finish_bridge_proof import manifest, check_summary

R07 = '0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
INTEGRATE = Path('Z:/pcb-runs/claude-finish/integrate')
MEASURE = INTEGRATE / 'measure/r07-ripup-signals-1'
V1 = 'eda72ec6559194a403dad2fed5fc78ae2d82520cebf2bb3fa88096e872344bc1'


def main():
    out = HERE / 'live-inputs.json'
    if out.exists():
        raise ValueError('Existing pins are preserved')
    reads = v1.ReadSet()
    v1.tracked(reads, HERE.parent / 'qualify_bundle.py', V1)
    paths = {'revision_board': INTEGRATE / 'revs/r07-ripup-signals-1.kicad_pcb',
             'r08_board': INTEGRATE / 'revs/r08-power-low-0p3mm.kicad_pcb',
             'live_board': INTEGRATE / 'board.kicad_pcb',
             'applied_board': INTEGRATE / 'work/r07-ripup-signals-1/applied.kicad_pcb',
             'copy_board': MEASURE / 'copy/board.kicad_pcb',
             'partitions': MEASURE / 'partitions.json', 'manifest': MEASURE / 'sha256.txt',
             'summary': MEASURE / 'summary.json', 'raw_drc': MEASURE / 'drc.json',
             'drc_log': MEASURE / 'drc.log', 'report': MEASURE / 'report.json'}
    paths.update({name: MEASURE / 'copy' / name for name in v1.PROJECT_NAMES})
    for role, path in paths.items():
        data = reads.read(path)
        if role.endswith('_board'):
            v1.require(v1.digest(data) == R07, 'Saved/current board identity differs: ' + role)
    partitions = reads.json(paths['partitions'])
    v1.require(partitions['sha256'] == R07 and partitions['refilled'] is True,
               'Saved native r07 partitions differ')
    v1.require(Path(partitions['board']).resolve() == paths['copy_board'].resolve(),
               'Saved r07 partitions were not measured on exact native copy')
    members = manifest(reads.read(paths['manifest']))
    v1.require(members['board.kicad_pcb'] == R07, 'Native r07 manifest board differs')
    for name in v1.PROJECT_NAMES:
        v1.tracked(reads, paths[name], members[name])
    drc = check_summary(reads.json(paths['raw_drc']), partitions, reads.json(paths['summary']), R07)
    v1.require(drc['errors'] == 0, 'Native r07 has unresolved ordinary DRC errors')
    reads.verify()
    receipt = {'schema': 'live-r07-continuity-inputs-v1', 'live_sha256': R07,
               'qualifier_v1_sha256': V1, 'saved_native_refilled': True,
               'native_manifest': members, 'native_drc': drc,
               'paths': {role: {'path': str(path.resolve()), 'sha256': reads.hashes[str(path.resolve())]}
                         for role, path in paths.items()},
               'native_jobs': 0, 'gpu_jobs': 0, 'live_changed': False,
               'scope': 'Host pins of saved actual native r07 receipts and exact current/r08/revision geometry; no fresh native measurement'}
    out.write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'pins': str(out), 'sha256': sha256(out.read_bytes()).hexdigest(),
                      'r07_sha256': R07, 'path_roles': len(paths),
                      'r07_joins': partitions['pad_island_joins'], 'r07_api': partitions['api_unconnected_count']}))


if __name__ == '__main__':
    main()
