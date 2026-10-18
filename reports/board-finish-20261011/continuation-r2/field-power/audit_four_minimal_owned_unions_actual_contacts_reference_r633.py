"""Independent actual all-drill delta on the exact four owned union scopes."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,time,hashlib,collections
from pathlib import Path
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import restore_field_current_mixed_precision_states_r366 as MS
M=H/'R543-four-unions-bound-exact-line-owned-scopes-r631/model.pkl'
P=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl'
BASE=H/'FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545'
OUT=H/'four-minimal-owned-unions-actual-all-drill-source-contact-reference-r633'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 r=set_precision(s,0);assert r.wkb==s.wkb;return r
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def count(xs):return len({r['uuid']for r in xs if r['kind']=='pad'and str(r['pin'])})
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(P)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416';assert sha(M)=='8dacfdb44f609ecbd3fcfb9280aac624eca7d03e3bf6d50ada3dbe3ac230887a'
 rc=json.loads(M.with_name('receipt.json').read_bytes());assert sha(M.with_name('receipt.json'))=='a52f6d19ea241092ad469de8e9ac2097cbbb136012fdd44f5a711f35e088c962'
 g,h,b,q,c=pickle.loads(M.read_bytes());pg,ph,pb,pq,pc=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(b,q);MS.restore_bound_field_current_precision_states(pb,pq)
 assert g==pg and h==ph and{k:v for k,v in c.items()if k!='zones'}=={k:v for k,v in pc.items()if k!='zones'}
 pk=M.parent/'only-four-current-member-to-inward-union-and-local-current-record-operations.pkl';assert sha(pk)==rc['packet_SHA256'];packet=pickle.loads(pk.read_bytes());withdraw={u for p in packet for u in p['members_before_UUIDs']};newids={p['new_q']['uuid']for p in packet};changed={L.norm(p['new_q']['net'])for p in packet};assert len(changed)==4
 beforeq={a['uuid']:a for a in pq};nowq={a['uuid']:a for a in q};beforez={a['uuid']:a for a in pc['zones']};nowz={a['uuid']:a for a in c['zones']};assert set(nowq)==set(beforeq)-withdraw|newids;assert set(nowz)==set(beforez)-withdraw|newids
 for uid,a in beforeq.items():
  if uid not in withdraw:assert nowq[uid]==a
 for uid,a in beforez.items():
  if uid not in withdraw:assert nowz[uid]==a
 role=[];mapping={}
 for p in packet:
  new=p['new_q'];uid=new['uuid'];assert nowq[uid]==new and nowz[uid]==p['new_actual_zone'];assert not set(p['members_before_UUIDs'])&{z['uuid']for z in h['zones']}
  for a in p['exact_before_q']:assert a==beforeq[a['uuid']];mapping[a['uuid']]=uid
  for r in ('shape','zone_outline_shape'):
   old=unary_union([zero(a[r])for a in p['exact_before_q']]);after=zero(new[r]);gain=after.difference(old);assert gain.is_empty;role.append({'UUID':uid,'role':r,'before_literal_union_SHA256':hs(old),'new_SHA256':hs(after),'literal_gained_Cu_EMPTY':True,'exact_removed_owned_Cu':ds(old.difference(after))})
  for op in p['actual_current_record_operations']:assert op['before_records']==beforez[op['old_UUID']]['fills'][new['layer']]
 put(OUT/'exact-minimal-owned-role-original-identity-and-negative-only-proof.json',role)
 gf=BASE/'actual-drilled-current-groups.pkl';br=json.loads((BASE/'receipt.json').read_bytes());assert sha(gf)==br['actual_current_groups_SHA256'];old=pickle.loads(gf.read_bytes());now=dict(old);ctx=K.hole_context(c);identity=[]
 allnets={L.norm(a['net'])for kind in ('pads','tracks','vias','zones')for a in pc[kind]};assert allnets=={L.norm(a['net'])for kind in ('pads','tracks','vias','zones')for a in c[kind]}
 for net in sorted(allnets-changed):
  assert[a for a in c['zones']if L.norm(a['net'])==net]==[a for a in pc['zones']if L.norm(a['net'])==net];identity.append({'net':net,'all_native_discrete_FP_hole_and_fill_arrays_exact':True,'no_new_holes':True,'physical_graph_exactly_unchanged':True})
 for net in sorted(changed):
  assert net in old;_,now[net]=K.physical(c,net,ctx);print('R633 actual',net,'groups',len(now[net]),flush=True)
 contacts=[];bad=[]
 for net in sorted(old):
  rows,loss=K.contact_losses(old[net],now[net]);contacts.append({'net':net,'fresh_actual_graph':net in changed,'before_groups':len(old[net]),'after_groups':len(now[net]),'all_retained_layer_relationships':rows,'losses':loss});bad.extend({'net':net,**r}for r in loss)
 sources=[]
 for net,ref,pin in K.ROOTS+[('/motherboard_power_entry/FIELD_5V','L11003','2'),('/motherboard_do/DOB_FIELD_3V3','U11018','8')]:
  a=K.root(old[net],ref,pin);n=K.root(now[net],ref,pin);lost=K.keys(a)-K.keys(n);sources.append({'net':net,'source':ref+'.'+pin,'before_source_named_pads':count(a),'after_source_named_pads':count(n),'lost_prior_source_keys':[list(k)for k in sorted(lost)]})
 direct=[];directbad=[]
 for net in sorted(changed):
  finalfill=collections.defaultdict(list)
  for xs in now[net]:
   for r in xs:
    if r['kind']=='fill':finalfill[r['uuid'],r['layer']].append(r['shape'])
  for ly in K.LAYERS:
   metal=[r for xs in old[net]for r in xs if r['kind']!='fill'and r['layer']==ly];tree=STRtree([r['shape']for r in metal])
   for f in[r for xs in old[net]for r in xs if r['kind']=='fill'and r['uuid']in withdraw and r['layer']==ly]:
    for j in tree.query(f['shape'].buffer(.000002),predicate='intersects'):
     r=metal[int(j)]
     if r['shape'].distance(f['shape'])>.000002:continue
     good=any(r['shape'].distance(z)<=.000002 for z in finalfill[mapping[f['uuid']],ly]);row={'net':net,'before_owned_UUID':f['uuid'],'new_union_UUID':mapping[f['uuid']],'layer':ly,'native_metal_key':[r['kind'],r['uuid'],ly],'retained_direct_fill_touch':good};direct.append(row)
     if not good:directbad.append(row)
 refs=[];refbad=[]
 for net,ref,pin in K.ROOTS[:3]:
  a=K.root(old[net],ref,pin);n=K.root(now[net],ref,pin)
  # Canonical primitive ordering is paired; no source-supported shadow grows.
  def source_refs(group):return {out:unary_union(sorted([r['shape']for r in group if r['kind']=='fill'and r['layer']==inner],key=hs))for out,inner in K.MAP.items()}
  ar=source_refs(a);nr=source_refs(n);trackbad,proof=RF.audit(pc,ar,nr,net,());refbad.extend({'bank':net,'kind':'old_routed_track',**r}for r in trackbad);dc=[]
  for z in pq:
   if z['layer']not in K.MAP or h['domains_normalized'][L.norm(z['net'])]!=h['domains_normalized'][net]:continue
   body=zero(z['shape']);raw=body.intersection(ar[z['layer']]).difference(nr[z['layer']]);selfraw=body.intersection(ar[z['layer']]).difference(ar[z['layer']]);novel=raw.difference(selfraw);row={'UUID':z['uuid'],'layer':z['layer'],'raw_full_strict_supported_before_reference_loss':ds(raw),'exact_same_before_SELF_formula':ds(selfraw),'novel_after_minus_before_formula':ds(novel),'raw_nonempty_full_flag_preserved':not raw.is_empty};dc.append(row)
   if not novel.is_empty:refbad.append({'bank':net,'kind':'prior_supported_DC_incremental_RAW_loss','no_waiver':True,**row})
  refs.append({'bank':net,'strict_old_routed_track_losses':trackbad,'strict_track_proof':proof,'all_prior_DC_actual_supported_before_deltas_and_self_flags':dc});print('R633 reference',net,'oldtracks',len(trackbad),'incrementalDC',sum(not r['novel_after_minus_before_formula']['empty']for r in dc),flush=True)
 put(OUT/'all-existing-physical-relationships.json',contacts);put(OUT/'all-eleven-prior-source-bank-keys.json',sources);put(OUT/'all-old-owned-member-direct-native-copper-touches.json',direct);put(OUT/'all-strict-routed-track-and-supported-DC-reference-deltas.json',refs);put(OUT/'unchanged-exhaustive-native-net-record-identity.json',identity);put(OUT/'actual-contact-source-reference-losses.json',{'contacts':bad,'direct':directbad,'reference':refbad,'sources':[r for r in sources if r['lost_prior_source_keys']]})
 gp=OUT/'actual-drilled-current-groups.pkl';gp.write_bytes(pickle.dumps(now,protocol=5));fail=bool(bad or directbad or refbad or any(r['lost_prior_source_keys']for r in sources))
 put(OUT/'receipt.json',{'status':'FOUR_OWNED_UNIONS_INCREMENTAL_SOURCE_CONTACT_REFERENCE_REPAIR_REQUIRED'if fail else'FOUR_OWNED_UNIONS_INCREMENTAL_ACTUAL_SOURCE_CONTACT_AND_OLD_REFERENCE_PASS_INHERITED_FULL_FAILS_NATIVE_CURRENT_OPEN','model_SHA256':sha(M),'parent_R543_SHA256':sha(P),'before_actual_group_SHA256':sha(gf),'fresh_changed_graph_nets':sorted(changed),'compared_cached_net_count':len(old),'exhaustive_actual_net_count':len(allnets),'exact_unchanged_net_count':len(identity),'old_physical_relationship_losses':bad,'old_direct_touch_count':len(direct),'old_direct_touch_losses':directbad,'source_prior_key_losses':sum(len(r['lost_prior_source_keys'])for r in sources),'incremental_reference_losses':refbad,'raw_parent_supported_DC_self_formula_FAIL_flags_and_B3_outside_intent_FAIL_NOT_WAIVED':True,'literal_same_net_source_group_merged_only_after_real_physical_contact':True,'all_original_native_discrete_Cu_FP_holes_outlines_settings_sources_rules_unchanged':True,'actual_current_groups_SHA256':sha(gp),'new_full_signed_current_drop_loop_thermal_native_API_refill_DRC':'OPEN','eight_old_native_overlap_ERRORS_not_yet_remeasured':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R633',sha(OUT/'receipt.json'),'incrementalPASS',not fail,flush=True)
if __name__=='__main__':main()
