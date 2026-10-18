"""Check direct outer same-source escapes before considering another drill."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import tri_route as T
OUT=H/'R214-field-ground-direct-outer-source-escape-diagnosis-r120'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());gs=pickle.loads(mp.with_name('groups.pkl').read_bytes())['/motherboard_motors/FIELD_GND'];root=next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==('J11003','2') for q in xs));rows=[];new={'tracks':[],'vias':[]}
    for ref,pin,layer in [('U10003','9','B.Cu'),('U11025','2','F.Cu')]:
        pad=next(p for p in h['pads'] if (p['ref'],p['num'])==(ref,pin));ps=unary_union(C.poly(pad['layers'][layer]));pt=Point(pad['x'],pad['y']);source=unary_union([q['shape'] for q in root if q['layer']==layer]);free=from_wkb((H/'R214-two-field-ground-fanout-face-diagnosis-r116'/(ref+'-10.0-outer.wkb')).read_bytes());hit=free.intersection(source)
        a,bb=nearest_points(free,source);near=[{'kind':q['kind'],'UUID':q['uuid'],'ref':q.get('ref'),'pin':q.get('pin'),'distance_to_outer_face_mm':free.distance(q['shape'])}for q in root if q['layer']==layer];near=sorted(near,key=lambda q:q['distance_to_outer_face_mm'])[:8]
        row={'ref':ref,'pin':pin,'layer':layer,'source_intersection_area_mm2':hit.area,'distance_to_actual_outer_source_mm':free.distance(source),'closest_source_objects':near,'closest_pair_mm':[list(a.coords[0]),list(bb.coords[0])],'direct_outer_route':None}
        if not hit.is_empty:
            start=nearest_points(free.intersection(ps.buffer(-.000020)),pt)[0];end=nearest_points(hit,pt)[0]
            try:points,_=T.route(free,tuple(start.coords[0]),tuple(end.coords[0]));row['direct_outer_route']=[[round(x,6),round(y,6)]for x,y in points]
            except (AssertionError,ValueError):pass
        rows.append(row)
    record={'verdict':'DIRECT_SAME_OUTER_GROUND_SOURCE_ESCAPE_DIAGNOSTIC_ONLY','parent_model_sha256':sha(mp),'rows':rows,'native_jobs':0,'board_written':False,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
