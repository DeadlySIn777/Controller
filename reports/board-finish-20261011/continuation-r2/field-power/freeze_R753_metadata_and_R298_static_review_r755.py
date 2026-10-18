"""Metadata-only clarification and static review; no PCB or geometry changes."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent
OUT = H / 'R753-frozen-metadata-clarification-and-native-runner-static-review-r755'
assert not OUT.exists()
OUT.mkdir()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def put(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=1, allow_nan=False) + '\n', encoding='utf-8')

stage = H / 'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753'
manifest_file = stage / 'final-stage-manifest.json'
ledger_file = stage / 'current-shared-role-exact-negative-operation-ledger.json'
assert sha(manifest_file) == '50016f4cc0f0928bf34d186b1fa6e912f6229ed88bb090eb788058486306253e'
assert sha(ledger_file) == '10e2c0f1252df112b83791c29360fa29999b793d73f93c881779ffe97457ee83'
manifest = json.loads(manifest_file.read_bytes())
board = Path(manifest['staged_native_board']['file'])
assert sha(board) == manifest['staged_native_board']['SHA256'] == '7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
recovery = Path(manifest['RECOVERY_manifest']['file'])
assert sha(recovery) == manifest['RECOVERY_manifest']['SHA256'] == '1c7fba1adc371ab8b3a4ffc78249cc63c0a2aec113ade7d4e683d21bd2b2b815'

def find_flags(obj, prefix=''):
    rows = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = prefix + '/' + k
            if k == 'R747_aggregate_scope_checker_PASS_NOT_claimed':
                rows.append({'json_pointer': key, 'frozen_value': v})
            rows.extend(find_flags(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            rows.extend(find_flags(v, prefix + '/' + str(i)))
    return rows

flags = find_flags(json.loads(ledger_file.read_bytes()))
assert len(flags) == 6 and all(r['frozen_value'] is False for r in flags)
clarification = {
    'status': 'METADATA_ONLY_CLARIFICATION_ALL_FROZEN_INPUTS_PRESERVED',
    'frozen_ledger': {'file': str(ledger_file), 'SHA256': sha(ledger_file)},
    'mislabelled_negated_flags': flags,
    'authoritative_meaning': 'R747 aggregate chained-scope checker did fail. No PASS or tolerance/area waiver is claimed. Its exact witness and the separately declared local owned negative redesign remain bound raw failures pending fresh actual source/contact/reference/native/current tests.',
    'R747_aggregate_scope_checker_PASS_claimed': False,
    'R747_aggregate_scope_checker_PASS_NOT_claimed_corrected_metadata_value': True,
    'remote_vertex_test_is_not_a_remote_edge_by_edge_identity_certificate': True,
    'whole_RECOVERY_R588_manifest_SHA_independently_verified': sha(recovery),
    'board_file': str(board), 'board_SHA256': sha(board),
    'geometry_or_native_source_or_rules_or_profiles_changed': False,
    'adopted': False, 'manufacturing_ready': False,
}
put('metadata-clarification.json', clarification)

runner = ROOT / 'native_combined_all_net_fill_and_real_saved_cache_r298.py'
review = {
    'status': 'STATIC_REVIEW_NO_EXECUTION',
    'runner_file': str(runner), 'runner_SHA256_at_freeze': sha(runner),
    'reviewed_behavior': ['Single captured native board and one successful all-zone CPP Fill', 'Exact integer raw-net Cu/locks and FP/pad poses before/after/reload', 'Separate genuinely CPP-filled diagnostic copy; source file is not saved', 'Pinned board/project/rules/baseline mask/helpers; no fabrication/adoption claim'],
    'findings_sent_to_root': [
        'Assert saved/reloaded versus in-memory FlashLayer set equality after recording mismatch evidence; do not continue CLI qualification against a different saved state.',
        'Missing old-mask UUID must be a mask-contract error unless its retirement is explicitly authorized by the exact bound operation ledger. Do not silently skip required retained vias.',
        'The whole R588 manifest was independently verified here against its frozen SHA. Its builder recorded rather than asserted that SHA.',
    ],
    'findings_are_version_scoped_and_may_be_resolved_by_a_separately_pinned_runner_successor': True,
    'native_execution_or_fill_or_source_validation_performed_by_this_review': False,
}
put('native-runner-static-review.json', review)
put('receipt.json', {
    'status': clarification['status'],
    'metadata_clarification_SHA256': sha(OUT / 'metadata-clarification.json'),
    'static_review_SHA256': sha(OUT / 'native-runner-static-review.json'),
    'source_board_SHA256_before_and_after': sha(board),
    'frozen_ledger_SHA256_before_and_after': sha(ledger_file),
    'all_frozen_inputs_unchanged': True,
    'jobs_launched': 0, 'adopted': False, 'manufacturing_ready': False,
})
print(json.dumps({'output': str(OUT), 'receipt_SHA256': sha(OUT / 'receipt.json'), 'board_SHA256': sha(board)}))
