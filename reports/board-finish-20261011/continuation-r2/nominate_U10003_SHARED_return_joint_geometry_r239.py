"""Rejoin field signals with the shared return and the native-attested HOST pose."""
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'U10003-shared-return-native-HOST-pose-joint-field-geometry-nomination-r239';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl';assert sha(mp)=='8bc676155f72e590cc8dd77f6315f0990d60b421f54a3c7928dc8e66ba48f91d';g,h,b,q,full=pickle.loads(mp.read_bytes())
rp=H/'U10003-R10007-shared-return-logic-side-source-reference-rigid-pose-nomination-r220/receipt.json';r=json.loads(rp.read_bytes());withdraw=set(r['only_unadopted_wall_UUIDs_withdrawn_for_joint_nomination']);assert len(withdraw)==9
shared=r['new_shared_ground_barrel'];FG=K.L.norm(shared['net']);FLT='/motherboard_do/DOA_FLT_N_FIELD';CLK='/motherboard_do/DOA_SCLK_FIELD'
restore=[t for t in g['tracks']if K.L.norm(t['net'])==CLK and t['layer']=='F.Cu'and set(map(tuple,[t['a'],t['b']]))=={(214.799999,143.711969),(216.68003,143.711969)}];assert len(restore)==1
hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in withdraw]+restore,'vias':[v for v in h['vias']if v['uuid']!=shared['uuid']]+[shared]}
sig=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');oldA=next(v for v in h['vias']if v['uuid']=='2938cbdd-1d38-4238-9455-504b30f06e5e');pad9=next(p for p in h['pads']if p['ref']=='U10003'and p['num']=='9');pad10=next(p for p in h['pads']if p['ref']=='U10003'and p['num']=='10')
records,trees=K.F.build({**hard,'zones':[]});dom=h['domains_normalized'];gap=lambda a,c:.15 if dom[K.L.norm(a)]==dom[K.L.norm(c)]else.6;areas,exempt=K.A.reservations();rows=[];added=[];routes=[]
def route(phase,net,layer,startshape,target):
 for margin in (1,3,6):
  win=box(212-margin,140-margin,220+margin,148+margin);query=win.buffer(1);cuts=[]
  for j in trees[layer].query(query,predicate='intersects'):
   z=records[layer][int(j)]
   if K.L.norm(z['net'])!=net:cuts.append(N.bounded_buffer(z['shape'].intersection(query),gap(net,z['net'])+.025+.10002))
  for t in added:
   if t['layer']==layer and K.L.norm(t['net'])!=net:cuts.append(N.bounded_buffer(LineString([t['a'],t['b']]),gap(net,t['net'])+.025+.20002))
  for z in q:
   if z['layer']==layer and K.L.norm(z['net'])!=net and z['shape'].intersects(query):cuts.append(N.bounded_buffer(z['shape'].intersection(query),max(gap(net,z['net']),float(z['clearance_mm']))+.025+.10002))
  for z in full['zones']:
   other=K.L.norm(z['net'])
   if other==net or dom[other]==dom[net]:continue
   for s in K.L.poly(z['fills'].get(layer,[])):
    if s.intersects(query):cuts.append(N.bounded_buffer(s.intersection(query),max(gap(net,other),float(z['clearance_mm']))+.025+.10002))
  for v in hard['vias']:
   if K.L.norm(v['net'])!=net and query.intersects(Point(v['x'],v['y'])):cuts.append(N.bounded_disk(v,v['drill']/2+.275+.10002))
  for p in hard['pads']:
   for s in K.L.poly(p.get('hole')or[]):
    if K.L.norm(p['net'])!=net and s.intersects(query):cuts.append(N.bounded_buffer(s,.275+.10002))
  for z in hard['rule_areas']:
   if z.get('no_tracks')and layer in z['layers']:cuts.extend(N.bounded_buffer(s,.025+.10002)for s in K.L.poly(z['outline'])if s.intersects(query))
  for z in areas['keepouts']:
   if layer in z['layers']and net not in exempt.get(z['name'],set()):cuts.extend(N.bounded_buffer(s,.025+.10002)for s in K.L.poly(z['outline'])if s.intersects(query))
  free=win.difference(unary_union(cuts));start=startshape.buffer(-.005).intersection(free);end=target.buffer(-.005).intersection(free);common=[]
  for p in K.RF.parts(free):
   aa=start.intersection(p);bb=end.intersection(p)
   if not aa.is_empty and not bb.is_empty:common.append((p,aa,bb))
  rows.append({'phase':phase,'margin_mm':margin,'common_faces':len(common),'start_area_mm2':start.area,'target_area_mm2':end.area})
  for part,aa,bb in common:
   p1,p2=nearest_points(aa,bb);ends=[(round(p.x,6),round(p.y,6))for p in(p1,p2)]
   if not all(part.covers(Point(p))for p in ends):continue
   axis=LineString(ends)
   if not part.covers(axis):
    try:xy,_=T.route(part,*ends);axis=LineString([(round(x,6),round(y,6))for x,y in xy])
    except(ValueError,AssertionError):continue
   if not part.covers(axis):continue
   xy=list(axis.coords);tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U10003-r239/'+phase+'/'+str(i))),'net':net,'layer':layer,'w':.2,'a':list(a),'b':list(bb),'prospective_not_native':True}for i,(a,bb)in enumerate(zip(xy,xy[1:]))if a!=bb];body=unary_union([K.A.shape({'kind':'segment',**t})for t in tracks])
   if not tracks or min(body.intersection(startshape).area,body.intersection(target).area)<=0:continue
   added.extend(tracks);routes.append({'phase':phase,'length_mm':axis.length,'tracks':tracks,'source_target_overlap_mm2':[body.intersection(startshape).area,body.intersection(target).area]});return True
 return False
ann=lambda v:Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))
results={}
for phase,net,layer,start,target in [('FLT_B',FLT,'B.Cu',unary_union(K.L.poly(pad10['layers']['B.Cu'])),ann(sig)),('FG_B',FG,'B.Cu',unary_union(K.L.poly(pad9['layers']['B.Cu'])),ann(shared)),('FLT_In2',FLT,'In2.Cu',ann(oldA),ann(sig))]:
 results[phase]=route(phase,net,layer,start,target);print('R239_ROUTE',phase,results[phase],flush=True)
 if not results[phase]:break
result={'verdict':'SHARED_RETURN_FIELD_JOINT_GEOMETRY_NOMINEE_ALL_REFERENCE_SOURCE_CURRENT_NATIVE_OPEN'if len(results)==3 and all(results.values())else'FINITE_SHARED_RETURN_FIELD_JOINT_GEOMETRY_INCOMPLETE','base_model_sha256':sha(mp),'exact_native_clock_track_restore':restore,'only_nine_unadopted_field_tracks_withdrawn':sorted(withdraw),'new_shared_ground_via':shared,'signal_return_distances_mm':r['both_actual_signal_return_distances_mm'],'new_tracks':added,'routes':routes,'results':results,'finite_rows':rows,'original_Cu_deletes_added':0,'two_existing_new_FG_plane_roles_require_fresh_source_bound_replacement':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');(OUT/'geometry-nominee.pkl').write_bytes(pickle.dumps(result,protocol=5));print('R239_COMPLETE',results,sha(OUT/'receipt.json'),flush=True)
