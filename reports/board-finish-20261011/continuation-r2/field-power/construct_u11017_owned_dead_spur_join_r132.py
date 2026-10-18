"""Scoped native FA spur withdrawal and local FIELD5 EN-to-IN join nominee."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,re,uuid
from pathlib import Path
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'u11017-dead-spur-local-join-nominee-r132'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def parts(s):return [s] if s.geom_type=='Polygon' else [p for q in getattr(s,'geoms',[]) for p in parts(q)]
def main():
 assert not O.exists();O.mkdir();base=H.parent/'safe-logic-five-and-fag-margin-r22';assert sha(base/'model.pkl')=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a';g,h,b,z,_=pickle.loads((base/'model.pkl').read_bytes());h=copy.deepcopy(h);z=copy.deepcopy(z);keep=H/'regulated-four-retained-hard-snapshot-r127';d=pickle.loads((keep/'proposed-discrete.pkl').read_bytes());h['vias']+=d['vias'];h['tracks']+=d['tracks'];z+=pickle.loads((keep/'proposed-zones.pkl').read_bytes())+pickle.loads((H/'regulated-reference-safe-source-replacements-r121/proposed-zones.pkl').read_bytes());up=pickle.loads((H/'regulated-reference-safe-source-replacements-r121/owned-new-return-updates.pkl').read_bytes());z=[next((u for u in up if u['uuid']==q['uuid']),q) for q in z];rec,trees=F.build({**h,'zones':[]},layers={'F.Cu'});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};target=next(q for q in rec['F.Cu'] if q['kind']=='pad' and (q['ref'],q['pin'])==('U11017','5'));source=next(q for q in rec['F.Cu'] if q['kind']=='pad' and (q['ref'],q['pin'])==('U11017','8'));net=C.norm(target['net']);assert source['net']==target['net'];raw=target['net'];dom=h['domains_normalized'][net];win=box(218.5,187,225,192);outline=unary_union(C.poly(h['outline'])).buffer(-.526);reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());adapter=H/'moved-supply-escape-rule-adapter-r122/proposed.kicad_dru';assert sha(adapter)=='7a26abd1177cef82d70116f48bc1cff4210c39e75970e043e50e57767425c360';exceptions={}
 for line in adapter.read_text().splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A.NetName != '([^']*)'",m[2])}
 trials=[];answer=None;nominees=['04ea5956-03de-40e7-b07d-1fbdb2533cd4','931d049b-db94-43c0-9411-dda62b2d62e9','147df214-0412-4578-a2c3-e051cafeb6da']
 for uid in nominees:assert tm[uid]['net']=='/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED'
 for count in (2,3):
  removed=set(nominees[:count]);walls=[]
  def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==dom else .6
  for idx in trees['F.Cu'].query(win.buffer(.627),predicate='intersects'):
   q=rec['F.Cu'][int(idx)]
   if q['uuid'] in removed or C.norm(q['net'])==net:continue
   if q['kind']=='track':t=tm[q['uuid']];walls.append(P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(q['net'])+.025))
   elif q['kind']=='via':v=vm[q['uuid']];walls.append(P.bounded_disk(v,v['d']/2+gap(q['net'])+.025))
   else:walls.append(P.bounded_buffer(q['shape'],gap(q['net'])+.025))
  walls += [P.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in z if q['layer']=='F.Cu' and C.norm(q['net'])!=net and q['shape'].intersects(win.buffer(.627))]
  for area in h['rule_areas']:
   if area.get('no_tracks') and 'F.Cu' in area['layers']:walls += [P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(win)]
  for area in reserved['keepouts']:
   if net not in exceptions.get(area['name'],set()) and 'F.Cu' in area['layers']:walls += [P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(win)]
  free=win.intersection(outline).difference(unary_union(walls))
  for width in (.25,.20):
   choices=[]
   for part in parts(free.buffer(-width/2-.002)):
    a=part.buffer(-.00002).intersection(target['shape']);bb=part.buffer(-.00002).intersection(source['shape'])
    if not a.is_empty and not bb.is_empty:choices.append((a.distance(bb),part,a,bb))
   trials.append({'deleted_UUIDs':sorted(removed),'width_mm':width,'target_and_actual_IN_same_legal_component':bool(choices)})
   for _,part,a,bb in sorted(choices,key=lambda r:r[0]):
    start,end=nearest_points(a,bb)
    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
    except (AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);body=P.bounded_buffer(line,width/2)
    if not free.covers(body) or body.intersection(source['shape']).area<.001 or body.intersection(target['shape']).area<.001:continue
    tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u11017-dead-spur-r132/{j}')),'net':raw,'layer':'F.Cu','a':a,'b':bb,'w':width,'prospective_not_native':True} for j,(a,bb) in enumerate(zip(points,points[1:])) if a!=bb];answer={'raw_net':raw,'source_pad_UUID':source['uuid'],'target_pad_UUID':target['uuid'],'length_mm':line.length,'width_mm':width,'points_mm':points,'source_overlap_mm2':body.intersection(source['shape']).area,'target_overlap_mm2':body.intersection(target['shape']).area,'deleted_UUIDs':sorted(removed),'search':search};(O/'proposed-tracks.pkl').write_bytes(pickle.dumps(tracks,protocol=5));(O/'exact-old-owned-track-records.pkl').write_bytes(pickle.dumps([tm[uid] for uid in sorted(removed)],protocol=5));break
   if answer:break
  if answer:break
 write(O/'trials.json',trials);write(O/'receipt.json',{'verdict':'SCOPED_U11017_LOCAL_JOIN_NOMINATION' if answer else 'SCOPED_U11017_WALL_REPAIR_INCOMPLETE','row':answer,'R22_model_sha256':sha(base/'model.pkl'),'R121_new_planes_sha256':sha(H/'regulated-reference-safe-source-replacements-r121/proposed-zones.pkl'),'proposed_tracks_sha256':sha(O/'proposed-tracks.pkl') if answer else None,'exact_old_records_sha256':sha(O/'exact-old-owned-track-records.pkl') if answer else None,'trials_sha256':sha(O/'trials.json'),'source_rule_adapter_sha256':sha(adapter),'old_outside_contacts_source_current_reference_full_native_obligations':'MANDATORY_OPEN','board_written':False,'native_jobs':0});print('R132',sha(O/'receipt.json'),json.dumps(answer),flush=True)
if __name__=='__main__':main()
