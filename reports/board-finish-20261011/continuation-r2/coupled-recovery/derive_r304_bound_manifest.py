from pathlib import Path
H=Path(__file__).resolve().parent
dst=H/'freeze_known_failed_reference_manifest_r304.py';assert not dst.exists()
s=(H/'freeze_known_failed_reference_manifest_r300.py').read_text()
s=s.replace('diagnostic-manifest-r300','diagnostic-manifest-r304').replace('production-failures-r300','production-failures-r304')
needle="for authority in row['exact_source_authorities']:pin(authority['file'],authority['sha256'])"
assert s.count(needle)==1
s=s.replace(needle,"for authority in row['exact_source_authorities']:\n  if 'file'in authority:pin(authority['file'],authority['sha256'])\n  else:pin(authority['model_file'],authority['model_sha256'])")
needle="'strict_old_reference_gate_pass':False,'full_new_reference_gate_pass':False,'raw_R368_strict_old_reference_rows'"
assert s.count(needle)==1
s=s.replace(needle,"'strict_old_reference_gate_pass':False,'strict_old_reference_loss_count':28,'new_R7_raw_reference_failure_preserved':True,'all_raw_old_and_new_reference_planner_CORE_current_ROOT42_native_failures_preserved':True,'full_new_reference_gate_pass':False,'raw_R368_strict_old_reference_rows'")
dst.write_text(s,encoding='utf-8',newline='\n')
dst=H/'run_R155_failure_bound_emitter_r306.py';assert not dst.exists()
s=(H/'run_R155_failure_bound_emitter_r302.py').read_text().replace('diagnostic-manifest-r300','diagnostic-manifest-r304').replace('native-recipe-r302','native-recipe-r306')
dst.write_text(s,encoding='utf-8',newline='\n')
