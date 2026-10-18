"""Fresh replay of an immutable staged IS2 record/DIC proposal; no live writes."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot():
    return {p.relative_to(HERE).as_posix(): sha(p) for p in HERE.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts
            and p.name not in ('bundle-manifest.json', 'freeze-receipt.json')}

def main(out, distro, inventory):
    if out.exists():
        raise RuntimeError('fresh output required')
    out.mkdir(parents=True)
    before = snapshot()
    declared = json.loads((HERE / 'bundle-manifest.json').read_text())['files']
    integrity = before == declared
    start = time.time()
    env = os.environ.copy()
    env['CNC3_WSL_DISTRO'] = distro
    rows = []
    stages = [
        ('actual_IS2_page_and_two_C_drivers', None),
        ('mutation_foreign_session_cannot_consume', 'foreign_consumes'),
        ('mutation_CMD_cannot_consume', 'CMD_consumes'),
        ('mutation_bad_CRC_cannot_queue', 'bad_CRC_queues'),
        ('mutation_fake_index_capability_rejected', 'fake_index'),
    ]
    for name, mutation in stages:
        runner='run_profile.py'
        category='actual fresh Verilated serial RTL + actual compiled C driver; compiled runtime-rejected mutation' if mutation else 'actual fresh Verilated serial RTL + original and explicit IS2 C drivers'
        row = {'name': name, 'runner': runner, 'evidence_type': category, 'status': 'NOT_RUN'}
        if not integrity:
            row.update(status='FAIL', reason='exact frozen bundle hash mismatch')
        elif inventory:
            row['reason'] = 'inventory only'
        else:
            command = [sys.executable, '-X', 'utf8', str(HERE / runner), '--out', str(out / name)]
            if mutation: command += ['--mutation', mutation]
            print('RUN ' + name, flush=True)
            try:
                completed = subprocess.run(command, env=env, capture_output=True,
                                           text=True, encoding='utf8', errors='replace', timeout=1200)
                (out / (name + '-command.log')).write_text(completed.stdout + completed.stderr,
                                                         encoding='utf8', newline='\n')
                receipt = out / name / 'receipt.json'
                data = json.loads(receipt.read_text()) if receipt.is_file() else {}
                good = completed.returncode == 0 and data.get('status') == 'PASS'
                if 'inputs_unchanged' in data:
                    good = good and data['inputs_unchanged'] is True
                row.update(status='PASS' if good else 'FAIL', exit_code=completed.returncode,
                           receipt=str(receipt), receipt_sha256=sha(receipt) if receipt.is_file() else None)
            except Exception as exception:
                row.update(status='FAIL', reason=repr(exception))
            print(row['status'] + ' ' + name, flush=True)
        rows.append(row)
        (out / 'checkpoint.json').write_text(json.dumps({'stages': rows, 'bundle_integrity': integrity}, indent=2) + '\n')
    unchanged = before == snapshot()
    counts = {s: sum(r['status'] == s for r in rows) for s in ('PASS', 'FAIL', 'BLOCKED', 'NOT_RUN')}
    passed = integrity and unchanged and counts['PASS'] == len(stages)
    status = 'PASS' if passed else 'NOT_RUN' if inventory and integrity and unchanged else 'FAIL'
    report = {
        'status': status, 'counts': counts, 'stages': rows, 'exact_inputs': before,
        'bundle_integrity': integrity, 'inputs_unchanged': unchanged,
        'bundle_manifest_sha256': sha(HERE / 'bundle-manifest.json'),
        'duration_seconds': round(time.time() - start, 3),
        'scope_flags': {
            'actual_compiled_C_to_actual_simulated_RTL_SPI_CAP3': any(r['name']=='actual_IS2_page_and_two_C_drivers' and r['status']=='PASS' for r in rows),
            'explicit_IS2_integrated12_class0_four_encoder_inventory': True,
            'PROFILE_COMPLETE': False,
            'ACTUAL_physical_providers_identity_or_full_output_authority': False,
            'commissioning_ARM_12joint_HAL_physical_qualification': False,
            'product_rate_frame_layout_shared_sources_changed': False,
        },
        'open_dependencies': [
            'actual complete safety/IOL1/factory/provider qualification before installed qualification or CONFIGURE/ARM',
            'real identity/config/diagnostic master support remains separate; no invented card identity',
            'actual C driver measured watchdog selftests and explicit reference/continuity commissioning',
            'real LinuxCNC HAL, complete I/O/event/output implementation, family fit/timing and physical validation',
        ],
    }
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': status, 'counts': counts, 'report': str(out / 'report.json')}), flush=True)
    return 0 if status in ('PASS', 'NOT_RUN') else 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--wsl-distro', default='GarciaMechBuilder')
    parser.add_argument('--inventory', action='store_true')
    arguments = parser.parse_args()
    raise SystemExit(main(arguments.out.resolve(), arguments.wsl_distro, arguments.inventory))
