"""Correct one pre-emission literal count; preserve R572 failed reader."""
from pathlib import Path
H=Path(__file__).resolve().parent
src=H/'prepare_DI6_actual_retained_target_route_r572.py';code=src.read_text();a="sub('R570_','R572_',5)";assert code.count(a)==1
code=code.replace(a,"sub('R570_','R572_',4)").replace('r572','r574').replace('R572','R574');exec(compile(code,str(src),'exec'))
