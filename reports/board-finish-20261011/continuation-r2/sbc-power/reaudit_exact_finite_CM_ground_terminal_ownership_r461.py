"""Actual endpoint-disc annulus overlap qualifies a genuine owned terminal."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-explicit-CM-terminal-joint-reaudit-r458.py').read_text(encoding='utf-8')
s=s.replace('CM51-explicit-terminal-joints-fresh-true-guards-and-SOURCE-before-graph-r458','CM51-finite-owned-terminals-five-inline-joints-fresh-analytic-and-source-graph-r461')
s=s.replace('CM51-explicit-only-NEW-ground-terminal-joints-and-named-R450-path-r457','CM51-five-ONLY_NEW-inline-joints-original-CM32-finite-terminal-r460').replace('only-NEW-six-terminal-joint-repairs-one-path-ownership.pkl','only-NEW-five-inline-joints-and-exact-terminal-ownership.pkl')
old="min(Point(xy).distance(Point(owner['x'],owner['y']))for xy in (it['a'],it['b']))<=owner['d']/2+.000002"
new="any(Point(xy).distance(Point(owner['x'],owner['y']))<=owner['d']/2+.000002 or Point(xy).buffer(rad,quad_segs=128).intersection(Point(owner['x'],owner['y']).buffer(owner['d']/2,quad_segs=128).difference(sh)).area>0 for xy in (it['a'],it['b']))"
assert old in s;s=s.replace(old,new)
s=s.replace("'R458_ANALYTIC'","'R461_ANALYTIC'").replace("'R458_COMPLETE'","'R461_COMPLETE'").replace("'R457_controlled_terminal_packet_SHA256'","'R460_controlled_terminal_packet_SHA256'")
E=P/'exact-expanded-finite-CM-ground-terminal-reaudit-r461.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
