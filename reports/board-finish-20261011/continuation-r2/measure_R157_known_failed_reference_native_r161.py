"""Run complete native measurement with exact R160 API and bound raw failures."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'measure_joint_power_native_r3.py';code=source.read_text()
needle="receipt=json.loads((stage/'receipt.json').read_bytes())"
replace="""original_receipt=json.loads((stage/'receipt.json').read_bytes())
    attestation=stage/'exact-adjacent-duplicate-vertices-r160/receipt.json'
    receipt=json.loads(attestation.read_bytes())
    assert original_receipt['verdict']=='FAIL_JOINT_POWER_NATIVE_API'
    assert sha(stage/'receipt.json')==receipt['original_failed_stage_receipt_sha256']
    assert receipt['strict_old_reference_gate_pass'] is False and receipt['strict_old_reference_loss_count']==28
    assert receipt['new_R7_raw_reference_failure_preserved'] is True
    assert not receipt['adopted'] and not receipt['manufacturing_ready']
    for p,v in receipt['input_sha256'].items():assert sha(p)==v
    assert sha(receipt['native_zone_exact_contract_file'])==receipt['native_zone_exact_contract_sha256']
    receipt['native_postfill_via_obligations_sha256']=original_receipt['native_postfill_via_obligations_sha256']"""
assert code.count(needle)==1;code=code.replace(needle,replace)
old="verdict='PASS_JOINT_POWER_SOURCE_ALL_CU_ALL_NEW_ZONES_API_ONLY'"
new="verdict='PASS_R157_NATIVE_API_WITH_EXACT_TWO_ZERO_LENGTH_EXPECTED_EDGES'"
assert code.count(old)==1;code=code.replace(old,new)
needle="actual_helper=H/'native_final_partitions_contract_r2.py'"
assert code.count(needle)==1;code=code.replace(needle,"actual_helper=H/'native_final_partitions_known_failure_diagnostic_r162.py'")
needle="code=source.read_text(encoding='utf-8')"
extra="""
    intake=\"    receipt=json.loads((STAGE/'receipt.json').read_bytes())\"
    check_intake=\"\"\"    original_api_receipt=json.loads((STAGE/'receipt.json').read_bytes())
    attestation=STAGE/'exact-adjacent-duplicate-vertices-r160/receipt.json'
    receipt=json.loads(attestation.read_bytes())
    assert original_api_receipt['verdict']=='FAIL_JOINT_POWER_NATIVE_API'
    assert sha(STAGE/'receipt.json')==receipt['original_failed_stage_receipt_sha256']
    for p,v in receipt['input_sha256'].items():assert sha(p)==v
    assert receipt['strict_old_reference_loss_count']==28 and not receipt['strict_old_reference_gate_pass']
    assert receipt['new_R7_raw_reference_failure_preserved'] and not receipt['adopted'] and not receipt['manufacturing_ready']\"\"\"
    assert code.count(intake)==1;code=code.replace(intake,check_intake)
    anchor=\"    pins.update(sourcepins);pins.update({str(p.resolve()):sha(p) for p in pinned});check(pins)\"
    extra_pins=\"    pinned.extend([attestation,Path(receipt['native_zone_exact_contract_file']),HERE/'attest_R157_exact_native_adjacent_duplicate_vertices_r160.py',HERE/'measure_R157_known_failed_reference_native_r161.py',HERE/'native_final_partitions_contract_r2.py'])\\n\"
    assert code.count(anchor)==1;code=code.replace(anchor,extra_pins+anchor)
"""
assert code.count(needle)==1;code=code.replace(needle,needle+extra)
needle="if actual_contract['verdict']!='PASS_ACTUAL_FULL_NATIVE_FILL_ALL_CU_AND_EXPLICIT_FLASH_CONTRACT' or actual_contract['postfill_Cu_or_flash_errors']:raise ValueError('Actual full native Cu/flash contract failed')"
replace="assert actual_contract['explicit_known_failed_reference_diagnostic_only'] is True\\n    assert not actual_contract['adopted'] and not actual_contract['manufacturing_ready']\\n    assert actual_contract['verdict'] in ('PASS_ACTUAL_FULL_NATIVE_FILL_ALL_CU_AND_EXPLICIT_FLASH_CONTRACT','FAIL_ACTUAL_FULL_NATIVE_FILL_CU_OR_FLASH_CONTRACT')"
assert code.count(needle)==1;code=code.replace(needle,replace)
needle="extra=\"'candidate_sha256':sha(candidate),'actual_full_refill_contract':actual_contract,"
replace="extra=\"'candidate_sha256':sha(candidate),'explicit_known_failed_reference_diagnostic_only':True,'strict_old_reference_gate_pass':False,'strict_old_reference_loss_count':28,'new_R7_raw_reference_failure_preserved':True,'actual_full_refill_contract':actual_contract,"
assert code.count(needle)==1;code=code.replace(needle,replace)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
