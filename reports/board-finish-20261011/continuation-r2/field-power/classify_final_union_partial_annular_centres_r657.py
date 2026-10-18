"""Keep R655 raw centre flags; distinguish inherited outer edges and holes."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;OUT=H/'final-union-ten-raw-centre-flags-exact-before-outline-attribution-r657'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def polys(s):return[s]if s.geom_type=='Polygon'else list(s.geoms)
def main():
 assert not OUT.exists();OUT.mkdir();m=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/model.pkl';assert sha(m)=='7141d6d37a909617aa339dadfc3b8a1b539904af1b06b2bf8f00ea2abeee69f9';g,h,b,q,c=pickle.loads(m.read_bytes());pk=m.parent/'only-four-current-member-to-qualified-direction-union-operation-candidates.pkl';plans=pickle.loads(pk.read_bytes());raw=H/'final-four-direction-union-native-intent-scope-readonly-r655/raw-enclosure-and-own-annular-landing-census.json';r=json.loads(raw.read_bytes());by={z['uuid']:z for z in q};rows=[]
 for e in r['errors']:
  assert e['kind']=='EXPECTED_ANNULAR_ATTACHMENT_CENTRE_OUTSIDE_NATIVE_INTENDED';v=e['row'];z=by[v['new_union_UUID']];p=next(a for a in plans if a['new_q']['uuid']==z['uuid']);before=unary_union([zero(a['zone_outline_shape'])for a in p['exact_before_q']]);after=zero(z['zone_outline_shape']);at=Point(v['at_mm']);holes=[]
  for poly in polys(after):
   for ring in poly.interiors:
    hpoly=Polygon(ring)
    if hpoly.covers(at):holes.append({'hole_WKB_SHA256':hashlib.sha256(hpoly.wkb).hexdigest(),'area_mm2':hpoly.area,'bounds_mm':list(hpoly.bounds),'all_integer_nm_coordinates':all(round(x*1e6)==x*1e6 and round(y*1e6)==y*1e6 for x,y in ring.coords)})
  rows.append({**v,'before_literal_member_intended_covers_centre':before.covers(at),'after_covers_centre':after.covers(at),'centre_enclosed_by_explicit_intended_hole':bool(holes),'holes':holes,'before_intended_distance_mm':before.distance(at),'after_intended_distance_mm':after.distance(at),'interpretation':'EXPLICIT_HOLE_ATTACHMENT_REQUIRES_SCOPED_NATIVE_OR_OWN_DRILL_CORRECTION'if holes else'PARTIAL_ANNULUS_AT_OUTER_EDGE_NATIVE_CONTACT_REMAINS_OPEN','new_union_changes_centre_membership':before.covers(at)!=after.covers(at)})
 put(OUT/'ten-exact-before-after-centre-and-hole-attributions.json',rows);put(OUT/'receipt.json',{'status':'READ_ONLY_RAW_CENTRE_FLAGS_PRESERVED_EXACT_BEFORE_SCOPE_CLASSIFIED','model_SHA256':sha(m),'R655_raw_census_SHA256':sha(raw),'attribution_SHA256':sha(OUT/'ten-exact-before-after-centre-and-hole-attributions.json'),'raw_flags':len(rows),'actual_explicit_hole_flags':sum(x['centre_enclosed_by_explicit_intended_hole']for x in rows),'new_union_centre_membership_changes':sum(x['new_union_changes_centre_membership']for x in rows),'no_geometry_change_blanket_hole_correction_or_native_flash_credit':True,'native_partial_annular_edge_contact_and_full_enclosure_FAILs':'OPEN_RETAINED'});print('R657',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
