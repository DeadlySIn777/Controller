"""Freeze conditional full-load numerical evidence and physical limits."""
import json, hashlib
from pathlib import Path
H = Path(__file__).resolve().parent
BASE = H / 'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697'
OLD = H / 'R157-actual-FBG-complete-signed-simplex-3D-current-r695'
INPUT = H / 'R157-actual-FBG-complete-signed-real-barrel-mesh-input-r693'
OUT = H / 'R157-full-FBG-conditional-current-independent-review-and-reinforcement-obligation-r699'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

assert not OUT.exists()
OUT.mkdir()
r = json.loads((BASE / 'receipt.json').read_bytes())
ir = json.loads((INPUT / 'receipt.json').read_bytes())
assert sha(BASE / 'receipt.json') == '286df7e59b8172661e4d8a4f24b18f6f5abaf340a6c073a32379142eebd1c0af'
assert sha(INPUT / 'receipt.json') == '3ba864f2dd3ede7a0de92f48ecad870e2a6535f7932d304c41ee66dd7f34734c'
assert not json.loads((BASE / 'missing-numerical-literal-contact-electrodes.json').read_bytes())
assert not json.loads((BASE / 'unresolved-full-signed-electrode-choices.json').read_bytes())
assert not ir['unrooted_or_other_raw_net_terms']
assert r['full_FB_terms'] == 75 and r['full_exact_physical_endpoint_choices'] == 152
assert r['maximum_unit_equation_KCL_residual_A'] < 1e-6
barrels = json.loads((BASE / 'all-actual-real-barrel-full-signed-simplex-current-bounds.json').read_bytes())
ordinary = sorted((e for e in barrels if e['kind'] == 'via'), key=lambda e: e['maximum_absolute_A'], reverse=True)
rows = {
    'status': 'FULL_ACTUAL_FBG_SIGNED_NUMERICAL_SCOPE_SOLVED_PHYSICAL_CURRENT_THERMAL_AND_TOTAL_LOOP_NOT_QUALIFIED',
    'actual_R157_geometry_SHA256': ir['actual_R157_geometry_SHA256'],
    'actual_R157_flashes_SHA256': ir['actual_R157_flashes_SHA256'],
    'full146_signed_ledger_SHA256': ir['complete146_signed_ledger_SHA256'],
    'complete75_FB_terms_152_endpoint_choices_all_source_rooted': True,
    'all663_actual_physical_contact_ports_and_every_observed_layer_electrode_mapped': True,
    'actual_native_missing_flash_layers_NOT_substituted': True,
    'signed_J11005_2_A': r['normal_J11005_2_sink_A'],
    'positive_ground_injection_A': r['positive_ground_injection_A'],
    'negative_converter_ground_injection_A': r['negative_converter_ground_injection_A'],
    'strict_failed_first_numeric_KCL_receipt_SHA256': sha(OLD / 'failure.json'),
    'conditional_smaller_contained_numeric_mesh_receipt_SHA256': sha(BASE / 'receipt.json'),
    'conditional_unit_current_KCL_residual_A': r['maximum_unit_equation_KCL_residual_A'],
    'explicit_omissions': r['assembly'],
    'all_numerical_omission_triangle_and_quality_artifacts_SHA256': {str(p.resolve()): sha(p) for p in BASE.iterdir() if p.name.endswith('-explicit-numerical-omissions.npy') or p.name.endswith('-original-all-triangle-quality.npy')},
    'numerical_subset_removal_is_NOT_proven_upper_bound_of_every_physical_voltage_or_barrel_current': True,
    'no_triangle_area_or_physical_copper_waiver': True,
    'conditional_material_inputs': r['conditional_material_inputs'],
    'conditional_max_return_voltage_V': r['maximum_conditional_absolute_voltage_V'],
    'scoped_return_result_does_NOT_qualify_total_signed_positive_feed_plus_return_0p48V_policy': True,
    'FIELD5_drop_budget_NOT_inferred_from_0p48V_FA_FB_policy': True,
    'all6_source_contact_scenarios': r['external_sink_contact_cases'],
    'highest_ordinary_barrel_current_obligations': ordinary[:12],
    'specific_constructive_next_gate': 'Actual source-preserving parallel stitch reinforcement of existing FIELD_B_0V .5/.2 barrel7a9206b1 at47.748/206.5, B-to-inner; reproject all original contact/source/reference obligations then recompute resistive sharing, no assigned via rating/equal sharing.',
    'independent_static_review': {
        'reviewer': '/root/recover14_r2',
        'scope': 'Read-only R695 algebra, source gauge, signed simplex and material/barrel assumptions',
        'finding': 'Normalized sheet/barrel units, source-layer gauge and per-term simplex envelopes are consistent; numerical-subset and equipotential/material/thermal limits remain necessary.',
        'no_independent_heavy_execution': True},
    'required_remaining_capacity_gates': ['Diagonal scaling or exact condensation of unchanged first matrix / further same-domain mesh sensitivity.',
                                         'Refined full-load endpoint voltage and each actual barrel current sensitivity.',
                                         'Actual guaranteed Cu/plating/height/contact/temperature and measured or qualified board thermal boundaries.',
                                         'Positive feed plus ground full-loop drop, switching/partial-power/fault/transient source and package limits.',
                                         'Native joint source/physical/all-required-flash/reference/DRC qualification on the exact final head.'],
    'native_jobs': 0, 'board_written': False, 'adopted': False,
    'current_capacity_or_manufacturing_acceptance': False,
    'input_SHA256': {str(p.resolve()): sha(p) for p in [INPUT / 'receipt.json', BASE / 'receipt.json', OLD / 'failure.json', H / 'prepare_R157_actual_FBG_full_signed_3D_mesh_r693.py', H / 'solve_R157_actual_FBG_complete_signed_simplex_3D_r695.py', H / 'solve_R157_actual_FBG_explicit_stable_numeric_subset_r697.py']}}
(OUT / 'receipt.json').write_text(json.dumps(rows, indent=1, allow_nan=False) + '\n', encoding='utf-8')
print('R699_COMPLETE', sha(OUT / 'receipt.json'))
