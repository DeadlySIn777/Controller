"""Contract-only exact R102 collector check and unowned mutation negatives."""
import json,pickle,copy,hashlib
from pathlib import Path
import owned_native_cu_replacements_r100 as C
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/cu-replacement-collector-contract-r103'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    base=pickle.loads((H/'field-power/native-bound-field-base-r5/model.pkl').read_bytes())['discrete'];af=H/'sbc-power/u19008-existing-native-copper-adapter-r99/replacement-only-recipe.json';assert sha(af)=='4fbf5b6d239b6308a757bc5298485688cb1726b4ba43217d723a6552aa066d03';a=json.loads(af.read_text());bound={'existing_native_owned_Cu_replacement_recipes':[{'file':str(af.resolve()),'sha256':sha(af)}]}
    replacements={r['uuid']:r['expected_replacement_geometry'] for r in a['replacement_rows']};h={**base,**{kind:[copy.deepcopy(replacements.get(q['uuid'],q)) for q in base[kind]] for kind in ('tracks','vias')}}
    rows,owned,recipes=C.collect(bound,base,h);assert len(rows)==2
    negatives=[]
    for label in ('undeclared_1nm_position','unknown_existing_via_metadata'):
        trial={**h,'vias':[dict(q) for q in h['vias']]};v=next(q for q in trial['vias'] if q['uuid']=='58446867-9078-4bf3-93c2-2c613644426e')
        if label=='undeclared_1nm_position':v['x']=65.620001
        else:v['unqualified_new_flag']=True
        try:C.collect(bound,base,trial)
        except AssertionError as err:negatives.append({'label':label,'rejected':True,'reason':str(err)})
        else:raise AssertionError('Unowned mutation accepted:'+label)
    binding=O/'binding-recipe.json';binding.write_text(json.dumps(bound,indent=2)+'\n')
    (O/'receipt.json').write_text(json.dumps({'verdict':'PASS_EXACT_R102_CU_COLLECTOR_CONTRACT_AND_TWO_UNOWNED_NEGATIVES','helper_file':str(Path(C.__file__).resolve()),'helper_sha256':sha(Path(C.__file__)),'adapter_sha256':sha(af),'binding_file':str(binding.resolve()),'binding_sha256':sha(binding),'native_existing_owned_Cu_replacement_rows':rows,'negative_controls':negatives,'uses_contract_only_synthetic_host_overlay_not_joint_geometry_or_source_proof':True,'full_joint_source_contact_reference_current_native_gates':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n');print('CU_REPLACEMENT_COLLECTOR_CONTRACT_PASS',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
