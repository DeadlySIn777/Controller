"""Exact cached original outline vs actual CPP fill; no geometry mutation."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,collections
from pathlib import Path
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=H/'R157-original-ground-outline-hole-min-thickness-and-actual-root-attribution-r661'
B=H/'eedf-original-parent-exact-cached-native-BEFORE-dump-r648/native-cached/cached-geometry.json'
N=ROOT/'R155-known-reference-native-diagnostic-r157/measure'
A=H/'R157-twenty-two-native-mask-loss-exact-cached-parent-finite-annulus-attribution-r659/twenty-two-vias-twenty-three-layer-exact-attribution.json'
G=H/'four-direction-unions-corrected-corners-actual-source-contact-reference-r645/actual-drilled-current-groups.pkl'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();before=json.loads(B.read_bytes());after=json.loads((N/'actual-full-refill-geometry.json').read_bytes());losses=json.loads(A.read_bytes());groups=pickle.loads(G.read_bytes());roots={L.norm(net):K.root(groups[L.norm(net)],ref,pin)for net,ref,pin in K.ROOTS[:3]};by={z['uuid']:z for z in after['zones']};out=[]
 assert sha(B)=='fb9302a169981fc77fd8493ae80919c7ebe72c561701e7095d3cf377a06814e0'
 stored=sum(bool(v)for z in before['zones']for v in z['fills'].values());assert stored==0
 for a in losses:
  uid=a['via_UUID'];ly=a['missing_layer'];raw=a['raw_net'];at=Point(a['at_mm']);ann=at.buffer(a['diameter_mm']/2,quad_segs=64).difference(at.buffer(a['drill_mm']/2,quad_segs=64));pieces=[]
  for z in before['zones']:
   if z['net']!=raw or ly not in z['layers']:continue
   polys=L.poly(O.polys(z['outline']));outline=unary_union(polys)
   if ann.distance(outline)>.3:continue
   az=by[z['uuid']];assert z['outline']==az['outline'],'Original zone outline mutated';assert all(z[k]==az[k]for k in ('priority','clearance_mm','min_thickness_mm','island_removal','min_island_area_mm2'))
   hit=ann.intersection(outline);holes=[]
   for poly in polys:
    for ring in poly.interiors:
     hole=Polygon(ring)
     if not hole.covers(at):continue
     hp=OUT/(uid+'-'+ly.replace('.','-')+'-'+z['uuid']+'-own-centre-containing-original-hole.wkb');hp.write_bytes(hole.wkb)
     holes.append({'hole':ds(hole),'file':str(hp.resolve()),'native_polygon_rings_integer_IU_preserved':True,'hole_vertex_count':len(ring.coords)-1,'min_vertex_radius_mm':min(at.distance(Point(x,y))for x,y in ring.coords),'max_vertex_radius_mm':max(at.distance(Point(x,y))for x,y in ring.coords),'nominal_own_drill_area_mm2':at.buffer(a['drill_mm']/2,quad_segs=64).area,'hole_outside_nominal_own_drill':ds(hole.difference(at.buffer(a['drill_mm']/2,quad_segs=64)))})
   afill=unary_union(L.poly(O.polys(az['fills'][ly])));pieces.append({'original_ground_zone_UUID':z['uuid'],'original_ground_raw_net':raw,'priority':z['priority'],'local_clearance_mm':z['clearance_mm'],'min_thickness_mm':z['min_thickness_mm'],'island_removal':z['island_removal'],'min_island_area_mm2':z['min_island_area_mm2'],'original_intended_polygon_SHA256':hs(outline),'cached_parent_stored_fill_polygon_count':len(z['fills'][ly]),'exact_original_outline_and_profile_unchanged_in_R157':True,'original_intended_covers_via_centre':outline.covers(at),'original_intended_nominal_drilled_annular_contact':ds(hit),'centre_containing_original_holes':holes,'actual_CPP_filled_nominal_drilled_annular_contact':ds(ann.intersection(afill)),'actual_CPP_fill_gap_mm':None if afill.is_empty else ann.distance(afill)})
  xs=roots[L.norm(raw)];keys=K.keys(xs);key=('via',uid,ly);rootkeyrows=[r for r in xs if r['kind']=='via'and r['uuid']==uid and r['layer']==ly];out.append({'via_UUID':uid,'raw_net':raw,'at_mm':a['at_mm'],'missing_layer':ly,'original_outline_records':pieces,'later_R645_host_source_root_contains_actual_physical_via_layer':bool(rootkeyrows),'later_host_not_actual_CPP_source_evidence':True});print('R661',uid[:8],ly,'originalholes',sum(len(r['centre_containing_original_holes'])for r in pieces),'hostroot',bool(rootkeyrows),flush=True)
 put(OUT/'exact-old-native-outline-hole-profile-and-later-host-source-attribution.json',out)
 put(OUT/'receipt.json',{'status':'READ_ONLY_ORIGINAL_GROUND_OUTLINE_AND_NATIVE_FILL_FAILURE_ATTRIBUTION','cached_parent_geometry_SHA256':sha(B),'cached_parent_stored_fill_layers':stored,'native_refilled_geometry_SHA256':sha(N/'actual-full-refill-geometry.json'),'R659_attribution_SHA256':sha(A),'later_R645_actual_host_group_SHA256':sha(G),'attribution_SHA256':sha(OUT/'exact-old-native-outline-hole-profile-and-later-host-source-attribution.json'),'lost_layer_rows':len(out),'with_original_centre_holes':sum(any(z['centre_containing_original_holes']for z in r['original_outline_records'])for r in out),'original_masks_are_not_finite_cached_fill_contacts':True,'native_old_masks_physical_outline_profile_and_all_failure_flags_preserved':True,'no_native_save_refill_or_manual_cached_fill_edit':True,'local_source_plane_or_original_outline_repair_current_reference_native_source':'OPEN_NOT_CONSTRUCTED','elapsed_seconds':time.monotonic()-st});print('R661_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
