"""Minimal local full-width bend; keep the rejected full-frame R255 visible."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_T4_duplicate_CORE5_fullwidth_detour_r255.py').read_text()
old="corepoints=[[154.65,96.65],[154.65,98.05],[167.75,98.05],[167.75,96.65]]"
new="corepoints=[[154.65,96.65],[155.4,97.15],[158.0,97.15],[159.1,96.65],[167.75,96.65]]"
assert s.count(old)==1
s=s.replace(old,new).replace('r255','r256').replace('R255','R256')
exec(compile(s,str(__file__),'exec'))
