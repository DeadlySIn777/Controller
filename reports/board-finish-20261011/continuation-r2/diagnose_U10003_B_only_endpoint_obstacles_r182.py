"""Read-only R181 no-path attribution; retain the original exact hard scene."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_U10003_B_only_fault_source_pad_r181.py'
code=source.read_text().replace('r181','r182')
needle="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))"
assert code.count(needle)==1
extra="""
needle="free=win.difference(unary_union(obstacles));faces=[s for s in polys(free) if s.covers(start) and s.covers(end)]"
assert code.count(needle)==1
code=code.replace(needle,"free=win.difference(unary_union(obstacles));faces=[s for s in polys(free) if s.covers(start) and s.covers(end)];print('R182_ENDPOINTS',{'margin':margin,'start_free':free.covers(start),'end_free':free.covers(end),'start_blockers':[i for i,s in enumerate(obstacles)if s.covers(start)],'end_blockers':[i for i,s in enumerate(obstacles)if s.covers(end)]},flush=True)")
"""
code=code.replace(needle,extra+'\n'+needle)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
