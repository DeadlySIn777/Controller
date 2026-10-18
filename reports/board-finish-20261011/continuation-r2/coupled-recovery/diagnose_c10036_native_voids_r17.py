"""Bind reference gaps to exact old native fill/net/outline identities."""
import sys,json,pickle
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
def main():
 out=HERE/'c10036-native-void-diagnostic-r17.json';assert not out.exists();d=pickle.loads(A.read(HERE/'c10036-reference-barrier-r15.pkl'));g=d['g'];r=json.loads(A.read(HERE/'c10036-reference-barrier-r15.json'));body=LineString(r['B_power_route']['points_mm']).buffer(.15,quad_segs=128);gap=body.difference(d['planes']['In4.Cu']);rows=[]
 for z in g['zones']:
  shapes=L.poly(z['fills'].get('In4.Cu',[]));outline=unary_union(L.poly(z.get('outline',[])));shape=unary_union(shapes)
  if gap.distance(shape)<.4 or gap.intersects(outline):rows.append({'uuid':z['uuid'],'raw_net':z['net'],'outline_gap_intersection_area_mm2':outline.intersection(gap).area,'fill_gap_intersection_area_mm2':shape.intersection(gap).area,'fill_gap_distance_mm':shape.distance(gap),'local_clearance_mm':z.get('clearance_mm'),'priority':z.get('priority'),'outline_bounds':outline.bounds})
 foreign=[]
 rec,_=F.build({**g,'zones':[]},layers={'In4.Cu'})
 for q in rec['In4.Cu']:
  if q['shape'].distance(gap)<.8:foreign.append({'uuid':q['uuid'],'net':q['net'],'kind':q['kind'],'body_gap_distance_mm':q['shape'].distance(gap),'bounds':q['shape'].bounds})
 allground=unary_union([s for z in g['zones'] if L.norm(z['net'])=='/motherboard_do/FIELD_B_0V' for s in L.poly(z['fills'].get('In4.Cu',[]))]);report={'gap_area_mm2':gap.area,'gap_bounds':gap.bounds,'gap_with_all_field_ground_fills_mm2':gap.difference(allground).area,'zones':rows,'discrete_near_gaps':foreign,'read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()

