"""Retain R444 compile failure; repair only conditional token spacing."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'qualify_prospective_CM73_ground_port_small_move_r444.py').read_text(encoding='utf-8')
assert 'else0' in s
s=s.replace('else0','else 0').replace('CM73-only-prospective-de03-80um-shift-two-owned-F-source-tracks-r444','CM73-only-prospective-de03-80um-shift-two-owned-F-source-tracks-r445').replace("'CM73-R444-","'CM73-R445-").replace("print('R444_COMPLETE'","print('R445_COMPLETE'")
E=P/'exact-expanded-de03-small-prospective-move-r445.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
