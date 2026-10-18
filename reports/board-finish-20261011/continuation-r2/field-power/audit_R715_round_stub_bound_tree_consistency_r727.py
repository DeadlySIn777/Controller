"""Pinned successor of R723; make returned broad-phase trees consistent.

K.physical rebuilds its own trees, so prior graph calculation did not use
the returned trees. Preserve the prior run and validate its group identity.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='2'
p=psutil.Process(); p.cpu_affinity(list(range(16,28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib, json
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'audit_R715_true_round_new_stub_direct_source_r723.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source)=='29fa1fccd3140d28781cb8895a713a1c31012a0ff5d5a7f393150b9fba28e46b'
s=source.read_text(encoding='utf-8')
def replace(old,new):
    global s
    assert s.count(old)==1, (old,s.count(old)); s=s.replace(old,new)
replace("OUT=H/'R715-new-stub-explicit-round-cap-direct-source-supplement-r723'", "OUT=H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727'")
replace("from shapely.ops import unary_union", "from shapely.ops import unary_union\nfrom shapely.strtree import STRtree")
replace("prior=json.loads((R721/'receipt.json').read_bytes()); assert prior['status']=='R715_SUPPLEMENT_REPAIR_REQUIRED'", "assert sha(R721/'receipt.json')=='048a0751eca9fed42b7e3253fe29f47413b4429b03d4d29ed58e5725a9a173d0'\n    prior=json.loads((R721/'receipt.json').read_bytes()); assert prior['status']=='R715_SUPPLEMENT_REPAIR_REQUIRED'")
replace("N.assert_R157_actual_before(); g,h,b,q,c=pickle.loads(M.read_bytes())", "N.assert_R157_actual_before(); assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'\n    g,h,b,q,c=pickle.loads(M.read_bytes())")
replace("return rows,trees", "trees['B.Cu']=STRtree([row['shape'] for row in rows['B.Cu']])\n        return rows,trees")
replace("put(OUT/'receipt.json',{'status'", """priorgraph=H/'R715-new-stub-explicit-round-cap-direct-source-supplement-r723/prospective-round-cap-FBG-all-drilled-groups.pkl'
    assert sha(priorgraph)=='7f5c26c3c60c1b513c5bcab7f00f29814e8d952b2b617fe53301a05965b4af5f'
    assert sha(groupfile)==sha(priorgraph), 'fresh K.physical graph differs after unused returned-tree correction'
    put(OUT/'receipt.json',{'returned_B_broadphase_tree_rebuilt_after_exact_NEW_row_override':True,
        'R723_returned_tree_defect_preserved_but_K_physical_ignored_it_and_rebuilt_all_layer_trees':True,
        'R723_receipt_SHA256':sha(H/'R715-new-stub-explicit-round-cap-direct-source-supplement-r723/receipt.json'),
        'fresh_groups_equal_R723_bytes':True,'R155_model_SHA256':sha(M),'status'""")
replace("print('R723_COMPLETE'", "print('R727_COMPLETE'")
generated=H/'audit_R715_round_stub_bound_tree_consistency_r727.generated.py'
assert not generated.exists(); generated.write_text(s,encoding='utf-8')
exec(compile(s,str(generated),'exec'))
