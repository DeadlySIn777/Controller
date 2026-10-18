"""Preserved R149 search-only base, corrected existing-barrel loop adapter."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'field5-IO3-preserving-In3-alternate-r150';BASE=HERE/'field5-alternate-search-base-r149'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']", "INNER=['In3.Cu']")
s=s.replace("for bank,net,ref,pin,policy in PORTS:", "for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='FIELD5']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11071','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):", "for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):")
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)", "construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
old="for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):"
assert s.count(old)==1;s=s.replace(old, "for a in []: # existing plated ports only; no ordinary-via fallback")
s=s.replace('controller-regulated-r76/', 'controller-regulated-IO3-preserving-r150/')
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
