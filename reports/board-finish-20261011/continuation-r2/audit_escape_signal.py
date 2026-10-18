"""Independent exact geometry/identity audit of one ordinary two-via escape."""
import collections,hashlib,json,re,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
S=F.S;C=F.C;HERE=F.HERE;OUT=HERE/'escape-signal-audit-r1'
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
def raw_registry(data):
    names={json.loads('"'+m+'"') for m in re.findall(r'\(net\s+"((?:[^"\\]|\\.)*)"\)',data.decode('utf-8'))};groups=collections.defaultdict(list)
    for raw in names:groups[S.norm(raw)].append(raw)
    if any(len(values)!=1 for values in groups.values()):raise ValueError('Raw native name collision')
    return {key:values[0] for key,values in groups.items()}
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__));plan=json.loads(F.read(HERE/'new-via-escape-r2/result.json'));rows=[r for r in plan['results'] if r['paths']]
    if len(rows)!=1:raise ValueError('One exact escape expected')
    row=rows[0];route=row['paths'][0];source=F.read(F.SOURCE);tokens=raw_registry(source);raw_net=tokens[S.norm(row['net'])]
    g=F.geometry();reserved=json.loads(F.read(F.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in F.read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    model=F.exact_model_class()(g,reserved,ex);paths=[(route['source_escape']['outer_layer'],route['source_escape']['outer_path']['points_mm']),('In3.Cu',route['inner_path']['points_mm']),(route['target_escape']['outer_layer'],route['target_escape']['outer_path']['points_mm'])];items=[];errors=[];nearest=collections.defaultdict(lambda:float('inf'))
    f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    for layer,points in paths:
        for a,b in zip(points,points[1:]):
            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-escape-r2/'+raw_net+'/'+layer+'/'+repr((a,b,.2))));ch=(f'\t(segment\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(width 0.2)\n\t\t(layer "{layer}")\n\t\t(net "{raw_net}")\n\t\t(uuid "{uid}")\n\t)\n').encode();items.append({'uuid':uid,'kind':'segment','layer':layer,'shape':LineString([a,b]).buffer(.1,resolution=128),'chunk':ch})
    cutters=unary_union([Point(v['at']).buffer(.425,resolution=128) for v in route['new_signal_vias']])
    existing={v['uuid']:v for v in g['vias']}
    for via in route['new_signal_vias']:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-escape-r2/'+raw_net+'/via/'+repr(via['at'])));x,y=via['at'];ch=(f'\t(via\n\t\t(at {f(x)} {f(y)})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{raw_net}")\n\t\t(uuid "{uid}")\n\t)\n').encode();items.append({'uuid':uid,'kind':'via','shape':Point(via['at']).buffer(.25,resolution=128),'hole':Point(via['at']).buffer(.1,resolution=128),'at':via['at'],'return':via,'chunk':ch})
        rv=existing[via['return_via_uuid']]
        if S.norm(rv['net'])!='/LOGIC_GND' or {'In1.Cu','In4.Cu'}-set(rv['flashed']) or Point(via['at']).distance(Point(rv['x'],rv['y']))>1:errors.append({'via':uid,'invalid_retained_return':rv['uuid']})
    affected=[];alloldcontactcuts=[]
    for layer in g['copper_layers']:
        for record in model.records[layer]:
            if record['kind']!='fill' or record.get('domain')!='DOM_LOGIC' or not record['shape'].intersects(cutters):continue
            after=record['shape'].difference(cutters);pieces=[after] if after.geom_type=='Polygon' else [p for p in after.geoms if p.geom_type=='Polygon' and p.area>1e-10];affected.append({'zone_uuid':record['uuid'],'layer':layer,'net':record['net'],'conservative_antipad_removed_mm2':record['shape'].intersection(cutters).area,'after_piece_count':len(pieces)})
            if len(pieces)!=1:errors.append({'zone_uuid':record['uuid'],'layer':layer,'split_or_removed_fill_piece':len(pieces)})
            for i in model.trees[layer].query(record['shape'].intersection(cutters),predicate='intersects'):
                old=model.records[layer][i]
                if old['kind'] in ('pad','track','via') and old.get('net')==record['net'] and old['shape'].intersects(record['shape']) and old['shape'].intersection(record['shape']).difference(after).area>1e-9:alloldcontactcuts.append({'zone_uuid':record['uuid'],'layer':layer,'old_uuid':old['uuid'],'kind':old['kind'],'lost_contact_area_mm2':old['shape'].intersection(record['shape']).difference(after).area})
    if alloldcontactcuts:errors.append({'old_plane_contacts_cut':alloldcontactcuts})
    for item in items:
        body=item['shape'];layers=g['copper_layers'] if item['kind']=='via' else [item['layer']]
        for layer in layers:
            for i in model.trees[layer].query(body.buffer(.75),predicate='intersects'):
                record=model.records[layer][i]
                if record['kind']=='hole':
                    if item['kind']=='segment' and record.get('net')==S.norm(row['net']):continue
                    required=.25;shape=item.get('hole',body)
                elif record.get('net')==S.norm(row['net']):
                    if item['kind']=='via' and record['kind']=='pad' and model.pads[record['pad_id']]['smd']:required=.1;shape=body
                    else:continue
                elif item['kind']=='via' and record['kind']=='fill' and record.get('domain')=='DOM_LOGIC':continue
                else:required=.15 if record.get('domain')=='DOM_LOGIC' else .6;shape=body
                gap=shape.distance(record['shape']);nearest[record['kind']]=min(nearest[record['kind']],gap)
                if gap<required+.010-1e-9:errors.append({'new_uuid':item['uuid'],'layer':layer,'old_uuid':record['uuid'],'kind':record['kind'],'gap_mm':gap,'minimum_with_geometry_error_mm':required+.010})
            for hard in model.hard[layer]:
                if S.norm(row['net']) not in hard['exempt'] and body.buffer(.010).intersects(hard['shape']):errors.append({'new_uuid':item['uuid'],'hard_area':hard['name'],'layer':layer})
        if item['kind']=='via':
            for v in g['vias']:
                distance=Point(item['at']).distance(Point(v['x'],v['y']))
                if distance<.8-1e-8:errors.append({'new_uuid':item['uuid'],'old_via':v['uuid'],'ordinary_pitch_mm':distance})
    refs={}
    for plane in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']=='/LOGIC_GND']);conductive=unary_union([fill]+[r['shape'] for r in model.records[plane] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane]));pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms);refs[plane]=fill.intersection(unary_union([p for p in pieces if p.intersects(anchor)]))
    reference=[]
    for layer,points in paths:
        body=LineString(points).buffer(.1,resolution=128);ref=refs[S.REF_LAYER[layer]];outside=body.difference(ref);reference.append({'layer':layer,'reference':S.REF_LAYER[layer],'body_uncovered_before_antipads_mm2':outside.area,'own_endpoint_antipad_exception_mm2':body.intersection(cutters).area})
        if outside.area>1e-8:errors.append({'layer':layer,'body_reference_uncovered_mm2':outside.area})
    baseline=C.inventory(source);candidate=baseline[0]+b''.join(baseline[1])+b''.join(i['chunk'] for i in items)+baseline[2];inv=C.inventory(candidate)
    if raw_registry(candidate)!=tokens or inv[5]!=baseline[5] or any(inv[3].get(u)!=ch for u,ch in baseline[3].items()):raise ValueError('Pure additive identity/net token contract failed')
    F.READS.update(S.READS)
    for p,h in F.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen input changed '+p)
    report={'schema':'ordinary-two-via-independent-audit-r1','verdict':'HOST_READY_NATIVE_ELECTRICAL_OPEN' if not errors else 'HOST_AUDIT_FAIL','board_source_sha256':C.sha(source),'candidate_sha256':C.sha(candidate),'net_raw':raw_net,'no_normalized_collisions':True,'geometry_errors':errors,'nearest_gaps_mm':dict(nearest),'prospective_plane_antipads':affected,'existing_plane_contacts_removed':alloldcontactcuts,'reference_rows':reference,'new_items':[{'uuid':i['uuid'],'kind':i['kind'],'layer':i.get('layer'),'raw_chunk':i['chunk'].decode(),'sha256':C.sha(i['chunk']),'existing_return':i.get('return')} for i in items],'inputs':F.READS,'native_drc':False,'native_actual_added_annuli':False,'adopted':False,'manufacturing_ready':False}
    F.write('audit.json',report)
    if not errors:(OUT/'escape-signal-host-only.kicad_pcb').write_bytes(candidate)
    print(json.dumps({'verdict':report['verdict'],'candidate_sha256':report['candidate_sha256'],'errors':errors,'new_items':len(items),'affected_fill_pieces':len(affected)}),flush=True)
if __name__=='__main__':main()
