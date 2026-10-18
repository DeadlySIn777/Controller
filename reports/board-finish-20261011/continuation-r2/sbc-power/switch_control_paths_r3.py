"""Source-bound EN/PG paths, ordinary vias and one inner-layer dive."""
import json,copy,hashlib,math
from shapely.geometry import Point,box,LineString
from shapely.ops import nearest_points
import local_copper_r3 as T
L=T.L;p=T.p;R=T.R;V=T.V;C=T.T

def model():
    g,h,tail=T.model();receipt=json.loads((L.OUT/'switch-control-paths-r3.json').read_text())
    return g,{**h,'tracks':h['tracks']+receipt['new_tracks'],'vias':h['vias']+receipt['new_vias']},tail

def main():
    g,h,tail=T.model();h=copy.deepcopy(h)
    escaped=json.loads((L.OUT/'switch-signal-escapes-r2.json').read_text());newvias=[];newtracks=[];rows=[]
    for row in escaped['rows']:
        q=row['via_escape'][0];net=row['net_raw'];v=C.via('switch-'+row['pin'],net,q['site']);newvias.append(v);h['vias'].append(v)
        ts=[C.track('switch-'+row['pin']+'-F-'+str(i),net,'F.Cu',a,b,q['width_mm']) for i,(a,b) in enumerate(zip(q['route']['points'],q['route']['points'][1:])) if math.dist(a,b)>1e-8]
        newtracks+=ts;h['tracks']+=ts
    for num in ('7','5'):
        row=next(x for x in escaped['rows'] if x['pin']==num);net=row['net_raw'];start=row['via_escape'][0]['site']
        if num=='7':
            target=C.pad(h,'R11049','2');at=(target['x'],target['y']);window=box(at[0]-4,at[1]-4,at[0]+4,at[1]+4)
            p.WINDOW=window;region=V.via_region(h,net,window);free=R.free_layer(h,net,'F.Cu',window,('/LOGIC_GND',),reference_guard=None,allow_own_via_connection=True);choices=[]
            for part in p.hubs.components(free.buffer(-.1)):
                if not part.covers(Point(at)):continue
                landing=part.intersection(region.buffer(-.025))
                if landing.is_empty:continue
                site=nearest_points(Point(at),landing)[1].coords[0];route=L.six.five.exact_path(part,at,site,step=.1,node_cap=20000)
                if route['verdict']=='HOST_PATH':choices.append((site,route));break
            if not choices:raise ValueError('PG load ordinary-via escape unavailable')
            end,escape=choices[0];v=C.via('switch-7-load',net,end);newvias.append(v);h['vias'].append(v)
            ts=[C.track('switch-7-load-F-'+str(i),net,'F.Cu',a,b,.2) for i,(a,b) in enumerate(zip(escape['points'],escape['points'][1:])) if math.dist(a,b)>1e-8]
            newtracks+=ts;h['tracks']+=ts
            print('PG_LOAD_ESCAPE',end,escape['length_mm'],flush=True)
        else:
            old=next(v for v in g['vias'] if v['uuid']=='11d97f37-875d-4fad-85ab-b6cb3e1baa02');end=(old['x'],old['y']);escape=None
        window=box(min(start[0],end[0])-10,min(start[1],end[1])-10,max(start[0],end[0])+10,max(start[1],end[1])+10);p.WINDOW=window
        free=R.free_layer(h,net,'In3.Cu',window,('/LOGIC_GND',),reference_guard=.025,allow_own_via_connection=True)
        w=.2;centre=free.buffer(-w/2);common=[part for part in p.hubs.components(centre) if part.covers(Point(start)) and part.covers(Point(end))]
        print('CONTROL_IN3_COMPONENT',num,len(common),flush=True)
        route=L.six.five.exact_path(common[0],start,end,step=.25,node_cap=700000) if common else {'verdict':'NO_SHARED_COMPONENT'}
        ts=[]
        if route['verdict']=='HOST_PATH':
            ts=[C.track('switch-'+num+'-In3-'+str(i),net,'In3.Cu',a,b,w) for i,(a,b) in enumerate(zip(route['points'],route['points'][1:])) if math.dist(a,b)>1e-8];newtracks+=ts;h['tracks']+=ts
        rows.append({'pin':num,'net_raw':net,'start':start,'end':end,'layer':'In3.Cu','width_mm':w,'route':route,'load_F_escape':escape,'new_inner_track_uuids':[t['uuid'] for t in ts],'preserve_all_original_same_net_items':True})
        print('CONTROL_PATH',num,route['verdict'],route.get('length_mm'),flush=True)
    result={'exact_board':L.live.SHA,'new_vias':newvias,'new_tracks':newtracks,'routes':rows,'all_remote_paths_found':all(r['route']['verdict']=='HOST_PATH' for r in rows),'source_escape_sha256':hashlib.sha256((L.OUT/'switch-signal-escapes-r2.json').read_bytes()).hexdigest(),'original_same_net_items_removed':[],'maximum_layer_segments':3,'native_full_contact_guard_and_return_qualification_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'switch-control-paths-r3.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
