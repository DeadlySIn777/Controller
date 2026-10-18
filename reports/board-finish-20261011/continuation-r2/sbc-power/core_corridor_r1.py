"""Ledgered split-layer CORE feeder construction; host search only."""
import json,copy,math,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box,mapping
from shapely.ops import unary_union
import layout_r1 as L
p=L.p;A=L.A;live=L.live;six=L.six;stage=L.stage
OUT=L.OUT

def main():
    g,h,scope,native,prior,omit=L.load()
    p.base.layer_reference=live.reference
    p.WINDOW=box(105,105,250,174);areas=[] if '--physical' in sys.argv else live.reservations()
    rows=[]
    for layer in ('In2.Cu','In3.Cu','B.Cu','F.Cu'):
        print('FREE',layer,flush=True)
        free=p.free_copper(h,areas,stage.caps.CORE,layer,window=p.WINDOW)
        for width in (3.,2.5,2.,1.5,1.):
            trunk=free.buffer(-width/2)
            source=Point(243.375,115.15).buffer(8)
            load=Point(116,161.4).buffer(8)
            connects=[]
            for part in p.hubs.components(trunk):
                aa=part.intersection(source);bb=part.intersection(load)
                if aa.is_empty or bb.is_empty:continue
                a=aa.representative_point().coords[0];b=bb.representative_point().coords[0]
                route=six.five.exact_path(part,a,b,step=.25,node_cap=350000)
                if route.get('verdict')!='HOST_PATH':continue
                connects.append({'a':a,'b':b,'path':route,'width':width,'layer':layer,'resistance_mohm_60C':.57003672*route['length_mm']/width})
            print('TRUNK',layer,width,'PATHS',len(connects),flush=True)
            rows.append({'layer':layer,'width':width,'paths':connects})
            if connects:break
    result={'source_sha256':live.SHA,'scope':scope,'window':p.WINDOW.bounds,'split_layer_leads':rows,'uniform_width_not_assumed':True,'physical_total_normal_CORE_A':6.63708429339838,'common_SBC_A':4.15,'branches_required':True,'stage_pad_arrays_and_shared_contacts_complete':False,'power_qualified':False,'board_written':False,'native_jobs':0,'source_hashes':p.READS}
    dest=OUT/('split-core-corridor-physical-r1.json' if '--physical' in sys.argv else 'split-core-corridor-r1.json')
    if dest.exists():raise ValueError('Immutable output exists')
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
