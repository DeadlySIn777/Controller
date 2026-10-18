"""Continue existing-barrel feeds from actual source-qualified R135 geometry."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
s=(H/'construct_major_rail_regional_logged_source_exit_r125.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
replace("OUT=H/'sbc-power/major-rail-regional-logged-source-exit-r125';", "OUT=H/'sbc-power/post-native-major-rail-existing-barrel-completion-r140';")
replace("if net=='/CORE_1V2' and layer=='In4.Cu' and q['uuid']==coupled_uid:obstruction=obstruction.difference(escape)", "if False:raise AssertionError('No additional CORE plane carve is authorized in R140')")
a=s.index("     if net=='/CORE_1V2' and layer=='In4.Cu':\n      oldq=");b=s.index("     selected={**h,'zones':",a)
s=s[:a]+s[b:]
replace("for radius in (5.,15.,35.,75.,800.):", "for radius in (5.,15.,35.,75.,125.,175.,800.):")
s=s.replace('controller-major-rail-regional-source-exit-r125/','controller-post-native-major-rail-completion-r140/').replace('Major rail regional bounded owned source exit R125','Post-native existing-barrel source continuation R140').replace('MAJOR_RAIL_REGIONAL_SOURCE_R125_FROZEN','POST_NATIVE_MAJOR_RAIL_R140_FROZEN')
out=H/'construct_post_native_major_rail_completion_r140.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
root=H.parent;mp=H/'CORE1V2-source-native-outline-correction-r135/model.pkl';rf=mp.with_name('receipt.json');assert sha(mp)=='729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca'
peers=[]
for folder,qsha,rsha,ds in [
 ('field-power/regulated-four-retained-hard-snapshot-r127','82ab625dbe9310aa1287321a1e96f814a3408dead04200a8c4340882edf1b589','66f83482cf96300b4fdfbeba537263c935fb46d61d791c29e7aee8df1706e85f','9651216efa39c190b8731162251cb4b68f6313f1b12c62f5eab45d2a452c891b'),
 ('safe-logic-five-and-fag-margin-r22','6265fec242e72d2453b1a478ee685bbf3df470540d7a682872a451ffca2d80a1','988c0f5d7fad8966699640e8c0c74ab5a23df99ed9c29eb1f4509f2a0f6cdcbe',None),
 ('field-power/regulated-reference-safe-source-replacements-r121','b53cb86a8827b613d2350952d5a76227bb52d5d666884136f416274e7a67aa03',None,None)]:
 qf=root/folder/'proposed-zones.pkl';rr=root/folder/'receipt.json';assert sha(qf)==qsha
 if rsha:assert sha(rr)==rsha
 qs=__import__('pickle').loads(qf.read_bytes());row={'zones_file':str(qf.resolve()),'zones_sha256':sha(qf),'receipt_file':str(rr.resolve()),'receipt_sha256':sha(rr),'expected_zone_shapes':len(qs),'no_source_current_or_contact_credit_from_hard_nominees':True}
 if ds:
  df=root/folder/'proposed-discrete.pkl';assert sha(df)==ds;row.update(discrete_file=str(df.resolve()),discrete_sha256=ds)
 else:row.update(new_holes=0,new_tracks=0)
 peers.append(row)
native=root/'core1v2-native-diagnostic-r138/independent-selected-CORE1V2-r139.json';nr=json.loads(native.read_bytes());assert nr['verdict']=='PASS_SELECTED_NATIVE_CORE1V2_SOURCE_PAIR_BARREL_AND_ANNULUS' and nr['exact_integer_expected25_pad_keys_source_retained']
spec={'model_file':str(mp.resolve()),'model_sha256':sha(mp),'receipt_file':str(rf.resolve()),'receipt_sha256':sha(rf),'all_later_actual_model_geometry_is_hard':True,'no_native_or_source_adoption':True,'selected_actual_native_source_f6_F_In3_and_In4_and25pads_proof_file':str(native.resolve()),'selected_actual_native_source_proof_sha256':sha(native),'full_final_native_source_and_current_still_required':True,'hard_only_peer_proposals':peers,'no_further_CORE_source_exit_carve_authorized':True}
ip=H/'post-native-major-rail-completion-input-r140.json';assert not ip.exists();ip.write_text(json.dumps(spec,indent=1)+'\n')
print('POST_NATIVE_COMPLETION_READY',sha(out),sha(ip))
