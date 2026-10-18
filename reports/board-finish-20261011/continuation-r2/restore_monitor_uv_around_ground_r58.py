"""Restore the exact temporary UV wall around a real source-rooted ground fanout."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
import tri_route as T
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return []
 if s.geom_type=='Polygon':return [s]
 return [q for p in getattr(s,'geoms',[])for q in parts(p)]
def main():
 parent=H/'field-monitor-ground-counterfactual-r51';mp=parent/'source-only-model.pkl';r=json.loads((parent/'receipt.json').read_bytes());assert sha(mp)==r['model_sha256']=='47c92360cc223dfc746560f0f8b484a5e95a3e6f6c9806fd41f179a85a3d6cc9'
 out=H/'field-monitor-UV-ground-coupled-restoration-r58';assert not out.exists();out.mkdir();g,h,b,z,current=pickle.loads(mp.read_bytes())
 old=json.loads((parent/'exact-owned-monitor-wall-reroute.json').read_bytes())['old_track'];assert old['uuid']=='b7ddd466-0bed-4b5a-968d-9ef0ce166364'and not any(t['uuid']==old['uuid']for t in h['tracks'])and old['w']==.2 and old['layer']=='F.Cu'
 net=old['net'];domain=h['domains_normalized'][C.norm(net)];peer=H/'field-power/regulated-four-retained-hard-snapshot-r127';pd=pickle.loads((peer/'proposed-discrete.pkl').read_bytes());pq=pickle.loads((peer/'proposed-zones.pkl').read_bytes());mh={**h,'tracks':h['tracks']+pd['tracks'],'vias':h['vias']+pd['vias']};records,trees=F.build({**mh,'zones':[]})
 I.p.WINDOW=box(.526,.526,449.474,234.474);hard=I.p.hard_shapes(mh,I.L.live.reservations(),C.norm(net),'F.Cu')
 fg=next(xs for xs in F.graph(current,'/motherboard_motors/FIELD_GND')if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));refs={l:unary_union([q['shape']for q in fg if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')}
 holes=[s for p in mh['pads']for s in C.poly(p.get('hole')or [])]+[N.bounded_disk(v,v['drill']/2)for v in mh['vias']];outline=unary_union(C.poly(h['outline'])).buffer(-.626);attempts=[];nominees=[]
 for radius in (5.,10.,20.):
  cx=(old['a'][0]+old['b'][0])/2;cy=(old['a'][1]+old['b'][1])/2;win=box(cx-radius,cy-radius,cx+radius,cy+radius);search=win.buffer(2);obs=[]
  for i in trees['F.Cu'].query(search,predicate='intersects'):
   q=records['F.Cu'][int(i)]
   if q['net']==net:continue
   n=(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6)+.025+.000020
   if q['kind']=='track':t=q['source'];obs.append(N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+.1+n))
   elif q['kind']=='via':v=q['source'];obs.append(N.bounded_disk(v,v['d']/2+.1+n))
   else:obs.append(N.bounded_buffer(q['shape'],.1+n))
  obs.extend(N.bounded_buffer(s,.1+.275+.000020)for s in holes if search.intersects(s))
  obs.extend(N.bounded_buffer(s,.1+.025+.000020)for s in hard if search.intersects(s))
  for q in z+pq:
   if q['net']==net or q['layer']!='F.Cu'or not search.intersects(q['shape']):continue
   n=max(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6,float(q.get('clearance_mm',.15)))+.025+.000020;obs.append(N.bounded_buffer(q['shape'],.1+n))
  free=set_precision(win.intersection(outline).difference(unary_union(obs)),1e-6)
  for mode,legal in [('physical_only',free),('actual_In1_source_full_body',free.intersection(refs['In1.Cu'].buffer(-.100020))),('actual_In4_source_full_body',free.intersection(refs['In4.Cu'].buffer(-.100020)))]:
   faces=[p for p in parts(legal)if p.covers(Point(old['a']))and p.covers(Point(old['b']))];row={'radius_mm':radius,'mode':mode,'legal_area_mm2':legal.area,'source_covered':legal.covers(Point(old['a'])),'target_covered':legal.covers(Point(old['b'])),'common_faces':len(faces)}
   for face in faces:
    try:points,proof=T.route(face,old['a'],old['b'])
    except(AssertionError,ValueError)as e:row['constructor_failure']=str(e);continue
    points=[[round(x,6),round(y,6)]for x,y in points];line=LineString(points)
    if not face.covers(line):row['rounded_axis_not_covered']=True;continue
    tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-monitor-UV-ground-r58/'+repr((a,bb)))),'net':net,'a':a,'b':bb,'w':.2,'layer':'F.Cu'}for a,bb in zip(points,points[1:])];body=N.bounded_buffer(line,.1);missing={l:body.difference(refs[l]).area for l in refs}
    candidate={'mode':mode,'radius_mm':radius,'replacement_tracks':tracks,'points_mm':points,'length_mm':line.length,'strict_axis_legal_coverage':True,'actual_J3_rooted_full_new_body_reference_missing_mm2':missing,'new_full_body_reference_pass':any(v==0 for v in missing.values()),'constructor':proof};nominees.append(candidate);row['nominated_length_mm']=line.length;row['full_body_reference_pass']=candidate['new_full_body_reference_pass']
   attempts.append(row);put(out/'checkpoint.json',{'attempts':attempts,'nominees':nominees});print('R58_UV_RESTORE',radius,mode,len(faces),row.get('nominated_length_mm'),flush=True)
  if any(q['new_full_body_reference_pass']for q in nominees):break
 (out/'nominees.pkl').write_bytes(pickle.dumps(nominees,protocol=5));put(out/'receipt.json',{'verdict':'COUPLED_MONITOR_UV_RESTORATION_NOMINATION_ONLY_FULL_GATES_OPEN'if nominees else'NO_UV_RESTORATION_IN_FINITE_SAME_F_REGION','parent_sha256':sha(mp),'exact_owned_deleted_track':old,'attempts':attempts,'nominees':nominees,'temporary_R51_never_native_or_adopted':True,'native_jobs':0,'board_written':False,'adopted':False,'full_source_contact_reference_current_threshold_native_DRC':'OPEN'})
 print('R58_COMPLETE',len(nominees),'strict_new_reference_positive',sum(q['new_full_body_reference_pass']for q in nominees),flush=True)
if __name__=='__main__':main()
