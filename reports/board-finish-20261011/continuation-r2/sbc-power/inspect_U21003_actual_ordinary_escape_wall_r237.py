"""Preserve R236 compile failure; inventory exact wall source functions."""
from pathlib import Path
P=Path(__file__).resolve().parent
old=P/'inspect_U21003_actual_ordinary_escape_wall_r236.py'
s=old.read_text();assert 'elseNone'in s
s=s.replace('elseNone','else None').replace('U21003-actual-ordinary-escape-wall-r236','U21003-actual-ordinary-escape-wall-r237').replace('R236_COMPLETE','R237_COMPLETE')
exec(compile(s,str(__file__),'exec'))
