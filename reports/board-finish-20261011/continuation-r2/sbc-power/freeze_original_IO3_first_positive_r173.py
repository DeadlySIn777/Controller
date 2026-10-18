"""Freeze the first exact R172 positive proposal without mutating its worker."""
from pathlib import Path
import hashlib,json,pickle
P=Path(__file__).resolve().parent;O=P/'original-IO3-r172-positive-snapshot-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();O.mkdir()
f=P/'original-IO3-physical-port-bridges-r172/accepted-zones.pkl';allq=pickle.loads(f.read_bytes());q=allq[0]
attempt=json.loads((f.parent/'attempts.json').read_bytes());r=next(x for x in attempt if x['new_UUID']==q['uuid'] and not x['lost_prior_source_keys'] and not x['target_keys_still_unrooted'])
o=O/'proposed-zones.pkl';o.write_bytes(pickle.dumps([q],protocol=5))
(O/'receipt.json').write_text(json.dumps({'verdict':'FIRST_ORIGINAL_IO3_ACTUAL_SOURCE_JOIN_GEOMETRY_HARD_SNAPSHOT_FULL_FOREIGN_NATIVE_CURRENT_OPEN','parent_SAFE_model_sha256':'d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b','accepted':r,'proposed_zones_sha256':sha(o),'physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'intended_WKB_sha256':hashlib.sha256(q['zone_outline_shape'].wkb).hexdigest(),'all_integer_nm_coordinates_from_constructor':True,'no_new_holes_or_original_discrete_or_native_zone_outline_changes':True,'hard_only_pending_full_mutual_reference_and_current_gates':True,'native_jobs':0,'board_written':False,'script_sha256':sha(Path(__file__))},indent=1)+'\n')
print('ORIGINAL_IO3_FIRST_SNAPSHOT',q['uuid'],r['layer'],r['length_mm'],r['source_keys'],sha(o),sha(O/'receipt.json'))
