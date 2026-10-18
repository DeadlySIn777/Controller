"""Conditional R715 redistribution, preserving full old-matrix failures.

Use the same explicitly omitted numerical-triangle criteria as R697. This
does not bound the full physical sheet solution or qualify any barrel.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='2'
p=psutil.Process(); p.cpu_affinity(list(range(16,28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'solve_R157_actual_FBG_complete_signed_simplex_3D_r695.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source)=='3af3fd3f98e09bfc5f1d66d0eb80218c8bc002d1780ca34c4368ad5debcd6eca'
s=source.read_text(encoding='utf-8')
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("IN = H / 'R157-actual-FBG-complete-signed-real-barrel-mesh-input-r693'", "IN = H / 'R715-one-prospective-barrel-complete-signed-native-baseline-mesh-input-r725'")
replace("OUT = H / 'R157-actual-FBG-complete-signed-simplex-3D-current-r695'", "OUT = H / 'R715-one-prospective-barrel-full-signed-explicit-numeric-subset-redistribution-r729'")
replace("assert sha(IN / 'receipt.json') == '3ba864f2dd3ede7a0de92f48ecad870e2a6535f7932d304c41ee66dd7f34734c'", """assert sha(IN / 'receipt.json') == 'cdb015a3ea113d4cba47242c4a40bda047ec847025aba8504746d0e01a8c4522'
    assert sha(H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727/receipt.json')=='b793ef3a1b887f27fb0fc013954a247c2564fee827679e9fa08a5408b4d564b8'
    assert sha(H/'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697/receipt.json')=='286df7e59b8172661e4d8a4f24b18f6f5abaf340a6c073a32379142eebd1c0af'""")
replace("np.cross(T0[:, 1] - T0[:, 0], T0[:, 2] - T0[:, 0])", "(T0[:,1,0]-T0[:,0,0])*(T0[:,2,1]-T0[:,0,1])-(T0[:,1,1]-T0[:,0,1])*(T0[:,2,0]-T0[:,0,0])")
replace("np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])", "(T[:,1,0]-T[:,0,0])*(T[:,2,1]-T[:,0,1])-(T[:,1,1]-T[:,0,1])*(T[:,2,0]-T[:,0,0])")
replace("omit = area0 < 1e-12", """max_edge_squared=np.max(np.stack([np.sum((T0[:,1]-T0[:,0])**2,axis=1),np.sum((T0[:,2]-T0[:,1])**2,axis=1),np.sum((T0[:,0]-T0[:,2])**2,axis=1)],axis=1),axis=1)
        relative_area=np.divide(area0,max_edge_squared,out=np.zeros_like(area0),where=max_edge_squared>0)
        omit=(area0<1e-12)|(relative_area<1e-8)
        np.save(OUT/(layer.replace('.','-')+'-original-all-triangle-quality.npy'),np.c_[area0,max_edge_squared,relative_area])""")
replace("'explicit_numerical_omitted_area_mm2': float(area0[omit].sum())", "'explicit_numerical_omitted_area_mm2': float(area0[omit].sum()), 'minimum_numeric_relative_area_over_longest_edge_squared': 1e-8, 'all_omitted_triangle_coordinates_and_quality_frozen': True")
replace("'conditional_voltage_envelope_within_saved_0p48V_return_policy'", "'return_voltage_alone_below_saved_0p48V_COMBINED_positive_plus_return_budget_NOT_loop_PASS'")
replace("'status': 'FULL_SIGNED_ACTUAL_FBG_SIMPLEX_DC_ENVELOPE_SOLVED_CONDITIONAL_MATERIAL_THERMAL_NATIVE_GATES_OPEN'", """'status': 'FULL_SIGNED_ONE_PROSPECTIVE_FBG_BARREL_NUMERICAL_SUBSET_DC_ENVELOPE_SOLVED_NOT_PHYSICAL_CAPACITY_QUALIFIED',
                              'R727_explicit_source_tree_and_byte_binding_receipt_SHA256':sha(H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727/receipt.json'),
                              'baseline_R697_explicit_numeric_subset_receipt_SHA256':sha(H/'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697/receipt.json'),
                              'R695_full_original_matrix_KCL_failure_and_R703_scaling_failure_preserved':True,
                              'one_new_barrel_contacts_PROSPECTIVE_NOT_observed_native':True,
                              'numeric_omission_does_NOT_automatically_upperbound_every_physical_voltage_or_barrel_current':True,
                              'same_numeric_criteria_as_R697_new_mesh_does_NOT_prove_convergence':True""")
replace("'conditional_saved_FA_FB_return_drop_policy_V': .48", "'saved_FA_FB_COMBINED_positive_plus_return_policy_V': .48")
replace("'The numerical .48V test is scoped to the FBG return; positive supply and full loop remain separate.'", "'The reported voltage is the return only; .48V is the saved COMBINED positive-supply-plus-return budget and no loop acceptance is inferred.'")
replace("print('R695_COMPLETE'", "print('R729_COMPLETE'")
generated=H/'solve_R715_full_signed_explicit_numeric_subset_r729.generated.py'
assert not generated.exists();generated.write_text(s,encoding='utf-8')
exec(compile(s,str(generated),'exec'))
