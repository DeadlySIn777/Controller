"""Restore the exact r15-created precision states before independent projection."""
from pathlib import Path
path=Path(__file__).resolve().parent/'audit_field_io3_crossings_r15c.py'
code=path.read_text()
insert="""code=code.replace(\"OUT=HERE/'field-io3-crossing-contact-audit-r15c'\",\"OUT=HERE/'field-io3-crossing-contact-audit-r15d'\")
code=code.replace('after,cuts=N.projected(old,discrete,zones);',\"precision_ids=set(carves)|{z['uuid'] for z in zones if z.get('label')=='CORE-main-In2' or z.get('label','').startswith('IO3-r15-field-crossing-')};zones=[{**z,'shape':set_precision(z['shape'],1e-6)} if z['uuid'] in precision_ids else z for z in zones];after,cuts=N.projected(old,discrete,zones);\")
code=code.replace(\"'input_r15_cache_sha256':sha(cache),\",\"'input_r15_cache_sha256':sha(cache),'restored_precision_model_UUIDs':sorted(precision_ids),'precision_grid_mm':1e-6,'prior_projection_precheck_failure_sha256':sha(HERE/'field-io3-crossing-contact-audit-r15c/projection-precheck-failure.json'),\")
"""
needle="exec(compile(code,str(path),'exec'))"
assert needle in code;code=code.replace(needle,insert+needle)
exec(compile(code,str(path),'exec'))
