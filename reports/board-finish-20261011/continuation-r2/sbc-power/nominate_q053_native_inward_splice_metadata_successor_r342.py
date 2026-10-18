"""Preserve R341 metadata-name failure; same owned splice in a successor."""
from pathlib import Path
p=Path(__file__).with_name('nominate_q053_only_new_native_inward_intersection_splices_r341.py')
t=p.read_text(encoding='utf-8').replace('proposal-r341','proposal-r342').replace('R341','R342')
t=t.replace("write_text(s,encoding='utf-8')", "write_text(EXACT_EXPANDED_SOURCE,encoding='utf-8')")
needle="exec(compile(s,str(__file__),'exec'))"
assert t.count(needle)==1
t=t.replace(needle,"EXACT_EXPANDED_SOURCE=s\n"+needle)
exec(compile(t,str(__file__),'exec'))
