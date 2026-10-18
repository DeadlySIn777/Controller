"""Supersede R268 with true literal DOB masks and exact ordered replay."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'freeze_T4_R7_sparse_owned_native_recipe_r267.py').read_text()
s=s.replace('T4-R7-sparse-exact-R250-diagnostic-r265/T4-plus-R7','R270-true-literal-DOB-current-filled-alignment-requalification-r271/T4-plus-R7')
s=s.replace('ef809424ddfeb32359740240ee195fb7a9a512d6ce1fd688ebf92cc0e473eadc','4905ba0fcf571b6ee569b984b4af3e96c89ce3201d8e57f4ffbc574d9df482bc').replace('e81143a727821d906558e6edce30088da3d410eb0dda8630f80d8fe85e1f16bf','3d086d6f0935cd1760dc95c383049f04e86a31b2c4fb00d925e1d1c43d0be006')
s=s.replace('assert g==bg',"assert g==bg;import restore_SAFE_generated_precision_states_r168 as PS;PS.restore_bound_generated_precision_states(b,q);PS.restore_bound_generated_precision_states(bb,bq)")
s=s.replace("assert z[r].difference(old[r]).is_empty;", "from shapely import set_precision;aa=set_precision(old[r],0);nn=set_precision(z[r],0);assert aa.wkb==old[r].wkb and nn.wkb==z[r].wkb and nn.difference(aa).is_empty;")
s=s.replace("'exact_negative_mask':old[r].difference(z[r])", "'exact_negative_mask':aa.difference(nn)")
start="scopefiles=[parent/'exact-current-filled-record-new-primitive-ledger.json',parent/'exact-generated-role-new-antipad-ledger.json',*parent.glob('*explicit-local-gain-reserve-ledger.json'),*parent.glob('*bound-local-reserve*')];manifest={str(f.resolve()):sha(f)for f in scopefiles if f.is_file()};"
new="""legacy=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r265/T4-plus-R7';repair=H/'sbc-power/DOB-R265-true-literal-zero-grid-role-local-negative-repair-r270';scopefiles=[parent/'exact-current-filled-record-new-primitive-ledger.json',parent/'only-DOB-filled-literal-role-alignment-ledger.json',*parent.glob('*literal-role-physical-alignment*'),*parent.glob('*negative-cut.wkb'),legacy/'exact-generated-role-new-antipad-ledger.json',*legacy.glob('*explicit-local-gain-reserve-ledger.json'),*legacy.glob('*bound-local-reserve*'),*repair.glob('*.wkb'),repair/'true-literal-rejected-and-successor-role-ledger.json'];manifest={str(f.resolve()):sha(f)for f in scopefiles if f.is_file()};
 from shapely import from_wkb,set_precision
 import guarded_power_projection_r44 as Z
 v=vias[0];normal=Z.bounded_disk(v,.8751);nf=O/'DOB-exact-normal-ground-via-foreign-antipad.wkb';nf.write_bytes(normal.wkb);assert sha(nf)=='165078876d502d97ef83317ca0cc1bfd99c66d82b481c0cc4ef1dd60ed45ca5f';rrows=json.loads((repair/'true-literal-rejected-and-successor-role-ledger.json').read_text());ordered=[]
 for row in rrows:
  rr=row['role'];uid=row['UUID'];prior=by[uid][rr];first=prior.difference(normal);assert hashlib.sha256(first.wkb).hexdigest()==row['rejected_R265_after_WKB_sha256'];current=first
  for step in row['all_role_operation_steps']:
   file=next(f for f in repair.glob('*explicit100nm-local-role-negative-mask.wkb')if sha(f)==step['explicit_local_reserve_sha256']);cut=from_wkb(file.read_bytes());tagged=set_precision(cut,1e-6,mode='pointwise');assert tagged.wkb==cut.wkb;current=current.difference(tagged)
  assert hashlib.sha256(current.wkb).hexdigest()==row['new_after_WKB_sha256'];aa=set_precision(prior,0);nn=set_precision(current,0);assert aa.wkb==prior.wkb and nn.wkb==current.wkb and nn.difference(aa).is_empty;ordered.append({'UUID':uid,'role':rr,'exact_before_WKB_sha256':hashlib.sha256(prior.wkb).hexdigest(),'normal_antipad_file':str(nf.resolve()),'normal_antipad_sha256':sha(nf),'rejected_after_first_mask_WKB_sha256':row['rejected_R265_after_WKB_sha256'],'ordered_local_negative_reserve_steps':row['all_role_operation_steps'],'exact_repaired_after_WKB_sha256':row['new_after_WKB_sha256'],'true_literal_zero_metadata_no_positive':True,'only_generated_operation_metadata_replayed_no_native_coords_snap':True})
 put(O/'ordered-exact-DOB-normal-antipad-plus-local-negative-replay.json',ordered);"""
assert s.count(start)==1;s=s.replace(start,new).replace('r267','r273').replace('R267','R273')
exec(compile(s,str(__file__),'exec'))
