"""Positive and negative strict-ledger checks; no geometry/source acceptance."""
from pathlib import Path
import json,pickle,hashlib,copy
import owned_native_additional_flashes_r113 as EF
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/additional-source-flash-contract-r119'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    mp=H/'sbc-power/core1v2-extra-In4-source-guarded-input-r112/model.pkl';assert sha(mp)=='b58fed8889bb7fed0f5460e16680d7c56fc69b14e04b5f528c98e1fa6811c8b7'
    g,h,b,z,c=pickle.loads(mp.read_bytes());basefile=H/'field-power/native-bound-field-base-r5/model.pkl';base=pickle.loads(basefile.read_bytes())['discrete'];rows,recipes=EF.collect(b,base,h);assert len(rows)==1
    uid=next(iter(rows));checks=[]
    for label,mutation in [('undeclared_1nm_coordinate',lambda v:v.update(x=round(v['x']+.000001,6))),('unknown_mask_metadata',lambda v:v.update(unknown_extra_flash_flag=True)),('dropped_original_actual_layer',lambda v:v.update(flashed=['F.Cu','In4.Cu'])),('undeclared_second_new_layer',lambda v:v.update(flashed=v['flashed']+['In2.Cu']))]:
        vs=[copy.deepcopy(v) if v['uuid']==uid else v for v in h['vias']];mutation(next(v for v in vs if v['uuid']==uid))
        rejected=False
        try:EF.collect(b,base,{**h,'vias':vs})
        except AssertionError:rejected=True
        assert rejected;checks.append({'negative_control':label,'rejected':rejected})
    r={'verdict':'PASS_EXACT_EXTRA_FLASH_CONTRACT_AND4_NEGATIVE_CONTROLS_ONLY','candidate_host_model_sha256':sha(mp),'strict_helper_sha256':sha(H/'sbc-power/owned_native_additional_flashes_r113.py'),'prepared_emitter_sha256':sha(H/'sbc-power/emit_complete_power_recipe_r114.py'),'exact_via_UUID':uid,'bound_recipes':recipes,'negative_controls':checks,'old_native_via_bytes_unchanged':True,'actual_native_extra_flash_source_contact_current_and_all_foreign_retention':'OPEN','native_jobs':0,'board_written':False}
    (O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('EXTRA_FLASH_STRICT_CONTRACT_PASS',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
