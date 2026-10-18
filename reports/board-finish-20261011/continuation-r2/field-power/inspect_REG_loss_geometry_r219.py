"""Scoped original fill/discrete attribution of rejected REG interactions."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
import contact_layout as C
import fast_contacts as F
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'REG-exact-discrete-and-IO3-interaction-r219'

def main():
 assert not O.exists();O.mkdir()
 R=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r212';g,h,b,z,a=pickle.loads((R/'model.pkl').read_bytes());b['restored_generated_grid_UUIDs']=sorted({q['uuid'] for q in z});restore_bound_generated_precision_states(b,z)
 d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());qs=pickle.loads((R/'new-owned-zones.pkl').read_bytes())
 rows=[]
 for q in qs:rows.append({'UUID':q['uuid'],'net':q['net'],'layer':q['layer'],'shape_bounds_mm':list(q['shape'].bounds),'area_mm2':q['shape'].area,'metadata':{k:v for k,v in q.items() if not hasattr(v,'wkb') and isinstance(v,(str,int,float,bool,list,tuple))}})
 (O/'new-zone-summary.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 print('zones',json.dumps([{k:r[k] for k in ('UUID','net','layer','shape_bounds_mm','area_mm2')} for r in rows]),flush=True)
 lr=json.loads((H/'REG-B3-exact-IO3-and-LG-loss-attribution-r217/LOGIC-reference-loss-exact-proposal-attribution.json').read_text(encoding='utf-8'));allrows=[]
 for r in lr:
  sh=from_wkb(Path(r['exact_lost_shape_file']).read_bytes());own=[]
  for kind,rs in [('via',d['vias']),('track',d['tracks'])]:
   for x in rs:
    geom=Point(x['at']).buffer(x['size']/2,quad_segs=128) if kind=='via' else P.bounded_buffer(LineString([x['start'],x['end']]),x['width']/2)
    guard=G.gap(h,x['net'],'/LOGIC_GND')+.025;cut=P.bounded_buffer(geom,guard);inter=sh.intersection(cut)
    if inter.area>1e-12:own.append({'kind':kind,'UUID':x['uuid'],'net':x['net'],'at_or_start':x.get('at',x.get('start')),'nominal_guard_mm':guard,'lost_intersection_mm2':inter.area,'min_physical_gap_mm':geom.distance(sh),'max_shape_distance_from_center_or_line_mm':max([Point(v).distance(Point(x['at']) if kind=='via' else LineString([x['start'],x['end']])) for pg in ([sh] if sh.geom_type=='Polygon' else list(sh.geoms)) for v in pg.exterior.coords])})
  allrows.append({'old_track_UUID':r['uuid'],'lost_area_mm2':sh.area,'old_proposal_causes':r['proposal_buffer_causes'],'new_discrete_causes':own})
 (O/'lost-LG-discrete-attribution.json').write_text(json.dumps(allrows,indent=1)+'\n',encoding='utf-8');print('discrete causes',json.dumps(allrows),flush=True)
 q=next(q for q in qs if q['uuid']=='938b9038-0f65-5de2-99ed-d6781afcb116');io=F.graph(a,'/IO_3V3');root=next(xs for xs in io if any(x['kind']=='pad' and(x['ref'],x['pin'])==('R18001','2') for x in xs));target=next(xs for xs in io if any(x['kind']=='pad' and x['ref']=='R7043' and x['pin']=='1' for x in xs));
 (O/'actual-IO3-detached-group.pkl').write_bytes(pickle.dumps(target));(O/'actual-IO3-source-group.pkl').write_bytes(pickle.dumps(root))
 under=[]
 for orig in h['zones']:
  if C.norm(orig['net'])!='/IO_3V3' or 'In1.Cu' not in orig['fills']:continue
  cutter=P.bounded_buffer(q['shape'],max(float(orig['clearance_mm']),float(q.get('clearance_mm',.15)),G.gap(h,q['net'],orig['net']))+.025);sh=orig['fills']['In1.Cu'].intersection(cutter)
  if sh.area>1e-9:
   f=O/(orig['uuid']+'.IO3-original-cut.wkb');f.write_bytes(sh.wkb);under.append({'native_zone_UUID':orig['uuid'],'area_mm2':sh.area,'bounds_mm':list(sh.bounds),'file':str(f.resolve()),'sha256':sha(f)})
 (O/'IO3-938-exact-original-fill-cuts.json').write_text(json.dumps(under,indent=1)+'\n',encoding='utf-8');print('IO3 cuts',json.dumps(under),flush=True)
 (O/'receipt.json').write_text(json.dumps({'verdict':'SCOPED_DIAGNOSTIC_ONLY','parent_receipt_sha256':sha(R/'receipt.json'),'discrete':d,'IO3_cut_count':len(under)},indent=1)+'\n',encoding='utf-8')
 print('R219 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
