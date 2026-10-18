from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

board = D / 'motherboard-C11087-ground-transfer-candidate.kicad_pcb'
generation = read(D / 'generation.json')
before = ROOT / generation['before_board']
assert sha(before) == generation['before_board_sha256']
board_hash = sha(board)
names = ['one-replacement-proof.json', 'all-old-SOURCE-cluster-proof.json',
         'combined101-current-proof.json', 'full-resource-review.json',
         'all82-retained-control-proof.json']
for name in names:
    row = read(D / name)
    assert row['passed'], name
    if 'board_sha256' in row:
        assert row['board_sha256'] == board_hash, name
full = read(D / 'full-resource-review.json')
assert full['filled_component_count'] == 187
assert not full['unanchored_components']
assert not full['derived_nonphysical_computation_artifacts']
combined = read(D / 'combined101-current-proof.json')
assert combined['retained_local_loops_checked'] == 101
assert len(combined['actual_receiving_return_anchor_reviews']) == 207
inventory = read(D / 'independent-connectivity/review.json')
assert inventory['source_net_checks_pass']
assert inventory['uncapped_unconnected_ratsnest_edges'] == 3562
assert inventory['independent_physical_cluster_missing_joins'] == 3562
assert not inventory['orphan_copper_items']
native = read(D / 'native.json')
assert not native['ignored_checks']
assert not [r for r in native['violations'] if r['severity'] == 'error']
assert len(native['violations']) == 3
cases = ['cut-actual-VCC-branch', 'cut-actual-nearby-Ground-barrel', 'wrong-actual-Ground-barrel-net']
for case in cases:
    p = D / f'{case}.fresh-native-review.json'
    row = read(p)
    assert row['passed'] and row['fresh_native_reload_rejected']
    assert row['persisted_mutation_verified']
    assert row['board_sha256'] == sha(D / f'{case}.kicad_pcb')
    names += [f'{case}.review.json', f'{case}.fresh-native-review.json']
names += ['native.json', 'bounded-scope.json', 'combined100-retained-plus1-replacement-manifest.json']
receipt = {
    'passed': True,
    'schema_version': 'C11087-one-replacement-r01',
    'before_board': str(before.relative_to(ROOT)),
    'before_board_sha256': sha(before),
    'board': str(board.relative_to(ROOT)),
    'board_sha256': board_hash,
    'bounded_scope': str((D / 'bounded-scope.json').relative_to(ROOT)),
    'added_Cu_UUIDs': generation['new_Cu_UUIDs'],
    'added_ground_branch_mm': generation['Ground_branch_points_mm'],
    'added_ground_via_mm': generation['new_ground_via_mm'],
    'added_free_ground_via_diameter_drill_mm': [0.50, 0.20],
    'actual_power_transfer_to_source_ground_distance_mm': 0.75,
    'actual_SOURCE_pair': {'power': ['C11087.1', 'U11033.5'], 'return': ['C11087.2', 'U11033.3']},
    'historical_101_unchanged': False,
    'historical_groups_retained_exactly': 100,
    'replaced_group': 'C11087 -> actual U11033.5/3',
    'current_groups_proved': 101,
    'actual_receiving_return_endpoints_proved': 207,
    'current_manifest': str((D / 'combined100-retained-plus1-replacement-manifest.json').relative_to(ROOT)),
    'three_real_physical_cuts_rejected_after_fresh_native_reload': True,
    'actual_flashing_annulus_SOURCE_and_both_adjacent_layers_proved': True,
    'actual_82_BankA_control_segments_retained': True,
    'native_regular_errors': 0,
    'native_regular_warnings': 3,
    'ignored_checks': 0,
    'warnings_disposition': 'Exactly the three pre-existing ROOT88 RAW via/track-center/hole-spacing warnings; separately corrected in parent ROOT89, not waived by this donor.',
    'native_missing_joins': 3562,
    'independent_missing_joins': 3562,
    'orphan_Cu_count': 0,
    'actual_reference_resources': 187,
    'unanchored_reference_resources': 0,
    'synthetic_reference_exemptions': 0,
    'all_old_SOURCE_pad_clusters_Cu_lands_poses_zones_preserved': True,
    'source26_unchanged': True,
    'source27_adopted': False,
    'effective_capacitance_inductance_high_current_timing_temperature_qualified': False,
    'manufacturing_ready': False,
    'evidence': {n: {'path': str((D / n).relative_to(ROOT)), 'sha256': sha(D / n)} for n in names},
    'independent_inventory': {'path': str((D / 'independent-connectivity/review.json').relative_to(ROOT)), 'sha256': sha(D / 'independent-connectivity/review.json')},
}
(D / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': True, 'board_sha256': board_hash, 'receipt_sha256': sha(D / 'receipt.json'), 'groups': '100 retained + 1 actual replacement', 'endpoints': 207}))
