"""Continuous ordinary CDONE via region and curved F escape, no native jobs."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for p in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
OUT=H/'FPGA-CDONE-continuous-ordinary-port-and-curved-F-source-search-r31'
NET='/fpga_core/FPGA_CDONE';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def pieces(s):
 if s.is_empty:return []
 if hasattr(s,'geoms'):return [q for x in s.geoms for q in pieces(x)]
 return [s]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();rp=H/'FPGA-CDONE-own-T1-native-ground-dogbone-and-ordinary-offpad-port-screen-r27/receipt.json';r=json.loads(rp.read_bytes());cf=Path(r['cache_file']);assert sha(cf)==r['cache_SHA256'];d=pickle.loads(cf.read_bytes());c=d['base_census'];local=c['local_current'];full=c['full_before'];circle=d['actual_FPGA_circle_pad_math'];producer=c['producer'];start=[producer['x'],producer['y']];court=c['courtyard'];refs=c['source_refs'];rec,trees=K.F.build(local);dom=full['domains_normalized'];req=lambda n:.175 if dom[K.L.norm(n)]==dom[NET]else .625
 returns=[]
 for candidate in c['own_return_candidates']:
  if not candidate['actually_observed_In1_In4_masks']or not candidate['actual_SOURCE_ground_layer_keys']or not all(x>0 for x in candidate['finite_actual_SOURCE_annular_area_mm2'].values()):continue
  v=candidate['via'];p=next(q for q in local['pads']if q['uuid']==candidate['same_part_ground_pad_UUID']);pt=[p['x'],p['y']];vt=[v['x'],v['y']];stub=[t for t in local['tracks']if t['layer']=='F.Cu'and K.L.norm(t['net'])==LG and min(math.dist(t['a'],pt)+math.dist(t['b'],vt),math.dist(t['b'],pt)+math.dist(t['a'],vt))<.000004]
  if len(stub)!=1:continue
  ann=Point(vt).buffer(v['d']/2,quad_segs=128).difference(Point(vt).buffer(v['drill']/2,quad_segs=128));body=K.L.body(stub[0]);pb=unary_union(K.L.poly(p['layers']['F.Cu']));assert body.intersection(pb).area>0 and body.intersection(ann).area>0;returns.append({'via':v,'pad':{k:p[k]for k in('uuid','ref','num','net','x','y')},'stub':stub[0],'finite_pad_stub_area':body.intersection(pb).area,'finite_stub_annulus_area':body.intersection(ann).area,'actual_SOURCE_annuli':candidate['finite_actual_SOURCE_annular_area_mm2']})
 assert returns;region=court.intersection(unary_union([Point(v['via']['x'],v['via']['y']).buffer(1.2,quad_segs=256)for v in returns]));initial=region;ledger=[];fblocks=[]
 def obstacle(row,radius):
  if row['kind']=='via':v=row['source'];return K.Z.bounded_disk(v,v['d']/2+radius)
  if row['kind']=='track':t=row['source'];return K.Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+radius)
  if row['kind']=='pad'and row['uuid']in circle:z=circle[row['uuid']];return K.Z.bounded_disk({'x':z['at'][0],'y':z['at'][1]},z['radius']+radius)
  return K.Z.bounded_buffer(row['shape'],radius+(.005 if row['kind']=='pad'else 0))
 for ly,rows in rec.items():
  for row in rows:
   if K.L.norm(row['net'])==NET:continue
   cut=obstacle(row,.25+req(row['net']));removed=region.intersection(cut)
   if not removed.is_empty:ledger.append({'kind':'current_discrete_true_Cu','UUID':row['uuid'],'layer':ly,'net':row['net'],'removed':info(removed)})
   region=region.difference(cut)
   if ly=='F.Cu':fblocks.append(obstacle(row,.1+req(row['net'])))
 for p in local['pads']:
  if p['smd']:
   for ly,rs in p['layers'].items():
    if ly not in('F.Cu','B.Cu'):continue
    for s in K.L.poly(rs):
     cut=K.Z.bounded_disk({'x':circle[p['uuid']]['at'][0],'y':circle[p['uuid']]['at'][1]},circle[p['uuid']]['radius']+.375)if p['uuid']in circle else K.Z.bounded_buffer(s,.38);removed=region.intersection(cut)
     if not removed.is_empty:ledger.append({'kind':'ALL_SMD_ordinary_drill_including_own','UUID':p['uuid'],'layer':ly,'removed':info(removed)})
     region=region.difference(cut)
 for v in local['vias']:
  cut=K.Z.bounded_disk(v,v['drill']/2+.375);removed=region.intersection(cut)
  if not removed.is_empty:ledger.append({'kind':'old_physical_hole','UUID':v['uuid'],'removed':info(removed)})
  region=region.difference(cut)
 for p in local['pads']:
  for s in K.L.poly(p.get('hole')or[]):region=region.difference(K.Z.bounded_buffer(s,.375))
 # Existing SOURCE-ground plane fills may acquire only the normal new SG
 # antipad. Other-net fill bodies remain hard in this screening phase.
 for zone in full['zones']:
  net=K.L.norm(zone['net'])
  if net==NET:continue
  for ly,rs in zone.get('fills',{}).items():
   for s in K.L.poly(rs):
    if not s.intersects(initial.buffer(1)):continue
    if net!=LG:
     cut=K.Z.bounded_buffer(s,.25+req(net));removed=region.intersection(cut)
     if not removed.is_empty:ledger.append({'kind':'foreign_actual_full_plane','UUID':zone['uuid'],'layer':ly,'net':net,'removed':info(removed)})
     region=region.difference(cut)
    if ly=='F.Cu':fblocks.append(K.Z.bounded_buffer(s,.1+req(net)))
 reservation,exempt=K.A.reservations()
 for q in full['rule_areas']:
  if q.get('no_vias'):
   for s in K.L.poly(q['outline']):region=region.difference(K.Z.bounded_buffer(s,.275))
  if q.get('no_tracks'):
   for s in K.L.poly(q['outline']):fblocks.append(K.Z.bounded_buffer(s,.125))
 for q in reservation['keepouts']:
  if NET in exempt.get(q['name'],set()):continue
  for s in K.L.poly(q['outline']):region=region.difference(K.Z.bounded_buffer(s,.275));fblocks.append(K.Z.bounded_buffer(s,.125))
 ffree=court.difference(unary_union(fblocks));fparts=[p for p in pieces(ffree)if p.covers(Point(start))];assert len(fparts)<=1;fcomponent=fparts[0]if fparts else Point().buffer(0);reachable=region.intersection(fcomponent);trials=[];accepted=[]
 for p in pieces(reachable):
  if p.geom_type!='Polygon':continue
  points=[p.representative_point(),p.centroid]
  # Sampling endpoints does not establish topology; topology is the full
  # continuous polygon intersection above. Every route chord is certified.
  for point in points:
   if not p.covers(point):continue
   at=list(point.coords[0]);cap=Point(at).buffer(.525,quad_segs=256);allowed=refs['In1.Cu'].union(cap).buffer(-.100004);free=fcomponent.intersection(allowed);part=next((q for q in pieces(free)if q.covers(Point(start))and q.covers(point)),None);row={'at':at,'reachable_true_Cu_component':True,'SOURCE_corridor_connected':part is not None}
   if part is not None:
    path,meta=tri_route.route(part,start,at);path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path);body=K.Z.bounded_buffer(axis,.1);gap=body.difference(cap).difference(refs['In1.Cu']);row.update(path=path,route=meta,literal_F_SOURCE_gap=info(gap))
    if gap.is_empty and fcomponent.covers(axis):accepted.append(row)
   trials.append(row)
 (OUT/'ordinary-centre-free-region.wkb').write_bytes(region.wkb);(OUT/'F-true-Cu-producer-component.wkb').write_bytes(fcomponent.wkb);put('continuous-ordinary-clearance-subtraction-ledger.json',ledger);put('verified-same-part-private-SOURCE-return-dogbones.json',returns);put('source-curved-F-endpoint-trials.json',trials)
 blockers=[q for ly,rows in rec.items()for q in rows if q['uuid']in('0f88a8b6-67a2-4f38-b7cf-6b33a89cf99e','a939ae18-b62d-444e-b29d-abc9a989a167')];put('named-old-current-blocker-primitives.json',[{'layer':q['layer'],'kind':q['kind'],'UUID':q['uuid'],'net':q['net'],'source':q.get('source',{'UUID':q['uuid'],'kind':q['kind']})}for q in blockers]);cache=OUT/'continuous-ordinary-site-and-escape-prospective-screen.pkl';cache.write_bytes(pickle.dumps({'context':c,'owned_returns':returns,'ordinary_region':region,'F_component':fcomponent,'reachable':reachable,'accepted':accepted},protocol=5));result={'verdict':'ORDINARY_CONTINUOUS_SITE_WITH_SOURCE_F_ESCAPE_SCREEN_POSITIVE_FULL_NATIVE_INTENT_ANTIPAD_B_ROUTE_OPEN'if accepted else'ORDINARY_CONTINUOUS_PORT_SCREEN_BOUNDED_NO_POSITIVE','actual_own_SOURCE_returns':len(returns),'initial_region':info(initial),'continuous_ordinary_region':info(region),'F_producer_component':info(fcomponent),'ordinary_F_reachable_region':info(reachable),'trial_count':len(trials),'accepted_count':len(accepted),'accepted':accepted,'new_VIPPO_locations':0,'native_jobs':0,'adopted':False,'foreign_current_native_owned_profile_intents_full_normal_antipads_B_ROUTE_source_oldrefs_current_SI':'OPEN','cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'inputs':{str(rp.resolve()):sha(rp),str(cf.resolve()):sha(cf)},'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','actual_own_SOURCE_returns','continuous_ordinary_region','ordinary_F_reachable_region','trial_count','accepted_count','accepted','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
