"""Construct FIELD5 through one existing same-raw ordinary barrel.

Original IO3 filled copper stays hard on In2 to preserve the exact existing
source network. Every owned positive peer remains hard. Only a proposal is
emitted; actual normal foreign-fill/owned-ground withdrawals require replay.
"""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import set_precision
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import complete_geometry_r2 as G
import tri_route as T
import guarded_declared_settings_projection_r58 as N
from inventory import sha
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
O=H/'FIELD5-existing-ordinary-barrel-In3-In2-original-IO3-hard-nomination-r437'
OLD='61cb8179-7754-5031-bbea-0da464bf816f';NET='/motherboard_power_entry/FIELD_5V';FG='/motherboard_motors/FIELD_GND'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads(M.read_bytes());vm={v['uuid']:v for v in h['vias']};tm={t['uuid']:t for t in h['tracks']};src=vm['e19f5a4a-8797-4ce8-a00d-4c884cc46739'];dst=vm['0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'];raw=src['net'];assert raw==dst['net'];a=Point(src['x'],src['y']);z=Point(dst['x'],dst['y']);rec,trees=F.build({**c,'zones':[]});trials=[];accepted=None
 def free(layer,core,win):
  query=win.buffer(2);hard=[]
  for j in trees[layer].query(query,predicate='intersects'):
   r=rec[layer][int(j)]
   if L.norm(r['net'])==NET:continue
   gap=core/2+G.gap(h,raw,r['net'])+.025+.0001
   if r['kind']=='via':v=vm[r['uuid']];hard.append(N.bounded_disk(v,max(gap+v['d']/2,core/2+v['drill']/2+.275)))
   elif r['kind']=='track'and not tm[r['uuid']].get('m'):t=tm[r['uuid']];hard.append(N.bounded_buffer(LineString([t['a'],t['b']]),gap+t['w']/2))
   else:hard.append(N.bounded_buffer(r['shape'],gap))
  for qq in q:
   if qq['uuid']==OLD or qq['layer']!=layer or L.norm(qq['net'])in(NET,FG):continue
   if qq['shape'].intersects(query):hard.append(N.bounded_buffer(qq['shape'],core/2+max(qq.get('clearance_mm',.15),G.gap(h,raw,qq['net']))+.025+.0001))
  for qq in c['zones']:
   if layer!='In2.Cu'or L.norm(qq['net'])!='/IO_3V3'or layer not in qq['fills']:continue
   actual=unary_union(L.poly(qq['fills'][layer])).intersection(query)
   if not actual.is_empty:hard.append(N.bounded_buffer(actual,core/2+max(qq.get('clearance_mm',.15),G.gap(h,raw,qq['net']))+.025+.0001))
  for pad in h['pads']:
   if L.norm(pad['net'])==NET:continue
   for sh in L.poly(pad.get('hole')or[]):
    if sh.intersects(query):hard.append(N.bounded_buffer(sh,core/2+.275+.0001))
  for ar in h['rule_areas']:
   if ar.get('no_zones')and layer in ar['layers']:
    for sh in L.poly(ar['outline']):
     if sh.intersects(query):hard.append(N.bounded_buffer(sh,core/2+.025+.0001))
  return win.difference(unary_union(hard))
 for core in (.50,.35):
  for extra in (20,40):
   win=box(min(a.x,z.x)-extra,min(a.y,z.y)-extra,max(a.x,z.x)+extra,max(a.y,z.y)+extra);fs={ly:polys(free(ly,core,win))for ly in ('In3.Cu','In2.Cu')};row={'core_mm':core,'window_extra_mm':extra,'source_faces':{},'target_faces':{},'existing_middle_candidates':[]};trials.append(row)
   for sl,tl in (('In3.Cu','In2.Cu'),('In2.Cu','In3.Cu')):
    if sl not in src['flashed']or tl not in dst['flashed']:continue
    ss=[ff for ff in fs[sl]if ff.covers(a)];tt=[ff for ff in fs[tl]if ff.covers(z)];row['source_faces'][sl]=len(ss);row['target_faces'][tl]=len(tt)
    for mid in sorted((v for v in h['vias']if v['net']==raw and sl in v['flashed']and tl in v['flashed']and win.covers(Point(v['x'],v['y']))),key=lambda v:a.distance(Point(v['x'],v['y']))+z.distance(Point(v['x'],v['y']))):
     pp=Point(mid['x'],mid['y']);pairs=[(sf,tf)for sf in ss for tf in tt if sf.covers(pp)and tf.covers(pp)]
     row['existing_middle_candidates'].append({'UUID':mid['uuid'],'at_mm':[mid['x'],mid['y']],'source_layer':sl,'target_layer':tl,'shared_endpoint_face_pairs':len(pairs),'host_actual_layers':mid['flashed']});put(O/'checkpoint.json',trials)
     for sf,tf in pairs:
      try:
       sp,_=T.route(sf,(a.x,a.y),(pp.x,pp.y));tp,_=T.route(tf,(pp.x,pp.y),(z.x,z.y));sp=[[round(x,6),round(y,6)]for x,y in sp];tp=[[round(x,6),round(y,6)]for x,y in tp];assert sf.covers(LineString(sp))and tf.covers(LineString(tp));planes=[]
       for ly,path in ((sl,sp),(tl,tp)):
        axis=LineString(path);outline=set_precision(N.bounded_buffer(axis,core/2),1e-6,mode='valid_output');physical=outline
        for v in h['vias']:
         hole=N.bounded_disk(v,v['drill']/2)
         if physical.intersects(hole):physical=physical.difference(hole)
        physical=set_precision(physical,1e-6,mode='valid_output');planes.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/FIELD5/R437/'+mid['uuid']+'/'+ly)),'net':raw,'layer':ly,'shape':physical,'zone_outline_shape':outline,'clearance_mm':.15,'priority':124,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'label':'FIELD5-existing-barrel-IO3-preserving-R437'})
       accepted={'planes':planes,'tracks':[],'vias':[],'removed':[],'source_barrel':src,'target_barrel':dst,'middle_barrel':mid,'routes':[{'layer':sl,'path_mm':sp,'length_mm':LineString(sp).length},{'layer':tl,'path_mm':tp,'length_mm':LineString(tp).length}],'core_mm':core};break
      except(ValueError,AssertionError)as e:row.setdefault('route_errors',[]).append(str(e))
     if accepted:break
    if accepted:break
   print('R437 core',core,'extra',extra,'accepted',bool(accepted),flush=True)
   if accepted:break
  if accepted:break
 if accepted:(O/'only-two-plane-existing-barrel-nominee.pkl').write_bytes(pickle.dumps(accepted,protocol=5))
 put(O/'receipt.json',{'verdict':'TWO_LAYER_EXISTING_BARREL_FIELD5_NOMINATION_ALL_GATES_OPEN'if accepted else'NO_TWO_LAYER_EXISTING_BARREL_NOMINEE_IN_DECLARED_WINDOWS','parent_sha256':sha(M),'original_IO3_In2_actualfilled_preserved_as_hard':True,'all_discrete_and_new_owned_positive_hard':True,'new_holes_discrete_deletes':0,'trials':trials,'middle_UUID':accepted['middle_barrel']['uuid']if accepted else None,'packet_sha256':sha(O/'only-two-plane-existing-barrel-nominee.pkl')if accepted else None,'normal_immutable_original_fill_and_owned_FAG_withdrawals':'NOT_APPLIED_FRESH_EXACT_REPLAY_AND_SOURCE_REFERENCE_GATES_REQUIRED','host_flash_is_not_native_annular_source_proof':True,'full_field_current_A':.341130981,'routing_current_reservation_A':.36,'current_loop_sheet_barrels_thermal_new_reference_native':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R437 receipt',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
