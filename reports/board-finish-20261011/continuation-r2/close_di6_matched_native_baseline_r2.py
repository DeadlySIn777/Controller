"""Close only the completed native export, without rerunning or altering it.

The R1 orchestration failed after the successful native child because its hash
helper did not accept string paths. This verifies every frozen child input and
output independently and preserves that orchestration failure as evidence.
"""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
O=H/'di6-matched-native-baseline-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
assert not (O/'receipt-r2.json').exists()
pins=read(O/'inputs.json')
assert all(sha(p)==v for p,v in pins.items())
r=read(O/'scoped-native-fill/receipt.json')
assert r['verdict']=='PASS_SCOPED_LOGIC_GND_NATIVE_REFILL_EXPORT_RAW_COPPER'
assert r['filler_ok'] and r['all_discrete_post_fill_errors']==[] and r['board_or_project_saved'] is False
assert r['candidate_sha256']==sha(O/'copy/board.kicad_pcb')=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
assert all(sha(p)==v for p,v in r['input_sha256'].items())
for key,name in [('geometry_sha256','geometry.json'),('actual_via_flashes_sha256','actual-via-flashes.json')]:
 assert sha(O/'scoped-native-fill'/name)==r[key]
after=H/'di6-native-diagnostic-r1/scoped-native-fill/receipt.json'
a=read(after)
assert a['verdict']==r['verdict'] and a['selected_raw_net']==r['selected_raw_net']=='/LOGIC_GND'
assert a['selected_zone_UUIDs']==r['selected_zone_UUIDs']
for ext in ('.kicad_pro','.kicad_dru'):
 assert sha((O/'copy/board.kicad_pcb').with_suffix(ext))==sha((H/'di6-native-diagnostic-r1/copy/board.kicad_pcb').with_suffix(ext))
record={'verdict':'PASS_MATCHED_NATIVE_BEFORE_EXPORT_DI6_DELTA_REVIEW_OPEN','candidate_sha256':r['candidate_sha256'],'exact_same_source_pose_project_rules_and_fill_helper_as_after':True,'only_exact_DI6_11additions_absent':True,'fresh_selected_raw_net':'/LOGIC_GND','native_child_verdict':r['verdict'],'R1_orchestration_failure_preserved':'AttributeError in post-child sha(str) input-pinning assertion; native child completed and its receipt independently verified here','frozen_input_pins':pins,'native_export_receipt_sha256':sha(O/'scoped-native-fill/receipt.json'),'after_native_export_receipt_sha256':sha(after),'geometry_sha256':r['geometry_sha256'],'actual_via_flashes_sha256':r['actual_via_flashes_sha256'],'same_selected_native_zone_UUIDs':True,'script_sha256':sha(__file__),'rerun_native_jobs':0,'all_other_fills_and_final_joint_source_reference_current_DRC_SI':'OPEN','adopted':False}
(O/'receipt-r2.json').write_text(json.dumps(record,indent=1)+'\n')
print(json.dumps({k:record[k]for k in ('verdict','geometry_sha256','actual_via_flashes_sha256')}))
