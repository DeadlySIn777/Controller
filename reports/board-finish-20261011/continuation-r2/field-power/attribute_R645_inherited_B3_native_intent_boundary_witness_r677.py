"""Read-only exact controlling-edge attribution; no boundary repair yet."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time
from pathlib import Path
from fractions import Fraction
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
P=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/only-four-current-member-to-qualified-direction-union-operation-candidates.pkl'
OUT=H/'R645-inherited-B3-native-intent-raw-witness-controlling-edge-attribution-r677'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def polys(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return [p for g in getattr(s,'geoms',[])for p in polys(g)]
def edges(uid,role,s):
 out=[]
 for pi,p in enumerate(polys(s)):
  for ri,r in enumerate([p.exterior,*p.interiors]):
   pp=list(r.coords)
   for ei,(a,b)in enumerate(zip(pp,pp[1:])):
    if a==b:continue
    line=LineString([a,b]);out.append({'source_UUID':uid,'role':role,'polygon_index':pi,'ring_index_outer0':ri,'edge_index':ei,'exact_binary64_endpoints':[list(a),list(b)],'native_IU_endpoint_tokens':[[int(round(x*1e6)),int(round(y*1e6))]for x,y in(a,b)],'line':line})
 return out
def rational(point):return [[str(Fraction.from_float(float(x)).numerator),str(Fraction.from_float(float(x)).denominator)]for x in point]
assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(P)=='6fa00a4fa7f7cce7025d7574b28a6f2b26e7820d63b124df6bdcdaa1f974b766';packet=pickle.loads(P.read_bytes());op=packet[1];q=op['new_q'];assert q['uuid']=='f595cb04-2945-5e6a-9b86-f7c7c6e1b0c1';physical=zero(q['shape']);intended=zero(q['zone_outline_shape']);witness=physical.difference(intended);assert hs(witness)=='0c1c1151ce54f0d4394e70076ad33501eede09a8bf7cd1680a027b54f55ec364'and not witness.is_empty;(OUT/'exact-inherited-physical-outside-intended-RAW_FAIL.wkb').write_bytes(witness.wkb)
edgegroups={}
for role,s in(('shape',physical),('zone_outline_shape',intended)):
 rows=edges(q['uuid'],role,s);edgegroups['current_'+role]=(rows,STRtree([r['line']for r in rows]))
for role in('shape','zone_outline_shape'):
 rows=[r for old in op['exact_before_q']for r in edges(old['uuid'],role,zero(old[role]))];edgegroups['R543_member_'+role]=(rows,STRtree([r['line']for r in rows]))
points=[];seen=set()
for wi,p in enumerate(polys(witness)):
 (OUT/(f'raw-positive-witness-{wi}.wkb')).write_bytes(p.wkb)
 for vi,xy in enumerate(p.exterior.coords):
  if tuple(xy)in seen:continue
  seen.add(tuple(xy));axis=Point(*xy);nearest={}
  for name,(rs,tree)in edgegroups.items():
   row=rs[int(tree.nearest(axis))];nearest[name]={k:v for k,v in row.items()if k!='line'};nearest[name]['raw_distance_to_complete_named_edge_mm']=axis.distance(row['line']);f=OUT/(name+'-'+str(len(points))+'.wkb');f.write_bytes(row['line'].wkb);nearest[name]['complete_edge_file']=str(f.resolve());nearest[name]['complete_edge_SHA256']=sha(f)
  points.append({'witness_component':wi,'vertex':vi,'exact_binary64_xy_mm':list(xy),'exact_binary64_Fraction_xy':rational(xy),'nearest_complete_current_and_old_member_edges':nearest,'distance_is_attribution_ONLY_not_Cu_waiver_or_classification':True})
put(OUT/'all-exact-witness-vertices-and-four-source-edge-attributions.json',points)
put(OUT/'receipt.json',{'status':'READONLY_INHERITED_B3_PHYSICAL_OUTSIDE_INTENDED_RAW_FAIL_EXACT_EDGE_ATTRIBUTION_COMPLETE','current_R643_sparse_packet_SHA256':sha(P),'current_B3_union_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_role_SHA256':hs(physical),'intended_role_SHA256':hs(intended),'raw_literal_physical_outside_intended_FAIL':ds(witness),'outside_positive_polygon_component_count':len(polys(witness)),'exact_distinct_witness_vertices':len(points),'raw_failed_geometry_and_all_old_current_source_scope_UNCHANGED':True,'no_regrid_clip_positive_addition_or_negative_wedge_or_model_write':True,'possible_future_repair_scope':'Only separately declared controlling owned boundary changes, with explicit added/removed Cu and true foreign/native/oldcontact/source/strictreference/current tests; no future geometry proposed by this attribution.','source_enclosure_native_current_loop_thermal_fullboard':'FAIL/OPEN retained','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R677_COMPLETE',sha(OUT/'receipt.json'),'witnesses',len(points),flush=True)
