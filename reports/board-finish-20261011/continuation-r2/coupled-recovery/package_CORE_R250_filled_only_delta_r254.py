"""Freeze filled-record-only R250 authority, without a board or native stage."""
import sys,json,pickle,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import restore_SAFE_generated_precision_states_r168 as PS
import contact_layout as L
from shapely.ops import unary_union
C=A.C;O=H/'CORE-R250-filled-only-immutable-integration-packet-r254'
def main():
 assert not O.exists();O.mkdir();r112=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';r250=H/'CORE-R112-per-polygon-immutable-owned-construction-r250/model.pkl';audit=H/'CORE-R250-vs-actual-R214-independent-r252/receipt.json'
 a=A.read(r112);b=A.read(r250);ar=A.read(audit);assert C.sha(a)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';assert C.sha(b)=='96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868';assert C.sha(ar)=='db5c57276f9dfc385b8a195daa178d36af296a3be24b226370c936d2442df560';rr=json.loads(ar)
 assert not(rr['all77_actual_drilled_contact_losses']or rr['direct_actual_original_layer_fill_contact_losses']or rr['true_all6_geometry_errors']or rr['nine_prior_source_bank_layer_key_loss_count']or rr['three_bank_strict_ZERO_retained_reference_loss_count']);assert rr['new_CORE_fullbody_actual_J1_reference']['actual_J1_In1_full_reference_gap_mm2']==93.04195929171794
 ga,ha,ba,qa,ca=pickle.loads(a);gb,hb,bb,qb,cb=pickle.loads(b);PS.restore_bound_generated_precision_states(ba,qa);PS.restore_bound_generated_precision_states(bb,qb);assert(ga,ha,ba)==(gb,hb,bb);assert len(qa)==len(qb)
 for x,y in zip(qa,qb):assert x['uuid']==y['uuid']and all(x[k].wkb==y[k].wkb for k in('shape','zone_outline_shape'))and {k:v for k,v in x.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in y.items()if k not in('shape','zone_outline_shape')}
 assert {k:v for k,v in ca.items()if k!='zones'}=={k:v for k,v in cb.items()if k!='zones'};old={z['uuid']:z for z in ca['zones']};new={z['uuid']:z for z in cb['zones']};assert old.keys()==new.keys();rows=[]
 for uid,z in new.items():
  p=old[uid];assert {k:v for k,v in p.items()if k!='fills'}=={k:v for k,v in z.items()if k!='fills'}
  if p['fills']!=z['fills']:
   rows.append({'UUID':uid,'before_fills':p['fills'],'after_fills':z['fills'],'before_fills_pickle_sha256':C.sha(pickle.dumps(p['fills'],protocol=5)),'after_fills_pickle_sha256':C.sha(pickle.dumps(z['fills'],protocol=5))})
 (O/'exact-filled-record-replacements.pkl').write_bytes(pickle.dumps(rows,protocol=5));receipt={'verdict':'EXACT_R250_FILLED_ONLY_HOST_DELTA_FROZEN_INCREMENTAL_PASS_FULL_CORE_DC_FAIL_OPEN','R112_model_file':str(r112),'R112_model_sha256':C.sha(a),'R250_model_file':str(r250),'R250_model_sha256':C.sha(b),'independent_R252_receipt_file':str(audit),'independent_R252_receipt_sha256':C.sha(ar),'exact_filled_replacement_file':str(O/'exact-filled-record-replacements.pkl'),'exact_filled_replacement_sha256':C.sha((O/'exact-filled-record-replacements.pkl').read_bytes()),'filled_zone_rows':len(rows),'all_discrete_native_definition_q_physical_intended_settings_exact_R112':True,'all_original_native_and_new_CORE_fill_records_exact_R112':True,'raw_CORE_wholebody_J1_In1_gap_mm2':93.04195929171794,'full_CORE_DC_current_native_ROOT42_qualification':'FAIL/OPEN preserved; sparse incremental acceptance only','host_retained_relationships_pass':False,'host_all_supply_pad_and_proposed_components_rooted':False,'exploratory_diagnostic_only':True,'native_jobs':0,'board_written':False,'source_or_project_written':False,'adopted':False,'read_files_sha256':A.READS};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'receipt_sha256':C.sha((O/'receipt.json').read_bytes()),'filled_rows':len(rows)}),flush=True)
if __name__=='__main__':main()
