"""Bind independent functional review evidence without changing any RTL."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'reports/board-finish-20261017'
OUT = BASE / 'release-review/producer-fifo-independent-supplement-r1/independent-reviewed-overlay-packet.json'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def bound(relative):
    p = BASE / relative
    return {'path': str(p), 'SHA256': sha(p)}

sources = {
    'cnc3_runtime_events.v': ('event-producer-fifo-r1/cnc3_runtime_events.v',
        '4d21b8af4ca2decc10d872361fb033fcaecb939b14ff4d62d959609cdc2f30d6',
        'ddb1cf8325d3cb89a441d6fa878d7ffe40e82835504289cbe76e0da9b0590c51'),
    'cnc3_event_bank.v': ('efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v',
        '6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841',
        '65fa79532ac564c58d878b7e2b804de11e5af7e85b1157638d7823645aa92659'),
    'cnc3_spi_transport_stateful.v': ('release-review/transport-cmd-alignment-r1/cnc3_spi_transport_stateful.v',
        'c909378cb28cf87c7113b1b92c6cdd82f71e166c64eb87548a8880ba85c9d4cc',
        '35496db3610c55547aecb756d99f2f13815ce5a599acae557afb9645f9801a47'),
}
receipt_paths = {
    'root_differential': 'event-producer-fifo-r1/behavior-receipt.json',
    'independent_supplement': 'release-review/producer-fifo-independent-supplement-r1/receipt.json',
    'semantic_mutations': 'release-review/producer-fifo-independent-supplement-r1/mutations/receipt.json',
    'unchanged_runtime_suite': 'event-producer-fifo-r1/full-runtime-independent-r1/receipt.json',
    'transport_differential_and_suite_packet': 'release-review/transport-cmd-alignment-r1/reviewable-transport-overlay-packet.json',
}
receipts = {k: json.loads((BASE / p).read_text()) for k,p in receipt_paths.items()}
assert receipts['root_differential']['status'] == 'PRODUCER_FIFO_DIFFERENTIAL_PASS'
assert receipts['independent_supplement']['status'] == 'PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS'
assert receipts['semantic_mutations']['status'] == 'THREE_FIFO_SEMANTIC_MUTATIONS_COMPILE_AND_FAIL_BEHAVIOR_AS_REQUIRED'
assert receipts['unchanged_runtime_suite']['status'] == 'PASS'
assert receipts['unchanged_runtime_suite']['sources_unchanged']
for control in receipts['semantic_mutations']['controls']:
    assert control['status'] == 'EXPECTED_BEHAVIORAL_REGRESSION_DETECTED'
    assert [(e['phase'], e['exit']) for e in control['executions']] == [('compile',0),('execute',1)]

source_bindings = {}
for name, (relative, expected, old) in sources.items():
    assert sha(BASE / relative) == expected
    canonical = ROOT / 'gateware/v3/runtime' / name
    assert sha(canonical) == old, f'canonical changed before finalization: {name}'
    assert receipts['unchanged_runtime_suite']['copied_input_sha256'][name] == expected
    source_bindings[name] = {**bound(relative), 'canonical_before_SHA256': old}
candidate = BASE / sources['cnc3_runtime_events.v'][0]
diff = BASE / 'event-producer-fifo-r1/candidate_diff.v'
assert diff.read_text().replace('module cnc3_runtime_events_candidate(', 'module cnc3_runtime_events(') == candidate.read_text()
original = BASE / 'event-producer-fifo-r1/original_diff.v'
assert original.read_text().replace('module cnc3_runtime_events_original(', 'module cnc3_runtime_events(') == (ROOT/'gateware/v3/runtime/cnc3_runtime_events.v').read_text()

packet = {
    'status': 'INDEPENDENT_FUNCTIONAL_REVIEW_PASS_FOR_DISCONNECTED_SIM2_ONLY',
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'selected_sources': source_bindings,
    'qualification_receipts': {k: bound(p) for k,p in receipt_paths.items()},
    'exact_normalization': {'selected_candidate_equals_root_differential_top_rename_only': True,
        'canonical_original_equals_root_differential_top_rename_only': True},
    'independent_harness_review': {
        'root_matrix_nonvacuous': True,
        'seeding_global_and_local_pointers_counts_and_records_reviewed': True,
        'root_scope': '110592 boundary vectors, 695104 cycles, 28164819 normalized live-record comparisons; all producer-valid masks, eight write-bank offsets, free slots 0..8, sequence 254/255/1, ACK/no-ACK and natural/random execution',
        'supplement_scope': '120 boundary cases, 11181 cycles, 2726 post-commit checks, 263949 live-record comparisons, 490 admissions; every producer full256 plus ACK+append, rotated interleaved heads, pointer wrap and complete drain, stale tags, empty/pending clear and async reset, X/Z payload',
        'controls': 'Three separately compiled semantic mutants fail the focused behavioral oracle: missing global prefetch guard, sequence replacing global slot tag, and capacity255',
        'unchanged_full_suite': '1190 actual SPI/runtime checks; events9; event storage11; provider7; default-deny10000 cycles',
    },
    'substantive_source_review': [
        'Original conditional temp_count/temp_wr/temp_sequence admission, producer order, exact-full and same-cycle ACK arithmetic retained; each fixed producer writes at most one record per cycle.',
        'Global slot tag is eight-bit rd/wr identity, separate from event sequence modulo255. Per-producer counts are nine bits and all are jointly bounded by the original global256 count.',
        'Global prefetched_rd guard, producer count/local prefetched pointer, pending-write masks and synchronous write-first forwarding preserve head timing. Arrays are not reset; metadata masks stale/uninitialized data.',
        'Probe/index/fault generation, snapshots, delivered ACK eligibility, overflow, clear/reset and capture selector semantics remain qualified by old/new functional and four-state tests.',
        'Transport retains all RX/completed-frame/TX-snapshot/header buffers. CMD alignment changes the shift position and corresponding taps; public protocol and malformed-frame policy are unchanged.',
        'Original event bank registered write-first bypass remains behavior-equivalent and separately RAM-inferred. The new producer banks are internal to the selected events file; no canonical public port change.',
    ],
    'adoption_review': {
        'substantive_functional_reason_to_block_disconnected_SIM2_source_adoption_found': False,
        'conditional_next_gate': 'Parent exact full-core native mapping and post-map bank checks; exact canonical-before guards, byte backups and provenance update at adoption.',
        'limits_and_features_reduced': False,
        'production_adopted': False,
        'physical_provider_wrapper_complete': False,
        'physical_IO_PNR_timing_hardware_programming_or_manufacturing_claim': False,
        'scope': 'Current sources are still disconnected SIM2. Functional regression and native mapping do not qualify a physical provider, package implementation or timing.',
    },
    'canonical_sources_unchanged_at_review': True,
}
assert not OUT.exists()
OUT.write_text(json.dumps(packet, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': packet['status'], 'packet': str(OUT), 'SHA256': sha(OUT)}))
