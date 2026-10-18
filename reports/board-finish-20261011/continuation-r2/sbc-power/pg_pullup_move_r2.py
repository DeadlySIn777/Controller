"""Targeted local PG pullup relocation with explicit IO3 restoration."""
import json,copy,math,hashlib,re
from shapely.geometry import Point,box,LineString
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from shapely.ops import nearest_points
from shapely import from_wkb
from shapely.prepared import prep
import local_copper_r3 as T
import continuous_path_r2 as CP
L=T.L;p=T.p;R=T.R;C=T.T
REP=('/LOGIC_GND','/IO_3V3',L.stage.caps.CORE,p.NET)
def records(shape):return [[list(q.exterior.coords),[list(x.coords) for x in q.interiors]] for q in p.hubs.components(shape)]
def move(h,at,angle):
    h={**h,'pads':[copy.deepcopy(q) if q['ref']=='R11049' else q for q in h['pads']], 'footprints':[copy.deepcopy(q) if q['ref']=='R11049' else q for q in h['footprints']]};old=(217.162,51.25)
    def tx(sh):return translate(rotate(sh,90-angle,origin=old),at[0]-old[0],at[1]-old[1])
    for pad in h['pads']:
        if pad['ref']=='R11049':
            q=tx(Point(pad['x'],pad['y']));pad['x'],pad['y']=q.x,q.y;pad['layers']={l:[r for sh in p.base.polygons(rs) for r in records(tx(sh))] for l,rs in pad['layers'].items()}
    for f in h['footprints']:
        if f['ref']=='R11049':f['courtyard']={l:[r for sh in p.base.polygons(rs) for r in records(tx(sh))] for l,rs in f['courtyard'].items()};f['x'],f['y']=at
    return h
def main():
    g,h,tail=T.model();native=tail[1];en=json.loads((L.OUT/'switch-control-coplan-r5.json').read_text());h={**h,'vias':h['vias']+en['new_vias'],'tracks':h['tracks']+en['new_tracks']};window=box(107,153,133,173);p.WINDOW=window;pg=C.pad(h,'U11012','7');at=(pg['x'],pg['y']);net=pg['net'];free=R.free_layer(h,net,'F.Cu',window,REP,reference_guard=None,allow_own_via_connection=True);part=next(q for q in p.hubs.components(free.buffer(-.0625)) if q.covers(Point(at)));freeio=R.free_layer(h,'/IO_3V3','F.Cu',window,REP,reference_guard=None,allow_own_via_connection=True)
    bodies=unary_union([sh for f in h['footprints'] if f['ref']!='R11049' and f.get('side')=='F' for l,rs in f['courtyard'].items() for sh in p.base.polygons(rs) if sh.intersects(window)]);pb=prep(bodies);pp=prep(part);pi=prep(freeio);origpads=[q for q in h['pads'] if q['ref']=='R11049'];of=next(f for f in h['footprints'] if f['ref']=='R11049');oc=unary_union([sh for rs in of['courtyard'].values() for sh in p.base.polygons(rs)]);old=(217.162,51.25);sites=[]
    for angle in (0,90,-90,180):
        cp=rotate(oc,90-angle,origin=old);pads=[rotate(L.body_pad(q),90-angle,origin=old) for q in origpads]
        for ix in range(1080,1321,2):
            for iy in range(1540,1721,2):
                pos=(ix/10,iy/10);dx,dy=pos[0]-old[0],pos[1]-old[1];court=translate(cp,dx,dy)
                if pb.intersects(court):continue
                io,pgo=[translate(q,dx,dy) for q in pads]
                if not pp.covers(pgo) or not pi.covers(io):continue
                sites.append((math.dist(at,pgo.centroid.coords[0]),pos,angle))
    sites.sort();print('PG_LOCAL_POSES',len(sites),flush=True);chosen=None
    core=from_wkb((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').read_bytes());sbc=from_wkb((L.OUT/'SBC-F-bounded-bus-r4.wkb').read_bytes())
    io3=unary_union([q for z in h['zones'] if p.norm(z['net'])=='/IO_3V3' for q in p.base.polygons(z['fills'].get('In2.Cu',[]))]).difference(core.buffer(.175))
    fingers=json.loads((L.OUT/'IO3-restoration-fingers-r4.json').read_text());io3=io3.union(unary_union([from_wkb(__import__('pathlib').Path(r['geometry_file']).read_bytes()) for r in fingers.get('fingers',[]) if 'geometry_file' in r]))
    rootio=max(p.hubs.components(io3),key=lambda q:q.area);ordinary=T.V.via_region(h,'/IO_3V3',window).difference(core.buffer(.475)).difference(sbc.buffer(.475)).intersection(rootio.buffer(-.3))
    for _,pos,angle in sites[:80]:
        hh=move(h,pos,angle);q=C.pad(hh,'R11049','2');a=(q['x'],q['y']);pgfree=free.difference(L.body_pad(C.pad(hh,'R11049','1')).buffer(.175))
        pcs=[q for q in p.hubs.components(pgfree.buffer(-.0625)) if q.covers(Point(at)) and q.covers(Point(a))]
        if not pcs:continue
        q=C.pad(hh,'R11049','1');ioat=(q['x'],q['y']);iofree=freeio.difference(L.body_pad(C.pad(hh,'R11049','2')).buffer(.175));ios=[x for x in p.hubs.components(iofree.buffer(-.1)) if x.covers(Point(ioat))]
        if not ios:continue
        iv=[v for v in hh['vias'] if p.norm(v['net'])=='/IO_3V3' and 'F.Cu' in v['flashed'] and ios[0].covers(Point(v['x'],v['y']))];iv.sort(key=lambda v:math.dist(ioat,(v['x'],v['y'])))
        if iv:v=iv[0];added=[]
        else:
            landing=ordinary.difference(L.body_pad(C.pad(hh,'R11049','1')).buffer(.425)).difference(L.body_pad(C.pad(hh,'R11049','2')).buffer(.475)).intersection(ios[0]).buffer(-.025)
            if landing.is_empty:continue
            loc=nearest_points(Point(ioat),landing)[1].coords[0];v=C.via('PG-pullup-r3-IO3','/IO_3V3',loc);added=[v]
        ir=CP.path(ios[0],ioat,(v['x'],v['y']),node_cap=100000)
        if ir['verdict']!='HOST_PATH':continue
        pr=CP.path(pcs[0],at,a,node_cap=100000)
        if pr['verdict']!='HOST_PATH':continue
        chosen=(hh,pos,angle,pr,ir,v,added);break
    if not chosen:
        (L.OUT/'PG-pullup-local-move-r2.json').write_text(json.dumps({'exact_board':L.live.SHA,'verdict':'NO_COMPLETE_LOCAL_POSE','legal_pose_count':len(sites)},indent=2)+'\n');return
    hh,pos,angle,pr,ir,v,added=chosen;ts=[]
    for label,net,w,r in [('PG',pg['net'],.125,pr),('IO3','/IO_3V3',.2,ir)]:ts += [C.track('PG-pullup-r2-'+label+'-'+str(i),net,'F.Cu',a,b,w) for i,(a,b) in enumerate(zip(r['points'],r['points'][1:])) if math.dist(a,b)>1e-8]
    ch=next(ch for ch in native.values() if p.base.pcbtext.chunk_kind(ch)=='footprint' and p.base.ref_of(ch)=='R11049')
    result={'exact_board':L.live.SHA,'verdict':'HOST_COMPLETE_PG_PULLUP_MOVE','R11049_target_pose':[pos[0],pos[1],angle],'original_native_chunk_sha256':hashlib.sha256(ch).hexdigest(),'pin_nets_unchanged':True,'moved_pad_positions':[{k:q[k] for k in ('uuid','num','x','y','net')} for q in hh['pads'] if q['ref']=='R11049'],'new_tracks':ts,'new_vias':added,'PG_F_route':pr,'IO3_F_route':ir,'IO3_endpoint_via':v,'new_IO3_endpoint_on_main_remaining_In2_fill':bool(added),'old_IO3_pad_stub_retained_exactly':'c6f8fe58-9a46-46d1-84b6-cf44d37b8b85','old_padnet_group_and_ordinary_aperture_native_guards_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'PG-pullup-local-move-r3.json').write_text(json.dumps(result,indent=2)+'\n');print('PG_LOCAL_FOUND',pos,angle,pr['length_mm'],ir['length_mm'],flush=True)
if __name__=='__main__':main()
