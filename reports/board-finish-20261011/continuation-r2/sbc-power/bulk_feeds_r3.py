"""Ordinary C94 source/return banks and a separate In2 CORE feed arm."""
import json,hashlib,math
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import joint_model_r2 as J
import continuous_path_r2 as CP
L=J.L;p=J.p;R=J.R;V=J.V;C=J.C
def geom(name,shape):
    sh=set_precision(shape,1e-6);f=L.OUT/name;f.write_bytes(sh.wkb);return {'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':sh.area},sh
def main():
    g,h,tail=J.model();native=tail[1];joint=json.loads((L.OUT/'joint-power-planes-r3.json').read_text());h={**h,'vias':h['vias']+joint['new_CORE_bank_vias']};core=L.stage.caps.CORE;window=box(240,94,264,112);p.WINDOW=window;vias=[];banks=[];fparts={}
    for num,net in [('1',core),('2','/LOGIC_GND')]:
        pad=C.pad(h,'C11094',num);at=(pad['x'],pad['y']);free=R.free_layer(h,net,'F.Cu',window,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True);part=next(q for q in p.hubs.components(free) if q.covers(Point(at)));fparts[num]=part
        region=V.via_region(h,net,window).intersection(part.buffer(-.3));sites=sorted(p.hubs.pack_region(region,at,spacing=.8),key=lambda q:math.dist(at,q))[:4];vv=[C.via('C94-r3-'+num+'-'+str(i),net,[round(x,6) for x in q]) for i,q in enumerate(sites)];vias+=vv;h={**h,'vias':h['vias']+vv};banks.append({'pad':num,'net_raw':net,'sites':[[v['x'],v['y']] for v in vv],'planning_current_limit_each_A':.5,'capacitor_total_planning_screen_A':2.,'actual_switching_ripple_transient_and_fault_sharing_not_proven':True});print('C94_BANK',num,len(vv),flush=True)
    assert all(len(b['sites'])==4 for b in banks)
    arms=[]
    for num,net in [('1',core),('2','/LOGIC_GND')]:
        pad=C.pad(h,'C11094',num);at=(pad['x'],pad['y']);free=R.free_layer(h,net,'F.Cu',window,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True);part=next(q for q in p.hubs.components(free) if q.covers(Point(at)));lines=[];routes=[]
        for pt in banks[int(num)-1]['sites']:
            route=CP.path(part,at,pt);assert route['verdict']=='HOST_PATH';routes.append(route);lines.append(LineString(route['points']).buffer(1.))
        row,_=geom('C94-'+num+'-F-arm-r3.wkb',unary_union(lines).intersection(part));arms.append({'pad':num,'net_raw':net,**row,'routes':routes})
    old=from_wkb((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').read_bytes());window=box(216,89,266,126);p.WINDOW=window;free=R.free_layer(h,core,'In2.Cu',window,('/IO_3V3',),reference_guard=.025,allow_own_via_connection=True)
    fingers=json.loads((L.OUT/'IO3-restoration-fingers-r4.json').read_text())['restoration_fingers'];finger=unary_union([from_wkb(Path(q['body_file']).read_bytes()) for q in fingers]);free=free.difference(finger.buffer(.175));centre=free.buffer(-.3);end=banks[0]['sites'][0];part=next(q for q in p.hubs.components(centre) if q.covers(Point(end)) and not q.intersection(old.buffer(-.3)).is_empty);start=nearest_points(Point(end),part.intersection(old.buffer(-.3)))[1].coords[0];route=CP.path(part,start,end);assert route['verdict']=='HOST_PATH'
    added=LineString(route['points']).buffer(3).intersection(free);added=next(q for q in p.hubs.components(added) if q.covers(Point(end)));merged=old.union(added);micros=[];ledger=[];merged_guard=merged.buffer(.2)
    for z in g['zones']:
        if p.norm(z['net'])!='/IO_3V3':continue
        for i,poly in enumerate(p.base.polygons(z['fills'].get('In2.Cu',[]))):
            for j,sh in enumerate(p.hubs.components(poly)):
                if sh.area<=.05 and sh.intersects(merged_guard):
                    micros.append(sh);ledger.append({'zone_uuid':z['uuid'],'component_key':f'{z["uuid"]}@In2.Cu@{i}@{j}','old_native_chunk_sha256':hashlib.sha256(native[z['uuid']]).hexdigest(),'old_cu_wkb_sha256':hashlib.sha256(sh.wkb).hexdigest(),'old_cu_retained_entirely':True})
    merged=merged.difference(unary_union(micros).buffer(.2));mr,merged=geom('CORE-In2-with-C94-arm-r3.wkb',merged);ar,added=geom('CORE-In2-C94-added-arm-r3.wkb',added);print('C94_CORE_ARM',route['length_mm'],added.area,len(ledger),flush=True)
    result={'exact_board':L.live.SHA,'native_coordinate_grid_nm':1,'new_vias':vias,'C94_banks':banks,'C94_F_arms':arms,'CORE_In2_complete_plane':mr,'CORE_In2_added_C94_arm':ar,'C94_inner_route':route,'IO3_original_micro_piece_preservation_ledger':ledger,'old_IO3_all_pad_via_and_track_groups_additional_carve_guard_required':True,'full_CORE_normal_A':7.882034293398381,'C94_feed_conservative_transient_bound_and_loop_model_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'C94-bulk-feeds-r3.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
