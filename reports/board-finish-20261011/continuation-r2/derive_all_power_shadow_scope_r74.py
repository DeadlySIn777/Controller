"""Investigate exact source-reviewed DC-power candidates, preserving all raw failed gates."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'restore_old_ground_reference_masks_r71.py';dst=H/'restore_old_ground_reference_masks_r74.py'
assert not dst.exists()
s=src.read_text().replace('SAFE-old-source-ground-reference-power-scope-proposal-r71','SAFE-old-source-ground-reference-power-scope-proposal-r74').replace('R71_','R74_')
def sub(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a))
 s=s.replace(a,b)
sub("mp=H/'SAFE-logic-four-return-restoration-r55/model.pkl';assert sha(mp)=='5499e67855ab47dcf207a3421c5bb630b56af52031e06c90e270312baf03232b'", "mp=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';assert sha(mp)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011'")
sub("parentgroups=pickle.loads(ng.read_bytes())", "parentgroups={net:F.graph(current,net) for net in ['/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V','/IO_3V3','/CORE_1V2','/mc_local_power/CORE_5V']}")
sub("basez=[q for q in z if q['uuid']!='ec99314b-c244-5748-bb67-de032c66ee3c']", "extra_UIDs={'ec99314b-c244-5748-bb67-de032c66ee3c','93bd9369-a6ff-537a-8678-5c84db255e75'};basez=[q for q in z if q['uuid'] not in extra_UIDs];assert len(basez)==36")
a=" extra=next(q for q in z if q['uuid']=='ec99314b-c244-5748-bb67-de032c66ee3c')\n for key in ('shape','zone_outline_shape'):\n  if key not in extra:continue\n  before=digest(extra[key]);extra[key]=set_precision(extra[key],1e-6,mode='pointwise');assert digest(extra[key])==before\n  precision.append({'UUID':extra['uuid'],'role':key,'grid_mm':1e-6,'WKB_before_after_exact':before,'constructor_origin':'repair_SAFE_logic_four_return_r55.py nm-quantized new owned strip'})"
b=" for extra in [q for q in z if q['uuid'] in extra_UIDs]:\n  for key in ('shape','zone_outline_shape'):\n   if key not in extra:continue\n   before=digest(extra[key]);extra[key]=set_precision(extra[key],1e-6,mode='pointwise');assert digest(extra[key])==before\n   precision.append({'UUID':extra['uuid'],'role':key,'grid_mm':1e-6,'WKB_before_after_exact':before,'constructor_origin':'exact nm-quantized ROOT55 or ROOT73 new owned strip'})"
sub(a,b)
start=" lostby['/LOGIC_GND']-=power_UIDs;assert sum(map(len,lostby.values()))==283"
extended=""" reviewfile=H/'sbc-power/remaining84-power-shadow-source-resolved-tap-review-r204/receipt.json';assert sha(reviewfile)=='0f0c7b723c2f010dd7af20e935eed7afd946cf61badef0819f6ad7f16fd43801';review=json.loads(reviewfile.read_bytes());assert review['source_sha256']==proposal['source_sha256']=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 remaining=review['literal84_rows'];other_UIDs={q['exact_track_UUID']for q in remaining};assert len(other_UIDs)==84 and not(power_UIDs & other_UIDs)and other_UIDs<=lostby['/LOGIC_GND']
 for row in remaining:
  assert row['classification']=='LITERAL_SOURCE_BACKED_DC_SUPPLY_DISTRIBUTION_CANDIDATE_REQUIRES_PDN_QUALIFICATION'and not row['row_exempted']
  assert bytrack[row['exact_track_UUID']]==row['actual_current_native_track'],'Only exact source-reviewed native track geometry may enter this proposal'
 power_UIDs |= other_UIDs;assert len(power_UIDs)==104
 lostby['/LOGIC_GND']-=power_UIDs;assert len(lostby['/LOGIC_GND'])==130 and sum(map(len,lostby.values()))==199
 put(out/'additional84-source-backed-PDN-proposal.json',{'source_review_sha256':sha(reviewfile),'exact104_literal_DC_distribution_track_UUIDs':sorted(power_UIDs),'all130_logic_signal_shadows_hard':True,'all56_FA_and13_FB_shadows_hard':True,'original_raw_reference_FAIL_unchanged':True,'PDN_current_decoupling_loop_ground_return_stability_transient_native':'OPEN','not_a_board_release_waiver':True})"""
sub(start,extended)
s=s.replace("'exact20_own_rail_track_UUIDs'", "'exact104_source_reviewed_power_track_UUIDs'")
s=s.replace("'own_rail_classification_proposal_sha256':sha(proposalfile)", "'own_rail_classification_proposal_sha256':sha(proposalfile),'other84_power_source_review_sha256':sha(reviewfile),'literal_power_scope104_pending_PDN':True")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'all-power-shadow-scope-r74-derivation.json').write_text(json.dumps({'source_constructor_sha256':sha(src),'derived_constructor_sha256':sha(dst),'parent':'Exact ROOT73 complete monitor operation and source-connected strip on SBC183 plus ROOT55','change':'Only104 literal source-reviewed DC distribution candidates omitted from constructive signal-shadow mask, all130 real signals and69 field shadows remain hard. Saved original checker FAIL preserved. No production gate change.','all104_candidate_PDN_replacement_qualification':'OPEN','native_jobs':0,'adopted':False},indent=1)+'\n')
print(dst)
