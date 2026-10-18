"""Independently reconstruct signal and return copper, including prior route.

This audit never treats a routing success as electrical/native approval.
"""
import ast,collections,json,math,re,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
from audit_escape_signal import raw_registry
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
S,C,HERE=F.S,F.C,F.HERE
OUT=HERE/'ground-escape-audit-r6'

def pieces(shape):
    if shape.is_empty:return []
    if shape.geom_type=='Polygon':return [shape]
    return [p for p in shape.geoms if p.geom_type=='Polygon' and p.area>1e-10]

def source_ports():
    parser=F.BASE/'parity-repair/root106/tools/netlist_parity.py'
    tree=ast.parse(F.read(parser).decode());ns={'re':re}
    nodes=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-source-pin-roles','exec'),ns)
    parse,child,children,atom=[ns[k] for k in ('sexpr_parse','child','children','atom')]
    root=parse(F.read(HERE/'cap-signal-native-r1/measure/fresh.net').decode())
    cs={atom(c,'ref'):{'value':atom(c,'value'),'sheet':atom(child(c,'sheetpath') or [],'names')} for c in children(child(root,'components'),'comp')}
    return {S.norm(atom(n,'name')):[{**{k:atom(v,k) for k in ('ref','pin','pinfunction','pintype')},**cs[atom(v,'ref')]} for v in children(n,'node')] for n in children(child(root,'nets'),'net')}

def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__))
    plan=json.loads(F.read(HERE/'ground-escape-return-repair-r6/result.json'))
    selected=[r for r in plan['results'] if r['paths']]
    if len(selected)!=1:raise ValueError('One exact independently reconstructed route expected')
    row=selected[0];net=S.norm(row['net']);source=F.read(F.SOURCE);registry=raw_registry(source)
    controlled=json.loads(F.read(F.BASE/'controlled-geometry/controlled-net-map.json'))
    if net in {S.norm(n) for n in controlled}:raise ValueError('Controlled route cannot use ordinary width/layer policy')
    roles=source_ports()[net]
    if any(p['pintype'] in ('power_in','power_out') for p in roles):raise ValueError('Ordinary power pin denied')
    g=F.geometry();prior=json.loads(F.read(HERE/'escape-signal-audit-r1/audit.json'))
    if prior['verdict']!='HOST_READY_NATIVE_ELECTRICAL_OPEN':raise ValueError('Prior route failed independent audit')
    prior_vias=[]
    for item in prior['new_items']:
        chunk=item['raw_chunk'].encode();pn=S.norm(S.overlay_tool.netname(chunk))
        if item['kind']=='segment':
            g['tracks'].append({'uuid':item['uuid'],'net':pn,'a':S.overlay_tool.numbers(chunk,'start'),'b':S.overlay_tool.numbers(chunk,'end'),'w':S.overlay_tool.scalar(chunk,'width'),'layer':C.pcbtext.chunk_layer(chunk)})
        else:
            x,y=S.overlay_tool.numbers(chunk,'at');v={'uuid':item['uuid'],'net':pn,'x':x,'y':y,'d':S.overlay_tool.scalar(chunk,'size'),'drill':S.overlay_tool.scalar(chunk,'drill'),'flashed':g['copper_layers']};g['vias'].append(v);prior_vias.append(v)
    reserved=json.loads(F.read(F.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in F.read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    model=F.exact_model_class()(g,reserved,ex)
    prior_cuts=unary_union([Point(v['x'],v['y']).buffer(.426,resolution=128) for v in prior_vias])
    for layer in g['copper_layers']:
        for record in model.records[layer]:
            if record['kind']=='fill' and record.get('domain')=='DOM_LOGIC':record['shape']=record['shape'].difference(prior_cuts)
        model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]])
    route=row['paths'][0];paths=[(route['source_escape']['outer_layer'],route['source_escape']['outer_path']),('In3.Cu',route['inner_path']),(route['target_escape']['outer_layer'],route['target_escape']['outer_path'])]
    items=[];errors=[];nearest=collections.defaultdict(lambda:float('inf'));fmt=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    for layer,path in paths:
        for a,b in zip(path['points_mm'],path['points_mm'][1:]):
            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-ground-escape-r5/'+registry[net]+'/'+layer+'/'+repr((a,b,.2))))
            ch=(f'\t(segment\n\t\t(start {fmt(a[0])} {fmt(a[1])})\n\t\t(end {fmt(b[0])} {fmt(b[1])})\n\t\t(width 0.2)\n\t\t(layer "{layer}")\n\t\t(net "{registry[net]}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
            items.append({'uuid':uid,'kind':'segment','net':net,'layer':layer,'shape':LineString([a,b]).buffer(.1,resolution=128),'chunk':ch})
    for signal in route['new_signal_vias']:
        if signal.get('new_return_stitch') is None:raise ValueError('This audit expects two separately reconstructed new returns')
        for vn,via in [(net,signal),('/LOGIC_GND',signal['new_return_stitch'])]:
            at=via['at'];uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-ground-escape-r5/'+registry[vn]+'/via/'+repr(at)))
            ch=(f'\t(via\n\t\t(at {fmt(at[0])} {fmt(at[1])})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{registry[vn]}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
            items.append({'uuid':uid,'kind':'via','net':vn,'at':at,'shape':Point(at).buffer(.25,resolution=128),'hole':Point(at).buffer(.1,resolution=128),'chunk':ch})
        d=math.dist(signal['at'],signal['new_return_stitch']['at'])
        if not .8<=d<=1:errors.append({'invalid_signal_return_distance_mm':d})
    vias=[i for i in items if i['kind']=='via'];signal_cuts=unary_union([Point(i['at']).buffer(.426,resolution=128) for i in vias if i['net']==net])
    all_cuts=unary_union([Point(i['at']).buffer(.426,resolution=128) for i in vias]);affected=[];contact_cuts=[]
    for layer in g['copper_layers']:
        for record in model.records[layer]:
            if record['kind']!='fill' or record.get('domain')!='DOM_LOGIC':continue
            cutters=unary_union([Point(i['at']).buffer(.426,resolution=128) for i in vias if i['net']!=record['net']])
            if not record['shape'].intersects(cutters):continue
            before=record['shape'];after=before.difference(cutters)
            if len(pieces(before))!=len(pieces(after)):errors.append({'zone':record['uuid'],'layer':layer,'fill_piece_count_changed':[len(pieces(before)),len(pieces(after))]})
            affected.append({'zone_uuid':record['uuid'],'layer':layer,'net':record['net'],'removed_mm2':before.difference(after).area,'before_piece_count':len(pieces(before)),'after_piece_count':len(pieces(after))})
            for j in model.trees[layer].query(before.difference(after),predicate='intersects'):
                old=model.records[layer][j]
                if old['kind'] not in ('pad','track','via') or old.get('net')!=record['net']:continue
                lost=old['shape'].intersection(before).difference(after).area
                if lost>1e-9:contact_cuts.append({'zone':record['uuid'],'layer':layer,'old_uuid':old['uuid'],'kind':old['kind'],'removed_contact_area_mm2':lost})
            record['shape']=after
        model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]])
    if contact_cuts:errors.append({'existing_plane_contact_cuts':contact_cuts})
    smd=STRtree([unary_union(S.poly(p['layers'].get(l,[]))) for p in g['pads'] if p['smd'] for l in ['F.Cu','B.Cu'] if p['layers'].get(l)])
    for item in items:
        body=item['shape'];layers=g['copper_layers'] if item['kind']=='via' else [item['layer']]
        if not model.outline.buffer(-.6).covers(body):errors.append({'new_uuid':item['uuid'],'edge_clearance':False})
        if item['kind']=='via' and len(smd.query(item['hole'].buffer(.125),predicate='intersects')):errors.append({'new_uuid':item['uuid'],'new_ordinary_drill_near_smd':True})
        for layer in layers:
            for j in model.trees[layer].query(body.buffer(.775),predicate='intersects'):
                old=model.records[layer][j]
                if old['kind']=='hole':
                    if item['kind']=='segment' and old.get('net')==item['net']:continue
                    shape=item.get('hole',body);minimum=.275
                elif old.get('net')==item['net']:continue
                else:shape=body;minimum=.175 if old.get('domain')=='DOM_LOGIC' else .625
                gap=shape.distance(old['shape']);nearest[old['kind']]=min(nearest[old['kind']],gap)
                if gap<minimum-1e-8:errors.append({'new_uuid':item['uuid'],'layer':layer,'old_uuid':old['uuid'],'kind':old['kind'],'gap_mm':gap,'minimum_mm':minimum})
            for hard in model.hard[layer]:
                if item['net'] not in hard['exempt'] and body.buffer(.025).intersects(hard['shape']):errors.append({'new_uuid':item['uuid'],'layer':layer,'hard_area':hard['name']})
        if item['kind']=='via':
            for v in g['vias']:
                d=math.dist(item['at'],[v['x'],v['y']])
                if d<.8-1e-8:errors.append({'new_uuid':item['uuid'],'old_via':v['uuid'],'ordinary_pitch_mm':d})
    for j,a in enumerate(items):
        for b in items[j+1:]:
            if a['kind']=='via' and b['kind']=='via' and math.dist(a['at'],b['at'])<.8-1e-8:errors.append({'new_via_pair':[a['uuid'],b['uuid']],'pitch_mm':math.dist(a['at'],b['at'])})
            if a['net']==b['net']:continue
            al=set(g['copper_layers'] if a['kind']=='via' else [a['layer']]);bl=set(g['copper_layers'] if b['kind']=='via' else [b['layer']])
            if al&bl and a['shape'].distance(b['shape'])<.175-1e-8:errors.append({'mutual_new_copper_gap_mm':a['shape'].distance(b['shape']),'items':[a['uuid'],b['uuid']]})
    refs={};return_checks=[];reference=[]
    for plane in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']=='/LOGIC_GND'])
        conductive=unary_union([fill]+[r['shape'] for r in model.records[plane] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane]));refs[plane]=fill.intersection(unary_union([p for p in pieces(conductive) if p.intersects(anchor)]))
        for via in vias:
            if via['net']!='/LOGIC_GND':continue
            covered=refs[plane].covers(via['shape'].buffer(.025));return_checks.append({'via':via['uuid'],'plane':plane,'whole_annulus_with_margin_source_connected':covered})
            if not covered:errors.append(return_checks[-1])
    for layer,path in paths:
        body=LineString(path['points_mm']).buffer(.1,resolution=128);outside=body.difference(refs[S.REF_LAYER[layer]].union(signal_cuts));reference.append({'layer':layer,'reference':S.REF_LAYER[layer],'uncovered_beyond_own_signal_antipads_mm2':outside.area,'own_antipad_exception_mm2':body.intersection(signal_cuts).area})
        if outside.area>1e-8:errors.append(reference[-1])
    inv=C.inventory(source);candidate=inv[0]+b''.join(inv[1])+b''.join(i['raw_chunk'].encode() for i in prior['new_items'])+b''.join(i['chunk'] for i in items)+inv[2];ci=C.inventory(candidate)
    if raw_registry(candidate)!=registry or ci[5]!=inv[5] or any(ci[3].get(u)!=ch for u,ch in inv[3].items()):raise ValueError('Unowned entity, footprint or exact raw net changed')
    F.READS.update(S.READS)
    for p,h in F.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen audit input changed '+p)
    report={'verdict':'HOST_READY_NATIVE_ELECTRICAL_OPEN' if not errors else 'HOST_AUDIT_FAIL','board_source_sha256':C.sha(source),'candidate_sha256':C.sha(candidate),'net_raw':registry[net],'source_ports':roles,'controlled_proposal_assignment':None,'errors':errors,'nearest_gaps_mm':dict(nearest),'prospective_plane_antipads':affected,'existing_plane_contacts_removed':contact_cuts,'reference_rows':reference,'new_return_checks':return_checks,'new_items':[{'uuid':i['uuid'],'kind':i['kind'],'net':i['net'],'layer':i.get('layer'),'raw_chunk':i['chunk'].decode(),'sha256':C.sha(i['chunk'])} for i in items],'prior_items_exact':len(prior['new_items']),'inputs':F.READS,'native_drc':False,'native_actual_annuli':False,'current_edge_length_timing_review':'OPEN','adopted':False}
    F.write('audit.json',report)
    if not errors:(OUT/'ground-escape-host-only.kicad_pcb').write_bytes(candidate)
    print(json.dumps({'verdict':report['verdict'],'errors':errors,'new_items':len(items),'source_ports':roles,'candidate_sha256':report['candidate_sha256']}),flush=True)

if __name__=='__main__':main()
