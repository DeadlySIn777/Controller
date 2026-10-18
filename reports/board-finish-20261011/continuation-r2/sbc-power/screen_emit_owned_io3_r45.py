"""Exact IO3 owned replacement chunks and scoped protected-overlay screen."""
import json,pickle,hashlib,sys
from shapely.geometry import Point,LineString
import core_inner_feed_r18 as I
L=I.L;p=I.p;G=I.G
FIELD=L.OUT.parent/'field-power';sys.path.insert(0,str(FIELD))
import contact_layout as C
from verify_source import parse,atom
OUT=L.OUT/'owned-io3-native-recipe-r45'
EXCLUDED={'32d1ff6d-3134-5587-b14c-e0fe8f143896','61bc227f-53f6-5ca5-98d2-ed53fdf555b0','2cffa505-7280-5065-aee5-167fd8d5db6b','152342e5-2634-56f0-b6a9-0520deb780d2'}
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();prior=L.OUT/'owned-io3-layer-escape-repair-r42';model=prior/'model.pkl'
    assert sha(model)=='dc06d1688f700a4c0232ee948ebbdfba6d4af931a9918f5521b1914de194ce68'
    g,h,binding,fullzones,_=pickle.loads(model.read_bytes());d=pickle.loads((prior/'proposed-discrete.pkl').read_bytes());zones=pickle.loads((prior/'proposed-zones.pkl').read_bytes())
    r7=L.OUT.parent/'protected24-dogbones-r7';rd=pickle.loads((r7/'proposed-discrete.pkl').read_bytes());rz=pickle.loads((r7/'proposed-zones.pkl').read_bytes());preserved=[z for z in rz if z['uuid'] not in EXCLUDED]
    assert len(rd['vias'])==12 and len(rd['tracks'])==12 and len(preserved)==6
    errors=[];pairs=[]
    for z in zones:
        for q in rd['tracks']:
            if q['layer']!=z['layer']:continue
            gap=G.gap(h,z['net'],q['net'])+.025;actual=LineString([q['a'],q['b']]).distance(z['shape'])-q['w']/2
            pairs.append({'owned_IO3_uuid':z['uuid'],'protected_uuid':q['uuid'],'kind':'zone_vs_segment','actual_gap_mm':actual,'required_gap_mm':gap})
            if actual<gap:errors.append(pairs[-1])
        for q in rd['vias']:
            gap=max(q['drill']/2+.275,q['d']/2+G.gap(h,z['net'],q['net'])+.025)
            actual=Point(q['x'],q['y']).distance(z['shape']);pairs.append({'owned_IO3_uuid':z['uuid'],'protected_uuid':q['uuid'],'kind':'zone_vs_via','center_distance_mm':actual,'required_center_distance_mm':gap})
            if actual<gap:errors.append(pairs[-1])
        for q in preserved:
            if q['layer']!=z['layer']:continue
            gap=max(G.gap(h,z['net'],q['net']),float(z.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025
            actual=z['shape'].distance(q['shape']);pairs.append({'owned_IO3_uuid':z['uuid'],'protected_uuid':q['uuid'],'kind':'zone_vs_zone','actual_gap_mm':actual,'required_gap_mm':gap})
            if actual<gap:errors.append(pairs[-1])
    for v in d['vias']:
        vp=Point(v['x'],v['y'])
        for q in rd['vias']:
            center=vp.distance(Point(q['x'],q['y']));required=max((v['drill']+q['drill'])/2+.275,(v['d']+q['d'])/2+G.gap(h,v['net'],q['net'])+.025)
            if center<required:errors.append({'owned_IO3_uuid':v['uuid'],'protected_uuid':q['uuid'],'kind':'via_vs_via','center_distance_mm':center,'required_center_distance_mm':required})
        for q in rd['tracks']:
            actual=vp.distance(LineString([q['a'],q['b']]))-v['d']/2-q['w']/2;gap=G.gap(h,v['net'],q['net'])+.025
            if actual<gap:errors.append({'owned_IO3_uuid':v['uuid'],'protected_uuid':q['uuid'],'kind':'via_vs_segment','actual_gap_mm':actual,'required_gap_mm':gap})
        for q in preserved:
            required=max(v['drill']/2+.275,v['d']/2+G.gap(h,v['net'],q['net'])+.025);actual=vp.distance(q['shape'])
            if actual<required:errors.append({'owned_IO3_uuid':v['uuid'],'protected_uuid':q['uuid'],'kind':'via_vs_zone','center_distance_mm':actual,'required_center_distance_mm':required})
    for t in d['tracks']:
        line=LineString([t['a'],t['b']])
        for q in preserved:
            if q['layer']!=t['layer']:continue
            actual=line.distance(q['shape'])-t['w']/2;gap=G.gap(h,t['net'],q['net'])+.025
            if actual<gap:errors.append({'owned_IO3_uuid':t['uuid'],'protected_uuid':q['uuid'],'kind':'segment_vs_zone','actual_gap_mm':actual,'required_gap_mm':gap})
        for q in rd['tracks']:
            if q['layer']!=t['layer']:continue
            actual=line.distance(LineString([q['a'],q['b']]))-(t['w']+q['w'])/2;gap=G.gap(h,t['net'],q['net'])+.025
            if actual<gap:errors.append({'owned_IO3_uuid':t['uuid'],'protected_uuid':q['uuid'],'kind':'segment_vs_segment','actual_gap_mm':actual,'required_gap_mm':gap})
    native=L.OUT.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    _,chunks,_=C.O.C.pcbtext.split(native.read_bytes());byid={C.O.C.pcbtext.chunk_uuid(x):x for x in chunks if C.O.C.pcbtext.chunk_uuid(x)}
    ledger=L.OUT/'owned-io3-cm-crossing-repair-r39/owned-existing-Cu-removal-ledger.json';old=json.loads(ledger.read_text());delete=[];adds=[]
    for row in old['rows']:
        chunk=byid[row['uuid']];assert hashlib.sha256(chunk).hexdigest()==row['chunk_sha256'];file=OUT/(row['uuid']+'.delete-original-segment-chunk');file.write_bytes(chunk)
        delete.append({'kind':'segment','uuid':row['uuid'],'raw_net':row['raw_net'],'expected_geometry':row['geometry'],'chunk_path':str(file.resolve()),'exact_original_chunk_sha256':sha(file)})
    assert hashlib.sha256(byid[old['exact_retained_CM_clock_uuid']]).hexdigest()==old['clock_native_chunk_sha256']
    for kind,items in [('via',d['vias']),('segment',d['tracks'])]:
        for q in items:
            uid=q['uuid'];assert uid not in byid
            if kind=='via':chunk='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.6f)\n\t\t(drill %.6f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],json.dumps(q['net']),json.dumps(uid))
            else:chunk='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*q['a'],*q['b'],q['w'],json.dumps(q['layer']),json.dumps(q['net']),json.dumps(uid))
            ast=parse(chunk);assert atom(ast,'net')==q['net'] and atom(ast,'uuid')==uid
            file=OUT/(uid+'.'+kind+'-chunk');file.write_text(chunk,encoding='utf-8',newline='');adds.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_path':str(file.resolve()),'chunk_sha256':sha(file)})
    (OUT/'protected-screen.json').write_text(json.dumps({'errors':errors,'pairs':pairs,'excluded_R9_replacement_UUIDs':sorted(EXCLUDED)},indent=2)+'\n')
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'SCOPED_IO3_REPLACEMENT_NATIVE_CHUNKS_WITH_PROTECTED_SCREEN','model_sha256':sha(model),'parent_native_board_sha256':sha(native),'delete_rows':delete,'add_rows':adds,
        'exact_retained_CM_clock_uuid':old['exact_retained_CM_clock_uuid'],'exact_retained_CM_clock_chunk_sha256':old['clock_native_chunk_sha256'],
        'required_new_via_native_postfill_flash':['F.Cu','In1.Cu'],'protected_R7_discrete_source_sha256':sha(r7/'proposed-discrete.pkl'),'protected_R7_zone_source_sha256':sha(r7/'proposed-zones.pkl'),
        'protected_screen_PASS':not errors,'protected_screen_error_count':len(errors),'protected_screen_sha256':sha(OUT/'protected-screen.json'),
        'R9_four_new_replacement_planes_not_screened':True,'IO3_source_host_pass':True,'full_all_outside_contacts_current_native':'OPEN','guarded_antipad_normalization':'OPEN','board_written':False,'native_jobs':0},indent=2)+'\n')
    print('IO3_NATIVE_SCOPE_PROTECTED_SCREEN',len(errors),sha(OUT/'receipt.json'),errors[:8],flush=True)
if __name__=='__main__':main()
