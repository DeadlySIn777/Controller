"""Minimal movement of two new HOST segments; every existing endpoint held."""
import pickle,json,sys,hashlib,copy,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
P=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r247/model.pkl';assert hashlib.sha256(P.read_bytes()).hexdigest()=='9b5ce5fcc6fcf741f73ba48cd15ab396a022115ba7110ee3d4c7fc27459cbf86';g,h,b,q,c=pickle.loads(P.read_bytes())
OUT=H/'HOST-two-new-segment-single-bend-minimal-drill-guard-nominations-r250';assert not OUT.exists();OUT.mkdir()
uids={'0e1758e0-b441-5845-bba2-0626dfeed39d','30508a19-c8b3-52b5-ac93-e67478d62990'};tracks=[t for t in h['tracks']if t['uuid']in uids];assert len(tracks)==2;old=[205.077357,143.450982];net=K.L.norm(tracks[0]['net']);records,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];holes=[(v['uuid'],K.L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],K.L.norm(p['net']),s)for p in h['pads']for s in K.L.poly(p.get('hole')or[])];ht=STRtree([x[2]for x in holes]);reserve,exempt=K.A.reservations();attempts=[];accepted=[]
for dy in(-.005,-.01,-.015,-.02,-.025):
 for dx in(0,-.005,.005,-.01,.01):
  xy=[round(old[0]+dx,6),round(old[1]+dy,6)];nt=[];errors=[];checks=[]
  for t in tracks:
   z=copy.deepcopy(t)
   for end in('a','b'):
    if list(z[end])==old:z[end]=xy
   nt.append(z);axis=LineString([z['a'],z['b']]);radius=z['w']/2;body=K.Z.bounded_buffer(axis,radius);ly=z['layer']
   for j in trees[ly].query(body.buffer(.8),predicate='intersects'):
    r=records[ly][int(j)]
    if K.L.norm(r['net'])==net:continue
    if r['kind']=='via':v=r['source'];dist=axis.distance(Point(v['x'],v['y']))-radius-v['d']/2
    elif r['kind']=='track'and not r['source'].get('m'):v=r['source'];dist=axis.distance(LineString([v['a'],v['b']]))-radius-v['w']/2
    else:dist=axis.distance(r['shape'])-radius
    req=(.15 if dom[K.L.norm(r['net'])]==dom[net]else.6)+.025;row={'track':z['uuid'],'other':r['uuid'],'kind':r['kind'],'gap_mm':dist,'required_mm':req};checks.append(row)
    if dist<req:errors.append(row)
   for j in ht.query(body.buffer(.285),predicate='intersects'):
    u,n,sh=holes[int(j)]
    if n==net:continue
    dist=axis.distance(sh)-radius-.005;row={'track':z['uuid'],'other_drill':u,'gap_mm':dist,'required_mm':.275};checks.append(row)
    if dist<.275:errors.append(row)
   for r in h['rule_areas']:
    if ly in r['layers']and r.get('no_tracks')and any(body.distance(s)<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'native_rule_area','UUID':r['uuid']})
   for r in reserve['keepouts']:
    if ly in r['layers']and net not in exempt.get(r['name'],set())and any(body.distance(s)<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'reserved_area','name':r['name']})
  row={'xy':xy,'move_mm':math.hypot(dx,dy),'errors':errors,'checks':checks};attempts.append(row)
  if not errors:accepted.append((row['move_mm'],xy,nt))
(OUT/'attempts.json').write_text(json.dumps(attempts,indent=1)+'\n')
assert accepted,'No local bend passes actual discrete/hole/rule guards';move,xy,nt=min(accepted,key=lambda x:(x[0],x[1]));packet={'base_model_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'only_two_new_track_UUIDs':sorted(uids),'original_bend':old,'new_bend':xy,'movement_mm':move,'replace_tracks':nt,'original_Cu_FP_and_vias_all_unchanged':True,'actual_fill_reference_source_rebuild':'OPEN'};p=OUT/'proposed-two-new-HOST-track-bend.pkl';p.write_bytes(pickle.dumps(packet,protocol=5));(OUT/'receipt.json').write_text(json.dumps({'status':'LOCAL_HOST_BEND_DISCRETE_ALL_HOLE_RULE_GUARD_NOMINEE_PASS','packet_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'selected_bend_mm':xy,'movement_mm':move,'accepted_sites':len(accepted),'fresh_fill_source_reference_native':'OPEN','adopted':False},indent=1)+'\n');print('R250_BEND',xy,move,hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
