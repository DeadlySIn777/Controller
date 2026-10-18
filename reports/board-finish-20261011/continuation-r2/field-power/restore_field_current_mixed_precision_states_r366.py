"""Exhaustive frozen profile: literal physical edges, canonical native intents.

Only ED/D8 physical roles may have zero model-grid metadata. No WKB vertex
is changed, normalized, silently accepted, or granted source/native credit.
"""
import hashlib
from shapely import get_precision,set_precision
PROFILE='LITERAL_ZERO_ED_D8_PHYSICAL_AND_NM_ALL_OTHER_ROLES_R366'
ZERO={('ed7b6af5-93e5-5f20-8977-d10ca721564d','shape'),('d8d8bdad-3845-5659-b172-4d0e231cdadc','shape')}
def digest(x):return hashlib.sha256(x.wkb).hexdigest()
def restore_bound_field_current_precision_states(binding,zones):
 assert binding['field_current_generated_geometry_precision_profile']==PROFILE
 assert binding['final_native_intended_zone_coords_integer_nm_canonical_before_audit'] is True
 assert binding['final_new_zone_coords_integer_nm_canonical_before_audit'] is False
 rows=binding['generated_precision_state_ledger'];by={q['uuid']:q for q in zones};expected=set(binding['restored_generated_grid_UUIDs'])
 assert len(by)==len(zones) and set(by)==expected
 required={(uid,role)for uid in expected for role in ('shape','zone_outline_shape')}
 assert len(rows)==len(required) and {(r['new_generated_UUID'],r['role'])for r in rows}==required
 result=[]
 for row in rows:
  uid=row['new_generated_UUID'];role=row['role'];q=by[uid];grid=0 if(uid,role)in ZERO else 1e-6
  assert row['grid_mm']==grid and row['mode']=='pointwise'
  assert digest(q[role])==row['unchanged_WKB_SHA256'],('changed bound WKB',uid,role)
  before=q[role].wkb;old=get_precision(q[role]);after=set_precision(q[role],grid,mode='pointwise');assert after.wkb==before,('metadata restoration changes coordinates',uid,role)
  q[role]=after;result.append({**row,'loaded_grid_mm':old,'restored_grid_mm':get_precision(after),'exact_WKB_unchanged':True})
 return result
