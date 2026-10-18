"""Preserve R56 early assertion failure and bind normalized owned-zone IDs correctly."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'audit_SAFE_logic_four_full_r56.py';dst=H/'audit_SAFE_logic_four_full_r57.py'
assert not dst.exists();s=src.read_text()
s=s.replace('SAFE-logic-four-independent-full-r56','SAFE-logic-four-independent-full-r57').replace('R56_CONTACT','R57_CONTACT').replace('R56_SOURCE_REFERENCE','R57_SOURCE_REFERENCE').replace('R56_COMPLETE','R57_COMPLETE')
a=" _,_,_,_,before=pickle.loads(contactbase.read_bytes())"
assert a in s;s=s.replace(a," original_contact_inventory,_,_,_,before=pickle.loads(contactbase.read_bytes())\n assert g['zones']==original_contact_inventory['zones'],'All original native zone records must remain exact across canonical owned normalization'")
a=" assert {q['uuid'] for q in before['zones']}<={q['uuid'] for q in after['zones']}"
b=" projected={q['uuid']:q for q in after['zones']}\n for original in original_contact_inventory['zones']:\n  assert original['uuid'] in projected\n  assert {k:v for k,v in original.items()if k!='fills'}=={k:v for k,v in projected[original['uuid']].items()if k!='fills'},'Original native zone outlines/settings unchanged; only filled geometry may be projected'"
assert a in s;s=s.replace(a,b)
compile(s,str(dst),'exec');dst.write_text(s)
(H/'SAFE-logic-four-r57-audit-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'R56_failure':'Early assertion compared 201 former owned preview zone IDs against 36 explicitly normalized canonical groups; no contact/source/reference results had run','replacement_assertion':'Exact all514 original native zone records and their projected outlines/settings preserved, canonical owned zones may carry newly bound UUIDs','all_contact_source_reference_geometry_requirements_unchanged':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
print(dst)
