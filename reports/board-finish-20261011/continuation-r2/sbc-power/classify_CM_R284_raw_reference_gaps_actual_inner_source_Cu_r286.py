"""Read-only raw-gap classification against real rooted inner Cu, no shadow.

The original fill-only fullbody reference failures remain failures. This
separate ledger uses only actual drilled pads/barrels/tracks present in the
bound source graph, and reports every residual nonempty geometry strictly.
"""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM-R284-raw-fill-reference-gap-real-inner-source-Cu-classification-r286'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def zero(s):a=set_precision(s,0);assert a.wkb==s.wkb;return a
def main():
 assert not O.exists();O.mkdir();P=H/'sbc-power/CM-R283-current-independent-all-contact-source-native-rule-r284';assert sha(P/'receipt.json')=='877050f6d37de31e39381d08a08c39f8acf789da412853b3ae65aa607af7fa62';gp=P/'actual-drilled-current-groups.pkl';assert sha(gp)=='4ab9643d092b7e4b50e46f9fd2fef362389277d97bc41d0059353338c847f555';groups=pickle.loads(gp.read_bytes());root=K.root(groups['/LOGIC_GND'],'J11001','2');inner=[rr for rr in root if rr['layer']=='In1.Cu'and rr['kind']!='fill'];support=zero(unary_union([rr['shape']for rr in inner]));sf=O/'actual-drilled-real-source-root-In1-nonfill-Cu-only.wkb';sf.write_bytes(support.wkb);put(O/'literal-real-source-inner-support-record-keys.json',[{k:v for k,v in rr.items()if k not in('shape','source','key')}for rr in inner]);rows=[]
 for row in json.loads((P/'all-new-full-actual-drilled-body-source-reference-gaps.json').read_text()):
  gf=P/(row['UUID']+'-actual-drill-subtracted-full-Cu-source-fill-reference-gap.wkb');assert sha(gf)==row['gap_sha256'];gap=zero(from_wkb(gf.read_bytes()));residual=gap.difference(support);qualified=gap.intersection(support);uf=O/(row['UUID']+'-strict-uncovered-after-real-source-inner-Cu.wkb');uf.write_bytes(residual.wkb);qf=O/(row['UUID']+'-exact-gap-covered-by-real-source-inner-Cu.wkb');qf.write_bytes(qualified.wkb);rows.append({**row,'original_fill_only_fullbody_reference_FAIL_retained':not row['gap_empty'],'exact_gap_covered_by_existing_real_source_inner_nonfill_Cu_mm2':qualified.area,'exact_real_source_Cu_coverage_sha256':sha(qf),'strict_residual_after_real_inner_source_Cu_mm2':residual.area,'strict_residual_empty':residual.is_empty,'residual_WKB_sha256':sha(uf),'no_buffer_generic_disk_net_or_mask_expansion':True})
 put(O/'strict-real-source-inner-Cu-reference-gap-classification.json',rows);put(O/'receipt.json',{'verdict':'READ_ONLY_REAL_INNER_SOURCE_CU_GAP_CLASSIFICATION_ALL_RAW_FAILED_REFERENCE_GATES_PRESERVED','exact_R284_receipt_sha256':sha(P/'receipt.json'),'actual_source_graph_sha256':sha(gp),'real_source_inner_nonfill_Cu_WKB_sha256':sha(sf),'new_body_rows':len(rows),'original_raw_fill_only_fullbody_reference_FAIL_count':sum(not x['gap_empty']for x in rows),'raw_gaps_exactly_covered_by_real_source_inner_Cu_count':sum(not x['gap_empty']and x['strict_residual_empty']for x in rows),'strict_residual_body_count':sum(not x['strict_residual_empty']for x in rows),'strict_residual_total_mm2':sum(x['strict_residual_after_real_inner_source_Cu_mm2']for x in rows),'strict_residual_max_mm2':max(x['strict_residual_after_real_inner_source_Cu_mm2']for x in rows),'support_only_actual_drilled_rooted_source_graph_records_not_generated_geometry':True,'new_via_flashes_host_prospective_native_PENDING':True,'no_original_reference_predicate_or_failed_gate_change':True,'no_magnitude_threshold_or_equalshare_current_credit':True,'physical_source_all51_fullcurrent_fault_native_qualification':'FAIL_OR_OPEN_RETAINED','board_written':False,'native_jobs':0,'adopted':False,'script_sha256':sha(__file__)});print('R286_COMPLETE',sha(O/'receipt.json'),sum(not x['strict_residual_empty']for x in rows),flush=True)
if __name__=='__main__':main()
