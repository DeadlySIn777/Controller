"""Preserve R174 path failure; bind the actual frozen R173 nomination directory."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'construct_U10003_preserved_branch_exact_two_port_reference_r174.py';code=source.read_text()
code=code.replace('reference-construction-r174','reference-construction-r175')
old="H/'U10003-exact-stub-source-seeded-ground-reference-nomination-r173'"
new="H/'U10003-two-signal-port-exact-stub-source-seeded-ground-reference-nomination-r173'"
assert code.count(old)==1;code=code.replace(old,new)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
