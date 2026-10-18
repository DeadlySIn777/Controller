"""Exact local coupled-DI6 component diagnosis using saved latest power bodies.

Read-only nomination. No acceptance, source write, native or GPU job.
"""
import sys,json,pickle,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
DI='/motherboard_di/DI6_LOGIC';FAULT='/motherboard_io_control/DI_SENSOR_G2_FAULT';GND='/LOGIC_GND'
BLOCKER='db89a07d-09fb-4801-ad1a-7d84f421f166'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def pieces(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return [sh]
 return [p for q in sh.geoms for p in pieces(q)]
def shape(t):return A.shape({'kind':'segment','a':t['a'],'b':t['b'],'w':t['w']}) if t.get('kind','segment')!='arc' else L.body(t)
def main():
 out=HERE/'di6-fault-exact-components-r2.json';assert not out.exists();started=time.monotonic()
 mf=HERE.parent/'sbc-power/remaining-core-accepted-checkpoints-r50/stage-10/accepted-checkpoint-model.pkl'
 assert C.sha(A.read(mf))=='a1d9cc1c180c827f2a3c9582b218d8856b9cf9dc672cb97a6d5e3bbf81348bb3'
 oldg,h,binding,zones,_=pickle.loads(A.read(mf));h={**h,'tracks':list(h['tracks']),'vias':list(h['vias'])}
 source=A.read(Path(binding['exact_native_discrete_board_file']));assert C.sha(source)==binding['exact_native_discrete_board_sha256'];identity=N.SourceNets(source)
 orig=C.inventory(A.read(S.overlay_tool.base.BASE));current=C.inventory(source)
 prior=json.loads(A.read(HERE/'di6-fault-coupled-r1.json'));restored=prior['restored_original_items'];parsed={u:G.parse(u,orig[4][u],{}) for u in restored}
 assert all(u not in current[4] for u in restored);assert prior['withheld_original_via_pitch_conflict']['withheld_uuid']=='583bf99d-e1f6-45d5-a5cc-692686cd56e9'
 blocker=G.parse(BLOCKER,current[4][BLOCKER],{});bt=next(t for t in h['tracks'] if t['uuid']==BLOCKER)
 assert (bt['a'],bt['b'],bt['w'],bt['layer'],L.norm(bt['net']))==(blocker['a'],blocker['b'],blocker['w'],blocker['layer'],FAULT)
 h['tracks']=[t for t in h['tracks'] if t['uuid']!=BLOCKER]
 for u,q in parsed.items():
  if q['kind']=='via':h['vias'].append({'uuid':u,'net':identity.raw(q['net']),'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'flashed':LAYERS})
  else:
   assert q['kind']=='segment';h['tracks'].append({'uuid':u,'net':identity.raw(q['net']),'a':q['a'],'b':q['b'],'w':q['w'],'layer':q['layer']})
 win=box(106,91,131,126);near=win.buffer(2);rec={l:[] for l in LAYERS};holes=[]
 def add(l,body,kind,uid,net,**extra):
  if body.distance(near)<1:rec[l].append({'layer':l,'shape':body,'kind':kind,'uuid':uid,'net':L.norm(net),**extra})
 for p in h['pads']:
  for l,rs in p['layers'].items():
   for sh in L.poly(rs):add(l,sh,'pad',p['uuid'],p['net'],ref=p['ref'],pin=p['num'])
  for sh in L.poly(p.get('hole') or []):
   if sh.intersects(near):holes.append({'shape':sh,'uuid':p['uuid'],'net':L.norm(p['net']),'kind':'pad_hole'})
 for t in h['tracks']:
  if max(t['a'][0],t['b'][0])<near.bounds[0]-1 or min(t['a'][0],t['b'][0])>near.bounds[2]+1 or max(t['a'][1],t['b'][1])<near.bounds[1]-1 or min(t['a'][1],t['b'][1])>near.bounds[3]+1:continue
  add(t['layer'],shape(t),'track',t['uuid'],t['net'],source=t)
 for v in h['vias']:
  p=Point(v['x'],v['y'])
  if p.distance(near)>2:continue
  for l in v['flashed']:add(l,p.buffer(v['d']/2,quad_segs=128),'via',v['uuid'],v['net'],source=v)
  holes.append({'shape':p.buffer(v['drill']/2,quad_segs=128),'uuid':v['uuid'],'net':L.norm(v['net']),'kind':'via_hole'})
 for z in h['zones']:
  for l,rs in z['fills'].items():
   for i,sh in enumerate(L.poly(rs)):add(l,sh.intersection(near),'fill',z['uuid'],z['net'],native_local=float(z['clearance_mm']),contour=i,prospective=False)
 for z in zones:add(z['layer'],z['shape'].intersection(near),'fill',z['uuid'],z['net'],native_local=float(z.get('clearance_mm',.15)),prospective=True)
 reserves,exempt=A.reservations();hard={l:[] for l in LAYERS}
 for z in h['rule_areas']:
  if z.get('no_tracks'):
   for l in z['layers']:hard[l]+=[{'shape':sh,'uuid':z['uuid'],'exempt':set()} for sh in L.poly(z['outline']) if sh.intersects(near)]
 for z in reserves['keepouts']:
  for l in z['layers']:hard[l]+=[{'shape':sh,'uuid':z['name'],'exempt':exempt.get(z['name'],set())} for sh in L.poly(z['outline']) if sh.intersects(near)]
 dom=h['domains_normalized'];rows=[];candidate={};faulta=[114.25,99.55];faultb=[120.05,99.95]
 for net,a,b in ((FAULT,faulta,faultb),(DI,[113.95,119.35],[114.65,119.45])):
  for layer in ('F.Cu','B.Cu','In3.Cu'):
   obstacles=[];ledger=[]
   for r in rec[layer]:
    if r['net']==net:continue
    gap=.15 if dom.get(net)==dom.get(r['net']) else .6
    if r['kind']=='fill' and not r['prospective'] and gap==.15:continue
    req=gap+.025+.005+.1;obs=r['shape'].buffer(req,quad_segs=128);obstacles.append(obs);ledger.append((r,obs))
   for r in holes:
    if r['net']!=net:obstacles.append(r['shape'].buffer(.275+.1+.005,quad_segs=128))
   for r in hard[layer]:
    if net not in r['exempt']:obstacles.append(r['shape'].buffer(.125,quad_segs=128))
   free=win.difference(unary_union(obstacles));ps=pieces(free);aa=[p for p in ps if p.covers(Point(a))];bb=[p for p in ps if p.covers(Point(b))];same=[p for p in aa if p.covers(Point(b))]
   row={'net':net,'layer':layer,'source_mm':a,'target_mm':b,'source_components':len(aa),'target_components':len(bb),'same_components':len(same),'paths':[]}
   for p in aa:
    boundary=p.boundary;walls=[]
    for r,obs in ledger:
     touch=boundary.intersection(obs.buffer(.000002)).length
     if touch>.00001:walls.append({k:r[k] for k in('uuid','net','kind') if k in r}|{'boundary_contact_length_mm':touch,'source':r.get('source'),'ref':r.get('ref'),'pin':r.get('pin')})
    row.setdefault('source_component_details',[]).append({'area_mm2':p.area,'bounds':p.bounds,'walls':sorted(walls,key=lambda z:z['boundary_contact_length_mm'],reverse=True)})
   for p in same:
    path,search=T.route(p,tuple(a),tuple(b));path=[[round(x,6),round(y,6)] for x,y in path];body=LineString(path).buffer(.1,quad_segs=128)
    assert free.buffer(.000003).covers(LineString(path));row['paths'].append({'points_mm':path,'length_mm':LineString(path).length,'width_mm':.2,'search':search})
   rows.append(row);print(json.dumps({'net':net,'layer':layer,'source_components':len(aa),'target_components':len(bb),'same_components':len(same),'paths':row['paths']}),flush=True)
 candidate={'h':h,'zones':zones,'records':rec,'holes':holes,'hard':hard,'oldg':oldg,'binding':binding,'parsed_restored':parsed,'blocker':blocker,'source_parent':str(Path(binding['exact_native_discrete_board_file']))}
 cache=HERE/'di6-fault-local-components-r2.pkl';cache.write_bytes(pickle.dumps(candidate,protocol=5))
 result={'verdict':'EXACT_PHYSICAL_COMPONENT_NOMINATION_REFERENCE_CONTACT_AND_NATIVE_OPEN','source_parent_sha256':C.sha(source),'latest_CORE10_sha256':C.sha(A.read(mf)),'owned_blocker':blocker,'restored_UUIDs':restored,'withheld_original_via':prior['withheld_original_via_pitch_conflict'],'rows':rows,'cache_path':str(cache),'cache_sha256':C.sha(cache.read_bytes()),'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started,'native_jobs':0,'board_written':False,'reference_contact_acceptance':False,'later_root_protected_additions_not_qualified':True}
 out.write_text(json.dumps(result,indent=1)+'\n');print('DI6_EXACT_COMPONENT_RECEIPT',C.sha(out.read_bytes()),flush=True)
if __name__=='__main__':main()
