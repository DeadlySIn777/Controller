"""Metadata-only fresh integer rings and exact two-q R155 delta package.

No geometry/native operation; historical union metadata remains history.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,hashlib,time
from pathlib import Path
from shapely import set_precision
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import restore_field_current_mixed_precision_states_r366 as MS
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
M=H/'IO3-TMR-bypass-only-two-role-union-individual-role-fill-scopes-r511/model.pkl'
P=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
O=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515'
UIDS={'7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19','4f297f78-8d11-5be4-910e-9245f73fa249'}
FIELDS=('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def rings(s):return [[[(int(round(x*1e6)),int(round(y*1e6)))for x,y in list(r.coords)[:-1]]for r in [p.exterior]+list(p.interiors)]for p in RF.parts(s)]
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(M)=='2d10de56f7e4fb5654431d4c1ba20361235127c7dc3d958da394300bf116cc19';assert sha(P)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);pg,ph,pb,pq,pc=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(pb,pq);assert g==pg and h==ph
 assert len(q)==len(pq)and {x['uuid']for x in q}=={x['uuid']for x in pq};assert len(c['zones'])==len(pc['zones']);assert{k:v for k,v in c.items()if k!='zones'}=={k:v for k,v in pc.items()if k!='zones'}
 roles=[];owned=[];states=[];fills=[]
 for x in q:
  old=next(y for y in pq if y['uuid']==x['uuid'])
  if x['uuid']not in UIDS:assert x==old;continue
  assert all(x[k]==old[k]for k in FIELDS)
  for role,key in [('shape','integer_nm_physical_rings'),('zone_outline_shape','integer_nm_native_outline_rings')]:
   before=x[role].wkb;pointwise=set_precision(x[role],1e-6,mode='pointwise');assert pointwise.wkb==before
   x[key]=rings(x[role]);f=O/(x['uuid']+'-'+role+'-current.wkb');f.write_bytes(before);of=O/(x['uuid']+'-'+role+'-exact-R155-before.wkb');of.write_bytes(old[role].wkb)
   roles.append({'UUID':x['uuid'],'raw_net':x['net'],'layer':x['layer'],'role':role,'before_file':str(of.resolve()),'before_sha256':sha(of),'after_file':str(f.resolve()),'after_sha256':sha(f),'integer_nm_metadata_field':key,'all_WKB_and_geometry_unchanged_from_R511':True,'same_all_nine_settings':{k:x[k]for k in FIELDS}})
  owned.append({'UUID':x['uuid'],'before_q':old,'after_q':x,'exact_before_role_hashes':{r:dg(old[r])for r in ('shape','zone_outline_shape')},'exact_after_role_hashes':{r:dg(x[r])for r in ('shape','zone_outline_shape')}})
 for z in c['zones']:
  old=next(x for x in pc['zones']if x['uuid']==z['uuid'])
  if z['uuid']not in UIDS:assert z==old;continue
  assert{k:v for k,v in z.items()if k!='fills'}=={k:v for k,v in old.items()if k!='fills'}
  fills.append({'UUID':z['uuid'],'raw_net':z['net'],'before_actual_zone':old,'after_actual_zone':z,'no_original_native_zone_definition_change':True})
 assert len(owned)==2 and len(fills)==2
 lf=O/'two-current-role-integer-metadata-inventory.json';put(lf,roles);b=copy.deepcopy(b);b['native_TMR_two_current_q_integer_metadata_r515']={'parent_R511_model_sha256':sha(M),'exact_current_role_inventory_file':str(lf.resolve()),'exact_current_role_inventory_sha256':sha(lf),'only_owned_UUIDs':sorted(UIDS),'historical_old_union_ledger_not_new_geometry_authority':True,'metadata_only_WKB_g_h_actual_arrays_exact':True}
 MS.restore_bound_field_current_precision_states(b,q)
 (O/'only-two-q-and-two-current-fill-exact-R155-delta.pkl').write_bytes(pickle.dumps({'parent_model_file':str(P.resolve()),'parent_model_sha256':sha(P),'only_q_replacements':owned,'only_current_fill_replacements':fills,'new_tracks':[],'new_vias':[],'old_native_Cu_deletes':[],'owned_new_same_raw_IO3_bypass_constituent':'a7168f4b-192a-52fe-a025-456a10753a51','all_other_q_roles_profiles_current_arrays_exact':True},protocol=5))
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,c),protocol=5))
 put(O/'receipt.json',{'status':'EXACT_TWO_OWNED_Q_NATIVE_TMR_KEEP_OUT_REPAIR_AND_IO3_BYPASS_PACKET_FRESH_GATE_PENDING','model_sha256':sha(O/'model.pkl'),'physical_source_graph_geometry_identity_R511_model_sha256':sha(M),'exact_R155_parent_sha256':sha(P),'only_two_owned_UUIDs':sorted(UIDS),'only_four_role_changes':roles,'only_two_current_fill_scopes_changed':True,'minimal_packet_sha256':sha(O/'only-two-q-and-two-current-fill-exact-R155-delta.pkl'),'all_original_Cu_holes_source_pads_design_outlines_rules_settings_exact':True,'integer_metadata_correction_only_from_R511_no_WKB_or_array_change':True,'full_scope_negative_witness_fail_history_preserved_R477_R487_R505_R507_R509':True,'inherited_R155_28refs_CORE_ROOT42_planner_current_NATIVE_FAIL_OPEN_retained':True,'unrelated_FIELD5_R465_13refs_383IO3_FAIL_not_overlaid':True,'current_full_FA4_567408669354_IO3_2A_mesh_drop_barrel_fault_thermal_native_fill_DRC':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R515 receipt',sha(O/'receipt.json'),'model',sha(O/'model.pkl'),flush=True)
if __name__=='__main__':main()
