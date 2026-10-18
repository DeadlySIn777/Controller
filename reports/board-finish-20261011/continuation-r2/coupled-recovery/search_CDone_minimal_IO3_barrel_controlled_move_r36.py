"""Constructive screen: retire only IO3 barrel pose, preserve old contacts."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import tri_route
OUT=H/'FPGA-CDONE-exact-IO3-barrel-controlled-move-ordinary-escape-screen-r36'
NET='/fpga_core/FPGA_CDONE';IO='/IO_3V3';LG='/LOGIC_GND';UID='0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):return [q for x in s.geoms for q in pieces(x)]if hasattr(s,'geoms')else[s]if not s.is_empty else[]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-continuous-ordinary-port-and-curved-F-source-search-r31/receipt.json';r=json.loads(rp.read_bytes());cf=Path(r['cache_file']);assert sha(cf)==r['cache_SHA256'];d=pickle.loads(cf.read_bytes());c=d['context'];local=c['local_current'];full=c['full_before'];rr=H/'FPGA-CDONE-own-T1-native-ground-dogbone-and-ordinary-offpad-port-screen-r27/receipt.json';cr=json.loads(rr.read_bytes());orig=pickle.loads(Path(cr['cache_file']).read_bytes());circle=orig['actual_FPGA_circle_pad_math'];producer=c['producer'];start=[producer['x'],producer['y']];io=next(v for v in local['vias']if v['uuid']==UID);old=[io['x'],io['y']];incident=[t for t in local['tracks']if min(math.dist(t['a'],old),math.dist(t['b'],old))<.000004];base={**local,'vias':[v for v in local['vias']if v['uuid']!=UID]};rec,trees=K.F.build(base);dom=full['domains_normalized'];gap=lambda n:.175 if dom[K.L.norm(n)]==dom[NET]else .625
 def obstacle(row,r):
  if row['kind']=='via':v=row['source'];return K.Z.bounded_disk(v,v['d']/2+r)
  if row['kind']=='track':t=row['source'];return K.Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+r)
  if row['kind']=='pad'and row['uuid']in circle:z=circle[row['uuid']];return K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+r)
  return K.Z.bounded_buffer(row['shape'],r+(.005 if row['kind']=='pad'else 0))
 returns=d['owned_returns'];sg=c['courtyard'].intersection(unary_union([Point(v['via']['x'],v['via']['y']).buffer(1.2,quad_segs=256)for v in returns]));iv=c['courtyard'].intersection(Point(old).buffer(1.5,quad_segs=128));fblocks=[]
 for ly,rows in rec.items():
  for q in rows:
   if K.L.norm(q['net'])!=NET:sg=sg.difference(obstacle(q,.25+gap(q['net'])))
   if K.L.norm(q['net'])!=IO:iv=iv.difference(obstacle(q,.3+gap(q['net'])))
   if ly=='F.Cu'and K.L.norm(q['net'])!=NET:fblocks.append(obstacle(q,.1+gap(q['net'])))
 for p in base['pads']:
  if p['smd']:
   for ly,rs in p['layers'].items():
    if ly not in('F.Cu','B.Cu'):continue
    for s in K.L.poly(rs):
     z=circle.get(p['uuid']);center={'x':z['at'][0],'y':z['at'][1]}if z else None
     sg=sg.difference(K.Z.bounded_disk(center,z['radius']+.375)if z else K.Z.bounded_buffer(s,.38));iv=iv.difference(K.Z.bounded_disk(center,z['radius']+.425)if z else K.Z.bounded_buffer(s,.43))
  for s in K.L.poly(p.get('hole')or[]):sg=sg.difference(K.Z.bounded_buffer(s,.375));iv=iv.difference(K.Z.bounded_buffer(s,.425))
 for v in base['vias']:sg=sg.difference(K.Z.bounded_disk(v,v['drill']/2+.375));iv=iv.difference(K.Z.bounded_disk(v,v['drill']/2+.425))
 # Retain every native no-track/no-via and registered keepout guard.
 reserve,exempt=K.A.reservations()
 for q in full['rule_areas']:
  for s in K.L.poly(q['outline']):
   if q.get('no_vias'):sg=sg.difference(K.Z.bounded_buffer(s,.275));iv=iv.difference(K.Z.bounded_buffer(s,.325))
   if q.get('no_tracks'):fblocks.append(K.Z.bounded_buffer(s,.125))
 for q in reserve['keepouts']:
  if NET in exempt.get(q['name'],set())and IO in exempt.get(q['name'],set()):continue
  for s in K.L.poly(q['outline']):
   if NET not in exempt.get(q['name'],set()):sg=sg.difference(K.Z.bounded_buffer(s,.275));fblocks.append(K.Z.bounded_buffer(s,.125))
   if IO not in exempt.get(q['name'],set()):iv=iv.difference(K.Z.bounded_buffer(s,.325))
 free=c['courtyard'].difference(unary_union(fblocks));component=next((p for p in pieces(free)if p.covers(Point(start))),Point().buffer(0));reachable=sg.intersection(component);trials=[]
 for p in pieces(reachable):
  if p.geom_type!='Polygon':continue
  signal=p.representative_point();sat=list(signal.coords[0]);allowedio=iv.difference(K.Z.bounded_disk({'x':sat[0],'y':sat[1]},.725))
  for q in pieces(allowedio):
   if q.geom_type!='Polygon':continue
   supply=q.representative_point();vat=list(supply.coords[0]);routefree=component.difference(K.Z.bounded_disk({'x':vat[0],'y':vat[1]},.575));part=next((x for x in pieces(routefree)if x.covers(Point(start))and x.covers(signal)),None)
   if part is None:continue
   path,meta=tri_route.route(part,start,sat);path=[[round(x,6),round(y,6)]for x,y in path];body=K.Z.bounded_buffer(LineString(path),.1);cap=Point(sat).buffer(.525,quad_segs=256);rawgap=body.difference(cap).difference(c['source_refs']['In1.Cu']);trials.append({'ordinary_new_SG_at':sat,'retained_existing_IO3_UUID':UID,'prospective_IO3_at':vat,'native_existing_IO3_size_drill':[io['d'],io['drill']],'F_path':path,'F_route':meta,'literal_actual_before_F_SOURCE_gap_without_old_IO3_hole_restoration':info(rawgap),'source_native_after_required_for_own_old_hole_restoration':True})
 (OUT/'ordinary-SG-region-excluding-only-IO3-barrel-old-pose.wkb').write_bytes(sg.wkb);(OUT/'IO3-discrete-safe-native-sized-controlled-move-region.wkb').write_bytes(iv.wkb);put('retained-native-IO3-incident-track-primitives.json',incident);put('joint-ordinary-signal-and-only-IO3-controlled-pose-trials.json',trials);cache=OUT/'only-controlled-IO3-barrel-pose-and-ordinary-CDONE-discrete-screen.pkl';cache.write_bytes(pickle.dumps({'context':c,'IO3':io,'incident':incident,'ordinary_SG_region':sg,'IO3_move_region':iv,'F_component':component,'reachable':reachable,'trials':trials},protocol=5));receipt={'verdict':'CONTROLLED_IO3_POSE_DISCRETE_CONSTRUCTIVE_SCREEN_POSITIVE_ALL_SOURCE_OLDREFS_NATIVE_INTENTS_OPEN'if trials else'CONTROLLED_IO3_POSE_DISCRETE_BOUNDED_SCREEN_NO_POSITIVE','only_nominated_old_material':UID,'native_size_drill_preserved':[io['d'],io['drill']],'incident_tracks_all_retained':len(incident),'ordinary_SG_region':info(sg),'IO3_move_region':info(iv),'F_component_excluding_only_old_IO3_via_pose':info(component),'ordinary_F_reachable_region':info(reachable),'joint_trials':len(trials),'no_new_VIPPO_locations':True,'current_native_intents_all_planes_normal_antipads_old_SOURCE_paths_refs_necks_current_SI':'OPEN','source_before_IO3_root_selector':'R18001.2','full_source_before_netlist_and_all_original_supply_contacts':'PENDING no qualification claimed','native_jobs':0,'adopted':False,'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'inputs':{str(rp.resolve()):sha(rp),str(cf.resolve()):sha(cf)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
