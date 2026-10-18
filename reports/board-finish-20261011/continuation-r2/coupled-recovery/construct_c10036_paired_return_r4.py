"""Qualify inherited gate transition with an exact ordinary rooted return."""
import sys,json,pickle,math,copy,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import audit_ao1_positive_operation_r4 as Q
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
GROUND='/motherboard_do/FIELD_B_0V';GATE='/motherboard_do/DO12_RCB_GATE';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for q in sh.geoms for p in vertices(q)]
def main():
 started=time.monotonic();out=HERE/'c10036-coupled-paired-return-recipe-r4.json';assert not out.exists()
 priorpath=HERE/'c10036-coupled-wall-exact-recipe-r2.json';prior=json.loads(A.read(priorpath));assert C.sha(A.read(priorpath))=='1c10f6d5e79727bfc49d19d77ee1a73fd0532c7aace5f05d271c567e3873810f'
 auditpath=HERE/'c10036-exact-operation-independent-r3.json';audit=json.loads(A.read(auditpath));assert C.sha(A.read(auditpath))=='4f71a988497afbc6c49d14855b1d7ba8645e404045917159210a13e5977567ff';assert len(audit['new_reference_errors'])==1
 for key in('clearance_errors','surviving_contact_losses','native_gate_pad_relationship_losses','unchanged_neighbor_reference_losses'):assert not audit[key],key
 for p,pin in prior['read_files_sha256'].items():assert C.sha(Path(p).read_bytes())==pin,p
 rp=FP/'local-and-b5-return-audit-r25';g=pickle.loads(A.read(rp/'geometry.pkl'));zones=pickle.loads(A.read(rp/'proposed-zones.pkl'));gg=pickle.loads(A.read(rp/'groups.pkl'));root=next(xs for xs in gg[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));v=next(v for v in g['vias'] if v['uuid']=='40bdf2f9-776c-4aa5-bca6-7921f7c90b54');assert(v['x'],v['y'],v['d'],v['drill'],L.norm(v['net']))==(66.55,95.35,.6,.3,GATE)
 native=json.loads(A.read(HERE.parent/'native-198b-geometry/geometry.json'));nv=next(q for q in native['vias'] if q['uuid']==v['uuid']);assert(nv['at'],nv['w'],nv['drill'],nv['net'])==([66.55,95.35],.6,.3,v['net']);flashes=json.loads(A.read(HERE.parent/'native-198b-geometry/actual-via-flashes.json'))['vias'];assert set(flashes[v['uuid']])==set(v['flashed'])==set(LAYERS)
 source=A.read(Path(prior['source_parent']));identity=N.SourceNets(source);parsed={u:G.parse(u,ch.encode(),{}) for u,ch in prior['exact_new_chunks'].items()};removed=set(prior['removed_source_UUIDs']);addedvia=next(q for q in parsed.values() if q['kind']=='via');holes=[Point(w['x'],w['y']).buffer(w['drill']/2,quad_segs=128) for w in g['vias']]+[sh for p in g['pads'] for sh in L.poly(p.get('hole') or [])]+[Point(addedvia['at']).buffer(.1,quad_segs=128)];ht=STRtree(holes)
 planes={}
 for l in('In1.Cu','In4.Cu'):
  sh=unary_union([r['shape'] for r in root if r['kind']=='fill' and r['layer']==l]);sh=sh.difference(unary_union([holes[int(i)] for i in ht.query(sh,predicate='intersects')]));planes[l]=sh
 relevant=[]
 for r in root:
  if r['kind']!='fill' or r['layer']!='In1.Cu' or r['shape'].distance(Point(v['x'],v['y']).buffer(.3))>.4:continue
  z=next(z for z in g['zones'] if z['uuid']==r['uuid']);relevant.append({'zone_uuid':z['uuid'],'local_clearance_mm':float(z['clearance_mm']),'prospective_not_native':bool(z.get('prospective_not_native'))})
 local=max([.15]+[z['local_clearance_mm'] for z in relevant]);radius=.3+local+.025
 t=parsed[audit['new_reference_errors'][0]['uuid']];body=A.shape(t);gap=body.difference(planes['In1.Cu']);maximum=max(math.dist(p[:2],(v['x'],v['y'])) for p in vertices(gap));assert abs(gap.area-audit['new_reference_errors'][0]['full_body_uncovered_mm2'])<1e-8,(gap.area,audit['new_reference_errors'][0]);assert maximum<=radius,(maximum,radius)
 discrete={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};rec,trees=F.build({**discrete,'zones':[]});extra=[]
 for z in parsed.values():
  ls=LAYERS if z['kind']=='via' else[z['layer']]
  for l in ls:extra.append({'net':z['net'],'layer':l,'shape':A.shape(z),'uuid':z['uuid']})
 smd=[sh for p in g['pads'] if p['smd'] for l,ps in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(ps)];st=STRtree(smd);padholes=[sh for p in g['pads'] for sh in L.poly(p.get('hole') or [])];ptree=STRtree(padholes);points=[Point(w['x'],w['y']) for w in g['vias']]+[Point(addedvia['at'])];vt=STRtree(points);outline=unary_union(L.poly(g['outline'])).buffer(-.526)
 res,exempt=A.reservations();sites=[(66.55,94.45)]+[(round(66.55+r*math.cos(k*math.pi/32),6),round(95.35+r*math.sin(k*math.pi/32),6)) for r in(.85,.9,.95,1.) for k in range(64)];chosen=None;attempts=[]
 def dg(other):return .15 if g['domains_normalized'].get(L.norm(other))==g['domains_normalized'][GROUND] else .6
 for xy in sites:
  p=Point(xy);disk=p.buffer(.25,quad_segs=128);hole=p.buffer(.1,quad_segs=128);bad=[]
  if not outline.covers(disk):bad.append('outline')
  smdgap=p.distance(smd[int(st.nearest(p))])-.1-.005
  if smdgap<.275:bad.append('SMD')
  for i in ptree.query(p.buffer(.7),predicate='intersects'):
   if p.distance(padholes[int(i)])-.1-.005<.275:bad.append('pad drill')
  for i in vt.query(p.buffer(1.2),predicate='intersects'):
   if p.distance(points[int(i)])<.81:bad.append('ordinary pitch')
  for l in LAYERS:
   for i in trees[l].query(disk.buffer(.7),predicate='intersects'):
    q=rec[l][int(i)]
    if L.norm(q['net'])!=GROUND and disk.distance(q['shape'])<dg(q['net'])+.025-1e-8:bad.append('discrete '+q['uuid'])
   for q in zones+extra:
    if q['layer']==l and L.norm(q['net'])!=GROUND and disk.distance(q['shape'])<dg(q['net'])+.025-1e-8:bad.append('prospective '+q['uuid'])
   for rule in g['rule_areas']:
    if rule.get('no_vias') and l in rule['layers'] and any(disk.distance(sh)<.025 for sh in L.poly(rule['outline'])):bad.append('rule '+rule['uuid'])
   for rule in res['keepouts']:
    if GROUND not in exempt.get(rule['name'],set()) and l in rule['layers'] and any(disk.distance(sh)<.025 for sh in L.poly(rule['outline'])):bad.append('reserve '+rule['name'])
  finalplanes={l:sh.difference(hole) for l,sh in planes.items()};ann=disk.difference(hole);areas={l:sh.buffer(-.075).intersection(ann).area for l,sh in finalplanes.items()};dist=math.dist(xy,(v['x'],v['y']));row={'at_mm':xy,'source_gate_distance_mm':dist,'guarded_SMD_hole_edge_mm':smdgap,'finite_source_rooted_annular_interior_mm2':areas,'violations':sorted(set(bad))};attempts.append(row)
  if not bad and .81<=dist<=1. and all(a>=.004 for a in areas.values()):chosen=row;break
 if not chosen:
  out.write_text(json.dumps({'verdict':'NO_RETURN_NOMINATION','sites':attempts,'source_transition_disk_proof':{'radius':radius,'maximum_gap_vertex_radius':maximum}},indent=1)+'\n');print('NO_RETURN',flush=True);return
 u,ch=Q.serial_via(identity,GROUND,chosen['at_mm']);new=dict(prior['exact_new_chunks']);assert u not in new;new[u]=ch.decode()
 report={**prior,'schema':'C10036-coupled-qualified-inherited-transition-r4','verdict':'EXACT_FIVE_DELETE_SIX_ADD_PAIRED_RETURN_RECIPE_FULL_INDEPENDENT_AUDIT_PENDING','exact_new_chunks':new,'new_items':prior['new_items']+[{'uuid':u,'kind':'via','raw_net':identity.raw(GROUND),'at_mm':chosen['at_mm'],'diameter_mm':.5,'drill_mm':.2,'role':'Inherited-DO12-gate-source-rooted-paired-return'}],'prior_r2_recipe_sha256':C.sha(A.read(priorpath)),'prior_full_independent_r3_sha256':C.sha(A.read(auditpath)),'inherited_actual_transition':{'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'actual_flash_layers':flashes[v['uuid']],'exact_local_reference_zone_clearances':relevant,'native_source_own_transition_disk_radius_mm':radius,'gap_area_mm2':gap.area,'maximum_gap_vertex_radius_mm':maximum,'all_gap_vertices_edges_and_interior_inside_exact_convex_disk':True,'radius_expansion_mm':0,'paired_return':chosen},'new_return_UUID':u,'return_nomination_attempts':attempts,'read_files_sha256':A.READS,'board_emitted':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'return':chosen,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
