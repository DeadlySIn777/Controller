"""Independent field continuation on corrected DIC, peer SBC still staged."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'compose_REG312_U25_only_current_R256_r354.py').read_text(encoding='utf-8')
s=s.replace('REG312-U25-sparse-actual-R256-current-composition-r354','REG-U25-corrected-DIC262-sparse-current-composition-r359').replace('DIC-C1022-exact-R250-current-construction-r256','DIC-C1022-exact-R250-original-guard-construction-r262').replace('7b4c123a051f7b177c928b7a02c479776237c198989f3c1a24d722c29dd25573','64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144').replace('baseline_R256_model_SHA256','baseline_corrected_DIC_R262_model_SHA256')
needle='h=copy.deepcopy(h0);b=copy.deepcopy(b0);z=copy.deepcopy(z0)'
assert s.count(needle)==1;s=s.replace(needle,needle+';PS.restore_bound_generated_precision_states(b,z)')
exec(compile(s,str(H/'compose_REG312_U25_only_current_R256_r354.py'),'exec'))
