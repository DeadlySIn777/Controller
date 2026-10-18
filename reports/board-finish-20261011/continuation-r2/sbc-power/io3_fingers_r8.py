"""Add bounded pad-free plane contact restoration to the preserved r4 fingers."""
import json,hashlib,math,time
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import io3_contact_restore_r2 as Q
import core_lane_r2 as R
L=R.L;p=R.p
def records(poly):return [[list(x.exterior.coords),[list(h.coords) for h in x.interiors]] for x in p.hubs.components(poly)]
def main():
    g,h,scope,native,prior,omit=R.model()
    old=json.loads((L.OUT/'IO3-restoration-fingers-r4.json').read_text());fingers=list(old['restoration_fingers'])
    lane_path=Path(old['CORE_after_fingers_file']);plane=from_wkb(lane_path.read_bytes());cut=plane.buffer(.175)
    extras=[{'uuid':'IO3-restoration-r4-'+str(i),'net':Q.NET,'fills':{'In2.Cu':records(from_wkb(Path(f['body_file']).read_bytes()))}} for i,f in enumerate(fingers)]
    projected={**g,'zones':g['zones']+extras}
    before,bparts,bmap=Q.groups(g,return_details=True,plane_terminals=True)
    after,aparts,amap=Q.groups(projected,cut,return_details=True,plane_terminals=True)
    orig_main=max(range(len(before)),key=lambda i:len(before[i]));orig_ids={r['source_obligation_uuid'] for r in before[orig_main]};assign={}
    for i,group in enumerate(after):
        for r in group:assign.setdefault(r['source_obligation_uuid'],set()).add(i)
    target_groups=set().union(*(assign.get(x,set()) for x in orig_ids));main=max(target_groups,key=lambda i:len(after[i]));detached=sorted(target_groups-{main})
    main_shape=unary_union([part for i,part in enumerate(aparts['In2.Cu']) if amap['In2.Cu'][i]==main]);window=box(103,97,240,172);p.WINDOW=window
    free=R.free_layer(h,Q.NET,'In2.Cu',window,('/LOGIC_GND',),reference_guard=None,allow_own_via_connection=True)
    centres={};failed=[]
    print('PAD_FREE_TARGETS',len(detached),[(i,len(after[i])) for i in detached],flush=True)
    for target in detached:
        target_shape=unary_union([part for i,part in enumerate(aparts['In2.Cu']) if amap['In2.Cu'][i]==target]);terminals=after[target]
        if target_shape.is_empty:failed.append({'group':target,'reason':'No In2 contact remains','terminals':terminals});continue
        aa,bb=nearest_points(target_shape,main_shape);distance=aa.distance(bb);chosen=None;attempts=[]
        widths=(.35,.5,.75,1.,1.25) if all(t['ref']=='@PLANE' for t in terminals) else (1.25,1.,.75,.5,.35)
        for width in widths:
            if width not in centres:centres[width]=p.hubs.components(free.buffer(-width/2-.005))
            target_buffer=target_shape.buffer(width/2-.025)
            main_buffer=main_shape.intersection(window.buffer(2.)).buffer(width/2-.025)
            for part in centres[width]:
                start=part.intersection(target_buffer)
                if start.is_empty:continue
                end=part.intersection(main_buffer)
                if end.is_empty:continue
                aa,bb=nearest_points(start,end);a=aa.coords[0];b=bb.coords[0]
                for extent in (2.,5.):
                    local=part.intersection(box(min(a[0],b[0])-extent,min(a[1],b[1])-extent,max(a[0],b[0])+extent,max(a[1],b[1])+extent))
                    route=L.six.five.exact_path(local,a,b,step=.1,node_cap=12000)
                    attempts.append({'width':width,'extent':extent,'verdict':route['verdict'],'nodes':route.get('searched_nodes')})
                    print('PLANE_ATTEMPT',target,width,extent,route['verdict'],flush=True)
                    if route['verdict']=='HOST_PATH':chosen={'width_mm':width,'route':route};break
                if chosen:break
            if chosen:break
        if chosen is None:failed.append({'group':target,'reason':'No local bounded finger','terminals':terminals,'attempts':attempts,'distance_mm':distance});continue
        body=LineString(chosen['route']['points']).buffer(chosen['width_mm']/2)
        assert free.covers(body.buffer(-1e-8))
        file=L.OUT/('IO3-padfree-group'+str(target)+'-r8.wkb');file.write_bytes(body.wkb)
        fingers.append({'candidate_group':target,'terminals':terminals,**chosen,'body_file':str(file.resolve()),'body_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'original_plane_contact_restoration':True,'actual_assigned_load_not_invented':True})
        main_shape=main_shape.union(body).union(target_shape)
    new=plane.difference(unary_union([from_wkb(Path(f['body_file']).read_bytes()) for f in fingers[17:]]).buffer(.175))
    file=L.OUT/'CORE-In2-after-IO3-fingers-r8.wkb';file.write_bytes(new.wkb)
    result={'exact_board':L.live.SHA,'initial_r4_receipt_sha256':hashlib.sha256((L.OUT/'IO3-restoration-fingers-r4.json').read_bytes()).hexdigest(),'new_padfree_detached_groups':detached,'all_original_source_contact_groups_restored_requires_final_regraph':not failed,'restoration_fingers':fingers,'failures':failed,'CORE_after_fingers_file':str(file.resolve()),'CORE_after_fingers_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'CORE_area_mm2':new.area,'fresh_native_contacts_and_IR_gate_open':True,'old_discrete_items_unchanged':True,'native_jobs':0,'board_written':False}
    (L.OUT/'IO3-restoration-fingers-r8.json').write_text(json.dumps(result,indent=2)+'\n');print('SUMMARY',len(detached),len(fingers),len(failed),new.area,flush=True)
if __name__=='__main__':main()
