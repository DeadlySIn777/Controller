"""Scoped reason diagnostics for the first existing FIELD5 barrel corridor."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_regulated_adaptive_feeds_r76.py').read_text().replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'first-regulated-bridge-rejection-diagnostic-r113';BASE=HERE/'corrected-regulated-native-bound-search-base-r111'")
s=s.replace("for bank,net,ref,pin,policy in PORTS:","for bank,net,ref,pin,policy in PORTS[:1]:")
s=s.replace("for width in(.5,.35):","for width in(.35,):").replace("for margin in(8.,25.,60.,140.,None):","for margin in(8.,):")
s=s.replace("for gi in wanted:","for gi in wanted[:1]:")
s=s.replace("for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):","for a in []:")
s=s.replace("try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))\n       except(AssertionError,ValueError):continue","print('R113 route',l,width,margin,get_num_coordinates(part),flush=True)\n       try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))\n       except(AssertionError,ValueError) as err:\n        print('R113 tri rejection',l,type(err).__name__,str(err),flush=True);continue")
s=s.replace("if not free.covers(core):continue","if not free.covers(core):\n        print('R113 rounded_core_outside',l,core.difference(free).area,search,flush=True);continue")
s=s.replace("if not free.covers(body) or body.intersection(sh).area<.001 or body.intersection(source[l]).area<1e-8:continue","if not free.covers(body) or body.intersection(sh).area<.001 or body.intersection(source[l]).area<1e-8:\n        print('R113 body rejection',l,'outside',body.difference(free).area,'target',body.intersection(sh).area,'source',body.intersection(source[l]).area,search,flush=True);continue")
s=s.replace("controller-regulated-r76/","controller-regulated-diagnostic-r113/")
exec(compile(s,str(p/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
