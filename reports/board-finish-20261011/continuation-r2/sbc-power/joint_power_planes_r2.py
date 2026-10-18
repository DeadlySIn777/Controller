"""Coupled complete support/control and F SBC, CORE bank/feed geometry."""
import json,hashlib,math
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import joint_model_r2 as J
import continuous_path_r2 as CP
L=J.L;p=J.p;R=J.R;V=J.V;C=J.C
def write(name,shape):
    shape=set_precision(shape,1e-6);file=L.OUT/name;file.write_bytes(shape.wkb);return {'geometry_file':str(file.resolve()),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'area_mm2':shape.area},shape
def main():
    g,h,tail=J.model();scope,native,prior,omit=tail;window=box(108,156,124,172);p.WINDOW=window;core=J.L.stage.caps.CORE
    sf=R.free_layer(h,p.NET,'F.Cu',window,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True);sp=J.C.pad(h,'U11012','8');sat=(sp['x'],sp['y']);centres=[q for q in p.hubs.components(sf.buffer(-.08)) if q.covers(Point(sat))];assert centres
    centre=centres[0];targets=[]
    for q in h['pads']:
        if q['ref'] in ('U11012','C15001','C15002','J15001') and p.norm(q['net'])==p.norm(p.NET):targets.append({'kind':'pad','uuid':q['uuid'],'ref':q['ref'],'pad':q['num'],'at':(q['x'],q['y'])})
    for v in h['vias']:
        if p.norm(v['net'])==p.norm(p.NET) and window.covers(Point(v['x'],v['y'])):targets.append({'kind':'via','uuid':v['uuid'],'at':(v['x'],v['y'])})
    for t in h['tracks']:
        if p.norm(t['net'])!=p.norm(p.NET) or t['layer']!='F.Cu':continue
        touch=p.base.body(t).intersection(centre)
        if not touch.is_empty:targets.append({'kind':'retained_track','uuid':t['uuid'],'at':touch.representative_point().coords[0]})
    lines=[];routes=[]
    for q in targets:
        route=CP.path(centre,sat,q['at'],node_cap=100000);routes.append({**q,'route':route})
        if route['verdict']=='HOST_PATH':lines.append(LineString(route['points']).buffer(.9))
    print('JOINT_SBC_ROUTES',len(routes),sum(q['route']['verdict']=='HOST_PATH' for q in routes),flush=True)
    sb=unary_union(lines).intersection(sf);sb=next(q for q in p.hubs.components(sb) if q.covers(Point(sat)));sbr,sb=write('SBC-F-joint-bus-r2.wkb',sb)
    plane=from_wkb((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').read_bytes())
    loadwindow=box(108,154,124,166);p.WINDOW=loadwindow
    lf=R.free_layer(h,core,'F.Cu',loadwindow,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True).difference(sb.buffer(.175));lp=C.pad(h,'U11012','3');lpart=next(q for q in p.hubs.components(lf) if q.covers(Point(lp['x'],lp['y'])))
    region=V.via_region(h,core,loadwindow).intersection(plane.buffer(-.3)).difference(sb.buffer(.475)).intersection(lpart.buffer(-.3));required=(114.2,161.4);chosen=[]
    if region.covers(Point(required)):chosen=[required];region=region.difference(Point(required).buffer(.8))
    chosen+=sorted(p.hubs.pack_region(region,(116,161.4),spacing=.8),key=lambda q:math.dist(q,(116,161.4)))[:16-len(chosen)]
    source=json.loads((L.OUT/'CORE-In2-variable-plane-r2.json').read_text())['ordinary_via_banks'][0]
    banks=[source,{'name':'load','sites':[{'at':[round(x,6) for x in q],'diameter_mm':.6,'drill_mm':.3,'maximum_planning_A':.5} for q in chosen],'required_total_current_A':4.396304643962849,'equal_share_claimed':False}]
    newv=[]
    for bank in banks:
        for i,v in enumerate(bank['sites']):
            v['at']=[round(x,6) for x in v['at']];newv.append(C.via('joint-CORE-bank-'+bank['name']+'-'+str(i),core,v['at']))
    h={**h,'vias':h['vias']+newv};print('JOINT_CORE_BANKS',len(source['sites']),len(chosen),required in chosen,flush=True)
    fanouts=[]
    for bank,fw,refs in [(banks[0],box(209,97,262,130),[('R11022','2'),('C11088','1'),('C11027','1'),('C11028','1'),('C11029','1'),('C11094','1')]),(banks[1],loadwindow,[('U11012','3'),('U11012','4'),('U11012','11')])]:
        p.WINDOW=fw;free=R.free_layer(h,core,'F.Cu',fw,('/LOGIC_GND','/IO_3V3'),reference_guard=None,allow_own_via_connection=True)
        if bank['name']=='load':free=free.difference(sb.buffer(.175))
        sourcepad=C.pad(h,*refs[0]);at=(sourcepad['x'],sourcepad['y']);parts=[q for q in p.hubs.components(free) if q.covers(Point(at))]
        assert parts,bank['name'];part=parts[0];targets=[{'kind':'pad','ref':ref,'pad':n,'at':[C.pad(h,ref,n)['x'],C.pad(h,ref,n)['y']]} for ref,n in refs]+[{'kind':'bank','at':v['at']} for v in bank['sites']];rr=[];shapes=[]
        for q in targets:
            if not part.covers(Point(q['at'])):route={'verdict':'DIFFERENT_F_COMPONENT'}
            else:route=CP.path(part,at,q['at'],node_cap=200000)
            rr.append({**q,'route':route})
            if route['verdict']=='HOST_PATH':shapes.append(LineString(route['points']).buffer(3. if bank['name']=='source' else 1.5))
        bus=unary_union(shapes).intersection(part);fr,bus=write('CORE-'+bank['name']+'-joint-F-r2.wkb',bus);fanouts.append({'name':bank['name'],**fr,'routes':rr,'all_targets_joined':all(q['route']['verdict']=='HOST_PATH' for q in rr)});print('JOINT_CORE_F',bank['name'],fanouts[-1]['all_targets_joined'],bus.area,flush=True)
    result={'exact_board':L.live.SHA,'native_coordinate_grid_nm':1,'SBC_F_bus':sbr,'SBC_F_routes':routes,'CORE_In2_plane_file':str((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').resolve()),'CORE_In2_plane_sha256':hashlib.sha256((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').read_bytes()).hexdigest(),'CORE_banks':banks,'new_CORE_bank_vias':newv,'CORE_F_fanouts':fanouts,'required_B_C11062_bank_site_present':required in chosen,'all_geometric_targets_host_joined':all(q['route']['verdict']=='HOST_PATH' for q in routes) and len(chosen)==16 and all(q['all_targets_joined'] for q in fanouts),'normal_CORE_A':7.882034293398381,'common_SBC_A':4.396304643962849,'every_displaced_plane_contact_and_native_current_return_guard_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'joint-power-planes-r3.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
