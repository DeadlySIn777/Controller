"""Restore only explicitly frozen generated-zone precision tags, WKB exact.

This changes GEOS operation metadata, never native originals or coordinates.
Unknown, missing, changed or unbound generated geometry is rejected.
"""
import hashlib
from shapely import set_precision,get_precision
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def restore_bound_generated_precision_states(binding,zones):
 assert binding.get('final_new_zone_coords_integer_nm_canonical_before_audit') is True
 rows=binding['generated_precision_state_ledger'];by={q['uuid']:q for q in zones}
 expected=set(binding['restored_generated_grid_UUIDs']);assert len(by)==len(zones) and set(by)==expected
 assert {(r['new_generated_UUID'],r['role']) for r in rows}=={(uid,role) for uid in expected for role in ('shape','zone_outline_shape')}
 result=[]
 for row in rows:
  uid=row['new_generated_UUID'];role=row['role'];q=by[uid]
  assert row['grid_mm']==1e-6 and row['mode']=='pointwise' and digest(q[role])==row['unchanged_WKB_SHA256']
  before=q[role].wkb;oldgrid=get_precision(q[role]);restored=set_precision(q[role],row['grid_mm'],mode=row['mode']);assert restored.wkb==before
  q[role]=restored;result.append({**row,'loaded_grid_mm':oldgrid,'restored_grid_mm':get_precision(restored),'exact_WKB_unchanged':True})
 return result
