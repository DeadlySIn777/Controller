"""Construct a true physical FG reference under the new monitor route, all foreign fills hard."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
import restore_SAFE_generated_precision_states_r168 as PS
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return []
 if s.geom_type=='Polygon':return [s]
 return [q for p in getattr(s,'geoms',[])for q in parts(p)]
def root(gs):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs))
def main():
 parent=H/'SAFE-native-monitor-rotation-composition-r69';mr=parent/'receipt.json';r=json.loads(mr.read_bytes());assert sha(mr)=='912d48982e310c06a126392a2a0712a275d65b1c5c99beccc785a250165d1d8c'and r['verdict']=='ACTUAL_NATIVE_MONITOR_SOURCE_PROJECTED_NO_PRIOR_SOURCE_LOSS_FULL_GATES_OPEN'
 mp=parent/'model.pkl';assert sha(mp)==r['model_sha256'];out=H/'SAFE-monitor-real-source-reference-patch-r73';assert not out.exists();out.mkdir();g,h,b,z,current=pickle.loads(mp.read_bytes())
 existing=[q for q in z if q['uuid']!='ec99314b-c244-5748-bb67-de032c66ee3c'];replay=PS.restore_bound_generated_precision_states(b,existing)
 q=next(q for q in z if q['uuid']=='ec99314b-c244-5748-bb67-de032c66ee3c')
 for role in ('shape','zone_outline_shape'):
  before=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==before
 put(out/'exact-parent-operation-metadata.json',replay)
 operation=pickle.loads((parent/'owned-operation.pkl').read_bytes());d=operation['exact_monitor_delta'];uv=next(t for t in d['tracks']if C.norm(t['net'])!='/motherboard_motors/FIELD_GND');axis=LineString([uv['a'],uv['b']]);body=N.bounded_buffer(axis,uv['w']/2);target=N.bounded_buffer(axis,.175);fg=root(pickle.loads((parent/'source-groups.pkl').read_bytes())['/motherboard_motors/FIELD_GND']);raw=next(q['net']for q in fg if q['kind']=='pad');source=unary_union([q['shape']for q in fg if q['kind']=='fill'and q['layer']=='In1.Cu']);window=box(337,53,357,70);outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 records,trees=F.build(current);obs=[];obstacles=[]
 for i in trees['In1.Cu'].query(window.buffer(2),predicate='intersects'):
  q=records['In1.Cu'][int(i)]
  if q['net']==raw:continue
  guard=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][C.norm(raw)]else .6)+.025+.000020
  if q['kind']=='track':t=q['source'];shape=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+guard)
  elif q['kind']=='via':v=q['source'];shape=N.bounded_disk(v,v['d']/2+guard)
  else:shape=N.bounded_buffer(q['shape'],guard)
  obs.append(shape)
  if shape.intersects(target):obstacles.append({'UUID':q['uuid'],'net':q['net'],'kind':q['kind'],'target_overlap_mm2':shape.intersection(target).area})
 for q in z:
  if q['layer']=='In1.Cu'and q['net']!=raw and window.buffer(2).intersects(q['shape']):
   guard=max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][C.norm(raw)]else .6,float(q.get('clearance_mm',.15)))+.025+.000020;obs.append(N.bounded_buffer(q['shape'],guard))
 for v in h['vias']:
  if C.norm(v['net'])==C.norm(raw):continue
  if window.buffer(1).intersects(Point(v['x'],v['y'])):obs.append(N.bounded_disk(v,v['drill']/2+.275+.000020))
 for p in h['pads']:
  if C.norm(p['net'])==C.norm(raw):continue
  obs.extend(N.bounded_buffer(s,.275+.000020)for s in C.poly(p.get('hole')or [])if window.buffer(1).intersects(s))
 for rule in h['rule_areas']:
  if rule.get('no_zones')and'In1.Cu'in rule['layers']:obs.extend(N.bounded_buffer(s,.025+.000020)for s in C.poly(rule['outline'])if window.intersects(s))
 legal=set_precision(window.intersection(outline).difference(unary_union(obs)),1e-6);attempts=[];candidate=None
 put(out/'target-legality.json',{'new_UV_body_covered_by_full_hard_physical_region':legal.covers(body),'new_reference_width035_strip_covered':legal.covers(target),'physical_target_outside_area_mm2':body.difference(legal).area,'foreign_blockers':obstacles})
 if legal.covers(target):
  for width in (.5,.35,.25):
   for face in parts(legal.buffer(-width/2-.000020)):
    aa=face.intersection(target.buffer(-width/2-.000020));bb=face.intersection(source.buffer(-.000020))
    if aa.is_empty or bb.is_empty:continue
    a,endpoint=nearest_points(aa,bb)
    try:points,proof=T.route(face,tuple(a.coords[0]),tuple(endpoint.coords[0]))
    except(AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)]for x,y in points];line=LineString(points)
    if not face.covers(line):continue
    native=set_precision(unary_union([target,N.bounded_buffer(line,width/2)]),1e-6)
    if not legal.covers(native):continue
    ownholes=unary_union([N.bounded_disk(v,v['drill']/2)for v in h['vias']if C.norm(v['net'])==C.norm(raw)]+[s for p in h['pads']if C.norm(p['net'])==C.norm(raw)for s in C.poly(p.get('hole')or [])]);physical=native.difference(ownholes)
    if not physical.covers(body):continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-monitor-reference-r73/'+repr(points)));q={'uuid':uid,'net':raw,'layer':'In1.Cu','shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'min_thickness_mm':.15,'priority':124,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'physical_Cu_drill_subtracted':True,'label':'Actual J3 source monitor UV return reference R73'};candidate=q;attempts.append({'width_mm':width,'points':points,'length_mm':line.length,'source_overlap_mm2':physical.intersection(source).area,'full_UV_body_coverage':physical.covers(body),'constructor':proof});break
   if candidate:break
 if candidate:
  projected,retreat=N.projected(g,h,z+[candidate]);new=root(F.graph(projected,'/motherboard_motors/FIELD_GND'));nf=unary_union([q['shape']for q in new if q['kind']=='fill'and q['layer']=='In1.Cu']);lost=F.discrete_keys(fg)-F.discrete_keys(new);gap=body.difference(nf);model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,z+[candidate],projected),protocol=5));(out/'proposed-zones.pkl').write_bytes(pickle.dumps([candidate],protocol=5));put(out/'whole-projection-ledger.json',retreat);sourceproof={'prior_source_keys_lost':[list(k)for k in sorted(lost)],'new_UV_source_reference_gap_mm2':gap.area,'FG_named_pads':len({q['uuid']for q in new if q['kind']=='pad'and q['pin']})};ok=not lost and gap.is_empty
 else:sourceproof=None;ok=False
 put(out/'receipt.json',{'verdict':'PHYSICAL_MONITOR_REFERENCE_PATCH_SOURCE_POSITIVE_FULL_GATES_OPEN'if ok else'NO_MONITOR_SOURCE_REFERENCE_PATCH_IN_DECLARED_FULL_FOREIGN_FILL_HARD_REGION','parent_sha256':sha(mp),'candidate_zone':candidate['uuid']if candidate else None,'model_sha256':sha(out/'model.pkl')if candidate else None,'target_legality_sha256':sha(out/'target-legality.json'),'attempts':attempts,'source_proof':sourceproof,'all_old_new_foreign_positive_fills_Cu_holes_hard':True,'no_old_native_outlines_Cu_or_holes_changed':True,'native_jobs':0,'adopted':False,'full76_contacts_reference_current_threshold_native_DRC':'OPEN'});print('R73_MONITOR_REFERENCE',ok,'legalbody',legal.covers(body),'blocked',len(obstacles),flush=True)
if __name__=='__main__':main()
