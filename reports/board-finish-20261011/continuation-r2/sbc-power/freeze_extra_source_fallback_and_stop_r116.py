"""Pin an explicit layer hypothesis and replace only our empty host search."""
from pathlib import Path
import json,hashlib,time
import psutil
H=Path(__file__).resolve().parent.parent
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,d):Path(f).write_text(json.dumps(d,indent=1)+'\n')
mp=H/'sbc-power/core1v2-extra-In4-source-guarded-input-r112/model.pkl';mr=mp.with_name('receipt.json')
assert sha(mp)=='b58fed8889bb7fed0f5460e16680d7c56fc69b14e04b5f528c98e1fa6811c8b7' and sha(mr)=='b60760a1dd0618075e46d83a683138a59c7b361f8a71b62307415f411e097053'
peer=H/'field-power/regulated-quantized-inner-source-feeds-r114';qf=peer/'proposed-zones.pkl';df=peer/'proposed-discrete.pkl';rf=peer/'receipt.json'
assert sha(qf)=='3069a86cc9a1c1e7d192bede4285a697e78f878932f84ae7458c62f931c54dab'
assert sha(df)=='9651216efa39c190b8731162251cb4b68f6313f1b12c62f5eab45d2a452c891b' and sha(rf)=='15b86661ee65d1961e865caea2862346757c7a9ff70aa47101b6d62cf9812eef'
spec={'model_file':str(mp.resolve()),'model_sha256':sha(mp),'receipt_file':str(mr.resolve()),'receipt_sha256':sha(mr),
      'all_later_actual_model_geometry_is_hard':True,'no_native_or_source_adoption':True,
      'exact_source_via_f6ad_original_F_In3_retained_additional_In4_prospective':True,
      'all_original_foreign_fills_and_contact_require_fresh_final_reprojection':True,
      'hard_only_peer_proposals':[{'zones_file':str(qf.resolve()),'zones_sha256':sha(qf),'discrete_file':str(df.resolve()),'discrete_sha256':sha(df),'receipt_file':str(rf.resolve()),'receipt_sha256':sha(rf),'expected_zone_shapes':6,'new_vias':3,'new_tracks':6,'no_source_current_or_contact_credit_from_hard_nominees':True}]}
sp=H/'sbc-power/major-rail-extra-source-input-r116.json';assert not sp.exists();write(sp,spec)
old=H/'sbc-power/major-rail-lazy-existing-annulus-feeds-r108';assert old.exists() and not list(old.iterdir()),'Inspect any earlier concrete results before replacing this run'
matches=[]
for q in psutil.process_iter(['pid','name','cmdline']):
    try:
        cmd=q.info['cmdline'] or []
        if any(a.replace('\\','/').endswith('/construct_major_rail_lazy_annuli_r108.py') for a in cmd) and any(a.replace('\\','/').endswith('/major-rail-lazy-input-r109.json') for a in cmd):matches.append(q)
    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
assert len(matches)==1,[q.pid for q in matches];p=matches[0];cmd=p.cmdline()
assert any(a.replace('\\','/').endswith('/launch_confined_host.py') for a in cmd)
record={'verdict':'DELIBERATELY_STOPPED_EMPTY_FIRST_SOURCE_LAYER_HOST_SEARCH_FOR_EXPLICIT_BOUNDED_LAYER_HYPOTHESIS',
        'PID':p.pid,'command_line':cmd,'creation_unix':p.create_time(),'cpu_user_seconds':p.cpu_times().user,'cpu_system_seconds':p.cpu_times().system,
        'accepted_geometry':0,'last_observed_stage':'all nine actual FPGA In3 ports at75mm produced no admissible route; first800mm legal region begun',
        'finite_failed_region_and_deliberate_stop_are_not_no_path_proof':True,'original_source_and_input_evidence_preserved':True,
        'successor_input_binding_sha256':sha(sp),'successor_script_sha256':sha(H/'sbc-power/construct_major_rail_extra_source_fallback_r115.py'),
        'native_jobs':0,'board_written':False,'stopped_unix':time.time()}
p.terminate();p.wait(timeout=10);write(old/'deliberate-stop-receipt-r116.json',record)
print('STOPPED_ONLY_EMPTY_R108',p.pid,'EXTRA_SOURCE_INPUT',sha(sp),'BASE',sha(mp),flush=True)
