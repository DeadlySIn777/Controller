"""Independent current-FA source/contact and exact no-zone audit.

Fresh physical FA graph; unchanged ground arrays/discrete copper are checked
before reusing their literal source reference roles. No mesh or native PASS.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time,hashlib,re
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
P=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
M=H/'R155-protected-FA-TMR-local-negative-inherited-outline-FAIL-r481/model.pkl'
S=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
R364=H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl'
D=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
O=H/'R155-protected-FA-TMR-local-negative-source-contact-native-nozone-r483'
NET='/motherboard_power_entry/FIELD_A_24V_PROTECTED'
UID='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def summary(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'WKB_SHA256':dg(s)}
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='206031df3e638b08ff3356239f2ff83efde810944c9a0630ee06c8a9672df1ff';assert sha(P)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,after=pickle.loads(M.read_bytes());pg,ph,pb,pq,before=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(b,q);MS.restore_bound_field_current_precision_states(pb,pq)
 assert g==pg and h==ph
 assert len(q)==len(pq)and all(a['uuid']==z['uuid']for a,z in zip(q,pq))
 for a,z in zip(q,pq):
  assert{k:v for k,v in a.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}
  if a['uuid']!=UID:assert all(a[r].wkb==z[r].wkb for r in ('shape','zone_outline_shape'))
 assert len(after['zones'])==len(before['zones'])
 for a,z in zip(after['zones'],before['zones']):
  if a['uuid']!=UID:assert a==z
  else:assert{k:v for k,v in a.items()if k!='fills'}=={k:v for k,v in z.items()if k!='fills'}
 assert{k:v for k,v in after.items()if k!='zones'}=={k:v for k,v in before.items()if k!='zones'}
 # R368 graph is reused only after its actual model is byte-for-byte physical-identical to R155.
 _,rh,_,rq,rc=pickle.loads(R364.read_bytes());assert rh==ph and rc==before
 assert all(a['shape'].wkb==z['shape'].wkb for a,z in zip(rq,pq))
 old=pickle.loads((S/'actual-drilled-current-groups.pkl').read_bytes());ctx=K.hole_context(after);_,new=K.physical(after,NET,ctx);prior=old[NET];_,losses=K.contact_losses(prior,new);ar=K.root(prior,'U11004','17');nr=K.root(new,'U11004','17');lost=K.keys(ar)-K.keys(nr)
 graphs={NET:new};(O/'fresh-FA-actual-drilled-groups.pkl').write_bytes(pickle.dumps(graphs,protocol=5))
 src={'status':'PASS_SOURCE_CONTACT_TO_EXACT_R155'if not losses and not lost else'REPAIR_REQUIRED','all_old_FA_group_losses':losses,'prior_source_keys_lost':[list(k)for k in sorted(lost)],'before_named_source_pads':len({r['uuid']for r in ar if r['kind']=='pad'and str(r['pin'])}),'after_named_source_pads':len({r['uuid']for r in nr if r['kind']=='pad'and str(r['pin'])}),'physical_contact_threshold_mm':.000002,'full_protected_current_A':4.567408669354,'current_mesh_drop_thermal_unequal_pad_barrel_sharing':'OPEN_NO_EQUAL_SHARING_CAPACITY_CLAIM'};put(O/'FA-source-contact-current-topology.json',src);print('R483 FA',len(losses),len(lost),'source pads',src['after_named_source_pads'],flush=True)
 # Ground identity is structural and literal: no ground fills, Cu, holes or source pad changed.
 refs=[]
 for net,ref,pin in K.ROOTS[:3]:
  root=K.root(old[net],ref,pin);rr=K.source_refs(root);raw,proof=RF.audit(before,rr,rr,net,());refs.append({'net':net,'source':ref+'.'+pin,'actual_before_after_source_references_identical_WKB':True,'raw_same-reference_RF_losses':raw,'proof':proof,'every_current_ground_fill_array_and_order_exact':True})
 put(O/'ground-source-and-retained-whole-track-reference-identity.json',refs)
 fg=K.source_refs(K.root(old[K.ROOTS[1][0]],'J11003','2'));oldx=next(z for z in pq if z['uuid']==UID);newx=next(z for z in q if z['uuid']==UID)
 rawbody=[]
 for ly in ['F.Cu','In2.Cu','B.Cu','In3.Cu']:
  relevant=[z for z in q if L.norm(z['net'])==NET and z['layer']==ly]
  for z in relevant:
   gap=lit(z['shape']).difference(fg[ly]);rawbody.append({'UUID':z['uuid'],'layer':ly,'raw_DC_fullbody_reference_gap':summary(gap),'not_qualified_as_signal_shadow_or_current_loop':True})
 put(O/'unchanged-FA-DC-fullbody-return-open-flags.json',rawbody)
 # Native unconditional no_zones flags and every actual disallow-zone DRU named-area predicate.
 text=D.read_text(encoding='utf-8');patterns=re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',text);rules=[]
 for name,cond,what in patterns:
  if 'zone'not in what.split():continue
  areas=re.findall(r"A\.intersectsArea\('([^']+)'\)",cond);exempt=re.findall(r"A\.NetName != '([^']+)'",cond)
  assert len(areas)==1 and cond.startswith("A.intersectsArea(")and '!A.memberOfFootprint('in cond,(name,'unhandled zone rule')
  aa=[a for a in h['rule_areas']if a.get('name')==areas[0]];assert len(aa)==1
  rules.append({'name':name,'condition':cond,'area':aa[0],'exempt_raw_nets':exempt,'type':'exact_native_D​RU_conditional'})
 for a in h['rule_areas']:
  if a.get('no_zones'):rules.append({'name':a.get('name',a['uuid']),'area':a,'exempt_raw_nets':[],'type':'native_unconditional_no_zones'})
 nozone=[];bad=[]
 for z in q:
  for rule in rules:
   if z['layer']not in rule['area']['layers']or z['net']in rule['exempt_raw_nets']:continue
   area=unary_union(L.poly(rule['area']['outline']))
   for role in ('shape','zone_outline_shape'):
    hit=lit(z[role]).intersection(area)
    if not hit.is_empty:
     row={'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'role':role,'rule':rule['name'],'rule_type':rule['type'],**summary(hit)};bad.append(row);wf=O/(z['uuid']+'-'+role+'-'+str(len(bad))+'-native-nozone-witness.wkb');wf.write_bytes(hit.wkb);row['witness_file']=str(wf.resolve())
   nozone.append({'UUID':z['uuid'],'rule':rule['name'],'actual_raw_exemption_not_used':True})
 put(O/'all-generated-both-role-native-nozone-errors.json',bad)
 # Preserve inherited outline mismatch and all preexisting reference/current failures.
 inherited=json.loads((M.parent/'unchanged-inherited-outline-mismatch-FAIL.json').read_text(encoding='utf-8'))
 rec={'status':'SCOPED_KEEP_OUT_SOURCE_CONTACT_NOZONE_HOST_PASS_INHERITED_FAIL_CURRENT_NATIVE_OPEN'if not losses and not lost and not bad and not any(r['raw_same-reference_RF_losses']for r in refs)else'SCOPED_KEEP_OUT_REPAIR_REQUIRES_FURTHER_WORK','model_sha256':sha(M),'model_file':str(M.resolve()),'parent_sha256':sha(P),'fresh_FA_graph_SHA256':sha(O/'fresh-FA-actual-drilled-groups.pkl'),'FA_source_contact':src,'all_generated_native_nozone_check_count':len(nozone),'all_generated_native_nozone_error_count':len(bad),'exact_native_zone_rule_count':len(rules),'native_rule_SHA256':sha(D),'all_ground_current_arrays_Cu_holes_source_actual_roles_exact':True,'inherited_remote_physical_outside_intended_FAIL':inherited,'inherited_R155_28_refs_CORE_ROOT42_planner_FAIL_OPEN_preserved':True,'full_signed_current_mesh_drop_thermal_native_fill_DRC':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(O/'receipt.json',rec);print('R483 receipt',sha(O/'receipt.json'),'nozone errors',len(bad),flush=True)
if __name__=='__main__':main()
