"""Independent AO1 cut audit; does not call the root's projection helper."""
import collections,copy,re
import audit_aux_exact_raw as A
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C=A.P,A.G,A.S,A.C

def prospective_fill(source,candidate,masks,inventory,parsed,changed):
    exact_zones={}
    for uid,chunk in inventory[3].items():
        if C.pcbtext.chunk_kind(chunk)!='zone':continue
        match=re.search(rb'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',chunk)
        if match:exact_zones[uid]=float(match.group(1))
    # Freeze all physical source drills; subtract them locally from original
    # pad/track/actual-flashed-via copper before nominating fill contact edges.
    holes=[Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128) for v in source.g['vias']]
    holes.extend(poly for pad in source.g['pads'] for poly in S.poly(pad.get('hole') or []))
    htree=STRtree(holes);source_metal={}
    for layer,rows in source.records.items():
        metal=[]
        for row in rows:
            if row['kind'] not in ('pad','track','via'):continue
            if row['kind']=='via' and layer not in masks.get(row['uuid'],set()):continue
            local_holes=unary_union([holes[int(i)] for i in htree.query(row['shape'],predicate='intersects')])
            shape=row['shape'].difference(local_holes)
            if not shape.is_empty:metal.append((row,shape))
        source_metal[layer]=(metal,STRtree([shape for row,shape in metal]))
    # Subtract each exact changed item sequentially in UUID order, instead of
    # sharing the constructor's union-cut projection or its polygon identities.
    additions=[]
    for uid in sorted(changed):
        item=parsed[uid]
        if item['kind']=='via':
            copper=Point(item['at']).buffer(item['d']/2,resolution=128)
            drill=Point(item['at']).buffer(item['drill']/2,resolution=128)
            layers=set(candidate.g['copper_layers'])
        elif item['kind']=='segment':
            copper=LineString([item['a'],item['b']]).buffer(item['w']/2,resolution=128)
            drill=None;layers={item['layer']}
        else:raise ValueError('Unqualified changed geometry kind')
        additions.append((uid,item['net'],layers,copper,drill))
    result=copy.copy(candidate);result.records={};result.trees={};ledger=[];errors=[]
    for layer,rows in candidate.records.items():
        metals,tree=source_metal[layer];newrows=[]
        for index,fill in enumerate(rows):
            if fill['kind']!='fill':newrows.append(fill);continue
            uid=fill['uuid']
            if uid not in exact_zones:raise ValueError('Missing exact native design zone clearance '+uid)
            remaining=fill['shape'];cutrows=[]
            for item_uuid,net,layers,copper,drill in additions:
                if layer not in layers:continue
                if net==fill['net']:
                    if drill is None:continue
                    region=drill;required=0.
                else:
                    domain=.15 if candidate.domains[net]==fill.get('domain') else .6
                    required=max(exact_zones[uid],domain)
                    region=copper.buffer(required+.025,resolution=128)
                if not fill['shape'].intersects(region):continue
                cutrows.append({'uuid':item_uuid,'net':net,'required_zone_domain_clearance_mm':required})
                remaining=remaining.difference(region)
            if not cutrows:newrows.append(fill);continue
            pieces=P.K.D.components(remaining);contacts=[]
            if len(pieces)!=1:errors.append({'zone_uuid':uid,'net':fill['net'],'layer':layer,'reason':'Old fill component removed or split','new_piece_count':len(pieces)})
            for i in tree.query(fill['shape'],predicate='intersects'):
                metal,body=metals[int(i)]
                if metal['net']!=fill['net'] or body.distance(fill['shape'])>.000002:continue
                indices=[j for j,piece in enumerate(pieces) if piece.distance(body)<=.000002]
                contacts.append({'key':list(metal['key']),'uuid':metal['uuid'],'kind':metal['kind'],'candidate_piece_indices':indices})
                if not indices:errors.append({'zone_uuid':uid,'net':fill['net'],'layer':layer,'reason':'Old physical contact lost','key':list(metal['key'])})
            ledger.append({'zone_uuid':uid,'net':fill['net'],'layer':layer,'old_fill_index':index,'exact_original_fill_wkb_sha256':C.sha(fill['shape'].wkb),'exact_serialized_local_zone_clearance_mm':exact_zones[uid],'original_area_mm2':fill['shape'].area,'candidate_area_mm2':remaining.area,'cut_items':cutrows,'candidate_component_count':len(pieces),'old_existing_physical_contacts':contacts})
            newrows.extend(dict(fill,shape=piece,key=('z',uid,layer,C.sha(piece.wkb),j)) for j,piece in enumerate(pieces))
        result.records[layer]=newrows;result.trees[layer]=STRtree([row['shape'] for row in newrows])
    return result,ledger,errors
