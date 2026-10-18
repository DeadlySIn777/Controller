"""Prepare a distinct exact project clone; native execution requires explicit --run.

Default preparation starts no native process and produces no connectivity proof.
Do not run until root approves the same-project rebind/engine audit.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
FINISH = HERE.parent
OLD = FINISH.parent / 'routing-resume-20261011'
sys.path.insert(0, str(OLD))
from finish_bridge_proof import ReadSet, digest, library_inventory, require
from native_bound_partitions import file_hashes

NATIVE = Path('C:/Program Files/KiCad/10.0/bin')
BINARIES = {'native_python': NATIVE / 'python.exe', 'kicad_cli': NATIVE / 'kicad-cli.exe',
            'pcbnew_python': NATIVE / 'Lib/site-packages/pcbnew.py',
            'pcbnew_extension': NATIVE / 'Lib/site-packages/_pcbnew.pyd'}
TOOLS = Path('Z:/pcb-runs/claude-finish/tools')
SLOTS = {'shared': 'heavy.sh', 'main': 'heavym.sh', 'test': 'heavyt.sh'}


def hash_bindings(reads, paths):
    return {str(Path(path).resolve()): digest(reads.read(path)) for path in paths}


def verify_bindings(reads, bindings):
    for path, expected in bindings.items():
        require(digest(reads.read(path)) == expected, 'frozen binding changed: ' + path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--project-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--slot', choices=sorted(SLOTS), required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    board_path, project_dir, out = args.board.resolve(), args.project_dir.resolve(), args.out.resolve()
    require(not out.exists(), 'new run output must be absent')
    require(project_dir not in out.parents, 'output cannot be created inside original project source')
    require(board_path.is_file() and project_dir.is_dir(), 'native board/project source unavailable')
    project_source = project_dir / 'board.kicad_pro.good'
    if not project_source.exists():
        project_source = project_dir / 'board.kicad_pro'
    require(project_source.is_file(), 'exact native project file unavailable')
    for name in ('board.kicad_dru', 'sch.net', 'fp-lib-table'):
        require((project_dir / name).is_file(), 'frozen project component missing: ' + name)
    reads = ReadSet()
    source_inventory = file_hashes(project_dir)
    source_paths = [project_dir / relative for relative in source_inventory] + [board_path]
    source_bindings = hash_bindings(reads, source_paths)
    tools = [Path(__file__), HERE / 'native_bound_partitions.py', OLD / 'finish_bridge_proof.py',
             TOOLS / SLOTS[args.slot], TOOLS / 'net_partitions.py']
    tool_bindings = hash_bindings(reads, tools)
    binary_bindings = {role: {'path': str(path.resolve()), 'sha256': digest(reads.read(path))}
                       for role, path in BINARIES.items()}
    out.mkdir()
    clone = out / 'copy'
    shutil.copytree(project_dir, clone)
    (clone / 'board.kicad_pcb').write_bytes(reads.read(board_path))
    (clone / 'board.kicad_pro').write_bytes(reads.read(project_source))
    libraries = library_inventory(clone, reads)
    clone_inventory = file_hashes(clone)
    require(digest((clone / 'board.kicad_pcb').read_bytes()) == source_bindings[str(board_path)], 'source board clone differs')
    require(digest((clone / 'board.kicad_pro').read_bytes()) == source_bindings[str(project_source)], 'source project clone differs')
    reads.verify()
    inputs = {'schema': 'explicit-bound-partitions-run-v1', 'prepared_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_board': str(board_path), 'source_board_sha256': source_bindings[str(board_path)],
              'source_project_directory': str(project_dir), 'source_project_files': source_inventory,
              'source_files': source_bindings, 'clone_files': clone_inventory, 'libraries': libraries,
              'tools': tool_bindings, 'native_binaries': binary_bindings, 'slot': args.slot,
              'native_execution_authorized_by_this_command': args.run,
              'source_adoption': False, 'manufacturing_ready': False,
              'custom_rule_engine_full_equivalence': 'NOT_VERIFIED',
              'limits': ['Same-project explicit rebind must be reviewed before --run',
                         'A matching bound class/global state is not proof of custom-rule engine equivalence',
                         'Native DRC and bound before/after comparison require separate qualified receipts']}
    manifest_path = out / 'inputs.json'
    manifest_path.write_text(json.dumps(inputs, indent=2) + '\n', encoding='utf-8')
    manifest_sha = digest(manifest_path.read_bytes())
    (out / 'preparation.json').write_text(json.dumps({'state': 'PREPARED_ONLY' if not args.run else 'NATIVE_REQUESTED',
                                                      'inputs_sha256': manifest_sha, 'native_jobs_started': 0,
                                                      'adopted': False}, indent=2) + '\n', encoding='utf-8')
    if not args.run:
        print(json.dumps({'state': 'PREPARED_ONLY', 'inputs_sha256': manifest_sha, 'native_jobs_started': 0}))
        return 0
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    command = ['C:/Program Files/Git/usr/bin/sh.exe', str(TOOLS / SLOTS[args.slot]), 'kicad',
               str(BINARIES['native_python']), str(HERE / 'native_bound_partitions.py'),
               '--board', str(clone / 'board.kicad_pcb'), '--manifest', str(manifest_path),
               '--manifest-sha256', manifest_sha, '--out', str(out / 'partitions.json'), '--refill']
    with (out / 'native.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, env=env, cwd=clone, stdout=log, stderr=subprocess.STDOUT, check=False)
    require(result.returncode == 0, 'native bound producer failed: ' + str(result.returncode))
    final = ReadSet()
    require(digest(final.read(manifest_path)) == manifest_sha, 'saved manifest bytes changed')
    require(json.loads(final.read(manifest_path)) == inputs, 'saved manifest differs from run inputs')
    require(file_hashes(project_dir) == source_inventory, 'original project tree changed')
    require(file_hashes(clone) == clone_inventory, 'native project clone changed')
    verify_bindings(final, source_bindings)
    verify_bindings(final, tool_bindings)
    verify_bindings(final, {rec['path']: rec['sha256'] for rec in binary_bindings.values()})
    require(library_inventory(clone, final) == libraries, 'effective native library inventory changed')
    parts = final.json(out / 'partitions.json')
    require(parts['sha256'] == inputs['source_board_sha256'] and parts['refilled'] is True, 'native partition source/refill differs')
    require(parts['manifest_sha256'] == manifest_sha, 'native producer manifest differs')
    final.verify()
    receipt = {'verdict': 'BOUND_STATE_REFILL_PRODUCED_ONLY', 'source_board_sha256': inputs['source_board_sha256'],
               'inputs_sha256': manifest_sha, 'partitions_sha256': digest(final.read(out / 'partitions.json')),
               'observed_file_hashes': final.hashes, 'native_binaries': binary_bindings,
               'all_source_clone_library_and_tool_files_unchanged': True, 'adopted': False, 'manufacturing_ready': False,
               'custom_rule_engine_full_equivalence': 'NOT_VERIFIED', 'fresh_drc': 'NOT_EXECUTED',
               'bound_before_after_partition_guard': 'SEPARATE_RECEIPT_REQUIRED'}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': receipt['verdict'], 'source_board_sha256': inputs['source_board_sha256']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
