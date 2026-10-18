"""Source-rooted LOGIC repair using a ledgered extra existing-via plane flash."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision,get_num_coordinates
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'logic-island-repair-r18'
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'complete-local-field-return-contact-audit-r10';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());net='/LOGIC_GND';rootref='J11001';viaid='18701851-0390-4dc4-b03d-f8e1cd66c395';v=next(q for q in g['vias'] if q['uuid']==viaid);raw=v['net'];assert set(v['flashed'])=={'F.Cu','In1.Cu','In4.Cu','B.Cu'}
 groups=F.graph(g,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,'2') for q in xs));target=next(xs for xs in groups if any(q['kind']=='via' and q['uuid']==viaid for q in xs));assert root is not target
 planes=pickle.loads((HERE.parent/'sbc-power/io3-field-crossings-r15/model.pkl').read_bytes())[3]+pickle.loads((HERE/'source-rooted-local-field-returns-r6/proposed-zones.pkl').read_bytes())+pickle.loads((HERE/'bridged-field-ground-dogbones-r8/proposed-zones.pkl').read_bytes());records,_=F.build({**g,'zones':[]});domain=g['domains_normalized'][net];outline=unary_union(C.poly(g['outline'])).buffer(-.526);result=None;attempts=[]
 def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
 disk=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64);hole=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64);ann=disk.difference(hole)
 for layer in('In3.Cu','In2.Cu'):
  dst=unary_union([q['shape'] for q in root if q['layer']==layer]);src=ann
  if dst.is_empty:continue
  a,b=nearest_points(src,dst);obstacles=[q['shape'].buffer(gap(q['net'])+.025) for q in records[layer] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']==layer and C.norm(q['net'])!=net]
  for p0 in g['pads']:
   if not p0.get('plated') or C.norm(p0['net'])!=net:obstacles.extend([s.buffer(.275) for s in C.poly(p0.get('hole') or [])])
  for v0 in g['vias']:
   if C.norm(v0['net'])!=net:obstacles.append(Point(v0['x'],v0['y']).buffer(v0['drill']/2+.275,quad_segs=32))
  for rule in g['rule_areas']:
   if rule.get('no_zones') and layer in rule['layers']:obstacles.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
  # The own drill has no Cu, but its plated annulus remains a real source contact.
  obstacles.append(hole);tree=STRtree(obstacles)
  for margin in(3.,10.,25.,50.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=tree.query(win,predicate='intersects');legal=win.difference(unary_union([obstacles[int(j)] for j in ii]))
   for width in(.5,.35,.25):
    options=[]
    for part in polys(legal.buffer(-width/2-.005)):
     aa=part.buffer(-.00002).intersection(src);bb=part.buffer(-.00002).intersection(dst)
     if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
    if not options:attempts.append({'layer':layer,'margin':margin,'width':width,'verdict':'NO_SHARED_COMPONENT'});continue
    _,part,aa,bb=min(options,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
    if get_num_coordinates(part)>160000:
     pp=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);poss=[q for q in polys(pp) if q.intersects(aa) and q.intersects(bb)]
     if not poss:continue
     part=max(poss,key=lambda q:q.area);start,end=nearest_points(part.buffer(-.00002).intersection(aa),part.buffer(-.00002).intersection(bb))
    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
    except(AssertionError,ValueError):continue
    line=LineString(points);core=line.buffer(width/2,quad_segs=32)
    if not legal.buffer(.000001).covers(core):continue
    body=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]),1e-6)
    if not legal.buffer(.000002).covers(body) or body.intersection(src).area<.01 or body.intersection(dst).area<1e-8:continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-logic-R5051-island-r18/'+layer));z={'uuid':uid,'net':raw,'layer':layer,'shape':body,'clearance_mm':.15};(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps([z],protocol=5));(OUT/(uid+'.wkb')).write_bytes(body.wkb);result={'zone_UUID':uid,'raw_net':raw,'layer':layer,'core_width_mm':width,'length_mm':line.length,'points_mm':points,'source_J11001_2_overlap_mm2':body.intersection(dst).area,'existing_via_annulus_overlap_mm2':body.intersection(src).area,'source_root':'J11001.2','search':search,'sheet_only_R35um60C_ohm':.00057003672*line.length/width};print(result,flush=True);break
   if result:break
  if result:break
 receipt={'verdict':'CONSTRUCTED_EXISTING_PTH_FLASH_REPAIR_NATIVE_PENDING' if result else 'LOGIC_ISLAND_REPAIR_INCOMPLETE','repair':result,'attempts':attempts,'exact_target_physical_relationship':[C.identity(q) for q in target if q['kind']!='fill'],'existing_via_UUID':viaid,'existing_native_flash_mask':v['flashed'],'prospective_additional_flash_layer':None if result is None else result['layer'],'native_fill_must_attest_added_flash_and_all_four_retained_flashes':True,'new_holes':0,'old_discrete_Cu_unchanged':True,'frozen_return_outlines_unchanged':True,'parent_r10_contact_receipt_sha256':sha(bp/'receipt.json'),'proposal_sha256':sha(OUT/'proposed-zones.pkl') if result else None,'full_joint_contact_current_clearance_fill_gates':'OPEN','board_written':False,'native_jobs':0};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
