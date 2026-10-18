"""Restore exactly one source barrel's drill void in its NEW native outline.

Physical host copper, all old native outlines and the CORE notch stay exact.
Native fill, FlashLayer and the exact-source review are mandatory afterwards.
"""
from pathlib import Path
import pickle,json,hashlib,copy
from shapely.geometry import Point,Polygon
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/CORE1V2-source-native-outline-correction-r135'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,d):Path(f).write_text(json.dumps(d,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/frozen-regional-source-exit-replay-r129/model.pkl';assert sha(mp)=='8f4db80497693186388d622a45508cdf39eb5e0f51a9ee359061bb7d6428ad93'
 old,h,b,z,c=pickle.loads(mp.read_bytes());b=copy.deepcopy(b)
 uid='2f346139-8f65-5990-b9e5-9d669e6c9438';q=next(x for x in z if x['uuid']==uid);v=next(x for x in h['vias'] if x['uuid']=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92')
 assert q['net']==v['net']=='/CORE_1V2' and q['layer']=='In4.Cu' and v['drill']==.2 and v['d']==.5
 outline=q['zone_outline_shape'];assert outline.geom_type=='Polygon';center=Point(v['x'],v['y']);holes=[Polygon(r) for r in outline.interiors];hits=[i for i,p in enumerate(holes) if p.covers(center)];assert len(hits)==1
 i=hits[0];void=holes[i];new=Polygon(outline.exterior,[r for j,r in enumerate(outline.interiors) if j!=i]);assert new.is_valid and new.covers(center)
 assert new.difference(outline).equals(void) and outline.difference(new).is_empty
 q2={**q,'zone_outline_shape':new,'native_outline_intentionally_preserves_frozen_physical_drill_holes':False,'native_outline_source_drill_void_restored_native_must_subtract_own_PTH_drill':True}
 assert q2['shape'].wkb==q['shape'].wkb
 zz=[q2 if x['uuid']==uid else x for x in z]
 for x,y in zip(z,zz):
  if x['uuid']!=uid:assert x==y
 files={}
 for label,s in [('intended-before',outline),('intended-after',new),('restored-source-drill-void',void),('physical-unchanged',q['shape'])]:
  f=O/(label+'.wkb');f.write_bytes(s.wkb);files[label]={'file':str(f.resolve()),'sha256':sha(f)}
 ledger={'verdict':'EXACT_ONE_OWN_SOURCE_DRILL_VOID_REMOVED_FROM_NEW_NATIVE_OUTLINE_ONLY','parent_model_sha256':sha(mp),'proposal_zone_UUID':uid,'layer':'In4.Cu','raw_net':q['net'],'source_via_UUID':v['uuid'],'source_via_at_mm':[v['x'],v['y']],'source_native_drill_mm':v['drill'],'source_native_outer_diameter_mm':v['d'],'original_actual_native_flashes':['F.Cu','In3.Cu'],'required_new_native_flash':'In4.Cu','restored_hole_index':i,'restored_intended_area_mm2':void.area,'exact_intended_added_equals_only_bound_original_source_hole':True,'physical_Cu_unchanged_byte_WKB':True,'all_other_owned_zones_and_CORE_notch_unchanged':True,'all_existing_native_discrete_and_native_zone_definitions_unchanged':True,'native_fill_must_apply_own_plated_drill_automatically':True,'host_source25_and_CORE8303_scope_inherited_only_by_exact_physical_identity':True,'native_1V2_source_and_flash_gate':'OPEN','board_written':False,'native_jobs':0,'files':files}
 lf=O/'exact-outline-operation-ledger.json';write(lf,ledger);b['CORE1V2_source_native_outline_one_drill_void_correction']={'file':str(lf.resolve()),'sha256':sha(lf),'source_fill_and_extra_In4_flash_mandatory':True}
 mf=O/'model.pkl';mf.write_bytes(pickle.dumps((old,h,b,zz,c),protocol=5));qf=O/'new-feed-zones.pkl';qf.write_bytes(pickle.dumps([q2],protocol=5));zf=O/'proposed-zones.pkl';zf.write_bytes(pickle.dumps(zz,protocol=5))
 write(O/'receipt.json',{'verdict':'EXACT_NATIVE_SOURCE_OUTLINE_CORRECTION_PHYSICAL_HOST_1V2_CORE_SCOPE_UNCHANGED_NATIVE_MANDATORY','model_sha256':sha(mf),'parent_model_sha256':sha(mp),'new_feed_zones_sha256':sha(qf),'proposed_zones_sha256':sha(zf),'outline_operation_ledger_sha256':sha(lf),'all_physical_zone_shapes_and_h_and_current_identical':True,'host_source_scope_receipt_file':str((H/'sbc-power/frozen-regional-source-exit-replay-r129/accepted-source-scope/receipt.json').resolve()),'host_source_scope_receipt_sha256':'03f79f5b1cad213c90af61747ccbbe6b6c35748d05c1cf04153846324e228513','native_source_barrel_annuli_and_extra_In4_gate':'OPEN','full_foreign_contacts_reference_current_and_full_native_final':'OPEN','native_jobs':0,'board_written':False})
 print('SOURCE_1V2_INTENDED_HOLE_CORRECTION',sha(mf),sha(O/'receipt.json'),sha(qf),void.area,flush=True)
if __name__=='__main__':main()
