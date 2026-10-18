"""Replay Claude's independent vector check on the original r06 stitch plan.

Read-only source geometry observation; no planner, GPU, board or native job.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = Path('Z:/pcb-runs/claude-finish/integrate/work/r06-stitch-plane-pads-2')
AUDITOR = Path('Z:/pcb-runs/claude-finish/agent-work/verify-stitch3/scripts/plan_exact_check.py')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    if (HERE / 'receipt.json').exists() or (HERE / 'exact.json').exists():
        raise ValueError('Fresh immutable audit output required')
    geom = WORK / 'copy/geom.json'
    plan = WORK / 'plan3.json'
    source = WORK / 'copy/source.kicad_pcb'
    revision = Path('Z:/pcb-runs/claude-finish/integrate/revs/r05-stitch-plane-pads-1.kicad_pcb')
    if source.read_bytes() != revision.read_bytes():
        raise ValueError('Historical r06 planning board differs from r05 revision')
    geometry = json.loads(geom.read_bytes())
    if not any(p.get('cls','').startswith('DOM_') for p in geometry['pads']):
        raise ValueError('Historical geometry lacks domain classes')
    inputs = [Path(__file__), AUDITOR, geom, plan, source, revision, WORK / 'copy/source.kicad_pro',
              WORK / 'copy/source.kicad_dru', WORK / 'pad-mask.json', WORK / 'remove_new_errors.json',
              Path('C:/Python314/python.exe')]
    identities = {str(p.resolve()): sha(p) for p in inputs}
    (HERE / 'auditor.py').write_bytes(AUDITOR.read_bytes())
    command = ['C:/Python314/python.exe', (HERE / 'auditor.py').as_posix(), geom.as_posix(),
               plan.as_posix(), (HERE / 'exact.json').as_posix(), '--classes', geom.as_posix(),
               '--pad-mask', (WORK / 'pad-mask.json').as_posix()]
    (HERE / 'inputs.json').write_text(json.dumps({'identities':identities,'command':command},indent=2)+'\n')
    started = time.time()
    with (HERE / 'audit.log').open('w',encoding='utf-8') as log:
        run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if run.returncode or not (HERE / 'exact.json').is_file():
        raise ValueError('Historical independent vector audit failed')
    if any(sha(p) != digest for p,digest in identities.items()):
        raise ValueError('Historical inputs/tool changed during audit')
    exact = json.loads((HERE / 'exact.json').read_bytes())
    receipt = {'verdict':'READ_ONLY_VECTOR_REPLAY_COMPLETE','evidence_class':'Host vector geometry; no native execution',
        'seconds':round(time.time()-started,3), 'planned':exact['planned'],
        'stitches_with_vector_violations':exact['stitches_with_violations'], 'by_type':exact['by_type'],
        'inputs':identities, 'native_original_removal_report':json.loads((WORK / 'remove_new_errors.json').read_bytes()),
        'limits':['Original geometry has no embedded board hash; historical source-copy equality and classes bound separately',
                  'Auditor is original Claude tool; its coverage/rounding and geometry exporter limits remain',
                  'No change to original planner or board; no GPU/native/current/return/DFM proof']}
    (HERE / 'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k in ('verdict','seconds','planned','stitches_with_vector_violations','by_type')}))


if __name__ == '__main__':
    main()
