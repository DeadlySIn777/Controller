"""Preserve R1 and prepare an audit bound to the actual corrected R9 recipe."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=H/'audit_protected_joint_model_r1.py';dst=H/'audit_protected_joint_model_r2.py'
assert not dst.exists()
s=src.read_text(encoding='utf-8')
s=s.replace("rp=H/'protected24-dogbones-r7'", "rp=H/'protected24-on-corrected-core-r9'")
s=s.replace("assert binding==bb", "assert binding==bb\n    assert sha(jointfile)==json.loads(jointfile.with_name('receipt.json').read_bytes())['model_sha256']\n    assert sha(basefile)=='91710ee78e3b35c7903bc590292af2fd3eccbb514589fd9a7553a76772f6f4db'")
s=s.replace("out.mkdir();errors=[];physical_errors=[];zone_errors=[]", """# The input is the actual accepted constructive model, including its exact
    # restored return shapes. Never audit stale R7 positive polygons here.
    byid={q['uuid']:q for q in zones}
    assert all(q['uuid'] in byid and q['shape'].equals(byid[q['uuid']]['shape']) for q in added)
    before_cu={q['uuid']:q for k in ('tracks','vias') for q in bh[k]}
    after_cu={q['uuid']:q for k in ('tracks','vias') for q in h[k]}
    added_cu={q['uuid']:q for k in ('tracks','vias') for q in new[k]}
    assert set(after_cu)-set(before_cu)==set(added_cu)
    assert not set(before_cu)-set(after_cu)
    assert all(after_cu[u]==q for u,q in before_cu.items())
    assert all(after_cu[u]==q for u,q in added_cu.items())
    assert h['pads']==bh['pads'] and h['rule_areas']==bh['rule_areas']
    out.mkdir();errors=[];physical_errors=[];zone_errors=[]""")
s=s.replace("bodies.extend((q['uuid'],q['net'],q['layer'],q['shape'],'protected_new_plane') for q in added)", "bodies.extend((q['uuid'],q['net'],q['layer'],q['shape'],'all_actual_final_owned_plane') for q in zones)")
s=s.replace("'original198b_and_native_dc936_full_source_obligations':'SEPARATE_OPEN'", "'exact_original_discrete_preservation':'PASS', 'R38_corrected_CORE_source_baseline_bound':True, 'actual_R9_recipe_and_all_final_owned_zone_shapes_audited':True, 'original198b_and_native_dc936_full_source_obligations':'SEPARATE_OPEN'")
dst.write_text(s,encoding='utf-8')
(H/'protected-joint-audit-r2-derivation.json').write_text(json.dumps({'source':str(src.resolve()),'source_sha256':sha(src),'derived':str(dst.resolve()),'derived_sha256':sha(dst),'changes':['Bind corrected R38 baseline and actual R9 recipe hashes','Check exact unchanged existing discrete/pads/rules and exact protected additions','Audit actual final owned zone shapes against all discrete Cu, rather than stale R7 polygons'],'runs_native':False,'adopted':False},indent=1)+'\n',encoding='utf-8')
compile(s,str(dst),'exec')
print(sha(dst))
