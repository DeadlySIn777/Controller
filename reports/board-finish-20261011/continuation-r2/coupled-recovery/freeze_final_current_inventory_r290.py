"""Complete final current native inventory with exact sparse owner packets."""
import os,psutil
for task_env in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,mmap,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
import native_bound_original_inventory_diff_r270 as D
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 assert len(sys.argv)==3,'current_model.pkl fresh_inventory_directory';model=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert not out.exists();out.mkdir();_,h,_,_,_=pickle.loads(model.read_bytes());legacyfile=H.parent/'sbc-power/exploratory-SAFE-power-native-recipe-r169/receipt.json';assert sha(legacyfile)=='cbc2252a73de52c5a5b3290aa10384bde88762cdb5d5bc6e826e184d627d4e40';legacy={}
 with legacyfile.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as mapped:
  for key in('native_existing_owned_Cu_delete_rows','native_existing_owned_Cu_replacement_rows','native_existing_owned_footprint_replacement_rows','existing_via_prospective_new_flashes'):
   i=mapped.find(('"'+key+'"').encode());assert i>=0;j=mapped.find(b':',i)+1;legacy[key]=json.JSONDecoder().raw_decode(mapped[j:].decode().lstrip())[0]
 rotations=H.parent/'two-rotated-FP-native-collector-contract-r87/frozen-rotation-rows.json';assert sha(rotations)=='c79354f60f6fba0e38cd5f3df774876c4fc541ede3a2f27109d1a236f9c448d3';fp=legacy['native_existing_owned_footprint_replacement_rows']+json.loads(rotations.read_bytes());dpacket=H/'DIC-C1022-one-R214-joint-native-integration-delta-r222/receipt.json';assert sha(dpacket)=='bbf14c6887829a93d50fbf285aad61353dbc60eb30eaad1485036d410c89be0f';dr=json.loads(dpacket.read_bytes())['delete_rows'];extra=[];pins={}
 for path,want in((H.parent/'field-power/U11025-exact-health-ground-native-owned-recipe-r350/receipt.json','9dea5de413ac3531e28275d05d589adadc7242e73d6cba4c8a8fa6657161944c'),(H.parent/'field-power/REG7-native-support-minimal-current-delta-r312/receipt.json','6aaa5037a045da3f492bb46315f2f69e509501299af8257364cb2e7948b518c3'),(H.parent/'sbc-power/T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r273/receipt.json','97bc789fb90e688dc2b78c6f24a4877d4b7497055023a1748935c55a4a274692')):
  assert sha(path)==want;pins[str(path)]=want;r=json.loads(path.read_bytes())
  if 'delete_rows'in r:rows=r['delete_rows']
  elif 'file_manifest'in r:
   rowsfile=path.parent/'three-exact-owned-U17-delete-rows.json';assert sha(rowsfile)==r['file_manifest'][rowsfile.name];rows=json.loads(rowsfile.read_bytes());pins[str(rowsfile)]=sha(rowsfile)
  else:
   rowsfile=Path(r['exact_operation_file']);assert sha(rowsfile)==r['exact_operation_sha256'];rows=[x for x in json.loads(rowsfile.read_bytes())if x['action']=='remove'];pins[str(rowsfile)]=sha(rowsfile)
  for row in rows:
   ch=row.get('chunk_path')or row.get('exact_chunk_path')or row.get('chunk_file');cs=row.get('exact_original_chunk_sha256')or row.get('exact_chunk_sha256')or row.get('chunk_sha256');assert ch and cs and sha(ch)==cs;extra.append({'uuid':row['uuid'],'kind':row['kind'],'chunk_path':ch,'exact_original_chunk_sha256':cs,'expected_geometry':row.get('expected_geometry')or row.get('actual_original_geometry'),'authorizing_recipe_file':str(path),'authorizing_recipe_sha256':want})
 assert len(extra)==18;carrier=out/'explicit-applied-extra-native-delete-authorizers.json';put(carrier,{'delete_rows':extra,'exact_owner_packets':pins,'no_arbitrary_or_counterfactual_original_Cu_authorization':True});diff,summary=D.freeze(h,legacy,fp,dr,out,extra_delete_packages=[(carrier,sha(carrier))]);receipt={'verdict':'COMPLETE_CURRENT_ORIGINAL_NATIVE_INVENTORY_AUTHORIZED'if not summary['unbound_original_difference_rows']else'COMPLETE_CURRENT_ORIGINAL_NATIVE_INVENTORY_UNBOUND_FAIL','current_model_file':str(model),'current_model_sha256':sha(model),'diff_file':str(diff),'diff_sha256':sha(diff),'all_original_inventory_differences_bound':summary['all_original_inventory_differences_bound'],'unbound_original_difference_count':len(summary['unbound_original_difference_rows']),'only_exact_current_model_geometry_controls_emitter':True,'owner_packet_pins':pins,'R87_whole_file_sha256':sha(rotations),'all_current_incremental_physical_source_reference_native_effective_Cu_gate':'SEPARATE_REQUIRED_RECEIPT; this inventory is not geometric acceptance','CORE_DCbody_ROOT42_current_native':'FAIL/OPEN preserved','native_jobs':0,'board_or_source_or_model_written':False,'adopted':False,'helper_sha256':sha(D.__file__),'script_sha256':sha(__file__)};put(out/'receipt.json',receipt);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),'diff_sha256':sha(diff),'unbound_rows':len(summary['unbound_original_difference_rows']),'missing_tracks':len(summary['counts']['tracks']['missing_original_UUIDs']),'new_tracks':len(summary['counts']['tracks']['new_UUIDs']),'new_vias':len(summary['counts']['vias']['new_UUIDs'])}),flush=True)
if __name__=='__main__':main()
