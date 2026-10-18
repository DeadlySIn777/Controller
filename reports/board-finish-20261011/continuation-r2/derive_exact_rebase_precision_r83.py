"""Restore only declared generated operation tags before exact differences; preserve rejected R81."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'rebase_signal_reference_masks_on_joint_r81.py';dst=H/'rebase_signal_reference_masks_on_joint_r83.py';assert not dst.exists();s=src.read_text().replace('joint-positive-head-signal-reference-mask-proposal-r81','joint-positive-head-signal-reference-mask-proposal-r83').replace('R81_','R83_')
a=" for q,row in zip(updates,rows):";assert s.count(a)==1
b=""" replay=[]
 for authority,qs in [('exactROOT73old-generated',list(oldz.values())),('exactROOT74remove-only-generated',updates),('exactpositiveR214current-generated',z)]:
  for item in qs:
   for role in ('shape','zone_outline_shape'):
    original=item[role].wkb;restored=set_precision(item[role],1e-6,mode='pointwise');assert restored.wkb==original,'Reject coordinate/ring change in operation metadata repair';item[role]=restored;replay.append({'authority':authority,'UUID':item['uuid'],'role':role,'exact_WKB_sha256':digest(restored),'restored_generated_operation_grid_mm':1e-6})
 for q,row in zip(updates,rows):"""
s=s.replace(a,b)
a="put(out/'remove-only-geometry-rebase-ledger.json',changes);ledger=[]";assert s.count(a)==1;s=s.replace(a,"put(out/'remove-only-geometry-rebase-ledger.json',changes);put(out/'before-difference-exact-generated-operation-replay.json',replay);ledger=[]")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'signal-reference-rebase-r81-failure.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(src),'failure':'Exact remove-only subset check failed while decoded GEOS generated polygons had lost their frozen precision tags. The check stopped before output directory/model/proof/native.','phase':'NO_SAVED_PROPOSAL_OR_BOARD_EDIT','repair':'Replay1nm pointwise only on documented new generated shapes, require every WKB byte unchanged before differences; no native coordinate snap/tolerance/area waiver.','native_jobs':0,'adopted':False},indent=1)+'\n')
(H/'exact-rebase-precision-r83-derivation.json').write_text(json.dumps({'prior_constructor_sha256':sha(src),'derived_constructor_sha256':sha(dst),'only_new_generated_metadata_replayed_WKB_exact':True,'all_old_native_Cu_outlines_holes_pads_and_poses_unchanged':True,'original_signal_mask_and_source_failure_gates_preserved':True,'native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
