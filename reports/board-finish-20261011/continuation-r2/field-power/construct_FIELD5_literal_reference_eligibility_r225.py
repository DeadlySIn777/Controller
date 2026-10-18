"""Preserve R223 stopped preprocessing; use the existing REF exact eligibility."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_FIELD5_actual_IO3_contact_preservation_r223.py').read_text(encoding='utf-8')
s=s.replace('FIELD5-current-IO3-and-reference-preservation-search-base-r223','FIELD5-current-IO3-and-reference-preservation-search-base-r225').replace('FIELD5-actual-IO3-preserving-alternate-r223','FIELD5-actual-IO3-preserving-alternate-r225')
s=s.replace("if t['layer']!=outer:continue","if t['layer']!=outer or C.norm(t['net'])==ground or h['domains_normalized'].get(C.norm(t['net']))!=h['domains_normalized'][ground]:continue")
s=s.replace('controller-field5-current-IO3-r223/','controller-field5-current-IO3-r225/')
exec(compile(s,str(H/'construct_FIELD5_actual_IO3_contact_preservation_r223.py'),'exec'))
