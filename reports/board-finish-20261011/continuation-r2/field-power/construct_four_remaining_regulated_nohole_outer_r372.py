"""Try additive ordinary outer joins on exact current source geometry."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys,uuid,time
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import nearest_points,unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import tri_route as T
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as N
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
O=H/'remaining-four-regulated-additive-nohole-outer-constructor-r372'
B=H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364'
C=H/'all-five-regulated-actual-drilled-literal-source-census-r370'
TARGETS=[('/motherboard_power_entry/FIELD_5V','L11003','2','U9004','10','F.Cu'),('/motherboard_do/DOA_FIELD_3V3','U11017','1','U10009','4','B.Cu'),('/motherboard_do/DOA_FIELD_3V3','U11017','1','R14065','1','B.Cu'),('DOB_DO_FIELD_3V3','U11038','1','U10022','4','B.Cu')]
def polys(s):return [p for p in ([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if p.geom_type=='Polygon'and not p.is_empty]
def write(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(B/'model.pkl')=='a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad';g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());groups=pickle.loads((C/'all-five-actual-drilled-regulated-groups.pkl').read_bytes());rec,trees=F.build(c);tm={r['uuid']:r for r in h['tracks']};vm={r['uuid']:r for r in h['vias']};new=[];rows=[]
 for net,ref,sp,target,pin,layer in TARGETS:
  pad=next(p for p in h['pads']if(p['ref'],str(p['num']))==(target,pin));anchor=Point(pad['x'],pad['y']);ps=unary_union(L.poly(pad['layers'][layer]));root=K.root(groups[net],ref,sp);source=unary_union([r['shape']for r in root if r['layer']==layer]);result=None;trials=[]
  for radius in (4,8,16):
   win=box(anchor.x-radius,anchor.y-radius,anchor.x+radius,anchor.y+radius);query=win.buffer(1.5);obs=[]
   for j in trees[layer].query(query,predicate='intersects'):
    r=rec[layer][int(j)]
    if L.norm(r['net'])==net:continue
    native=max(r.get('clearance_mm',.15)if r['kind']=='fill'else 0,G.gap(h,pad['net'],r['net']));distance=.1+native+.025+.000020
    if r['kind']=='track'and not tm[r['uuid']].get('m'):q=tm[r['uuid']];obs.append(N.bounded_buffer(LineString([q['a'],q['b']]),distance+q['w']/2))
    elif r['kind']=='via':q=vm[r['uuid']];obs.append(N.bounded_disk(q,distance+q['d']/2))
    else:obs.append(N.bounded_buffer(r['shape'],distance))
   for a in h['rule_areas']:
    if a.get('no_tracks')and layer in a['layers']:
     for sh in L.poly(a['outline']):
      if sh.intersects(query):obs.append(N.bounded_buffer(sh,.125+.000020))
   for t in new:
    if t['layer']==layer and L.norm(t['net'])!=net:obs.append(N.bounded_buffer(LineString([t['a'],t['b']]),.1+t['w']/2+G.gap(h,pad['net'],t['net'])+.025+.000020))
   free=win.difference(unary_union(obs));faces=[f for f in polys(free)if f.intersects(ps.buffer(-.00001))];options=[]
   for face in faces:
    targetbody=face.intersection(ps.buffer(-.00001));goal=face.intersection(source.buffer(-.00001))
    if targetbody.is_empty or goal.is_empty:continue
    start=nearest_points(anchor,targetbody)[1];end=nearest_points(start,goal)[1];options.append((start.distance(end),face,start,end))
   trial={'target':target+'.'+pin,'window_radius_mm':radius,'actual_target_centre_faces':len(faces),'same_actual_source_faces':len(options)};trials.append(trial);write(O/'checkpoint.json',rows+[{'target':target+'.'+pin,'trials':trials}]);print('R372',target+'.'+pin,radius,'faces',len(faces),'source_faces',len(options),flush=True)
   for length,face,start,end in sorted(options,key=lambda q:q[0]):
    try:
     path,_=T.route(face,tuple(start.coords[0]),tuple(end.coords[0]));path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path)
     assert face.covers(axis);assert ps.intersects(N.bounded_buffer(axis,.1))and source.intersects(N.bounded_buffer(axis,.1));result={'path_mm':path,'length_mm':axis.length,'width_mm':.20,'layer':layer,'literal_source_overlap_mm2':N.bounded_buffer(axis,.1).intersection(source).area,'literal_target_overlap_mm2':N.bounded_buffer(axis,.1).intersection(ps).area};break
    except (ValueError,AssertionError)as e:trial.setdefault('route_failures',[]).append(str(e))
   if result:break
  if result:
   namespace='controller-four-regulated-nohole-R372/'+target+'.'+pin
   for i,(a,bb)in enumerate(zip(result['path_mm'],result['path_mm'][1:])):new.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,namespace+'/'+str(i))),'net':pad['net'],'layer':layer,'w':.20,'a':a,'b':bb,'prospective_not_native':True})
  rows.append({'target':target+'.'+pin,'native_pad_UUID':pad['uuid'],'raw_net':pad['net'],'trials':trials,'accepted_constructor_nominee':result,'actual_source_reference_full_contact_current_native':'OPEN'});write(O/'checkpoint.json',rows)
 (O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'tracks':new,'vias':[],'removed':[]},protocol=5));rec={'verdict':'ADDITIVE_OUTER_NOMINATIONS_ONLY_FULL_CURRENT_REPLAY_AND_PROOF_OPEN','parent_model_sha256':sha(B/'model.pkl'),'rows':rows,'new_segments':len(new),'new_vias':0,'old_deletes':0,'old_or_new_zone_rule_or_source_changes':0,'source_census_receipt_sha256':sha(C/'receipt.json'),'proposed_discrete_sha256':sha(O/'proposed-discrete.pkl'),'no_source_reference_or_capacity_credit_from_nomination':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};write(O/'receipt.json',rec);print('R372_COMPLETE',sha(O/'receipt.json'),len(new),flush=True)
if __name__=='__main__':main()
