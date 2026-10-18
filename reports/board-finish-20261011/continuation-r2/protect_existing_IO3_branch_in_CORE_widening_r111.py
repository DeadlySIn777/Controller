"""Widen only away from the proven old IO3 via/branch; preserve original route."""
import os
for key in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import hashlib,json,pickle,sys,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for folder in('field-power','sbc-power'):sys.path.insert(0,str(H/folder))
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 narrow=H/'CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';wide=H/'CORE-wider-new-only-legal-envelope-proposal-r106';assert sha(narrow/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd'and sha(wide/'receipt.json')=='74bb46a6fd31e60c8461f7f8c2ecf58cfc32a259abf3616466888f24400f4b39';a=pickle.loads((narrow/'proposed-route-and-zone.pkl').read_bytes())[0];r=pickle.loads((wide/'proposed-route-and-zone.pkl').read_bytes())[0];q=copy.deepcopy(r['zone']);old=a['zone'];assert q['uuid']==old['uuid']=='b0453302-df03-561f-9bc4-0560bc66658a';ledger=[]
 for obj in(old,q):
  for role in('shape','zone_outline_shape'):
   b=obj[role].wkb;obj[role]=set_precision(obj[role],1e-6,mode='pointwise');assert obj[role].wkb==b
 via={'x':190.625,'y':88.05};cut=N.bounded_disk(via,2.);removed=[]
 for role in('shape','zone_outline_shape'):
  before=q[role];new_only=before.difference(old[role]);added=set_precision(new_only.difference(cut),1e-6);after=set_precision(unary_union([old[role],added]),1e-6);assert old[role].difference(after).is_empty and after.difference(before).is_empty;q[role]=after;removed.append({'role':role,'wide_before_WKB_sha256':digest(before),'after_WKB_sha256':digest(after),'only_NEW_widening_removed_mm2':before.difference(after).area,'added_vs_wide_mm2':0.,'original1mm_core_and_all_endpoints_retained':True})
 q['label']='CORE widened envelope with existing U4013 IO3 branch reservation R111';r.update(zone=q,only_new_widening_IO3_original_via57bd_local_reservation_radius_mm=2.,original_core_min_width_mm=1.);out=H/'CORE-wide-local-IO3-branch-reservation-proposal-r111';assert not out.exists();out.mkdir();(out/'proposed-route-and-zone.pkl').write_bytes(pickle.dumps([r],protocol=5));(out/'proposed-discrete.pkl').write_bytes((narrow/'proposed-discrete.pkl').read_bytes());(out/'local-original-IO3-branch-reservation.wkb').write_bytes(cut.wkb);receipt=json.loads((wide/'receipt.json').read_bytes());receipt.update({'verdict':'ONLY_NEW_CORE_WIDENING_LOCALLY_WITHHELD_FOR_ACTUAL_OLD_IO3_BRANCH_FULL_GATES_OPEN','new_physical_WKB_sha256':digest(q['shape']),'new_actual_physical_mm2':q['shape'].area,'known_IO3_old_via_UUID':'57bddec8-de07-4f55-88de-5be6f97412fe','actual_original_IO3_via_position_mm':[190.625,88.05],'only_new_widening_local_reservation_radius_mm':2.,'local_new_role_operations':removed,'all77_source_full_reference_true_geometry_native_guard_actual_mesh':'OPEN','rejected_R107_three_IO3_pads_and7keys_loss_not_waived':True});receipt['routes'][0]['physical_WKB_sha256']=digest(q['shape']);(out/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R111_CORE_LOCAL_IO3_RESERVATION',q['shape'].area,sha(out/'receipt.json'),digest(q['shape']),flush=True)
if __name__=='__main__':main()
