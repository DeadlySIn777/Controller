"""Read-only Claude handoff coverage inventory; writes only this local receipt."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
EXT = Path('Z:/pcb-runs/claude-finish')


def file_record(path, mode):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data), 'review_mode': mode}


def json_record(path):
    result = file_record(path, 'structured outcome/provenance fields inspected; individual raw geometry/records not exhaustively read')
    data = json.loads(path.read_bytes())
    if isinstance(data, list):
        result['records'] = len(data)
        result['status_counts'] = dict(Counter(item.get('status', item.get('kind', 'UNKNOWN'))
                                             for item in data if isinstance(item, dict)))
        result['revision_board_hashes'] = sorted({item['revision']['board'] for item in data
                if isinstance(item, dict) and isinstance(item.get('revision'), dict)
                and isinstance(item['revision'].get('board'), str)})
    else:
        result['top_level_keys'] = list(data)
    return result


def md_record(path):
    result = file_record(path, 'handoff intent/outcome/coverage and revision identifiers inspected')
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    result['headings'] = [line for line in lines if line.startswith('#')][:24]
    result['outcomes'] = [line for line in lines if line.startswith('**Verdict:')
                          or re.match(r'- \d+ (FAIL|NOT_ROUTED|NOT_RUN|required test)', line)]
    return result


def records(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield {'path': value['path'], 'sha256': value['sha256']}
        for item in value.values():
            yield from records(item)
    elif isinstance(value, list):
        for item in value:
            yield from records(item)


def main():
    names = subprocess.run(['rg', '--files', '--hidden', '--no-ignore', str(EXT)],
                           capture_output=True, text=True, check=True).stdout.splitlines()
    notes = ['integrate/STATUS.md', 'integrate/POWER-WIDTH-DECISION.md', 'tools/integrate/README.md',
             'agent-work/hs-si-r3/gate/final.md', 'agent-work/pdn-thermal-r3/run4/orch/final.md',
             'agent-work/verify-gate-r3/recheck/dense-run-0436.final.md',
             'agent-work/verify-gate-r3/wrap-real/final.md',
             'agent-work/spice-harness-r3/resume/prev/README.md']
    structured = ['agent-work/power-reinforce-r3/final-summary.json',
                  'agent-work/power-strict/result-run2.json', 'agent-work/router-via-fix/results.json',
                  'agent-work/via-dogbone-proof-r3/final_report.json',
                  'agent-work/pairs3-r3/r5/dense-d6/pair-upgrade-d6/final-summary.json',
                  'agent-work/pairs3-r3/r5/clean-c6/pair-upgrade-c6/final-summary.json',
                  'agent-work/dfm-fix-r3/out/dfm_fix_report.json', 'agent-work/hs-si-r3/runs/summary.json',
                  'agent-work/return-iso-r3/rp/return_path.records.json',
                  'agent-work/return-iso-r3/iso/isolation.records.json',
                  'agent-work/fpga-system-r3/records_dryrun.json',
                  'agent-work/spice-harness-r3/resume/validate/final.records.json']
    latest_logs = ['agent-work/fpga-system-r3/logs/suite_final.log',
                   'agent-work/spice-harness-r3/resume/validate/final.out']
    examined = [md_record(EXT / name) for name in notes]
    examined.extend(json_record(EXT / name) for name in structured)
    examined.extend(file_record(EXT / name, 'last outcome lines inspected') for name in latest_logs)
    # Root read these full handoff files separately; record that distinction honestly.
    root_reviewed = [file_record(EXT / name, 'parent reported full reading in current session')
                     for name in ['reports-notes.md', 'tools/verify/README.md', 'tools/fix/README.md',
                                  'tools/integrate/tool_status.json']]
    construction = HERE / 'recovery-composite/c05/construction.json'
    pinned = { (item['path'], item['sha256']) for item in records(json.loads(construction.read_bytes())) }
    pins = [{'path': path, 'sha256': sha} for path, sha in sorted(pinned)]
    inspected_paths = {str(Path(item['path'])).casefold() for item in examined + root_reviewed}
    for item in pins:
        item['current_coverage_receipt_inspected'] = str(Path(item['path'])).casefold() in inspected_paths
        item['meaning'] = 'Already reused and hash-verified by frozen c05→c04→c03 source reconstruction; this does not claim every file was read semantically here'
    current = {role: file_record(EXT / name, 'saved native source bytes independently hashed; native geometry not remeasured here')
               for role, name in {'r06': 'integrate/revs/r06-stitch-plane-pads-2.kicad_pcb',
                                  'r07': 'integrate/revs/r07-ripup-signals-1.kicad_pcb',
                                  'r08': 'integrate/revs/r08-power-low-0p3mm.kicad_pcb',
                                  'live': 'integrate/board.kicad_pcb'}.items()}
    local_scan = subprocess.run(['rg', '--files', '--hidden', '--no-ignore', str(PROJECT),
        '-g', '*CLAUDE*', '-g', '*claude*', '-g', '*HANDOFF*', '-g', '*handoff*',
        '-g', '*MEMORY*', '-g', '*memory*', '-g', '*OPERATOR-DECISIONS*',
        '-g', '!**/.git/**', '-g', '!**/node_modules/**', '-g', '!**/.venv/**',
        '-g', '!**/__pycache__/**', '-g', '!**/cache/**', '-g', '!**/.build/**',
        '-g', '!**/runtime/**', '-g', '!**/.claude/settings*'],
        capture_output=True, text=True, check=True).stdout.splitlines()
    settings = PROJECT / '.claude/settings.local.json'
    stat = settings.stat()
    decision_hits = [name for name in names + local_scan
                     if Path(name).name.casefold() == 'operator-decisions-2026-10-03.md']
    receipt = {'schema': 'claude-resume-context-coverage-v1', 'evidence_class': 'Read-only source/handoff coverage',
       'scope': [str(EXT), str(PROJECT)], 'external_filename_inventory_count': len(names),
       'top_level_external_entries': sorted(path.name for path in EXT.iterdir()),
       'agent_work_directories': sorted(path.name for path in (EXT / 'agent-work').iterdir() if path.is_dir()),
       'examined_relevant_files': examined, 'parent_examined_relevant_files': root_reviewed,
       'frozen_c05_construction': file_record(construction, 'complete recursive source bindings compared'),
       'already_reused_frozen_source_bindings': pins, 'saved_integrated_board_identities': current,
       'r08_same_as_r07': current['r08']['sha256'] == current['r07']['sha256'],
       'live_same_as_r07': current['live']['sha256'] == current['r07']['sha256'],
       'project_local_handoff_memory_filename_matches': local_scan,
       'claude_settings_metadata_only': {'path': str(settings), 'bytes': stat.st_size,
                                        'modified_unix_seconds': stat.st_mtime, 'contents_read': False},
       'unresolved_reference': {'name': 'OPERATOR-DECISIONS-2026-10-03.md',
                               'searched_project_and_external_filename_inventories': True,
                               'found': bool(decision_hits), 'filename_hits': decision_hits,
                               'contents_reviewed': False},
       'findings': [
         'No later integrated geometry than r07: saved r08 and live board have identical r07 SHA',
         'STATUS.md initial working-board-not-created statement is stale; later ledger/revisions supersede it',
         'Existing workflow and Hybrid power-width decision continue; FIELD_GND/FIELD_B_0V small-return bridge assumption was explicitly withdrawn03:20',
         'Historical dense pair candidate lost25pad joins; its clean-board alternative improved18joins on a different sparse baseline; neither is a missed finished current board',
         'Historical SI/PDN/orchestrator final matrices explicitly NOT VERIFIED on cc0535 dense source',
         'Historical FPGA suite final subcycle reports pass13/fail1/viol31; dry-run records leave24FAIL/45NOT_RUN',
         'Historical return/isolation results have3468FAIL/960NOT_ROUTED and31FAIL respectively; separate current board checks remain necessary',
         'SPICE resume validation provides180PASS/35INFO/209NOT_MODELED reusable harness/model records, not copper qualification',
         'c05 continues existing substantial routing: recovery retained1935r07 additions, withdrew33whole groups, and c05 exact-replays that source plus retained In3/DFM; it does not preserve every r07 new join'],
       'explicitly_unread_or_not_exhaustive': [
         'No claim that every binary, serialized PCB/schematic, geometry/cache, waveform, vendor runtime or datasheet was read',
         'Historical top-level r00/r00j/r01/final-s1/final-s2/final-s3/parity/parity2/fix/sync/move/pair/net/frouting experiment copies were inventoried by filename but not newly reviewed exhaustively',
         'Archived before-audit-fixes and before-final-sync gateware/synthesis/validation copies were not newly read',
         'Historical project reports/before-docs/PROJECT_MEMORY copies and handoff-building scripts were filename-inventoried, not reread as current decisions',
         'Individual thousands of raw model records and failed router geometries were summarized structurally, not exhaustively interpreted',
         '.claude/settings.local.json metadata only; no settings or credential contents dumped'],
       'reader_tool': file_record(Path(__file__), 'local coverage writer'),
       'native_jobs': 0, 'gpu_jobs': 0, 'shared_or_frozen_files_changed': False,
       'manufacturing_ready': False}
    out = HERE / 'claude-coverage-audit-r1.json'
    if out.exists():
        raise ValueError('Coverage receipt destination already exists')
    out.write_text(json.dumps(receipt, indent=1)+'\n', encoding='utf-8')
    print(json.dumps({'receipt': str(out), 'examined_here': len(examined), 'parent_reviewed': len(root_reviewed),
                      'frozen_source_bindings': len(pins), 'external_filename_count': len(names),
                      'r08_same_r07': receipt['r08_same_as_r07'], 'live_same_r07': receipt['live_same_as_r07']}))


if __name__ == '__main__':
    main()
