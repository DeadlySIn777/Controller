"""R491 source/contact/no-zone audit; frozen failed R487 is not reused."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_current_FA_plus_IO3_TMR_source_rules_r489.py').read_text(encoding='utf-8')
s=s.replace('R155-FA-plus-IO3-TMR-owned-local-negative-r487','R155-FA-plus-IO3-TMR-individual-local-scope-witnesses-r491')
s=s.replace('R155-FA-plus-IO3-TMR-source-contact-native-nozone-r489','R155-FA-plus-IO3-TMR-individual-scopes-source-contact-native-nozone-r493')
s=s.replace("print('R489 IO3'", "print('R493 IO3'").replace("print('R489 receipt'", "print('R493 receipt'")
exec(compile(s,str(H/'audit_FA_IO3_TMR_individual_scopes_source_rules_r493.py'),'exec'))
