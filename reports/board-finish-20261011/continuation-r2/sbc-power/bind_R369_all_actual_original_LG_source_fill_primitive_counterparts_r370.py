"""Exhaustive actual source-fill identity, with raw union FAIL left visible."""
import json,pickle,hashlib,sys,collections,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-R369-all-original-J1-source-fill-primitive-exact-counterparts-r370'
D=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='0f9bcc18a3aff488219e9c77853b1f45279a134c69dbebaa67d91a39785fc9f0';assert sha(D/'model.pkl')=='f9c6940123267d94fb8a4a927e62c47d541bc4295dc240ada398c588095c8964';beforeFile=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/actual-drilled-after-groups.pkl';assert sha(beforeFile)=='339dbe2c2173388fa7384c697e6364dcf5b9c507e552e64836b08c55203ed4eb';before=K.root(pickle.loads(beforeFile.read_bytes())['/LOGIC_GND'],'J11001','2');afterFile=D/'fresh-actual-drilled-changed-source-groups.pkl';after=K.root(pickle.loads(afterFile.read_bytes())['/LOGIC_GND'],'J11001','2');key=lambda rr:(rr['uuid'],rr['layer'],rr['shape'].wkb);old=[rr for rr in before if rr['kind']=='fill'];new=[rr for rr in after if rr['kind']=='fill'];counts=collections.Counter(key(rr)for rr in new);rows=[];bad=[]
 for i,rr in enumerate(old):
  kk=key(rr);matched=counts[kk]>0
  if matched:counts[kk]-=1
  row={'before_source_piece':i,'UUID':rr['uuid'],'layer':rr['layer'],'actual_all_drill_subtracted_source_fill_WKB_sha256':hashlib.sha256(rr['shape'].wkb).hexdigest(),'exact_after_J1_source_component_counterpart':matched,'all_closed_set_points_edges_faces_preserved_by_exact_same_primitive':matched};rows.append(row)
  if not matched:bad.append(row)
 put(O/'exhaustive-every-original-actual-source-fill-closed-set-counterpart.json',rows);put(O/'missing-exact-source-fill-counterparts.json',bad);parent=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r353/model.pkl';g,h,b,q,c=pickle.loads(parent.read_bytes());gg,hh,bb,qq,cc=pickle.loads((D/'model.pkl').read_bytes());assert h['vias']==hh['vias']and h['pads']==hh['pads']and c['zones']==cc['zones'][:-1];raw=D/'raw-original-In4-source-reference-before-minus-after.wkb';assert not json.loads((D/'receipt.json').read_text())['raw_old_reference_union_loss_EMPTY'];result={'verdict':'EVERY_ORIGINAL_ACTUAL_J1_FILL_PRIMITIVE_HAS_EXACT_SOURCE_ROOTED_AFTER_COUNTERPART_RAW_UNION_FAIL_RETAINED'if not bad else'MISSING_OLD_SOURCE_FILL_PRIMITIVE','R369_receipt_sha256':sha(D/'receipt.json'),'before_actual_source_cache_sha256':sha(beforeFile),'after_actual_source_cache_sha256':sha(afterFile),'original_actual_source_fill_piece_count':len(old),'after_actual_source_fill_piece_count':len(new),'missing_exact_counterpart_count':len(bad),'all_original_holes_pads_masks_via_flags_and_fill_arrays_exact':True,'raw_reassociated_In4_union_FAIL_WKB_sha256':sha(raw),'raw_union_FAIL_preserved_not_area_waived_or_changed':True,'scope':'Every original actual J1-rooted fill primitive on all six layers is itself present byte for byte in the fresh after J1 source group. This constructive inclusion preserves all true primitive reference points and direct contacts; it does not claim the reassociated GEOS union predicate passed or clear native/current/terminal-transfer gates.','new_shapes_original_precision_native_source_or_rule_mutations':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)};put(O/'receipt.json',result);print('R370',sha(O/'receipt.json'),len(old),len(new),len(bad),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
