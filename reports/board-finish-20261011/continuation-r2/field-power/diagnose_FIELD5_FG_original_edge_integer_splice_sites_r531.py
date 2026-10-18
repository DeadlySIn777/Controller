"""Read-only exact parent-edge/lattice attribution for local FIELD5 notch."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,hashlib,time,math,traceback
from fractions import Fraction as F
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
D=H/'FIELD5-R525-raw-FG-gain-and-literal-boundary-attribution-r527';O=H/'FIELD5-original-edge-cut-intersection-and-native-lattice-attribution-r531'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def rings(s):
 for p in(s.geoms if s.geom_type=='MultiPolygon'else[s]):
  yield list(p.exterior.coords)
  for r in p.interiors:yield list(r.coords)
def main():
 assert not O.exists();O.mkdir();st=time.monotonic();before=from_wkb((D/'shape-exact-parent.wkb').read_bytes());after=from_wkb((D/'shape-literal_zero_direct_difference/after.wkb').read_bytes());cut=from_wkb((D/'actual-normal-cut.wkb').read_bytes());oldverts={tuple(x)for r in rings(before)for x in r[:-1]};es=[(tuple(a),tuple(z))for r in rings(before)for a,z in zip(r,r[1:])if a!=z];lines=[LineString(e)for e in es];tree=STRtree(lines);rows=[]
 for p in{tuple(x)for r in rings(after)for x in r[:-1]}-oldverts:
  if all(a==round(a*1e6)/1e6 for a in p):continue
  j=int(tree.nearest(Point(p)));a,z=es[j];ax,ay,zx,zy=map(F.from_float,(*a,*z));px,py=map(F.from_float,p);cross=(px-ax)*(zy-ay)-(py-ay)*(zx-ax);ints=[(round(x*1e6),round(y*1e6))for x,y in(a,z)];dx=ints[1][0]-ints[0][0];dy=ints[1][1]-ints[0][1];g=math.gcd(abs(dx),abs(dy));t=((p[0]-a[0])*(z[0]-a[0])+(p[1]-a[1])*(z[1]-a[1]))/(lines[j].length**2);k=t*g;near=[]
  for n in sorted({max(0,min(g,int(math.floor(k)))),max(0,min(g,int(math.ceil(k))))}):
   pt=((ints[0][0]+(dx//g)*n)/1e6,(ints[0][1]+(dy//g)*n)/1e6);fx,fy=map(F.from_float,pt);exactcross=(fx-ax)*(zy-ay)-(fy-ay)*(zx-ax);near.append({'integer_nm_point':pt,'fraction_of_edge':n/g,'distance_from_raw_intersection_mm':Point(pt).distance(Point(p)),'distance_to_cut_mm':Point(pt).distance(cut),'literal_binary64_collinear_with_old_edge':exactcross==0,'literal_cross_numerator':str(exactcross.numerator),'literal_cross_denominator':str(exactcross.denominator)})
  rows.append({'raw_new_vertex':p,'nearest_parent_edge':(a,z),'edge_length_mm':lines[j].length,'diagnostic_locator_distance_mm':Point(p).distance(lines[j]),'exact_binary64_point_collinear':cross==0,'literal_cross_numerator':str(cross.numerator),'literal_cross_denominator':str(cross.denominator),'native_integer_lattice_steps':g,'native_integer_lattice_interval_mm':lines[j].length/g,'nearest_native_lattice_candidates':near})
 put(O/'receipt.json',{'status':'READ_ONLY_EXACT_OLD_EDGE_AND_NATIVE_LATTICE_LOCATORS_NOT_GEOMETRY_AUTHORITY','old_physical_SHA256':dg(before),'literal_after_SHA256':dg(after),'cut_SHA256':dg(cut),'rows':rows,'near_float_locator_not_acceptance':True,'no_geometry_or_native_change':True,'elapsed_seconds':time.monotonic()-st});print('R531 noninteger intersections',len(rows),'sha',hashlib.sha256((O/'receipt.json').read_bytes()).hexdigest(),flush=True)
 print('max nearest lattice gap',max(min(c['distance_from_raw_intersection_mm']for c in r['nearest_native_lattice_candidates'])for r in rows),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
