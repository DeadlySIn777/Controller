"""Explicit positive native-intent corner only; actual physical/source geometry exact."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,copy,re,time
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import fast_contacts as F
import restore_field_current_mixed_precision_states_r366 as MS
from emit_logic_zones_r1 import render
from verify_source import parse,children,child,atom
M=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/model.pkl'
P=M.with_name('only-four-current-member-to-qualified-direction-union-operation-candidates.pkl')
N=H/'R645-B3-one-native-IU-positive-intended-corner-enclosure-nomination-r679'
D=ROOT/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
OUT=H/'R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r683'
KEYS=('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def obj(x):return hashlib.sha256(pickle.dumps(x,protocol=5)).hexdigest()
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(name,s):
 f=OUT/(name+'.wkb');f.write_bytes(s.wkb);return {'file':str(f.resolve()),**ds(s)}
def main():
 assert not OUT.exists();OUT.mkdir();start=time.monotonic()
 assert sha(M)=='7141d6d37a909617aa339dadfc3b8a1b539904af1b06b2bf8f00ea2abeee69f9'
 assert sha(P)=='6fa00a4fa7f7cce7025d7574b28a6f2b26e7820d63b124df6bdcdaa1f974b766'
 assert sha(N/'receipt.json')=='4399aee896f10f68fa033b445d1eff2cdcb495c4025c54db99834cec04e1bd1f'
 nf=N/'only-one-owned-B3-intended-corner-positive-proposal-NOT_MODEL.pkl';assert sha(nf)=='00b7660081aff794b976a8a95e68b0fdba31c72871ee99d83e50a6faee0c9d18'
 proposal=pickle.loads(nf.read_bytes());g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 snap={k:obj(v)for k,v in [('g',g),('h',h),('actual_candidate',c)]};uid=proposal['exact_before_q']['uuid'];old=next(a for a in q if a['uuid']==uid);assert old==proposal['exact_before_q']
 new=copy.deepcopy(proposal['exact_after_q_NOT_ADOPTED']);new['zone_outline_shape']=set_precision(new['zone_outline_shape'],1e-6,mode='pointwise')
 before=zero(old['zone_outline_shape']);after=zero(new['zone_outline_shape']);physical=zero(old['shape']);gain=after.difference(before);loss=before.difference(after);excess=physical.difference(after)
 assert loss.is_empty and excess.is_empty and not gain.is_empty and after.is_valid
 assert {k:v for k,v in new.items()if k!='zone_outline_shape'}=={k:v for k,v in old.items()if k!='zone_outline_shape'}
 assert {k:new[k]for k in KEYS}=={k:old[k]for k in KEYS}=={'priority':124,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3}
 pv=(84.643271,125.496937);ov=(85.304972,125.334335);nv=(85.304971,125.334336);nx=(86.843612,125.423508)
 triangles=[Polygon([pv,ov,nv]),Polygon([ov,nx,nv])]
 declared=unary_union(triangles);fan=[save('declared-positive-triangle-'+str(i),t)for i,t in enumerate(triangles)]
 fan_extra=gain.difference(declared);fan_missing=declared.difference(gain)
 # Raw exact union comparisons remain visible; the integer half-plane authority is also pinned.
 fanproof={'triangle_rows':fan,'exact_integer_triangle_areas_IU2':[249549.5,813906.5],'actual_positive_gain':save('explicit-added-native-intended-Cu',gain),'raw_gain_outside_declared_triangles':save('raw-added-outside-declared-triangle-fan',fan_extra),'raw_declared_triangles_not_in_gain':save('raw-declared-triangle-fan-missing-from-gain',fan_missing)}
 finalq=[new if a['uuid']==uid else a for a in q];rec,trees=F.build({**h,'zones':[]});checks=[];errors=[];dom=h['domains_normalized'];ly=new['layer'];net=new['net'];nativegap=lambda raw:.15 if dom[L.norm(raw)]==dom[L.norm(net)]else .6
 for j in trees[ly].query(gain.buffer(.85),predicate='intersects'):
  r=rec[ly][int(j)]
  if r['net']==net:continue
  if r['kind']=='via':v=r['source'];distance=Point(v['x'],v['y']).distance(gain)-v['d']/2
  elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];distance=LineString([t['a'],t['b']]).distance(gain)-t['w']/2
  else:distance=zero(r['shape']).distance(gain)
  row={'kind':'ADDED_INTENDED_TRUE_'+r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'actual_gap_mm':distance,'native_required_mm':nativegap(r['net']),'planner_required_mm':nativegap(r['net'])+.025};checks.append(row)
  if distance<row['planner_required_mm']:errors.append(row)
 for z in c['zones']:
  if z['net']==net or ly not in z['fills']:continue
  body=unary_union(L.poly(z['fills'][ly]))
  if body.is_empty:continue
  distance=body.distance(gain)
  if distance>.85:continue
  req=max(float(z['clearance_mm']),nativegap(z['net']),.15)+.025;row={'kind':'ADDED_INTENDED_ACTUAL_FOREIGN_FILLED_Cu','UUID':z['uuid'],'raw_net':z['net'],'actual_gap_mm':distance,'planner_required_mm':req};checks.append(row)
  if distance<req:errors.append(row)
 overlaps=[]
 for z in finalq:
  if z['uuid']==uid or z['layer']!=ly:continue
  hit=after.intersection(zero(z['zone_outline_shape']))
  if not hit.is_empty:overlaps.append({'other_UUID':z['uuid'],'other_raw_net':z['net'],'actual_intended_intersection':save('new-intended-intersection-'+z['uuid'],hit),'same_nine_settings':all(z.get(k)==new[k]for k in KEYS)})
  if z['net']==net:continue
  for role in ('shape','zone_outline_shape'):
   distance=zero(z[role]).distance(gain)
   if distance>.85:continue
   req=max(float(z['clearance_mm']),nativegap(z['net']),.15)+.025;row={'kind':'ADDED_INTENDED_OWNED_FOREIGN_'+role,'UUID':z['uuid'],'raw_net':z['net'],'actual_gap_mm':distance,'planner_required_mm':req};checks.append(row)
   if distance<req:errors.append(row)
 rules=[]
 for name,cond,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',D.read_text(encoding='utf-8')):
  if 'zone'not in what.split():continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",cond);assert len(names)==1;area=next(a for a in h['rule_areas']if a.get('name')==names[0]);rules.append((name,area,re.findall(r"A.NetName != '([^']+)'",cond)))
 rules.extend((a.get('name',a['uuid']),a,[])for a in h['rule_areas']if a.get('no_zones'));nozone=[]
 for name,area,exempt in rules:
  if ly not in area['layers']or net in exempt:continue
  ar=unary_union(L.poly(area['outline']))
  for role in ('shape','zone_outline_shape'):
   hit=zero(new[role]).intersection(ar)
   if not hit.is_empty:nozone.append({'UUID':uid,'role':role,'rule':name,**save('nozone-'+role+'-'+area['uuid'],hit)})
 holes=[]
 for v in c['vias']:
  if v['net']!=net or ly not in v['layers']:continue
  centre=Point(v['x'],v['y']);a=before.covers(centre);z=after.covers(centre)
  holes.append({'via_UUID':v['uuid'],'native_before_centre_in_intended':a,'native_after_centre_in_intended':z,'membership_changed':a!=z,'centre_in_explicit_intended_hole_before':any(Polygon(r).covers(centre)for p in(before.geoms if before.geom_type=='MultiPolygon'else[before])for r in p.interiors),'centre_in_explicit_intended_hole_after':any(Polygon(r).covers(centre)for p in(after.geoms if after.geom_type=='MultiPolygon'else[after])for r in p.interiors)})
 # Physically identical tuple permits exact prior source/contact/reference receipt reuse, never native effect credit.
 assert snap=={k:obj(v)for k,v in [('g',g),('h',h),('actual_candidate',c)]}
 assert all(hs(a['shape'])==hs(next(v for v in finalq if v['uuid']==a['uuid'])['shape'])for a in q)
 for a in finalq:
  if a['uuid']!=uid:assert a==next(v for v in q if v['uuid']==a['uuid'])
 geometry_identity={'g_full_object_SHA256':snap['g'],'h_full_native_header_discrete_pads_vias_holes_FP_object_SHA256':snap['h'],'actual_candidate_full_filled_arrays_discrete_object_SHA256':snap['actual_candidate'],'all_40_actual_physical_role_WKB_exact':True,'all_other_39_intended_roles_WKB_profiles_exact':True,'all_actual_source_filled_arrays_original_header_holes_NATIVE_exact':True,'only_changed_role':[uid,'zone_outline_shape'],'no_native_added_triangle_fill_credit':True}
 original_packet=pickle.loads(P.read_bytes());assert original_packet[1]['new_q']==old;fullpacket=copy.deepcopy(original_packet);fullpacket[1]['new_q']=new;assert fullpacket[1]['new_actual_zone']==original_packet[1]['new_actual_zone'];fullfile=OUT/'only-four-current-qualified-unions-with-one-positive-B3-native-intent-corner.pkl';fullfile.write_bytes(pickle.dumps(fullpacket,protocol=5))
 rolefile=OUT/'only-one-owned-B3-positive-native-intended-role-exact-before-after-operation.pkl';rolefile.write_bytes(pickle.dumps({'owner_UUID':uid,'role':'zone_outline_shape','exact_before_q':old,'exact_after_q':new,'explicit_positive_intended_Cu':gain,'exact_integer_changed_vertex':[[85304972,125334335],[85304971,125334336]],'all_other_vertex_tokens_exact':True,'physical_and_actual_filled_candidate_UNCHANGED':True,'parent_sparse_four_cluster_packet_SHA256':sha(P),'actual_identity':geometry_identity,'raw_x_only_and_R681_rejections_preserved':True},protocol=5))
 put(OUT/'declared-positive-intended-two-triangle-fan-and-raw-differences.json',fanproof);put(OUT/'new-intended-corner-true-foreign-copper-guard-checks.json',checks);put(OUT/'new-intended-corner-true-guard-errors.json',errors);put(OUT/'whole-B3-both-role-native-no-zone-errors.json',nozone);put(OUT/'new-intended-interzone-actual-intersection-errors.json',overlaps);put(OUT/'all-same-raw-existing-via-intended-centre-and-holes-identity.json',holes);put(OUT/'actual-full-physical-header-fill-holes-identity-certificate.json',geometry_identity)
 binding=copy.deepcopy(b);binding['generated_precision_state_ledger']=[{**r,'unchanged_WKB_SHA256':hs(new['zone_outline_shape'])}if r['new_generated_UUID']==uid and r['role']=='zone_outline_shape'else r for r in binding['generated_precision_state_ledger']];binding['owned_B3_native_intended_positive_corner_r683']={'role_operation_file':str(rolefile.resolve()),'role_operation_SHA256':sha(rolefile),'only_positive_intended_scope_no_physical_effect':True,'prior_R645_actual_source_contact_reference_receipt_file':str(H/'four-direction-unions-corrected-corners-actual-source-contact-reference-r645/receipt.json'),'prior_R645_actual_source_contact_reference_receipt_SHA256':'a290ae014dc4844446ad9ae392f3d3c86f36b98eb1a9e87d2e7a1feaa3cfa064','complete_actual_geometry_identity_file':str(OUT/'actual-full-physical-header-fill-holes-identity-certificate.json'),'complete_actual_geometry_identity_SHA256':sha(OUT/'actual-full-physical-header-fill-holes-identity-certificate.json')};MS.restore_bound_field_current_precision_states(binding,finalq)
 text=render(uid,net,ly,new['zone_outline_shape']).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Exact current B3 union positive native intent corner');ast=parse(text);assert atom(ast,'net')==net
 rings=[[[int(round(float(x[1])*1e6)),int(round(float(x[2])*1e6))]for x in child(pp,'pts')[1:]]for pp in children(ast,'polygon')];expected=[[[int(round(x*1e6)),int(round(y*1e6))]for x,y in r.coords[:-1]]for pp in(new['zone_outline_shape'].geoms if new['zone_outline_shape'].geom_type=='MultiPolygon'else[new['zone_outline_shape']])for r in(pp.exterior,*pp.interiors)];assert rings==expected
 chunk=OUT/(uid+'.zone-chunk');chunk.write_text(text,encoding='utf-8',newline='');put(OUT/'native-owner-profile-and-exact-IU-chunk-row.json',{'UUID':uid,'raw_net':net,'layer':ly,'all_current_declared_native_profile_fields':{k:new[k]for k in KEYS},'chunk_file':str(chunk.resolve()),'chunk_SHA256':sha(chunk),'exact_ring_coordinate_arrays_IU':rings,'native_API_and_refill':'OPEN_NO_NATIVE_LAUNCH'})
 failures=errors+nozone+overlaps;mp=OUT/'model.pkl';mp.write_bytes(pickle.dumps((g,h,binding,finalq,c),protocol=5));status='HOST_NATIVE_INTENT_CORNER_GUARD_OR_INTERSECTION_REPAIR_REQUIRED'if failures else'HOST_POSITIVE_INTENDED_CORNER_GUARDS_ENCLOSURE_PROFILE_PASS_ACTUAL_R645_IDENTITY_REBOUND_NATIVE_OPEN'
 put(OUT/'receipt.json',{'status':status,'parent_model_SHA256':sha(M),'parent_R645_source_contact_reference_receipt_SHA256':binding['owned_B3_native_intended_positive_corner_r683']['prior_R645_actual_source_contact_reference_receipt_SHA256'],'nominee_R679_SHA256':sha(N/'receipt.json'),'model_SHA256':sha(mp),'only_native_intended_role_operation_SHA256':sha(rolefile),'updated_four_cluster_sparse_operation_packet_SHA256':sha(fullfile),'one_new_native_intended_chunk_SHA256':sha(chunk),'explicit_one_IU_y_positive_extension_and_minus_one_IU_x':[[85304972,125334335],[85304971,125334336]],'positive_intended_added_area_mm2':gain.area,'literal_old_intended_loss_EMPTY':loss.is_empty,'literal_whole_physical_outside_corrected_intent_EMPTY':excess.is_empty,'true_foreign_native_and_peer_Cu_check_count':len(checks),'true_guard_error_count':len(errors),'whole_B3_both_roles_native_nozone_error_count':len(nozone),'actual_intended_interzone_intersection_count':len(overlaps),'explicit_triangle_fan_raw_scope_extra_EMPTY':fan_extra.is_empty,'explicit_triangle_fan_raw_scope_missing_EMPTY':fan_missing.is_empty,'complete_physical_header_holes_actual_fill_identity':geometry_identity,'all_R645_actual_source_contact_reference_tests_rebound_by_EXACT_COMPLETE_IDENTITY':not failures,'native_fill_source_CAPACITY_current_LOOP_thermal_SI_effect':'OPEN; intended-only additive Cu may only gain fill after actual native validation','inherited_R645_raw_DC_body_current_and_all_other_native_failure_ledgers_retained':True,'x_only_partly_negative_and_R681_selfintersection_rejections_preserved':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R683_COMPLETE',status,sha(OUT/'receipt.json'),'guardErrors',len(errors),'nozone',len(nozone),'overlaps',len(overlaps),'fan',fan_extra.is_empty,fan_missing.is_empty,flush=True)
if __name__=='__main__':main()
