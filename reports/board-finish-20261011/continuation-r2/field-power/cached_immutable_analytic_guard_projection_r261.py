"""Exact input-keyed cache/progress adapter; no geometric operator changes."""
import inspect,hashlib
from shapely import get_precision
from shapely.geometry import Point
import immutable_baseline_analytic_guard_supplements_r252 as IP
cache={};stats={'calls':0,'exact_input_hits':0,'original_operator_calls':0};proofs=[]
def cached_buffer(shape,distance):
 raw=shape.wkb;grid=get_precision(shape);key=(hashlib.sha256(raw).hexdigest(),grid,float(distance));stats['calls']+=1
 if key in cache:
  original_raw,result=cache[key];assert raw==original_raw,'guard hash collision';stats['exact_input_hits']+=1;return result
 result=IP.BASE.P.bounded_buffer(shape,distance);cache[key]=(raw,result);stats['original_operator_calls']+=1
 proofs.append({'input_WKB_SHA256':key[0],'input_GE0S_grid_mm':grid,'unchanged_distance_mm':distance,'exact_original_outward_operator_output_SHA256':IP.BASE.P.digest(result)})
 return result
def cached_disk(v,radius):return cached_buffer(Point(v['x'],v['y']),radius)
ns=dict(IP.projected.__globals__);ns.update({'cached_buffer':cached_buffer,'cached_disk':cached_disk})
rows=inspect.getsource(IP.BASE.primitive_rows).replace('P.bounded_buffer','cached_buffer').replace('P.bounded_disk','cached_disk')
exec(compile(rows,__file__,'exec'),ns)
source=IP.source.replace("  result.append(row)","  result.append(row)\n  if len(result)%10==0:print('R261 native definitions projected',len(result),'buffer calls/hits/original',stats['calls'],stats['exact_input_hits'],stats['original_operator_calls'],flush=True)")
ns['stats']=stats
exec(compile(source,__file__,'exec'),ns)
projected=ns['projected']
