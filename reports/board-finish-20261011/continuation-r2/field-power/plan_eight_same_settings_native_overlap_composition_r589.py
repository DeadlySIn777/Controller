"""Read-only minimal ownership/constituent plan; no native or host adoption."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent;OUT=H/'eight-native-overlaps-minimal-exact-owned-constituent-plan-r589'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'SHA256':hs(s)}
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();a=H/'R218-eight-native-zone-intersections-exact-input-attribution-r583/receipt.json';rp=ROOT/'coupled-recovery/R155-known-failed-reference-native-recipe-r306/receipt.json';assert sha(a)=='6c3083cdfdd8c9e8ab0aac83fbaf1ef6aa6fdc682a36a4289e19a8758c2027fc'
 ar=json.loads(a.read_bytes());r=json.loads(rp.read_bytes());mp=Path(r['frozen_host_model_file']);assert sha(mp)==r['frozen_host_model_sha256']=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,c=pickle.loads(mp.read_bytes());Q={z['uuid']:z for z in q};ids={z['UUID']for z in ar['zone_rows']};nr={x['uuid']:x for x in r['native_zone_rows']};pairfile=a.parent/'all-eight-exact-pair-location-native-profile-attributions.json';pairs=json.loads(pairfile.read_bytes())
 maps=[];props=set()
 for uid in sorted(ids):
  row=nr[uid];z=Q[row['proposal_uuid']];props.add(z['uuid']);assert sha(row['chunk_file'])==row['chunk_sha256']
  maps.append({'native_UUID':uid,'proposal_UUID':z['uuid'],'native_part_index':row['part_index'],'exact_chunk_file':row['chunk_file'],'exact_chunk_SHA256':row['chunk_sha256'],'raw_net':row['raw_net'],'layer':row['layer'],'actual_owner_label':z.get('label'),'constituent_proposal_UUIDs':z.get('constituent_proposal_UUIDs',[]),'declared_native_profile_authority':row['declared_native_settings'],'exact_model_before_physical_SHA256':hs(z['shape']),'exact_model_before_intended_SHA256':hs(z['zone_outline_shape'])})
 graph={u:set()for u in props}
 for row in pairs:
  x,y=[nr[v['UUID']]['proposal_uuid']for v in row['zones']];graph[x].add(y);graph[y].add(x)
 clusters=[];pending=set(props)
 while pending:
  todo=[min(pending)];found=set()
  while todo:
   u=todo.pop()
   if u in found:continue
   found.add(u);todo.extend(graph[u]-found)
  pending-=found;clusters.append(sorted(found))
 plans=[];packet=[]
 for i,members in enumerate(clusters):
  zs=[Q[u]for u in members];settings=[next(x['declared_native_settings']for x in r['native_zone_rows']if x['proposal_uuid']==u)for u in members];assert all(x==settings[0]for x in settings);assert len({(z['net'],z['layer'])for z in zs})==1
  roles={};controls={}
  for role in ('shape','zone_outline_shape'):
   union=unary_union([z[role]for z in zs]);roles[role]=union
   gains=union.difference(unary_union([z[role]for z in zs]));losses=unary_union([z[role]for z in zs]).difference(union)
   # These are representation-plan controls; no post-native current proof.
   controls[role]={'literal_union_gain':ds(gains),'literal_union_loss':ds(losses),'WKB_SHA256':hs(union),'constituent_WKBs':{z['uuid']:hs(z[role])for z in zs}}
   (OUT/('planned-cluster-'+str(i)+'-'+role+'.wkb')).write_bytes(union.wkb)
  hits=[row for row in pairs if any(nr[v['UUID']]['proposal_uuid']in members for v in row['zones'])]
  plan={'index':i,'exact_owned_proposal_UUIDs':members,'raw_net':zs[0]['net'],'layer':zs[0]['layer'],'all_nine_settings_bound':settings[0],'owned_native_chunks':[{k:m[k]for k in('native_UUID','proposal_UUID','native_part_index','exact_chunk_file','exact_chunk_SHA256')}for m in maps if m['proposal_UUID']in members],'reported_overlap_locations':[{'report_index':x['report_index'],'native_positions':[v.get('pos')for v in x['native_DRC_row']['items']],'intersection':x['intersection']}for x in hits],'physical_and_intended_literal_union_controls':controls,'current_before_host_and_actual_fill_arrays_UNMODIFIED':True,'required_next_steps':['Rebind exact role/chunk hashes to an agreed later integration head (never overwrite running R157).','Construct only this cluster from exact current constituents/profile with every untouched role/current-record array exact; preserve primitive precision state and own-drill intent separately.','Require literal zero-gain/locality and physical/source/current-fill union retention, all actual old contacts/direct/source/reference before emitting.','Serialize a single native polygon collection per touching component with same profile; API/full native refill must verify zero overlap errors and all actual annular/source contacts.'],'no_current_native_fill_source_DRC_promotion_from_plan':True}
  plans.append(plan);packet.append({'plan':plan,'constituent_q_rows':zs,'provisional_literal_union_roles':roles})
 put(OUT/'exact-thirteen-native-to-eleven-owned-proposal-mappings.json',maps);put(OUT/'four-minimal-same-settings-component-plans.json',plans);(OUT/'only-four-planned-clusters-exact-before-constituents-NOT_REPLACEMENT.pkl').write_bytes(pickle.dumps(packet,protocol=5))
 put(OUT/'receipt.json',{'status':'READ_ONLY_MINIMAL_FOUR_OWNED_CLUSTER_COMPOSITION_PLAN_BEFORE_FULL_CONTACT_REFERENCE_NATIVE_REVIEW','R583_attribution_SHA256':sha(a),'exact_R306_recipe_SHA256':sha(rp),'exact_before_model_file':str(mp),'exact_before_model_SHA256':sha(mp),'native_pair_count':8,'native_chunk_count':len(ids),'proposal_count':len(props),'planned_component_count':len(plans),'mapping_file_SHA256':sha(OUT/'exact-thirteen-native-to-eleven-owned-proposal-mappings.json'),'plans_file_SHA256':sha(OUT/'four-minimal-same-settings-component-plans.json'),'packet_file_SHA256':sha(OUT/'only-four-planned-clusters-exact-before-constituents-NOT_REPLACEMENT.pkl'),'all_original_native_zone_profiles_discrete_Cu_rules_source_FP_and_host_records_UNCHANGED':True,'not_a_replacement_model_or_native_emission':True,'native_R567_all_eight_ERRORS_preserved':True,'current_after_contact_direct_reference_source_capacity_and_DRC':'OPEN; plan does not change copper or waive inherited failures','R543_FIELD5_successor_rebase':'Its new ae376 and withdrawal61cb require a fresh cluster census and before hashes; do not copy current R155 union shapes onto that newer head.','adopted':False,'elapsed_seconds':time.monotonic()-st})
 print('R589',sha(OUT/'receipt.json'),len(ids),len(props),len(plans),flush=True)
if __name__=='__main__':main()
