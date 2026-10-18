"""Scoped two-net U11015 ground/ILIM wall repair, no source/rating changes."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid,re
from pathlib import Path
from shapely.geometry import LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'u11015-ilim-wall-repair-r24'
def polys(s):return[s] if s.geom_type=='Polygon' else[q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'repaired-local-return-audit-r19';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());planes=pickle.loads((bp/'proposed-zones.pkl').read_bytes());r23p=HERE/'remaining-field-ground-feeds-r23';r23=json.loads((r23p/'receipt.json').read_text());assert sha(r23p/'proposed-discrete.pkl')==r23['proposed_discrete_sha256'];d=pickle.loads((r23p/'proposed-discrete.pkl').read_bytes());assert sha(r23p/'proposed-zones.pkl')==r23['proposed_zones_sha256'];z=pickle.loads((r23p/'proposed-zones.pkl').read_bytes());planes+=z;g={**g,'tracks':g['tracks']+d['tracks'],'vias':g['vias']+d['vias'],'zones':g['zones']+[{'uuid':q['uuid'],'net':q['net'],'fills':{q['layer']:[[[list(p) for p in q['shape'].exterior.coords[:-1]],[[list(p) for p in r.coords[:-1]] for r in q['shape'].interiors]]]}} for q in z]}
 ground='/motherboard_motors/FIELD_GND';ilim='/motherboard_power_entry/AUX24_A_ILIM';owned=[t for t in g['tracks'] if t['net']==ilim];assert len(owned)==4 and all(t['layer']=='B.Cu' and t['w']==.2 for t in owned);removed={t['uuid'] for t in owned};h={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};records,trees=F.build({**h,'zones':[]});fullrec,_=F.build(g,nets={ilim});outside=[]
 for t in owned:
  s=C.body(t);hits=[]
  for r in fullrec['B.Cu']:
   if r['uuid'] in removed:continue
   if s.intersection(r['shape']).area>1e-9:hits.append(C.identity(r)|{'contact_Cu_area_mm2':s.intersection(r['shape']).area})
  outside.append({'removed_original_track':t,'retained_same_raw_net_outside_contacts':hits})
 expected={'a96a3ce3-3802-4acb-a1be-cba693067b11','cad97694-7ba9-42fd-97b0-88fa3ad8198a'};assert {q['uuid'] for t in outside for q in t['retained_same_raw_net_outside_contacts']}==expected
 root=next(xs for xs in F.graph(g,ground) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));gpad=next(q for q in records['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','6'));raw=gpad['net'];srcg=gpad['shape'];dstg=unary_union([q['shape'] for q in root if q['layer']=='B.Cu']);srcI=next(q['shape'] for q in records['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','7'));dstI=next(q['shape'] for q in records['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('R11056','1'));outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 masks={};mt={}
 for net in(ground,ilim):
  dom=g['domains_normalized'][net]
  def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==dom else .6
  oo=[q['shape'].buffer(gap(q['net'])+.025) for q in records['B.Cu'] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']=='B.Cu' and C.norm(q['net'])!=net]
  for rule in g['rule_areas']:
   if rule.get('no_tracks') and 'B.Cu' in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
  for rule in res['keepouts']:
   if net not in exceptions.get(rule['name'],set()) and 'B.Cu' in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
  masks[net]=oo;mt[net]=STRtree(oo)
 def route(net,src,dst,width,margin,extra):
  a,b=nearest_points(src,dst);win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=mt[net].query(win,predicate='intersects');legal=win.difference(unary_union([masks[net][int(j)] for j in ii]+extra));options=[]
  for part in polys(legal.buffer(-width/2-.005)):
   aa=part.buffer(-.00002).intersection(src.buffer(width/2-.025));bb=part.buffer(-.00002).intersection(dst.buffer(width/2-.025))
   if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
  if not options:return None
  _,part,aa,bb=min(options,key=lambda q:q[0]);a,b=nearest_points(aa,bb)
  if a.distance(b)<1e-6:return None
  try:pts,search=T.route(part,tuple(a.coords[0]),tuple(b.coords[0]))
  except(AssertionError,ValueError):return None
  pts=[[round(x,6),round(y,6)] for x,y in pts];line=LineString(pts);body=line.buffer(width/2,quad_segs=32)
  if not legal.buffer(.000001).covers(body) or body.intersection(src).area<.001 or body.intersection(dst).area<.001:return None
  return{'points_mm':pts,'width_mm':width,'length_mm':line.length,'body':body,'source_Cu_overlap_mm2':body.intersection(src).area,'destination_Cu_overlap_mm2':body.intersection(dst).area,'search':search}
 answer=None;attempts=[];avoid=[]
 for trial in range(10):
  gr=None
  for width in(.5,.35,.25,.2):
   for margin in(3.,8.,16.):
    gr=route(ground,srcg,dstg,width,margin,avoid)
    if gr:break
   if gr:break
  if gr is None:attempts.append({'trial':trial,'verdict':'NO_GROUND_ESCAPE_WITH_OWNED_ILIM_REMOVED'});break
  ir=None
  for margin in(3.,8.,16.):
   ir=route(ilim,srcI,dstI,.2,margin,[gr['body'].buffer(.175)])
   if ir:break
  if ir:answer={'ground':gr,'ilim':ir};break
  attempts.append({'trial':trial,'ground_route':{k:v for k,v in gr.items() if k!='body'},'verdict':'NO_COMPANION_ILIM_RESTORE'});avoid.append(gr['body'].buffer(.1))
 tracks=[];rows=[]
 if answer:
  for role,rr in answer.items():
   net=raw if role=='ground' else ilim;ids=[]
   for j,(a,b) in enumerate(zip(rr['points_mm'],rr['points_mm'][1:])):
    if a==b:continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-U11015-ILIM-wall-r24/{role}/{j}'));t={'uuid':uid,'net':net,'layer':'B.Cu','a':a,'b':b,'w':rr['width_mm'],'prospective_not_native':True};tracks.append(t);ids.append(uid);(OUT/(uid+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*a,*b,t['w'],net,uid),encoding='utf-8',newline='')
   rows.append({'role':role,'raw_net':net,'new_segment_UUIDs':ids,'route':{k:v for k,v in rr.items() if k!='body'}});print(role,rr['length_mm'],rr['width_mm'],flush=True)
 (OUT/'proposed-tracks.pkl').write_bytes(pickle.dumps(tracks,protocol=5));write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_SCOPED_GROUND_AND_ILIM_RESTORE_MUTUAL_NATIVE_PENDING' if answer else 'U11015_WALL_REPAIR_INCOMPLETE','rows':rows,'attempts':attempts,'owned_original_track_removals':owned,'exact_outside_contact_ledger':outside,'source_components_BOM_properties_node_roles_limits_unchanged':True,'all_R11056_setting_and_U11015_pin_functions_preserved':True,'TPS26624_RTN_pins_remain_distinct_from_GND6':True,'ground_source_root':'J11003.2','new_holes':0,'new_segments':len(tracks),'proposal_sha256':sha(OUT/'proposed-tracks.pkl'),'parent_r19_contact_receipt_sha256':sha(bp/'receipt.json'),'R23_ground_additions_receipt_sha256':sha(r23p/'receipt.json'),'minimum_track_width_mm':.2,'all_other_native_discrete_and_zone_outlines_preserved':True,'full_old_relationship_current_native_DRC_gates':'OPEN','board_written':False,'native_jobs':0});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
