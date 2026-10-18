"""Preserve stopped R158 and derive lazy regional reference-mask construction."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
src=P/'construct_IO3_safe_existing_via_reroute_r158.py'
s=src.read_text()
s=s.replace("IO3-safe-existing-via-reroute-r158","IO3-safe-existing-via-reroute-r162").replace("source-safe R11049 existing-via bridge R158","source-safe R11049 existing-via bridge R162").replace("controller/IO3-SAFE-owned-replacement-r158/","controller/IO3-SAFE-owned-replacement-r162/").replace("IO3_SAFE_R158_FROZEN","IO3_SAFE_R162_FROZEN")
s=s.replace("u10017-protected-source-via-bypass-nominee-r154","u10017-reference-safe-source-bypass-nominee-r160")
s=s.replace(" rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'][RAW]"," dom=h['domains_normalized'][RAW]")
start=s.index(" refs={};refrows=[]")
end=s.index(" attempts=[];answer=None;chosen=None",start)
s=s[:start]+''' holes=[(p['uuid'],p['net'],s) for p in hard_h['pads'] for s in C.poly(p.get('hole') or [])]+[(vv['uuid'],vv['net'],Point(vv['x'],vv['y']).buffer(vv['drill']/2,quad_segs=128)) for vv in hard_h['vias']]
 ht=STRtree([s for uid,n,s in holes]);ownholes=unary_union([s for uid,n,s in holes if n==RAW])
 refs={};refrows=[];oldfills={l:[s for q in h['zones'] if C.norm(q['net'])=='/LOGIC_GND' for s in C.poly(q['fills'].get(l,[]))] for l in ('In1.Cu','In4.Cu')};oldfilltrees={l:STRtree(ss) for l,ss in oldfills.items()}
 def reference_mask(layer,query):
  if layer not in ('In1.Cu','In4.Cu'):return None
  key=(layer,query.bounds)
  if key in refs:return refs[key]
  outer=('F.Cu',) if layer=='In1.Cu' else ('B.Cu','In3.Cu');bodies=[]
  for ol in outer:
   for i in trees[ol].query(query,predicate='intersects'):
    r=rec[ol][int(i)]
    if r['kind']!='track' or r['net']=='/LOGIC_GND' or hard_h['domains_normalized'].get(C.norm(r['net']))!=hard_h['domains_normalized']['/LOGIC_GND']:continue
    t=r['source'];bodies.append(LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128).intersection(query))
  fills=[oldfills[layer][int(i)].intersection(query) for i in oldfilltrees[layer].query(query,predicate='intersects')]
  mask=unary_union(bodies).intersection(unary_union(fills));refs[key]=mask;refrows.append({'reference_layer':layer,'regional_query_bounds_mm':query.bounds,'actual_original_fill_intersection_mm2':mask.area,'hard_mask_WKB_SHA256':digest(mask),'conservative_all_original_LOGIC_fill_not_unproven_source_credit':True});return mask
''' +s[end:]
s=s.replace("   if layer in refs and refs[layer].intersects(query):obs.append(GP.bounded_buffer(refs[layer].intersection(query),.175+.000020))","   refmask=reference_mask(layer,query)\n   if refmask is not None and not refmask.is_empty:obs.append(GP.bounded_buffer(refmask,.175+.000020))")
out=P/'construct_IO3_safe_existing_via_reroute_r162.py';assert not out.exists();out.write_text(s)
receipt={'verdict':'R158_DELIBERATELY_STOPPED_BEFORE_ANY_ACCEPTED_OR_ATTEMPTED_GEOMETRY_LAZY_REGIONAL_SUCCESSOR','stopped_exact_owned_PID':33036,'stopped_script_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'reason':'Avoid repeated full-board reference intersections before a small In2 source search; lazy regional intersections retain the same conservative original body/fill obligation.','accepted_zones':0,'attempts_file_absent':not(P/'IO3-safe-existing-via-reroute-r158/attempts.json').exists(),'withdrawn_field_R154_in_successor':True,'replacement_field_R160_hard_only':True,'successor_script_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'native_jobs':0,'board_written':False}
(P/'IO3-safe-existing-via-reroute-r158/deliberate-stop-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n')
print(receipt)
