"""Freeze exactly one native FP root translation; preserve every other byte."""
import hashlib,json,importlib.util
from pathlib import Path
import freeze_owned_native_parts_r3 as F
HERE=Path(__file__).resolve().parent;OUT=HERE/'r17031-native-translation-contract-r81'
SHA='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes())
    board=HERE.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)==SHA
    gate=HERE/'r17031-independent-analytic-r79/receipt.json';assert sha(gate)=='95107ec12b11daf8bb2699f5b6d150008b276ea9023b43a8b5f24951f164b3db';assert json.loads(gate.read_text())['errors']==[]
    nom=HERE/'r17031-coupled-native-mask-nominations-r74/receipt.json';assert sha(nom)=='2bdfbb31ba0a99f9a90fdbae1128674f2e982a9e42f426bc87041a3021208c31';target=json.loads(nom.read_text())['rows'][0]['target_FP_pose'];assert target==[247.252,34.197,0.]
    spec=importlib.util.spec_from_file_location('native_translation_pcbtext',F.I.PARSER.parent/'pcbtext.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);head,chunks,tail=P.split(board.read_bytes())
    old=next(ch for ch in chunks if P.chunk_kind(ch)=='footprint' and b'(property "Reference" "R17031"' in ch);uid=P.chunk_uuid(old);assert uid=='22ecc877-cc67-4abe-8582-59c4abee8832'
    ns=F.parser();parse,child,children,atom=(ns[n] for n in ('sexpr_parse','child','children','atom'));a=parse(old.decode());before=child(a,'at');assert before==['at','250.752','32.697'];text=old.decode();changed=[]
    for x,y in reversed(F.top_spans(text)):
        node=parse(text[x:y])
        if node[0]=='at':changed.append({'kind':'root_at_only','original_tokens':node,'replacement_tokens':['at','247.252','34.197','0']});text=text[:x]+'(at 247.252 34.197 0)'+text[y:]
    assert len(changed)==1;b=parse(text);assert [n for n in a if not isinstance(n,list) or n[0]!='at']==[n for n in b if not isinstance(n,list) or n[0]!='at']
    of=OUT/'R17031.original-exact-footprint-chunk';nf=OUT/'R17031.translated-footprint-chunk';of.write_bytes(old);nf.write_bytes(text.encode());pads=[];posepads=[];texts=[];props=[]
    for q in children(b,'pad'):
        at=child(q,'at');local=[float(at[1]),float(at[2]),float(at[3]) if len(at)>3 else 0.];xy=[round(target[0]+local[0],6),round(target[1]+local[1],6)];layers=child(q,'layers')[1:];puid=atom(q,'uuid');raw=atom(q,'net');pin=q[1]
        pads.append({'type':q[2],'shape':q[3],'size_mm':[float(v) for v in child(q,'size')[1:]],'drill_native':child(q,'drill'),'native_declared_layers':layers,'expected_copper_layer_names':['F.Cu'],'roundrect_rratio':atom(q,'roundrect_rratio'),'custom_primitive_native':child(q,'primitives'),'expected_raw_net':raw,'physical_pad_UUID':puid,'pin':pin,'at_native':local,'absolute_position_mm':xy,'absolute_angle_deg':local[2]})
        posepads.append({'pad_uuid':puid,'pin':pin,'raw_net':raw,'absolute_center_mm':xy,'local_at_native':local,'actual_original_clone_native_flashes':['F.Cu']})
    for q in children(b,'property')+children(b,'fp_text'):
        at=child(q,'at');local=[float(at[1]),float(at[2]),float(at[3]) if len(at)>3 else 0.];texts.append({'kind':q[0],'identity':q[1],'local_at_native':local,'absolute_position_mm':[round(target[0]+local[0],6),round(target[1]+local[1],6)],'native_angle_deg':local[2],'native_layer':atom(q,'layer')})
        if q[0]=='property':props.append({'name':q[1],'value':q[2],'native_UUID':atom(q,'uuid')})
    pose={'ref':'R17031','native_footprint_uuid':uid,'root_pose_mm_deg':target,'layer':'F.Cu','schematic_path':atom(b,'path'),'chunk_path':str(nf.resolve()),'chunk_sha256':sha(nf),'pads':posepads}
    mask={'ref':'R17031','footprint_UUID':uid,'target_native_layer':'F.Cu','target_pose_mm_deg':target,'exact_chunk_sha256':sha(nf),'pads':pads,'texts':texts}
    auth=OUT/'authorization.json';write(auth,{'verdict':'EXACT_TRANSLATION_SCOPED_GEOMETRY_AUTHORIZED_FULL_SOURCE_NATIVE_CURRENT_PENDING','ref':'R17031','uuid':uid,'native_parent_file':str(board.resolve()),'native_parent_sha256':SHA,'source_export_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','nominee_recipe_file':str(nom.resolve()),'nominee_recipe_sha256':sha(nom),'independent_analytic_gate_file':str(gate.resolve()),'independent_analytic_gate_sha256':sha(gate),'exact_original_FP_chunk_sha256':sha(of),'exact_replacement_FP_chunk_sha256':sha(nf),'exact_changed_fields':changed,'all_other_native_AST_nodes_and_bytes_unchanged':True,'original_root_angle_implicit_zero':True,'original_native_source_path':atom(a,'path'),'local_pad_UUID_raw_net_shape_size_mask_paste_and_angles_unchanged':True,'local_text_layer_angle_and_properties_unchanged':True,'properties':props,'source_and_contact_proof_dependency':'r17031-translated-source-composition-r78/receipt.json must PASS before final adoption','native_refill_DRC_full_current_and_all_foreign_contacts':'OPEN','board_written':False,'native_jobs':0})
    row={'uuid':uid,'ref':'R17031','original_chunk_file':str(of.resolve()),'original_chunk_sha256':sha(of),'replacement_chunk_file':str(nf.resolve()),'replacement_chunk_sha256':sha(nf),'authorizing_recipe_file':str(auth.resolve()),'authorizing_recipe_sha256':sha(auth),'original_root_pose_mm_deg':[250.752,32.697,0.],'original_root_at_serialized_tokens':before[1:],'replacement_root_pose_mm_deg':target,'native_pose_row':pose,'native_mask_and_text_row':mask}
    write(OUT/'receipt.json',{'verdict':'EXACT_NATIVE_FP_TRANSLATION_CHUNKS_READY_FULL_SOURCE_AND_NATIVE_PENDING','parent_native_board_sha256':SHA,'native_existing_owned_footprint_replacement_rows':[row],'native_local_pad_and_text_geometry_unchanged':True,'one_root_at_only_native_edit':True,'all_coordinates_integer_nm':True,'native_jobs':0,'board_written':False});assert sha(board)==SHA;print('R81_FP_CONTRACT',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
