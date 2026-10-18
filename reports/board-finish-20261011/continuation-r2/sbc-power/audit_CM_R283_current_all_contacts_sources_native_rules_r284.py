"""Fresh R283 CM proof, inherited literal role/fill FAIL stays explicit."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_CM_R279_current_all_contacts_sources_native_rules_r282.py').read_text()
s=s.replace('CM-sparse-exact-current-R364-normal-antipads-local-negative-r279','CM-sparse-exact-current-R364-only-new-role-withdrawal-inherited-fills-FAIL-r283')
s=s.replace('CM-R279-current-independent-all-contact-source-native-rule-r282','CM-R283-current-independent-all-contact-source-native-rule-r284')
s=s.replace("'parent_R368_strict_oldrefs_FAIL_count_retained':28", "'parent_R368_strict_oldrefs_FAIL_count_retained':28,'parent_owned_fill_outside_bound_physical_FAIL_count_retained':r['inherited_owned_fill_outside_physical_FAIL_count']")
s=s.replace('R279','R283').replace('R282','R284')
exec(compile(s,str(__file__),'exec'))
