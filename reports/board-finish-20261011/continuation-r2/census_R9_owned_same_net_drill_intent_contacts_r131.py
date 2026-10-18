"""Exact native annular contact census for pure own plated drill outline holes."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
OUT=H/'R9-owned-same-net-drill-intent-vs-actual-contact-census-r131'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';assert sha(mp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
    g,h,b,z,full=pickle.loads(mp.read_bytes());gp=H/'SAFE-exploratory-native-trial-r9/measure/actual-full-refill-geometry.json';assert sha(gp)=='20a225d2bfbd30206979609c10ccb5803f311c2a4c6b11afb0fdb067359e65b1';native=json.loads(gp.read_bytes())
    flashes=json.loads((gp.parent/'actual-full-refill-via-flashes.json').read_bytes())['vias'];new_ids=set(json.loads((gp.parent.parent/'native-postfill-via-obligations.json').read_bytes())['new_ordinary_via_UUIDs'])
    via_points=[Point(v['x'],v['y']) for v in h['vias']];vt=STRtree(via_points);actual={}
    for q in native['zones']:
        for layer,records in q['fills'].items():
            key=(C.norm(q['net']),layer)
            actual.setdefault(key,[]).extend(Polygon(rs[0],rs[1:]) for rs in records)
    actualtrees={k:STRtree(v) for k,v in actual.items()};rows=[];pure=[]
    for q in z:
        outline=q.get('zone_outline_shape',q['shape']);parts=[outline] if outline.geom_type=='Polygon' else list(outline.geoms)
        for pi,p in enumerate(parts):
            for hi,ring in enumerate(p.interiors):
                hole=Polygon(ring)
                for j in vt.query(hole,predicate='intersects'):
                    v=h['vias'][int(j)];pt=via_points[int(j)]
                    if C.norm(v['net'])!=C.norm(q['net']) or q['layer'] not in v['flashed'] or not hole.covers(pt):continue
                    ann=pt.buffer(v['d']/2,quad_segs=256).difference(pt.buffer(v['drill']/2,quad_segs=256));planned=q['shape'].intersection(ann).area
                    key=(C.norm(q['net']),q['layer']);xs=actual.get(key,[]);tree=actualtrees.get(key);indices=tree.query(ann,predicate='intersects') if tree is not None else []
                    actualnear=unary_union([xs[int(k)] for k in indices]);overlap=actualnear.intersection(ann).area
                    radius=v['drill']/2;radial=max(abs(Point(x,y).distance(pt)-radius) for x,y in list(ring.coords));samepure=radial<.000002 and len(p.interiors[hi].coords)>32
                    row={'owned_zone_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'owned_part_index':pi,'hole_index':hi,'hole_WKB_sha256':hashlib.sha256(hole.wkb).hexdigest(),'hole_area_mm2':hole.area,'old_or_new_via_UUID':v['uuid'],'centre_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'via_is_new_ordinary':v['uuid'] in new_ids,'actual_native_via_flash':q['layer'] in flashes.get(v['uuid'],[]),'exact_pure_own_drill_radius_max_deviation_mm':radial,'pure_own_drill_hole':samepure,'planned_physical_annular_overlap_mm2':planned,'actual_same_net_same_layer_filled_Cu_annular_overlap_mm2':overlap,'native_contact_deficit_despite_planned_overlap':planned>.01 and overlap==0.}
                    rows.append(row)
                    if samepure:pure.append(row)
    write(OUT/'all-owned-hole-annular-contact-rows.json',rows);write(OUT/'pure-own-plated-drill-hole-rows.json',pure)
    missing=[r for r in pure if r['native_contact_deficit_despite_planned_overlap']];write(OUT/'pure-own-drill-actual-contact-deficits.json',missing)
    record={'verdict':'PURE_OWN_PLATED_DRILL_INTENT_AND_ACTUAL_NATIVE_CONTACT_CENSUS_ONLY','model_sha256':sha(mp),'native_actual_geometry_sha256':sha(gp),'owned_hole_same_net_via_rows':len(rows),'bound_pure_own_plated_drill_hole_rows':len(pure),'actual_zero_annular_contact_despite_host_planned_positive':len(missing),'deficit_net_counts':{n:sum(r['raw_net']==n for r in missing) for n in sorted({r['raw_net'] for r in missing})},'deficit_unique_vias':len({r['old_or_new_via_UUID'] for r in missing}),'ordinary_forced_all6_flash_does_not_grant_a_source_zone_contact':True,'only_exact_literal_same_net_pure_holes_are_nominees_not_all_holes':True,'foreign_holes_native_keepouts_physical_q_and_original_Cu_unchanged':True,'rows_sha256':sha(OUT/'all-owned-hole-annular-contact-rows.json'),'pure_rows_sha256':sha(OUT/'pure-own-plated-drill-hole-rows.json'),'deficits_sha256':sha(OUT/'pure-own-drill-actual-contact-deficits.json'),'native_jobs':0,'board_written':False,'adopted':False}
    write(OUT/'receipt.json',record);print(json.dumps(record),flush=True)
if __name__=='__main__':main()
