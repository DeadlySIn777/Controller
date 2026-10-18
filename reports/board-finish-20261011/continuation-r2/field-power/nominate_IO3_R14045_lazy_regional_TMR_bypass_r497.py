"""Same constraints, lazy reference masks after fixed source-layer cases.

All original reference bodies remain hard on their actual reference layer;
provably disjoint full-cap bounds skip expensive global intersections.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'nominate_IO3_R14045_existing_barrel_TMR_bypass_r495.py').read_text(encoding='utf-8')
s=s.replace("O=H/'IO3-R14045-existing-native-barrel-TMR-legal-bypass-nomination-r495'", "O=H/'IO3-R14045-lazy-regional-existing-barrel-TMR-bypass-r497'")
start=s.index(' # Ground reference masks must remain exact')
end=s.index(' rows=[];accepted=None',start)
replacement=""" # In2/In3 do not cut the actual In1/In4 reference layers. Build all
 # supported track AND DC-q masks only if a later reference-layer case occurs.
 old=None;protect={'In1.Cu':[],'In4.Cu':[]};references_built=False
 def build_reference_masks():
  nonlocal old,references_built
  old=pickle.loads((H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl').read_bytes())
  region=box(via['x']-42.,via['y']-42.,via['x']+42.,via['y']+42.)
  for net,ref,pin in K.ROOTS[:3]:
   rr=K.source_refs(K.root(old[net],ref,pin));req=max(.25,gap(net))+.0251
   for t in c['tracks']:
    if t['layer']not in K.MAP:continue
    if not t.get('m'):
     x0=min(t['a'][0],t['b'][0])-t['w']/2;y0=min(t['a'][1],t['b'][1])-t['w']/2;x1=max(t['a'][0],t['b'][0])+t['w']/2;y1=max(t['a'][1],t['b'][1])+t['w']/2
     if x1<region.bounds[0]or x0>region.bounds[2]or y1<region.bounds[1]or y0>region.bounds[3]:continue
    body=L.body(t)
    if not body.intersects(region):continue
    supported=body.intersection(region).intersection(rr[t['layer']]);layer=K.MAP[t['layer']]
    if not supported.is_empty:protect[layer].append(lit(N.bounded_buffer(supported,req)))
   for z in q:
    if z['layer']not in K.MAP or not z['shape'].intersects(region):continue
    supported=lit(z['shape']).intersection(region).intersection(rr[z['layer']]);layer=K.MAP[z['layer']]
    if not supported.is_empty:protect[layer].append(lit(N.bounded_buffer(supported,req)))
  references_built=True
"""
s=s[:start]+replacement+s[end:]
s=s.replace(" for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):", " for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):\n  if layer in protect and not references_built:build_reference_masks()")
s=s.replace('R495 case','R497 case').replace('R495 receipt','R497 receipt').replace('TMR-r495','TMR-r497')
exec(compile(s,str(H/'nominate_IO3_R14045_lazy_regional_TMR_bypass_r497.py'),'exec'))
