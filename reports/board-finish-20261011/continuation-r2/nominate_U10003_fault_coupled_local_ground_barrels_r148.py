"""Refine the exact near-legal primary FG site without moving retained Cu."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_fault_coupled_ground_barrels_r147.py';code=source.read_text()
code=code.replace('barrel-nominees-r147','barrel-nominees-r148')
start=code.index(' sites=[');end=code.index('\n rows=[];accepted=[]',start)
code=code[:start]+" sites=[(x,y)for x in(216.03,216.04,216.05,216.06)for y in(142.94,142.95,142.96)]"+code[end:]
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
