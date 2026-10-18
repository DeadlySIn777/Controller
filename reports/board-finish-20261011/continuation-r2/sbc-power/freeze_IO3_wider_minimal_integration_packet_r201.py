"""Exact one-group replacement on validated R183 with the final .30 branch."""
from pathlib import Path
import ast
P=Path(__file__).resolve().parent;old=P/'freeze_IO3_minimal_integration_packet_r188.py';s=old.read_text()
needle="om={(q['net'],q['layer']):q for q in oz};rows=[];replacements=[];untouched=[]"
repl="def key(q):return (q['net'],q['layer'],q.get('clearance_mm',.15),q.get('min_thickness_mm',.15),q.get('pad_connect_mode','FULL_SOLID'),q.get('priority',124),q.get('island_removal_mode',1),q.get('thermal_gap_mm',.15),q.get('thermal_bridge_width_mm',.3))\n om={key(q):q for q in oz};assert len(om)==len(oz);rows=[];replacements=[];untouched=[]"
assert needle in s;s=s.replace(needle,repl).replace("before=om[q['net'],q['layer']]","before=om[key(q)]")
s=s.replace('IO3-minimal-validated-integration-packet-r188','IO3-wider-minimal-validated-integration-packet-r201').replace('R188_COMPLETE','R201_COMPLETE')
s=s.replace('SAFE-repaired-owned-zone-normalization-r160/model.pkl','IO3-exact-unchanged-primitive-composition-r183/model.pkl').replace('IO3-exact-unchanged-primitive-composition-r183/model.pkl\'\n',"IO3-group6-wider-minimal-canonical-union-r196/model.pkl'\n")
# Replace the two-path line explicitly to avoid replacing the parent path.
source="oldp=H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183/model.pkl';newp=H/'sbc-power/IO3-group6-wider-minimal-canonical-union-r196/model.pkl'"
assert source in s
s=s.replace('d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b','6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5')
s=s.replace("assert sha(newp)=='6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5'","assert sha(newp)=='bf5603eebd87b3c5c197b8ae1266c0c0e780c3628dc65adbaa6b7f94f31721af'")
s=s.replace("q['layer'] not in ('In2.Cu','In3.Cu')","q['layer'] not in ('In3.Cu',)").replace('len(rows)==2 and len(untouched)==34','len(rows)==1 and len(untouched)==35')
s=s.replace('exact-owned-IO3-two-group-replacements.pkl','exact-owned-IO3-one-In3-group-replacement.pkl').replace('only_two_owned_host_group_replacements','only_one_owned_host_group_replacement').replace('all34_unchanged_group_WKB_rows','all35_unchanged_group_WKB_rows')
s=s.replace('IO3-exact-primitive-independent-true-geometry-r184','IO3-wider-minimal-independent-true-geometry-r197').replace('IO3-exact-primitive-original198b-DC936-contact-audit-r185','IO3-wider-minimal-original198b-DC936-contact-audit-r198').replace('IO3-exact-primitive-all76-incremental-audit-r186','IO3-wider-minimal-all76-incremental-audit-r199')
s=s.replace("'whole_earlier_scope_substitution_forbidden':True,","'literal_final_full_capsule_width_mm':.3,'replaces_only_unadopted_e1ca_branch_with_35a950a3':True,'whole_earlier_scope_substitution_forbidden':True,")
ast.parse(s);exec(compile(s,str(old),'exec'))
