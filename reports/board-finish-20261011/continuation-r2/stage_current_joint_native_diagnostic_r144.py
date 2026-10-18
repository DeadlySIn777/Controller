"""Stage a freshly bound joint head for exploratory native checks only.

The frozen R7 production stager and R9 failed diagnostic stay byte-identical.
This successor binds its own current-head manifest and the exact R87 rotations.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'stage_joint_power_native_r7.py';code=source.read_text()
needle='import native_translation_owned_contract_r2 as FP';assert code.count(needle)==1
code=code.replace(needle,'import native_owned_root_pose_contract_r3 as FP')
needle="assert len(sys.argv) == 3, 'recipe/receipt.json fresh_output_directory'";assert code.count(needle)==1
code=code.replace(needle,"assert len(sys.argv) == 4, 'recipe/receipt.json fresh_output_directory explicit_current_diagnostic_gate.json'")
needle='recipe = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()';assert code.count(needle)==1
code=code.replace(needle,needle+"; gatepath=Path(sys.argv[3]).resolve(); gate=read(gatepath)")
needle="assert r['host_retained_relationships_pass'], 'Retained host contact gate must pass before native staging'";assert code.count(needle)==1
replacement="""assert gate['schema']=='current-joint-native-exploratory-gate-r144'
    assert gate['verdict']=='ALLOW_CURRENT_JOINT_EXPLORATORY_NATIVE_WITH_BOUND_FAILED_OR_OPEN_PRODUCTION_GATES'
    assert gate['recipe_file']==str(recipe) and gate['recipe_sha256']==sha(recipe)
    assert gate['model_sha256']==r['frozen_host_model_sha256']
    assert gate['fresh_actual_incremental_contact_source_old_reference_native_effective_Cu_gate_pass'] is True
    assert gate['all_current_sparse_operations_authorized_and_bound'] is True
    assert gate['all_unresolved_old_and_new_reference_current_native_gates_explicitly_bound'] is True
    assert not gate['adopted'] and not gate['manufacturing_ready']
    assert r['host_retained_relationships_pass'] is False
    assert r['host_all_supply_pad_and_proposed_components_rooted'] is False
    for e in gate['frozen_read_set']:assert sha(e['file'])==e['sha256']
    rot=H/'two-rotated-FP-native-collector-contract-r87/frozen-rotation-rows.json'
    assert sha(rot)=='c79354f60f6fba0e38cd5f3df774876c4fc541ede3a2f27109d1a236f9c448d3'
    assert [q for q in r['native_existing_owned_footprint_replacement_rows'] if q['ref']!='R17031']==read(rot)
    assert sha(source)==gate['unchanged_frozen_R7_stager_sha256']
    assert sha(H/'stage_joint_power_native_diagnostic_r9.py')==gate['unchanged_frozen_R9_stager_sha256']"""
code=code.replace(needle,replacement)
needle='pins[str(declared_parent.resolve())]=sha(declared_parent)';assert code.count(needle)==1
code=code.replace(needle,needle+"\n    pins[str(gatepath)]=sha(gatepath);pins[str(rot)]=sha(rot);pins.update({e['file']:e['sha256']for e in gate['frozen_read_set']})")
needle="'parent_sha256':sha(parent),'candidate_sha256':sha(board),'all_unlisted_parent_entities_header_tail_exact':True";assert code.count(needle)==1
code=code.replace(needle,"'parent_sha256':sha(parent),'candidate_sha256':sha(board),'explicit_current_diagnostic_gate_file':str(gatepath),'explicit_current_diagnostic_gate_sha256':sha(gatepath),'full_failed_or_open_production_gate_ledger_file':gate['production_failure_ledger_file'],'full_failed_or_open_production_gate_ledger_sha256':gate['production_failure_ledger_sha256'],'manufacturing_ready':False,'all_unlisted_parent_entities_header_tail_exact':True")
compile(code,str(source),'exec')
exec(compile(code,str(source),'exec'))
