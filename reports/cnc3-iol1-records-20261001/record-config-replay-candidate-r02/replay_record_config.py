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
        ('same_C_signature_record_config_and_ARM', 'run_record_config.py',
         'actual host Python/Ed25519; same compiled C with sanitizers; four ARM ELF/bin; linker overflow negative; separate source inspection'),
        ('actual_SPI_record_config', 'run_record_spi.py',
         'actual simulated SPI edges into the same staged C, explicit disconnected GPIO fixtures'),
        ('compiled_authority_and_integrity_mutations', 'run_mutations.py',
         'seven compiled C runtime-rejected mutations and executed Python cryptographic provenance mutation'),
    ]
    for name, runner, category in stages:
        row = {'name': name, 'runner': runner, 'evidence_type': category, 'status': 'NOT_RUN'}
        if not integrity:
            row.update(status='FAIL', reason='exact frozen bundle hash mismatch')
        elif inventory:
            row['reason'] = 'inventory only'
        else:
            command = [sys.executable, '-X', 'utf8', str(HERE / runner), '--out', str(out / name)]
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
            'actual_simulated_SPI_record_config': any(r['name'] == 'actual_SPI_record_config' and r['status'] == 'PASS' for r in rows),
            'actual_fitted_four_ARM_targets_compiled': any(r['name'] == 'same_C_signature_record_config_and_ARM' and r['status'] == 'PASS' for r in rows),
            'proposed_IS2_record_IDENT_supplement_not_adopted': True,
            'real_manufacturer_trust_provisioning': False,
            'actual_flash_program_erase_ECC_MMIO_DMA_IRQ_execution': False,
            'commercial_ACTIVE_output_ARM_CAP3_HAL': False,
            'physical_qualification_product_ratings_changed': False,
        },
        'open_dependencies': [
            'coordinated actual host/master IDENT/config framing adoption and provisioned-major handling',
            'real factory SWD record programming, page WRP/BOR/IWDG option readback and power interruption/ECC qualification',
            'actual manufacturer trust registry, calibration/factory records and compatibility policy',
            'loaded GPIO/IRQ/DMA/poll timing, full actual I/O qualification and independent safe ACTIVE transition',
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
