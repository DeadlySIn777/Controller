"""Pin the later exact joint head and stop only our empty earlier host search."""
from pathlib import Path
import hashlib,json,time
import psutil
H=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n')
mp=H/'field-power/corrected-regulated-native-bound-search-base-r111/model.pkl';mr=mp.with_name('receipt.json')
assert sha(mp)=='722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8'
assert sha(mr)=='27c890a9ea46f89ddbbbc42015037c4a292df652fffe0d8cc95c162bf1b375a3'
spec={'model_file':str(mp),'model_sha256':sha(mp),'receipt_file':str(mr),'receipt_sha256':sha(mr),
      'all_later_actual_model_geometry_is_hard':True,'no_native_or_source_adoption':True,
      'CORE1V2_full_fitted_load_A':.8,'IO3_full_fitted_envelope_A':2.,
      'actual_new_root_R10_FBG_spine_uuid':'d480dd23-09f4-5c53-bc5b-0bee7c7536ff',
      'source_root_labels':{'/CORE_1V2':'L2001.2','/IO_3V3':'R18001.2'},
      'field_REG_nominees_in_head_are_geometry_obstacles_not_accepted_current_or_source_qualification':True}
sp=H/'sbc-power/major-rail-lazy-input-r109.json';assert not sp.exists();write(sp,spec)
old=H/'sbc-power/major-rail-existing-annulus-feeds-r93';assert old.exists()
assert not list(old.iterdir()),'Earlier run has concrete results; inspect them instead of treating it as empty'
p=psutil.Process(32540);cmd=p.cmdline();assert any('construct_major_rail_annuli_r93.py' in q for q in cmd)
assert any('unused-new-core-fragment-removal-r91/model.pkl' in q.replace('\\','/') for q in cmd)
record={'verdict':'DELIBERATELY_STOPPED_EMPTY_EAGER_REGION_HOST_SEARCH_FOR_LATER_SOURCE_FILTERED_SUCCESSOR',
        'PID':p.pid,'command_line':cmd,'creation_unix':p.create_time(),'cpu_user_seconds':p.cpu_times().user,
        'cpu_system_seconds':p.cpu_times().system,'output_files_before_stop':[],
        'accepted_geometry':0,'does_not_prove_no_path':True,'source_script_sha256':sha(H/'sbc-power/construct_major_rail_annuli_r93.py'),
        'successor_script_sha256':sha(H/'sbc-power/construct_major_rail_lazy_annuli_r108.py'),
        'successor_input_binding_sha256':sha(sp),'all_original_evidence_preserved':True,
        'native_jobs':0,'board_written':False,'stopped_unix':time.time()}
p.terminate();p.wait(timeout=10);write(old/'deliberate-stop-receipt-r109.json',record)
print('STOPPED_ONLY_EMPTY_R93',record['PID'],'NEW_INPUT',sha(sp),'BASE',sha(mp))
