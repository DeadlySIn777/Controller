"""Replace the removed VS wall with an actual ordinary lower-bank feed.

This emits bounded coupled nominees only. All eight VS, the old lower-bank
contacts, full four .5 A outputs, signed current and final return/fill/native
checks remain mandatory; the rejected R379 withdrawal is never adopted.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,uuid,time,copy
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import complete_geometry_r2 as G
import tri_route as T
import guarded_declared_settings_projection_r58 as N
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
W=H/'U10009-exact-VS-cycle-withdrawal-VDD-join-nomination-r379'
O=H/'U10009-retained-lower-VS-ordinary-barrel-coupled-nomination-r397'
LAYERS=('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')
FG='/motherboard_motors/FIELD_GND'
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads(M.read_bytes());d=pickle.loads((W/'only-proposed-track-and-exact-original-VS-withdrawals.pkl').read_bytes());removed=set(d['removed']);protected=d['exact_original_tracks'][0]['net'];vdd=d['tracks'][0]
 virtual={**h,'tracks':[t for t in h['tracks']if t['uuid']not in removed]+[vdd]};rec,trees=F.build({**virtual,'zones':[]});tm={t['uuid']:t for t in virtual['tracks']};vm={v['uuid']:v for v in h['vias']};rawnorm=L.norm(protected);win=box(263.8,172.0,273.0,178.5);query=win.buffer(2);startpoint=Point(267.85,174.95)
 # The actual lower bank has no old barrel. A candidate must retain an
 # ordinary all-six-layer annulus and every SMD/drill/reservation guard.
 obs=[]
 for layer in LAYERS:
  for j in trees[layer].query(query,predicate='intersects'):
   r=rec[layer][int(j)]
   if L.norm(r['net'])==rawnorm:continue
   clearance=.3+G.gap(h,protected,r['net'])+.025+.0001
   if r['kind']=='via':v=vm[r['uuid']];obs.append(N.bounded_disk(v,clearance+v['d']/2))
   elif r['kind']=='track'and not tm[r['uuid']].get('m'):t=tm[r['uuid']];obs.append(N.bounded_buffer(LineString([t['a'],t['b']]),clearance+t['w']/2))
   else:obs.append(N.bounded_buffer(r['shape'],clearance))
  for plane in q:
   if plane['layer']==layer and L.norm(plane['net'])not in(rawnorm,FG)and plane['shape'].intersects(query):obs.append(N.bounded_buffer(plane['shape'],.3+max(G.gap(h,protected,plane['net']),plane.get('clearance_mm',.15))+.025+.0001))
 for pad in h['pads']:
  shapes=L.poly(pad.get('hole')or[])
  if pad['smd']:shapes += [s for layer,rs in pad['layers'].items()if layer in('F.Cu','B.Cu')for s in L.poly(rs)]
  for sh in shapes:
   if sh.intersects(query):obs.append(N.bounded_buffer(sh,.15+.275+.0001))
 for via in h['vias']:
  if query.intersects(Point(via['x'],via['y'])):obs.append(N.bounded_disk(via,max(.815,.15+via['drill']/2+.275+.0001)))
 for area in h['rule_areas']:
  if area.get('no_vias'):
   for sh in L.poly(area['outline']):
    if sh.intersects(query):obs.append(N.bounded_buffer(sh,.3251))
 landing=win.difference(unary_union(obs));(O/'all6-.6-.3-ordinary-landing-centres.wkb').write_bytes(landing.wkb)
 def discrete_free(layer,width,window,extra=[]):
  qo=window.buffer(2);masks=[]
  for j in trees[layer].query(qo,predicate='intersects'):
   r=rec[layer][int(j)]
   if L.norm(r['net'])==rawnorm:continue
   clearance=width/2+G.gap(h,protected,r['net'])+.025+.0001
   if r['kind']=='via':v=vm[r['uuid']];masks.append(N.bounded_disk(v,clearance+v['d']/2))
   elif r['kind']=='track'and not tm[r['uuid']].get('m'):t=tm[r['uuid']];masks.append(N.bounded_buffer(LineString([t['a'],t['b']]),clearance+t['w']/2))
   else:masks.append(N.bounded_buffer(r['shape'],clearance))
  for plane in q:
   if plane['layer']==layer and L.norm(plane['net'])not in(rawnorm,FG)and plane['shape'].intersects(qo):masks.append(N.bounded_buffer(plane['shape'],width/2+max(G.gap(h,protected,plane['net']),plane.get('clearance_mm',.15))+.025+.0001))
  for pad in h['pads']:
   if L.norm(pad['net'])==rawnorm:continue
   for sh in L.poly(pad.get('hole')or[]):
    if sh.intersects(qo):masks.append(N.bounded_buffer(sh,width/2+.275+.0001))
  for area in h['rule_areas']:
   if area.get('no_tracks'if layer=='B.Cu'else'no_zones')and layer in area['layers']:
    for sh in L.poly(area['outline']):
     if sh.intersects(qo):masks.append(N.bounded_buffer(sh,width/2+.025+.0001))
  return window.difference(unary_union(masks+extra))
 outer=discrete_free('B.Cu',.3,win);faces=[f for f in polys(outer)if f.covers(startpoint)];candidates=[]
 for face in faces:
  for piece in polys(face.intersection(landing).buffer(-.000002)):
   for pt in (nearest_points(piece,startpoint)[0],piece.representative_point(),piece.centroid):
    pp=Point(round(pt.x,6),round(pt.y,6))
    if piece.covers(pp)and face.covers(pp):candidates.append((pp.distance(startpoint),pp,face))
 print('R397 candidate ordinary sites',len(candidates),'landing area',landing.area,flush=True)
 actualgroups=pickle.loads((H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl').read_bytes());root=K.root(actualgroups[rawnorm],'U11004','17');rootvia={r['uuid']for r in root if r['kind']=='via'};trials=[];chosen=None
 for distance,point,face in sorted(candidates,key=lambda x:x[0])[:12]:
  try:
   bp,_=T.route(face,tuple(startpoint.coords[0]),tuple(point.coords[0]));bp=[[round(x,6),round(y,6)]for x,y in bp];assert face.covers(LineString(bp))
  except (ValueError,AssertionError)as e:trials.append({'site':list(point.coords[0]),'outer_error':str(e)});continue
  sources=sorted([vm[u]for u in rootvia],key=lambda v:point.distance(Point(v['x'],v['y'])))[:10]
  for source in sources:
   goal=Point(source['x'],source['y'])
   for layer in ('In1.Cu','In4.Cu','In2.Cu','In3.Cu'):
    if layer not in source['flashed']:continue
    iw=box(min(point.x,goal.x)-3,min(point.y,goal.y)-3,max(point.x,goal.x)+3,max(point.y,goal.y)+3)
    if max(iw.bounds[2]-iw.bounds[0],iw.bounds[3]-iw.bounds[1])>60:continue
    free=discrete_free(layer,.5,iw);innerfaces=[f for f in polys(free)if f.covers(point)and f.covers(goal)];trial={'new_site':list(point.coords[0]),'source_old_barrel':source['uuid'],'layer':layer,'same_free_faces':len(innerfaces)};trials.append(trial);put(O/'checkpoint.json',trials)
    for ff in innerfaces:
     try:ip,_=T.route(ff,tuple(point.coords[0]),tuple(goal.coords[0]));ip=[[round(x,6),round(y,6)]for x,y in ip];assert ff.covers(LineString(ip));chosen=(point,bp,source,layer,ip);break
     except (ValueError,AssertionError)as e:trial.setdefault('route_errors',[]).append(str(e))
    if chosen:break
   if chosen:break
  if chosen:break
 packet=None
 if chosen:
  point,bp,source,layer,ip=chosen;vid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/U10009/R397/lower-VS/'+repr(tuple(point.coords[0]))));via={'uuid':vid,'net':protected,'x':point.x,'y':point.y,'d':.6,'drill':.3,'span':LAYERS,'flashed':LAYERS,'prospective_not_native':True};tracks=[vdd]+[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,vid+'/outer/'+str(i))),'net':protected,'w':.3,'layer':'B.Cu','a':a,'b':bb}for i,(a,bb)in enumerate(zip(bp,bp[1:]))]
  outline=set_precision(N.bounded_buffer(LineString(ip),.25),1e-6,mode='pointwise');physical=outline
  for v in h['vias']+[via]:
   disk=N.bounded_disk(v,v['drill']/2+.00000002)
   if physical.intersects(disk):physical=physical.difference(disk)
  physical=set_precision(physical,1e-6,mode='pointwise');plane={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,vid+'/inner')),'net':protected,'layer':layer,'clearance_mm':.15,'priority':124,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'shape':physical,'zone_outline_shape':outline,'label':'U10009-lower-VS-wall-restoration'}
  packet={'tracks':tracks,'vias':[via],'removed':sorted(removed),'exact_original_tracks':d['exact_original_tracks'],'planes':[plane],'source_old_barrel_UUID':source['uuid'],'source_layer':layer};(O/'only-coupled-ordinary-and-inner-plane-nominee.pkl').write_bytes(pickle.dumps(packet,protocol=5))
 receipt={'verdict':'CONCRETE_LOWER_VS_FEED_PLUS_VDD_COUPLED_NOMINATION_FULL_GATES_OPEN'if packet else'NO_ORDINARY_LOWER_VS_COUPLED_FEED_NOMINATION','parent_model_sha256':sha(M),'rejected_R379_withdrawal_never_adopted':True,'ordinary_landing_area_mm2':landing.area,'candidate_sites':len(candidates),'trials':trials,'source_old_barrel_UUID':packet['source_old_barrel_UUID']if packet else None,'lower_VS_four_pads_C10017_and_all109_retained_keys_source':'MANDATORY_OPEN','all_eight_VS_full_four_.5A_outputs_no_equal_VS_sharing':'RETAINED','new_single_.6-.3_barrel_current_capacity_and_full_sheet_package_drop_thermal':'OPEN_NOT_QUALIFIED','foreign_native_fills_and_owned_FAG_cuts':'NOT_APPLIED_NEED_EXACT_NORMAL_ANTIPAD_AND_REMOVE_ONLY_LEDGER','outer_B_reference_full_body':'OPEN','native_fullmask_and_annular_contact':'OPEN','packet_sha256':sha(O/'only-coupled-ordinary-and-inner-plane-nominee.pkl')if packet else None,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(O/'receipt.json',receipt);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'nominee':bool(packet),'sites':len(candidates)}),flush=True)
if __name__=='__main__':main()
