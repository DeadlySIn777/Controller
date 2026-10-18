"""Read-only exact final union enclosure/settings/own-plated landing census."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,sys,time
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('coupled-recovery','sbc-power'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import restore_field_current_mixed_precision_states_r366 as MS
M=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/model.pkl'
P=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl'
OUT=H/'final-four-direction-union-native-intent-scope-readonly-r651'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(M)=='7141d6d37a909617aa339dadfc3b8a1b539904af1b06b2bf8f00ea2abeee69f9'
 g,h,b,q,c=pickle.loads(M.read_bytes());pg,ph,pb,pq,pc=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(b,q);MS.restore_bound_field_current_precision_states(pb,pq)
 pk=M.parent/'only-four-current-member-to-qualified-direction-union-operation-candidates.pkl';assert sha(pk)=='6fa00a4fa7f7cce7025d7574b28a6f2b26e7820d63b124df6bdcdaa1f974b766';plans=pickle.loads(pk.read_bytes());newids={a['new_q']['uuid']for a in plans};oldids={u for a in plans for u in a['members_before_UUIDs']}
 enclosure=[];landings=[];overlaps=[];errors=[]
 fields=('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
 for pl in plans:
  z=pl['new_q'];assert z==next(a for a in q if a['uuid']==z['uuid']);assert all(tuple(z[k]for k in fields)==tuple(a[k]for k in fields)for a in pl['exact_before_q'])
  actual=zero(z['shape']).difference(zero(z['zone_outline_shape']));before=unary_union([zero(a['shape']).difference(zero(a['zone_outline_shape']))for a in pl['exact_before_q']]);novel=actual.difference(before);row={'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'nine_settings_exact_all_members':True,'physical_outside_intended_raw':ds(actual),'before_member_physical_outside_intended_raw':ds(before),'novel_outside_intended_raw':ds(novel)};enclosure.append(row)
  if not novel.is_empty:errors.append({'kind':'NOVEL_PHYSICAL_OUTSIDE_NATIVE_INTENDED','row':row})
  for v in c['vias']:
   if v['net']!=z['net']or z['layer']not in v.get('flashed',v['span']):continue
   at=Point(v['x'],v['y'])
   if at.distance(z['shape'])>v['d']/2:continue
   ann=at.buffer(v['d']/2,quad_segs=64).difference(at.buffer(v['drill']/2,quad_segs=64));hit=zero(z['shape']).intersection(ann)
   if hit.is_empty or hit.area<=0:continue
   inside=zero(z['zone_outline_shape']).covers(at);line={'new_union_UUID':z['uuid'],'existing_via_UUID':v['uuid'],'at_mm':[v['x'],v['y']],'raw_net':v['net'],'layer':z['layer'],'intended_covers_via_centre':inside,'nominal_annular_overlap_mm2':hit.area,'source_and_CPP_actual_annular_contact':'SEPARATE_OPEN'};landings.append(line)
   if not inside:errors.append({'kind':'EXPECTED_ANNULAR_ATTACHMENT_CENTRE_OUTSIDE_NATIVE_INTENDED','row':line})
 for i,a in enumerate(q):
  for bq in q[i+1:]:
   if not({a['uuid'],bq['uuid']}&newids)or a['layer']!=bq['layer']:continue
   hit=zero(a['zone_outline_shape']).intersection(zero(bq['zone_outline_shape']))
   if hit.is_empty:continue
   row={'UUIDs':[a['uuid'],bq['uuid']],'raw_nets':[a['net'],bq['net']],'layer':a['layer'],'actual_intended_intersection':ds(hit),'same_all_nine_settings':tuple(a[k]for k in fields)==tuple(bq[k]for k in fields)};overlaps.append(row);errors.append({'kind':'NEW_UNION_NATIVE_INTENDED_INTERSECTION_WITH_ANOTHER_OWNED_ZONE','row':row})
 put(OUT/'raw-enclosure-and-own-annular-landing-census.json',{'enclosure':enclosure,'landings':landings,'overlaps':overlaps,'errors':errors})
 put(OUT/'receipt.json',{'status':'PASS_MINIMAL_UNION_NATIVE_INTENT_SCOPE_RAW_INHERITED_FAILS_RETAINED'if not errors else'REPAIR_REQUIRED_FINAL_UNION_NATIVE_INTENT_SCOPE','model_SHA256':sha(M),'four_cluster_packet_SHA256':sha(pk),'scope_census_SHA256':sha(OUT/'raw-enclosure-and-own-annular-landing-census.json'),'errors':errors,'inherited_raw_physical_outside_intended_not_waived':True,'no_geometry_or_native_mutation':True,'native_CPP_API_fullfill_DRC_current_return_thermal':'OPEN','elapsed_seconds':time.monotonic()-st});print('R651',sha(OUT/'receipt.json'),'errors',len(errors),flush=True)
if __name__=='__main__':main()
