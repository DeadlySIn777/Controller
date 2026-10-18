"""Prepare existing-barrel LOGIC_GND restoration after corrected field returns freeze."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'repair_protected_field_returns_r4.py';out=H/'repair_logic_existing_returns_r6.py';r=H/'logic-existing-returns-r6-derivation.json'
assert not out.exists() and not r.exists();s=p.read_text()
start=s.index(" mp=Path(sys.argv[1]).resolve();pins=");end=s.index(" assert not OUT.exists();",start)
block=""" mp=Path(sys.argv[1]).resolve();mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes())
 assert sha(mp)==r['model_sha256'] and r['only_new_R4_return_shapes_changed'] is True
 assert r['baseline_model_sha256']=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff'
 assert r['new_holes']==r['old_Cu_deleted']==r['old_native_zone_outlines_changed']==0
 assert r['script_sha256']==sha(H/'normalize_regional_return_outward_r5.py')
 assert all(x['all_R4_prior_actual_source_contacts_retained'] and x['all_R4_accepted_targets_actual_source_rooted'] for x in r['outward_actual_source_proofs'])
"""
s=s[:start]+block+s[end:]
s=s.replace("OUT=H/'protected-field-return-restoration-r4'","OUT=H/'logic-existing-return-restoration-r6'")
needle="[('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]";assert s.count(needle)==1;s=s.replace(needle,"[('/LOGIC_GND','J11001')]")
s=s.replace("controller-protected-ground-r4/","controller-logic-existing-return-r6/").replace('Protected supply return restoration R4','Logic existing-barrel return restoration R6').replace('RETURN_R4_FROZEN','LOGIC_RETURN_R6_FROZEN')
# Source-level legal contours receive an explicit 20nm construction reserve;
# the independent physical requirement remains the original full0.025mm guard.
s=s.replace('gap(q[\'net\'])+.025','gap(q[\'net\'])+.025+.000020')
s=s.replace("float(q.get('clearance_mm',.15)))+.025)","float(q.get('clearance_mm',.15)))+.025+.000020)")
s=s.replace("gap(craw)+.025)","gap(craw)+.025+.000020)")
s=s.replace("N.bounded_buffer(s,.025)","N.bounded_buffer(s,.025+.000020)")
compile(s,str(out),'exec');out.write_text(s)
r.write_text(json.dumps({'parent_constructor_sha256':sha(p),'derived_constructor_sha256':sha(out),'parent_must_be_frozen_outward_corrected_R5_with_actual_field_ground_source_contacts_retained':True,'target_net_and_actual_source':'/LOGIC_GND J11001.2','ordinary_existing_barrels_only_no_new_Cu_holes_or_removals':True,'same_authoritative_source_only_and_fullbank_projector_equality_gate':True,'explicit_legal_construction_extra_outward_mm':.000020,'all_other_net_contact_current_reference_native_refill_DRC':'OPEN','finite_route_failure_is_not_proof_of_no_path':True,'not_run':True,'native_jobs':0},indent=1)+'\n')
print(json.dumps({'script':str(out),'sha256':sha(out)}))
