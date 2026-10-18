"""Co-select ordinary F escape vias from a shared physical inner corridor."""
import json,copy,math,hashlib
from shapely import from_wkb
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union,nearest_points
import local_copper_r3 as T
import continuous_path_r2 as CP
L=T.L;p=T.p;R=T.R;V=T.V;C=T.T
REPOUR=('/LOGIC_GND','/IO_3V3',L.stage.caps.CORE,p.NET)
def main():
    g,h,tail=T.model();scope,native,prior,omit=tail;h=copy.deepcopy(h);newvias=[];newtracks=[];rows=[]
    for num in ('7','5'):
        pad=C.pad(h,'U11012',num);net=pad['net'];at=(pad['x'],pad['y']);sw=box(109,156,124,169);p.WINDOW=sw
        sf=R.free_layer(h,net,'F.Cu',sw,REPOUR,reference_guard=None,allow_own_via_connection=True);width=.125 if num=='7' else .2
        sc=next(q for q in p.hubs.components(sf.buffer(-width/2)) if q.covers(Point(at)));sr=V.via_region(h,net,sw).buffer(-.025).intersection(sc)
        if num=='7':
            target=C.pad(h,'R11049','2');endat=(target['x'],target['y']);ew=box(193,42,230,66);p.WINDOW=ew
            ef=R.free_layer(h,net,'F.Cu',ew,REPOUR,reference_guard=None,allow_own_via_connection=True);ec=next(q for q in p.hubs.components(ef.buffer(-.1)) if q.covers(Point(endat)));er=V.via_region(h,net,ew).buffer(-.025).intersection(ec)
        else:
            oldvias=[v for v in g['vias'] if p.norm(v['net'])==p.norm(net) and 'In3.Cu' in v['flashed']];endat=None;er=None
        found=None
        for layer in ('In3.Cu','In2.Cu','B.Cu'):
            window=box(103,38,271,221);p.WINDOW=window
            free=R.free_layer(h,net,layer,window,REPOUR,reference_guard=None,allow_own_via_connection=True)
            if layer=='In2.Cu':free=free.difference(from_wkb((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').read_bytes()).buffer(.175))
            parts=sorted(p.hubs.components(free.buffer(-.1)),key=lambda q:q.area,reverse=True);options=[]
            for part in parts:
                ss=part.intersection(sr)
                if ss.is_empty:continue
                if num=='7':
                    ee=part.intersection(er)
                    if ee.is_empty:continue
                    end=nearest_points(Point(endat),ee)[1].coords[0];oldid=None
                else:
                    ends=[v for v in oldvias if layer in v['flashed'] and part.covers(Point(v['x'],v['y']))]
                    if not ends:continue
                    vv=min(ends,key=lambda v:math.dist(at,(v['x'],v['y'])));end=(vv['x'],vv['y']);oldid=vv['uuid']
                start=nearest_points(Point(at),ss)[1].coords[0];options.append((math.dist(at,start)+(math.dist(endat,end) if endat else 0)+math.dist(start,end),part,start,end,oldid))
            print('COPLAN_OPTIONS',num,layer,len(options),flush=True)
            for _,part,start,end,oldid in sorted(options,key=lambda x:x[0]):
                route=CP.path(part,start,end,node_cap=700000)
                if route['verdict']=='HOST_PATH':found=(layer,start,end,oldid,route);break
            if found:break
        if not found:
            rows.append({'pin':num,'verdict':'NO_COPLANNED_PATH'});continue
        layer,start,end,oldid,inner=found;sv=C.via('switch-r4-'+num+'-source',net,start);newvias.append(sv);h['vias'].append(sv)
        src=L.six.five.exact_path(sc,at,start,step=.05,node_cap=100000);endroute=None
        if num=='7':
            ev=C.via('switch-r4-'+num+'-load',net,end);newvias.append(ev);h['vias'].append(ev);endroute=L.six.five.exact_path(ec,endat,end,step=.1,node_cap=100000)
        routes=[('source-F','F.Cu',width,src),('inner',layer,.2,inner)]+([('load-F','F.Cu',.2,endroute)] if endroute else [])
        for label,lay,w,r in routes:
            if r['verdict']!='HOST_PATH':raise ValueError('Expected endpoint route '+label)
            ts=[C.track('switch-r4-'+num+'-'+label+'-'+str(i),net,lay,a,b,w) for i,(a,b) in enumerate(zip(r['points'],r['points'][1:])) if math.dist(a,b)>1e-8];newtracks+=ts;h['tracks']+=ts
        body=LineString(inner['points']).buffer(.1);ledger=[]
        for z in g['zones']:
            if p.norm(z['net'])==p.norm(net):continue
            fills=unary_union(p.base.polygons(z['fills'].get(layer,[])));cut=fills.intersection(body.buffer(.175))
            if not cut.is_empty:ledger.append({'uuid':z['uuid'],'net_raw':z['net'],'layer':layer,'old_native_chunk_sha256':hashlib.sha256(native[z['uuid']]).hexdigest(),'cut_area_mm2':cut.area,'every_original_pad_plane_track_and_via_contact_required':True})
        rows.append({'pin':num,'verdict':'HOST_PATH','net_raw':net,'inner_layer':layer,'start':start,'end':end,'existing_endpoint_via_uuid':oldid,'routes':[{'label':label,'layer':lay,'width':w,'route':r} for label,lay,w,r in routes],'affected_zone_contact_obligations':ledger})
        print('COPLAN_PATH',num,layer,inner['length_mm'],flush=True)
    result={'exact_board':L.live.SHA,'new_vias':newvias,'new_tracks':newtracks,'rows':rows,'all_remote_paths_found':all(r['verdict']=='HOST_PATH' for r in rows),'reference_trace_return_coverage_and_original_plane_contact_gates_open':True,'no_SMD_or_drill_waiver':True,'native_jobs':0,'board_written':False}
    (L.OUT/'switch-control-coplan-r5.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
