"""Explicit proposed LG return reservations, without modifying the B3 plane."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import LineString
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/C1021-C1023-source-ground-return-reservations-r224'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();nom=H/'sbc-power/remaining-original-IO3-monotone-direct-source-nominees-r220';assert sha(nom/'receipt.json')=='058c220326717e0643436e9b51f41a884c337bb1578e7c270e85a02a8582647a';diag=H/'sbc-power/five-IO3-feed-actual-return-gap-diagnosis-r223';assert sha(diag/'receipt.json')=='0a720e8c335c8838605874429c80ecf6f92eab9ef671750c9cbea082128bd910';n=json.loads((nom/'receipt.json').read_text());d=json.loads((diag/'receipt.json').read_text());tracks=pickle.loads((nom/'proposed-tracks.pkl').read_bytes());rows=[];objects=[]
 for ref in ('C1021','C1023'):
  row=next(r for r in n['accepted_source_nominations'] if r['ref']==ref);assert row['layer']=='B.Cu' and row['width_mm']==.2;owned=next(r for r in d['rows'] if r['nominee']['ref']==ref);assert owned['foreign_owned_physical_plane_attribution'][0]['owned_foreign_UUID']=='f4863c44-a057-598a-aef7-adca7cfb15f1'
  actual=[t for t in tracks if t['uuid'] in row['new_track_UUIDs']];axis=LineString(row['points_mm']);body=GP.bounded_buffer(axis,.1);return_support=GP.bounded_buffer(axis,.25);power_avoid=GP.bounded_buffer(return_support,.625+.000100)
  roles={'exact_power_track_full_reference_body':body,'proposed_0p50mm_LG_return_support_only':return_support,'proposed_foreign_B3_avoidance_mask_only':power_avoid};proof={}
  for role,sh in roles.items():
   f=O/(ref+'.'+role+'.wkb');f.write_bytes(sh.wkb);proof[role]={'file':str(f.resolve()),'sha256':sha(f),'bounds_mm':sh.bounds,'area_mm2':sh.area}
  rows.append({'ref':ref,'power_track_rows':actual,'reference_layer':'In4.Cu','raw_return_net':'/LOGIC_GND','role_files':proof,'desired_return_core_width_mm':.5,'return_current_or_width_not_yet_qualified':True,'foreign_required_domain_clearance_plus_planning_mm':.625,'additional_construction_reserve_nm':100,'owned_foreign_B3_UUID':'f4863c44-a057-598a-aef7-adca7cfb15f1','owned_foreign_physical_WKB_sha256':'57aa36978af3dc9ab53e6392c8f971fa9b65756082511fc22ebeac14bf04d1bc','actual_local_ground_source_pins':owned['actual_local_ground_pin_rows'],'no_old_or_new_plane_carve_authorized_by_mask_export':True})
  objects.append({'ref':ref,'tracks':actual,'reference_body':body,'proposed_return_support':return_support,'proposed_B3_avoidance':power_avoid})
 pf=O/'exact-return-reservation-objects.pkl';pf.write_bytes(pickle.dumps(objects,protocol=5));put(O/'receipt.json',{'verdict':'EXACT_TWO_UNACCEPTED_IO3_REFERENCE_AND_PROPOSED_RETURN_RESERVATIONS_FOR_DERIVED_B3_REBUILD','R220_receipt_sha256':sha(nom/'receipt.json'),'R223_diagnosis_sha256':sha(diag/'receipt.json'),'rows':rows,'object_file':str(pf.resolve()),'object_sha256':sha(pf),'actual_positive_integration_base':'R214 + sole accepted C1022 R222 additive track','no_B3_or_IO3_plane_source_copper_rule_or_current_mutation':True,'full_IO3_A_retained':2.0,'actual_source_connected_return_route_full_current_and_mutual_native_GATES':'OPEN','native_jobs':0,'board_written':False,'script_sha256':sha(__file__)});print('R224_COMPLETE',sha(O/'receipt.json'),sha(pf),flush=True)
if __name__=='__main__':main()
