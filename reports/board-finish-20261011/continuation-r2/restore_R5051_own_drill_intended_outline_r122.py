"""Reapply saved SBC135's exact own-drill native-outline correction to R5051.

The physical generated copper, original native definitions, drills and all
source/reference failures remain exact. Fresh native flash/source is mandatory.
"""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,Polygon,MultiPolygon
H=Path(__file__).resolve().parent
OUT=H/'R112-R5051-own-drill-intended-outline-only-correction-r122'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e'
    model=pickle.loads(mp.read_bytes());g,h,b,z,current=model
    q=next(q for q in z if q['uuid']=='47888e35-9a96-5393-b579-7c0b4a64ec93');v=next(v for v in h['vias'] if v['uuid']=='18701851-0390-4dc4-b03d-f8e1cd66c395')
    assert q['net']==v['net']=='/LOGIC_GND' and q['layer']=='In3.Cu' and [v['x'],v['y'],v['d'],v['drill']]==[292.,209.375,.6,.3]
    outline=q['zone_outline_shape'];parts=list(outline.geoms) if outline.geom_type=='MultiPolygon' else [outline];pt=Point(v['x'],v['y']);hits=[(i,j,Polygon(r)) for i,p in enumerate(parts) for j,r in enumerate(p.interiors) if Polygon(r).covers(pt)];assert len(hits)==1
    i,j,void=hits[0];assert void.bounds==(291.85,209.225,292.15,209.525)
    assert all(abs(Point(x,y).distance(pt)-.15)<.000002 for x,y in list(void.exterior.coords)), 'Hole must be exactly the existing own .3mm plated drill void'
    afterparts=parts.copy();afterparts[i]=Polygon(parts[i].exterior,[r for k,r in enumerate(parts[i].interiors) if k!=j]);new=MultiPolygon(afterparts) if outline.geom_type=='MultiPolygon' else afterparts[0]
    assert new.is_valid and new.covers(pt)
    new=set_precision(new,1e-6,mode='pointwise');old_generated=set_precision(outline,1e-6,mode='pointwise');assert old_generated.wkb==outline.wkb
    assert new.difference(old_generated).equals(void) and old_generated.difference(new).is_empty
    update=copy.deepcopy(q);update['zone_outline_shape']=new;assert update['shape'].wkb==q['shape'].wkb
    for key in q:
        if key!='zone_outline_shape':assert update[key].wkb==q[key].wkb if hasattr(q[key],'wkb') else update[key]==q[key]
    (OUT/'one-owned-zone-update.pkl').write_bytes(pickle.dumps([update],protocol=5))
    files={}
    for role,shape in [('intended-before',outline),('intended-after',new),('exact-own-drill-void',void),('physical-unchanged',q['shape'])]:
        p=OUT/(role+'.wkb');p.write_bytes(shape.wkb);files[role]={'file':str(p.resolve()),'sha256':sha(p)}
    original=H/'SAFE-exploratory-native-trial-r9/measure/actual-full-refill-contract.json'
    failed=json.loads(original.read_bytes());assert failed['candidate_sha256']=='3b579aa7ea4cf4c070c22e36df8dca2fbfcdefccd0e3c2a874ebf337acda3919' and failed['verdict']=='FAIL_ACTUAL_FULL_NATIVE_FILL_CU_OR_FLASH_CONTRACT'
    record={'verdict':'EXACT_R5051_OWN_DRILL_INTENDED_OUTLINE_ONLY_CORRECTION_NATIVE_MANDATORY','parent_model_sha256':sha(mp),'saved_SBC135_method_sha256':sha(H/'sbc-power/restore_source_1V2_intended_drill_void_r135.py'),'proposal_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'old_same_serialized_via_UUID':v['uuid'],'same_serialized_via_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'original_actual_native_flashes':['F.Cu','In1.Cu','In4.Cu','B.Cu'],'required_extra_actual_native_flash':'In3.Cu','only_own_hole_component_index':i,'only_own_hole_ring_index':j,'intended_added_only_exact_own_drill_void_mm2':void.area,'physical_Cu_byte_WKB_unchanged':True,'all_other_role_settings_discrete_native_definitions_unchanged':True,'owned_update_sha256':sha(OUT/'one-owned-zone-update.pkl'),'original_actual_full_native_flash_FAILURE_retained_sha256':sha(original),'native_fill_must_subtract_actual_own_drill':True,'fresh_native_flash_source_annular_all_original_groups_full_DRC_current_reference_gates':'MANDATORY_OPEN','files':files,'native_jobs':0,'board_written':False,'adopted':False}
    write(OUT/'receipt.json',record);print('R122_OUTLINE_ONLY',void.area,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
