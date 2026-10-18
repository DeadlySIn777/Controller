"""Short F/B/F PG dive, freeing continuous F SBC output power geometry."""
import json,math,hashlib
from shapely.geometry import Point,box,LineString
from shapely.ops import nearest_points
import joint_model_r2 as J
import continuous_path_r2 as CP
L=J.L;p=J.p;R=J.R;V=J.V;C=J.C
REP=('/LOGIC_GND','/IO_3V3',L.stage.caps.CORE,p.NET)
def main():
    g,h,_=J.model(include_pg_dive=False);net='/motherboard_power_entry/SBC_SWITCH_PG';src=C.pad(h,'U11012','7');dst=C.pad(h,'R11049','2');aa=(src['x'],src['y']);bb=(dst['x'],dst['y']);window=box(108,156,124,172);p.WINDOW=window
    h={**h,'tracks':[t for t in h['tracks'] if p.norm(t['net'])!=net]}
    ff=R.free_layer(h,net,'F.Cu',window,REP,reference_guard=None,allow_own_via_connection=True);narrow=next(q for q in p.hubs.components(ff.buffer(-.0625)) if q.covers(Point(aa)));wideparts=p.hubs.components(ff.buffer(-.1));load=next(q for q in wideparts if q.covers(Point(bb)));ordinary=V.via_region(h,net,window).buffer(-.025)
    sr=ordinary.intersection(narrow);er=ordinary.intersection(load);found=None
    for layer in ('B.Cu','In3.Cu'):
        free=R.free_layer(h,net,layer,window,REP,reference_guard=None,allow_own_via_connection=True);parts=p.hubs.components(free.buffer(-.1));options=[]
        for q in parts:
            s=q.intersection(sr);e=q.intersection(er)
            if s.is_empty or e.is_empty:continue
            start=nearest_points(Point(aa),s)[1].coords[0];ends=e.difference(Point(start).buffer(.8))
            if ends.is_empty:continue
            end=nearest_points(Point(bb),ends)[1].coords[0];options.append((math.dist(aa,start)+math.dist(bb,end),q,start,end))
        print('PG_DIVE_OPTIONS',layer,len(options),flush=True)
        for _,q,start,end in sorted(options,key=lambda x:x[0]):
            wide=next((w for w in wideparts if w.covers(Point(start))),None)
            if wide is None:
                print('PG_DIVE_NO_WIDE_SOURCE',start,flush=True);continue
            landing=narrow.intersection(wide.buffer(-.025));join=nearest_points(Point(aa),landing)[1].coords[0];fine=CP.path(narrow,aa,join);sf=CP.path(wide,join,start);inner=CP.path(q,start,end);ef=CP.path(load,bb,end)
            print('PG_DIVE_TRIAL',layer,start,end,[x['verdict'] for x in (fine,sf,inner,ef)],fine.get('length_mm'),flush=True)
            if any(x['verdict']!='HOST_PATH' for x in (fine,sf,inner,ef)) or fine['length_mm']>2.8:continue
            found=(layer,start,end,fine,sf,inner,ef);break
        if found:break
    if not found:raise ValueError('No short-neck local PG dive')
    layer,start,end,fine,sf,inner,ef=found;ts=[]
    for label,lay,w,r in [('fine-neck','F.Cu',.125,fine),('source-F','F.Cu',.2,sf),('inner',layer,.2,inner),('load-F','F.Cu',.2,ef)]:
        ts += [C.track('PG-r5-'+label+'-'+str(i),net,lay,[round(x,6) for x in a],[round(x,6) for x in b],w) for i,(a,b) in enumerate(zip(r['points'],r['points'][1:])) if math.dist(a,b)>1e-8]
    vv=[C.via('PG-r5-source',net,[round(x,6) for x in start]),C.via('PG-r5-load',net,[round(x,6) for x in end])];neck=LineString([[round(x,6) for x in q] for q in fine['points']]).buffer(.09);nf=L.OUT/'U11012_LITERAL_PG_NECK-r5.wkb';nf.write_bytes(neck.wkb)
    rule='(rule "U11012 exact PG fine-pitch neck only" (layer "F.Cu")\n (condition "A.Type == \'Track\' && A.Width < 0.20mm && A.NetName == \'/motherboard_power_entry/SBC_SWITCH_PG\' && A.enclosedByArea(\'U11012_LITERAL_PG_NECK\')")\n (constraint track_width (min 0.125mm) (max 0.125mm))\n (constraint track_segment_length (max 1.2mm)))\n'
    result={'exact_board':L.live.SHA,'new_tracks':ts,'new_vias':vv,'fine_neck_length_mm':fine['length_mm'],'fine_neck_route':fine,'source_F_route':sf,'inner_layer':layer,'inner_route':inner,'load_F_route':ef,'named_area':{'name':'U11012_LITERAL_PG_NECK','geometry_file':str(nf.resolve()),'sha256':hashlib.sha256(nf.read_bytes()).hexdigest(),'bounds':neck.bounds},'native_effective_rule_proposal':rule,'whole_old_PG_F_route_superseded':True,'native_rule_body_ordinary_drill_contacts_gate_open':True,'maximum_layer_segments':3,'native_jobs':0,'board_written':False}
    (L.OUT/'PG-local-dive-r5.json').write_text(json.dumps(result,indent=2)+'\n');print('PG_DIVE',layer,fine['length_mm'],inner['length_mm'],start,end,flush=True)
if __name__=='__main__':main()
