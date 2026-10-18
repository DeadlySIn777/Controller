"""Build the isolated sparse repair on the fully bound corrected DIC head."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'construct_U10003_sparse_current_ground_fault_r151.py';code=source.read_text()
code=code.replace('construction-r151','construction-r153')
code=code.replace('field-power/REG-U25-corrected-DIC262-sparse-current-composition-r359/model.pkl','coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl')
code=code.replace('52076bd44490e66b73dbd06994eea58a13f80152abdb7643cf2c3ae05e055739','64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144')
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
