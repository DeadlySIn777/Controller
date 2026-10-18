"""Exact legal full-reference face; no old monitor trace withdrawal."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_declared_settings_projection_r58 as P
import complete_geometry_r2 as G
R=H/'U11025-health-shutdown-monitor-aperture-preserved-r328';B=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';O=H/'U11025-shutdown-true-monitor-and-reference-reroute-r332';FG='/motherboard_motors/FIELD_GND';NET='/motherboard_power_entry/FA_SHDN_CONTACT'
def main():
 assert not O.exists();O.mkdir();g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());failedids={t['uuid'] for t in d['tracks'] if t['net']==NET};h['tracks']=[t for t in h['tracks'] if t['uuid'] not in failedids];c['tracks']=[t for t in c['tracks'] if t['uuid'] not in failedids];rec,trees=F.build({**h,'zones':[]});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};root=next(xs for xs in pickle.loads((B/'groups.pkl').read_bytes())[FG] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));ref=unary_union([q['shape'] for q in root if q['layer']=='In1.Cu' and q['kind']=='fill']);start=(308.85,151.25);end=(310.05,150.95);win=box(306.5,147.0,312.0,152.0);obstacles=[];maskrows=[]
 for i in trees['F.Cu'].query(win.buffer(1.),predicate='intersects'):
  item=rec['F.Cu'][int(i)]
  if item['net']==NET:continue
  req=G.gap(h,NET,item['net'])+.025+.000020;distance=req+.1;sh=P.bounded_buffer(item['shape'],distance)
  if item['kind']=='track':t=tm[item['uuid']];sh=P.bounded_buffer(LineString([t['a'],t['b']]),distance+t['w']/2)
  elif item['kind']=='via':v=vm[item['uuid']];sh=P.bounded_disk(v,distance+v['d']/2)
  obstacles.append(sh);maskrows.append({'foreign_UUID':item['uuid'],'kind':item['kind'],'raw_net':item['net'],'required_gap_and_constructor_reserve_mm':req})
 for a in h['rule_areas']:
  if a.get('no_tracks') and 'F.Cu' in a['layers']:
   for sh in C.poly(a['outline']):
    if sh.intersects(win):obstacles.append(P.bounded_buffer(sh,.125+.000020))
 for q in z:
  if q['layer']=='F.Cu' and q['net']!=NET and q['shape'].intersects(win):obstacles.append(P.bounded_buffer(q['shape'],max(G.gap(h,NET,q['net']),q.get('clearance_mm',.15))+.025+.1+.000020))
 free=win.intersection(set_precision(ref,0).buffer(-.100020,quad_segs=256)).difference(unary_union(obstacles));(O/'exact-centre-free-face.wkb').write_bytes(free.wkb);parts=[free] if free.geom_type=='Polygon' else list(free.geoms);faces=[s for s in parts if s.geom_type=='Polygon' and s.covers(Point(start)) and s.covers(Point(end))];path=None;error=None
 if faces:
  face=max(faces,key=lambda s:s.area)
  try:path,_=T.route(face,start,end);path=[[round(x,6),round(y,6)] for x,y in path];assert face.covers(LineString(path))
  except (ValueError,AssertionError) as e:error=str(e)
 tracks=[]
 if path:
  for i,(a,bb) in enumerate(zip(path,path[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U11025-r332-shdn-'+str(i))),'net':NET,'a':a,'b':bb,'w':.2,'layer':'F.Cu','locked':False})
  h['tracks']+=tracks;c['tracks']+=tracks
 (O/'proposed-shutdown-only-tracks.pkl').write_bytes(pickle.dumps(tracks,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));out={'verdict':'EXACT_SHUTDOWN_RETAINED_MONITOR_SOURCE_REFERENCE_FACE_PATH_NOMINATION' if path else 'EXACT_SHUTDOWN_RETAINED_MONITOR_NO_FULL_REFERENCE_FACE_PATH','parent_R328_model_SHA256':sha(R/'model.pkl'),'same_face_count':len(faces),'free_area_mm2':free.area,'route_mm':path,'route_error':error,'new_shutdown_tracks':len(tracks),'mask_rows':maskrows,'model_SHA256':sha(O/'model.pkl'),'tracks_SHA256':sha(O/'proposed-shutdown-only-tracks.pkl'),'all_other_original_monitor_health_ground_Cu_retained':True,'full_actual_source_contact_analytic_native_current':'OPEN','native_jobs':0,'board_written':False,'adopted':False};(O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'faces':len(faces),'new_tracks':len(tracks),'error':error}),flush=True)
if __name__=='__main__':main()
