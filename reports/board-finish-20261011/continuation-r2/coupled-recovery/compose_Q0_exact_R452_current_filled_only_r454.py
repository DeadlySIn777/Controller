"""Bind smaller sparse recipe into immutable actual filled records only."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'compose_Q0_exact_R428_current_filled_only_r434.py'
code=base.read_text().replace('Q0-exact-R428-current-filled-only-r434','Q0-exact-R452-current-filled-only-r454').replace('Q0-R426-exact-native-owned-operation-r428','Q0-R450-exact-native-owned-operation-r452').replace('f0b31e152b7f13c0a00401149176fb5dff69c4743121654439ca39a82dfeb27c','ed12eb485bd83caef6632d6d7aaf35bbddf18b06b4dbe277c34447b76bee030e').replace('c884f640a6b722b977a8e8256c8f0463b3450c979e064ad9e40bc21fbef041b9','9c56a850a48dca1f08eadab78db04d3ac41c8b7eeab8d614a41d77f087a84b11')
old="sv=next(v for v in h['vias']if v['uuid']==op['original_SENSE_via_UUID']);assert sv['flashed']==['F.Cu','B.Cu'];sv['flashed']=['F.Cu','In2.Cu','B.Cu'];sv['prospective_additional_natural_annulus']='In2.Cu; native attestation mandatory, flags untouched';newpads=[]"
new="""extraanns=[]
for uid in op['original_SENSE_via_UUIDs']:
 sv=next(v for v in h['vias']if v['uuid']==uid);assert sv['flashed']==['F.Cu','B.Cu'];sv['flashed']=['F.Cu','In2.Cu','B.Cu'];sv['prospective_additional_natural_annulus']='In2.Cu; native attestation mandatory, flags untouched';extraanns.append({**sv,'flashed':['In2.Cu'],'existing_SENSE_added_layer_only':True})
newpads=[]"""
assert old in code;code=code.replace(old,new,1)
old="assert fp['uuid']==op['R10016_FP_UUID'];fp['x']=229.86"
new="assert 'uuid' not in fp and(fp['x'],fp['y'])==(230.36,167.162);oldfpast=K.Q.parse(Path(op['exact_FP_before_file']).read_text());assert K.Q.atom(oldfpast,'uuid')==op['R10016_FP_UUID'];assert {K.Q.atom(p,'uuid')for p in K.Q.children(oldfpast,'pad')}==padids;fp['x']=229.86"
assert old in code;code=code.replace(old,new,1).replace("extraann={**sv,'flashed':['In2.Cu']};",'').replace('nt+nv+[extraann]','nt+nv+extraanns').replace("item is extraann and layer!='In2.Cu'","item.get('existing_SENSE_added_layer_only')and layer!='In2.Cu'").replace('item is extraann',"bool(item.get('existing_SENSE_added_layer_only'))").replace('source_R428_receipt_sha256','source_R452_receipt_sha256')
exec(compile(code,str(base),'exec'))
