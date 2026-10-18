"""Independent vector rejection before a ROOT106 raster stitch plan is saved.

Scope is a geometric proposal guard, not source anchoring/current/native proof.
The native no-loss/DRC gate still decides acceptance of an applied board.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_plan(geometry_path, plan, output, pad_mask=''):
    geometry_path, output = Path(geometry_path), Path(output)
    geometry = json.loads(geometry_path.read_bytes())
    if geometry.get('bbox') != [-0.05, -0.05, 450.05, 235.05]:
        raise ValueError('Independent stitch guard supports the explicit ROOT106 450x235 geometry only')
    domains = {}
    for pad in geometry['pads']:
        if pad.get('net'):
            domain = pad.get('cls', '').split(',')[0]
            if pad['net'] in domains and domains[pad['net']] != domain:
                raise ValueError('Contradictory domain classes')
            domains[pad['net']] = domain
    if not any(domain.startswith('DOM_') for domain in domains.values()):
        raise ValueError('Exact guard requires geometry from the matching domain-class project')
    roles = set()
    for item in plan:
        domain = domains.get(item['net'], '')
        if not (domain.startswith('DOM_') or domain == 'NC_ISOLATE'):
            raise ValueError('Planned net has no explicit isolated-domain class')
        role = (item['ref'], item['pad'])
        if role in roles:
            raise ValueError('Duplicate planned physical pad role')
        roles.add(role)
        values = [item['d'], item['drill'], item['stub_w'], *item['via'], *item['pad_xy']]
        if not all(math.isfinite(v) for v in values) or item['d'] < .5 or item['drill'] < .2 or (item['d']-item['drill'])/2 < .15-1e-9 or item['stub_w'] <= 0:
            raise ValueError('Unsupported or invalid stitch dimensions')
    helper = Path(__file__).with_name('stitch_vector_audit.py')
    proposal = Path(str(output)+'.vector-proposal.json')
    report = Path(str(output)+'.vector-report.json')
    log = Path(str(output)+'.vector.log')
    receipt_path = Path(str(output)+'.vector-guard.json')
    frozen = {str(p.resolve()): digest(p) for p in [geometry_path, helper, Path(__file__), Path(sys.executable)]}
    if pad_mask:
        frozen[str(Path(pad_mask).resolve())] = digest(pad_mask)
    proposal.write_text(json.dumps({'plan':plan},indent=1)+'\n',encoding='utf-8')
    frozen[str(proposal.resolve())] = digest(proposal)
    command = [sys.executable, str(helper), str(geometry_path), str(proposal), str(report), '--classes', str(geometry_path)]
    if pad_mask:
        command += ['--pad-mask', str(pad_mask)]
    with log.open('w',encoding='utf-8') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode or not report.is_file():
        raise ValueError('Independent vector stitch check did not complete')
    if any(digest(path) != expected for path, expected in frozen.items()):
        raise ValueError('Vector guard input/helper changed during execution')
    check = json.loads(report.read_bytes())
    if check['planned'] != len(plan) or len(check['rows']) != len(plan):
        raise ValueError('Vector result does not cover every planned stitch')
    accepted, rejected = [], []
    for item, row in zip(plan, check['rows']):
        if any(item[key] != row[key] for key in ('ref','pad','net','layer','via')):
            raise ValueError('Vector result has a wrong physical proposal identity')
        if row['viol']:
            rejected.append({'proposal':item,'vector_violations':row['viol']})
        else:
            accepted.append(item)
    if len(rejected) != check['stitches_with_violations']:
        raise ValueError('Vector rejection accounting differs')
    receipt = {'verdict':'VECTOR_PROPOSAL_FILTER_COMPLETE','planned':len(plan),'accepted':len(accepted),
        'rejected':rejected,'input_sha256':frozen,'vector_report_sha256':digest(report),
        'scope':'Independent vector clearance/landing/mask/hole observations; no native/GPU execution',
        'limits':['No planner raster rebuild or source-anchored return/current proof',
                  'Original vector geometry exporter and coverage limits remain',
                  'Current matching project, reservations, DRC, pad partitions and electrical gates remain required']}
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tool':'stitch_exact_guard','planned':len(plan),'accepted':len(accepted),'rejected':len(rejected),'receipt':str(receipt_path)}),flush=True)
    return accepted
