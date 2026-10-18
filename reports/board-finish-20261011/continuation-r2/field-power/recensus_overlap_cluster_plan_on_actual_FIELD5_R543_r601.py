"""Rebind only overlap composition plans to the exact later FIELD5 source head."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent;OUT=H/'eight-native-overlap-plan-exact-R543-source-head-recensus-r601'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();old=H/'eight-native-overlaps-minimal-exact-owned-constituent-plan-r589';assert sha(old/'receipt.json')=='ffe28fa9191d324d1cf73652dc7ff3a2a8ad7760ef25c9315bf28c0de3f7ad13';mp=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl';assert sha(mp)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416';g,h,b,q,c=pickle.loads(mp.read_bytes());Q={z['uuid']:z for z in q};prior=pickle.loads((old/'only-four-planned-clusters-exact-before-constituents-NOT_REPLACEMENT.pkl').read_bytes());newuid='ae376fef-55ba-5504-ac43-bd588c093e82';withdrawn='61cb8179-7754-5031-bbea-0da464bf816f';assert newuid in Q and withdrawn not in Q
 new=Q[newuid];keys=['net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm'];assert all(k in new for k in keys)
 untouched=[];plans=[];packet=[];touch=[]
 for p in prior:
  members=p['plan']['exact_owned_proposal_UUIDs'];zs=[]
  for oldq in p['constituent_q_rows']:
   current=Q[oldq['uuid']]
   assert current.keys()==oldq.keys()
   assert all(current[k].wkb==oldq[k].wkb if k in('shape','zone_outline_shape')else current[k]==oldq[k]for k in current)
   untouched.append(current['uuid']);zs.append(current)
  if p['plan']['raw_net']==new['net']and p['plan']['layer']==new['layer']:
   profile=p['plan']['all_nine_settings_bound'];assert (new['priority'],new['clearance_mm'],new['min_thickness_mm'],new['pad_connect_mode'],new['island_removal_mode'],new['thermal_gap_mm'],new['thermal_bridge_width_mm'])==(profile['priority'],profile['local_clearance_mm'],profile['min_thickness_mm'],profile['pad_connect_mode'],profile['island_removal_mode'],profile['thermal_gap_mm'],profile['thermal_bridge_width_mm'])
   for z in zs:
    hit=new['shape'].intersection(z['shape']);intent=new['zone_outline_shape'].intersection(z['zone_outline_shape']);touch.append({'before_UUID':z['uuid'],'new_UUID':newuid,'actual_same_raw_layer_physical_hit':ds(hit),'same_settings_intended_hit':ds(intent)})
   assert any(not x['same_settings_intended_hit']['empty']for x in touch);zs.append(new);members=members+[newuid]
  actualroles={role:unary_union([z[role]for z in zs])for role in('shape','zone_outline_shape')}
  plan={'exact_R543_before_owned_UUIDs':members,'raw_net':zs[0]['net'],'layer':zs[0]['layer'],'nine_setting_owner_authority':p['plan']['all_nine_settings_bound'],'before_roles':[{'UUID':z['uuid'],'shape_SHA256':hs(z['shape']),'intended_SHA256':hs(z['zone_outline_shape'])}for z in zs],'planned_union_roles':{role:ds(s)for role,s in actualroles.items()},'no_emission_or_replacement_model':True}
  plans.append(plan);packet.append({'plan':plan,'exact_R543_constituent_q_rows':zs,'provisional_union_roles_NOT_ADOPTED':actualroles})
 # All other same-raw/layer q stay separate unless their intended contour
 # actually intersects an affected cluster; report this, never silently add.
 extra=[];cluster_ids={z['uuid']for p in packet for z in p['exact_R543_constituent_q_rows']}
 for p in packet:
  spec=p['plan'];s=p['provisional_union_roles_NOT_ADOPTED']['zone_outline_shape']
  for z in q:
   if z['uuid']in cluster_ids or(z['net'],z['layer'])!=(spec['raw_net'],spec['layer']):continue
   hit=s.intersection(z['zone_outline_shape'])
   if not hit.is_empty:extra.append({'planned_cluster_net':spec['raw_net'],'layer':spec['layer'],'other_current_q_UUID':z['uuid'],'actual_intended_overlap':ds(hit),'no_automatic_merge_or_priority_change':True})
 put(OUT/'new-FIELD5-exact-overlap-census.json',touch);put(OUT/'other-current-owned-same-raw-intended-overlap-obligations.json',extra);put(OUT/'four-current-scope-minimal-component-plans.json',plans);pk=OUT/'only-current-cluster-constituents-and-provisional-unions-NOT_REPLACEMENT.pkl';pk.write_bytes(pickle.dumps(packet,protocol=5));source=H/'FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545/receipt.json';assert sha(source)=='327869c6a571da7935a4a5535b4d5457b3168ad20d5522bff2961de72f3a947a'
 put(OUT/'receipt.json',{'status':'READ_ONLY_EXACT_R543_MINIMAL_OVERLAP_PLAN_RECENSUS_NO_COMPOSITION_ADOPTION','exact_R543_model_SHA256':sha(mp),'R589_plan_SHA256':sha(old/'receipt.json'),'all11_prior_plan_q_rows_roles_and_metadata_exact_on_current_head':True,'new_FIELD5_same_nine_settings_member_added':newuid,'withdrawn_failed_FIELD5_preview_explicitly_not_restored':withdrawn,'planned_components':len(packet),'planned_constituents':sum(len(p['exact_R543_constituent_q_rows'])for p in packet),'other_same_raw_current_intended_overlap_obligation_count':len(extra),'plans_SHA256':sha(OUT/'four-current-scope-minimal-component-plans.json'),'packet_SHA256':sha(pk),'exact_current_source_contact_authority_R545_SHA256':sha(source),'source_contact_reference_after_any_future_integer_union_emission':'OPEN: must fresh-check actual changed roles/current records and all old supported references; same-settings union plan does not grant native source/current or physical union rounding credit.','original_native_discrete_rules_source_and_host_model_UNCHANGED':True,'all8_R567_errors_and_R543_rawDC_reference_current_failures_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R601',sha(OUT/'receipt.json'),'newtouch',sum(not x['same_settings_intended_hit']['empty']for x in touch),'extra',len(extra),flush=True)
if __name__=='__main__':main()
