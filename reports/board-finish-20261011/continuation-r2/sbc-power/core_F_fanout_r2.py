"""Concrete CORE F fanouts, retaining exact copper/pads and ordinary via geometry."""
import json,hashlib,math
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union
import core_lane_r2 as R
p=R.p;L=R.L
def main():
    g,h,scope,native,prior,omit=R.model();proposal=json.loads((L.OUT/'CORE-In2-variable-plane-r2.json').read_text());out=[]
    for bank,window,padrefs in [(proposal['ordinary_via_banks'][0],box(209,97,248,121),[('R11022','2'),('C11088','1')]),(proposal['ordinary_via_banks'][1],box(108,154,124,166),[('U11012','3'),('U11012','4'),('U11012','11'),('C11062','1')])]:
        p.WINDOW=window
        free=R.free_layer(h,L.stage.caps.CORE,'F.Cu',window,('/LOGIC_GND',),reference_guard=.025)
        bodies={ref+'.'+num:next(pad for pad in h['pads'] if pad['ref']==ref and pad['num']==num) for ref,num in padrefs}
        parts=p.hubs.components(free);parts=sorted(parts,key=lambda part:sum(part.intersects(L.body_pad(pad)) for pad in bodies.values()),reverse=True)
        touched=[]
        for n,part in enumerate(parts):
            contacts=[name for name,pad in bodies.items() if part.intersects(L.body_pad(pad))]
            sites=[v for v in bank['sites'] if part.covers(Point(v['at']).buffer(.3))]
            if contacts or sites:
                touched.append({'part_index':n,'area_mm2':part.area,'required_pads':contacts,'bank_sites':[v['at'] for v in sites]})
                if contacts:
                    dest=L.OUT/('CORE-'+bank['name']+'-F-part'+str(n)+'-r2.wkb');dest.write_bytes(part.wkb);touched[-1].update(geometry_file=str(dest.resolve()),geometry_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
        print('FANOUT',bank['name'],json.dumps(touched),flush=True)
        out.append({'bank':bank['name'],'window':window.bounds,'required_pad_refs':list(bodies),'parts':touched,'all_components_share_one_part':any(set(t['required_pads'])==set(bodies) for t in touched),'all_bank_sites_reachable':sum(len(t['bank_sites']) for t in touched if t['required_pads'])==len(bank['sites'])})
    (L.OUT/'CORE-F-fanout-r2.json').write_text(json.dumps({'exact_board':L.live.SHA,'fresh_scope':scope,'rows':out,'local_F_GND_repours_required':True,'source_hashes':p.READS,'board_written':False,'native_jobs':0},indent=2)+'\n')
if __name__=='__main__':main()
