"""Exact frozen positive-mesh interaction with retained outer power reference."""
import sys,json,pickle
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP));import contact_layout as L
sys.path.insert(0,str(HERE));import audit_aux_exact_raw as A
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
def main():
 out=HERE/'c10036-r41-reference-interaction-r23.json';assert not out.exists();d=pickle.loads(A.read(HERE/'c10036-joint-reference-bridge-diagnostic-r19.pkl'));zones=pickle.loads(A.read(FP/'regulated-field-source-feeds-r41/proposed-zones.pkl'));p=Point(d['old']['b']);near=[];tracklost=[]
 for q in zones:
  if q['layer']!='In4.Cu' or L.norm(q['net'])=='/motherboard_do/FIELD_B_0V':continue
  if q['shape'].distance(p)<1.:near.append({'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'body_point_distance_mm':q['shape'].distance(p),'buffered_point_distance_mm':q['shape'].buffer(.28,quad_segs=128).distance(p),'shape_bounds':q['shape'].bounds,'shape_WKB_sha256':A.C.sha(q['shape'].wkb)})
  for t in d['g']['tracks']:
   if t.get('m') is None and (max(t['a'][0],t['b'][0])+t['w']/2<62 or min(t['a'][0],t['b'][0])-t['w']/2>71 or max(t['a'][1],t['b'][1])+t['w']/2<90 or min(t['a'][1],t['b'][1])-t['w']/2>99):continue
   if t['layer']!='B.Cu' or L.norm(t['net'])=='/motherboard_do/FIELD_B_0V':continue
   body=L.body(t);oldcovered=body.intersection(d['planes']['In4.Cu']);lost=oldcovered.intersection(q['shape'].buffer(.275,quad_segs=128))
   if lost.area>1e-9:tracklost.append({'native_old_track_uuid':t['uuid'],'native_old_track_net':t['net'],'exact_track':t,'mesh_uuid':q['uuid'],'mesh_raw_net':q['net'],'prior_rooted_reference_intersection_mm2':lost.area,'bounds':lost.bounds})
 report={'endpoint_mm':d['old']['b'],'near_R41_In4_meshes':near,'all_current_B_outer_tracks_prior_rooted_reference_touched_by_R41':tracklost,'read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()

