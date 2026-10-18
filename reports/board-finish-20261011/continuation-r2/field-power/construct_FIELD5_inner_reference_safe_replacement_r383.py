"""Construct an inner-layer replacement for the rejected In4 FIELD5 feed.

Only current same-domain FIELD_GND plane bodies are eligible for an explicit
later cut. Every discrete native item and all other current filled planes
remain hard. This emits a nomination, not current or source qualification.
"""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,uuid,time
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
O=H/'FIELD5-inner-source-barrel-reference-safe-replacement-nomination-r383'
UID='61cb8179-7754-5031-bbea-0da464bf816f';NET='/motherboard_power_entry/FIELD_5V';FG='/motherboard_motors/FIELD_GND'
def write(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();g,h,b,q,c=pickle.loads(M.read_bytes());raw=next(z['net']for z in q if z['uuid']==UID);vmap={v['uuid']:v for v in h['vias']};source=vmap['e19f5a4a-8797-4ce8-a00d-4c884cc46739'];target=vmap['0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'];assert source['net']==target['net']==raw
 a=Point(source['x'],source['y']);bb=Point(target['x'],target['y']);tm={t['uuid']:t for t in h['tracks']};rec,trees=F.build({**c,'zones':[]});trials=[];accepted=None
 for layer in ('In2.Cu','In3.Cu'):
  assert layer in source['flashed']and layer in target['flashed']
  for core in (1.0,.75,.5):
   for extra in (4,10,20):
    win=box(min(a.x,bb.x)-extra,min(a.y,bb.y)-extra,max(a.x,bb.x)+extra,max(a.y,bb.y)+extra);query=win.buffer(2);hard=[];soft=[]
    for j in trees[layer].query(query,predicate='intersects'):
     r=rec[layer][int(j)]
     if L.norm(r['net'])==NET:continue
     d=core/2+G.gap(h,raw,r['net'])+.025+.0001
     if r['kind']=='via':v=vmap[r['uuid']];hard.append(N.bounded_disk(v,max(d+v['d']/2,core/2+v['drill']/2+.275)))
     elif r['kind']=='track'and not tm[r['uuid']].get('m'):t=tm[r['uuid']];hard.append(N.bounded_buffer(LineString([t['a'],t['b']]),d+t['w']/2))
     else:hard.append(N.bounded_buffer(r['shape'],d))
    for z in c['zones']:
     if z['uuid']==UID or layer not in z['fills']or L.norm(z['net'])==NET:continue
     sh=unary_union(L.poly(z['fills'][layer])).intersection(query)
     if sh.is_empty:continue
     if L.norm(z['net'])==FG:soft.append({'UUID':z['uuid'],'kind':'ACTUAL_SAME_DOMAIN_GROUND_FILLED_ROLE','shape':sh});continue
     hard.append(N.bounded_buffer(sh,core/2+max(z.get('clearance_mm',.15),G.gap(h,raw,z['net']))+.025+.0001))
    for z in q:
     if z['uuid']==UID or z['layer']!=layer or L.norm(z['net'])==NET:continue
     if L.norm(z['net'])==FG:soft.append({'UUID':z['uuid'],'kind':'OWNED_SAME_DOMAIN_GROUND_PROPOSAL','shape':z['shape']});continue
     if z['shape'].intersects(query):hard.append(N.bounded_buffer(z['shape'],core/2+max(z.get('clearance_mm',.15),G.gap(h,raw,z['net']))+.025+.0001))
    for p in h['pads']:
     if L.norm(p['net'])==NET:continue
     for sh in L.poly(p.get('hole')or[]):
      if sh.intersects(query):hard.append(N.bounded_buffer(sh,core/2+.275+.0001))
    for area in h['rule_areas']:
     if area.get('no_zones')and layer in area['layers']:
      for sh in L.poly(area['outline']):
       if sh.intersects(query):hard.append(N.bounded_buffer(sh,core/2+.025+.0001))
    free=win.difference(unary_union(hard));faces=[p for p in polys(free)if p.covers(a)and p.covers(bb)];trial={'layer':layer,'core_mm':core,'outer_window_extra_mm':extra,'same_centre_face_count':len(faces),'source_centre_in_free':free.covers(a),'target_centre_in_free':free.covers(bb)};trials.append(trial);write(O/'checkpoint.json',trials);print('R383',layer,core,extra,len(faces),flush=True)
    for face in sorted(faces,key=lambda s:s.area):
     try:
      path,_=T.route(face,(a.x,a.y),(bb.x,bb.y));path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path);assert face.covers(axis)
      outline=set_precision(N.bounded_buffer(axis,core/2),1e-6,mode='pointwise');physical=outline
      for v in h['vias']:
       disk=N.bounded_disk(v,v['drill']/2)
       if physical.intersects(disk):physical=physical.difference(disk)
      physical=set_precision(physical,1e-6,mode='pointwise');assert outline.covers(a)and outline.covers(bb)
      uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/FIELD5/R383/'+layer));new={'uuid':uid,'net':raw,'layer':layer,'clearance_mm':.15,'priority':124,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'shape':physical,'zone_outline_shape':outline,'label':'FIELD5-In4-reference-replacement-R383','physical_Cu_drill_subtracted':True}
      affected=[{'UUID':s['UUID'],'kind':s['kind'],'exact_prospective_guard_overlap_mm2':s['shape'].intersection(N.bounded_buffer(physical,.1751)).area}for s in soft if s['shape'].intersects(N.bounded_buffer(physical,.1751))]
      accepted={'layer':layer,'core_mm':core,'path_mm':path,'length_mm':axis.length,'new_UUID':uid,'source_existing_barrel_UUID':source['uuid'],'target_existing_barrel_UUID':target['uuid'],'same_domain_ground_cut_obligations':affected};(O/'one-new-field5-replacement-plane.pkl').write_bytes(pickle.dumps([new],protocol=5));break
     except (ValueError,AssertionError)as e:trial.setdefault('route_failures',[]).append(str(e));write(O/'checkpoint.json',trials)
    if accepted:break
   if accepted:break
  if accepted:break
 result={'verdict':'INNER_FIELD5_EXISTING_BARREL_REPLACEMENT_CONSTRUCTOR_NOMINATION_FULL_CURRENT_SOURCE_REFS_OPEN'if accepted else'INNER_FIELD5_FIXED_DISCRETE_AND_FOREIGN_PLANE_CONSTRUCTOR_NO_PATH','parent_model_sha256':sha(M),'withdraw_only_failed_NEW_In4_UUID_after_fresh_replay':UID,'accepted_nomination':accepted,'trials':trials,'native_original_Cu_outline_rules_source_changed':False,'same_domain_ground_cuts_not_applied':True,'full_current_contact_ref_native_and_two_actual_annuli':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start}
 if accepted:result['new_plane_packet_sha256']=sha(O/'one-new-field5-replacement-plane.pkl')
 write(O/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'accepted':accepted}),flush=True)
if __name__=='__main__':main()
