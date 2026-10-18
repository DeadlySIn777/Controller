"""Close actual remaining field grounds with curved ordinary dogbones.

Each new barrel must overlap already source-rooted inner Cu. All hole/SMD
guards are exact and dynamic; no isolated cached fill is a landing goal.
"""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,math,uuid,re
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'remaining-field-ground-feeds-r20'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def polys(s):return[s] if s.geom_type=='Polygon' else[q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'repaired-local-return-audit-r19';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());planes=pickle.loads((bp/'proposed-zones.pkl').read_bytes());rec,trees=F.build({**g,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 smd=[unary_union(C.poly(rs)) for q in g['pads'] if q['smd'] for l,rs in q['layers'].items() if l in('F.Cu','B.Cu')];st=STRtree(smd);ph=[s for q in g['pads'] for s in C.poly(q.get('hole') or [])];ht=STRtree(ph);newvias=[];newtracks=[];newcu=[];rows=[]
 for bank,net,rootref in[('FB','/motherboard_do/FIELD_B_0V','J11005'),('FA','/motherboard_motors/FIELD_GND','J11003')]:
  groups=F.graph(g,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in root if q['kind']=='pad');domain=g['domains_normalized'][net];source={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS[1:-1]};obs={};ots={};foreign={l:[q for q in planes if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS};ft={l:STRtree([q['shape'] for q in foreign[l]]) for l in LAYERS}
  def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
  for l in('F.Cu','B.Cu'):
   oo=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in foreign[l]]
   for rule in g['rule_areas']:
    if rule.get('no_tracks') and l in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
   for rule in res['keepouts']:
    if net not in exceptions.get(rule['name'],set()) and l in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
   obs[l]=oo;ots[l]=STRtree(oo)
  def routed(src,dst,layer,width):
   a,b=nearest_points(src,dst)
   for margin in(2.,5.,12.):
    win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=ots[layer].query(win,predicate='intersects');legal=win.difference(unary_union([obs[layer][int(j)] for j in ii]+[q['shape'].buffer(gap(q['net'])+.025) for q in newcu if q['layer']==layer and C.norm(q['net'])!=net]));options=[]
    for part in polys(legal.buffer(-width/2-.005)):
     aa=part.buffer(-.00002).intersection(src);bb=part.buffer(-.00002).intersection(dst)
     if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
    if not options:continue
    _,part,aa,bb=min(options,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
    except(AssertionError,ValueError):continue
    pts=[[round(x,6),round(y,6)] for x,y in points]
    if len(set(tuple(p) for p in pts))<2:continue
    line=LineString(pts);body=line.buffer(width/2,quad_segs=32)
    if not legal.buffer(.000001).covers(body) or body.intersection(src).area<1e-8 or body.intersection(dst).area<1e-8:continue
    return{'points':pts,'length_mm':line.length,'width_mm':width,'search':search,'body':body}
   return None
  wanted=[(i,xs) for i,xs in enumerate(groups) if xs is not root and any(q['kind']=='pad' and q['pin'] for q in xs)]
  for gi,xs in wanted:
   result=None;attempts=0;annularCandidates=0
   for layer in('F.Cu','B.Cu'):
    pads=[q for q in xs if q['kind']=='pad' and q['layer']==layer];src=unary_union([q['shape'] for q in xs if q['kind']!='fill' and q['layer']==layer])
    if src.is_empty:continue
    for a in sorted(pads,key=lambda q:-q['shape'].area):
     anchor=a['shape'].representative_point()
     for dia,drill in((.5,.2),(.6,.3)):
      for radius in(.6,.9,1.2,1.6,2.2,3.,4.,5.,6.,8.,10.,12.):
       for step in range(32):
        xy=(round(anchor.x+radius*math.cos(step*math.pi/16),6),round(anchor.y+radius*math.sin(step*math.pi/16),6));pt=Point(xy);disk=pt.buffer(dia/2,quad_segs=32);hole=pt.buffer(drill/2,quad_segs=64);attempts+=1
        if not outline.covers(disk):continue
        if any(pt.distance(smd[int(j)])-drill/2<.275-1e-9 for j in st.query(pt.buffer(drill/2+.276),predicate='intersects')):continue
        if any(pt.distance(ph[int(j)])-drill/2<.275-1e-9 for j in ht.query(pt.buffer(drill/2+.276),predicate='intersects')):continue
        if any(math.hypot(xy[0]-v['x'],xy[1]-v['y'])-(drill+v['drill'])/2<.275-1e-9 for v in g['vias']+newvias):continue
        inner=next((l for l in('In1.Cu','In4.Cu','In2.Cu','In3.Cu') if disk.difference(hole).intersection(source[l]).area>.025),None)
        if inner is None:continue
        bad=False
        for l in LAYERS:
         if any(C.norm(rec[l][int(j)]['net'])!=net and disk.distance(rec[l][int(j)]['shape'])<gap(rec[l][int(j)]['net'])+.025-1e-9 for j in trees[l].query(disk.buffer(.65),predicate='intersects')):bad=True;break
         if any(disk.distance(foreign[l][int(j)]['shape'])<gap(foreign[l][int(j)]['net'])+.025-1e-9 for j in ft[l].query(disk.buffer(.65),predicate='intersects')):bad=True;break
         if any(q['layer']==l and C.norm(q['net'])!=net and disk.distance(q['shape'])<gap(q['net'])+.025-1e-9 for q in newcu):bad=True;break
         for rule in g['rule_areas']:
          if rule.get('no_vias') and l in rule['layers'] and any(disk.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad=True;break
         if bad:break
         for rule in res['keepouts']:
          if net not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(disk.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad=True;break
         if bad:break
        if bad:continue
        annularCandidates+=1
        for width in(.25,.2):
         rr=routed(src,disk,layer,width)
         if rr is None:continue
         uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-field-remaining-r20/{bank}/{gi}/{xy}/{dia}'));v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};newvias.append(v);uids=[]
         for l in LAYERS:newcu.append({'uuid':uid+'@'+l,'net':raw,'layer':l,'shape':disk})
         for j,(aa,bb) in enumerate(zip(rr['points'],rr['points'][1:])):
          if aa==bb:continue
          sid=str(uuid.uuid5(uuid.UUID(uid),'stub'+str(j)));t={'uuid':sid,'net':raw,'layer':layer,'a':aa,'b':bb,'w':width,'prospective_not_native':True};newtracks.append(t);uids.append(sid);newcu.append({'uuid':sid,'net':raw,'layer':layer,'shape':C.body(t)});(OUT/(sid+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*aa,*bb,width,layer,raw,sid),encoding='utf-8',newline='')
         (OUT/(uid+'.via-chunk')).write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*xy,dia,drill,raw,uid),encoding='utf-8',newline='');result={'via':v,'native_flash_required':[layer,inner],'real_source_root':rootref+'.2','physical_source_overlap_mm2':disk.difference(hole).intersection(source[inner]).area,'outer_route':{k:v for k,v in rr.items() if k!='body'},'new_segment_UUIDs':uids};break
        if result:break
       if result:break
      if result:break
     if result:break
    if result:break
   rows.append({'domain':bank,'r19_group':gi,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad'],'verdict':'CONSTRUCTED' if result else 'NO_DIRECT_ROOTED_INNER_LANDING','repair':result,'via_candidates':attempts,'all_layer_legal_rooted_annulus_candidates':annularCandidates});print(bank,gi,rows[-1]['verdict'],attempts,annularCandidates,flush=True);write(OUT/'checkpoint.json',rows);(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5))
 write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_ALL_REMAINING_GROUND_FEEDS_MUTUAL_NATIVE_CURRENT_PENDING' if all(q['repair'] for q in rows) else 'REMAINING_GROUND_FEEDS_INCOMPLETE','rows':rows,'new_vias':len(newvias),'new_segments':len(newtracks),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'parent_r19_receipt_sha256':sha(bp/'receipt.json'),'all_layer_prospective_annuli_not_native_evidence':True,'hole_to_every_SMD_guard_mm':.275,'dynamic_all_drill_edge_guard_mm':.275,'minimum_track_width_mm':.20,'no_new_planes':True,'source_rooted_inner_annuli_only':True,'full_mutual_aperture_contact_native_current_gates':'OPEN','board_written':False,'native_jobs':0});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
