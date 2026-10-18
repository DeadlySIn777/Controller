"""Cover literal branch contacts without forcing the route axis onto them."""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route
from shapely.geometry import Point,LineString
OUT=H/'FPGA-CDONE-two-CORE-owners-literal-contact-coverage-inside-SOURCE-route-r48'
WALL={'233cfa24-bc17-4dfa-9617-321c8db03618','b1e1f4cd-cfe9-421c-8c66-6662888515d5'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):
 if s.is_empty:return []
 return [q for x in s.geoms for q in pieces(x)]if hasattr(s,'geoms')else[s]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-authorized-two-CORE-duplicate-detour-C1028-VIPPO-process-gated-screen-r47/receipt.json';r=json.loads(rp.read_bytes());cp=Path(r['cache_file']);assert sha(cp)==r['cache_SHA256'];d=pickle.loads(cp.read_bytes());c=d['c'];contact=d['CORE_contacts'];geo=d['CORE_geometry_free'];oldbody=K.L.body(d['CORE_before'][0]);rows=[(q,oldbody.intersection(K.L.body(q['exact_current_native_original_geometry'])))for q in contact['direct_same_net_native_F_contacts']if q['uuid']not in WALL];assert len(rows)==16
 branch=next(g for q,g in rows if q['uuid']=='a72621ad-3c77-4ab2-9703-4d31121c0e01');center=branch.centroid;bounds=branch.bounds;maxdist=max(center.distance(Point(x,y))for x in(bounds[0],bounds[2])for y in(bounds[1],bounds[3]));coverradius=.625-maxdist-.005;assert coverradius>0;coverage= center.buffer(coverradius,quad_segs=128);A=[148.65,90.65];P=[148.9,90.9];Q=[154.4,96.4];B=[154.65,96.65];sat=d['signal_at'];source=c['source_refs']['In1.Cu'].intersection(d['wide']['window'].buffer(2));results=[];accepted=[]
 for old in d['trials']:
  if not old.get('own_pad_contains_drill_with_5um_export_bound'):continue
  at=old['IO3_at'];cut=K.Z.bounded_disk({'x':at[0],'y':at[1]},.55).union(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.5));src=source.difference(cut);gfree=geo.difference(K.Z.bounded_disk({'x':at[0],'y':at[1]},1.10));strict=gfree.intersection(src.buffer(-.625100));row=dict(old);row.update(CORE_path=None,CORE_geometry_route=False,CORE_strict_source_route=False);path=None;mode=None
  for free,label in((strict,'strict_SOURCE'),(gfree,'geometry_only_raw_SOURCE_open')):
   component=next((p for p in pieces(free)if all(p.covers(Point(q))for q in(A,P,Q,B))and not p.intersection(coverage).is_empty),None)
   if component is None:continue
   contactport=component.intersection(coverage).representative_point();via=list(contactport.coords[0]);points=[A,P,via,Q,B];joined=[];meta=[]
   for left,right in zip(points,points[1:]):
    route,proof=tri_route.route(component,left,right);joined.extend(route if not joined else route[1:]);meta.append(proof)
   path=[[round(x,6),round(y,6)]for x,y in joined];mode=label;break
  if path is None:
   row['endpoint_or_contact_coverage_block']={'strict_endpoints':[strict.covers(Point(p))for p in(A,P,Q,B)],'geometry_endpoints':[gfree.covers(Point(p))for p in(A,P,Q,B)],'strict_coverage':info(strict.intersection(coverage)),'geometry_coverage':info(gfree.intersection(coverage))};results.append(row);continue
  axis=LineString(path);body=K.Z.bounded_buffer(axis,.625);missing=body.difference(src);loss=[];allcontacts=[]
  for oldcontact,g in rows:
   raw=g.difference(body);newoverlap=body.intersection(K.L.body(oldcontact['exact_current_native_original_geometry']));item={'UUID':oldcontact['uuid'],'old_contact':info(g),'new_finite_overlap':info(newoverlap),'literal_old_contact_loss':info(raw)};allcontacts.append(item)
   if not raw.is_empty:loss.append(item)
  row.update(CORE_path=path,CORE_geometry_route=True,CORE_strict_source_route=mode=='strict_SOURCE',CORE_route_method=mode,CORE_route_proof=meta,CORE_literal_contact_coverage_disk={'at':list(center.coords[0]),'radius_mm':coverradius,'branch_patch_bounding_corner_radius_mm':maxdist},CORE_new_whole_body_SOURCE_gap=info(missing),all16_retained_literal_contact_losses=loss,all16_retained_contact_checks=allcontacts,CORE_old_length_mm=math.sqrt(72),CORE_new_length_mm=axis.length)
  row['CORE_conditional_delta_R_25um_Cu_125C_ohm']=1.724e-5*(1+.00393*105)*(axis.length-math.sqrt(72))/(1.25*.025)
  if missing.is_empty and not loss:accepted.append(row)
  results.append(row);print(json.dumps({'phase':'CORE_CONTACT_COVERAGE_ROUTE','at':at,'route_method':mode,'new_source_gap_empty':missing.is_empty,'old_literal_contacts_lost':len(loss),'segments':len(path)-1}),flush=True)
 put('CORE-two-owner-contact-coverage-all-coupled-site-results.json',results);cache=OUT/'CORE-two-owner-exact-literal-contact-route-screen-context.pkl';cache.write_bytes(pickle.dumps({'prior':d,'results':results,'accepted':accepted,'contact_coverage':coverage},protocol=5));receipt={'verdict':'TWO_CORE_OWNERS_NATIVE_WIDTH_FULL_SOURCE_LITERAL_16_CONTACT_SCREEN_PASS_NEW_C1028_PROCESS_GRAPH_CURRENT_NATIVE_OPEN'if accepted else'TWO_CORE_OWNERS_CONTACT_COVERAGE_SCREEN_RAW_GATES_OPEN','accepted':len(accepted),'trials':len(results),'best':min(accepted,key=lambda x:x['CORE_new_length_mm'])if accepted else None,'retained_literal_original_contacts':16,'controlled_original_duplicate_pair_contact':'new paired owned routes must be coincident; original duplicate is an authorized changed body','process_gate':'one new exact C1028.1 VIPPO location required, not registered; ordinary CDONE SG retained','current_thermal_PDN_SI_all_old_graph_native_SOURCE_and_masks':'OPEN','native_jobs':0,'adopted':False,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'input_SHA256':{str(p.resolve()):sha(p)for p in(rp,cp)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',receipt);print(json.dumps({k:receipt[k]for k in('verdict','accepted','trials','best','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
