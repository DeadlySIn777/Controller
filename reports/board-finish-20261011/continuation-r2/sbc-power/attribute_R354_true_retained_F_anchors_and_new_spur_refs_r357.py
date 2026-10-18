"""Correct scope attribution; preserve the raw broader helper FAIL ledger."""
import json,pickle,sys,hashlib
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import LineString
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import guarded_power_projection_r44 as Z
import audit_aux_exact_raw as A
D=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354'
B=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r353'
O=H/'sbc-power/CM79-R354-exact-retained-anchor-vs-new-spur-reference-scope-attribution-r357'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='5c8660beeaab679f950140fca697854d01ec9379c0ddf40da210c599021093d8';d=pickle.loads((B/'only-CM79-fullwidth-tracks-one-larger-power-via-one-exact-old-delete.pkl').read_bytes());oldchunk=B/'dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1.exact-original-source-delete-chunk';assert sha(oldchunk)=='191f77c745a09f3083e5f0afac04439c853245e4362681b1bf3a1cd5af81e14e';old=A.G.parse('dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1',oldchunk.read_bytes(),{});assert old['w']==1.25 and old['layer']=='F.Cu';oldbody=Z.bounded_buffer(LineString([old['a'],old['b']]),old['w']/2);oldbody=set_precision(oldbody,0);tmap={t['uuid']:t for t in d['tracks']};rows=json.loads((D/'retained-original-fullwidth-F-before-supported-anchor-proof.json').read_text());anchors=[];new=[];errors=[]
 for row in rows:
  t=tmap[row['UUID']];expected= t['a']==old['a']and t['b']==[116.2,202.35]or t['a']==[120.1,202.35]and t['b']==old['b'];fn=D/(t['uuid']+'-retained-fullwidth-F-before-supported-anchor-loss.wkb');assert sha(fn)==row['loss_WKB_sha256'];loss=from_wkb(fn.read_bytes());lostOld=loss.intersection(oldbody);record={**row,'exact_new_track':t,'actual_pre_or_post_original_anchor':expected,'loss_intersects_any_original_fullwidth_body':not lostOld.is_empty,'loss_intersection_original_body_type':lostOld.geom_type,'loss_intersection_original_body_area_mm2':lostOld.area,'raw_R354_helper_row_preserved':True}
  (anchors if expected else new).append(record)
  if not lostOld.is_empty:errors.append(record)
 assert len(anchors)==2
 put(O/'exact-true-retained-anchor-proof.json',anchors);put(O/'new-external-F-spur-before-location-support-diagnostics.json',new);put(O/'any-original-F-body-reference-losses.json',errors);put(O/'receipt.json',{'verdict':'EXACT_TRUE_RETAINED_FULLWIDTH_ANCHOR_SCOPE_ATTRIBUTION_RAW_NEW_SPUR_REFERENCE_FAILS_RETAINED','R354_receipt_sha256':sha(D/'receipt.json'),'R353_receipt_sha256':sha(B/'receipt.json'),'exact_original_fullwidth_F_chunk_sha256':sha(oldchunk),'two_exact_retained_original_F_anchor_loss_count':sum(not r['literal_before_supported_loss_EMPTY']for r in anchors),'all_new_F_spur_loss_intersection_any_original_F_body_count':len(errors),'raw_R354_broader_helper_loss_count_retained':sum(not r['literal_before_supported_loss_EMPTY']for r in rows),'new_spur_raw_reference_fullbody_current_thermal_native':'FAIL_OR_OPEN_RETAINED','IO3_1484_keys_split_repair_required':True,'source_model_board_native_changes':0});print('R357',sha(O/'receipt.json'),'two-real-anchor-losses',sum(not r['literal_before_supported_loss_EMPTY']for r in anchors),'original-any-body',len(errors),flush=True)
if __name__=='__main__':main()
