"""Find ordinary all-layer sites on actual existing CORE fill outside dense via escape walls."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for q in getattr(s,'geoms',[])for p in parts(q)]
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
class AuditedObstacles(list):
 def __init__(self):super().__init__();self.rows=[];self.family=None;self.meta={}
 def label(self,family,**meta):self.family=family;self.meta=meta
 def append(self,shape):
  assert self.family is not None
  super().append(shape);self.rows.append({'family':self.family,**self.meta,'shape':shape})
 def extend(self,shapes):
  for shape in shapes:self.append(shape)
 def audit(self,candidate,region,out,side,actual):
  from collections import defaultdict
  grouped=defaultdict(list)
  for row in self.rows:grouped[row['family']].append(row['shape'])
  unions={key:unary_union(values)for key,values in grouped.items()}
  stages=[];remaining=candidate
  for family,shape in unions.items():
   before=remaining;remaining=remaining.difference(shape)
   other=unary_union([sh for key,sh in unions.items()if key!=family])
   only=candidate.difference(shape);without=candidate.difference(other)
   (out/(side+'-family-'+family+'.wkb')).write_bytes(shape.wkb)
   stages.append({'family':family,'primitive_count':len(grouped[family]),'initial_candidate_intersection_mm2':candidate.intersection(shape).area,'candidate_area_after_this_family_alone_mm2':only.area,'remaining_after_ordered_family_mm2':remaining.area,'ordered_removed_area_mm2':before.difference(remaining).area,'candidate_area_without_this_family_mm2':without.area})
  ranks=[]
  for row in self.rows:
   area=candidate.intersection(row['shape']).area
   if area>0:ranks.append({k:v for k,v in row.items()if k!='shape'}|{'candidate_intersection_mm2':area})
  ranks.sort(key=lambda x:-x['candidate_intersection_mm2'])
  original=H/'CORE-ordinary-external-fill-port-nominations-r90'/(side+'-ordinary-site-region.wkb')
  assert original.exists();R90_original_region_WKB_equal=original.read_bytes()==region.wkb
  (out/(side+'-initial-candidate.wkb')).write_bytes(candidate.wkb)
  report={'side':side,'initial_source_fill_contained_candidate_area_mm2':candidate.area,'R90_initial_full_disk_containment_predicate_replaced_with_exact_annular_contact':True,'R90_original_final_region_WKB_equal_diagnostic':R90_original_region_WKB_equal,'final_legal_area_mm2':region.area,'families':stages,'largest_literal_blockers':ranks[:80],'attribution_only_no_predicate_or_geometry_changes':True}
  put(out/(side+'-blocker-attribution.json'),report)
  self.propose_IO3_antipad_ports(candidate,out,side,actual)
  print('R93_BLOCKERS',side,candidate.area,[(x['family'],round(x['candidate_area_after_this_family_alone_mm2'],6),round(x['candidate_area_without_this_family_mm2'],6))for x in stages],flush=True)

 def propose_IO3_antipad_ports(self,candidate,out,side,actual):
  allowed_UUID='54921f4b-0308-4821-9549-ff9360bf05ca'
  eligible=[r for r in self.rows if r['family']=='native_foreign_power_filled_Cu'and r.get('UUID')==allowed_UUID]
  assert eligible and all(r['raw_net']=='/IO_3V3'and r['layer']=='In2.Cu'for r in eligible)
  retained=[r['shape']for r in self.rows if r not in eligible]
  region=set_precision(candidate.difference(unary_union(retained)),1e-6)
  (out/(side+'-new-native-IO3-antipad-prospective-port-region.wkb')).write_bytes(region.wkb)
  proposals=[]
  nominees=parts(region)
  if side=='main':nominees=parts(region.intersection(box(174,92.5,181,100)))+nominees
  if side=='source':nominees=parts(region.intersection(box(226,92,233.5,101)))+nominees
  used=set()
  for face in sorted(nominees,key=lambda q:(0 if(side=='main'and q.bounds[0]>=174)or(side=='source'and q.bounds[2]<=233.5)else 1,-q.area))[:20]:
   point=face.representative_point();xy=[round(point.x,6),round(point.y,6)]
   if tuple(xy)in used or not region.covers(Point(xy)):continue
   used.add(tuple(xy));via={'x':xy[0],'y':xy[1]};ann=N.bounded_disk(via,.25).difference(N.bounded_disk(via,.1));finite_overlap=ann.intersection(actual).area
   if finite_overlap<.01:continue
   uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-CORE-partial-annular-antipad-r95/'+side+'/'+repr(xy)))
   proposals.append({'side':side,'via':{'uuid':uid,'net':'/CORE_1V2','x':xy[0],'y':xy[1],'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'prospective_not_native':True},'ordinary_site_face_area_mm2':face.area,'actual_existing_CORE_In3_annular_overlap_mm2':finite_overlap,'one_native_IO3_plane_exact_new_hole_and_annulus_antipad_required':allowed_UUID})
  (out/(side+'-prospective-new-ordinary-ports.pkl')).write_bytes(pickle.dumps(proposals,protocol=5))
  put(out/(side+'-antipad-site-proposal.json'),{'side':side,'prospective_new_ordinary_port_region_area_mm2':region.area,'proposals':proposals,'all_original_R90_guards_except_one_literal_IO3_native_filled_plane_remain_hard':True,'native_zone_original_outline_and_settings_unchanged':True,'required_new_antipad_predicate':'new CORE ordinary .5/.2 via, .15 same-domain Cu+.025 planning margin and >=.275 foreign-hole clearance; ALL old IO3 source/direct-layer-contact/shape/no-loss checks required','ordinary_native_flashes_all6': 'UNPROVEN','actual_CORE_In3_finite_annular_overlap':'EACH_NOMINEE_AT_LEAST_0_01_MM2_MEASURED_FROM_EXACT_ANNULUS','all77_contacts_all_original_discrete_IO3_fill_contacts_full_2A_IO3_and_0_8A_CORE_current_return_drop_thermal_native_DRC':'OPEN','no_native_or_board_written':True,'adopted':False})
  print('R95_PARTIAL_ANNULAR_IO3_ANTIPAD_NOMINEES',side,region.area,len(proposals),flush=True)

def main():
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';mp=parent/'model.pkl';assert sha(parent/'receipt.json')=='ec4a2744f502fc250ecf5f5e0e04c6e043dd7b5b1fe916419231163e4aafaf33'and sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';g,h,b,z,current=pickle.loads(mp.read_bytes());saved=pickle.loads((parent/'source-groups.pkl').read_bytes());source=root(saved['/CORE_1V2'],'L2001');main=next(xs for xs in saved['/CORE_1V2']if any(q['kind']=='pad'and q['ref']=='U1001'for q in xs));lground=root(saved['/LOGIC_GND'],'J11001');raw='/CORE_1V2';layer='In3.Cu';records,trees=F.build({**h,'zones':[]});out=H/'CORE-partial-annular-native-IO3-antipad-port-nominees-r95';assert not out.exists();out.mkdir();rows=[];proposals=[]
 local_ground=max(float(q['clearance_mm'])for q in h['zones']if C.norm(q['net'])=='/LOGIC_GND');reference_guard=.25+max(.15,local_ground)+.025+.000100
 for label,xs,window in[('main',main,box(170,92.5,181,100)),('source',source,box(226,89,241,101))]:
  search=window.buffer(2);actual=unary_union([q['shape']for q in xs if q['layer']==layer and q['kind']!='via']);candidate=set_precision(window.intersection(actual.buffer(.20)),1e-6);obs=AuditedObstacles()
  for l in('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'):
   for i in trees[l].query(search,predicate='intersects'):
    q=records[l][int(i)]
    if q['net']==raw:continue
    gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;guard=.25+gap+.025+.000100
    if q['kind']=='track':t=q['source'];sh=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+guard)
    elif q['kind']=='via':v=q['source'];sh=N.bounded_disk(v,v['d']/2+guard)
    else:sh=N.bounded_buffer(q['shape'],guard)
    obs.label("actual_foreign_discrete",layer=l,raw_net=q["net"],kind=q["kind"],UUID=q['uuid']);obs.append(sh)
  for q in z:
   if q['net']==raw or C.norm(q['net'])=='/LOGIC_GND' or not search.intersects(q['shape']):continue
   gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;obs.label('held_owned_foreign_power_planes',raw_net=q['net'],layer=q['layer'],UUID=q['uuid']);obs.append(N.bounded_buffer(q['zone_outline_shape'],.25+max(gap,float(q.get('clearance_mm',.15)))+.025+.000100))
  for native in current['zones']:
   if C.norm(native['net'])in('/CORE_1V2','/LOGIC_GND'):continue
   for native_layer,rings in native['fills'].items():
    for sh in C.poly(rings):
     if search.intersects(sh):obs.label('native_foreign_power_filled_Cu',raw_net=native['net'],layer=native_layer,UUID=native['uuid']);obs.append(N.bounded_buffer(sh,.25+(.15 if h['domains_normalized'][C.norm(native['net'])]==h['domains_normalized'][raw]else .6)+.025+.000100))
  for v in h['vias']:
   if search.intersects(Point(v['x'],v['y'])):obs.label('every_existing_drill',raw_net=v['net'],UUID=v['uuid']);obs.append(N.bounded_disk(v,v['drill']/2+.1+.275+.000100))
  for pad in h['pads']:
   for rings in pad['layers'].values():
    if pad.get('smd'):obs.label('source_SMD_hole_edge',raw_net=pad['net'],UUID=pad['uuid'],ref=pad['ref'],pin=pad['num']);obs.extend(N.bounded_buffer(sh,.1+.275+.000100)for sh in C.poly(rings)if search.intersects(sh))
   obs.label('source_plated_pad_hole_edge',raw_net=pad['net'],UUID=pad['uuid'],ref=pad['ref'],pin=pad['num']);obs.extend(N.bounded_buffer(sh,.1+.275+.000100)for sh in C.poly(pad.get('hole')or[])if search.intersects(sh))
  for rule in h['rule_areas']:
   if rule.get('no_vias')or rule.get('no_pads'):obs.label('native_via_pad_keepouts',UUID=rule.get('uuid'));obs.extend(N.bounded_buffer(sh,.25+.025+.000100)for sh in C.poly(rule['outline'])if search.intersects(sh))
  shadows=[]
  for outer,inner in[('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
   reference=unary_union([q['shape']for q in lground if q['kind']=='fill'and q['layer']==inner]).intersection(search)
   for t in h['tracks']:
    if t['layer']!=outer or C.norm(t['net'])=='/LOGIC_GND'or h['domains_normalized'][C.norm(t['net'])]!=h['domains_normalized']['/LOGIC_GND']:continue
    if max(t['a'][0],t['b'][0])<search.bounds[0]or min(t['a'][0],t['b'][0])>search.bounds[2]or max(t['a'][1],t['b'][1])<search.bounds[1]or min(t['a'][1],t['b'][1])>search.bounds[3]:continue
    covered=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2).intersection(reference)
    if not covered.is_empty:shadows.append(covered)
  if shadows:obs.label('actual_before_source_supported_old_reference_shadows');obs.append(N.bounded_buffer(unary_union(shadows),reference_guard))
  region=set_precision(candidate.difference(unary_union(obs)),1e-6);obs.audit(candidate,region,out,label,actual);(out/(label+'-ordinary-site-region.wkb')).write_bytes(region.wkb);sites=[]
  for face in sorted(parts(region),key=lambda x:-x.area)[:8]:
   p=face.representative_point();xy=[round(p.x,6),round(p.y,6)]
   if not region.covers(Point(xy)):continue
   uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-CORE-external-fill-r90/'+label+'/'+repr(xy)));v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'prospective_not_native':True};ann=N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1));overlap=ann.intersection(actual).area
   if overlap<.01:continue
   sites.append({'via':v,'actual_existing_CORE_In3_annular_Cu_overlap_mm2':overlap,'site_face_area_mm2':face.area});proposals.append({'side':label,'via':v,'actual_Cu_overlap_mm2':overlap})
  rows.append({'side':label,'legal_site_area_mm2':region.area,'sites':sites,'all6_actual_foreign_Cu_all_held_planes_all_source_SMDs_every_drill_native_keepouts_hard':True,'actual_old_F_In1_B_In4_body_shadows_guard_mm':reference_guard});put(out/'checkpoint.json',rows);print('R90_EXTERNAL_PORTS',label,region.area,len(sites),flush=True)
 (out/'prospective-new-ordinary-ports.pkl').write_bytes(pickle.dumps(proposals,protocol=5));put(out/'receipt.json',{'verdict':'PARTIAL_FINITE_ANNULAR_CONTACT_ORDINARY_PORT_PROPOSALS_ONLY','parent_model_sha256':sha(mp),'sides':rows,'prospective_ports_sha256':sha(out/'prospective-new-ordinary-ports.pkl'),'required_new_ordinary_barrels_diameter_drill_mm':[.5,.2],'full_fitted_CORE1V2_load_A':.8,'no_old_barrel_unsuppression_or_native_Cu_pad_hole_outline_edits':True,'selected_pair_layer_feed_all77_contacts_full_source_current_return_drop_thermal_stability_native_DRC':'OPEN','new_initial_candidate_uses_annular_overlap_instead_of_whole_disk_containment':True,'all_clearance_hole_keepout_oldreference_predicates_unchanged':True,'blocker_attributions_files':['main-blocker-attribution.json','source-blocker-attribution.json'],'no_site_region_is_proof_of_global_no_path':True,'native_jobs':0,'adopted':False});print('R95_PARTIAL_ANNULAR_IO3_ANTIPAD_PORT_PROPOSALS_FROZEN',sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
