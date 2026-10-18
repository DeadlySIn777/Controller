"""Replay protected24 cuts onto a newer, frozen, owned power model.

Never substitute the older R19 return shapes for the later CORE/B5 composition.
Only new same-domain field-return proposals may be cut; source/native originals
remain intact. Independent mutual and retained-contact gates follow composition.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[key]='2'
import hashlib, json, pickle, sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import zone_projection_r1 as N

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')

def main():
    assert len(sys.argv)==3,'frozen_newer_model.pkl fresh_output_directory'
    mp=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    assert out.is_relative_to(H) and not out.exists()
    rp=H/'protected24-dogbones-r7';rr=json.loads((rp/'receipt.json').read_bytes())
    r19=H/'field-power/repaired-local-return-audit-r19'
    assert sha(r19/'geometry.pkl')=='38882eeb997cfe1836314af74532bc497704548af8c8e9b1851607c2a92fff1c'
    for key,name in [('proposed_discrete_sha256','proposed-discrete.pkl'),('proposed_zones_sha256','proposed-zones.pkl'),('owned_return_zone_updates_sha256','owned-new-return-zone-updates.pkl')]:assert sha(rp/name)==rr[key]
    old,h,binding,zones,prior=pickle.loads(mp.read_bytes())
    new=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes())
    native=pickle.loads((H/'field-power/native-bound-field-base-r5/model.pkl').read_bytes())['discrete']
    original_zone_ids={q['uuid'] for q in native['zones']}
    assert not original_zone_ids & {q['uuid'] for q in zones+adds}
    known={q['uuid']:q for q in pickle.loads((r19/'proposed-zones.pkl').read_bytes())}
    byid={q['uuid']:q for q in zones}
    assert {q['owned_new_return_uuid'] for q in rr['owned_return_carve_ledger']}<=byid.keys()
    for row in rr['owned_return_carve_ledger']:
        assert row['owned_new_return_uuid'] in known and sha(row['removed_file'])==row['removed_file_sha256'] and sha(row['quantization_added_file'])==row['quantization_added_file_sha256']
    ids={q['uuid'] for kind in ('pads','tracks','vias') for q in h[kind]}
    assert not ids & {q['uuid'] for kind in ('vias','tracks') for q in new[kind]}
    assert len({q['uuid'] for q in zones+adds})==len(zones+adds)
    out.mkdir();replay=[];result=[]
    # The frozen recipe's every via/outer stub and inner bridge determines its
    # local antipad. Actual physical drill-subtracted shapes are kept separate.
    for q in zones:
        return_net=C.norm(q['net'])
        if return_net not in ('/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V') or q['layer'] not in ('In1.Cu','In2.Cu','In4.Cu'):
            result.append(q);continue
        positive='/motherboard_power_entry/FIELD_A_24V_PROTECTED' if return_net=='/motherboard_motors/FIELD_GND' else '/motherboard_power_entry/FIELD_B_24V_PROTECTED'
        bodies=[Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32) for v in new['vias'] if C.norm(v['net'])==positive]
        bodies += [C.body(t) for t in new['tracks'] if C.norm(t['net'])==positive and t['layer']==q['layer']]
        bodies += [z['shape'] for z in adds if C.norm(z['net'])==positive and z['layer']==q['layer']]
        if not bodies:result.append(q);continue
        cutter=unary_union(bodies).buffer(.175)
        before=q['shape'];after=set_precision(before.difference(cutter),1e-6)
        prior_outline=q.get('zone_outline_shape',before)
        final_outline=set_precision(prior_outline.difference(cutter),1e-6)
        removed=before.difference(after);gained=after.difference(before)
        if removed.area<=1e-9 and gained.area<=1e-9 and final_outline.equals(prior_outline):result.append(q);continue
        record={'uuid':q['uuid'],'raw_return_net':q['net'],'layer':q['layer'],'baseline_newer_shape_sha256':hashlib.sha256(before.wkb).hexdigest(),'new_shape_sha256':hashlib.sha256(after.wkb).hexdigest(),'removed_area_mm2':removed.area,'quantization_gained_area_mm2':gained.area,'native_outline_before_sha256':hashlib.sha256(prior_outline.wkb).hexdigest(),'native_outline_after_sha256':hashlib.sha256(final_outline.wkb).hexdigest(),'exact_grid_mm':1e-6,'local_clearance_buffer_mm':.175}
        for label,shape in [('cutter',cutter),('removed',removed),('quantization-gained',gained),('physical-before',before),('physical-after',after),('native-outline-before',prior_outline),('native-outline-after',final_outline)]:
            path=out/(q['uuid']+'.'+label+'.wkb');path.write_bytes(shape.wkb);record[label+'_file']=str(path);record[label+'_sha256']=sha(path)
        replay.append(record);result.append({**q,'shape':after,'zone_outline_shape':final_outline})
    # GEOS precision metadata is not preserved by WKB pickling. Restore the nine
    # explicitly grid-bound r15 shapes before the original-fill projection.
    precision_ids={q['uuid'] for q in result if q.get('label')=='CORE-main-In2' or q.get('label','').startswith('IO3-r15-field-crossing-') or q.get('field_return_proposal') and q['layer']=='In2.Cu'}
    assert len(precision_ids)==9
    result=[{**q,'shape':set_precision(q['shape'],1e-6)} if q['uuid'] in precision_ids else q for q in result]+adds
    h={**h,'tracks':h['tracks']+new['tracks'],'vias':h['vias']+new['vias']}
    print('PROJECTING_JOINT',len(result),'NEW_ZONE_SHAPES',len(new['vias']),'PROTECTED_VIAS',flush=True)
    candidate,cuts=N.projected(old,h,result)
    model=out/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,result,candidate),protocol=5))
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),mp,rp/'receipt.json',rp/'proposed-discrete.pkl',rp/'proposed-zones.pkl',rp/'owned-new-return-zone-updates.pkl',r19/'receipt.json',r19/'proposed-zones.pkl',H/'field-power/native-bound-field-base-r5/model.pkl',Path(N.__file__),Path(C.__file__))}
    write(out/'receipt.json',{'verdict':'JOINT_PROTECTED_ON_NEWER_CORE_B5_FROZEN_MUTUAL_CONTACT_CURRENT_NATIVE_PENDING','model_sha256':sha(model),'input_sha256':pins,'new_protected_vias':len(new['vias']),'new_protected_stubs':len(new['tracks']),'new_protected_bridge_shapes':len(adds),'all_owned_shapes':len(result),'later_ground_shapes_cut_without_overwriting_CORE_carves':replay,'original_zone_shapes_replaced_or_removed':[],'source_poses_and_existing_discrete_unchanged':True,'restored_precision_ids':sorted(precision_ids),'original_native_fill_projection_ledger':cuts,'full_mutual_no_loss_original198b_dc936_source_root_current_and_native_gates':'OPEN','board_written':False,'native_jobs':0,'adopted':False})
    print('JOINT_MODEL',sha(model),flush=True)

if __name__=='__main__':main()
