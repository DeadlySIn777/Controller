"""Preserve R231 reader failure; use the established exact physical-key comparator."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_B3_envelope_scoped_LOGIC_r231.py').read_text(encoding='utf-8')
s=s.replace('B3-envelope-scoped-LOGIC-projection-r231','B3-envelope-scoped-LOGIC-projection-r233')
s=s.replace('import fast_contacts as F','import fast_contacts as F\nfrom audit_field_io3_crossings_r15e import losses as relationship_losses')
s=s.replace('losses=F.losses(oldgroups,groups)','losses=relationship_losses(oldgroups,groups)').replace('R231','R233')
exec(compile(s,str(H/'audit_B3_envelope_scoped_LOGIC_r231.py'),'exec'))
