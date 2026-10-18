"""3D IO_3V3 terminal partition comparison around the explicit CORE In2 lane."""
import json,hashlib,time
from shapely import from_wkb,set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
import fresh_model_r2 as F
L=F.L;p=L.p;NET='/IO_3V3'
def groups(g,cut=None,return_details=False,plane_terminals=False):
    layers=g['copper_layers'];parts={};trees={};offset={};parent=[]
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    for layer in layers:
        shapes=[]
        for z in g['zones']:
            if p.norm(z['net'])==NET:
                for poly in p.base.polygons(z['fills'].get(layer,[])):shapes.append(poly.difference(cut) if cut is not None and layer=='In2.Cu' else poly)
        for pad in g['pads']:
            if p.norm(pad['net'])==NET:shapes+=p.base.polygons(pad['layers'].get(layer,[]))
        shapes.extend(p.base.body(t) for t in g['tracks'] if t['layer']==layer and p.norm(t['net'])==NET)
        shapes.extend(Point(v['x'],v['y']).buffer(v['d']/2) for v in g['vias'] if p.norm(v['net'])==NET and layer in v['flashed'])
        print('IO3_UNION',layer,'SHAPES',len(shapes),flush=True)
        parts[layer]=p.hubs.components(set_precision(unary_union(shapes),1e-6));trees[layer]=STRtree(parts[layer]);offset[layer]=len(parent);parent.extend(range(len(parent),len(parent)+len(parts[layer])))
    def hits(layer,shape):return [offset[layer]+int(i) for i in trees[layer].query(set_precision(shape,1e-6),predicate='intersects')]
    # GEOS can return separate polygon components that meet at a boundary
    # point. Preserve that original contact topology explicitly, as native Cu
    # connectivity does; this does not qualify the cross-section for current.
    for layer in layers:
        for i,shape in enumerate(parts[layer]):
            for j in trees[layer].query(shape,predicate='intersects'):
                if int(j)>i:union(offset[layer]+i,offset[layer]+int(j))
    for via in g['vias']:
        if p.norm(via['net'])!=NET:continue
        nodes=[node for layer in via['flashed'] for node in hits(layer,Point(via['x'],via['y']).buffer(via['d']/2))]
        for node in nodes[1:]:union(nodes[0],node)
    terminals=[]
    for pad in g['pads']:
        if p.norm(pad['net'])!=NET:continue
        nodes=[node for layer,records in pad['layers'].items() for node in hits(layer,unary_union(p.base.polygons(records)))]
        for node in nodes[1:]:union(nodes[0],node)
        terminals.append((pad,nodes))
    if return_details:
        for via in g['vias']:
            if p.norm(via['net'])!=NET:continue
            for layer in via['flashed']:
                nodes=hits(layer,Point(via['x'],via['y']).buffer(via['d']/2))
                terminals.append(({'ref':'@VIA','num':layer,'uuid':via['uuid']+'@'+layer,'x':via['x'],'y':via['y']},nodes))
        for t in g['tracks']:
            if p.norm(t['net'])!=NET:continue
            body=p.base.body(t);pt=body.representative_point()
            terminals.append(({'ref':'@TRACK','num':t['layer'],'uuid':t['uuid'],'x':pt.x,'y':pt.y},hits(t['layer'],body)))
    if plane_terminals:
        for z in g['zones']:
            if p.norm(z['net'])!=NET:continue
            for layer,records in z['fills'].items():
                for poly_i,poly in enumerate(p.base.polygons(records)):
                    # Native polygon repair can contain multiple disconnected
                    # original components. Give each its own stable obligation.
                    for original_i,original_piece in enumerate(p.hubs.components(poly)):
                        obligation=z['uuid']+'@'+layer+'@'+str(poly_i)+'@'+str(original_i)
                        remaining=original_piece.difference(cut) if cut is not None and layer=='In2.Cu' else original_piece
                        for piece_i,piece in enumerate(p.hubs.components(remaining)):
                            pt=piece.representative_point()
                            terminals.append(({'ref':'@PLANE','num':layer,'uuid':obligation+'|'+str(piece_i),
                                               'source_obligation_uuid':obligation,'x':pt.x,'y':pt.y},hits(layer,piece)))
    grouped={}
    for pad,nodes in terminals:
        key=find(nodes[0]) if nodes else 'none-'+pad['uuid'];grouped.setdefault(key,[]).append({'ref':pad['ref'],'pad':pad['num'],'uuid':pad['uuid'],'source_obligation_uuid':pad.get('source_obligation_uuid',pad['uuid']),'at':[pad['x'],pad['y']]})
    ordered=sorted(grouped.values(),key=lambda row:min(x['uuid'] for x in row))
    if return_details:
        ids={r['uuid']:i for i,group in enumerate(ordered) for r in group};root_to_group={find(nodes[0]):ids[pad['uuid']] for pad,nodes in terminals if nodes}
        partgroups={layer:[root_to_group.get(find(offset[layer]+i)) for i in range(len(parts[layer]))] for layer in layers}
        return ordered,parts,partgroups
    return ordered,parts
def main():
    g,*_=F.load();path=L.OUT/'CORE-In2-variable-plane-r2.wkb';cut=from_wkb(path.read_bytes()).buffer(.175)
    before,bparts=groups(g);after,aparts=groups(g,cut);assign={r['uuid']:i for i,group in enumerate(after) for r in group};lost=[]
    for index,group in enumerate(before):
        divided={}
        for r in group:divided.setdefault(assign[r['uuid']],[]).append(r)
        if len(divided)>1:lost.append({'baseline_group':index,'baseline_terminals':len(group),'new_groups':[{'candidate_group':i,'terminals':r} for i,r in divided.items()]})
    result={'exact_board':L.live.SHA,'plane_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'net':NET,'before_terminal_groups':before,'after_terminal_groups':after,'lost_group_partitions':lost,'old_group_count':len(before),'new_group_count':len(after),'baseline_pad_count':sum(len(x) for x in before),'old_In2_parts':len(bparts['In2.Cu']),'new_In2_parts':len(aparts['In2.Cu']),'all_existing_discrete_track_pad_via_geometry_unchanged':True,'candidate_IO3_fill_is_boolean_projection_not_native_refill':True,'native_jobs':0,'board_written':False,'source_hashes':p.READS}
    (L.OUT/'IO3-contact-restoration-r2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('before_terminal_groups','after_terminal_groups','source_hashes','lost_group_partitions')}));print('LOST',json.dumps(lost))
if __name__=='__main__':main()
