"""Explicit same-UUID native Cu replacement adapter for frozen field R102.

This proves recipe applicability and exact serialized mutation bounds only.
It does not grant full contact, source, reference, current, or native approval.
"""
import json,pickle,hashlib,re,copy,sys
from pathlib import Path
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
from verify_source import parse,child,atom
O=H/'sbc-power/u19008-existing-native-copper-adapter-r99'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    rf=H/'field-power/u19008-corrected-native-owned-recipe-r102/receipt.json';assert sha(rf)=='1d012f2eb0b92b3dac83bab686c1506f1783251a19ff3536f361915f39e29003';recipe=json.loads(rf.read_text())
    native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)==recipe['native_base_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    basefile=H/'field-power/native-bound-field-base-r5/model.pkl';base=pickle.loads(basefile.read_bytes())['discrete'];by={kind:{q['uuid']:q for q in base[kind]} for kind in ('tracks','vias')}
    _,chunks,_=C.O.C.pcbtext.split(native.read_bytes());replacement_rows=[];delete_rows=[]
    for row in recipe['exact_original_replacements']:
        kind=row['kind'];uid=row['uuid'];key='tracks' if kind=='segment' else 'vias';old=by[key][uid];new=row['replacement_geometry'];op=Path(row['original_chunk_path']);np=Path(row['replacement_chunk_path'])
        assert sha(op)==row['original_chunk_sha256'] and sha(np)==row['replacement_chunk_sha256'];assert sum(ch==op.read_bytes() for ch in chunks)==1
        oa=parse(op.read_text());na=parse(np.read_text());token='end' if kind=='segment' else 'at';pattern=rb'\('+token.encode()+rb'\s+[^)]*\)'
        assert len(re.findall(pattern,op.read_bytes()))==len(re.findall(pattern,np.read_bytes()))==1
        assert re.sub(pattern,b'<EXACT-OWNED-FIELD>',op.read_bytes())==re.sub(pattern,b'<EXACT-OWNED-FIELD>',np.read_bytes()),'Unowned serialized bytes changed'
        assert [q for q in oa if not isinstance(q,list) or q[0]!=token]==[q for q in na if not isinstance(q,list) or q[0]!=token]
        assert atom(oa,'uuid')==atom(na,'uuid')==uid and atom(oa,'net')==atom(na,'net')==row['raw_net']==old['net']==new['net']
        if kind=='via':
            assert child(oa,'at')[1:]==['65.495','111.8'];assert tuple(map(float,child(na,'at')[1:]))==(new['x'],new['y'])==(65.62,111.8)
            a={k:v for k,v in old.items() if k not in ('x','y','mask_provenance')};b={k:v for k,v in new.items() if k not in ('x','y','mask_provenance')};assert a==b
            assert new['mask_provenance']=='prospective relocation; exact native F/In1/In4 retained-flash obligation'
        else:
            assert tuple(map(float,child(oa,'end')[1:]))==tuple(old['b']);assert tuple(map(float,child(na,'end')[1:]))==tuple(new['b'])==(65.62,111.8)
            assert {k:v for k,v in old.items() if k!='b'}=={k:v for k,v in new.items() if k!='b'}
        out_old=O/(uid+'.original-'+kind+'-chunk');out_new=O/(uid+'.replacement-'+kind+'-chunk');out_old.write_bytes(op.read_bytes());out_new.write_bytes(np.read_bytes())
        replacement_rows.append({'uuid':uid,'kind':kind,'raw_net':row['raw_net'],'expected_original_geometry':old,'expected_replacement_geometry':new,'original_chunk_file':str(out_old.resolve()),'original_chunk_sha256':sha(out_old),'replacement_chunk_file':str(out_new.resolve()),'replacement_chunk_sha256':sha(out_new),'authorizing_recipe_file':str(rf.resolve()),'authorizing_recipe_sha256':sha(rf),'exact_native_changed_fields':[token],'every_other_AST_node_and_serialized_byte_unchanged':True,'same_existing_UUID_replacement_not_addition':True,'original_actual_native_flash_mask':old.get('flashed'),'required_post_refill_retained_flash_mask':new.get('flashed'),'host_only_mask_provenance_change_authorized_literal':new.get('mask_provenance') if kind=='via' else None,'all_old_shared_contacts_source_reference_and_native_refill_gates':'OPEN'})
    for row in recipe['exact_original_deletes']:
        kind=row['kind'];uid=row['uuid'];assert kind=='segment';expected=by['tracks'][uid];assert row['geometry']==expected
        f=Path(row['chunk_path']);assert sha(f)==row['chunk_sha256'] and sum(ch==f.read_bytes() for ch in chunks)==1
        out=O/(uid+'.delete-original-segment-chunk');out.write_bytes(f.read_bytes());delete_rows.append({'uuid':uid,'kind':kind,'raw_net':row['raw_net'],'expected_geometry':expected,'chunk_path':str(out.resolve()),'exact_original_chunk_sha256':sha(out)})
    assert len(replacement_rows)==2 and len(delete_rows)==1
    rep=O/'replacement-only-recipe.json';rep.write_text(json.dumps({'verdict':'EXACT_SAME_UUID_REPLACEMENT_CONTRACT_APPLICABLE_FULL_GATES_OPEN','parent_native_board_sha256':sha(native),'authorizing_recipe_file':str(rf.resolve()),'authorizing_recipe_sha256':sha(rf),'replacement_rows':replacement_rows,'no_unlisted_changed_native_Cu_fields_authorized':True,'native_jobs':0,'board_written':False},indent=2)+'\n')
    rem=O/'remove-only-recipe.json';rem.write_text(json.dumps({'verdict':'EXACT_REMOVE_ONLY_CONTRACT_APPLICABLE_OUTSIDE_CONTACT_GATES_OPEN','parent_native_board_sha256':sha(native),'authorizing_recipe_file':str(rf.resolve()),'authorizing_recipe_sha256':sha(rf),'delete_rows':delete_rows,'native_jobs':0,'board_written':False},indent=2)+'\n')
    (O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_R102_SAME_UUID_ADAPTER_BYTE_AND_GEOMETRY_CONTRACT_PASS_ONLY','native_base_sha256':sha(native),'authorizing_recipe_sha256':sha(rf),'replacement_recipe_file':str(rep.resolve()),'replacement_recipe_sha256':sha(rep),'remove_recipe_file':str(rem.resolve()),'remove_recipe_sha256':sha(rem),'native_existing_owned_Cu_replacement_rows':replacement_rows,'full_joint_source_contact_geometry_reference_current_and_native_gates':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n');print('R102_REPLACEMENT_ADAPTER_PASS',sha(rep),sha(rem),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
