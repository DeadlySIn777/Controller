"""Locate every actual attachment of the five preserved CORE feeders."""
import json,pickle,hashlib
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
L=I.L;p=I.p;Q=I.Q;NET=I.NET
OUT=L.OUT/'five-core-attachment-diagnostic-r34'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    model=L.OUT/'five-core-and-b5-checkpoint-r32/model.pkl';assert not OUT.exists();OUT.mkdir()
    g,h,binding,zones,candidate=pickle.loads(model.read_bytes());Q.NET=NET
    groups,parts,assign=Q.groups(candidate,return_details=True)
    ids={q['uuid']:i for i,rr in enumerate(groups) for q in rr};source=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=ids[source['uuid']]
    (OUT/'groups.pkl').write_bytes(pickle.dumps({'groups':groups,'parts':parts,'assign':assign},protocol=5))
    routes=[]
    for folder in ('core-inner-feed-r24-checkpoint-frozen-r25','core-inner-feed-r28'):
        receipt=json.loads((L.OUT/folder/'checkpoint.json').read_text());routes += [(folder,r) for r in receipt['rows']]
    rows=[]
    for folder,r in routes:
        v=next(q for q in h['vias'] if q['uuid']==r['via']['uuid']);layer=r['inner_layer']
        via_point=Point(v['x'],v['y']);ann=via_point.buffer(v['d']/2).difference(via_point.buffer(v['drill']/2))
        target=r['physical_contacts'];tp=[{'ref':q['ref'],'pin':q['pad'],'uuid':q['uuid'],'group':ids.get(q['uuid']),'source_connected':ids.get(q['uuid'])==root} for q in target if not q['ref'].startswith('@')]
        stubs=[next(q for q in h['tracks'] if q['uuid']==uid) for uid in r['new_track_uuids']]
        nearzones=[]
        for z in zones:
            if p.norm(z['net'])!=NET or z['layer']!=layer or z['shape'].intersection(ann).area<=0:continue
            hits=[{'part_index':i,'group':j,'intersection_area_mm2':part.intersection(z['shape']).area} for i,(part,j) in enumerate(zip(parts[layer],assign[layer])) if part.intersection(z['shape']).area>0]
            sourceparts=[part for part,j in zip(parts[layer],assign[layer]) if j==root];src=unary_union(sourceparts)
            nearzones.append({'uuid':z['uuid'],'label':z.get('label'),'annulus_intersection_mm2':ann.intersection(z['shape']).area,'shape_groups':hits,'distance_to_actual_root_layer_Cu_mm':z['shape'].distance(src),'actual_root_overlap_mm2':z['shape'].intersection(src).area,'native_outline_equals_physical':z.get('zone_outline_shape',z['shape']).equals(z['shape'])})
        endpoints=[]
        for name,xy in (('stub_start',r['stub_route']['points'][0]),('stub_end',r['stub_route']['points'][-1]),('inner_start',r['inner_route']['points'][0] if r.get('inner_route') else [v['x'],v['y']]),('inner_end',r['inner_route']['points'][-1] if r.get('inner_route') else [v['x'],v['y']])):
            ll=r['outer'] if name.startswith('stub') else layer;pt=Point(xy)
            endpoints.append({'name':name,'xy':xy,'layer':ll,'candidate_parts':[{'part':i,'group':j,'distance_mm':part.distance(pt),'contains_endpoint':part.covers(pt)} for i,(part,j) in enumerate(zip(parts[ll],assign[ll])) if part.distance(pt)<.5]})
        # Explicit old fill retreat at the actual target and source anchors.
        anchor=unary_union([Point(e['xy']).buffer(.5) for e in endpoints])
        affected=[]
        oldzones={q['uuid']:q for q in h['zones']}
        for z in candidate['zones']:
            if z['uuid'] not in oldzones:continue
            old=oldzones[z['uuid']]
            for ll,rs in old['fills'].items():
                original=unary_union(p.base.polygons(rs));new=unary_union(p.base.polygons(z['fills'].get(ll,[])))
                removed=original.difference(new).intersection(anchor)
                if removed.area>0:affected.append({'uuid':z['uuid'],'net_raw':z['net'],'layer':ll,'local_anchor_removed_area_mm2':removed.area})
        row={'origin':folder,'initial_target_group':r['group'],'via':v,'target_physical_pads':tp,
            'actual_via_layer_groups':{ll:ids.get(v['uuid']+'@'+ll) for ll in v['flashed']},
            'stub_actual_groups':[{'uuid':t['uuid'],'group':ids.get(t['uuid']),'a':t['a'],'b':t['b'],'width':t['w']} for t in stubs],
            'attached_proposed_inner_planes':nearzones,'endpoints':endpoints,'old_fill_retreats_at_anchors':affected,
            'all_target_pads_source_connected':all(q['source_connected'] for q in tp)}
        rows.append(row);(OUT/'checkpoint.json').write_text(json.dumps({'source_group':root,'rows':rows},indent=2)+'\n')
        print('FEED_ATTACHMENT',folder,r['group'],v['uuid'],'rooted',row['all_target_pads_source_connected'],'via',row['actual_via_layer_groups'],'planes',[(q['uuid'],q['distance_to_actual_root_layer_Cu_mm']) for q in nearzones],flush=True)
    receipt={'verdict':'EXACT_FIVE_CORE_ATTACHMENT_DIAGNOSTIC','model_sha256':sha(model),'source_group':root,'rows':rows,
        'remaining_named_groups':[{'group':i,'pads':[q for q in rr if not q['ref'].startswith('@')]} for i,rr in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rr)],
        'native_jobs':0,'board_written':False,'native_actual_flashes_and_fill_current_gates':'OPEN'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
