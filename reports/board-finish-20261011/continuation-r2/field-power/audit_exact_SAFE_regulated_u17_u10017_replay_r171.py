"""Preserve R170 compile failure; freeze derived generated grid bindings."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_exact_SAFE_regulated_u17_u10017_replay_r170.py').read_text(encoding='utf-8')
s=s.replace('r170','r171').replace('R170','R171')
s=s.replace("after,retreat=P.projected(g,h,z);\n+", "after,retreat=P.projected(g,h,z);\n+") if False else s
s=s.replace("after,retreat=P.projected(g,h,z);\n'''", "after,retreat=P.projected(g,h,z);\n '''")
old="print('R171 candidate full regional projection',flush=True);after,retreat=P.projected(g,h,z);"
new="""precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   original=q[role].wkb;loaded=get_precision(q[role]);q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==original
   precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'loaded_grid_mm':loaded,'exact_WKB_unchanged':True})
 b['restored_generated_grid_UUIDs']=[q['uuid'] for q in z];b['generated_precision_state_ledger']=precision;b['field_SAFE_regulated_replay_r171']={'exact_SAFE_parent_sha256':sha(baseline/'model.pkl'),'new_REG6_plus_protected_plane_count':7,'exact_owned_old_deletes':sorted(removed),'documented_prior_failed_R142_preserved':True}
 write(O/'derived-generated-precision-state-ledger.json',precision)
 print('R171 candidate full regional projection',flush=True);after,retreat=P.projected(g,h,z);"""
assert old in s;s=s.replace(old,new)
exec(compile(s,str(H/'audit_exact_SAFE_regulated_u17_u10017_replay_r170.py'),'exec'))
