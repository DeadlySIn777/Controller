import json,hashlib,math,copy,re
from shapely.geometry import Point,box
from shapely.affinity import translate,rotate
from shapely.ops import unary_union
import local_copper_r3 as T
L=T.L;p=T.p;R=T.R
def main():
    g,h,tail=T.model();native=tail[1];ref='C11088';foot=next(f for f in g['footprints'] if f['ref']==ref);pads=[q for q in g['pads'] if q['ref']==ref];cu=[unary_union(p.base.polygons(q['layers'].get('F.Cu',[]))) for q in pads];court=unary_union(p.base.polygons(foot['courtyard'].get('F',foot['courtyard'].get('F.Cu',[]))));window=box(193,85,269,150);p.WINDOW=window
    bodies=unary_union([poly for f in g['footprints'] if f.get('side')=='F' for layer,records in f['courtyard'].items() for poly in p.base.polygons(records) if poly.intersects(window)])
    free=[R.free_layer(h,q['net'],'F.Cu',window,('/LOGIC_GND',L.stage.caps.CORE),reference_guard=None,allow_own_via_connection=True) for q in pads]
    from shapely.prepared import prep
    pb=prep(bodies);pf=[prep(q) for q in free];sites=[]
    for rotation in (0,90,-90,180):
        centre=(foot['x'],foot['y']);rc=rotate(court,rotation,origin=centre);rp=[rotate(q,rotation,origin=centre) for q in cu]
        for ix in range(1950,2671,5):
            for iy in range(870,1481,5):
                x,y=ix/10,iy/10;dx=x-foot['x'];dy=y-foot['y'];c=translate(rc,dx,dy)
                if pb.intersects(c):continue
                pc=[translate(q,dx,dy) for q in rp]
                if not all(f.covers(q) for f,q in zip(pf,pc)):continue
                sites.append({'native_pose_xy_deg':[x,y,180-rotation],'distance_from_C88_mm':math.hypot(dx,dy),'pad_at':[list(q.centroid.coords[0]) for q in pc],'translated_courtyard_bounds':c.bounds})
    sites.sort(key=lambda x:x['distance_from_C88_mm']);ch=next(ch for ch in native.values() if p.base.pcbtext.chunk_kind(ch)=='footprint' and p.base.ref_of(ch)==ref)
    result={'exact_board':L.live.SHA,'C11088_original':foot,'native_at':re.search(rb'\(at ([^)]+)\)',ch).group(1).decode(),'native_chunk_sha256':hashlib.sha256(ch).hexdigest(),'pad_nets':[q['net'] for q in pads],'candidate_poses':sites[:20],'placement_count':len(sites),'new_C94_native_source_path_still_requires_combined_source_binding':True,'native_jobs':0,'board_written':False}
    (L.OUT/'C11094-placement-probe-r3.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
