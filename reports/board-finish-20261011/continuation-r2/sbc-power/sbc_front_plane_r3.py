"""Allocate a bounded F output bus, preserving room for the CORE input bus."""
import json,hashlib
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import local_copper_r3 as T
L=T.L;p=T.p;R=T.R
def main():
    g,h,_=T.model();window=box(108,156,124,172);p.WINDOW=window
    free=R.free_layer(h,p.NET,'F.Cu',window,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True)
    src=next(pad for pad in h['pads'] if pad['ref']=='U11012' and pad['num']=='8');source=(src['x'],src['y'])
    targets=[{'kind':'pad','ref':r['ref'],'pad':r['num'],'uuid':r['uuid'],'at':(r['x'],r['y'])} for r in h['pads'] if r['ref'] in ('U11012','C15001','C15002','J15001') and p.norm(r['net'])==p.norm(p.NET)]
    for v in h['vias']:
        if p.norm(v['net'])==p.norm(p.NET) and window.covers(Point(v['x'],v['y'])):targets.append({'kind':'via','uuid':v['uuid'],'at':(v['x'],v['y'])})
    for track in h['tracks']:
        if track['layer']=='F.Cu' and p.norm(track['net'])==p.norm(p.NET):
            intersection=p.base.body(track).intersection(free)
            if not intersection.is_empty:
                pt=intersection.representative_point();targets.append({'kind':'retained_track','uuid':track['uuid'],'at':(pt.x,pt.y)})
    lines=[];routes=[];centre=free.buffer(-.08)
    for target in targets:
        route=L.six.five.exact_path(centre,source,target['at'],step=.1,node_cap=18000)
        routes.append({**target,'route':route})
        if route['verdict']=='HOST_PATH':lines.append(LineString(route['points']).buffer(.9))
    if not all(r['route']['verdict']=='HOST_PATH' for r in routes):
        print('BLOCKED',[(r['kind'],r['uuid'],r['route']['verdict']) for r in routes if r['route']['verdict']!='HOST_PATH'],flush=True)
    bus=unary_union(lines).intersection(free);file=L.OUT/'SBC-F-bounded-bus-r3.wkb';file.write_bytes(bus.wkb)
    result={'exact_board':L.live.SHA,'allocated_SBC_F_plane_file':str(file.resolve()),'allocated_plane_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'allocated_area_mm2':bus.area,'target_routes':routes,'all_exact_routes_found':all(r['route']['verdict']=='HOST_PATH' for r in routes),'C11063_native_pose':[115.75,165.325,-90.],'full_F_IR_return_and_six_contact_connector_qualification_open':True,'new_CORE_F_plane_and_via_banks_must_exclude_bus_plus_clearance':True,'native_jobs':0,'board_written':False}
    (L.OUT/'SBC-F-bounded-bus-r3.json').write_text(json.dumps(result,indent=2)+'\n');print('SBC_ALLOCATED',bus.area,len(routes),result['all_exact_routes_found'],flush=True)
if __name__=='__main__':main()
