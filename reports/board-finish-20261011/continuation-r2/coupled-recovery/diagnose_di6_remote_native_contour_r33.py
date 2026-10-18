"""Native remote contour vertex ledger and actual old return nomination.

Pure diagnostic; no threshold waiver, reference adoption or power SI claim.
"""
import sys,json,pickle,math
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
from shapely.geometry import Point
C=A.C
def iu_vertices(z,layer):
 out=[]
 for native_polygon in z['fills'].get(layer,[]):
  for native_ring in native_polygon:
   for x,y in native_ring:
    assert abs(x*1000000-round(x*1000000))<.000001 and abs(y*1000000-round(y*1000000))<.000001
    out.append((round(x*1000000),round(y*1000000)))
 return set(out)
def main():
 out=HERE/'di6-remote-native-contour-return-diagnostic-r33.json';assert not out.exists();A.read(__file__);rp=HERE/'di6-matched-actual-native-independent-r27.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='c56ae1566e40cd7d385ba790873d24645bd4b36719900dc5ca3ddec320acd8b8';m=pickle.loads(A.read(r['saved_matched_actual_model']));g=m['after'];root=m['after_root'];refs=m['after_refs'];rk=Q.discrete_keys(root);native={}
 for key,d in [('before','di6-matched-native-baseline-r1'),('after','di6-native-diagnostic-r1')]:
  p=HERE.parent/d/'scoped-native-fill/geometry.json';ng=json.loads(A.read(p));native[key]={z['uuid']:z for z in ng['zones']}
 vertexrows=[]
 for u,l in [('58c55cd5-98e6-4467-88e3-146ceeee361a','In1.Cu'),('c1d27fa1-452b-4e27-985d-5ad23644d800','In4.Cu')]:
  b=iu_vertices(native['before'][u],l);a=iu_vertices(native['after'][u],l);removed=sorted(b-a);added=sorted(a-b);local_removed=[p for p in removed if abs(p[0]-342560000)<1000000 and abs(p[1]-100827000)<1000000];local_added=[p for p in added if abs(p[0]-342560000)<1000000 and abs(p[1]-100827000)<1000000];vertexrows.append({'zone_UUID':u,'layer':l,'before_removed_vertices_total':len(removed),'after_added_vertices_total':len(added),'exact_removed_local_vertices_IU':local_removed,'exact_added_local_vertices_IU':local_added,'minimum_local_changed_vertex_distance_IU':min((math.dist(p,q) for p in local_removed for q in local_added),default=None)})
 via=next(v for v in g['vias'] if v['uuid']=='237f91e0-a23b-4de7-8c1f-a116ad5338d0');candidates=[]
 for v in g['vias']:
  if L.norm(v['net'])!='/LOGIC_GND':continue
  d=math.dist((via['x'],via['y']),(v['x'],v['y']))
  if d>1.5:continue
  ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));areas={l:ref.buffer(-.075).intersection(ann).area for l,ref in refs.items() if l in('F.Cu','B.Cu')};row={'UUID':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':d,'d_mm':v['d'],'drill_mm':v['drill'],'actual_flash_layers':v['flashed'],'actual_source_rooted_J11001_2':('via',v['uuid']) in rk,'finite_interior_annular_contact_mm2':areas,'ordinary_geometric_pair_nominee':.81<=d<=1 and('via',v['uuid']) in rk and all(a>=.004 for a in areas.values())};candidates.append(row)
 report={'verdict':'REMOTE_NATIVE_CONTOUR_INTEGER_VERTEX_AND_EXISTING_RETURN_DIAGNOSTIC_ONLY','R27_sha256':C.sha(A.read(rp)),'exact_native_integer_vertex_deltas':vertexrows,'old_MOTION_5V_RAW_transition':via,'near_actual_source_rooted_return_nominees':sorted(candidates,key=lambda q:q['distance_mm']),'no_blanket_existing_transition_reference_waiver':True,'whole_power_feed_DC_return_SI_current_and_root_review':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'vertices':vertexrows,'returns':candidates}),flush=True)
if __name__=='__main__':main()
