"""Measure an explicitly failed reference candidate without adoption.

R144, R7 and R9 remain immutable. This gate keeps exact R368 failures and
R155 physical identity bound; it requires only the separate contact/source
and native-rule geometry scopes to pass before diagnostic API measurement.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
wrapper=H/'stage_current_joint_native_diagnostic_r144.py';code=wrapper.read_text()
needle="gate['schema']=='current-joint-native-exploratory-gate-r144'";assert code.count(needle)==1
code=code.replace(needle,"gate['schema']=='known-reference-failure-native-diagnostic-gate-r157'")
needle="gate['verdict']=='ALLOW_CURRENT_JOINT_EXPLORATORY_NATIVE_WITH_BOUND_FAILED_OR_OPEN_PRODUCTION_GATES'";assert code.count(needle)==1
code=code.replace(needle,"gate['verdict']=='ALLOW_KNOWN_REFERENCE_FAILURE_NATIVE_DIAGNOSTIC_ONLY_WITH_RAW_FAILURES_BOUND'")
needle="assert gate['fresh_actual_incremental_contact_source_old_reference_native_effective_Cu_gate_pass'] is True";assert code.count(needle)==1
replacement="""assert gate['fresh_actual_incremental_contacts_sources_and_native_effective_Cu_gate_pass'] is True
    assert gate['strict_old_reference_gate_pass'] is False
    assert gate['strict_old_reference_loss_count']==28
    assert gate['new_R7_raw_reference_failure_preserved'] is True
    assert gate['model_sha256']=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    assert sha(gate['raw_R368_audit_receipt_file'])==gate['raw_R368_audit_receipt_sha256']=='e4a9373b5816de6926cc3b3cea82d1751e5db6cb70d9f150443dff577afff29e'
    assert sha(gate['exact_R364_to_R155_physical_identity_receipt_file'])==gate['exact_R364_to_R155_physical_identity_receipt_sha256']=='cc0aa7aa4328d2cdf0a071d1c987c94c910a0850f4bafb094ec492c0e93866e7'
    assert sha(gate['production_failure_ledger_file'])==gate['production_failure_ledger_sha256']
    failure=read(gate['production_failure_ledger_file'])
    assert failure['strict_old_reference_gate_pass'] is False and failure['strict_old_reference_loss_count']==28
    assert failure['new_R7_raw_reference_failure_preserved'] is True
    assert failure['all_raw_old_and_new_reference_planner_CORE_current_ROOT42_native_failures_preserved'] is True
    assert not failure['adopted'] and not failure['manufacturing_ready']"""
code=code.replace(needle,replacement)
needle="'manufacturing_ready':False,'all_unlisted_parent_entities_header_tail_exact':True";assert code.count(needle)==1
code=code.replace(needle,"'strict_old_reference_gate_pass':False,'strict_old_reference_loss_count':28,'new_R7_raw_reference_failure_preserved':True,'manufacturing_ready':False,'all_unlisted_parent_entities_header_tail_exact':True")
compile(code,str(wrapper),'exec');exec(compile(code,str(wrapper),'exec'))
