"""Exact-source prospective B ground retreat; no source/zone/native mutation.

Only same-domain LOGIC_GND filled copper may retreat. Serialized source zone
clearances, every cross-domain boundary and actual no_zones/no_tracks area
remain authoritative. Every touched old filled component and every original
physical same-net contact is retained. Native refill/DRC/no-loss is mandatory.
"""
import collections,copy,math,re
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
import audit_aux_exact_raw as A
P,G,S,C=A.P,A.G,A.S,A.C
GND='/LOGIC_GND'

def zone_clearances(inventory):
    result={}
    for uid,ch in inventory[3].items():
        if C.pcbtext.chunk_kind(ch)!='zone':continue
        text=ch.decode();match=re.search(r'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',text)
        if match:result[uid]=max(.15,float(match.group(1)))
    return result

def permitted(record,net,model):
    return record['kind']=='fill' and record['net']==GND and record.get('domain')==model.domains[net]

def free(model,net,layer,window,width=.2):
    obstacles=[];blocked=[];domain=model.domains[net]
    for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
        r=model.records[layer][i]
        if layer=='B.Cu' and permitted(r,net,model):continue
        if r['kind']=='hole':
            if r['net']==net:continue
            gap=.25
        else:
            if r['net']==net:continue
            gap=.15 if r.get('domain')==domain else .6
        obstacles.append(r['shape'].buffer(gap+width/2+S.MARGIN));blocked.append({k:r[k] for k in ('kind','uuid','net') if k in r})
    for r in model.hard[layer]:
        if net not in r['exempt'] and r['shape'].intersects(window.buffer(2)):
            obstacles.append(r['shape'].buffer(width/2+S.MARGIN));blocked.append({'kind':r['kind'],'name':r['name']})
    return window.intersection(model.outline.buffer(-.5-width/2-S.MARGIN)).difference(unary_union(obstacles)),blocked

def freevia(model,net,window):
    obstacles=[];counts=collections.Counter();domain=model.domains[net]
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=model.records[layer][i]
            if layer=='B.Cu' and permitted(r,net,model):continue
            if r['kind']=='hole':gap=.25
            elif r['kind']=='pad' and r['net']==net:gap=.1 if model.pads[r['pad_id']]['smd'] else .25
            elif r['net']==net:continue
            elif r['kind']=='fill' and layer in ('In1.Cu','In2.Cu','In4.Cu') and r.get('domain')==domain:continue
            else:gap=.15 if r.get('domain')==domain else .6
            obstacles.append(r['shape'].buffer(.25+gap+S.MARGIN));counts[r['kind']]+=1
        for r in model.hard[layer]:
            if net not in r['exempt'] and r['shape'].intersects(window.buffer(2)):
                obstacles.append(r['shape'].buffer(.25+S.MARGIN));counts[r['kind']]+=1
    for v in model.g['vias']:
        if window.buffer(2).covers(Point(v['x'],v['y'])):obstacles.append(Point(v['x'],v['y']).buffer(.8+S.MARGIN,resolution=128))
    return window.intersection(model.outline.buffer(-.5-.25-S.MARGIN)).difference(unary_union(obstacles)),dict(counts)

def retreat(model,parsed,changed,masks,clearances,source_model=None):
    """Cut B tracks and all-layer via GND voids; source chunks stay verbatim."""
    cuts=[];rows=[]
    for uid in sorted(changed):
        r=parsed[uid]
        if r['kind']=='segment' and r['layer']=='B.Cu':cuts.append((uid,r['net'],{'B.Cu'},LineString([r['a'],r['b']]).buffer(r['w']/2,resolution=128)))
        elif r['kind']=='via':cuts.append((uid,r['net'],set(model.g['copper_layers']),Point(r['at']).buffer(r['d']/2 if r['net']!=GND else r['drill']/2,resolution=128)))
    candidate=copy.copy(model);candidate.records=dict(model.records);candidate.trees=dict(model.trees)
    old_contact_shapes=collections.defaultdict(list)
    source_model=source_model or model
    vias={v['uuid']:v for v in source_model.g['vias']}
    for z in source_model.own[GND]:
        if z['kind']=='via':
            if z['layer'] not in masks.get(z['uuid'],set()):continue
            v=vias[z['uuid']];body=Point(v['x'],v['y']).buffer(v['d']/2,resolution=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128))
        else:body=z['shape']
        old_contact_shapes[z['layer']].append((z['key'],z['uuid'],z['kind'],body))
    errors=[]
    for layer in model.g['copper_layers']:
        old=old_contact_shapes[layer];tree=STRtree([q[3] for q in old]);new_records=[]
        for index,z in enumerate(model.records[layer]):
            if z['kind']!='fill' or z['net']!=GND:new_records.append(z);continue
            relevant=[];required=clearances.get(z['uuid'])
            for uid,net,layers,body in cuts:
                if layer not in layers or model.domains[net]!=z.get('domain'):continue
                if required is None:raise ValueError('No exact serialized zone clearance for '+z['uuid'])
                cut=body if net==GND else body.buffer(required+S.MARGIN,resolution=128)
                if cut.intersects(z['shape']):relevant.append((uid,net,cut))
            if not relevant:new_records.append(z);continue
            after=z['shape'].difference(unary_union([x[2] for x in relevant]));pieces=P.K.D.components(after);contacts=[]
            for i in tree.query(z['shape'],predicate='intersects'):
                key,uuid,kind,body=old[i]
                if body.distance(z['shape'])>.000002:continue
                touching=[j for j,piece in enumerate(pieces) if body.distance(piece)<=.000002]
                contacts.append({'key':list(key),'uuid':uuid,'kind':kind,'candidate_piece_indices':touching})
                if not touching:errors.append({'zone_uuid':z['uuid'],'layer':layer,'old_fill_index':index,'kind':'lost_existing_ground_contact','key':list(key)})
            # No speculative cross-layer bridge credits a split old component.
            if len(pieces)!=1:errors.append({'zone_uuid':z['uuid'],'layer':layer,'old_fill_index':index,'kind':'old_fill_component_removed_or_split','candidate_component_count':len(pieces)})
            rows.append({'zone_uuid':z['uuid'],'layer':layer,'old_fill_index':index,'exact_original_fill_wkb_sha256':C.sha(z['shape'].wkb),'old_area_mm2':z['shape'].area,'candidate_area_mm2':after.area,'removed_area_mm2':z['shape'].area-after.area,'exact_zone_clearance_mm':required,'planning_margin_mm':S.MARGIN,'cut_item_uuids':[x[0] for x in relevant],'candidate_component_count':len(pieces),'old_existing_physical_contacts':contacts})
            for piece in pieces:new_records.append(dict(z,shape=piece))
        candidate.records[layer]=new_records;candidate.trees[layer]=STRtree([z['shape'] for z in new_records])
    return candidate,rows,errors
