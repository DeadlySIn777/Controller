"""Fresh IO3 source graph and full conditional no-zone checks after both cuts."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
r=H/'R155-FA-plus-IO3-TMR-owned-local-negative-r487/receipt.json'
assert r.exists()
receipt=json.loads(r.read_text(encoding='utf-8'))
s=(H/'audit_current_FA_TMR_local_negative_source_rules_r483.py').read_text(encoding='utf-8')
s=s.replace("M=H/'R155-protected-FA-TMR-local-negative-inherited-outline-FAIL-r481/model.pkl'", "M=H/'R155-FA-plus-IO3-TMR-owned-local-negative-r487/model.pkl'")
s=s.replace('206031df3e638b08ff3356239f2ff83efde810944c9a0630ee06c8a9672df1ff',receipt['model_sha256'])
s=s.replace("O=H/'R155-protected-FA-TMR-local-negative-source-contact-native-nozone-r483'", "O=H/'R155-FA-plus-IO3-TMR-source-contact-native-nozone-r489'")
s=s.replace("NET='/motherboard_power_entry/FIELD_A_24V_PROTECTED'", "NET='/IO_3V3'")
s=s.replace("UID='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19'", "UID='4f297f78-8d11-5be4-910e-9245f73fa249'\nFA_UID='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19'")
s=s.replace("a['uuid']!=UID", "a['uuid']not in (UID,FA_UID)")
s=s.replace("K.root(prior,'U11004','17')", "K.root(prior,'R18001','2')").replace("K.root(new,'U11004','17')", "K.root(new,'R18001','2')")
s=s.replace("'full_protected_current_A':4.567408669354", "'full_IO3_output_current_A':2.0")
s=s.replace('fresh-FA-actual-drilled-groups.pkl','fresh-IO3-actual-drilled-groups.pkl').replace('FA-source-contact-current-topology.json','IO3-source-contact-current-topology.json').replace('FA_source_contact','IO3_source_contact').replace('fresh_FA_graph_SHA256','fresh_IO3_graph_SHA256')
s=s.replace("inherited=json.loads((M.parent/'unchanged-inherited-outline-mismatch-FAIL.json').read_text(encoding='utf-8'))", "inherited=json.loads((H/'R155-protected-FA-TMR-local-negative-inherited-outline-FAIL-r481/unchanged-inherited-outline-mismatch-FAIL.json').read_text(encoding='utf-8'))")
s=s.replace("print('R483 FA'", "print('R489 IO3'").replace("print('R483 receipt'", "print('R489 receipt'")
exec(compile(s,str(H/'audit_current_FA_plus_IO3_TMR_source_rules_r489.py'),'exec'))
