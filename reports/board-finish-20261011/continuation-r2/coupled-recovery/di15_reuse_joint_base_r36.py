"""Reuse exact R34 projected ROOT R11 plus DI6 checkpoint for local search."""
import pickle
from pathlib import Path
import audit_aux_exact_raw as A
HERE=Path(__file__).resolve().parent
def bind(r11,cp):
 p=HERE/'di15-current-joint-r11-projection-r34.pkl';raw=A.read(p);assert A.C.sha(raw)=='ca01c67961d85d528014511defbc03cf0d5da4776d273e407c22cac5207b7451';r=pickle.loads(raw)
 assert r['joint_R11_model_sha256']=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8';assert r['R11_only_owned_additions_sha256']==r11['saved_model_sha256'];assert len(cp['nt'])==9 and len(cp['nv'])==2
 # R34's overbroad metadata label did not compute every electrical domain:
 # only the actual drilled LOGIC_GND source-root reference was reconstructed.
 r.pop('all_source_roots_recomputed_after_actual_drills',None);r['LOGIC_GND_root_only_recomputed_after_actual_drills']=True;r['checkpoint_sha256']=A.C.sha(raw);return r
