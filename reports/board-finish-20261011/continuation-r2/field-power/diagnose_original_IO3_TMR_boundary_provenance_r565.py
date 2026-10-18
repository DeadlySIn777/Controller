"""Read-only original IO3 outline/cache/fresh-fill TMR boundary attribution."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,re,time
from decimal import Decimal
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
from verify_source import P as SP
from inventory import sha
OUT=H/'original-IO3-native-TMR-boundary-outline-cache-fill-provenance-r565'
N=ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl'
UUID='54921f4b-0308-4821-9549-ff9360bf05ca';AREA='db0285ed-ad42-400f-9df4-32278be33f57'
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return dict(empty=s.is_empty,type=s.geom_type,area_mm2=s.area,length_mm=s.length,bounds_mm=None if s.is_empty else list(s.bounds),WKB_SHA256=hashlib.sha256(s.wkb).hexdigest())
def extract(path,uid):
 data=path.read_bytes();needle=('(uuid "'+uid+'")').encode();at=data.index(needle);begin=data.rfind(b'\n\t(zone',0,at)+1;end=re.search(rb'\r?\n\t\)\r?\n',data[at:]);assert begin>0 and end
 chunk=data[begin:at+end.end()];assert chunk.count(needle)==1;return chunk
def outline(ast):
 rings=[]
 for poly in SP['children'](ast,'polygon'):
  pts=SP['child'](poly,'pts');coords=SP['children'](pts,'xy');assert len(coords)+1==len(pts)
  ring=[]
  for xy in coords:
   vals=[]
   for v in xy[1:]:
    x=Decimal(str(v))*1000000;assert x==x.to_integral_value();vals.append(int(x))
   ring.append(vals)
  rings.append(ring)
 return rings
def geometry(shape,name,area,rows):
 (OUT/(name+'.wkb')).write_bytes(shape.wkb);hit=shape.intersection(area);(OUT/(name+'-closed-AREA-intersection.wkb')).write_bytes(hit.wkb)
 rows.append({'control':name,'physical_or_outline':ds(shape),'strict_closed_AREA_intersection':ds(hit),'predicate_requires_nonempty_line_to_remain_FAIL':True})
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862'
 paths={'R218_selected_input':N/'copy/board.kicad_pcb','R157_frozen_parent_input':ROOT/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','R9_frozen_input':ROOT/'SAFE-exploratory-native-trial-r9/copy/board.kicad_pcb','R9_saved_native_full_refill':ROOT/'SAFE-exploratory-native-trial-r9/measure/copy/board.kicad_pcb'}
 pins={str(x.resolve()):sha(x) for x in paths.values()};assert pins[str(paths['R218_selected_input'].resolve())]=='6befbca6dcac6bfe812dc8be04069701338f8ef95159faf9a5cb4a114395d55e'
 assert pins[str(paths['R157_frozen_parent_input'].resolve())]=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
 rows=[];raw={};profiles={};rings={};area_chunks={}
 for label,path in paths.items():
  chunk=extract(path,UUID);(OUT/(label+'-original-zone.chunk')).write_bytes(chunk);ast=SP['sexpr_parse'](chunk.decode());assert SP['atom'](ast,'uuid')==UUID
  raw[label]=hashlib.sha256(chunk).hexdigest();rings[label]=outline(ast);profiles[label]=[x for x in ast[1:] if isinstance(x,list) and x[0] not in ('filled_polygon','fill_segments')]
  area_chunk=extract(path,AREA);area_chunks[label]=hashlib.sha256(area_chunk).hexdigest();aa=SP['sexpr_parse'](area_chunk.decode());ar=outline(aa);assert ar==[[[348198000,130350000],[323998000,130350000],[323998000,118650000]]]
  area=Polygon([(x/1e6,y/1e6)for x,y in ar[0]])
  for k,ring in enumerate(rings[label]):
   shape=Polygon([(x/1e6,y/1e6)for x,y in ring]);assert shape.is_valid
   geometry(shape,label+'-raw-outline-ring-'+str(k),area,rows)
  cache=[]
  for fp in SP['children'](ast,'filled_polygon'):
   if SP['atom'](fp,'layer')!='In2.Cu':continue
   coords=SP['children'](SP['child'](fp,'pts'),'xy');ring=[(float(x[1]),float(x[2])) for x in coords];shape=Polygon(ring)
   cache.append({'ring_points':len(ring),'raw_shape_valid':shape.is_valid,'raw_shape':ds(shape),'closed_AREA_intersection':ds(shape.intersection(area)) if shape.is_valid else 'RAW_RING_INVALID_NO_GEOMETRY_REPAIR_OR_CREDIT'})
  put(OUT/(label+'-raw-original-In2-filled-cache.json'),cache)
 g,h,b,q,c=pickle.loads(M.read_bytes())
 for label,board in [('R515_original_fresh_198b_h',h),('R515_actual_current_candidate',c)]:
  z=next(x for x in board['zones'] if x['uuid']==UUID);shape=unary_union(L.poly(z['fills'].get('In2.Cu',[])));geometry(shape,label+'-In2-filled',area,rows)
 for label,path in [('original_native_198b_export',ROOT/'native-198b-geometry/geometry.json'),('R9_fresh_full_native_export',ROOT/'SAFE-exploratory-native-trial-r9/measure/actual-full-refill-geometry.json'),('R218_fresh_selected_native_export',N/'scoped-fill/geometry.json')]:
  data=json.loads(path.read_bytes());z=next(x for x in data['zones'] if x['uuid']==UUID);shape=unary_union(L.poly(O.polys(z['fills'].get('In2.Cu',[]))));geometry(shape,label+'-In2-filled',area,rows);pins[str(path.resolve())]=sha(path)
  if 'outline' in z:geometry(unary_union(L.poly(O.polys(z['outline']))),label+'-native_API_outline',area,rows)
 p157=ROOT/'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-geometry.json'
 unavailable=[]
 if p157.exists():
  data=json.loads(p157.read_bytes());z=next(x for x in data['zones']if x['uuid']==UUID);geometry(unary_union(L.poly(O.polys(z['fills'].get('In2.Cu',[])))),'R157_fresh_full_native_export-In2-filled',area,rows);pins[str(p157.resolve())]=sha(p157)
 else:unavailable.append({'file':str(p157.resolve()),'reason':'Running frozen native job has not produced this file; no waiting, modification or fresh launch.'})
 assert all(sha(Path(p))==v for p,v in pins.items())
 put(OUT/'exact-original-native-outline-area-source-controls.json',{'original_zone_UUID':UUID,'original_zone_chunk_sha256':raw,'raw_outline_integer_rings':rings,'zone_AST_excluding_only_filled_cache_equal_across_all_controls':all(v==next(iter(profiles.values()))for v in profiles.values()),'TMR_raw_AREA_chunk_sha256':area_chunks,'TMR_raw_AREA_all_control_bytes_equal':len(set(area_chunks.values()))==1,'original_zone_outline_and_all_settings_not_changed_by_R515_or_R218':profiles['R218_selected_input']==profiles['R157_frozen_parent_input'],'original_zone_input_cache_bytes_equal_R218_vs_R157':raw['R218_selected_input']==raw['R157_frozen_parent_input']})
 put(OUT/'closed-native-area-physical-outline-and-fill-control-results.json',rows)
 put(OUT/'receipt.json',{'status':'READ_ONLY_ORIGINAL_NATIVE_TMR_CLOSED_BOUNDARY_PROVENANCE_DIAGNOSIS_RAW_FAIL_PRESERVED','pins':pins,'model_SHA256':sha(M),'original_zone_UUID':UUID,'exact_original_native_zone_settings_outline_equality_R218_R157':profiles['R218_selected_input']==profiles['R157_frozen_parent_input'],'all_native_AREA_AST_bytes_equal':len(set(area_chunks.values()))==1,'controls':rows,'unavailable_controls':unavailable,'no_native_job_no_original_fill_or_outline_edit_no_rule_change':True,'closed_boundary_LineString_is_NOT_waived':True,'minimal_next_native_diagnostic':'Existing exact native candidate/project/DRU: invoke native rule provider / CLI DRC for items_not_allowed without refill and report original54921 UUID and exact TMR area. No geometry, rule, source, zone, cache or input edits; compare native reports with already preserved closed-set intersection. Full CLI may take time; parent owns existing test slot.','native_DRC_boundary_touch_behavior':'OPEN; read-only geometry does not establish provider collision semantics','adopted':False,'elapsed_seconds':time.monotonic()-st})
 print('R565',sha(OUT/'receipt.json'),'controls',len(rows),flush=True)
if __name__=='__main__':main()
