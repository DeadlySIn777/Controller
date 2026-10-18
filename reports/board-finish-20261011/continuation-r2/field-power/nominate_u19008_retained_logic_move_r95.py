"""Retained local LOGIC contacts, without inventing a J11001 source join."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'nominate_u19008_logic_barrel_relocation_r94.py').read_text()
s=s.replace("OUT=H/'u19008-logic-barrel-relocation-r94'", "OUT=H/'u19008-retained-logic-barrel-relocation-r95'")
s=s.replace("ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));roots=gs[ri];", "ri=next(i for i,xs in enumerate(gs) if any(q['uuid']==v['uuid'] for q in xs));roots=gs[ri];old_ann=P.bounded_disk(v,v['d']/2).difference(P.bounded_disk(v,v['drill']/2));old_local_fill_contact={l:old_ann.intersection(unary_union([q['shape'] for q in roots if q['layer']==l and q['kind']=='fill'])).area for l in LAYERS};")
s=s.replace("if any(r['old_actual_source_fill_annular_overlap_mm2']<.001 for r in support):", "if any(old_local_fill_contact[r['layer']]>=.001 and r['old_actual_source_fill_annular_overlap_mm2']<.001 for r in support):")
s=s.replace("'old_actual_source_fill_annular_overlap_mm2'", "'retained_local_group_fill_annular_overlap_mm2'")
s=s.replace("'source_annular_support':support", "'retained_local_group_annular_support':support,'old_local_group_fill_annular_contact_mm2':old_local_fill_contact,'J11001_source_join':'UNQUALIFIED_SEPARATE_FULL_RETURN_OBLIGATION'")
s=s.replace("STRONG_RELOCATION_NOMINATION_FULL_ORIGINAL_SOURCE_CONTACT_REFERENCE_NATIVE_CURRENT_GATES_OPEN", "STRONG_LOCAL_CONTACT_RELOCATION_NOMINATION_J11001_SOURCE_NATIVE_CURRENT_GATES_OPEN")
s=s.replace("print('R94", "print('R95")
exec(compile(s,str(p/'nominate_u19008_logic_barrel_relocation_r94.py'),'exec'))
