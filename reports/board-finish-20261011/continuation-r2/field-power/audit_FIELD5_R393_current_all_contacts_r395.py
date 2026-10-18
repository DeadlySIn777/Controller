"""Fresh complete current audit; no failed earlier reference proof reused."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=(H/'audit_corrected_full_sparse_current_r365.py').read_text(encoding='utf-8')
prefix=owner.rsplit("exec(compile(s,",1)[0]
ns={'__file__':str(H/'audit_corrected_full_sparse_current_r365.py'),'__name__':'_generate_frozen_current_auditor'}
exec(compile(prefix,str(H/'audit_corrected_full_sparse_current_r365.py'),'exec'),ns)
s=ns['s']
s=s.replace('REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364','FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393')
s=s.replace('REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r365','FIELD5-R393-current-independent-all-contact-source-reference-audit-r395')
s=s.replace("'f4863c44-a057-598a-aef7-adca7cfb15f1'}","'f4863c44-a057-598a-aef7-adca7cfb15f1','e2fe644a-2849-5c69-8ebb-d1e94909cd4c'}")
old="if z['uuid']not in IDS:assert all(n[r].wkb==z[r].wkb for r in('shape','zone_outline_shape'));unchanged.append(z['uuid'])"
new="""if z['uuid']=='47888e35-9a96-5393-b579-7c0b4a64ec93':
   assert n['shape'].wkb==z['shape'].wkb
   assert A.C.sha(z['zone_outline_shape'].wkb)=='ad3562a883de7f852644f14da8e579402c973091e9cffdcd9aa3f4a960dfb5c9'
   assert A.C.sha(n['zone_outline_shape'].wkb)=='51eedabfa7a40829dbac8388728bbc4a85844a89fa596b15558d64588aea3e1e'
  elif z['uuid']not in IDS:assert all(n[r].wkb==z[r].wkb for r in('shape','zone_outline_shape'));unchanged.append(z['uuid'])"""
assert s.count(old)==1;s=s.replace(old,new)
dirty="affected={L.norm(t['net'])for t in nt+nv}|{L.norm(z['net'])for z in newq}"
assert s.count(dirty)==1;s=s.replace(dirty,dirty+"|{L.norm(oldtracks[u]['net'])for u in removed}")
s=s.replace('R365','R395')
exec(compile(s,str(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py'),'exec'))
