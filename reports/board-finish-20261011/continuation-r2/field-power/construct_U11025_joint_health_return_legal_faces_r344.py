"""Find a real ordinary barrel and restore every explicitly owned health edge.

Withdrawing the bounded old wall is only a constructor step. A candidate is
emitted solely when both the new ground path and complete health detour exist.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_declared_settings_projection_r58 as P
import complete_geometry_r2 as G
B=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';O=H/'U11025-joint-health-return-legal-face-construction-r344';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];FG='/motherboard_motors/FIELD_GND';CUTTABLE={'c6e94ae3-51b4-5df8-b6ed-c6508267dfee'}
DELETE={'8325bd7c-2971-40a7-88e4-4d24b2404b71','d26a6078-f4a0-44b8-9138-ddf692940b64','e70df82a-5f2d-4af2-9dc0-0c2045253f14','73485ae6-bd09-4e06-b6dc-618c037f55c1','e4373f43-4bf8-4252-afdf-b11a56a2c998','ae1f7ba5-1068-4183-b487-c3dba73482b0','e3944b89-76a2-41d2-b5bf-3a0feec1b288','6b8c17ea-bd34-40f4-8e00-7fdd201ac1f3','b45815b7-39e2-4242-8d07-24ca4e0db339','3a5cb040-1645-404a-982f-e4f68b186ad7','9e67fe4b-ea58-4172-a8aa-1b951513d5f7'}
def polys(sh):return [q for q in ([sh] if sh.geom_type=='Polygon' else getattr(sh,'geoms',[])) if q.geom_type=='Polygon' and not q.is_empty]
def main():
 assert not O.exists();O.mkdir();g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());pad=next(q for q in h['pads'] if(q['ref'],q['num'])==('U11025','2'));health=next(q['net'] for q in h['pads'] if(q['ref'],q['num'])==('U11025','4'));removed=[t for t in h['tracks'] if t['uuid'] in DELETE];assert len(removed)==11 and all(t['net']==health and t['w']==.2 and t['layer']=='F.Cu' for t in removed);hc=copy.deepcopy(h);hc['tracks']=[t for t in h['tracks'] if t['uuid'] not in DELETE];rec,trees=F.build({**hc,'zones':[]});tm={t['uuid']:t for t in hc['tracks']};vm={v['uuid']:v for v in hc['vias']};root=next(xs for xs in pickle.loads((B/'groups.pkl').read_bytes())[FG] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));sources={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS};reference=unary_union([q['shape'] for q in root if q['layer']=='In1.Cu' and q['kind']=='fill']);win=box(307.5,151.0,319.0,163.0);query=win.buffer(1.5);viaobs=[];holes=[s for q in h['pads'] for s in C.poly(q.get('hole') or [])];smd=[s for q in h['pads'] if q['smd'] for rs in q['layers'].values() for s in C.poly(rs)];peers=pickle.loads((H/'REG7-native-support-minimal-current-delta-r312/new-REG7-zones.pkl').read_bytes())
 for l in LAYERS:
  for i in trees[l].query(query,predicate='intersects'):
   q=rec[l][int(i)]
   if q['net']==pad['net']:continue
   req=G.gap(h,pad['net'],q['net'])+.025+.000020;radius=.25+req;sh=P.bounded_buffer(q['shape'],radius)
   if q['kind']=='track':t=tm[q['uuid']];sh=P.bounded_buffer(LineString([t['a'],t['b']]),radius+t['w']/2)
   elif q['kind']=='via':v=vm[q['uuid']];sh=P.bounded_disk(v,radius+v['d']/2)
   viaobs.append(sh)
  for q in z+peers:
   if q['layer']==l and q['net']!=pad['net'] and q['uuid'] not in CUTTABLE and q['shape'].intersects(query):viaobs.append(P.bounded_buffer(q['shape'],.25+max(G.gap(h,pad['net'],q['net']),q.get('clearance_mm',.15))+.025+.000020))
 for sh in holes+smd:
  if sh.intersects(query):viaobs.append(P.bounded_buffer(sh,.375+.000020))
 for v in h['vias']:
  if query.intersects(Point(v['x'],v['y'])):viaobs.append(P.bounded_disk(v,.1+v['drill']/2+.275+.000020))
 for a in h['rule_areas']:
  if a.get('no_vias'):
   for sh in C.poly(a['outline']):
    if sh.intersects(query):viaobs.append(P.bounded_buffer(sh,.25+.025+.000020))
 landing=win.difference(unary_union(viaobs));(O/'exact-all6-normal-antipad-landing-centres.wkb').write_bytes(landing.wkb)
 def free(net,extra=[]):
  obs=[]
  for i in trees['F.Cu'].query(query,predicate='intersects'):
   q=rec['F.Cu'][int(i)]
   if q['net']==net:continue
   req=G.gap(h,net,q['net'])+.025+.000020;dist=.1+req;sh=P.bounded_buffer(q['shape'],dist)
   if q['kind']=='track':t=tm[q['uuid']];sh=P.bounded_buffer(LineString([t['a'],t['b']]),dist+t['w']/2)
   elif q['kind']=='via':v=vm[q['uuid']];sh=P.bounded_disk(v,dist+v['d']/2)
   obs.append(sh)
  for q in z+peers:
   if q['layer']=='F.Cu' and q['net']!=net and q['shape'].intersects(query):obs.append(P.bounded_buffer(q['shape'],.1+max(G.gap(h,net,q['net']),q.get('clearance_mm',.15))+.025+.000020))
  for a in h['rule_areas']:
   if a.get('no_tracks') and 'F.Cu' in a['layers']:
    for sh in C.poly(a['outline']):
     if sh.intersects(query):obs.append(P.bounded_buffer(sh,.125+.000020))
  return win.intersection(reference.buffer(-.100020,quad_segs=256)).difference(unary_union(obs+extra))
 groundfree=free(pad['net']);(O/'exact-ground-centre-free.wkb').write_bytes(groundfree.wkb);ps=unary_union(C.poly(pad['layers']['F.Cu']));faces=[s for s in polys(groundfree) if s.intersects(ps.buffer(-.000020))];options=[]
 for face in faces:
  for inner in ('In1.Cu','In4.Cu'):
   for piece in polys(landing.intersection(face).intersection(P.bounded_buffer(sources[inner],.15))):
    for pt in (nearest_points(piece,Point(pad['x'],pad['y']))[0],piece.representative_point(),piece.centroid):
     if piece.covers(pt):options.append((pt.distance(Point(pad['x'],pad['y'])),inner,pt,face))
 print('R344 landing',landing.area,'ground faces',len(faces),'options',len(options),flush=True);checkpoint=[];chosen=None
 for _,inner,point,face in sorted(options,key=lambda x:x[:2])[:24]:
  point=Point(round(point.x,6),round(point.y,6))
  if not landing.covers(point) or not face.covers(point):continue
  start=nearest_points(face.intersection(ps.buffer(-.000020)),Point(pad['x'],pad['y']))[0]
  try:gp,_=T.route(face,tuple(start.coords[0]),tuple(point.coords[0]));gp=[[round(x,6),round(y,6)] for x,y in gp];assert face.covers(LineString(gp))
  except (ValueError,AssertionError) as e:checkpoint.append({'site_mm':list(point.coords[0]),'ground_error':str(e)});continue
  extra=[P.bounded_buffer(LineString(gp),.375+.000020),P.bounded_disk({'x':point.x,'y':point.y},.525+.000020)];healthfree=free(health,extra);ends=[(311.5315,153.408),(308.5315,157.308)];hs=[s for s in polys(healthfree) if all(s.covers(Point(pt)) for pt in ends)];row={'site_mm':list(point.coords[0]),'source_layer':inner,'health_same_faces':len(hs)}
  if hs:
   try:hp,_=T.route(max(hs,key=lambda s:s.area),*ends);hp=[[round(x,6),round(y,6)] for x,y in hp];assert max(hs,key=lambda s:s.area).covers(LineString(hp));chosen=(point,inner,gp,hp);checkpoint.append(row);break
   except (ValueError,AssertionError) as e:row['health_route_error']=str(e)
  checkpoint.append(row);(O/'routing-checkpoint.json').write_text(json.dumps(checkpoint,indent=1)+'\n',encoding='utf-8')
 new={'vias':[],'tracks':[]}
 if chosen:
  pt,inner,gp,hp=chosen;vid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U11025-r344/'+repr(tuple(pt.coords[0]))));new['vias']=[{'uuid':vid,'net':pad['net'],'x':pt.x,'y':pt.y,'d':.5,'drill':.2,'span':LAYERS,'flashed':LAYERS,'prospective_not_native':True}]
  for role,net,path in [('ground',pad['net'],gp),('health',health,hp)]:
   for i,(a,bb) in enumerate(zip(path,path[1:])):new['tracks'].append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,vid+'/'+role+'/'+str(i))),'net':net,'a':a,'b':bb,'w':.2,'layer':'F.Cu','prospective_not_native':True})
  hc['tracks']+=new['tracks'];hc['vias']+=new['vias'];current={**c,'tracks':[t for t in c['tracks'] if t['uuid'] not in DELETE]+new['tracks'],'vias':c['vias']+new['vias']};(O/'model.pkl').write_bytes(pickle.dumps((g,hc,b,z,current),protocol=5))
 (O/'proposed-discrete.pkl').write_bytes(pickle.dumps(new,protocol=5));(O/'exact-owned-old-track-rows.json').write_text(json.dumps(removed,indent=1)+'\n',encoding='utf-8');out={'verdict':'COMPLETE_GROUND_PLUS_HEALTH_RESTORATION_CONCRETE_FACE_NOMINATION' if chosen else 'NO_COMPLETE_HEALTH_AND_GROUND_FACE_PAIR_NO_CANDIDATE_EMITTED','parent_ROOT112_model_SHA256':sha(B/'model.pkl'),'deleted_original_health_UUIDs':sorted(DELETE),'new_vias':len(new['vias']),'new_tracks':len(new['tracks']),'checkpoint':checkpoint,'landing_area_mm2':landing.area,'candidate_options':len(options),'new_discrete_SHA256':sha(O/'proposed-discrete.pkl'),'model_SHA256':sha(O/'model.pkl') if chosen else None,'only_new_owned_supply_antipad_permission_scope':list(CUTTABLE),'no_withdrawn_wall_credited_without_complete_health_restoration':True,'no_shutdown_monitor_other_original_copper_change':True,'all_actual_fill_source_contact_reference_true_copper_current_native':'OPEN','native_jobs':0,'board_written':False,'adopted':False};(O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'via':len(new['vias']),'tracks':len(new['tracks'])}),flush=True)
if __name__=='__main__':main()
