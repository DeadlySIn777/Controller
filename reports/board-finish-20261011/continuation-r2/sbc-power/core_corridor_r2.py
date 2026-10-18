"""Whole-board split-feed path search with the actual nearest reference plane."""
import json,math,copy
from shapely.geometry import Point,LineString,box,mapping
from shapely.ops import unary_union
import layout_r1 as L
p=L.p;six=L.six;stage=L.stage
def reference(g,layer):return g['_rooted_refs'][layer]
def main():
    g,h,scope,native,prior,omit=L.load();p.WINDOW=box(8,8,442,227)
    # This is not a clearance waiver: keepouts/barriers remain; retained routing
    # reservations are recorded as outdated endpoints and must be regenerated.
    areas=[];rows=[]
    for layer,plane in (('In2.Cu','In1.Cu'),('In3.Cu','In4.Cu'),('F.Cu','In1.Cu'),('B.Cu','In4.Cu')):
        old=p.base.layer_reference
        p.base.layer_reference=lambda gg,ll:reference(gg,plane)
        try:free=p.free_copper(h,areas,stage.caps.CORE,layer,window=p.WINDOW)
        finally:p.base.layer_reference=old
        for width in (3.,2.5,2.,1.5,1.,.6):
            trunk=free.buffer(-width/2);leads=[]
            source=Point(243.375,115.15).buffer(12);load=Point(116,161.4).buffer(12)
            for part in p.hubs.components(trunk):
                aa=part.intersection(source);bb=part.intersection(load)
                if aa.is_empty or bb.is_empty:continue
                a=aa.representative_point().coords[0];b=bb.representative_point().coords[0]
                route=six.five.exact_path(part,a,b,step=.5,node_cap=400000)
                if route.get('verdict')=='HOST_PATH':leads.append({'source_hub':a,'load_hub':b,'route':route,'resistance_mohm_60C':.57003672*route['length_mm']/width})
            print('WHOLE',layer,plane,width,len(leads),flush=True)
            rows.append({'layer':layer,'source_connected_reference':plane,'width':width,'leads':leads})
            if leads:break
    result={'source_sha256':L.live.SHA,'scope':scope,'window':p.WINDOW.bounds,'rows':rows,'nearest_reference_required':True,'both_In1_In4_unchanged':True,'historical_router_only_reservations_require_endpoint_regeneration':True,'barriers_rules_clearances_unchanged':True,'board_written':False,'source_and_load_arrays_not_yet_connected':True,'native_jobs':0,'source_hashes':p.READS}
    dest=L.OUT/'split-core-corridor-r2.json'
    if dest.exists():raise ValueError('Immutable output')
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
