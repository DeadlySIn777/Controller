import json
from shapely.geometry import Point,box,mapping
from shapely.ops import unary_union
import layout_r1 as L
p=L.p
def main():
    g,h,scope,native,prior,omit=L.load();p.WINDOW=box(8,8,442,227);rows=[]
    for layer,plane in (('In2.Cu','In1.Cu'),('In3.Cu','In4.Cu'),('F.Cu','In1.Cu'),('B.Cu','In4.Cu')):
        zrows=[]
        for z in h['zones']:
            if layer not in z['fills']:continue
            poly=unary_union(p.base.polygons(z['fills'][layer]))
            if not poly.is_empty:zrows.append({'uuid':z['uuid'],'net':p.norm(z['net']),'area':poly.area,'source_distance':poly.distance(Point(243.375,115.15)),'load_distance':poly.distance(Point(116,161.4))})
        for repour in (False,True):
            model=dict(h)
            if repour:
                model['zones']=[{**z,'fills':{k:v for k,v in z['fills'].items() if k not in ('F.Cu','B.Cu','In2.Cu','In3.Cu')}} if p.norm(z['net'])=='/LOGIC_GND' else z for z in h['zones']]
            old=p.base.layer_reference;p.base.layer_reference=lambda gg,ll:g['_rooted_refs'][plane]
            try:free=p.free_copper(model,[],L.stage.caps.CORE,layer,window=p.WINDOW)
            finally:p.base.layer_reference=old
            cs=p.hubs.components(free.buffer(-.3));s=Point(243.375,115.15).buffer(12);l=Point(116,161.4).buffer(12)
            lead=[part for part in cs if part.intersects(s) and part.intersects(l)]
            row={'layer':layer,'repour_same_LOGIC_GND_on_routing_layers':repour,'component_count':len(cs),'source_components':[x.area for x in cs if x.intersects(s)],'load_components':[x.area for x in cs if x.intersects(l)],'shared':len(lead),'zones':zrows}
            rows.append(row);print('COMP',layer,repour,row['component_count'],row['source_components'],row['load_components'],row['shared'],flush=True)
            if repour and lead:
                dest=L.OUT/(layer.replace('.','-')+'-free-r1.wkb');dest.write_bytes(free.wkb)
    (L.OUT/'free-components-r1.json').write_text(json.dumps({'source':L.live.SHA,'rows':rows},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
