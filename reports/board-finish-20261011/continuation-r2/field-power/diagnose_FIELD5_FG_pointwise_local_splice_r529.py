"""Read-only native vertex splice: preserve all parent vertices, no model."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time,traceback
from pathlib import Path
from shapely import set_precision,from_wkb
from shapely.geometry import Polygon,MultiPolygon,Point,LineString
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import guarded_declared_settings_projection_r58 as N
from inventory import sha
D=H/'FIELD5-R525-raw-FG-gain-and-literal-boundary-attribution-r527'
O=H/'FIELD5-R525-pointwise-local-vertex-edge-splice-attribution-r529'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'sha256':dg(s)}
def polys(s):return list(s.geoms)if s.geom_type=='MultiPolygon'else[s]
def rings(s):
 for p in polys(s):
  yield list(p.exterior.coords)
  for r in p.interiors:yield list(r.coords)
def vertices(s):return {tuple(x)for r in rings(s)for x in r[:-1]}
def edges(s):return {tuple(sorted((tuple(a),tuple(z))))for r in rings(s)for a,z in zip(r,r[1:])}
def save(f,s):f.write_bytes(s.wkb);return {'file':str(f.resolve()),'sha256':sha(f),**sm(s)}
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();cut=from_wkb((D/'actual-normal-cut.wkb').read_bytes());local=from_wkb((D/'declared-2mm-locality.wkb').read_bytes());rows=[]
 for role in ('shape','zone_outline_shape'):
  before=from_wkb((D/(role+'-exact-parent.wkb')).read_bytes());raw=from_wkb((D/(role+'-literal_zero_direct_difference')/'after.wkb').read_bytes());oldvertices=vertices(before);oldedges=edges(before)
  changed=[]
  def coord(x):
   v=tuple(x)
   if v in oldvertices:return v
   out=tuple(round(a*1e6)/1e6 for a in v);changed.append({'before':v,'after':out,'cut_distance_mm':Point(v).distance(cut)})
   return out
  ps=[Polygon([coord(x)for x in p.exterior.coords],[[coord(x)for x in r.coords]for r in p.interiors])for p in polys(raw)]
  manual=MultiPolygon(ps)if len(ps)>1 else ps[0]
  for name,after in [('raw_literal',raw),('pointwise_nm_no_valid_output_rebuild',lit(set_precision(raw,1e-6,mode='pointwise'))),('only_non_parent_vertices_nearest_nm',manual)]:
   path=O/(role+'-'+name);path.mkdir();gain=after.difference(before);loss=before.difference(after);outer=gain.difference(local);outchange=before.symmetric_difference(after).difference(local);vs=vertices(after);es=edges(after);remote_oldv={v for v in oldvertices if Point(v).disjoint(local)};remote_olde={e for e in oldedges if LineString(e).disjoint(local)};missingv=remote_oldv-vs;missinge=remote_olde-es
   row={'role':role,'variant':name,'valid':after.is_valid,'gain':save(path/'literal-gain.wkb',gain),'loss':save(path/'literal-loss.wkb',loss),'gain_outside_locality':save(path/'literal-gain-outside-2mm.wkb',outer),'change_outside_locality':save(path/'literal-change-outside-2mm.wkb',outchange),'after':save(path/'after.wkb',after),'remote_parent_vertex_count':len(remote_oldv),'remote_parent_edge_count':len(remote_olde),'remote_exact_vertex_missing_count':len(missingv),'remote_exact_edge_missing_count':len(missinge),'missing_remote_vertices':sorted(missingv),'missing_remote_edges':sorted(missinge),'only_non_parent_vertex_round_rows':changed if name=='only_non_parent_vertices_nearest_nm'else None};rows.append(row)
   print(role,name,'valid',after.is_valid,'gain',gain.area,'outside2',outer.area,'missingv/e',len(missingv),len(missinge),flush=True)
 put(O/'receipt.json',{'status':'READ_ONLY_VERTEX_EDGE_PRESERVATION_DIAGNOSIS_NO_MODEL','R527_receipt_SHA256':sha(D/'receipt.json'),'rows':rows,'no_boundary_area_waiver':True,'native_jobs':0,'accepted':False,'elapsed_seconds':time.monotonic()-start});print('R529',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_model_or_acceptance':True})
  raise
