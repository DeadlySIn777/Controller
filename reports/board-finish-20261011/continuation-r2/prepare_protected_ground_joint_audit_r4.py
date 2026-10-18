"""Bind the root ground repair audit to the current full CORE parent."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'audit_protected_joint_model_r2.py';out=H/'audit_protected_ground_joint_model_r4.py';assert not out.exists()
s=p.read_text()
s=s.replace("assert sha(basefile)=='91710ee78e3b35c7903bc590292af2fd3eccbb514589fd9a7553a76772f6f4db'","assert sha(basefile)=='3e4e42806786d7d15f66f8029f674db50c4df235adcea16d2f5d7a19b7757baa'")
old="    assert all(q['uuid'] in byid and q['shape'].equals(byid[q['uuid']]['shape']) for q in added)"
new="""    guarded_base=H/'sbc-power/core-protected-outward-joint-r59/model.pkl'
    assert sha(guarded_base)=='a77ba8a283d9b1e856ec6e4627363f9ba413e9db5c5af4c5fa1b8e3c41c32682'
    guarded_receipt=guarded_base.with_name('receipt.json');assert sha(guarded_receipt)=='f8acc308e831626bdd3076022122969dded931c260cd2016700c65fa23ed45fa'
    _,gh,gb,gzs,gcurrent=pickle.loads(guarded_base.read_bytes());assert gh==h and gb==bb
    reference={q['uuid']:q for q in gzs}
    assert all(q['uuid'] in byid and q['shape'].equals(byid[q['uuid']]['shape']) for q in gzs)
    assert all(q['uuid'] in reference for q in added)
    repair=H/'protected-field-return-restoration-r3';repair_rows=pickle.loads((repair/'proposed-zones.pkl').read_bytes())
    assert set(byid)-set(reference)=={q['uuid'] for q in repair_rows}
    assert all(byid[q['uuid']]['shape'].equals(q['shape']) for q in repair_rows)"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("rp/'proposed-zones.pkl',Path(F.__file__)","rp/'proposed-zones.pkl',guarded_base,guarded_receipt,repair/'receipt.json',repair/'proposed-zones.pkl',Path(F.__file__)")
s=s.replace("'R38_corrected_CORE_source_baseline_bound':True","'R48_all15_CORE_source_branch_baseline_bound':True,'R59_exact_normalized_protected_positives_and_owned_return_carves_bound':True")
s=s.replace('PASS_PROTECTED_LATEST_MODEL_MUTUAL_CONTACT_NATIVE_CURRENT_OPEN','PASS_PROTECTED_AND_GROUND_LATEST_MODEL_MUTUAL_CONTACT_NATIVE_CURRENT_OPEN')
compile(s,str(out),'exec');out.write_text(s)
r=H/'protected-ground-joint-audit-r4-derivation.json';assert not r.exists();r.write_text(json.dumps({'prior_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_script_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'baseline_R48_all15CORE_branches_and_exact12protected_additions':True,'R59_each_preexisting_guarded_zone_shape_exact_required':True,'rootR3_additional_return_shapes_explicit_only':True,'all_mutual_physical_Cu_analytic_clearances_apertures_and_retained_contacts_rechecked':True,'original198b_native_dc936_all_source_and_current_gates':'SEPARATE_OPEN'},indent=1)+'\n')
print(json.dumps({'script':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
