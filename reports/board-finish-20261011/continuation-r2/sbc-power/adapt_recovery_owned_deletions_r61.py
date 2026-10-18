"""Exact remove-only adapters; original C32 and AO19 receipts stay immutable."""
import json,pickle,hashlib,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;R2=HERE.parent
sys.path.insert(0,str(R2/'field-power'))
from verify_source import parse,child,atom
OUT=HERE/'recovery-owned-deletion-adapters-r61'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    parent=R2/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';native=parent.read_bytes()
    bf=R2/'field-power/native-bound-field-base-r5/model.pkl';base=pickle.loads(bf.read_bytes())['discrete'];byid={q['uuid']:q for k in ('tracks','vias') for q in base[k]}
    outputs=[]
    for name,receipt,digest,count in [('C10036',R2/'coupled-recovery/c10036-native-owned-ledger-r32/receipt.json','017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb',6),('AO1',R2/'coupled-recovery/ao1-reference-coupled-r19.json','203f9f36ec4979ba2715139a16058a38f40f4d9fdcb4ec9f95fad07c4c6526b7',7)]:
        assert sha(receipt)==digest;r=json.loads(receipt.read_text());rows=[]
        if name=='C10036':
            removes=[q for q in r['rows'] if q['action']=='remove'];assert len(removes)==count
            chunks=[]
            for row in removes:
                path=Path(row['exact_chunk_path']);assert sha(path)==row['exact_chunk_sha256'];chunks.append((row['uuid'],path.read_bytes(),row['kind'],str(path.resolve()),sha(path)))
        else:
            assert len(r['exact_removed_chunks'])==count
            chunks=[]
            for uid,text in r['exact_removed_chunks'].items():
                data=text.encode('utf-8');kind=parse(text)[0];path=OUT/(name+'-'+uid+'.original-remove-chunk');path.write_bytes(data);chunks.append((uid,data,kind,str(path.resolve()),sha(path)))
        for uid,data,kind,path,digest2 in chunks:
            assert kind in ('segment','via') and uid in byid
            assert native.count(data)==1,('authoritative_old_chunk_not_exactly_once_in_eedf',name,uid)
            a=parse(data.decode('utf-8'));expected=byid[uid];assert atom(a,'uuid')==uid and atom(a,'net')==expected['net']
            if kind=='segment':
                assert expected['a']==[float(x) for x in child(a,'start')[1:]] and expected['b']==[float(x) for x in child(a,'end')[1:]] and expected['w']==float(atom(a,'width')) and expected['layer']==atom(a,'layer')
                assert expected['locked']==(atom(a,'locked')=='yes')
            else:
                assert [expected['x'],expected['y']]==[float(x) for x in child(a,'at')[1:]] and expected['d']==float(atom(a,'size')) and expected['drill']==float(atom(a,'drill'))
                assert child(a,'layers')[1:]==['F.Cu','B.Cu']
            rows.append({'uuid':uid,'kind':kind,'raw_net':expected['net'],'expected_geometry':expected,'chunk_path':path,'exact_original_chunk_sha256':digest2,'authoritative_original_recipe_file':str(receipt.resolve()),'authoritative_original_recipe_sha256':sha(receipt),'exact_eedf_chunk_presence_verified':True,'all_outside_shared_contacts_must_be_restored':True})
        output=OUT/(name+'-remove-only-recipe.json');output.write_text(json.dumps({'schema':'canonical-exact-owned-native-remove-only/v1','verdict':'EXACT_REMOVE_ONLY_ADAPTER_FROZEN_NO_NEW_GEOMETRY','authoritative_source_receipt_file':str(receipt.resolve()),'authoritative_source_receipt_sha256':sha(receipt),'original_source_authority_preserved':True,'verified_native_parent_file':str(parent.resolve()),'verified_native_parent_sha256':sha(parent),'native_base_cache_file':str(bf.resolve()),'native_base_cache_sha256':sha(bf),'delete_rows':rows,'new_items_in_adapter':0,'all_additions_remain_authoritative_separate_recipes':True,'native_jobs':0,'board_written':False},indent=2)+'\n')
        outputs.append({'file':str(output.resolve()),'sha256':sha(output),'exact_removals':count,'all_exact_eedf_chunks_present':True})
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'PASS_EXACT_REMOVE_ONLY_RECOVERY_ADAPTERS','outputs':outputs,'original_receipts_and_geometry_unmodified':True,'native_jobs':0,'board_written':False},indent=2)+'\n');print('RECOVERY_ADAPTERS_R61',outputs,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
