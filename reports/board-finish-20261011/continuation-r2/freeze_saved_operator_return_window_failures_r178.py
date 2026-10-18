"""Supplement diagnostic failures without changing pinned recipes or native jobs."""
import hashlib,json,math,pickle
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
policy=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');text=policy.read_text();assert 'Everywhere else the 0.90-1.0 mm stitch window and the 0.8 mm via spacing are unchanged.'in text
model=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';h=pickle.loads(model.read_bytes())[1];via={v['uuid']:v for v in h['vias']}
pairsfile=H/'coupled-recovery/DIC-C1022-actual-R250-original-guard-independent-r264/three-real-paired-returns-after-combined-holes.json';pairs=json.loads(pairsfile.read_bytes());rows=[]
for r in pairs:
 s=via[r['signal_UUID']];g=via[r['return_UUID']];dist=math.dist([s['x'],s['y']],[g['x'],g['y']]);assert abs(dist-r['actual_distance_mm'])<1e-12
 alternatives=[{'UUID':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':math.dist([s['x'],s['y']],[v['x'],v['y']]),'nominal_host_flashes':v.get('flashed'),'actual_source_In1_In4_annuli_and_native_masks':'REQUIRED_SEPARATE_PROOF'}for v in h['vias']if v['net'].replace('{slash}','/')=='/LOGIC_GND'and .90<=math.dist([s['x'],s['y']],[v['x'],v['y']])<=1.0]
 rows.append({'signal_UUID':s['uuid'],'designated_return_UUID':g['uuid'],'actual_distance_mm':dist,'designated_pair_saved_operator_window_pass':.90<=dist<=1.0,'saved_window_mm':[.90,1.0],'D4_applied':False,'existing_other_returns_inside_window_nomination_only':alternatives,'no_global_absence_or_electrical_failure_claim':True})
assert len(rows)==3 and not any(r['designated_pair_saved_operator_window_pass']for r in rows)
out=H/'saved-operator-return-window-supplemental-failure-r178';assert not out.exists();out.mkdir();(out/'operator-decisions-exact-snapshot.md').write_bytes(policy.read_bytes())
receipt={'verdict':'ADDITIONAL_DESIGNATED_RETURN_POLICY_FAILURES_DIAGNOSTIC_ONLY_NO_COPPER_CHANGE','saved_operator_policy_file':str(policy),'saved_operator_policy_sha256':sha(policy),'current_R155_model_sha256':sha(model),'designated_pair_receipt_file':str(pairsfile),'designated_pair_receipt_sha256':sha(pairsfile),'rows':rows,'U10003_R176_designated_pairs_mm':[.8266868844496132,1.321091034751669],'U10003_R176_return_policy_qualification':'FAIL_NON_D4_SAVED_WINDOW; no acceptance','frozen_R312_failure_ledger_or_running_native_inputs_modified':False,'original_failed_receipts_preserved':True,'adopted':False,'manufacturing_ready':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'designated_pair_policy_failures':len(rows),'other_return_nominees_counts':[len(r['existing_other_returns_inside_window_nomination_only'])for r in rows]}),flush=True)
