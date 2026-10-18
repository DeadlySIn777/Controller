"""Scoped retained LOGIC barrel/stub move, strong ordinary and contact screen."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,math,sys,re,copy
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely import STRtree,from_wkb
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=H/'u19008-logic-barrel-relocation-r94';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'c-u19008-actual-regulated-search-base-r84/model.pkl';assert sha(mp)=='61e7a9e2207c2a21ae850fc7c508db85a1fc49ec391b7d9397f3750424b94c36';g,h,b,z,a=pickle.loads(mp.read_bytes());v=next(v for v in h['vias'] if v['uuid']=='58446867-9078-4bf3-93c2-2c613644426e');t=next(t for t in h['tracks'] if t['uuid']=='01cebc00-28c8-46b8-850d-a04411bc34af');assert t['b']==[v['x'],v['y']] and t['w']==.2
 ud=pickle.loads((H/'c-u19008-actual-regulated-search-base-r84/U19008-proposed-discrete.pkl').read_bytes());failed={t['uuid'] for t in ud['tracks'] if t['w']==.8};newd=pickle.loads((H/'u19008-outside-reservation-branch-tree-r89/proposed-discrete.pkl').read_bytes());newpower=[t for t in newd['tracks'] if t['w']==.8];hh={**h,'tracks':[q for q in h['tracks'] if q['uuid']!=t['uuid'] and q['uuid'] not in failed]+newpower,'vias':[q for q in h['vias'] if q['uuid']!=v['uuid']]};rec,trees=F.build({**hh,'zones':[]});viamap={q['uuid']:q for q in hh['vias']};trackmap={q['uuid']:q for q in hh['tracks']};holes=[];smd=[]
 for q in hh['pads']:
  holes.extend(C.poly(q.get('hole') or []))
  if q['smd']:
   for l in ('F.Cu','B.Cu'):smd.extend(C.poly(q['layers'].get(l,[])))
 holes += [P.bounded_disk(q,q['drill']/2) for q in hh['vias']];hole_tree=STRtree(holes);smdtree=STRtree(smd)
 reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 gs=F.graph(a,v['net']);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));roots=gs[ri];sourcefills={l:unary_union([q['shape'] for q in roots if q['layer']==l and q['kind']=='fill']) for l in LAYERS};powerbody=from_wkb((H/'u19008-outside-reservation-branch-tree-r89/proposed-power-body.wkb').read_bytes());chosen=None;attempts=[]
 def gap(net,other,local=.15):return max(.15 if h['domains_normalized'].get(C.norm(net))==h['domains_normalized'].get(C.norm(other)) else .6,local)+.025
 def dist(q,point,line,r):
  target=point if point is not None else line
  if q['kind']=='via':vv=viamap[q['uuid']];return target.distance(Point(vv['x'],vv['y']))-r-vv['d']/2
  if q['kind']=='track':tt=trackmap[q['uuid']];return target.distance(LineString([tt['a'],tt['b']]))-r-tt['w']/2
  return target.distance(q['shape'])-r
 options=sorted([(math.hypot(dx,dy),dx,dy) for dx in (.10,.125,.15,.175,.2,.25,.3,.4,.5) for dy in (0,.05,-.05,.1,-.1,.15,-.15,.2,-.2)],key=lambda x:x[0])
 for _,dx,dy in options:
  nv=copy.deepcopy(v);nv['x']=round(v['x']+dx,6);nv['y']=round(v['y']+dy,6);nv['mask_provenance']='prospective relocation; exact native F/In1/In4 retained-flash obligation';nt={**t,'b':[nv['x'],nv['y']]};pt=Point(nv['x'],nv['y']);line=LineString([nt['a'],nt['b']]);disk=P.bounded_disk(nv,nv['d']/2);tb=P.bounded_buffer(line,nt['w']/2);errors=[]
  for kind,sh,layers,point,line0,r in [('via',disk,LAYERS,pt,None,nv['d']/2),('stub',tb,['F.Cu'],None,line,nt['w']/2)]:
   for l in layers:
    for j in trees[l].query(sh.buffer(.627),predicate='intersects'):
     q=rec[l][int(j)]
     if q['net']==v['net']:continue
     actual=dist(q,point,line0,r);req=gap(v['net'],q['net'])
     if actual<req+.000002:errors.append({'kind':'all_Cu','item':kind,'layer':l,'foreign_uuid':q['uuid'],'gap_mm':actual,'required_mm':req})
    for q in z:
     if q['layer']!=l or q['net']==v['net']:continue
     req=gap(v['net'],q['net'],float(q.get('clearance_mm',.15)));actual=(point if point is not None else line0).distance(q['shape'])-r
     if actual<req+.000002:errors.append({'kind':'new_plane','item':kind,'layer':l,'foreign_uuid':q['uuid'],'gap_mm':actual,'required_mm':req})
   for area in hh['rule_areas']:
    if set(layers)&set(area['layers']) and area.get('no_vias' if kind=='via' else 'no_tracks') and any(sh.intersects(P.bounded_buffer(s,.025)) for s in C.poly(area['outline'])):errors.append({'kind':'native_area','item':kind,'area':area['uuid']})
   for area in reserved['keepouts']:
    if set(layers)&set(area['layers']) and C.norm(v['net']) not in exceptions.get(area['name'],set()) and any(sh.intersects(P.bounded_buffer(s,.025)) for s in C.poly(area['outline'])):errors.append({'kind':'DRU_reservation','item':kind,'area':area['name']})
  query=pt.buffer(.627)
  for name,shapes,tree in [('all_holes',holes,hole_tree),('all_SMD',smd,smdtree)]:
   for j in tree.query(query,predicate='intersects'):
    actual=pt.distance(shapes[int(j)])-nv['drill']/2
    if actual<.275+.000002:errors.append({'kind':name,'gap_mm':actual,'required_mm':.275})
  if pt.distance(powerbody)-nv['d']/2<.625+.000002:errors.append({'kind':'retained_LOGIC_annulus_to_new_FBG_reference','gap_mm':pt.distance(powerbody)-nv['d']/2,'required_mm':.625})
  ann=disk.difference(P.bounded_disk(nv,nv['drill']/2));support=[{'layer':l,'old_actual_source_fill_annular_overlap_mm2':ann.intersection(sourcefills[l]).area} for l in v['flashed']]
  if any(r['old_actual_source_fill_annular_overlap_mm2']<.001 for r in support):errors.append({'kind':'old_source_fill_contact_missing','support':support})
  attempts.append({'xy':[nv['x'],nv['y']],'errors':errors,'source_annular_support':support});print('R94',nv['x'],nv['y'],len(errors),'errors',flush=True)
  if not errors:chosen={'via':nv,'track':nt,'source_annular_support':support};break
 write(OUT/'site-attempts.json',attempts)
 if chosen:(OUT/'owned-replacements.pkl').write_bytes(pickle.dumps({'vias':[chosen['via']],'tracks':[chosen['track']]},protocol=5))
 write(OUT/'receipt.json',{'verdict':'STRONG_RELOCATION_NOMINATION_FULL_ORIGINAL_SOURCE_CONTACT_REFERENCE_NATIVE_CURRENT_GATES_OPEN' if chosen else 'NO_STRONG_SOURCE_SUPPORTED_LOGIC_RELOCATION_NOMINEE','input_model_sha256':sha(mp),'old_via':v,'old_track':t,'chosen':chosen,'attempts_sha256':sha(OUT/'site-attempts.json'),'replacement_pickle_sha256':sha(OUT/'owned-replacements.pkl') if chosen else None,'board_written':False,'native_jobs':0})
 print('R94 receipt',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
