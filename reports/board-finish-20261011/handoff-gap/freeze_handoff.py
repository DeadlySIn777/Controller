"""Save exact recovered handoff evidence; never change source or old receipts."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
MEMORY = Path('C:/Users/Gluis/.claude/projects/C--Users-Gluis-OneDrive-Documents-ChatGPT-Controller/memory')
DOCUMENTS = [Path(name) for name in (
    'Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md',
    'Z:/pcb-runs/codex-resume-20261004/r01/intake/OPERATOR-DECISIONS-2026-10-03.md',
    'Z:/pcb-runs/relayout/rules-r3/d4/codex-resume-r01/snapshots-r02/metadata/OPERATOR-DECISIONS-2026-10-03.md',
    'Z:/pcb-runs/relayout/rules-r3/d4/codex-resume-r01/snapshots/metadata/OPERATOR-DECISIONS-2026-10-03.md')]
EXPECTED = '392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5'


def record(path, mode):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha256(data).hexdigest(),
            'mtime_ns': path.stat().st_mtime_ns, 'review_mode': mode}


def main():
    out = HERE / 'handoff-gap-receipt.json'
    if out.exists():
        raise ValueError('Evidence receipt already exists')
    docs = [record(path, 'Full recovered original read; historical copies byte compared') for path in DOCUMENTS]
    if any(item['sha256'] != EXPECTED or item['bytes'] != 16583 for item in docs):
        raise ValueError('Recovered original/historical copy identity changed')
    empty = record(Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-04.md'), 'Empty file only; no newer authority inferred')
    memory = [record(path, 'Full project memory read' if path.name in ('MEMORY.md', 'board-finishing-state.md')
                     else 'Project-scoped context read; no broader settings or unrelated projects read')
              for path in sorted(MEMORY.glob('*.md'))]
    project_root = MEMORY.parent.parent
    scoped = sorted(path for path in project_root.iterdir()
                    if path.is_dir() and ('controller' in path.name.casefold() or path.name.startswith('Z--pcb-runs')))
    scoped_record = []
    for path in scoped:
        scoped_record.append({'path': str(path), 'selection_basis': 'Encoded project path contains Controller or starts Z--pcb-runs',
                              'direct_jsonl_files': [str(item) for item in sorted(path.glob('*.jsonl'))],
                              'has_memory': (path / 'memory').is_dir(),
                              'subagent_tool_result_contents_read': False})
    recovered = HERE / 'recovered'
    recovered.mkdir()
    copies = []
    for source in (DOCUMENTS[0], MEMORY / 'MEMORY.md', MEMORY / 'board-finishing-state.md'):
        target = recovered / source.name
        data = source.read_bytes()
        target.write_bytes(data)
        if target.read_bytes() != data or source.read_bytes() != data:
            raise ValueError('Source or exact copy changed while freezing')
        copies.append({'source': str(source), 'copy': str(target), 'sha256': sha256(data).hexdigest(), 'bytes': len(data)})
    refs = []
    external = Path('Z:/pcb-runs/claude-finish/tools/verify')
    for name in ('required_tests.json', 'wrap_quality.py', 'rail_model.json', 'si_pairs.py',
                 'return_path.py', 'pdn_ir.py', 'isolation.py', 'drc_records.py'):
        path = external / name
        refs.append(dict(record(path, 'Only exact operator-document citation lines inspected'),
                         references=[{'line': number, 'text': line.strip()} for number, line in
                                     enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1)
                                     if 'OPERATOR-DECISIONS-2026-10-03' in line]))
    prior = [record(WORK / name, 'Prior coverage receipt retained unchanged') for name in
             ('claude-coverage-audit.json', 'claude-coverage-audit-r1.json')]
    recent = json.loads((HERE / 'recent-board-context.json').read_bytes())
    sessions = json.loads((HERE / 'controller-session-context.json').read_bytes())
    result = {'schema': 'controller-handoff-gap-v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'verdict': 'RECOVERED_AND_PROJECT_CONTEXT_REVIEWED',
              'original_reference_gap_resolved': True, 'document': docs[0], 'matching_historical_copies': docs[1:],
              'empty_later_named_file': empty, 'exact_evidence_copies': copies,
              'standing_rules_recovered': [
                  'Final definition of done14 and five final reviews',
                  'VIPPO only for intentional via-in-pad; ordinary vias remain ordinary',
                  'Same-side functional subnets grouped; true galvanic barriers preserved across all copper layers',
                  '0.6mm ordinary separated24V domains; barrier clearance/creepage derived from actual working conditions',
                  'Interface-specific parametric controlled impedance and continuous reference; provisional pending PCBWay',
                  'No vacuous no-net-loses-a-join or bypassed zone/fill gate',
                  'Source-anchored return rules and bounded D4/D5 exemptions with per-item accounting',
                  'SBC5V draft<=100mV at3.6A, >=5vias/transition, never cut In1/In4 or barriers'],
              'historical_scope': 'ROOT104/105 sizes, counts and reference identities are historical; ROOT106 contract is current. required_tests.json explicitly says standing rules apply but ROOT104/105 counts/outlines do not.',
              'exact_citation_sources': refs, 'controller_project_memories': memory,
              'scoped_claude_project_directories': scoped_record,
              'session_scan': {'receipt': record(HERE / 'controller-session-context.json', 'Structured scan reviewed'),
                               'main_sessions_scanned': len(sessions),
                               'no_z_pcb_runs_encoded_directory_present': not any(path.name.startswith('Z--pcb-runs') for path in scoped),
                               'malformed_json_lines': [{'path': item['path'], 'lines': item['parse_error_lines']}
                                                        for item in sessions if item['parse_error_lines']],
                               'unchanged_during_each_read': all(item['unchanged_during_read'] for item in sessions)},
              'latest_relevant_summary': recent['latest_summary'],
              'recent_board_context_receipt': record(HERE / 'recent-board-context.json', 'Latest relevant assistant context read'),
              'findings': [
                  'Controller board memory ends with 11Oct05:47 resource note; compact summary timestamp10:44:42UTC and last relevant assistant11:14:33UTC are newer.',
                  'Latest relevant Claude board reply explicitly says r07 not done:29completed17lost vsr06,1355joins1364API,0DRCerrors179warnings; its E1 proposal and obstacle census are historical source context.',
                  'No missed finished current board found in the six main-session structured scans or eight scoped memories. This bounded scan does not establish all subagent transcript coverage.',
                  'Latest summary references already reviewed external workflows/tools. Current frozen native receipts supersede its pending r07/E1 state.',
                  'Prior gap receipts are retained unchanged; this separate receipt resolves their missing-document and project-local-memory coverage gap.'],
              'limits': ['Prior agent memory/transcripts are context, not fresh native proof or authorization.',
                         'No unrelated project transcripts, Claude settings/secrets or tool-result/subagent payloads read.',
                         'Main-session parse failures are retained as coverage limits; no malformed payload repair attempted.',
                         'No claim of exhaustive semantic reading of every historical transcript/geometry/datasheet.'],
              'prior_coverage_receipts_unchanged': prior,
              'native_jobs': 0, 'gpu_jobs': 0, 'board_or_shared_source_edits': False,
              'reader_scripts': [record(HERE / name, 'Executed isolated host-only reader') for name in
                                 ('inspect_sessions.py', 'inspect_recent.py', 'freeze_handoff.py')]}
    for item in docs + memory + prior:
        if sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Read source changed before receipt completion: ' + item['path'])
    out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(out), 'sha256': sha256(out.read_bytes()).hexdigest(),
                      'document_sha256': EXPECTED, 'memories': len(memory), 'sessions': len(sessions),
                      'latest_board_reply': recent['recent_board_assistant_messages'][-1]['timestamp']}))


if __name__ == '__main__':
    main()
