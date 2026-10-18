"""Attribute literal LG-plane proximity and native hole ownership at old wall ports."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
OUT=H/'U10003-existing-wall-signal-port-source-hole-reference-r143'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,full=pickle.loads(mp.read_bytes());groups=pickle.loads(mp.with_name('groups.pkl').read_bytes());root=next(xs for xs in groups['/LOGIC_GND']if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11001','2')for q in xs));rows=[]
 for uid in('4422bb55-b6cf-449f-b92a-acb2d08a35b1','fa948c46-81c3-44ce-9287-51003d300406'):
  v=next(v for v in h['vias']if v['uuid']==uid);pt=Point(v['x'],v['y']);rr=[]
  for layer in('In1.Cu','In4.Cu'):
   sh=unary_union([q['shape']for q in root if q['layer']==layer and q['kind']=='fill']);holes=[]
   for q in full['zones']:
    if C.norm(q['net'])!='/LOGIC_GND':continue
    for i,p in enumerate(C.poly(q['fills'].get(layer,[]))):
     if p.distance(pt)>2:continue
     for j,ring in enumerate(p.interiors):
      from shapely.geometry import Polygon
      hole=Polygon(ring)
      if hole.covers(pt):holes.append({'zone_UUID':q['uuid'],'record':i,'hole':j,'bounds':hole.bounds,'area':hole.area,'boundary_distance_to_center':hole.boundary.distance(pt),'native_definition':q['uuid']in {o['uuid']for o in h['zones']}})
   rr.append({'layer':layer,'J11001_actual_plane_distance_mm':sh.distance(pt),'closest_actual_plane_point_mm':list(nearest_points(pt,sh)[1].coords[0]),'own_.575_cap_source_overlap_mm2':pt.buffer(.575,quad_segs=256).intersection(sh).area,'actual_enclosing_holes':holes})
  rows.append({'existing_signal_barrel':v,'rows':rr})
 receipt={'verdict':'READ_ONLY_OLD_PORT_LITERAL_SOURCE_AND_HOLE_OWNERSHIP','model_sha256':sha(mp),'rows':rows,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
