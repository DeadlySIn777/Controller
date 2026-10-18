"""Preserve R267; replay exact generated operation metadata before masks."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'freeze_T4_R7_sparse_owned_native_recipe_r267.py').read_text()
old="assert g==bg"
new="assert g==bg;import restore_SAFE_generated_precision_states_r168 as PS;PS.restore_bound_generated_precision_states(b,q);PS.restore_bound_generated_precision_states(bb,bq)"
assert s.count(old)==1;s=s.replace(old,new).replace('r267','r268').replace('R267','R268')
exec(compile(s,str(__file__),'exec'))
