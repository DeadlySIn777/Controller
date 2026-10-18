"""Nominate actual B group landings and test each allowed own-transition void."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;p=HERE/'ao1_reference_coupled_r2.py';t=p.read_text()
t=t.replace("OUT=HERE/'ao1-reference-coupled-r2.json'","OUT=HERE/'ao1-reference-coupled-r3.json'")
needle="    vfront=containing(strict[VREF,'F.Cu'],vstart);vback=containing(strict[VREF,'B.Cu'],vend);vspace=vfront.intersection(vback)"
replacement="""    _,vgroups=P.physical(initial,VREF,smasks)
    vtarget=next(g for g in vgroups if 'U14636.7#0' in g['pad_ids'])
    vtarget_records=S.seed_sites(vtarget,'B.Cu',physical_free[VREF,'B.Cu'],WINDOW)
    vtargets=[p for p,r in vtarget_records]
    vfront=containing(physical_free[VREF,'F.Cu'],vstart)
    vback=unary_union([p for p in P.K.D.components(physical_free[VREF,'B.Cu']) if any(p.covers(Point(q)) for q in vtargets)])
    vspace=vfront.intersection(vback)"""
assert needle in t;t=t.replace(needle,replacement)
t=t.replace("sfront=containing(strict[SDI,'F.Cu'],sstart)","sfront=containing(physical_free[SDI,'F.Cu'],sstart)")
t=t.replace("target_records=S.seed_sites(target,'In3.Cu',strict[SDI,'In3.Cu'],WINDOW)","target_records=S.seed_sites(target,'In3.Cu',physical_free[SDI,'In3.Cu'],WINDOW)")
t=t.replace("P.K.D.components(strict[SDI,'In3.Cu'])","P.K.D.components(physical_free[SDI,'In3.Cu'])")
t=t.replace("'vref_back_target_mm':vend","'vref_back_remote_pad_mm':vend,'vref_actual_retained_B_target_seeds':vtargets")
t=t.replace("(VREF,'B.Cu',[vat],[vend])","(VREF,'B.Cu',[vat],vtargets)")
t=t.replace("for q,r in target_records if q==p","for q,r in target_records+vtarget_records if q==p")
t=t.replace("'initial_rooted_reference_witness':witness}","'initial_rooted_reference_witness':witness,'source_pad_full_reference_component_areas_mm2':{VREF:containing(strict[VREF,'F.Cu'],vstart).area,SDI:containing(strict[SDI,'F.Cu'],sstart).area}}")
q=HERE/'ao1_reference_coupled_r3.py'
if q.exists():raise ValueError('Fresh r3 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-reference-r3-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'changes':['Actual retained U14636.7 native-group B copper landing within local ROI','Physically reachable all6 via nomination; per-case full-body reference path using only the route-own transition exception and actual qualified return','No neighbouring or stale removed-signal void fill credit outside route-own transition'],'source_definitions_changed':False},indent=1)+'\n')
print('Reference r3 syntax PASS; r2 zero-site diagnostic preserved')
