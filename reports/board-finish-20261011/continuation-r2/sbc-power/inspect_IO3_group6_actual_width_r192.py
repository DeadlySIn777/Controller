"""Literal corridor body width screen; no capacity or area waiver."""
import hashlib,json,pickle
from pathlib import Path
from shapely.geometry import LineString
P=Path(__file__).resolve().parent;O=P/'IO3-group6-literal-width-screen-r192'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not O.exists();O.mkdir()
qf=P/'original-IO3-r172-positive-snapshot-8/proposed-zones.pkl';qs=pickle.loads(qf.read_bytes());q=next(q for q in qs if q['uuid']=='e1ca93bf-40e7-5ec0-8482-bcd115ce3838')
rf=P/'original-IO3-physical-port-bridges-r172/receipt.json';r=json.loads(rf.read_bytes());row=next(r for r in r['accepted'] if r['new_UUID']==q['uuid']);line=LineString(row['points_mm']);rows=[]
for width in (.25,.3,.35,.5):
 body=line.buffer(width/2,quad_segs=256);outside=body.difference(q['zone_outline_shape']);f=O/('width-'+str(width)+'-outside-intended.wkb');f.write_bytes(outside.wkb)
 rows.append({'width_mm':width,'literal_centerline_capsule_covered_by_actual_integer_intended_shape':q['zone_outline_shape'].covers(body),'outside_mm2':outside.area,'outside_WKB_sha256':sha(f),'outside_bounds':None if outside.is_empty else list(outside.bounds),'physical_drill_void_effect_mm2':body.intersection(q['zone_outline_shape'].difference(q['shape'])).area})
(O/'receipt.json').write_text(json.dumps({'verdict':'GEOMETRIC_WIDTH_SCREEN_CURRENT_AND_RETURN_QUALIFICATION_STILL_OPEN','IO3_eight_delta_sha256':sha(qf),'constructor_receipt_sha256':sha(rf),'UUID':q['uuid'],'layer':q['layer'],'length_mm':line.length,'rows':rows,'no_current_derating_or_capacity_claim':True,'no_geometry_or_source_change':True,'script_sha256':sha(Path(__file__))},indent=1)+'\n')
print('R192_COMPLETE',sha(O/'receipt.json'),rows,flush=True)
