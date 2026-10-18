"""Bounded direct >=.20 joins for two bare CORE1V2 pads; no source credit."""
import json,pickle,hashlib,math,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import core_inner_feed_r18 as I
L=G.L;p=G.p;C=I.C;O=L.OUT/'core1v2-local-outer-join-nominees-r106'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir();mp=L.OUT/'unused-new-core-fragment-removal-r91/model.pkl';assert sha(mp)=='1bb0d52095c4f2ad003d0c5934d8e7fca7174c8936af19ae0bbed66021003e09';g,h,b,z,c=pickle.loads(mp.read_bytes());raw=next(q['net'] for q in h['pads'] if (q['ref'],q['num'])==('L2001','2'));attempts=[];accepted=[]
    for target_ref,target_pin,preferred in [('U1001','J7',[('U1001','J6'),('U1001','K9'),('U1001','F9')]),('C1024','1',[('C1001','1')])]:
        pad=next(q for q in h['pads'] if (q['ref'],q['num'])==(target_ref,target_pin));body=unary_union(p.base.polygons(pad['layers']['F.Cu']));assert pad['net']==raw
        answer=None
        goals=[]
        for ref,pin in preferred:
            goal=next(q for q in h['pads'] if (q['ref'],q['num'])==(ref,pin));assert goal['net']==raw
            if 'F.Cu' in goal['layers']:goals.append((ref,pin,unary_union(p.base.polygons(goal['layers']['F.Cu']))))
        for via in h['vias']:
            if via['net']==raw and 'F.Cu' in via['flashed'] and Point(via['x'],via['y']).distance(body)<15:
                gshape=Point(via['x'],via['y']).buffer(via['d']/2).difference(Point(via['x'],via['y']).buffer(via['drill']/2));goals.append(('@VIA',via['uuid'],gshape))
        goals.sort(key=lambda q:q[2].distance(body))
        for ref,pin,gshape in goals:
            a,bp=nearest_points(body.buffer(-.03),gshape.buffer(-.03));coords=[list(map(lambda x:round(x,6),s)) for s in (a.coords[0],bp.coords[0])]
            if (target_ref,target_pin,ref,pin)==('U1001','J7','U1001','J6'):coords=[[160.02,89.947],[159.36,89.947]]
            elif (target_ref,target_pin,ref,pin)==('C1024','1','C1001','1'):coords=[[158.19,80.3],[161.69,80.3],[161.69,81.127]]
            else:continue
            assert body.covers(Point(coords[0])) and gshape.covers(Point(coords[-1]))
            line=LineString(coords);errors=[];region=line.buffer(2)
            for q in h['pads']:
                if q['net']==raw:continue
                if abs(q['x']-pad['x'])>50 or abs(q['y']-pad['y'])>50:continue
                for sh in p.base.polygons(q['layers'].get('F.Cu',[])):
                    required=G.gap(h,raw,q['net'])+.025;dist=line.distance(sh)-.1
                    if dist<required:errors.append({'kind':'pad','uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'gap_mm':dist,'required_mm':required})
            for q in h['tracks']:
                if q['layer']!='F.Cu' or q['net']==raw:continue
                if max(q['a'][0],q['b'][0])+q['w']/2+1<region.bounds[0] or min(q['a'][0],q['b'][0])-q['w']/2-1>region.bounds[2] or max(q['a'][1],q['b'][1])+q['w']/2+1<region.bounds[1] or min(q['a'][1],q['b'][1])-q['w']/2-1>region.bounds[3]:continue
                dist=line.distance(LineString([q['a'],q['b']]))-.1-q['w']/2;req=G.gap(h,raw,q['net'])+.025
                if dist<req:errors.append({'kind':'track','uuid':q['uuid'],'gap_mm':dist,'required_mm':req})
            for q in h['vias']:
                if q['net']==raw:continue
                dist=line.distance(Point(q['x'],q['y']))-.1-q['d']/2;req=G.gap(h,raw,q['net'])+.025
                if dist<req:errors.append({'kind':'via','uuid':q['uuid'],'gap_mm':dist,'required_mm':req})
            for q in z:
                if q['layer']!='F.Cu' or q['net']==raw:continue
                dist=line.distance(q['shape'])-.1;req=max(G.gap(h,raw,q['net']),float(q.get('clearance_mm',.15)))+.025
                if dist<req:errors.append({'kind':'owned_zone','uuid':q['uuid'],'gap_mm':dist,'required_mm':req})
            record={'target':[target_ref,target_pin],'goal':[ref,pin],'points_mm':coords,'width_mm':.2,'length_mm':line.length,'errors':errors};attempts.append(record)
            if errors:continue
            ts=[C.track('CORE1V2-bent-local-r106-'+target_ref+'-'+target_pin+'-'+str(j),raw,'F.Cu',aa,bb,.20) for j,(aa,bb) in enumerate(zip(coords,coords[1:]))];accepted+=ts;answer=ts;break
        print('CORE1V2_LOCAL_DIRECT_NOMINEE',target_ref,target_pin,bool(answer),[(r['goal'],len(r['errors']),r['errors'][:2]) for r in attempts if r['target']==[target_ref,target_pin]],flush=True)
    f=O/'proposed-tracks.pkl';f.write_bytes(pickle.dumps(accepted,protocol=5));(O/'receipt.json').write_text(json.dumps({'verdict':'LOCAL_GEOMETRY_NOMINEES_ONLY_FULL_CONTACT_REFERENCE_RULE_CURRENT_NATIVE_GATES_OPEN','parent_model_sha256':sha(mp),'actual_raw_net':raw,'tracks_sha256':sha(f),'tracks':accepted,'attempts':attempts,'new_vias':0,'native_jobs':0,'board_written':False,'source_credit':False,'all_unscanned_distant_pad_graphics_reserved_rules_and_native_actual_contacts':'OPEN'},indent=2)+'\n')
if __name__=='__main__':main()
