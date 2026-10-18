"""Bind seven latest LOGIC return spines and stop only the empty earlier fallback."""
from pathlib import Path
import json,hashlib,time
import psutil
H=Path(__file__).resolve().parent.parent
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,d):Path(f).write_text(json.dumps(d,indent=1)+'\n')
oldspec=H/'sbc-power/major-rail-extra-source-input-r116.json';assert sha(oldspec)=='c94d72e10727a54a5569f4c77ea9c8f20556b0369d1ff62cde65742018f37d1c'
spec=json.loads(oldspec.read_bytes());rp=H/'logic-return-r18-snapshot-1';qf=rp/'proposed-zones.pkl';rf=rp/'receipt.json'
assert sha(qf)=='943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42'
rr=json.loads(rf.read_bytes());assert rr['parent_model_sha256']=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8' and rr['accepted_shapes']==7
spec['hard_only_peer_proposals'].append({'zones_file':str(qf.resolve()),'zones_sha256':sha(qf),'receipt_file':str(rf.resolve()),'receipt_sha256':sha(rf),'expected_zone_shapes':7,'new_holes':0,'new_tracks':0,'no_source_current_or_contact_credit_from_hard_nominees':True})
spec['CORE1V2_source_layer_priority_explicitly_In4_first']=True
sp=H/'sbc-power/major-rail-prioritized-extra-source-input-r118.json';assert not sp.exists();write(sp,spec)
old=H/'sbc-power/major-rail-extra-source-layer-feeds-r115';assert old.exists() and not list(old.iterdir())
matches=[]
for q in psutil.process_iter(['pid','cmdline']):
    try:
        cmd=q.info['cmdline'] or []
        if any(a.replace('\\','/').endswith('/construct_major_rail_extra_source_fallback_r115.py') for a in cmd) and any(a.replace('\\','/').endswith('/major-rail-extra-source-input-r116.json') for a in cmd):matches.append(q)
    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
assert len(matches)==1;pr=matches[0];cmd=pr.cmdline();assert any(a.replace('\\','/').endswith('/launch_confined_host.py') for a in cmd)
record={'verdict':'EMPTY_FIRST_LAYER_ORDER_RUN_REPLACED_WITH_EXPLICIT_IN4_PRIORITY_AND_LATEST7_HARD_GROUND_SPINES','PID':pr.pid,'command_line':cmd,'creation_unix':pr.create_time(),'accepted_geometry':0,'cpu_user_seconds':pr.cpu_times().user,'cpu_system_seconds':pr.cpu_times().system,'successor_input_sha256':sha(sp),'later_LOGIC_snapshot_sha256':sha(qf),'original_source_and_evidence_preserved':True,'native_jobs':0,'board_written':False,'stopped_unix':time.time()}
pr.terminate();pr.wait(timeout=10);write(old/'deliberate-stop-receipt-r118.json',record)
print('PRIORITIZED_IN4_INPUT',sha(sp),'STOPPED_ONLY_EMPTY_R115',pr.pid,flush=True)
