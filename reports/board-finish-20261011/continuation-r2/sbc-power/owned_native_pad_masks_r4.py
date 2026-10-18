"""Native chunk-derived pad masks/shapes and text poses for root attestation."""
import json,hashlib,math
from pathlib import Path
import freeze_owned_native_parts_r3 as F
def main():
    path=F.HERE/'owned-native-parts-r4/receipt.json';r=json.loads(path.read_text());ns=F.parser();parse,child,children,atom=(ns[k] for k in ('sexpr_parse','child','children','atom'));rows=[]
    for fp in r['footprint_replacements']:
        p=Path(fp['new_chunk_path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==fp['new_chunk_sha256'];root=parse(p.read_text());theta=math.radians(-fp['target_pose_mm_deg'][2]);expected={p['uuid']:p for p in fp['actual_native_pad_positions']};pads=[];texts=[]
        for q in children(root,'pad'):
            uid=atom(q,'uuid');layers=child(q,'layers')[1:];shape={'type':q[2],'shape':q[3],'size_mm':[float(x) for x in child(q,'size')[1:]],'drill_native':child(q,'drill'),'native_declared_layers':layers,'expected_copper_layer_names':[x for x in layers if x.endswith('.Cu')],'roundrect_rratio':atom(q,'roundrect_rratio'),'custom_primitive_native':child(q,'primitives'),'expected_raw_net':atom(q,'net'),'physical_pad_UUID':uid,'pin':q[1],'at_native':[float(x) for x in child(q,'at')[1:]],'absolute_position_mm':expected[uid]['position_mm'],'absolute_angle_deg':expected[uid]['absolute_angle_deg']};assert set(layers)=={'F.Cu','F.Paste','F.Mask'} or set(layers)=={'B.Cu','B.Paste','B.Mask'},('Unexpected pad-layer family',fp['ref'],q[1],layers);pads.append(shape)
        for q in children(root,'property')+children(root,'fp_text'):
            at=child(q,'at')
            if at is None:continue
            x,y=float(at[1]),float(at[2]);pos=[round(fp['target_pose_mm_deg'][0]+x*math.cos(theta)-y*math.sin(theta),6),round(fp['target_pose_mm_deg'][1]+x*math.sin(theta)+y*math.cos(theta),6)];texts.append({'kind':q[0],'identity':q[1],'local_at_native':[float(v) for v in at[1:]],'absolute_position_mm':pos,'native_angle_deg':float(at[3]) if len(at)>3 else 0.,'native_layer':atom(q,'layer')})
        rows.append({'ref':fp['ref'],'footprint_UUID':fp['uuid'],'target_native_layer':fp['layer'],'target_pose_mm_deg':fp['target_pose_mm_deg'],'exact_chunk_sha256':fp['new_chunk_sha256'],'pads':pads,'texts':texts})
    out=path.parent/'pad-mask-and-text-ledger.json';result={'recipe':str(path.resolve()),'recipe_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_parent_sha256':F.SHA,'all_declared_pads_are_ordinary_SMD':True,'native_effective_flashes_and_shape_attestation_required':True,'integer_grid_nm':1,'footprints':rows};out.write_text(json.dumps(result,indent=2)+'\n');print('NATIVE_PAD_LEDGER',sum(len(x['pads']) for x in rows),hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=='__main__':main()
