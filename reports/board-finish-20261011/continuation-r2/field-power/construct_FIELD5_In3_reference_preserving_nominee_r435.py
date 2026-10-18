"""Test only a new owned FIELD5 In3 replacement; no original Cu edits."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'construct_FIELD5_inner_native_fill_retreat_nomination_r385.py'
ns={'__file__':str(owner),'__name__':'_load_native_retreat_nomination_without_run'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('native-fill-retreat-replacement-nomination-r385','In3-only-original-IO3-preserving-replacement-nomination-r435')
s=s.replace("for layer in ('In2.Cu','In3.Cu'):","for layer in ('In3.Cu',):")
s=s.replace("for core in (1.0,.75,.5):","for core in (.5,.35,.30):")
s=s.replace("assert layer in source['flashed']and layer in target['flashed']", "assert layer in source['flashed']and layer in target['flashed'],('actual_source_target_host_flash_missing',source['flashed'],target['flashed']);write(O/'source-target-host-flash-binding.json',{'source_UUID':source['uuid'],'source_host_masks':source['flashed'],'target_UUID':target['uuid'],'target_host_masks':target['flashed'],'actual_native_flash_annular_source_gate':'OPEN_NO_NATIVE_ASSUMPTION'})")
s=s.replace("'controller/FIELD5/R385/'+layer", "'controller/FIELD5/R435/'+layer")
s=s.replace("'all_contact_source_reference_true_geometry_current_and_native_gates':'OPEN'", "'all_contact_source_reference_true_geometry_current_and_native_gates':'OPEN'")
s=s.replace("'native_jobs':0", "'prior_failed_In2_IO3_383_key_split':'PRESERVED_NOT_OVERLAID','new_feed_current_reservation_A':.36,'sheet_loop_drop_temperature_and_native':'OPEN_NO_WIDTH_RATING','native_jobs':0")
exec(compile(s,str(H/'construct_FIELD5_inner_reference_safe_replacement_r383.py'),'exec'))
