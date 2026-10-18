"""Explicit metadata-only profile authority; model geometry is not altered."""
import sys,json,pickle,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
from verify_source import parse,child,atom
FIELDS=('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 assert len(sys.argv)==3,'current_model.pkl fresh_profile_directory';model=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert not out.exists();out.mkdir();_,h,_,q,c=pickle.loads(model.read_bytes());actual={z['uuid']:z for z in c['zones']};rows=[];fail=[];pins={str(model):sha(model)}
 chunks={'e8ec0287-e6d1-597d-8ad8-c4ab74280f6c':H.parent/'field-power/SAFE-U10017-wider-native-owned-recipe-r183/e8ec0287-e6d1-597d-8ad8-c4ab74280f6c.zone-chunk','c920c894-e731-5293-a67a-b83c9ff1ffe9':H.parent/'field-power/R11054-static-and-AUX-bleed-native-owned-recipe-r208/c920c894-e731-5293-a67a-b83c9ff1ffe9.zone-chunk'}
 for z in q:
  missing=[k for k in FIELDS if k not in z]
  if not missing:continue
  owner={k:z[k]for k in FIELDS if k in z};receipt_sources=[];reason={}
  if z['uuid']in chunks:
   path=chunks[z['uuid']];ast=parse(path.read_text());assert atom(ast,'uuid')==z['uuid']and atom(ast,'net')==z['net']and atom(ast,'layer')==z['layer'];assert child(ast,'connect_pads')[1]=='yes';fill=child(ast,'fill');profile={'priority':int(atom(ast,'priority')),'clearance_mm':float(atom(child(ast,'connect_pads'),'clearance')),'min_thickness_mm':float(atom(ast,'min_thickness')),'pad_connect_mode':'FULL_SOLID','island_removal_mode':int(atom(fill,'island_removal_mode')),'thermal_gap_mm':float(atom(fill,'thermal_gap')),'thermal_bridge_width_mm':float(atom(fill,'thermal_bridge_width'))};pins[str(path)]=sha(path);receipt_sources.append({'source_kind':'EXACT_EXISTING_OWNER_NATIVE_ZONE_CHUNK','file':str(path),'sha256':sha(path)})
   assert all(profile[k]==v for k,v in owner.items());owner=profile
  else:
   record=actual[z['uuid']];assert record['net']==z['net'];receipt_sources.append({'source_kind':'EXACT_CURRENT_SAME_UUID_PROJECTED_FILLED_ZONE_METADATA','model_file':str(model),'model_sha256':sha(model),'UUID':z['uuid'],'exact_record_metadata':{k:v for k,v in record.items()if k!='fills'}})
   for k in missing:
    if k in record:owner[k]=record[k];reason[k]='EXACT_CURRENT_ACTUAL_FILLED_ZONE_METADATA'
   remaining=[k for k in FIELDS if k not in owner]
   if any(k not in('thermal_gap_mm','thermal_bridge_width_mm')for k in remaining):fail.append({'UUID':z['uuid'],'unbound_nonthermal_fields':remaining,'actual_metadata':receipt_sources[-1]});continue
   assert owner['pad_connect_mode']=='FULL_SOLID'
   for k,value in(('thermal_gap_mm',.15),('thermal_bridge_width_mm',.3)):
    if k not in owner:owner[k]=value;reason[k]='EXPLICIT_NEW_OWNER_DECLARATION_AUTHORIZED_BY_ROOT_2026_10_12; semantically inactive under FULL_SOLID, actual native setting check mandatory'
  assert all(owner[k]==z[k]for k in FIELDS if k in z);assert set(owner)==set(FIELDS)
  rows.append({'proposal_UUID':z['uuid'],'physical_WKB_sha256':hashlib.sha256(z['shape'].wkb).hexdigest(),'intended_WKB_sha256':hashlib.sha256(z['zone_outline_shape'].wkb).hexdigest(),'complete_native_settings':owner,'previously_missing_fields_only':missing,'exact_source_authorities':receipt_sources,'explicit_completion_reasons':reason,'ALL_current_h_q_WKB_present_settings_unchanged':True,'native_actual_declared_settings_gate':'OPEN'})
 declaration=out/'explicit-owner-profile-declarations.json';put(declaration,{'schema':'current-owned-native-profile-owner-declarations-r276','current_model_file':str(model),'current_model_sha256':sha(model),'all_geometry_h_physical_intended_WKB_and_present_q_fields_untouched':True,'root_scope_authority':'Explicit fresh metadata-only owner manifest: U17/AUX exact owned native chunks; others exact current sameUUID actual filled metadata; absent thermal only FULL_SOLID explicit .15/.3, native check mandatory.','rows':rows,'unbound_profile_fields':fail,'pins':pins,'native_jobs':0,'model_written':False,'adopted':False});bound=[{**r,'authorizing_receipt_file':str(declaration),'authorizing_receipt_sha256':sha(declaration)}for r in rows];put(out/'receipt.json',{'verdict':'EXPLICIT_CURRENT_NATIVE_PROFILE_COMPLETION_METADATA_ONLY_PASS_NATIVE_OPEN'if not fail else'EXPLICIT_CURRENT_NATIVE_PROFILE_COMPLETION_MISSING_AUTHORITY_FAIL','current_model_file':str(model),'current_model_sha256':sha(model),'owned_zone_native_profile_completion_rows':bound,'unbound_profile_fields':fail,'owner_declaration_file':str(declaration),'owner_declaration_sha256':sha(declaration),'native_jobs':0,'source_or_model_or_board_written':False,'adopted':False});print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),'complete_roles':len(rows),'unbound_roles':len(fail)}),flush=True)
if __name__=='__main__':main()
