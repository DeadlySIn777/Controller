"""C63 B-side support placement beside the new F output/CM feed."""
import json,copy,math,hashlib
from shapely import from_wkb
from shapely.geometry import Point,box
from shapely.ops import nearest_points
from shapely.affinity import rotate,translate
import local_copper_r2 as T
L=T.L;p=T.p;R=T.R;V=T.V
def move_c63(h):
    old=(112.975,162.375);new=(115.75,165.325)
    def tx(poly):return translate(rotate(poly,-90,origin=old),new[0]-old[0],new[1]-old[1])
    def records(poly):return [[list(x.exterior.coords),[list(q.coords) for q in x.interiors]] for x in p.hubs.components(poly)]
    h=copy.deepcopy(h)
    for pad in h['pads']:
        if pad['ref']=='C11063':
            pt=tx(Point(pad['x'],pad['y']));pad['x'],pad['y']=pt.x,pt.y
            pad['layers']={layer:[row for poly in p.base.polygons(rows) for row in records(tx(poly))] for layer,rows in pad['layers'].items()}
    for foot in h['footprints']:
        if foot['ref']=='C11063':foot['courtyard']={layer:[row for poly in p.base.polygons(rows) for row in records(tx(poly))] for layer,rows in foot['courtyard'].items()}
    return h
def model():
    g,h,*tail=R.model();h=move_c63(h);old=json.loads((L.OUT/'local-copper-r2.json').read_text());drop={'GND-C63','SBC-C63'}
    vias=[v for v in old['new_vias'] if v['uuid'] not in {T.uid(label) for label in drop}]
    drops={u for row in old['route_results'] if row['label'] in {'GND-C63-B','SBC-C63-B'} for u in row['new_track_uuids']}
    tracks=[t for t in old['new_tracks'] if t['uuid'] not in drops]
    new=json.loads((L.OUT/'local-copper-r3.json').read_text())
    return g,{**h,'vias':h['vias']+vias+new['new_vias'],'tracks':h['tracks']+tracks+new['new_tracks']},tail
def main():
    g,h,*_=R.model();h=move_c63(h);old=json.loads((L.OUT/'local-copper-r2.json').read_text());drop={'GND-C63','SBC-C63'}
    h['vias'] += [v for v in old['new_vias'] if v['uuid'] not in {T.uid(label) for label in drop}]
    drops={u for row in old['route_results'] if row['label'] in {'GND-C63-B','SBC-C63-B'} for u in row['new_track_uuids']};h['tracks'] += [t for t in old['new_tracks'] if t['uuid'] not in drops]
    p.WINDOW=box(110,162,121,170);newvias=[];newtracks=[];checks=[];routes=[]
    for label,net,at,ref,padnum,w in [('GND-C63-r3','/LOGIC_GND',(116.8,166.15),'C11063','2',.25),('SBC-C63-r3',p.NET,(114.8,164.6),'C11063','1',.4)]:
        region=V.via_region(h,net,p.WINDOW);selected=at if region.covers(Point(at)) else nearest_points(Point(at),region.buffer(-.03))[1].coords[0]
        v=T.via(label,net,selected);newvias.append(v);h['vias'].append(v);pp=T.pad(h,ref,padnum)
        free=R.free_layer(h,net,'B.Cu',p.WINDOW,('/LOGIC_GND','/IO_3V3',L.stage.caps.CORE,p.NET),reference_guard=None,allow_own_via_connection=True)
        route=L.six.five.exact_path(free.buffer(-w/2),[pp['x'],pp['y']],selected,step=.05,node_cap=12000);rows=[]
        if route['verdict']=='HOST_PATH':
            rows=[T.track(label+'-'+str(i),net,'B.Cu',a,b,w) for i,(a,b) in enumerate(zip(route['points'],route['points'][1:]))];newtracks+=rows;h['tracks']+=rows
        checks.append({'label':label,'desired':at,'selected':selected,'ordinary_region_pass':region.covers(Point(selected))});routes.append({'label':label,'route':route,'width':w})
        print(label,selected,route['verdict'],route.get('length_mm'),flush=True)
    result={'exact_board':L.live.SHA,'C11063_new_native_pose':[115.75,165.325,-90.],'C11063_new_pad_positions':[{k:r[k] for k in ('num','x','y','net')} for r in h['pads'] if r['ref']=='C11063'],'superseded_r2_local_via_uuids':[T.uid(label) for label in drop],'superseded_r2_local_track_uuids':sorted(drops),'new_vias':newvias,'new_tracks':newtracks,'ordinary_site_checks':checks,'routes':routes,'source_r2_sha256':hashlib.sha256((L.OUT/'local-copper-r2.json').read_bytes()).hexdigest(),'native_body_DRC_return_and_all_contact_gates_open':True,'board_written':False,'native_jobs':0}
    (L.OUT/'local-copper-r3.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
