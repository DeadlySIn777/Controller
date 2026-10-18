from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'audit_u11015_discrete_r33.py').read_text().replace('u11015-r32-independent-discrete-audit-r33','u11015-r44-independent-discrete-audit-r45').replace('u11015-three-net-inner-ILIM-repair-r32','u11015-reverse-companion-repair-r44').replace('input_R32_receipt_SHA256','input_R44_receipt_SHA256')
(P/'audit_u11015_discrete_r45.py').write_text(s,encoding='utf-8');compile(s,'audit_u11015_discrete_r45.py','exec')
