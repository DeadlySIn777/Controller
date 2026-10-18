"""Check the forwarded old-barrel obligation against saved independent native evidence."""
import copy,hashlib,json
from pathlib import Path
import native_existing_extra_flash_contract_r1 as EF
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=H/'sbc-power/core1v2-source-barrel-extra-In4-proposal-r111';f=d/'extra-flash-obligation.json';r=json.loads(f.read_bytes());uid=r['via_uuid'];chunk=Path(r['original_native_via_chunk_file']);data=chunk.read_bytes();parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)==r['parent_native_board_sha256'] and parent.read_bytes().count(data)==1
 native=H/'core1v2-native-diagnostic-r138';cu=json.loads((native/'expected-Cu.json').read_bytes())['copper'];actual=json.loads((native/'scoped-native-fill/actual-via-flashes.json').read_bytes());report=json.loads((native/'independent-selected-CORE1V2-r139.json').read_bytes())
 row={'uuid':uid,'original_native_flashes':r['original_actual_native_flash_mask'],'required_after_refill':r['required_native_postfill_flash_mask'],'same_existing_serialized_via':True,'exact_consumed_prospective_metadata':{'prospective_new_flash_requires_native_refill':'In4.Cu'},'explicit_ledger_file':str(f.resolve()),'explicit_ledger_sha256':sha(f)}
 original={uid:data};after=original.copy();ok,pins=EF.collect([row],original,after,cu,{},{});assert len(ok)==1 and ok[0]['required_actual_fresh_refill_flashes']==['F.Cu','In3.Cu','In4.Cu']
 controls=[]
 for name in ['lost_old_flash','wrong_layer_metadata','deleted_barrel','changed_serialized_chunk','moved_diameter','duplicate_obligation']:
  rows=[copy.deepcopy(row)];a=original.copy();c=copy.deepcopy({uid:cu[uid]});removed={}
  if name=='lost_old_flash':rows[0]['required_after_refill']=['In4.Cu']
  elif name=='wrong_layer_metadata':rows[0]['exact_consumed_prospective_metadata']['prospective_new_flash_requires_native_refill']='In2.Cu'
  elif name=='deleted_barrel':removed={uid:data}
  elif name=='changed_serialized_chunk':a[uid]=data+b' '
  elif name=='moved_diameter':c[uid]['diameters_IU']['F.Cu']+=1
  elif name=='duplicate_obligation':rows.append(copy.deepcopy(row))
  try:EF.collect(rows,original,a,c,removed,{})
  except AssertionError:controls.append({'name':name,'rejected':True})
  else:raise AssertionError('Negative control accepted: '+name)
 out=H/'native-existing-extra-flash-r8-check.json';assert not out.exists();out.write_text(json.dumps({'verdict':'PASS_EXACT_EXISTING_CORE_SOURCE_BARREL_FORWARDING_AND_SIX_REJECTION_CONTROLS','required_actual_postfill_mask':ok[0]['required_actual_fresh_refill_flashes'],'controls':controls,'independent_native_report_sha256':sha(native/'independent-selected-CORE1V2-r139.json'),'independent_native_report_verdict':report.get('verdict'),'independent_actual_flash_file_sha256':sha(native/'scoped-native-fill/actual-via-flashes.json'),'input_sha256':{**pins,str(Path(EF.__file__).resolve()):sha(EF.__file__),str(Path(__file__).resolve()):sha(__file__),str(native/'expected-Cu.json'):sha(native/'expected-Cu.json'),str(parent):sha(parent)},'whole_joint_native_measurement':'OPEN','native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n');print('R8_EXTRA_FLASH_COLLECTOR_PASS',len(controls),report.get('verdict'),flush=True)
if __name__=='__main__':main()
