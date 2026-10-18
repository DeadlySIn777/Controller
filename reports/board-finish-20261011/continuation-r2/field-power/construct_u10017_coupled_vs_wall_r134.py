"""Coupled .20 VDD join and exact-width retained VS wall replacement."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,re,uuid
from pathlib import Path
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union,nearest_points
from shapely import STRtree
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'u10017-coupled-vdd-vs-wall-nominee-r134'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def parts(s):return [s] if s.geom_type=='Polygon' else [p for q in getattr(s,'geoms',[]) for p in parts(q)]
def main():
 assert not O.exists();O.mkdir();base=H.parent/'safe-logic-five-and-fag-margin-r22';assert sha(base/'model.pkl')=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a';g,h,b,z,prior=pickle.loads((base/'model.pkl').read_bytes());h=copy.deepcopy(h);keep=H/'regulated-four-retained-hard-snapshot-r127';d=pickle.loads((keep/'proposed-discrete.pkl').read_bytes());h['vias']+=d['vias'];h['tracks']+=d['tracks'];z+=pickle.loads((keep/'proposed-zones.pkl').read_bytes())+pickle.loads((H/'regulated-reference-safe-source-replacements-r121/proposed-zones.pkl').read_bytes());rec,trees=F.build({**h,'zones':[]},layers={'F.Cu'});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};old=tm['5c6ebac9-c76a-41f1-8cb8-45e2321f2e89'];target=next(q for q in rec['F.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U10017','4'));net=C.norm(target['net']);assert net=='DOB_DO_FIELD_3V3';gs=pickle.loads((base/'groups.pkl').read_bytes())[net];root=next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==('U11038','1') for q in xs));goal=unary_union([q['shape'] for q in root if q['layer']=='F.Cu']);assert not goal.is_empty;outline=unary_union(C.poly(h['outline'])).buffer(-.526);reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());adapter=H/'moved-supply-escape-rule-adapter-r122/proposed.kicad_dru';exceptions={}
 for line in adapter.read_text().splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A.NetName != '([^']*)'",m[2])}
 def legal(raw,win,extra=()):
  nn=C.norm(raw);dom=h['domains_normalized'][nn];walls=[]
  def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==dom else .6
  for idx in trees['F.Cu'].query(win.buffer(.627),predicate='intersects'):
   q=rec['F.Cu'][int(idx)]
   if q['uuid']==old['uuid'] or C.norm(q['net'])==nn:continue
   if q['kind']=='track':t=tm[q['uuid']];walls.append(P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(q['net'])+.025))
   elif q['kind']=='via':v=vm[q['uuid']];walls.append(P.bounded_disk(v,v['d']/2+gap(q['net'])+.025))
   else:walls.append(P.bounded_buffer(q['shape'],gap(q['net'])+.025))
  walls += [P.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in z if q['layer']=='F.Cu' and C.norm(q['net'])!=nn and q['shape'].intersects(win.buffer(.627))]
  walls += [P.bounded_buffer(body,gap(other)+.025) for other,body in extra if C.norm(other)!=nn]
  for area in h['rule_areas']:
   if area.get('no_tracks') and 'F.Cu' in area['layers']:walls += [P.bounded_buffer(s,.025) for s in C.poly(area['outline']) if s.intersects(win)]
  for area in reserved['keepouts']:
   if nn not in exceptions.get(area['name'],set()) and 'F.Cu' in area['layers']:walls += [P.bounded_buffer(s,.025) for s in C.poly(area['outline']) if s.intersects(win)]
  return win.intersection(outline).difference(unary_union(walls))
 def route(free,startshape,endshape,width):
  options=[]
  for part in parts(free.buffer(-width/2-.002)):
   a=part.buffer(-.00002).intersection(startshape);bb=part.buffer(-.00002).intersection(endshape)
   if not a.is_empty and not bb.is_empty:options.append((a.distance(bb),part,a,bb))
  for _,part,a,bb in sorted(options,key=lambda r:r[0]):
   start,end=nearest_points(a,bb)
   try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
   except (AssertionError,ValueError):continue
   points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);body=P.bounded_buffer(line,width/2)
   if free.covers(body) and body.intersection(startshape).area>.001 and body.intersection(endshape).area>.001:return points,line,body,search
  return None
 a,bb=nearest_points(target['shape'],goal);trials=[];answer=None
 for margin in (3.,8.,18.):
  win=box(min(a.x,bb.x)-margin,min(a.y,bb.y)-margin,max(a.x,bb.x)+margin,max(a.y,bb.y)+margin);join=route(legal(target['net'],win),target['shape'],goal,.2);trials.append({'window_margin_mm':margin,'VDD_source_join':bool(join)})
  if not join:continue
  points,line,body,search=join;aa=P.bounded_buffer(Point(old['a']),old['w']/2);eb=P.bounded_buffer(Point(old['b']),old['w']/2);vw=box(min(old['a'][0],old['b'][0])-margin,min(old['a'][1],old['b'][1])-margin,max(old['a'][0],old['b'][0])+margin,max(old['a'][1],old['b'][1])+margin);replacement=route(legal(old['net'],vw,[(target['net'],body)]),aa,eb,old['w']);trials[-1]['protected_wall_same_width_replacement']=bool(replacement)
  if not replacement:continue
  vp,vl,vbody,vsearch=replacement
  # Exact old center endpoints are mandatory; anchor disks alone may select
  # a shifted endpoint. Complete the subpath only when exact end caps remain
  # covered by unchanged legal geometry.
  vpts=[old['a']]+vp+[old['b']];vline=LineString(vpts);vbody=P.bounded_buffer(vline,old['w']/2)
  if not legal(old['net'],vw,[(target['net'],body)]).covers(vbody):continue
  adds=[]
  for tag,raw,width,pts in [('VDD',target['net'],.2,points),('VS',old['net'],old['w'],vpts)]:
   for j,(pa,pb) in enumerate(zip(pts,pts[1:])):
    if pa==pb:continue
    adds.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u10017-coupled-r134/{tag}/{j}')),'net':raw,'layer':'F.Cu','a':pa,'b':pb,'w':width,'locked':old.get('locked',False) if tag=='VS' else False,'prospective_not_native':True})
  answer={'target_physical_UUID':target['uuid'],'source':'U11038.1','VDD_raw':target['net'],'VDD_points_mm':points,'VDD_length_mm':line.length,'VDD_width_mm':.2,'old_owned_wall_UUID':old['uuid'],'protected_raw':old['net'],'protected_width_mm_unchanged':old['w'],'protected_points_mm':vpts,'protected_old_length_mm':LineString([old['a'],old['b']]).length,'protected_new_length_mm':vline.length,'old_exact_endpoints_retained':True};(O/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5));(O/'exact-old-owned-track-records.pkl').write_bytes(pickle.dumps([old],protocol=5));break
 write(O/'trials.json',trials);write(O/'receipt.json',{'verdict':'COUPLED_VDD_VS_WALL_NOMINATION' if answer else 'COUPLED_U10017_REPAIR_INCOMPLETE','row':answer,'R22_model_sha256':sha(base/'model.pkl'),'trials_sha256':sha(O/'trials.json'),'proposed_tracks_sha256':sha(O/'proposed-tracks.pkl') if answer else None,'exact_old_track_sha256':sha(O/'exact-old-owned-track-records.pkl') if answer else None,'retained_outside_contacts_source_reference_current_native_gates':'MANDATORY_OPEN','board_written':False,'native_jobs':0});print('R134',sha(O/'receipt.json'),json.dumps(answer),flush=True)
if __name__=='__main__':main()
