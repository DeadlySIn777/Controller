"""Carry all untouched R160 canonical primitives exactly; replace only IO3 In2/3.

R177 remains frozen evidence. Its repeated canonical/guard operations on
unaffected layers are not necessary to append the eight inner IO3 joins.
No thresholds, original-fill definitions, source entities or current change.
"""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import restore_SAFE_generated_precision_states_r168 as PS
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 oldp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';newp=H/'sbc-power/original-IO3-full-owned-zone-normalization-r177/model.pkl'
 assert sha(oldp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 assert sha(newp)=='dce1b14de236b36b45e8cb613cd0a0472bcfbc85765e70854fd409de38392896'
 g,h,ob,oz,oc=pickle.loads(oldp.read_bytes());ng,nh,nb,nz,nc=pickle.loads(newp.read_bytes());assert g==ng and h==nh
 PS.restore_bound_generated_precision_states(ob,oz);PS.restore_bound_generated_precision_states(nb,nz)
 def key(q):return (q['net'],q['layer'],q.get('clearance_mm',.15),q.get('min_thickness_mm',.15),q.get('pad_connect_mode','FULL_SOLID'),q.get('priority',124),q.get('island_removal_mode',1),q.get('thermal_gap_mm',.15),q.get('thermal_bridge_width_mm',.3))
 om={key(q):q for q in oz};nm={key(q):q for q in nz};assert len(om)==len(oz)==len(nm)==len(nz)==36 and set(om)==set(nm)
 selected=[];ledger=[];precision=[]
 for q in nz:
  k=key(q);old=om[k];changed=k[0]=='/IO_3V3' and k[1] in ('In2.Cu','In3.Cu')
  chosen=copy.deepcopy(q if changed else old);selected.append(chosen)
  row={'raw_net':k[0],'layer':k[1],'declared_settings':list(k[2:]),'old_UUID':old['uuid'],'selected_UUID':chosen['uuid'],'R177_UUID':q['uuid'],'operation':'REPLACE_ONLY_IO3_IN2_IN3_CANONICAL_UNION' if changed else 'EXACT_UNCHANGED_R160_PRIMITIVE_CARRY','roles':{}}
  for role in ('shape','zone_outline_shape'):
   sh=chosen[role];before=sh.wkb;tag=set_precision(sh,1e-6,mode='pointwise');assert tag.wkb==before;chosen[role]=tag
   precision.append({'new_generated_UUID':chosen['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest(sh)})
   row['roles'][role]={'old_R160_SHA256':digest(old[role]),'historical_R177_SHA256':digest(q[role]),'selected_SHA256':digest(sh),'old_removed_mm2':old[role].difference(sh).area,'old_added_mm2':sh.difference(old[role]).area}
   if not changed:assert sh.wkb==old[role].wkb
  ledger.append(row)
 assert sum(r['operation'].startswith('REPLACE') for r in ledger)==2
 lf=O/'exact-unchanged-primitive-and-two-IO3-replacement-ledger.json';lf.write_text(json.dumps(ledger,indent=1)+'\n')
 b=copy.deepcopy(nb);b.update({'generated_precision_state_ledger':precision,'restored_generated_grid_UUIDs':[q['uuid'] for q in selected],'IO3_unchanged_primitive_preservation_ledger_file':str(lf.resolve()),'IO3_unchanged_primitive_preservation_ledger_sha256':sha(lf),'IO3_historical_repeated_guard_failure_receipt_file':str((H/'sbc-power/original-IO3-full-all76-incremental-audit-r180/receipt.json').resolve()),'IO3_historical_repeated_guard_failure_receipt_sha256':sha(H/'sbc-power/original-IO3-full-all76-incremental-audit-r180/receipt.json'),'IO3_exact_primitive_parent_model_sha256':sha(oldp),'IO3_two_changed_canonical_groups_model_sha256':sha(newp),'all_original_contact_and_reference_gates_required_after_correction':True,'host_all_supply_rooted':False})
 candidate,cuts=GP.projected(g,h,selected)
 mp=O/'model.pkl';mp.write_bytes(pickle.dumps((g,h,b,selected,candidate),protocol=5))
 (O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_UNCHANGED_LAYER_PRIMITIVE_CARRY_AND_TWO_IO3_UNIONS_FROZEN_FULL_GATES_REQUIRED','model_sha256':sha(mp),'parent_R160_sha256':sha(oldp),'historical_R177_sha256':sha(newp),'owned_zone_count':len(selected),'changed_canonical_group_count':2,'exact_unchanged_owned_group_count':34,'ledger_sha256':sha(lf),'old_fill_retreats':cuts,'no_original_discrete_source_or_native_definition_changes':True,'no_area_waiver':True,'host_all_supply_rooted':False,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)},indent=1)+'\n')
 print('R183_COMPLETE',sha(mp),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
