"""Successor correcting the read-only diagnostic's unavailable body API."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'inspect_U10003_two_actual_logic_walls_r137.py'
code=source.read_text()
assert code.count('C.track(t)')==1
code=code.replace('C.track(t)','C.body(t)').replace('coupled-geometry-r137','coupled-geometry-r138')
# No largest-group source substitution: diagnose literal connector membership.
code=code.replace("if not roots:roots=[max(groups[net],key=len)]","assert roots, ('literal connector ground source absent',net,ref,pin)")
exec(compile(code,str(source),'exec'))
