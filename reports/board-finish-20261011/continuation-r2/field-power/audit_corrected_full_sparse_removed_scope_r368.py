"""Correct independent reuse scope: authorized removals also dirty a net."""
from pathlib import Path
H=Path(__file__).resolve().parent
t=(H/'audit_corrected_full_sparse_current_r365.py').read_text(encoding='utf-8')
t=t.replace('REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r365','REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368').replace("s=s.replace('R358','R365')","s=s.replace('R358','R368')")
needle="exec(compile(s,str(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py'),'exec'))"
replacement="""dirty=\"affected={L.norm(t['net'])for t in nt+nv}|{L.norm(z['net'])for z in newq}\"
assert s.count(dirty)==1
s=s.replace(dirty,dirty+\"|{L.norm(oldtracks[u]['net'])for u in removed}\")
exec(compile(s,str(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py'),'exec'))"""
assert t.count(needle)==1;t=t.replace(needle,replacement)
exec(compile(t,str(H/'audit_corrected_full_sparse_current_r365.py'),'exec'))
