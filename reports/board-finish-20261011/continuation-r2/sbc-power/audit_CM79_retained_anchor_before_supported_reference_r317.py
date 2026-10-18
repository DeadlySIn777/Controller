"""No deleted-object exclusion for retained original F anchor copper reference."""
import hashlib,json,pickle,sys,time
from pathlib import Path
from shapely.ops import unary_union
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-R315-retained-original-F-anchor-before-supported-reference-r317'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(sh):z=set_precision(sh,0);assert z.wkb==sh.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();base=H/'sbc-power/CM79-exact-R289-existing-return-fullwidth-sparse-diagnostic-r315';assert sha(base/'model.pkl')=='df44ef8d66cc4bea0b2dd1bf1e8ab9d9c54e4c88e41c92fefd0301f5555391bf';g,h,b,q,c=pickle.loads((base/'model.pkl').read_bytes());audit=H/'sbc-power/CM79-R315-fresh-sparse-current-source-native-reference-audit-r316';ar=json.loads((audit/'receipt.json').read_text());assert ar['model_sha256']==sha(base/'model.pkl');old=pickle.loads((audit/'actual-drilled-before-groups.pkl').read_bytes());new=pickle.loads((audit/'actual-drilled-after-groups.pkl').read_bytes());aa=K.root(old['/LOGIC_GND'],'J11001','2');bb=K.root(new['/LOGIC_GND'],'J11001','2');before=zero(K.source_refs(aa)['F.Cu']);after=zero(K.source_refs(bb)['F.Cu']);d=pickle.loads((base/'only-CM79-six-tracks-two-power-vias-one-exact-old-delete.pkl').read_bytes());rows=[]
 for t in d['tracks']:
  if t['net']=='/LOGIC_GND'or t['layer']!='F.Cu':continue
  actual=zero(unary_union([rr['shape']for xs in new[L.norm(t['net'])]for rr in xs if rr['kind']=='track'and rr['uuid']==t['uuid']and rr['layer']=='F.Cu']));old_supported=actual.intersection(before);new_supported=actual.intersection(after);lost=old_supported.difference(new_supported);fn=O/(t['uuid']+'-retained-original-anchor-before-supported-loss.wkb');fn.write_bytes(lost.wkb);rows.append({'new_exact_original_F_anchor_UUID':t['uuid'],'actual_new_drill_subtracted_retained_anchor_Cu_mm2':actual.area,'actual_BEFORE_supported_remaining_Cu_mm2':old_supported.area,'same_remaining_Cu_supported_AFTER_mm2':new_supported.area,'literal_before_supported_remaining_anchor_reference_loss_EMPTY':lost.is_empty,'literal_loss_type':lost.geom_type,'literal_loss_area_mm2':lost.area,'literal_loss_WKB_sha256':sha(fn),'deleted_whole_native_dc1a_object_exclusion_not_applied_to_remaining_anchor_Cu':True,'no_generic_own_aperture_radius_or_D4_power_exemption':True})
 put(O/'retained-original-F-anchor-strict-before-supported-reference.json',rows);put(O/'receipt.json',{'verdict':'RETAINED_ORIGINAL_F_ANCHOR_BEFORE_SUPPORTED_REFERENCE_FAIL'if any(not x['literal_before_supported_remaining_anchor_reference_loss_EMPTY']for x in rows)else'RETAINED_ORIGINAL_F_ANCHOR_BEFORE_SUPPORTED_REFERENCE_EMPTY_LOSS_LOCAL_DIAGNOSTIC','R315_model_sha256':sha(base/'model.pkl'),'R316_receipt_sha256':sha(audit/'receipt.json'),'retained_original_anchor_count':len(rows),'strict_before_supported_remaining_anchor_reference_FAIL_count':sum(not x['literal_before_supported_remaining_anchor_reference_loss_EMPTY']for x in rows),'actual_ordinary_return_pairs_current_loop_and_source_own_aperture_qualification':'OPEN_NO_WAIVER','all_inherited_CORE_FIELD_IO3_q93_rawbody_CMcurrent_native_fault_failure_flags_retained':True,'source_model_rules_native_adoption_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R317_COMPLETE',sha(O/'receipt.json'),json.dumps(rows),flush=True)
if __name__=='__main__':main()
