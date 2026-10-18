"""Keep R240 construction evidence; remove its explicit positive snap sliver."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'correct_owned_FBG_inherited_actual_LOGIC_fill_guard_r240.py').read_text(encoding='utf-8')
s=s.replace('B3-subset-inherited-FBG-native-LOGIC-guard-correction-r240','B3-subset-inherited-FBG-native-LOGIC-guard-correction-r241')
s=s.replace("q[role]=set_precision(prior.difference(cutter),1e-6);rf=", "q[role]=set_precision(prior.difference(cutter).buffer(-.000002,quad_segs=64),1e-6);assert q[role].difference(prior).area<1e-12,('positive quantization gain',role,q[role].difference(prior).area);rf=")
s=s.replace("'explicit_additional_constructor_reserve_mm':.00005", "'explicit_additional_constructor_reserve_mm':.00005,'owned_shape_only_inward_quantization_reserve_mm':.000002,'R240_positive_grid_sliver_not_accepted':True").replace('R240 complete','R241 complete')
exec(compile(s,str(H/'correct_owned_FBG_inherited_actual_LOGIC_fill_guard_r240.py'),'exec'))
