"""Restore every original IO3 pad/via/track joined group around the CORE lane."""
import json,hashlib,math
from shapely import from_wkb
from shapely.geometry import Point,LineString,box,mapping
from shapely.ops import unary_union,nearest_points
import io3_contact_restore_r2 as Q
import core_lane_r2 as R
L=R.L;p=R.p
def main():
    g,h,scope,native,prior,omit=R.model();lane_path=L.OUT/'CORE-In2-variable-plane-r2.wkb';plane=from_wkb(lane_path.read_bytes());cut=plane.buffer(.175)
    before,bparts,bmap=Q.groups(g,return_details=True);after,aparts,amap=Q.groups(g,cut,return_details=True)
    orig_main=max(range(len(before)),key=lambda i:len(before[i]));orig_ids={r['uuid'] for r in before[orig_main]};assign={r['uuid']:i for i,group in enumerate(after) for r in group}
    target_groups={assign[x] for x in orig_ids};main=max(target_groups,key=lambda i:len(after[i]));detached=sorted(target_groups-{main})
    main_shape=unary_union([part for i,part in enumerate(aparts['In2.Cu']) if amap['In2.Cu'][i]==main]);window=box(103,97,240,172);p.WINDOW=window
    # CORE placement is explicitly carved by each restoration finger. Original
    # pads/actual foreign annuli/native tracks/holes and barriers remain fixed.
    free=R.free_layer(h,Q.NET,'In2.Cu',window,('/LOGIC_GND',),reference_guard=.025,allow_own_via_connection=True)
    fingers=[];failed=[]
    for target in detached:
        target_shape=unary_union([part for i,part in enumerate(aparts['In2.Cu']) if amap['In2.Cu'][i]==target]);terminals=after[target]
        if target_shape.is_empty:
            failed.append({'group':target,'reason':'No native In2 contact remains','terminals':terminals});continue
        aa,bb=nearest_points(target_shape,main_shape);distance=aa.distance(bb);routes=[]
        for width in (1.25,1.,.75,.5,.35):
            centre=free.buffer(-width/2)
            for part in p.hubs.components(centre):
                start=part.intersection(target_shape);end=part.intersection(main_shape)
                if start.is_empty or end.is_empty:continue
                a=start.representative_point().coords[0];b=nearest_points(start,end)[1].coords[0]
                route=L.six.five.exact_path(part,a,b,step=.1,node_cap=150000)
                if route.get('verdict')=='HOST_PATH':routes.append({'width_mm':width,'route':route});break
            if routes:break
        if not routes:
            failed.append({'group':target,'reason':'No exact legal In2 finger path in sampled widths','distance_mm':distance,'terminals':terminals});print('IO3_FAIL',target,distance,flush=True);continue
        chosen=routes[0];body=LineString(chosen['route']['points']).buffer(chosen['width_mm']/2)
        assert free.covers(body.buffer(-1e-8))
        finger_path=L.OUT/('IO3-finger3-group'+str(target)+'-r2.wkb');finger_path.write_bytes(body.wkb)
        row={'candidate_group':target,'terminals':terminals,'closest_original_main_distance_mm':distance,**chosen,'body_file':str(finger_path.resolve()),'body_sha256':hashlib.sha256(finger_path.read_bytes()).hexdigest(),'hypothetical_full_2A_branch_drop_mV_60C':.57003672*chosen['route']['length_mm']/chosen['width_mm']*2.,'old_pad_via_barrel_track_contacts_preserved_required':True}
        fingers.append(row);main_shape=main_shape.union(body).union(target_shape);print('IO3_FINGER',target,len(terminals),chosen['width_mm'],chosen['route']['length_mm'],flush=True)
    restored=unary_union([from_wkb(Path(f['body_file']).read_bytes()) for f in fingers]) if fingers else Point().buffer(0)
    newplane=plane.difference(restored.buffer(.175));output=L.OUT/'CORE-In2-after-IO3-fingers-r3.wkb';output.write_bytes(newplane.wkb)
    result={'exact_board':L.live.SHA,'original_pad_via_and_track_contacts_in_main_group':len(before[orig_main]),'candidate_main_group':main,'detached_contact_groups':detached,'restoration_fingers':fingers,'failures':failed,'fingers_restore_all_original_contact_groups_host_geometry':not failed,'original_CORE_plane_sha256':hashlib.sha256(lane_path.read_bytes()).hexdigest(),'CORE_after_fingers_file':str(output.resolve()),'CORE_after_fingers_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'IO3_new_copper_boolean_projection_only_native_fill_open':True,'old_discrete_items_unchanged':True,'all_original_pad_partitions_and_padfree_via_track_contacts_must_be_reverified':True,'new_CORE_banks_and_full_return_not_yet_recomputed':True,'source_hashes':p.READS,'board_written':False,'native_jobs':0}
    (L.OUT/'IO3-restoration-fingers-r3.json').write_text(json.dumps(result,indent=2)+'\n');print('SUMMARY',len(detached),len(fingers),len(failed),newplane.area,flush=True)
if __name__=='__main__':
    from pathlib import Path
    main()

