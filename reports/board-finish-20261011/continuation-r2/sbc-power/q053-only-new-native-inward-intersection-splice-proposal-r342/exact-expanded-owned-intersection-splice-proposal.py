"""Scoped integer splice proposal: all parent vertices exact, no model/adoption.

Every new fractional cut intersection moves at most 0.5um into the retained
literal polygon. Actual additional removed wedges are explicit, never waived.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,traceback,math
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,Polygon,MultiPolygon,box
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'sbc-power'))
import guarded_declared_settings_projection_r58 as N
D=H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339';O=H/'sbc-power/q053-only-new-native-inward-intersection-splice-proposal-r342'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'sha256':dg(s)}
def polys(s):return list(s.geoms)if s.geom_type=='MultiPolygon'else[s]
def rings(s):
 for p in polys(s):
  yield list(p.exterior.coords)
  for r in p.interiors:yield list(r.coords)
def vertices(s):return{tuple(x)for r in rings(s)for x in r[:-1]}
def edges(s):return{tuple(sorted((tuple(a),tuple(z))))for r in rings(s)for a,z in zip(r,r[1:])}
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(f,s):f.write_bytes(s.wkb);return {'file':str(f.resolve()),**sm(s)}
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def main():
 assert not O.exists();O.mkdir();st=time.monotonic();assert hashlib.sha256((D/'receipt.json').read_bytes()).hexdigest()=='c9d0fac1b6e01d61b7c732952c12557b4fe3e8ff1bcb95a7d3ddba4e7ee5bf91';(O/'exact-expanded-owned-intersection-splice-proposal.py').write_text(EXACT_EXPANDED_SOURCE,encoding='utf-8');cut=from_wkb((D/'actual-normal-cut.wkb').read_bytes());local=box(116,169,139,208);rows=[];objects={}
 for role in('shape','zone_outline_shape'):
  before=from_wkb((D/(role+'-exact-parent.wkb')).read_bytes());raw=from_wkb((D/(role+'-literal-zero-direct-after.wkb')).read_bytes());oldv=vertices(before);olde=edges(before);moves={}
  for v in vertices(raw)-oldv:
   if all(a==round(a*1e6)/1e6 for a in v):continue
   choices=[]
   for radius in(.0001,.0002,.0005,.001,.002):
    angles=[2*math.pi*i/256 for i in range(256)]
    for r in rings(raw):
     for k,x in enumerate(r[:-1]):
      if tuple(x)!=v:continue
      aa=r[k-1] if k else r[-2];zz=r[k+1];ux,uy=aa[0]-v[0],aa[1]-v[1];vx,vy=zz[0]-v[0],zz[1]-v[1];u=math.hypot(ux,uy);w=math.hypot(vx,vy);angle=math.atan2(uy/u+vy/w,ux/u+vx/w);angles.extend([angle,angle+math.pi])
    for angle in angles:
     a=angle;pt=(round((v[0]+radius*math.cos(a))*1e6)/1e6,round((v[1]+radius*math.sin(a))*1e6)/1e6);s=Point(pt)
     if raw.covers(s)and before.covers(s)and s.distance(raw.boundary)>=.000000001:choices.append((s.distance(Point(v)),pt))
    if choices:break
   assert choices,('no inward local native intersection',role,v);moves[v]=min(choices)[1]
  def rc(r):return[moves.get(tuple(x),tuple(x))for x in r.coords]
  ps=[Polygon(rc(p.exterior),[rc(r)for r in p.interiors])for p in polys(raw)];after=MultiPolygon(ps)if len(ps)>1 else ps[0];assert after.is_valid
  gain=after.difference(before);removed=before.difference(after);extra=removed.difference(cut);outside=extra.difference(local);remotev={v for v in oldv if Point(v).disjoint(local)};remotee={e for e in olde if LineString(e).disjoint(local)}
  assert gain.is_empty,('new-intersection splice literal gain',role,sm(gain));assert outside.is_empty,('owned negative wedge outside declared local corridor',role,sm(outside));assert remotee<=edges(after)and remotev<=vertices(after),('original vertex or complete edge changed outside local owned corridor',role);row={'role':role,'before_sha256':dg(before),'after':save(O/(role+'-only-new-intersections-inward.wkb'),after),'gain':save(O/(role+'-literal-gain.wkb'),gain),'removed':save(O/(role+'-literal-removed.wkb'),removed),'extra_negative_outside_primary_guard':save(O/(role+'-additional-negative-wedges-outside-primary-cut.wkb'),extra),'extra_negative_outside_declared_owner_corridor':save(O/(role+'-additional-negative-wedges-outside-declared-corridor.wkb'),outside),'intersection_moves':[{'before':a,'after':z,'displacement_mm':Point(a).distance(Point(z)),'new_point_inside_literal_before_and_after':True}for a,z in moves.items()],'all_complete_parent_edges_disjoint_declared_corridor_identical':remotee<=edges(after),'all_parent_vertices_disjoint_declared_corridor_identical':remotev<=vertices(after),'native_intended_integer_nm_vertices':all(a==round(a*1e6)/1e6 for v in vertices(after)for a in v),'strict_gain_EMPTY':gain.is_empty,'extra_negative_outside_declared_corridor_EMPTY':outside.is_empty,'additional_negative_requires_explicit_local_scope_and_fresh_source_current_proof':not extra.is_empty};rows.append(row);objects[role]=after
  print(role,'gain',gain.area,'extra-negative',extra.area,'outside2',outside.area,'moves',len(moves),flush=True)
 put(O/'receipt.json',{'status':'Q053_ONLY_NEW_NATIVE_INTERSECTION_SPLICE_STRICT_NEGATIVE_LOCAL_PROPOSAL_ONLY_NO_MODEL','R339_input_receipt_sha256':hashlib.sha256((D/'receipt.json').read_bytes()).hexdigest(),'rows':rows,'only_parent_cut_intersections_moved_other_vertex_tokens_exact':True,'raw_R525_R527_R529_failures_preserved':True,'current_contacts_source_references_native_OPEN':True,'accepted':False,'elapsed_seconds':time.monotonic()-st});(O/'only-proposed-q053-two-roles.pkl').write_bytes(pickle.dumps(objects,protocol=5));print('R342',hashlib.sha256((O/'receipt.json').read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_model_or_adoption':True})
  raise
