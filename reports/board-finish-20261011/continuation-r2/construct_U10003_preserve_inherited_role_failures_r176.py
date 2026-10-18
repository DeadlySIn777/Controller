"""Keep unchanged pre-existing role failures explicit; gate only added outside Cu."""
from pathlib import Path
H=Path(__file__).resolve().parent;wrapper=H/'construct_U10003_exact_bound_nominee_path_r175.py';code=wrapper.read_text()
needle="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))";assert code.count(needle)==1
extra="""code=code.replace('reference-construction-r175','reference-construction-r176')
needle=\"for z in q:assert set_precision(z['shape'],0).difference(set_precision(z['zone_outline_shape'],0)).is_empty,('physical_outside_intended',z['uuid'])\"
replacement=\"\"\"inherited_outside=[];oldroles={z['uuid']:z for z in q0}
 for z in q:
  outside=set_precision(z['shape'],0).difference(set_precision(z['zone_outline_shape'],0))
  previous=oldroles.get(z['uuid'])
  if previous is not None and z['uuid']not in replaceids:
   oldoutside=set_precision(previous['shape'],0).difference(set_precision(previous['zone_outline_shape'],0))
   unchanged=all(z[r].wkb==previous[r].wkb for r in('shape','zone_outline_shape'))
   if unchanged:
    if not outside.is_empty:inherited_outside.append({'UUID':z['uuid'],'unchanged_physical_and_intended_WKB_exact':True,'raw_before_and_after_outside_area_mm2':outside.area,'raw_failure_preserved':True})
   else:assert outside.difference(oldoutside).is_empty,('new_physical_outside_intended',z['uuid'])
  else:assert outside.is_empty,('new_role_physical_outside_intended',z['uuid'])
 put(OUT/'inherited-unchanged-physical-outside-intention-FAIL-ledger.json',inherited_outside)\"\"\"
assert code.count(needle)==1;code=code.replace(needle,replacement)
needle=\"'all_existing_actual_fills_literal_remove_only':True\"
assert code.count(needle)==1;code=code.replace(needle,needle+\",'unchanged_inherited_role_outside_intention_failures_preserved':inherited_outside\")
"""
code=code.replace(needle,extra+needle)
compile(code,str(wrapper),'exec');exec(compile(code,str(wrapper),'exec'))
