"""Freeze explicit REG7 native owner profiles without changing model geometry."""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
import restore_field_current_mixed_precision_states_r366 as PS
O=H/'REG7-current-R155-explicit-native-owner-profile-authority-r375'
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
C=H/'REG7-native-support-minimal-current-delta-r312/minimal-delta-composition-contract.json'
FIELDS=('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir()
 assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 assert sha(C)=='09428391c2648468dfcef680576aca5e65e037914c99936069ff14ebfe6d471e'
 contract=json.loads(C.read_bytes());profile=contract['native_intended_settings'];assert set(profile)==set(FIELDS)
 assert profile==dict(priority=124,clearance_mm=.15,min_thickness_mm=.15,pad_connect_mode='FULL_SOLID',island_removal_mode=1,thermal_gap_mm=.15,thermal_bridge_width_mm=.3)
 g,h,b,q,actual=pickle.loads(M.read_bytes());PS.restore_bound_field_current_precision_states(b,q)
 qm={z['uuid']:z for z in q};am={z['uuid']:z for z in actual['zones']};rows=[]
 for uid in contract['new_REG_zone_UUIDs']:
  z=qm[uid];record=am[uid];assert z['net']==record['net'];assert z['layer']in record['fills']
  present={k:z[k]for k in FIELDS if k in z};assert all(v==profile[k]for k,v in present.items())
  actual_present={k:record[k]for k in FIELDS if k in record};assert all(v==profile[k]for k,v in actual_present.items())
  rows.append({'proposal_UUID':uid,'raw_net':z['net'],'layer':z['layer'],'physical_WKB_sha256':dg(z['shape']),'intended_WKB_sha256':dg(z['zone_outline_shape']),'complete_native_settings':dict(profile),'previously_missing_fields_only':[k for k in FIELDS if k not in z],'present_proposal_fields_preserved':present,'present_actual_filled_record_fields_preserved':actual_present,'exact_source_authorities':[{'source_kind':'EXACT_REG7_FROZEN_OWNER_NATIVE_INTENDED_SETTINGS','file':str(C),'sha256':sha(C),'field':'native_intended_settings','applies_only_to_enumerated_new_REG_zone_UUIDs':True}],'explicit_completion_reasons':{k:'EXPLICIT_REG7_OWNER_DECLARATION_FROZEN_R312_AND_ROUTINE_ROOT_AUTHORIZATION_2026_10_12; no measured native effect until API/refill'for k in FIELDS if k not in z},'ALL_current_h_q_WKB_present_settings_unchanged':True,'native_actual_declared_settings_gate':'OPEN'})
 assert len(rows)==7 and len({r['proposal_UUID']for r in rows})==7
 declaration=O/'explicit-owner-profile-declarations.json'
 put(declaration,{'schema':'current-owned-native-profile-owner-declarations-r375','current_model_file':str(M),'current_model_sha256':sha(M),'root_scope_authority':'Routine metadata-only native profile completion of seven NEW REG proposals, preserving all present fields. Priority124 binds frozen R312 modeled/native-intended profile; no native fill or manufacture claim.','all_geometry_h_physical_intended_WKB_and_present_q_fields_untouched':True,'rows':rows,'unbound_profile_fields':[],'pins':{str(M):sha(M),str(C):sha(C),PS.__file__:sha(PS.__file__)},'native_jobs':0,'model_written':False,'adopted':False})
 bound=[{**r,'authorizing_receipt_file':str(declaration),'authorizing_receipt_sha256':sha(declaration)}for r in rows]
 put(O/'receipt.json',{'verdict':'SEVEN_CURRENT_REG_NATIVE_OWNER_PROFILES_EXPLICIT_METADATA_AUTHORITY_PASS_NATIVE_OPEN','current_model_file':str(M),'current_model_sha256':sha(M),'owned_zone_native_profile_completion_rows':bound,'unbound_profile_fields':[],'owner_declaration_file':str(declaration),'owner_declaration_sha256':sha(declaration),'priority_authority':'Frozen exact R312 owner settings124, not an inferred native default','settings_do_not_modify_host_WKB_or_fills_or_h_or_rules_or_source':True,'native_jobs':0,'source_or_model_or_board_written':False,'adopted':False})
 print(json.dumps({'receipt_file':str(O/'receipt.json'),'receipt_sha256':sha(O/'receipt.json'),'declaration_sha256':sha(declaration),'complete_REG_roles':len(rows)}),flush=True)
if __name__=='__main__':main()
