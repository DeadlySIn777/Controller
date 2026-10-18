"""Fresh read-only endpoint attribution of the exact B-only nomination."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_U10003_B_only_fault_source_pad_r180.py'
code=source.read_text().replace('r180','r183')
anchor="code=code.replace('fault-two-existing-barrel-one-layer-replacement-r128','B-only-fault-source-pad-nomination-r183')"
assert code.count(anchor)==1
code=code.replace(anchor,anchor+"\ncode=code.replace(\"for d in ('field-power','sbc-power'):\",\"for d in ('field-power','sbc-power','coupled-recovery'):\")")
anchor="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))"
assert code.count(anchor)==1
extra="""
needle="row={'layer':layer,'window_margin_mm':margin,'common_faces':len(faces)}"
assert code.count(needle)==1
code=code.replace(needle,"row={'layer':layer,'window_margin_mm':margin,'common_faces':len(faces),'start_free':free.covers(start),'end_free':free.covers(end),'start_blockers':[i for i,s in enumerate(obstacles)if s.covers(start)],'end_blockers':[i for i,s in enumerate(obstacles)if s.covers(end)]}")
"""
code=code.replace(anchor,extra+'\n'+anchor)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
