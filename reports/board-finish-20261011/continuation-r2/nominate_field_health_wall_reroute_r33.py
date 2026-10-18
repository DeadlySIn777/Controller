"""Find a same-layer replacement for one exact field-health wall.

An ordinary .20 F detour must preserve both old endpoints, actual clearances,
drill spacing, native/reserved areas and an actual source-rooted inner return.
No board or accepted model is emitted by this nomination.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 mp=H/'safe-logic-five-and-fag-margin-r22/model.pkl';out=H/'field-health-wall-reroute-r33';assert not out.exists();out.mkdir();g,h,b,z,full=pickle.loads(mp.read_bytes());assert sha(mp)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a';uid='e4373f43-4bf8-4252-afdf-b11a56a2c998';old=next(t for t in h['tracks']if t['uuid']==uid);net=old['net'];domain=h['domains_normalized'][C.norm(net)];peer=H/'field-power/regulated-four-retained-hard-snapshot-r127';pd=pickle.loads((peer/'proposed-discrete.pkl').read_bytes());pq=pickle.loads((peer/'proposed-zones.pkl').read_bytes());mh={**h,'tracks':h['tracks']+pd['tracks'],'vias':h['vias']+pd['vias']};records,trees=F.build({**mh,'zones':[]});search=box(307,150,317,159);holes=[s for p in mh['pads']for s in C.poly(p.get('hole')or[])]+[N.bounded_disk(v,v['drill']/2)for v in mh['vias']];holes=[s for s in holes if s.intersects(search)];I.p.WINDOW=box(.526,.526,449.474,234.474);hard=[s for s in I.p.hard_shapes(mh,I.L.live.reservations(),C.norm(net),'F.Cu')if search.intersects(s)];rr=next(xs for xs in F.graph(full,'/motherboard_motors/FIELD_GND')if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));refs={l:unary_union([q['shape']for q in rr if q['layer']==l])for l in ('In1.Cu','In4.Cu')};near=[records['F.Cu'][int(i)]for i in trees['F.Cu'].query(search,predicate='intersects')];attempts=[];answer=None
 for dx in (.1,.2,.3,.4,.45,.48,.49,.50,.51,.52,.53,.54,.55):
  x=round(old['a'][0]+dx,6);points=[old['a'],[x,old['a'][1]],[x,old['b'][1]],old['b']];new=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-health-wall-r33/'+repr((a,b)))),'net':net,'a':a,'b':b,'w':.2,'layer':'F.Cu'}for a,b in zip(points,points[1:])];errors=[]
  for t in new:
   line=LineString([t['a'],t['b']])
   for q in near:
    if q['net']==net:continue
    need=(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6)+.025+.000020
    if q['kind']=='track':o=q['source'];gap=line.distance(LineString([o['a'],o['b']]))-.1-o['w']/2
    elif q['kind']=='via':o=q['source'];gap=line.distance(Point(o['x'],o['y']))-.1-o['d']/2
    else:gap=line.distance(q['shape'])-.1
    if gap<need:errors.append({'obstacle_kind':q['kind'],'uuid':q['uuid'],'net_raw':q['net'],'gap_mm':gap,'required_mm':need})
   for s in holes:
    if line.distance(s)-.1<.275+.000020:errors.append({'drill_guard_fail':True})
   for s in hard:
    if line.distance(s)-.1<.025+.000020:errors.append({'native_or_reserved_area_fail':True})
   for q in z+pq:
    if q['layer']=='F.Cu'and q['net']!=net and line.distance(q['shape'])-.1<max(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6,float(q.get('clearance_mm',.15)))+.025+.000020:errors.append({'peer_F_plane_fail':q['uuid']})
  body=unary_union([LineString([t['a'],t['b']]).buffer(.1,resolution=256)for t in new]);missing={l:body.difference(refs[l]).area for l in refs};r={'dx_mm':dx,'points_mm':points,'strict_actual_obstacles':errors,'source_rooted_FAG_required_shadow_missing_mm2':missing};attempts.append(r)
  if not errors and min(missing.values())==0:answer={'removed_exact_host_track':old,'new_tracks':new,'new_vias':[],'actual_adjacent_source_reference_layer':min(missing,key=missing.get),'candidate':r};break
 out.joinpath('receipt.json').write_text(json.dumps({'verdict':'STRICT_SAME_F_HEALTH_WALL_NOMINEE_REFERENCE_CONTACT_SOURCE_NATIVE_OPEN'if answer else'NO_DETOUR_IN_FINITE_SAME_F_GRID','parent_model_sha256':sha(mp),'exact_blocker_uuid':uid,'nominee':answer,'attempts':attempts,'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n');print('R33_DETOUR',bool(answer),[(r['dx_mm'],len(r['strict_actual_obstacles']),r['source_rooted_FAG_required_shadow_missing_mm2'])for r in attempts],flush=True)
 if answer:out.joinpath('nomination.pkl').write_bytes(pickle.dumps(answer,protocol=5))
 print('R33_LOCAL_PADS',[(p['num'],p['net'],p['x'],p['y'])for p in h['pads']if p['ref']=='U11025'],flush=True)
if __name__=='__main__':main()
