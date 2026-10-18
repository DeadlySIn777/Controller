"""Independent prospective signal-reference audit of exact combined source, host only."""
import hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent/'alternate-r07')); sys.path.insert(0,str(HERE.parent))
import validate_combined as V
import screen_r07 as R
import screen_c06 as S
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

def main():
    destination = HERE / 'combined-audit.json'
    if destination.exists(): raise ValueError('Fresh audit receipt required')
    receipt = V.FAG/'staged/construction.json'; candidate = V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb'
    contract = V.validate_construction(receipt, candidate)
    pins = V.construction_hashes(receipt)
    for path, expected in pins.items():
        if hashlib.sha256(S.read(path)).hexdigest()!=expected: raise ValueError('Bound input differs:'+path)
    four = json.loads(S.read(V.FOUR/'audit.json')); paths = four['rows']
    if four['failures'] or four['changed_plane_tracks_or_arcs']: raise ValueError('Four-path reference base is invalid')
    combined = R.composition.inventory(S.read(candidate)); original = R.composition.inventory(S.read(R.R07))
    extra = {uid: chunk for uid,chunk in combined[4].items() if uid not in original[4]}
    field = [V.C.W.parse_copper(uid,chunk) for uid,chunk in extra.items() if uid in json.loads(S.read(receipt))['owned269']]
    field_vias = [row for row in field if row['kind']=='via']
    if len(field)!=269 or len(field_vias)!=5 or any(row['d']!=.6 or row['drill']!=.3 for row in field_vias): raise ValueError('Final FIELD source ownership differs')
    g,_,overlay = R.overlay_and_targets()
    reservations = json.loads(S.read(HERE.parent/'alternate-r07/reserved-r07.json'))
    import re
    exemptions={}
    for line in S.read(HERE.parent/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        match=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if match: exemptions[match[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",match[2])}
    print('COMBINED_REFERENCE_MODEL_START',flush=True)
    model = S.Model(g,reservations,exemptions)
    print('COMBINED_REFERENCE_MODEL_READY',flush=True)
    old = R.composition.inventory(S.read(S.overlay_tool.base.BASE))
    changed = set(original[4])-{uid for uid,ch in old[4].items() if original[4].get(uid)==ch}
    changed_plane=[uid for uid in changed if R.composition.pcbtext.chunk_kind(original[4][uid]) in ('segment','arc') and R.composition.pcbtext.chunk_layer(original[4][uid]) in ('In1.Cu','In4.Cu')]
    if changed_plane: raise ValueError('Changed reference-plane copper needs distinct geometry model')
    foreign=[via for via in g['vias'] if via['uuid'] in changed and S.norm(via['net'])!='/LOGIC_GND']
    old_cuts=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+(.15 if g['domains_normalized'].get(S.norm(v['net']))=='DOM_LOGIC' else .6)+.025) for v in foreign])
    signal_vias=[via for row in paths for via in row['new_signal_vias']]
    signal_cuts=unary_union([Point(v['point_mm']).buffer(.425) for v in signal_vias])
    field_cuts=unary_union([Point(v['at']).buffer(v['d']/2+.6+.025) for v in field_vias])
    refs,conductive_refs,witnesses={},{},{}
    anchor=model.pads['J11001.2#0']
    for layer in ('In1.Cu','In4.Cu'):
        fill=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']=='/LOGIC_GND'])
        safe=fill.difference(old_cuts).difference(signal_cuts).difference(field_cuts)
        own=[r['shape'] for r in model.records[layer] if r['net']=='/LOGIC_GND' and r['kind'] in ('pad','via','track')]
        conductive=unary_union([safe]+own); source=unary_union(S.poly(anchor['layers'][layer]))
        pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms)
        anchored=unary_union([piece for piece in pieces if piece.intersects(source)])
        refs[layer]=safe.intersection(anchored); conductive_refs[layer]=anchored
        if not refs[layer].is_valid: raise ValueError('Prospective reference invalid')
        witnesses[layer]={'source_pad':'J11001.2#0','source_uuid':anchor['uuid'],'new_FIELD_via_cutters':len(field_vias),'FIELD_antipad_radius_mm':.925,'new_signal_via_cutters':2,'old_foreign_via_cutters':len(foreign)}
    checks=[]; failures=[]
    for path in paths:
        for segment in path['segments']:
            remainder=LineString(segment['points_mm']).difference(signal_cuts)
            missing={layer: remainder.difference(shape) for layer,shape in refs.items()}
            row={'net':path['net'],'segment_layer':segment['layer'],'source_connected_reference':{layer:shape.is_empty for layer,shape in missing.items()},'uncovered_mm':{layer:shape.length for layer,shape in missing.items()}}
            checks.append(row)
            if not all(row['source_connected_reference'].values()): failures.append(row)
        for via in path['new_signal_vias']:
            retained=next(v for v in g['vias'] if v['uuid']==via['return_via']['uuid'])
            body=Point(retained['x'],retained['y']).buffer(retained['d']/2)
            connected={layer:shape.intersects(body) and refs[layer].intersects(body) for layer,shape in conductive_refs.items()}
            row={'net':path['net'],'return_via_uuid':retained['uuid'],'source_connected_after_all_FIELD_and_signal_antipads':connected};checks.append(row)
            if not all(connected.values()): failures.append(row)
    for path,expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('Audit input changed:'+path)
    result={'schema':'four-fag-independent-prospective-reference-v1','verdict':'HOST_PASS_NATIVE_ELECTRICAL_OPEN' if not failures else 'HOST_BLOCKED','contract':contract,'source_files_sha256':S.READS,'reference_witnesses':witnesses,'checks':checks,'failures':failures,'changed_plane_tracks_or_arcs':changed_plane,'field_vias':field_vias,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'limits':['Conservative r06 refilled copper over exact r07 items, no new native fill','Whole FAG layered copper contact audit bound, plane source/current/thermal scope remains open','Native DRC and both r07/r06 no-loss gates mandatory; full board source/electrical/physical gates remain open']}
    destination.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':result['verdict'],'failures':len(failures),'audit':str(destination)}),flush=True)

if __name__=='__main__': main()
