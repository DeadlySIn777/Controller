"""Select grounded companions around an already planned exact signal path."""
import json,math,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
S,C,HERE=F.S,F.C,F.HERE
OUT=HERE/'ground-escape-return-repair-r6'
def pieces(s):return [s] if s.geom_type=='Polygon' else [p for p in s.geoms if p.geom_type=='Polygon']
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__))
    original=json.loads(F.read(HERE/'new-via-escape-r5/result.json'));rows=[r for r in original['results'] if r['paths']]
    if len(rows)!=1:raise ValueError('One route expected')
    row=rows[0];route=row['paths'][0];net=S.norm(row['net']);g=F.geometry()
    prior=json.loads(F.read(HERE/'escape-signal-audit-r1/audit.json'));pv=[]
    for item in prior['new_items']:
        ch=item['raw_chunk'].encode();n=S.norm(S.overlay_tool.netname(ch))
        if item['kind']=='segment':g['tracks'].append({'uuid':item['uuid'],'net':n,'a':S.overlay_tool.numbers(ch,'start'),'b':S.overlay_tool.numbers(ch,'end'),'w':S.overlay_tool.scalar(ch,'width'),'layer':C.pcbtext.chunk_layer(ch)})
        else:
            x,y=S.overlay_tool.numbers(ch,'at');v={'uuid':item['uuid'],'net':n,'x':x,'y':y,'d':.5,'drill':.2,'flashed':g['copper_layers']};g['vias'].append(v);pv.append(v)
    reserved=json.loads(F.read(F.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in F.read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    model=F.exact_model_class()(g,reserved,ex);pc=unary_union([Point(v['x'],v['y']).buffer(.426,resolution=128) for v in pv])
    for layer in g['copper_layers']:
        for r in model.records[layer]:
            if r['kind']=='fill' and r.get('domain')=='DOM_LOGIC':r['shape']=r['shape'].difference(pc)
        model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]])
    refs={}
    for layer in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']=='/LOGIC_GND']);conductive=unary_union([fill]+[r['shape'] for r in model.records[layer] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][layer]));refs[layer]=fill.intersection(unary_union([p for p in pieces(conductive) if p.intersects(anchor)]))
    pathbody=unary_union([LineString(p['points_mm']).buffer(.1,resolution=128) for p in [route['source_escape']['outer_path'],route['inner_path'],route['target_escape']['outer_path']]])
    smd=STRtree([unary_union(S.poly(p['layers'].get(l,[]))) for p in g['pads'] if p['smd'] for l in ['F.Cu','B.Cu'] if p['layers'].get(l)])
    signal_points=[s['at'] for s in route['new_signal_vias']];selected=[];trials=[]
    for signal in route['new_signal_vias']:
        found=None
        for angle in range(64):
            theta=angle*math.tau/64;at=[round(signal['at'][0]+.95*math.cos(theta),9),round(signal['at'][1]+.95*math.sin(theta),9)];point=Point(at);body=point.buffer(.25,resolution=128);hole=point.buffer(.1,resolution=128);reason=None;cuts=[]
            if pathbody.distance(body)<.175:reason='complete signal path clearance'
            elif any(math.dist(at,p)<.8 for p in [*signal_points,*selected]):reason='mutual new via pitch'
            elif any(math.dist(at,[v['x'],v['y']])<.8 for v in g['vias']):reason='existing via pitch'
            elif not model.outline.buffer(-.6).covers(body):reason='edge'
            elif len(smd.query(hole.buffer(.125),predicate='intersects')):reason='SMD drill'
            elif not all(ref.covers(body.buffer(.025)) for ref in refs.values()):reason='unrooted reference body'
            if reason is None:
                for layer in g['copper_layers']:
                    for i in model.trees[layer].query(body.buffer(.775),predicate='intersects'):
                        r=model.records[layer][i]
                        if r['kind']=='hole':gap=hole.distance(r['shape']);minimum=.275
                        elif r.get('net')=='/LOGIC_GND':continue
                        elif r['kind']=='fill' and r.get('domain')=='DOM_LOGIC':
                            if body.buffer(.175).intersects(r['shape']):cuts.append({'zone_uuid':r['uuid'],'layer':layer,'net':r['net'],'antipad_radius_mm':.426})
                            continue
                        else:gap=body.distance(r['shape']);minimum=.175 if r.get('domain')=='DOM_LOGIC' else .625
                        if gap<minimum:reason='old '+r['kind']+' clearance';break
                    if reason:break
                    if any('/LOGIC_GND' not in r['exempt'] and body.buffer(.025).intersects(r['shape']) for r in model.hard[layer]):reason='hard area';break
            trials.append({'signal_at':signal['at'],'ground_at':at,'rejected':reason})
            if reason is None:
                found={'at':at,'diameter_mm':.5,'drill_mm':.2,'raw_net':'/LOGIC_GND','source_anchor':'J11001.2#0','whole_copper_body_connected_reference_planes':['In1.Cu','In4.Cu'],'prospective_antipads':cuts,'all_six_native_annuli_required':True};selected.append(at);break
        if found is None:raise ValueError('No complete-path-cleared grounded companion')
        signal['new_return_stitch']=found;signal['return_at']=found['at'];signal['return_distance_mm']=math.dist(signal['at'],found['at'])
    for side,index in [('source_escape',0),('target_escape',1)]:route[side]['via']=route['new_signal_vias'][index]
    out={'results':[row],'inputs':F.READS,'repair':'Signal route unchanged; new ground companion angles selected against complete signal copper','adopted':False,'native_jobs':0,'board_emitted':False}
    F.write('result.json',out);F.write('return-selection.json',{'selected':selected,'trials':trials,'inputs':F.READS,'independent_audit':'OPEN'})
    audit=HERE/'audit_ground_escape_r5.py';raw=F.read(audit).decode();derived=HERE/'audit_ground_escape_r6.py'
    if derived.exists():raise ValueError('Fresh audit required')
    raw=raw.replace("OUT=HERE/'ground-escape-audit-r5'","OUT=HERE/'ground-escape-audit-r6'").replace("HERE/'new-via-escape-r5/result.json'","HERE/'ground-escape-return-repair-r6/result.json'").replace('buffer(.425,resolution=128)','buffer(.426,resolution=128)')
    derived.write_text(raw,encoding='utf-8');F.write('audit-derivation.json',{'source':str(audit),'source_sha256':C.sha(audit.read_bytes()),'derived':str(derived),'derived_sha256':C.sha(derived.read_bytes()),'changes':['Audit exact repaired return plan','Use .426mm conservative predicted fill cuts to keep .175mm clearance despite polygon sagitta'],'no_actual_clearance_rule_changed':True})
    print(json.dumps({'selected':selected,'trials':len(trials),'audit':str(derived)}),flush=True)
if __name__=='__main__':main()
