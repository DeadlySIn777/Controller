"""Fresh independent audit for the exact source-derived local MON cut."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'audit_ao1_reference_coupled_mon_r2.py').read_text()
source=source.replace('import json,math,sys,time', 'import json,math,sys,time\nfrom decimal import Decimal')
source=source.replace("path.stem+'-independent-mon-r2.json'", "path.stem+'-independent-mon-r3.json'")
source=source.replace("path.stem+'-independent-reference-gaps-mon-r2'", "path.stem+'-independent-reference-gaps-mon-r3'")
needle="parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};vias={u:z for u,z in parsed.items() if z['kind']=='via'}"
replacement=needle+"\n    source_mon_uuid='6b5d7465-3e16-4492-82be-cd9ae2fb2ad5'\n    exact_fraction=(Decimal('372.85')-Decimal('369.35'))/(Decimal('373.75')-Decimal('369.35'))\n    exact_y=Decimal('125.15')+exact_fraction*(Decimal('129.549999')-Decimal('125.15'))\n    preserved_uuid,preserved_chunk=identity.serial_segment(MON,'F.Cu',(369.35,125.15),(372.85,round(float(exact_y),9)),.2)\n    if new.get(preserved_uuid)!=preserved_chunk:raise ValueError('Source-derived retained MON chunk differs')\n    old_mon=G.parse(source_mon_uuid,now[4][source_mon_uuid],{});preserved_body=A.shape(parsed[preserved_uuid]);source_body=A.shape(old_mon)\n    if old_mon['a']!=(373.75,129.549999) or old_mon['b']!=(369.35,125.15) or old_mon['w']!=.2 or old_mon['layer']!='F.Cu' or old_mon['net']!=MON:raise ValueError('Exact native source MON line differs')\n    outside=preserved_body.difference(source_body.buffer(.000001)).area\n    if outside>1e-12:raise ValueError('Retained metal differs beyond source native 1nm lattice')\n    preserved={'uuid':preserved_uuid,'source_uuid':source_mon_uuid,'source_chunk_SHA256':C.sha(now[4][source_mon_uuid]),'exact_rational_line_fraction':str(exact_fraction),'exact_rational_y_mm':str(exact_y),'source_native_lattice_error_bound_mm':.000001,'outside_source_plus_lattice_error_mm2':outside,'newly_routed_reference_waivers':0}\n    changed=set(parsed)-{preserved_uuid}"
assert needle in source;source=source.replace(needle,replacement)
source=source.replace('IF.prospective_fill(base,final,smasks,now,parsed,set(parsed))', 'IF.prospective_fill(base,final,smasks,now,parsed,changed)')
source=source.replace('A.clearance(final,parsed,set(parsed),set())', 'A.clearance(final,parsed,changed,set())')
source=source.replace("if z['kind']!='segment':continue\n        v=signals", "if z['kind']!='segment' or u==preserved_uuid:continue\n        v=signals")
needle="gaps=Q.zone_gaps(now);reference=[]"
replacement="retained_covered=preserved_body.intersection(original_refs['F.Cu']);retained_lost=retained_covered.difference(refs['F.Cu'])\n    preserved.update(original_source_uncovered_mm2=source_body.difference(original_refs['F.Cu']).area,retained_body_original_uncovered_mm2=preserved_body.difference(original_refs['F.Cu']).area,retained_body_final_uncovered_mm2=preserved_body.difference(refs['F.Cu']).area,previously_covered_retained_body_lost_mm2=retained_lost.area)\n    if retained_lost.area>1e-9:contacts.append({'reason':'Source-derived retained MON body lost previous rooted reference','mm2':retained_lost.area})\n    gaps=Q.zone_gaps(now);reference=[]"
assert needle in source;source=source.replace(needle,replacement)
source=source.replace('GD.diagnose(base,final,parsed,removed,smasks,refs,now,gap_dir)', 'GD.diagnose(base,final,{u:z for u,z in parsed.items() if u!=preserved_uuid},removed,smasks,refs,now,gap_dir)')
source=source.replace("'owned_exact_MON_F_segments':sorted(MON_REMOVED),", "'owned_exact_MON_F_segments':sorted(MON_REMOVED),'independent_preserved_source_MON_piece':preserved,'newly_changed_source_UUIDs':sorted(changed),")
target=here/'audit_ao1_reference_coupled_mon_r3.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-independent-mon-r3-syntax-only.pyc'))
print('Fresh independent MON R3 syntax PASS; exact rational source-derived metal audit.')
