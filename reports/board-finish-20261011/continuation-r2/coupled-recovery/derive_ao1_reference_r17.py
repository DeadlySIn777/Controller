"""Preserve r14/r16; exact local MON cut with source-derived retained metal."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r14.py').read_text()
source=source.replace("OUT=HERE/'ao1-reference-coupled-r14.json'", "OUT=HERE/'ao1-reference-coupled-r17.json'")
source=source.replace('ao1-r14-', 'ao1-r17-')
source=source.replace('import collections,json,math,sys,time', 'import collections,json,math,sys,time\nfrom decimal import Decimal')
needle="chunks={u:ch for u,ch in now[4].items() if u not in removed}"
replacement=needle+"\n    # Retain the exact source copper before the local obstructing span.\n    # KiCad native coordinates quantize to 1 nm; this rational source-line\n    # parameter is bound independently before any retained-metal credit.\n    preserved_source_uuid='6b5d7465-3e16-4492-82be-cd9ae2fb2ad5'\n    original_mon=G.parse(preserved_source_uuid,now[4][preserved_source_uuid],{})\n    cut_x=Decimal('372.85');fraction=(cut_x-Decimal('369.35'))/(Decimal('373.75')-Decimal('369.35'))\n    exact_cut_y=Decimal('125.15')+fraction*(Decimal('129.549999')-Decimal('125.15'))\n    mon_cut=(float(cut_x),round(float(exact_cut_y),9))\n    pu,pch=identity.serial_segment(MON,'F.Cu',(369.35,125.15),mon_cut,.2)\n    preserved={pu:pch};chunks.update(preserved)\n    preserved_body=A.shape(G.parse(pu,pch,{}));old_mon_body=A.shape(original_mon)\n    if preserved_body.difference(old_mon_body.buffer(.000001)).area>1e-12:raise ValueError('Preserved MON metal differs beyond the 1-nm native lattice')\n    preserved_proof={'new_uuid':pu,'source_uuid':preserved_source_uuid,'exact_source_chunk_sha256':C.sha(now[4][preserved_source_uuid]),'native_source_start_mm':original_mon['a'],'native_source_end_mm':original_mon['b'],'exact_rational_line_fraction':str(fraction),'exact_rational_cut_y_mm':str(exact_cut_y),'serialized_cut_mm':mon_cut,'source_line_error_mm':float(abs(Decimal(str(mon_cut[1]))-exact_cut_y)),'native_1nm_endpoint_error_bound_mm':.000001,'preserved_new_body_outside_source_plus_1nm_mm2':preserved_body.difference(old_mon_body.buffer(.000001)).area,'reference_acceptance':'Only existing source metal is retained; original uncovered source body remains unqualified and may not grow.'}"
assert needle in source;source=source.replace(needle,replacement)
source=source.replace('nominations=[((374.0,129.0),(373.4,128.3))]', 'nominations=[((373.9,129.0),(373.4,128.3))]')
source=source.replace('new={};signals={}', 'new=dict(preserved);signals={}')
source=source.replace('preferred=(373.5,129.15)', 'preferred=(373.05,127.5) if net==SDI else (373.1,129.45)')
source=source.replace('all(.81-1e-9<=math.dist(preferred,q)<=1.+1e-9 for q in (vat,sat))', '.81-1e-9<=math.dist(preferred,at)<=1.+1e-9')
source=source.replace("(MON,'F.Cu',[(369.35,125.15)],[(374.55,130.049999)])", "(MON,'F.Cu',[mon_cut],[(374.55,130.049999)])")
source=source.replace("'uuid':'036f4f5d-d8f0-4b5f-bd20-72e5cdeecb36'", "'uuid':pu")
source=source.replace("final,fillledger,fillerrors=Q.prospective_fill(base,final,masks,now,parsed,set(parsed))", "changed=set(parsed)-set(preserved)\n            final,fillledger,fillerrors=Q.prospective_fill(base,final,masks,now,parsed,changed)")
source=source.replace('A.clearance(final,parsed,set(parsed),set())', 'A.clearance(final,parsed,changed,set())')
source=source.replace("if z['kind']!='segment':continue\n                plane=", "if z['kind']!='segment' or u in preserved:continue\n                plane=")
needle="ref_errors=[]\n            for u,z in parsed.items():"
replacement="original_refs,original_witness,_,_=Q.rooted_reference(base,smasks,identity.raw(COM))\n            preserved_previously_covered=preserved_body.intersection(original_refs['F.Cu'])\n            retained_ref_lost=preserved_previously_covered.difference(frefs['F.Cu'])\n            retained_reference={'source_original_uncovered_mm2':old_mon_body.difference(original_refs['F.Cu']).area,'retained_source_body_uncovered_before_mm2':preserved_body.difference(original_refs['F.Cu']).area,'retained_source_body_uncovered_after_mm2':preserved_body.difference(frefs['F.Cu']).area,'retained_previously_covered_lost_mm2':retained_ref_lost.area,'new_body_reference_waivers':0}\n            if retained_ref_lost.area>1e-9:fillerrors.append({'reason':'Retained source MON body lost rooted reference','mm2':retained_ref_lost.area})\n            ref_errors=[]\n            for u,z in parsed.items():"
assert needle in source;source=source.replace(needle,replacement)
source=source.replace('reference_errors=ref_errors,returns=paired)', 'reference_errors=ref_errors,returns=paired,preserved_source_MON_reference=retained_reference)')
source=source.replace("'new_chunks':{u:ch.decode() for u,ch in new.items()},", "'new_chunks':{u:ch.decode() for u,ch in new.items()},'preserved_source_MON_piece':preserved_proof,'preserved_source_MON_reference':retained_reference,")
source=source.replace("'owned_original_MON_F_segments':sorted(MON_REMOVED),", "'owned_original_MON_F_segments':sorted(MON_REMOVED),'preserved_source_MON_piece':preserved_proof,")
target=here/'ao1_reference_coupled_r17.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r17-syntax-only.pyc'))
print('Fresh R17 syntax PASS; local source-derived MON cut and shifted VREF nomination.')
