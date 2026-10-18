"""Exact native local ON/PG ordinary-via escape search, prior to power pours."""
import json,math
from shapely.geometry import Point,box
from shapely.ops import nearest_points
import local_copper_r3 as T
L=T.L;p=T.p;R=T.R;V=T.V
def main():
    g,h,_=T.model();window=box(108,155,124,168);p.WINDOW=window;rows=[]
    for num in ('7','5'):
        pad=next(r for r in h['pads'] if r['ref']=='U11012' and r['num']==num);net=pad['net'];at=(pad['x'],pad['y']);region=V.via_region(h,net,window);free=R.free_layer(h,net,'F.Cu',window,('/LOGIC_GND','/IO_3V3',L.stage.caps.CORE,p.NET),reference_guard=None,allow_own_via_connection=True);found=[]
        for w in (.2,.15,.125):
            centre=free.buffer(-w/2)
            for component in p.hubs.components(centre):
                if not component.covers(Point(at)):continue
                landing=component.intersection(region.buffer(-.02))
                if landing.is_empty:continue
                site=nearest_points(Point(at),landing)[1].coords[0];route=L.six.five.exact_path(component,at,site,step=.05,node_cap=12000)
                if route['verdict']=='HOST_PATH':found.append({'site':site,'width_mm':w,'route':route});break
            if found:break
        rows.append({'pin':num,'net_raw':net,'native_pad_at':at,'via_escape':found,'no_clearance_mask_or_drill_exception':True})
        if found:h['vias'].append(T.T.via('switch-'+num,net,found[0]['site']))
        print('SWITCH_ESCAPE',num,found,flush=True)
    (L.OUT/'switch-signal-escapes-r2.json').write_text(json.dumps({'rows':rows,'exact_board':L.live.SHA,'native_jobs':0,'board_written':False},indent=2)+'\n')
if __name__=='__main__':main()
