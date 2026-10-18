"""Optimize only the controlled IO3 pose and report actual upstream reference."""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-CORE-controlled-pose-optimization-and-actual-upstream-SOURCE-start-r49'
WALL={'233cfa24-bc17-4dfa-9617-321c8db03618','b1e1f4cd-cfe9-421c-8c66-6662888515d5'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):
 if s.is_empty:return []
 return [q for x in s.geoms for q in pieces(x)]if hasattr(s,'geoms')else[s]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-two-CORE-owners-literal-contact-coverage-inside-SOURCE-route-r48/receipt.json';r=json.loads(rp.read_bytes());cp=Path(r['cache_file']);assert sha(cp)==r['cache_SHA256'];last=pickle.loads(cp.read_bytes());d=last['prior'];c=d['c'];full=c['full_before'];geo=d['CORE_geometry_free'];oldbody=K.L.body(d['CORE_before'][0]);contacts=[(q,oldbody.intersection(K.L.body(q['exact_current_native_original_geometry'])))for q in d['CORE_contacts']['direct_same_net_native_F_contacts']if q['uuid']not in WALL];cover=last['contact_coverage'];A=[148.65,90.65];B=[154.65,96.65];sat=d['signal_at'];window=d['wide']['window'];source=c['source_refs']['In1.Cu'].intersection(window.buffer(2));allLG=unary_union([s for z in full['zones']if K.L.norm(z['net'])=='/LOGIC_GND'for s in K.L.poly(z['fills'].get('In1.Cu',[]))]).intersection(window.buffer(2));upstream=[]
 for label,point in(('A',A),('original_prefix',[148.9,90.9]),('B',B)):
  disk=K.Z.bounded_disk({'x':point[0],'y':point[1]},.625);upstream.append({'point':label,'at':point,'whole_CORE_body_endcap_missing_actual_SOURCE_In1':info(disk.difference(source)),'whole_CORE_body_endcap_missing_any_actual_LG_In1':info(disk.difference(allLG))})
 put('actual-full-before-upstream-source-versus-any-LG-endcap-gaps.json',upstream);print(json.dumps({'phase':'ACTUAL_UPSTREAM_SOURCE','checks':upstream}),flush=True)
 inner=d['ordinary_IO3_region'].buffer(-.005);vertices=[]
 for p in pieces(inner):
  if p.geom_type=='Polygon':vertices.extend(list(p.exterior.coords)[:-1])
 vertices.sort(key=lambda p:p[0]-p[1],reverse=True);candidates=[]
 for p in vertices:
  at=[round(x,6)for x in p]
  if inner.covers(Point(at))and all(math.dist(at,q)>.025 for q in candidates):candidates.append(at)
  if len(candidates)==4:break
 for p in pieces(inner):
  if p.geom_type=='Polygon':
   at=[round(x,6)for x in p.representative_point().coords[0]]
   if all(math.dist(at,q)>.025 for q in candidates):candidates.append(at)
 results=[];positive=[]
 for at in candidates:
  row={'IO3_at':at,'CORE_geometry_route':False,'CORE_source_gate':'OPEN','new_C1028_1_VIPPO_location':'PROSPECTIVE ONLY not registered'};cut=K.Z.bounded_disk({'x':at[0],'y':at[1]},.55).union(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.5));src=source.difference(cut);gfree=geo.difference(K.Z.bounded_disk({'x':at[0],'y':at[1]},1.10));strict=gfree.intersection(src.buffer(-.625100));found=None
  for free,label in((strict,'strict_SOURCE'),(gfree,'geometry_SOURCE_raw_open')):
   component=next((p for p in pieces(free)if p.covers(Point(A))and p.covers(Point(B))and not p.intersection(cover).is_empty),None)
   if component is None:continue
   target=component.intersection(cover).representative_point();target=list(target.coords[0])
   for delta in(.25,.10,0):
    points=[A]
    if delta:points.append([A[0]+delta,A[1]+delta])
    points.append(target)
    if delta:points.append([B[0]-delta,B[1]-delta])
    points.append(B)
    if not all(component.covers(Point(p))for p in points):continue
    route=[];proof=[]
    for a,b in zip(points,points[1:]):
     path,meta=tri_route.route(component,a,b);route.extend(path if not route else path[1:]);proof.append(meta)
    route=[[round(x,6),round(y,6)]for x,y in route];body=K.Z.bounded_buffer(LineString(route),.625);loss=[];newcontacts=[]
    for original,shape in contacts:
     missing=shape.difference(body);new=body.intersection(K.L.body(original['exact_current_native_original_geometry']));record={'UUID':original['uuid'],'literal_contact_loss':info(missing),'finite_after_contact':info(new)};newcontacts.append(record)
     if not missing.is_empty:loss.append(record)
    found={'IO3_at':at,'CORE_path':route,'route_class':label,'source_gap':info(body.difference(src)),'literal_contact_losses':loss,'retained_contact_checks':newcontacts,'CORE_geometry_route':True,'route_proof':proof,'retained_original_axis_prefix_suffix_delta_mm':delta,'CORE_length_mm':LineString(route).length,'CORE_original_length_mm':math.sqrt(72),'new_C1028_1_VIPPO_location':'PROSPECTIVE ONLY not registered'}
    if not loss:break
   if found and not found['literal_contact_losses']:break
  if found:
   row=found
   if not row['literal_contact_losses']:positive.append(row)
   print(json.dumps({'phase':'CONTROLLED_SITE','at':at,'geometry_route':True,'literal_contact_losses':len(row['literal_contact_losses']),'SOURCE_gap_empty':row['source_gap']['EMPTY'],'segments':len(row['CORE_path'])-1}),flush=True)
  else:
   row['geometry_component_endpoints']=[{'component':i,'A':p.covers(Point(A)),'B':p.covers(Point(B)),'contact_cover':not p.intersection(cover).is_empty,'geometry':info(p)}for i,p in enumerate(pieces(gfree))if p.covers(Point(A))or p.covers(Point(B))or not p.intersection(cover).is_empty]
  results.append(row)
 put('optimized-controlled-IO3-sites-and-CORE-literal-contact-route-results.json',results);cache=OUT/'optimized-only-authorized-CORE-owner-route-and-upstream-reference-screen.pkl';cache.write_bytes(pickle.dumps({'prior':d,'results':results,'geometry_contact_positive':positive,'source_start_checks':upstream},protocol=5));best=min(positive,key=lambda x:x['CORE_length_mm'])if positive else None;receipt={'verdict':'COUPLED_CORE_GEOMETRY_LITERAL_CONTACT_PACKET_NOMINEE_SOURCE_CURRENT_PROCESS_NATIVE_GATES_OPEN'if positive else'COUPLED_CORE_SITE_OPTIMIZATION_BOUNDED_NO_LITERAL_CONTACT_POSITIVE','candidate_sites':len(candidates),'geometry_literal_contact_positive':len(positive),'best':best,'actual_source_start_checks':upstream,'all_rooted_SOURCE_graphs_reference_native_current_thermal_PDN_and_one_new_VIPPO_process':'OPEN; raw reference gaps never waived','native_jobs':0,'adopted':False,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'input_SHA256':{str(p.resolve()):sha(p)for p in(rp,cp)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',receipt);print(json.dumps({k:receipt[k]for k in('verdict','candidate_sites','geometry_literal_contact_positive','best','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
