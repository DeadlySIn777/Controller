"""Preserve r13; nominate MON around exact signal holes with old-cache evidence only."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r13.py').read_text()
source=source.replace("OUT=HERE/'ao1-reference-coupled-r13.json'", "OUT=HERE/'ao1-reference-coupled-r14.json'")
source=source.replace('WINDOW=box(368.8,124.7,379,133)', 'WINDOW=box(365,123,380,135)')
source=source.replace('ao1-r13-', 'ao1-r14-')
source=source.replace("if net==MON:shape=free_now.intersection(case_refs[layer].buffer(-.11))", "if net==MON:shape=free_now.intersection((case_refs if enforce_reference else nomination_refs)[layer].buffer(-.11))")
source=source.replace("jobs=[(VREF,", "attempt['nomination_returns']=returns\n            jobs=[(VREF,")
needle="source_parts=[p for p in pieces if any(p.covers(Point(a)) for a in starts)]"
replacement=needle+"\n                    all_goal_parts=[p for p in pieces if any(p.covers(Point(b)) for b in goals)]\n                    debug=HERE/('ao1-r14-'+str(len(attempts))+'-'+net.rsplit('/',1)[-1]+'-'+layer+'-free-reference.wkb');debug.write_bytes(shape.wkb)\n                    attempt.setdefault('exact_failure_shapes',[]).append({'net':net,'layer':layer,'path':str(debug.resolve()),'WKB_sha256':C.sha(shape.wkb),'starts_mm':starts,'goals_mm':goals,'target_component_areas_mm2':[p.area for p in all_goal_parts],'target_component_bounds_mm':[list(p.bounds) for p in all_goal_parts]})"
assert needle in source;source=source.replace(needle,replacement)
target=here/'ao1_reference_coupled_r14.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r14-syntax-only.pyc'))
print('Fresh R14 syntax PASS; wider MON window and strictly exploratory old-SDI cache nomination.')
