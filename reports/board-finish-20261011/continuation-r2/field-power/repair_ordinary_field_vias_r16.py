"""Replace rejected proposed vias, preserving actual outside contacts.

Original native Cu and all frozen planes are immutable. Source groups are
rebuilt after removing rejected items; a removed path cannot prove itself.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,uuid,re
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'ordinary-field-via-repair-r17'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir()
 bp=HERE/'complete-local-field-return-contact-audit-r10';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes())
 rp=HERE/'bridged-field-ground-dogbones-r8';r8=json.loads((rp/'receipt.json').read_text());ds=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());r11p=HERE/'extended-outer-field-ground-joins-r11';r11=json.loads((r11p/'receipt.json').read_text());r11tracks=pickle.loads((r11p/'proposed-tracks.pkl').read_bytes());assert sha(r11p/'proposed-tracks.pkl')==r11['proposal_sha256']
 ap=HERE/'local-via-aperture-audit-r14';audit=json.loads((ap/'receipt.json').read_text());bad={q['via_uuid'] for q in audit['rows'] if q['violations']}
 pairs=json.loads((ap/'new-via-pair-drill-failures.json').read_text());pairs=pairs if isinstance(pairs,list) else pairs['pairs']
 # Preserve the strong clear member of a failed pair when the other member is already rejected.
 for pair in pairs:
  ids=[v for v in (pair.get('a'),pair.get('b')) if isinstance(v,str)]
  if not ids:ids=[pair[k] for k in pair if 'uuid' in k.lower() and isinstance(pair[k],str)]
  if not ids:
   ids=[v['via_uuid'] for v in pair.values() if isinstance(v,dict) and 'via_uuid' in v]
  assert len(ids)==2,pair
  if not bad.intersection(ids):bad.add(ids[1])
 badstub='ad24a90e-2565-5700-b98a-173c8744c1ca';bad.add('89e216f8-3252-5aee-88bb-bf9d39e1cd9d')
 oldvias={q['uuid']:q for q in ds['vias']};oldrows={q['via_uuid']:q for q in r8['rows']};assert bad<=set(oldvias)
 h={**g,'vias':[q for q in g['vias'] if q['uuid'] not in bad],'tracks':[q for q in g['tracks'] if q['uuid']!=badstub]+r11tracks}
 rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 planes=pickle.loads((HERE.parent/'sbc-power/io3-field-crossings-r15/model.pkl').read_bytes())[3]+pickle.loads((HERE/'source-rooted-local-field-returns-r6/proposed-zones.pkl').read_bytes())+pickle.loads((rp/'proposed-zones.pkl').read_bytes())
 res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 smd=[unary_union(C.poly(ps)) for q in h['pads'] if q['smd'] for l,ps in q['layers'].items() if l in ('F.Cu','B.Cu')];st=STRtree(smd)
 padholes=[s for q in h['pads'] for s in C.poly(q.get('hole') or [])];pt=STRtree(padholes)
 newvias=[];newtracks=[];rows=[];newcu=[]
 def checkpoint():
  write(OUT/'checkpoint.json',{'rows':rows,'remove_rejected_via_UUIDs':sorted(bad),'remove_rejected_stub_UUID':badstub,'complete':False});(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5))
 for bank,net,rootref in [('FBG','/motherboard_do/FIELD_B_0V','J11005'),('FAG','/motherboard_motors/FIELD_GND','J11003')]:
  raw=next(q['net'] for q in h['pads'] if(q['ref'],q['num'])==(rootref,'2'));domain=h['domains_normalized'][net]
  def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==domain else .6
  obs={};obsTrees={}
  for layer in LAYERS:
   oo=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[layer] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']==layer and C.norm(q['net'])!=net]
   for rule in h['rule_areas']:
    if (rule.get('no_tracks') if layer in ('F.Cu','B.Cu') else rule.get('no_zones')) and layer in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
   if layer in ('F.Cu','B.Cu'):
    for rule in res['keepouts']:
     if net not in exceptions.get(rule['name'],set()) and layer in rule['layers']:oo.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
   obs[layer]=oo;obsTrees[layer]=STRtree(oo)
  def route(src,dst,layer,margin,width):
   if src.is_empty or dst.is_empty:return None
   a,b=nearest_points(src,dst);win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ids=obsTrees[layer].query(win,predicate='intersects');legal=win.difference(unary_union([obs[layer][int(j)] for j in ids]+[q['shape'].buffer(gap(q['net'])+.025) for q in newcu if q['layer']==layer and C.norm(q['net'])!=net]))
   options=[]
   for part in polys(legal.buffer(-width/2-.005)):
    aa=part.buffer(-.00002).intersection(src);bb=part.buffer(-.00002).intersection(dst)
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   if not options:return None
   _,part,aa,bb=min(options,key=lambda q:q[0]);a,b=nearest_points(aa,bb)
   if a.distance(b)<1e-6:return {'points':[],'length':0.,'width':width,'source_overlap':src.intersection(dst).area}
   try:points,search=T.route(part,tuple(a.coords[0]),tuple(b.coords[0]))
   except(AssertionError,ValueError):return None
   points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);core=line.buffer(width/2,quad_segs=32)
   if not legal.buffer(.000001).covers(core) or core.intersection(src).area<1e-8 or core.intersection(dst).area<1e-8:return None
   return {'points':points,'length':line.length,'width':width,'search':search,'source_overlap':core.intersection(dst).area}
  def emit(routeResult,layer,label):
   ids=[]
   for j,(a,b) in enumerate(zip(routeResult['points'],routeResult['points'][1:])):
    if a==b:continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-field-ordinary-repair-r16/{label}/{j}'));t={'uuid':uid,'net':raw,'layer':layer,'a':a,'b':b,'w':routeResult['width'],'prospective_not_native':True};newtracks.append(t);newcu.append({'uuid':uid,'net':raw,'layer':layer,'shape':LineString([a,b]).buffer(t['w']/2,quad_segs=32)});ids.append(uid)
    (OUT/(uid+'.segment-chunk')).write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*a,*b,t['w'],layer,raw,uid),encoding='utf-8',newline='')
   return ids
  wanted=sorted([u for u in bad if oldrows[u]['bank']==bank],key=lambda u:oldrows[u]['r5_group'])
  for oldid in wanted:
   row=oldrows[oldid];oldv=oldvias[oldid];paduid=row['source_outer_pad']['uuid'];layer=row['stub_outer_layer'];actual={**h,'tracks':h['tracks']+newtracks,'vias':h['vias']+newvias};groups=F.graph(actual,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,'2') for q in xs));target=next(xs for xs in groups if any(q['kind']=='pad' and q['uuid']==paduid for q in xs));result=None
   if target is root:result={'method':'REMOVE_REDUNDANT_REJECTED_VIA','already_source_rooted_after_removal':True,'new_segments':[]}
   src=unary_union([q['shape'] for q in target if q['layer']==layer and q['kind']!='fill']);dst=unary_union([q['shape'] for q in root if q['layer']==layer])
   if result is None:
    for margin in (3.,8.,16.):
     for width in(.25,.2):
      rr=route(src,dst,layer,margin,width)
      if rr is not None:
       ids=emit(rr,layer,oldid+'/outer-reuse');result={'method':'REUSE_RETAINED_SOURCE_COPPER_WITHOUT_NEW_HOLE','outer_route':rr,'new_segments':ids};break
     if result:break
   if result is None:
    source={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS[1:-1]};found=False
    for dia,drill in((oldv['d'],oldv['drill']),(.5,.2)):
     for radius in(.025,.05,.075,.1,.15,.2,.3,.45,.6,.8,1.,1.5,2.):
      for step in range(32):
       xy=(round(oldv['x']+radius*math.cos(step*math.pi/16),6),round(oldv['y']+radius*math.sin(step*math.pi/16),6));point=Point(xy);disk=point.buffer(dia/2,quad_segs=32);hole=point.buffer(drill/2,quad_segs=64)
       if not outline.covers(disk):continue
       if any(point.distance(smd[int(j)])-drill/2<.275-1e-9 for j in st.query(point.buffer(drill/2+.276),predicate='intersects')):continue
       if any(point.distance(padholes[int(j)])-drill/2<.275-1e-9 for j in pt.query(point.buffer(drill/2+.276),predicate='intersects')):continue
       if any(math.hypot(xy[0]-v['x'],xy[1]-v['y'])-(drill+v['drill'])/2<.275-1e-9 for v in h['vias']+newvias):continue
       badcu=False
       for l in LAYERS:
        if any(disk.intersects(obs[l][int(j)]) for j in obsTrees[l].query(disk,predicate='intersects')):badcu=True;break
        if any(q['layer']==l and C.norm(q['net'])!=net and disk.distance(q['shape'])<gap(q['net'])+.025-1e-9 for q in newcu):badcu=True;break
        for rule in h['rule_areas']:
         if rule.get('no_vias') and l in rule['layers'] and any(disk.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):badcu=True;break
        if badcu:break
        for rule in res['keepouts']:
         if net not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(disk.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):badcu=True;break
        if badcu:break
       if badcu:continue
       ann=disk.difference(hole);inner=next((l for l in('In1.Cu','In4.Cu','In2.Cu','In3.Cu') if ann.intersection(source[l]).area>.025),None)
       if inner is None:continue
       for width in(.25,.2):
        rr=route(src,disk,layer,3.,width)
        if rr is None:continue
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-field-ordinary-repair-r16/{oldid}/{xy}/{dia}'));v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};newvias.append(v)
        for l in LAYERS:newcu.append({'uuid':uid+'@'+l,'net':raw,'layer':l,'shape':disk})
        ids=emit(rr,layer,oldid+'/relocated');(OUT/(uid+'.via-chunk')).write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*xy,dia,drill,raw,uid),encoding='utf-8',newline='')
        result={'method':'RELOCATED_STRONG_APERTURE_VIA','new_via':v,'outer_route':rr,'new_segments':ids,'native_flash_required':[layer,inner],'rooted_inner_annulus_overlap_mm2':ann.intersection(source[inner]).area};found=True;break
       if found:break
      if found:break
     if found:break
   rows.append({'old_via_UUID':oldid,'old_via':oldv,'bank':bank,'r5_group':row['r5_group'],'physical_pad_UUID':paduid,'source_root':rootref+'.2','verdict':'CONSTRUCTED' if result else 'REPAIR_REQUIRED','repair':result});print(bank,row['r5_group'],None if result is None else result['method'],flush=True);checkpoint()
 write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_REPAIR_MUTUAL_NATIVE_CURRENT_PENDING' if all(q['repair'] for q in rows) else 'LOCAL_VIA_REPAIR_INCOMPLETE','rows':rows,'remove_rejected_via_UUIDs':sorted(bad),'remove_rejected_stub_UUID':badstub,'new_vias':len(newvias),'new_segments':len(newtracks),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'failed_r8_receipt_sha256':sha(rp/'receipt.json'),'strong_aperture_failure_receipt_sha256':sha(ap/'receipt.json'),'pair_failure_sha256':sha(ap/'new-via-pair-drill-failures.json'),'r10_contact_receipt_sha256':sha(bp/'receipt.json'),'r11_receipt_sha256':sha(r11p/'receipt.json'),'all_native_discrete_and_frozen_return_outlines_preserved':True,'only_removed_track_is_rejected_proposed_015_stub':True,'native_min_track_width_mm':.2,'drill_edge_guard_mm':.275,'hole_to_every_SMD_copper_guard_mm':.275,'source_groups_rebuilt_after_rejected_items_removed':True,'full_independent_aperture_contact_mutual_current_and_native_gates':'OPEN','board_written':False,'native_jobs':0});print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
