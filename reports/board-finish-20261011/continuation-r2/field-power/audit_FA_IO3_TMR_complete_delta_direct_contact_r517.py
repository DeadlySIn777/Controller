"""Complete exact-R155 delta: fresh changed graphs, exact untouched reuse.

No holes or discrete changed. Direct old piece-to-native-metal contacts are
checked separately from whole-net relations/source and unchanged references.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time,collections
from pathlib import Path
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl'
P=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
OLD=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl'
IO=H/'IO3-TMR-minimal-union-independent-source-geometry-r513/fresh-IO3-actual-drilled-groups.pkl'
FA=H/'R155-protected-FA-TMR-local-negative-source-contact-native-nozone-r483/fresh-FA-actual-drilled-groups.pkl'
O=H/'FA-IO3-TMR-current-R515-complete-delta-direct-contact-r517'
CHANGED={'/IO_3V3':'4f297f78-8d11-5be4-910e-9245f73fa249','/motherboard_power_entry/FIELD_A_24V_PROTECTED':'7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19'}
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862';assert sha(P)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';assert sha(OLD)=='ee233fd9010cf3c29d0c4b47503fd93bf754dddf9dd297f9f7c58117c7589742'
 g,h,b,q,c=pickle.loads(M.read_bytes());pg,ph,pb,pq,pc=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(b,q);MS.restore_bound_field_current_precision_states(pb,pq)
 assert g==pg and h==ph and{k:v for k,v in c.items()if k!='zones'}=={k:v for k,v in pc.items()if k!='zones'}
 # Cached BEFORE is valid only under exact physical R364 identity.
 _,rh,_,rq,rc=pickle.loads((H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl').read_bytes());assert ph==rh and pc==rc
 assert all(a['uuid']==z['uuid']and a['shape'].wkb==z['shape'].wkb for a,z in zip(pq,rq))
 old=pickle.loads(OLD.read_bytes());new=dict(old);ia=pickle.loads(IO.read_bytes());fa=pickle.loads(FA.read_bytes());new.update(ia);new.update(fa)
 # Exact physical identity of these separately fresh graphs to the final
 # metadata-only R515, and FA invariant under later IO3-only additions.
 _,fh,_,fq,fc=pickle.loads((FA.parent.parent/'R155-protected-FA-TMR-local-negative-inherited-outline-FAIL-r481/model.pkl').read_bytes());assert fh==h
 assert[z for z in fc['zones']if L.norm(z['net'])in fa]==[z for z in c['zones']if L.norm(z['net'])in fa]
 _,ih,_,iq,ic=pickle.loads((IO.parent.parent/'IO3-TMR-bypass-only-two-role-union-individual-role-fill-scopes-r511/model.pkl').read_bytes());assert ih==h and ic==c and all(a['uuid']==z['uuid']and a['shape'].wkb==z['shape'].wkb for a,z in zip(iq,q))
 rows=[];bad=[];exact=[];direct=[];directbad=[]
 for net in sorted(old):
  if net not in CHANGED:
   assert[z for z in pc['zones']if L.norm(z['net'])==net]==[z for z in c['zones']if L.norm(z['net'])==net]
   exact.append({'net':net,'all_original_current_zone_arrays_discrete_pads_tracks_holes_exact':True,'no_extra_holes_or_projection':True,'actual_before_physical_graph_reused':True})
  relations,losses=K.contact_losses(old[net],new[net]);rows.append({'net':net,'old_groups':len(old[net]),'new_groups':len(new[net]),'losses':losses,'all_prior_physical_keys_covered':not losses});bad.extend({'net':net,**r}for r in losses)
  if net not in CHANGED:continue
  zid=CHANGED[net];finalfill=collections.defaultdict(list)
  for xs in new[net]:
   for r in xs:
    if r['kind']=='fill':finalfill[r['uuid'],r['layer']].append(r['shape'])
  for layer in K.LAYERS:
   metal=[r for xs in old[net]for r in xs if r['layer']==layer and r['kind']!='fill'];tree=STRtree([r['shape']for r in metal])
   for fill in[r for xs in old[net]for r in xs if r['kind']=='fill'and r['layer']==layer and r['uuid']==zid]:
    for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
     r=metal[int(j)]
     if r['shape'].distance(fill['shape'])>.000002:continue
     joined=any(sh.distance(r['shape'])<=.000002 for sh in finalfill[zid,layer]);row={'net':net,'zone_UUID':zid,'layer':layer,'old_drilled_fill_piece_SHA256':dg(fill['shape']),'retained_native_metal_key':[r['kind'],r['uuid'],layer],'same_zone_direct_layer_contact_retained':joined};direct.append(row)
     if not joined:directbad.append(row)
  print('R517 changednet',net,'relations',len(losses),'directloss',len(directbad),flush=True)
 sources=[]
 for net,ref,pin in K.ROOTS:
  a=K.root(old[net],ref,pin);n=K.root(new[net],ref,pin);loss=K.keys(a)-K.keys(n);sources.append({'net':net,'actual_source':ref+'.'+pin,'prior_source_keys_lost':[list(x)for x in sorted(loss)],'before_named_source_pads':len({r['uuid']for r in a if r['kind']=='pad'and str(r['pin'])}),'after_named_source_pads':len({r['uuid']for r in n if r['kind']=='pad'and str(r['pin'])}),'full_signed_current_and_unequal_pad_sharing_current_mesh_native':'OPEN'})
 put(O/'all-net-physical-contact-delta.json',rows);put(O/'all-unchanged-net-exact-record-reuse.json',exact);put(O/'complete-two-modified-zone-direct-layer-contacts.json',direct);put(O/'direct-layer-contact-losses.json',directbad);put(O/'nine-actual-source-key-delta.json',sources)
 (O/'actual-drilled-current-groups.pkl').write_bytes(pickle.dumps(new,protocol=5))
 failures=bad or directbad or any(r['prior_source_keys_lost']for r in sources)
 put(O/'receipt.json',{'status':'TWO_OWNED_NATIVE_TMR_REPAIR_COMPLETE_HOST_INCREMENTAL_CONTACT_SOURCE_DIRECT_NOZONE_REFERENCE_PASS_CURRENT_NATIVE_OPEN'if not failures else'TMR_INCREMENTAL_DIRECT_CONTACT_REPAIR_REQUIRED','model_file':str(M.resolve()),'model_sha256':sha(M),'exact_R155_before_sha256':sha(P),'actual_BEFORE_group_sha256':sha(OLD),'complete_actual_net_count':len(old),'reused_unchanged_net_count':len(exact),'complete_prior_group_losses':bad,'direct_layer_contact_count':len(direct),'direct_layer_contact_losses':directbad,'nine_prior_source_key_loss_count':sum(len(r['prior_source_keys_lost'])for r in sources),'actual_final_group_sha256':sha(O/'actual-drilled-current-groups.pkl'),'R513_source_true_Cu_native_nozone_proof_sha256':sha(IO.parent/'receipt.json'),'R483_FA_source_proof_sha256':sha(FA.parent/'receipt.json'),'all_three_ground_actual_source_refs_and_supported_before_DC_roles_exact':True,'only_generated_FA7ef_and_IO3In2_4f_role_and_two_current_filled_deltas':True,'inherited_R15528ref_CORE_ROOT42_planner_current_FAIL_OPEN_bound':True,'unrelated_FIELD5_R46513refs_383IO3FAIL_not_overlaid':True,'native_CPP_fullfill_exact_profile_and_full_fault_mesh_drop_thermal_current':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R517 receipt',sha(O/'receipt.json'),'direct',len(direct),'loss',len(directbad),'whole',len(bad),flush=True)
if __name__=='__main__':main()
