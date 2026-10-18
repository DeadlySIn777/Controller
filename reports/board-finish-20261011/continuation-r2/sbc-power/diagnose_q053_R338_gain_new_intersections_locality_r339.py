"""Read-only q053 raw gain and controlling original-edge attribution."""
import hashlib,json,pickle,sys,time,traceback,math
from fractions import Fraction
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import guarded_power_projection_r44 as Z
O=H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339'
D=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-r338'
UID='053e747d-d229-5488-b123-0bd7612fb8ef'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,x):Path(p).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):a=set_precision(s,0);assert a.wkb==s.wkb;return a
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else list(s.bounds),'WKB_sha256':dg(s)}
def rings(s):
 for p in(s.geoms if s.geom_type=='MultiPolygon'else[s]):
  yield list(p.exterior.coords)
  for r in p.interiors:yield list(r.coords)
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'failure.json')=='9dd83cab7776e92ec697838edaa0b8b9bf116a54d6d5a7491ee18a423b181f32';mp=H/'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333/model.pkl';assert sha(mp)=='f9df66060a0f45959c4234f698500070c1ba2b4837894eee644cec36891dce9b';g,h,b,q,c=pickle.loads(mp.read_bytes());z=next(x for x in q if x['uuid']==UID);cut=zero(from_wkb((D/(UID+'-shape-normal-new-primitives-cutter.wkb')).read_bytes()));gain=zero(from_wkb((D/(UID+'-shape-0-literal-raw-positive-component.wkb')).read_bytes()));reserve=zero(Z.bounded_buffer(gain,.0001));corridor=box(116,169,139,208);outsideLocal=reserve.difference(corridor);outsideGuard=reserve.difference(zero(Z.bounded_buffer(cut,.0002)));(O/'failed-grid-gain-actual-100nm-reserve.wkb').write_bytes(reserve.wkb);(O/'failed-grid-reserve-outside-actual-normal-plus200nm.wkb').write_bytes(outsideGuard.wkb);(O/'failed-grid-reserve-outside-declared-owner-corridor.wkb').write_bytes(outsideLocal.wkb)
 before=zero(z['shape']);raw=before.difference(cut);(O/'shape-exact-parent.wkb').write_bytes(before.wkb);(O/'actual-normal-cut.wkb').write_bytes(cut.wkb);(O/'shape-literal-zero-direct-after.wkb').write_bytes(raw.wkb);rawgain=zero(raw).difference(before);(O/'shape-literal-zero-direct-gain.wkb').write_bytes(rawgain.wkb);oldverts={tuple(x)for rr in rings(before)for x in rr[:-1]};es=[(tuple(a),tuple(bb))for rr in rings(before)for a,bb in zip(rr,rr[1:])if a!=bb];lines=[LineString(e)for e in es];tree=STRtree(lines);rows=[]
 for v in{tuple(x)for rr in rings(raw)for x in rr[:-1]}-oldverts:
  if all(a==round(a*1e6)/1e6 for a in v):continue
  j=int(tree.nearest(Point(v)));a,bb=es[j];ax,ay,bx,by=map(Fraction.from_float,(*a,*bb));px,py=map(Fraction.from_float,v);cross=(px-ax)*(by-ay)-(py-ay)*(bx-ax);rows.append({'raw_new_vertex':list(v),'nearest_parent_edge':[list(a),list(bb)],'old_controlling_edge_length_mm':lines[j].length,'float_locator_distance_mm':Point(v).distance(lines[j]),'literal_binary64_collinear':cross==0,'literal_cross_numerator':str(cross.numerator),'literal_cross_denominator':str(cross.denominator),'old_edge_entirely_inside_declared_owner_corridor':corridor.covers(lines[j]),'new_point_inside_declared_owner_corridor':corridor.covers(Point(v))})
 for role in('shape','zone_outline_shape'):
  p=zero(z[role]);after=p.difference(cut);(O/(role+'-exact-parent.wkb')).write_bytes(p.wkb);(O/(role+'-literal-zero-direct-after.wkb')).write_bytes(after.wkb)
 put(O/'receipt.json',{'verdict':'READ_ONLY_CONTROLLED_NEW_INTERSECTION_AND_LOCALITY_ATTRIBUTION_NO_HEAD','R338_failure_sha256':sha(D/'failure.json'),'R333_model_sha256':sha(mp),'q053_failed_nm_grid_raw_gain':sm(gain),'raw_positive_witness_coordinates':list(rings(gain)),'explicit100nm_reserve':sm(reserve),'reserve_outside_actual_guard_plus200nm':sm(outsideGuard),'reserve_outside_declared_owner_corridor':sm(outsideLocal),'literal_zero_direct_after_gain':sm(rawgain),'only_new_fractional_cut_intersections':rows,'original_and_native_Cu_holes_roles_current_source_reference_or_adoption_changes':0,'all_after_current_source_reference_mesh_native_gates':'OPEN','elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R339_COMPLETE',sha(O/'receipt.json'),'gain',sm(gain),'reserve_outside_local',sm(outsideLocal),'new_intersections',len(rows),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
