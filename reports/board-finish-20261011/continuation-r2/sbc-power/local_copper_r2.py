"""Ordinary local CT, decoupling and return geometry; no native operations."""
import json,hashlib,math,uuid,copy
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import core_lane_r2 as R
import core_variable_plane_r2 as V
import raw_net_tokens_r2 as N
L=R.L;p=R.p
HERE=L.OUT
def uid(label):return str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-sbc-r2-local/'+label))
def pad(g,ref,num):return next(r for r in g['pads'] if r['ref']==ref and r['num']==num)
def track(label,net,layer,a,b,w):return {'uuid':uid(label),'net':N.raw(net),'layer':layer,'a':list(a),'b':list(b),'w':w,'locked':False}
def via(label,net,at):return {'uuid':uid(label),'net':N.raw(net),'x':at[0],'y':at[1],'d':.6,'drill':.3,'span':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']}
def main():
    g,h,*_=R.model();h=copy.deepcopy(h);window=box(108,155,122,168);p.WINDOW=window
    ct=L.stage.CT;gn='/LOGIC_GND';sb=L.p.NET;core=L.stage.caps.CORE
    desired=[('CT',ct,(118.1,160.0)),('GND-C61',gn,(119.9,158.4)),('GND-C62',gn,(118.4,161.85)),('GND-C63',gn,(111.25,162.575)),('SBC-C63',sb,(113.4,163.4))]
    newvias=[];checks=[]
    for label,net,at in desired:
        region=V.via_region(h,net,window)
        legal=region.covers(Point(at));candidate=at if legal else nearest_points(Point(at),region)[1].coords[0]
        if not legal:
            # Move inward slightly so exact polygon boundaries do not masquerade
            # as a robust ordinary drill site. Keep this search local and bounded.
            shrunk=region.buffer(-.03)
            if not shrunk.is_empty:candidate=nearest_points(Point(at),shrunk)[1].coords[0]
        record=via(label,net,candidate);newvias.append(record);h['vias'].append(record)
        checks.append({'label':label,'desired':at,'selected':candidate,'desired_passed':legal,'move_mm':math.dist(at,candidate),'ordinary_all_layer_legal_region_mm2':region.area,'exact_selected_site_in_region':region.covers(Point(candidate))})
        print('VIA',label,candidate,legal,flush=True)
    vv={r['uuid']:r for r in newvias};bylabel={label:(newvias[i]['x'],newvias[i]['y']) for i,(label,_,_) in enumerate(desired)}
    def pp(ref,num):r=pad(h,ref,num);return [r['x'],r['y']]
    proposed=[('CT-F',ct,'F.Cu',pp('U11012','1'),bylabel['CT'],.2),
              ('CT-B',ct,'B.Cu',bylabel['CT'],pp('C11061','1'),.2),
              ('GND-C61-B',gn,'B.Cu',pp('C11061','2'),bylabel['GND-C61'],.25),
              ('GND-C62-B',gn,'B.Cu',pp('C11062','2'),bylabel['GND-C62'],.25),
              ('GND-C63-B',gn,'B.Cu',pp('C11063','2'),bylabel['GND-C63'],.25),
              ('SBC-C63-B',sb,'B.Cu',pp('C11063','1'),bylabel['SBC-C63'],.4),
              ('CORE-C62-B',core,'B.Cu',pp('C11062','1'),(114.2,161.4),.4),
              ('GND-U12-F',gn,'F.Cu',pp('U11012','6'),(114.6,163.3),.4),
              ('GND-C15001-F',gn,'F.Cu',pp('C15001','2'),(114.6,163.3),.25),
              ('GND-C15002-F',gn,'F.Cu',pp('C15002','2'),(118.7,164.65),.25)]
    newtracks=[];routes=[]
    for label,net,layer,a,b,width in proposed:
        free=R.free_layer(h,net,layer,window,('/LOGIC_GND','/IO_3V3',core,sb),reference_guard=None,allow_own_via_connection=True)
        route=L.six.five.exact_path(free.buffer(-width/2),a,b,step=.05,node_cap=180000)
        rows=[]
        if route['verdict']=='HOST_PATH':
            for i,(aa,bb) in enumerate(zip(route['points'],route['points'][1:])):rows.append(track(label+'-'+str(i),net,layer,aa,bb,width))
            newtracks+=rows;h['tracks']+=rows
        routes.append({'label':label,'net_raw':N.raw(net),'layer':layer,'width_mm':width,'route':route,'new_track_uuids':[r['uuid'] for r in rows]})
        print('LOCAL',label,route['verdict'],route.get('length_mm'),flush=True)
    result={'exact_source_board_sha256':L.live.SHA,'ordinary_via_sites':checks,'new_vias':newvias,'new_tracks':newtracks,'route_results':routes,'all_routes_found':all(r['route']['verdict']=='HOST_PATH' for r in routes),'all_via_sites_passed':all(r['exact_selected_site_in_region'] for r in checks),'required_plane_repours':['local F/B LOGIC_GND','local IO_3V3','local CORE_5V and SBC_5V'],'IO3_all_original_contacts_required_after_local_carves':True,'mask_paste_aperture_model_not_native_qualified':True,'CORE_C62_stub_target_requires_bank_repacking':True,'source_connected_ground_return_native_refill_and_IR_open':True,'source_hashes':p.READS,'board_written':False,'native_jobs':0}
    (HERE/'local-copper-r2.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
