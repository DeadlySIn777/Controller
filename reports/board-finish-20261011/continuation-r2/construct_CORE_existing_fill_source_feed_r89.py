"""Use finite existing same-net fill contacts, preserving all retained connections as later gates."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
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
 if s.geom_type=='Polygon':return[s]
 return[p for q in getattr(s,'geoms',[])for p in parts(q)]
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
def main():
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';assert sha(parent/'receipt.json')=='ec4a2744f502fc250ecf5f5e0e04c6e043dd7b5b1fe916419231163e4aafaf33';mp=parent/'model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';g,h,b,z,current=pickle.loads(mp.read_bytes());replay=PS.restore_bound_generated_precision_states(b,z);saved=pickle.loads((parent/'source-groups.pkl').read_bytes());source=root(saved['/CORE_1V2'],'L2001');target=next(xs for xs in saved['/CORE_1V2']if any(q['kind']=='pad'and q['ref']=='U1001'for q in xs));need={q['uuid']for q in target if q['kind']=='pad'and q['pin']};assert len(need)==21;raw='/CORE_1V2';layer='In3.Cu';cuttable='47888e35-9a96-5393-b579-7c0b4a64ec93';source_Cu=unary_union([q['shape']for q in source if q['layer']==layer and q['kind']!='via']);target_Cu=unary_union([q['shape']for q in target if q['layer']==layer and q['kind']!='via']);assert source_Cu.area>1 and target_Cu.area>1
 out=H/'CORE-existing-fill-source-feed-r89';assert not out.exists();out.mkdir();put(out/'exact-parent-operation-replay.json',replay);(out/'actual-existing-source-Cu.wkb').write_bytes(source_Cu.wkb);(out/'actual-existing-target-Cu.wkb').write_bytes(target_Cu.wkb);records,trees=F.build({**h,'zones':[]});windows=[box(145,72,250,125),box(130,50,255,150)];attempts=[];candidate=None;record=None
 for wi,window in enumerate(windows):
  search=window.buffer(2);obs=[]
  for i in trees[layer].query(search,predicate='intersects'):
   q=records[layer][int(i)]
   if q['net']==raw:continue
   guard=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6)+.025+.000100
   if q['kind']=='track':t=q['source'];sh=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+guard)
   elif q['kind']=='via':v=q['source'];sh=N.bounded_disk(v,v['d']/2+guard)
   else:sh=N.bounded_buffer(q['shape'],guard)
   obs.append(sh)
  for q in z:
   if q['layer']==layer and q['net']!=raw and q['uuid']!=cuttable and search.intersects(q['shape']):obs.append(N.bounded_buffer(q['zone_outline_shape'],max(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6,float(q.get('clearance_mm',.15)))+.025+.000100))
  # Actual old non-ground foreign power fills stay hard. Original ground outlines stay exact,
  # while projected same-domain ground fill retreat remains subject to ALL77/source/reference gates.
  for nz in current['zones']:
   if C.norm(nz['net'])in('/CORE_1V2','/LOGIC_GND'):continue
   for sh in C.poly(nz['fills'].get(layer,[])):
    if search.intersects(sh):obs.append(N.bounded_buffer(sh,(.15 if h['domains_normalized'][C.norm(nz['net'])]==h['domains_normalized'][raw]else .6)+.025+.000100))
  for v in h['vias']:
   if v['net']!=raw and search.intersects(Point(v['x'],v['y'])):obs.append(N.bounded_disk(v,v['drill']/2+.275+.000100))
  for p in h['pads']:
   if p['net']!=raw:obs.extend(N.bounded_buffer(sh,.275+.000100)for sh in C.poly(p.get('hole')or[])if search.intersects(sh))
  for rule in h['rule_areas']:
   if rule.get('no_zones')and layer in rule['layers']:obs.extend(N.bounded_buffer(sh,.025+.000100)for sh in C.poly(rule['outline'])if search.intersects(sh))
  legal=set_precision(window.intersection(unary_union(C.poly(h['outline'])).buffer(-.526)).difference(unary_union(obs)),1e-6);(out/('window-'+str(wi)+'-legal.wkb')).write_bytes(legal.wkb);print('R89_LEGAL_WINDOW',wi,'source',legal.intersection(source_Cu).area,'target',legal.intersection(target_Cu).area,flush=True)
  for width in(4.,3.,2.,1.,.5,.35,.25):
   faces=parts(legal.buffer(-width/2-.000100));common=[]
   for face in faces:
    aa=face.intersection(target_Cu);bb=face.intersection(source_Cu)
    if aa.area>.01 and bb.area>.01:common.append((aa.distance(bb),face,aa,bb))
   attempts.append({'window':wi,'width_mm':width,'common_existing_source_and_target_fill_faces':len(common)});put(out/'route-face-checkpoint.json',attempts)
   for dist,face,aa,bb in sorted(common,key=lambda x:x[0]):
    if get_num_coordinates(face)>5000:
     conservative=face.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(face);eligible=[sh for sh in parts(conservative)if sh.intersection(aa).area>.01 and sh.intersection(bb).area>.01]
     if not eligible:continue
     face=max(eligible,key=lambda x:x.area);aa=face.intersection(aa);bb=face.intersection(bb)
    a,end=nearest_points(aa,bb);print('R89_EXISTING_FILL_PATH',wi,width,dist,get_num_coordinates(face),flush=True)
    try:points,proof=T.route(face,tuple(a.coords[0]),tuple(end.coords[0]))
    except(AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)]for x,y in points];line=LineString(points)
    if not face.covers(line):continue
    core=N.bounded_buffer(line,width/2)
    if not legal.covers(core):continue
    native=set_precision(unary_union([sh for sh in parts(N.bounded_buffer(line,max(.6,width)).intersection(legal))if sh.intersection(core).area>0]),1e-6);ownholes=unary_union([N.bounded_disk(v,v['drill']/2)for v in h['vias']if v['net']==raw]+[sh for p in h['pads']if p['net']==raw for sh in C.poly(p.get('hole')or[])]);physical=native.difference(ownholes)
    if physical.intersection(source_Cu).area<.01 or physical.intersection(target_Cu).area<.01:continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-existing-core-fill-source-r89/'+repr(points)));candidate={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'min_thickness_mm':.15,'priority':124,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'physical_Cu_drill_subtracted':True,'label':'Actual existing CORE In3 source to main fill R89'};record={'width_core_mm':width,'length_mm':line.length,'points':points,'existing_source_Cu_overlap_mm2':physical.intersection(source_Cu).area,'existing_target_Cu_overlap_mm2':physical.intersection(target_Cu).area,'route_constructor':proof};break
   if candidate:break
  if candidate:break
 if candidate:
  cutter=N.bounded_buffer(candidate['shape'],.175+.000100);newz=[];cuts=[]
  for q in z:
   if q['uuid']!=cuttable:newz.append(q);continue
   n=copy.deepcopy(q);n['shape']=q['shape'].difference(cutter);n['zone_outline_shape']=q['zone_outline_shape'].difference(cutter);assert n['shape'].difference(q['shape']).is_empty and not n['shape'].is_empty;cuts.append({'UUID':q['uuid'],'physical_removed_mm2':q['shape'].difference(n['shape']).area,'physical_added_mm2':0.,'before_WKB_sha256':digest(q['shape']),'after_WKB_sha256':digest(n['shape'])});newz.append(n)
  assert len(cuts)==1;put(out/'new-owned-LG-In3-remove-only-ledger.json',cuts);(out/'proposed-zones.pkl').write_bytes(pickle.dumps([candidate],protocol=5));current,retreat=N.projected(g,h,newz+[candidate]);put(out/'full-projection-ledger.json',retreat);after=root(F.graph(current,raw),'L2001');joined={q['uuid']for q in after if q['kind']=='pad'and q['pin']};keys=F.discrete_keys(source)-F.discrete_keys(after);sourceproof={'all21_target_pads_joined':need<=joined,'prior_source_keys_lost':[list(k)for k in sorted(keys)],'source_named_pads':len(joined)};model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,newz+[candidate],current),protocol=5));ok=need<=joined and not keys
 else:sourceproof=None;ok=False
 put(out/'receipt.json',{'verdict':'EXISTING_CORE_FILL_FEED_SOURCE_POSITIVE_FULL_GATES_OPEN'if ok else'NO_ACCEPTED_EXISTING_CORE_FILL_FEED_IN_DECLARED_WINDOWS','model_sha256':sha(out/'model.pkl')if candidate else None,'parent_model_sha256':sha(mp),'route':record,'source_proof':sourceproof,'candidate_UUID':candidate['uuid']if candidate else None,'no_new_holes_or_old_native_barrel_pad_pose_mask_Cu_or_outline_edits':True,'full_fitted_CORE1V2_load_A':.8,'all77_other_contacts_five_sources_oldreferences_truegeometry_current_mesh_drop_return_stability_thermal_native':'OPEN','generated_precision_ledger_after_new_geometry_requires_rebind':True,'original104_PDN_proposal_and_raw_reference_FAIL_preserved':True,'native_jobs':0,'adopted':False});print('R89_EXISTING_FILL_FEED',ok,sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
