"""Conservative new-outline clipping before exact 1 nm coverage checks."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_regulated_native_bound_lazy_feeds_r112.py').read_text().replace('regulated-native-bound-lazy-source-feeds-r112','regulated-quantized-inner-source-feeds-r114').replace('controller-regulated-r112/','controller-regulated-r114/')
# R112 composes R105, which composes frozen R76. Add this final scoped source
# transform after that wrapper has prepared its underlying constructor.
s=s.replace("exec(compile(s,str(p/'construct_regulated_lazy_feeds_r105.py'),'exec'))", "s=s.replace(\"exec(compile(s,str(p/'construct_regulated_adaptive_feeds_r76.py'),'exec'))\",\"s=s.replace(\\\"native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)\\\",\\\"construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)\\\");exec(compile(s,str(p/'construct_regulated_adaptive_feeds_r76.py'),'exec'))\");exec(compile(s,str(p/'construct_regulated_lazy_feeds_r105.py'),'exec'))")
exec(compile(s,str(p/'construct_regulated_native_bound_lazy_feeds_r112.py'),'exec'))
