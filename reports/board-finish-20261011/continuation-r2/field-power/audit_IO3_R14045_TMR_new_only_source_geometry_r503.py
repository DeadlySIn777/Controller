"""Independent actual drilled source, true cap and native no-zone checks.

Only a new IO3 In2 region was added after exact FA/IO3 forbidden-area cuts;
no ground or original fill is projected again. Native same-net union/current
gates remain explicit until a separate minimal successor is qualified.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,re,time
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MS
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
M=H/'IO3-R14045-new-only-existing-barrel-TMR-materialization-r501/model.pkl'
P=H/'R155-FA-plus-IO3-TMR-individual-local-scope-witnesses-r491/model.pkl'
S=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
D=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
O=H/'IO3-R14045-new-only-TMR-bypass-independent-source-geometry-r503'
NET='/IO_3V3';UID='a7168f4b-192a-52fe-a025-456a10753a51'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def summary(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'WKB_SHA256':dg(s)}
def main():
 assert not O.exists();O.mkdir();start=time.monotonic()
 assert sha(M)=='4085476528750a14f77b9d9c78a75c10914522a82932b38991f35241b7c77bd3';assert sha(P)=='c41d00e4c79e6374fbdc5a8167de451fbd4c84f8350cb41935cea3e0ae4a6abf'
 g,h,b,q,after=pickle.loads(M.read_bytes());pg,ph,pb,pq,before=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(b,q);MS.restore_bound_field_current_precision_states(pb,pq)
 assert g==pg and h==ph and q[:-1]==pq
 assert after['zones'][:-1]==before['zones']and{k:v for k,v in after.items()if k!='zones'}=={k:v for k,v in before.items()if k!='zones'}
 newq=q[-1];assert newq['uuid']==UID and L.norm(newq['net'])==NET
 old=pickle.loads((S/'actual-drilled-current-groups.pkl').read_bytes())
 _,new=K.physical(after,NET,K.hole_context(after));prior=old[NET];_,losses=K.contact_losses(prior,new);ar=K.root(prior,'R18001','2');nr=K.root(new,'R18001','2');lost=K.keys(ar)-K.keys(nr)
 targets={('pad','fd718e28-2f39-4c99-9c18-ba03fc86da8b','F.Cu'),('track','e34c9ec3-20ba-430a-902c-b5069a85c2f7','F.Cu')}|{('via','498e9bfd-bcf6-4711-864a-ddfe55479c3a',ly)for ly in K.LAYERS}
 source={'all_old_IO3_group_losses':losses,'prior_R155_source_keys_lost':[list(x)for x in sorted(lost)],'retained_R14045_eight_keys_rooted':targets<=K.keys(nr),'before_named_source_pads':len({r['uuid']for r in ar if r['kind']=='pad'and str(r['pin'])}),'after_named_source_pads':len({r['uuid']for r in nr if r['kind']=='pad'and str(r['pin'])}),'full_IO3_output_current_A':2,'branch_barrel_sheet_drop_thermal_current_loop':'OPEN_NO_EQUAL_PAD_SHARING_CLAIM'}
 put(O/'IO3-retained-source-current-topology.json',source);(O/'fresh-IO3-actual-drilled-groups.pkl').write_bytes(pickle.dumps({NET:new},protocol=5));print('R503 source',len(losses),len(lost),source['after_named_source_pads'],source['retained_R14045_eight_keys_rooted'],flush=True)
 # Exact true circular caps and real pad polygons, separate .025 planning
 # reserve; all positive/native peers are hard, no same-raw alias lookup.
 records,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda n:.15 if dom[L.norm(n)]==dom[NET]else .6;checks=[];errors=[]
 for j in trees['In2.Cu'].query(newq['shape'].buffer(.8),predicate='intersects'):
  r=records['In2.Cu'][int(j)]
  if L.norm(r['net'])==NET:continue
  if r['kind']=='via':v=r['source'];distance=Point(v['x'],v['y']).distance(lit(newq['shape']))-v['d']/2
  elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];distance=LineString([t['a'],t['b']]).distance(lit(newq['shape']))-t['w']/2
  else:distance=lit(r['shape']).distance(lit(newq['shape']))
  row={'kind':'new_plane_to_true_discrete_'+r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'actual_gap_mm':distance,'required_guard_mm':gap(r['net'])+.025};checks.append(row)
  if distance<row['required_guard_mm']:errors.append(row)
 for z in after['zones']:
  if L.norm(z['net'])==NET or'In2.Cu'not in z['fills']:continue
  sh=unary_union(L.poly(z['fills']['In2.Cu']))
  if sh.is_empty or sh.distance(lit(newq['shape']))>.8:continue
  distance=sh.distance(lit(newq['shape']));req=max(float(z['clearance_mm']),gap(z['net']),.15)+.025;row={'kind':'new_plane_to_current_foreign_fill','UUID':z['uuid'],'raw_net':z['net'],'actual_gap_mm':distance,'required_guard_mm':req};checks.append(row)
  if distance<req:errors.append(row)
 for z in q:
  if z['layer']!='In2.Cu'or L.norm(z['net'])==NET:continue
  for role in ('shape','zone_outline_shape'):
   sh=lit(z[role]);distance=sh.distance(lit(newq['shape']))
   if distance>.8:continue
   req=max(float(z['clearance_mm']),gap(z['net']),.15)+.025;row={'kind':'new_plane_to_owned_foreign_'+role,'UUID':z['uuid'],'raw_net':z['net'],'actual_gap_mm':distance,'required_guard_mm':req};checks.append(row)
   if distance<req:errors.append(row)
 put(O/'true-cap-and-owned-foreign-checks.json',checks);put(O/'true-cap-and-owned-foreign-errors.json',errors);print('R503 geometry',len(checks),len(errors),flush=True)
 # This candidate has no ground/foreign filled change at all; every bank's
 # actual source key/reference geometries and every native track is exact.
 refs=[]
 for net,ref,pin in K.ROOTS[:3]:
  assert[z for z in before['zones']if L.norm(z['net'])==net]==[z for z in after['zones']if L.norm(z['net'])==net]
  root=K.root(old[net],ref,pin);rr=K.source_refs(root);raw,proof=RF.audit(before,rr,rr,net,());refs.append({'net':net,'all_actual_ground_arrays_discrete_holes_exact':True,'raw_identical_reference_delta_losses':raw,'proof':proof})
 put(O/'three-bank-exact-source-reference-identity.json',refs)
 text=D.read_text(encoding='utf-8');rules=[]
 for name,cond,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',text):
  if'zone'not in what.split():continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",cond);assert len(names)==1
  area=next(a for a in h['rule_areas']if a.get('name')==names[0]);rules.append((name,area,re.findall(r"A.NetName != '([^']+)'",cond)))
 rules +=[(a.get('name',a['uuid']),a,[])for a in h['rule_areas']if a.get('no_zones')]
 nozone=[];count=0
 for z in q:
  for name,area,exempt in rules:
   if z['layer']not in area['layers']or z['net']in exempt:continue
   arshape=unary_union(L.poly(area['outline']))
   for role in ('shape','zone_outline_shape'):
    count+=1;hit=lit(z[role]).intersection(arshape)
    if not hit.is_empty:nozone.append({'UUID':z['uuid'],'role':role,'rule':name,'raw_net':z['net'],**summary(hit)})
 put(O/'all-generated-both-role-native-nozone-errors.json',nozone)
 failed=losses or lost or not source['retained_R14045_eight_keys_rooted']or errors or nozone or any(r['raw_identical_reference_delta_losses']for r in refs)
 put(O/'receipt.json',{'status':'SCOPED_TMR_SOURCE_CONTACT_TRUE_GEOMETRY_NOZONE_HOST_PASS_NATIVE_UNION_CURRENT_OPEN'if not failed else'SCOPED_TMR_BYPASS_REPAIR_REQUIRED','model_sha256':sha(M),'source':source,'true_geometry_check_count':len(checks),'true_geometry_errors':errors,'all_generated_both_role_nozone_check_count':count,'all_generated_nozone_errors':nozone,'three_bank_old_track_and_before_supported_DC_reference_roles_exact':True,'all_other_R491_original_objects_and_arrays_exact':True,'FA_source47_proof_R483_receipt_sha256':sha(H/'R155-protected-FA-TMR-local-negative-source-contact-native-nozone-r483/receipt.json'),'full_native_same_raw_equal_settings_overlap_normalization_current_loop_mesh_DRC':'OPEN','all_inherited_R155_28reference_CORE_ROOT42_planner_FAIL_OPEN_retained':True,'FIELD5_R465_13reference_383IO3_FAIL_not_overlaid':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start})
 print('R503 receipt',sha(O/'receipt.json'),'nozone',len(nozone),flush=True)
if __name__=='__main__':main()
