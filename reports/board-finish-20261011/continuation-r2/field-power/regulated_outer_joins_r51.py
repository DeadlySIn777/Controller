"""Complete short outer regulated-rail joins after actual source projection."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,re,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision,get_num_coordinates
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
from u11015_projection_r49 import correct_original_fills
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
OUT=HERE/'regulated-outer-source-joins-r51'
PORTS=[('FIELD5','/motherboard_power_entry/FIELD_5V','L11003','2',.360),('A3V3','/motherboard_do/DOA_FIELD_3V3','U11017','1',.050),('B3V3','/motherboard_do/DOB_FIELD_3V3','U11018','1',.090),('BDO3V3','DOB_DO_FIELD_3V3','U11038','1',.040)]

def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(sh):return [sh] if sh.geom_type=='Polygon' else [x for x in getattr(sh,'geoms',[]) if x.geom_type=='Polygon']
def projected(g,h,planes):
 ids={z['uuid'] for z in planes if z.get('label')=='CORE-main-In2' or z.get('label','').startswith('IO3-r15-field-crossing-') or z.get('field_return_proposal') and z['layer']=='In2.Cu'}
 assert len(ids)==9
 return N.projected(g,h,[{**z,'shape':set_precision(z['shape'],1e-6)} if z['uuid'] in ids else z for z in planes])
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'logic-core-split-repair-r53';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'base-model.pkl')==br['base_model_sha256'];g,h,binding,planes,_=pickle.loads((bp/'base-model.pkl').read_bytes());assert sha(bp/'proposed-zones.pkl')==br['proposed_zones_sha256'];planes+=pickle.loads((bp/'proposed-zones.pkl').read_bytes());rp=HERE/'regulated-field-source-feeds-r41';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());assert sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256'];planes+=pickle.loads((rp/'proposed-zones.pkl').read_bytes());h={**h,'tracks':h['tracks']+d['tracks'],'vias':h['vias']+d['vias']};print('project regulated base',len(planes),flush=True);after,cuts=projected(g,h,planes);r44=pickle.loads((HERE/'u11015-reverse-companion-repair-r44/proposed-discrete.pkl').read_bytes());after,roundcuts=correct_original_fills(after,r44['vias']);rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'});outline=unary_union(C.poly(h['outline'])).buffer(-.526);reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 adds=[];rows=[];missing=[];initial=[]
 for bank,net,rootref,rootpin,policy in PORTS:
  gs=F.graph(after,net);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,rootpin) for q in xs));root=gs[ri];raw=next(q['net'] for q in root if q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,rootpin));dom=h['domains_normalized'][net];connected={ri};goal={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in ('F.Cu','B.Cu')};obs={};ots={};initial.append({'bank':bank,'net':net,'source':rootref+'.'+rootpin,'source_group':ri,'unrooted_named_groups':[{ 'group':i,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]})
  def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==dom else .6
  for l in ('F.Cu','B.Cu'):
   ss=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']==l and C.norm(q['net'])!=net]
   for v in h['vias']:
    if v['net']!=raw:ss.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=64))
   for p0 in h['pads']:
    if p0['net']!=raw:ss.extend([s.buffer(.275) for s in C.poly(p0.get('hole') or [])])
   for area in h['rule_areas']:
    if area.get('no_tracks') and l in area['layers']:ss.extend([s.buffer(.025) for s in C.poly(area['outline'])])
   for area in reserved['keepouts']:
    if net not in exceptions.get(area['name'],set()) and l in area['layers']:ss.extend([s.buffer(.025) for s in C.poly(area['outline'])])
   obs[l]=ss;ots[l]=STRtree(ss)
  for gi,xs in enumerate(gs):
   if gi in connected or not any(q['kind']=='pad' and q['pin'] for q in xs):continue
   options=[];answer=None
   for l in ('F.Cu','B.Cu'):
    src=unary_union([q['shape'] for q in xs if q['kind']!='fill' and q['layer']==l]);dst=goal[l]
    if src.is_empty or dst.is_empty:continue
    a,b=nearest_points(src,dst)
    if a.distance(b)<40.:options.append((a.distance(b),l,a,b,src))
   for distance,l,a,b,src in sorted(options,key=lambda x:x[0]):
    for margin in(3.,8.,18.,35.):
     win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=ots[l].query(win,predicate='intersects');legal=win.difference(unary_union([obs[l][int(j)] for j in ii]+[C.body(t).buffer(gap(t['net'])+.025) for t in adds if t['layer']==l and C.norm(t['net'])!=net]))
     for width in(.25,.2):
      choices=[]
      for part in polys(legal.buffer(-width/2-.005)):
       pa=part.buffer(-.00002).intersection(src);pb=part.buffer(-.00002).intersection(goal[l])
       if not pa.is_empty and not pb.is_empty:choices.append((pa.distance(pb),part,pa,pb))
      if not choices:continue
      _,part,pa,pb=min(choices,key=lambda x:x[0]);start,end=nearest_points(pa,pb)
      if get_num_coordinates(part)>150000:continue
      try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
      except(AssertionError,ValueError):continue
      points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);core=line.buffer(width/2,quad_segs=32)
      if line.length>60 or not legal.buffer(.000001).covers(core) or core.intersection(src).area<.001 or core.intersection(goal[l]).area<.001:continue
      uids=[]
      for j,(aa,bb) in enumerate(zip(points,points[1:])):
       if aa==bb:continue
       uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-regulated-outer-r51/{bank}/{gi}/{l}/{j}'));t={'uuid':uid,'net':raw,'layer':l,'a':aa,'b':bb,'w':width,'prospective_not_native':True};adds.append(t);uids.append(uid)
      hits=[i for i,ys in enumerate(gs) if any(q['kind']!='fill' and q['layer']==l and q['shape'].intersection(core).area>.001 for q in ys)];connected|=set(hits);goal[l]=unary_union([goal[l],core]+[q['shape'] for i in hits for q in gs[i] if q['layer']==l and q['kind']!='fill']);answer={'bank':bank,'group':gi,'verdict':'CONSTRUCTED','raw_net':raw,'source':rootref+'.'+rootpin,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']],'layer':l,'length_mm':line.length,'width_mm':width,'points_mm':points,'segment_UUIDs':uids,'physical_groups_joined':hits,'full_rail_reservation_A':policy,'actual_signed_branch_current_mesh_and_fault_capacity':'OPEN','search':search};print(bank,gi,'outer',l,width,line.length,flush=True);break
     if answer:break
    if answer:break
   if answer:rows.append(answer)
   else:missing.append({'bank':bank,'group':gi,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']],'nearest_source_mm':min([x[0] for x in options],default=None)});print(bank,gi,'NO_OUTER_JOIN',flush=True)
   write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing});(OUT/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5))
 if not (OUT/'proposed-tracks.pkl').exists():(OUT/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5))
 (OUT/'base-model.pkl').write_bytes(pickle.dumps((g,h,binding,planes,after),protocol=5));write(OUT/'initial-source-census.json',initial);write(OUT/'outward-round-cutters.json',roundcuts)
 write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_COMPLETE_REGULATED_OUTER_FEEDS_MUTUAL_NATIVE_CURRENT_PENDING' if not missing else 'REGULATED_OUTER_FEEDS_INCOMPLETE','rows':rows,'remaining':missing,'new_segments':len(adds),'new_holes':0,'new_zones':0,'proposed_tracks_sha256':sha(OUT/'proposed-tracks.pkl'),'base_model_sha256':sha(OUT/'base-model.pkl'),'input_R41_receipt_sha256':sha(rp/'receipt.json'),'input_R53_receipt_sha256':sha(bp/'receipt.json'),'initial_source_census_sha256':sha(OUT/'initial-source-census.json'),'outward_round_cutter_ledger_sha256':sha(OUT/'outward-round-cutters.json'),'all_control_BOM_poses_outputs_safety_rates_limits_unchanged':True,'minimum_track_width_mm':.2,'protected_R7_not_composed':True,'native_jobs':0,'board_written':False,'full_mutual_contact_signed_mesh_native_aperture_flash_min_thickness_fault_thermal_gates':'OPEN'});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
