"""Preserve R87, add explicit same-UUID replacement support with strict ledger."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;s=(H/'emit_complete_power_recipe_r87.py').read_text()
def replace(a,b):
    global s
    assert s.count(a)==1;s=s.replace(a,b)
replace("import owned_native_footprint_delta_r86 as FP", "import owned_native_footprint_delta_r86 as FP\nimport owned_native_cu_replacements_r100 as CR")
replace("OUT=L.OUT/'complete-power-native-recipe-r87'", "OUT=L.OUT/'complete-power-native-recipe-r101'")
replace("native_FP_rows,owned_FP_pads,owned_FP_recipes=FP.collect(binding,base,h)","native_FP_rows,owned_FP_pads,owned_FP_recipes=FP.collect(binding,base,h)\n    native_Cu_replacement_rows,owned_Cu_replaced,owned_Cu_replacement_recipes=CR.collect(binding,base,h)\n    assert not set(owned_removed)&set(owned_Cu_replaced),'Existing item cannot be both removed and replaced'")
replace("else:assert now==prior,('unexpected_existing_native_discrete_change',kind,uid)","elif kind in ('tracks','vias') and uid in owned_Cu_replaced:\n                assert CR.canonical_record(prior)==owned_Cu_replaced[uid]['expected_original_geometry'] and CR.canonical_record(now)==owned_Cu_replaced[uid]['expected_replacement_geometry']\n            else:assert now==prior,('unexpected_existing_native_discrete_change',kind,uid)")
replace("receipt.update({'native_existing_owned_Cu_delete_rows':native_delete_rows", "receipt.update({'native_existing_owned_Cu_replacement_rows':native_Cu_replacement_rows,'existing_native_owned_Cu_replacement_recipes':owned_Cu_replacement_recipes,'exact_changed_existing_Cu_UUIDs':sorted(owned_Cu_replaced),'same_UUID_existing_Cu_replacements_not_counted_as_additions':True})\n    receipt.update({'native_existing_owned_Cu_delete_rows':native_delete_rows")
out=H/'emit_complete_power_recipe_r101.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec');print('EMITTER_WITH_EXACT_CU_REPLACEMENTS',hashlib.sha256(out.read_bytes()).hexdigest())
