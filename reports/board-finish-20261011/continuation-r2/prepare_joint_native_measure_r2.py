"""Prepare full native geometry/flash exports while retaining uncapped DRC gates."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'measure_joint_power_native_r1.py';o=H/'measure_joint_power_native_r2.py';assert not o.exists()
s=p.read_text();s=s.replace("measure_joint_power_backend_","measure_joint_power_backend_r2_")
anchor="    target.write_text(code,encoding='utf-8')"
inject='''    postfill=stage/'native-postfill-via-obligations.json'
    assert sha(postfill)==receipt['native_postfill_via_obligations_sha256']
    actual_helper=H/'native_final_partitions_contract_r1.py'
    original_step=Path('Z:/pcb-runs/claude-finish/tools/step_measure.sh')
    step=stage/'step_measure_all_native_r2.sh';assert not step.exists()
    ss=original_step.read_text();needle='"$T/net_partitions.py"'
    replacement='"'+actual_helper.resolve().as_posix()+'" "Z:/pcb-runs/claude-finish/tools/net_partitions.py" "'+postfill.resolve().as_posix()+'"'
    assert ss.count(needle)==1;ss=ss.replace(needle,replacement);step.write_text(ss,newline='\\n')
    a="    step=Path('Z:/pcb-runs/claude-finish/tools/step_measure.sh')"
    assert code.count(a)==1;code=code.replace(a,"    step=Path("+repr(str(step))+ ")")
    a="    for bp,pp in baselines.values():pinned.extend([bp,pp])"
    extra="    pinned.extend([Path("+repr(str(actual_helper))+"),Path("+repr(str(postfill))+"),Path("+repr(str(original_step))+")])\\n"
    assert code.count(a)==1;code=code.replace(a,extra+a)
    a="    summary=json.loads((OUT/'summary.json').read_bytes());after=json.loads((OUT/'partitions.json').read_bytes())"
    extra="    actual_contract=json.loads((OUT/'actual-full-refill-contract.json').read_bytes())\\n    if actual_contract['verdict']!='PASS_ACTUAL_FULL_NATIVE_FILL_ALL_CU_AND_EXPLICIT_FLASH_CONTRACT' or actual_contract['postfill_Cu_or_flash_errors']:raise ValueError('Actual full native Cu/flash contract failed')\\n    if actual_contract['candidate_sha256']!=sha(candidate):raise ValueError('Actual full native geometry belongs to a different candidate')\\n"
    assert code.count(a)==1;code=code.replace(a,extra+a)
    a="'candidate_sha256':sha(candidate),'summary':summary"
    extra="'candidate_sha256':sha(candidate),'actual_full_refill_contract':actual_contract,'actual_full_refill_contract_sha256':sha(OUT/'actual-full-refill-contract.json'),'actual_full_refill_geometry_sha256':sha(OUT/'actual-full-refill-geometry.json'),'actual_full_refill_via_flashes_sha256':sha(OUT/'actual-full-refill-via-flashes.json'),'summary':summary"
    assert code.count(a)==1;code=code.replace(a,extra)
    compile(code,str(target),'exec')
'''
assert s.count(anchor)==1;s=s.replace(anchor,inject+anchor)
compile(s,str(o),'exec');o.write_text(s)
(H/'joint-native-measure-r2-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'actual_native_same_loaded_project_board_all_zone_fill_uncapped_partitions_all_Cu_all_flashes_and_exact_geometry_export':True,'same_UUID_replacement_old_flashes_not_credited_as_new_ordinary':True,'existing_full_CLI_DRC_options_and_original_matching_source_all_baseline_partition_gates_preserved':True,'actual_native_helper_file':str(H/'native_final_partitions_contract_r1.py'),'actual_native_helper_sha256':sha(H/'native_final_partitions_contract_r1.py'),'native_API_and_full_refill_execution':'NOT_RUN_REQUIRES_FINAL_PASSED_STAGE','new_heavy_slots':0,'adopted':False},indent=1)+'\n')
print(json.dumps({'measure':str(o),'sha256':sha(o)}))
