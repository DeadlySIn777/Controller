"""Reuse the exact current R78/DI6 source-root checkpoint without projection."""
import pickle
import audit_aux_exact_raw as A
from pathlib import Path
HERE=Path(__file__).resolve().parent
def bind(r11,cp):
 p=HERE/'di15-current-r78-projection-r13.pkl';raw=A.read(p);assert A.C.sha(raw)=='2b272430cc2d0e2368a23c3d7aad25c3142010fdbec4ef6f2f78ff3239cd82c2';r=pickle.loads(raw);assert r['R78_model_sha256']=='128a21a83ccc8e1029f4b97e27930f82de743e00ef45fb1fc2041f0967b8a821';assert r['ground_snapshot4_hard_only_sha256']=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239';assert r['R11_only_owned_additions_sha256']==r11['saved_model_sha256'];r['checkpoint_sha256']=A.C.sha(raw);return r
