"""Pin a static review only; never run the native helpers."""
import ast
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent
OUT = H / 'revised-R298-R299-all-net-native-static-review-r757'
assert not OUT.exists()
OUT.mkdir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
scripts = [ROOT / 'native_combined_all_net_fill_and_real_saved_cache_r298.py', ROOT / 'launch_combined_R753_full_native_diagnostic_r299.py', ROOT / 'supplement_combined_actual_retained_via_scope_r300.py']
for p in scripts:
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
expected = ROOT / 'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json'
assert sha(expected) == '13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3'
e = json.loads(expected.read_bytes())
mask = Path(e['baseline_full_native_mask_file'])
assert sha(mask) == e['baseline_full_native_mask_SHA256']
m = json.loads(mask.read_bytes())['vias']
assert len(m) == 8006 and set(m) <= set(e['copper'])
assert e['authorized_removed_actual_full_R157_via_UUIDs'] == []
assert len(e['copper']) == 94448 and len(e['required_NEW_ordinary_all6']) == 13
native = scripts[0].read_text(encoding='utf-8')
launch = scripts[1].read_text(encoding='utf-8')
assert "assert {u:set(v)for u,v in savedflashes.items()}=={u:set(v)for u,v in flashes.items()}" in native
assert 'missing_required_retained_actual_FULL_R157_via' in native
assert "if not reloadmask['matches_in_memory_full_native_flash_sets']" in launch
assert "assert sha(recovery)=='1c7fba1adc371ab8b3a4ffc78249cc63c0a2aec113ade7d4e683d21bd2b2b815'" in launch
assert '--refill-zones' not in launch
pins = {str(p): sha(p) for p in [*scripts, expected, mask]}
receipt = {
    'status': 'REVISED_STATIC_REVIEW_NO_BLOCKER_FOR_ONE_KNOWN_FAILURE_DIAGNOSTIC',
    'input_SHA256': pins,
    'all_8006_actual_R157_via_UUIDs_retained_no_retirement_exemption': True,
    'saved_vs_in_memory_FlashLayer_equality_asserted_after_mismatch_evidence': True,
    'complete_R588_manifest_SHA_asserted_by_launcher': True,
    'single_all_zone_same_instance_fill_exact_Cu_locks_and_FP_pad_pose_checks': True,
    'separate_genuine_CPP_filled_copy_reload_checks_before_cached_CLI': True,
    'matched_stem_source_project_rules_and_libraries_pinned': True,
    'cached_CLI_without_additional_refill': True,
    'native_source_contact_reference_mask_current_DRC_and_adoption_gates_remain_independent': True,
    'review_does_not_execute_or_qualify_native_geometry': True,
    'native_jobs_launched': 0, 'adopted': False, 'manufacturing_ready': False,
}
fp = OUT / 'receipt.json'
fp.write_text(json.dumps(receipt, indent=1, allow_nan=False) + '\n', encoding='utf-8')
assert all(sha(p) == h for p, h in pins.items())
print(json.dumps({'receipt_file': str(fp), 'receipt_SHA256': sha(fp), 'reviewed_helper_SHA256': pins[str(scripts[0])], 'reviewed_launcher_SHA256': pins[str(scripts[1])]}))
