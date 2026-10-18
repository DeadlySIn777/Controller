"""Reconstruct exactly one attested footprint move and two owned copper recipes."""
import hashlib,json,re,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE/'coupled-recovery'))
import compose_additions as C
import net_identity_exact as N
from shapely.geometry import LineString,Point
from shapely.ops import unary_union

def sha(raw):return hashlib.sha256(raw).hexdigest()
def checked(p,h):
    raw=Path(p).read_bytes()
    if sha(raw)!=h:raise ValueError('Frozen constructor input changed: '+str(p))
    return raw
def construction_hashes(path):
    spec=json.loads(Path(path).read_bytes());pins=dict(spec['inputs'])
    pins[str(Path(path).resolve())]=sha(Path(path).read_bytes())
    pins[str(Path(__file__).resolve())]=sha(Path(__file__).read_bytes())
    for p,h in pins.items():checked(p,h)
    return pins
def signal_segment(net,layer,a,b):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-escape-r2/'+net+'/'+layer+'/'+repr((a,b,.2))))
    f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    return uid,(f'\t(segment\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(width 0.2)\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
def signal_via(net,at):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-escape-r2/'+net+'/via/'+repr(at)))
    f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    return uid,(f'\t(via\n\t\t(at {f(at[0])} {f(at[1])})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
def ident(spec,key):return checked(spec[key]['path'],spec[key]['sha256'])
def footprint_map(inv):return {u:c for u,c in inv[3].items() if C.pcbtext.chunk_kind(c)=='footprint'}
def body(chunk):
    text=chunk.decode();kind=C.pcbtext.chunk_kind(chunk)
    xy=lambda k:[float(v) for v in re.search(r'\('+k+r'\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)',text).groups()]
    if kind=='segment':return LineString([xy('start'),xy('end')]).buffer(float(re.search(r'\(width\s+([-+0-9.eE]+)',text)[1])/2,resolution=64)
    if kind=='via':return Point(xy('at')).buffer(float(re.search(r'\(size\s+([-+0-9.eE]+)',text)[1])/2,resolution=64)
    raise ValueError('Unsupported owned copper geometry: '+kind)

def reconstruct(spec):
    source=ident(spec,'source');current=C.inventory(source);names=N.SourceNets(source)
    cap=json.loads(ident(spec,'cap_audit'));comp=json.loads(ident(spec,'cap_composition'));recipe=json.loads(ident(spec,'cap_recipe'))
    att=json.loads(ident(spec,'native_attestation'));fp=ident(spec,'native_footprint')
    escape=json.loads(ident(spec,'signal_audit'));plan=json.loads(ident(spec,'signal_plan'))
    if cap['verdict']!='HOST_COMPLETE_CANDIDATE_AUDIT_PASS_NATIVE_ELECTRICAL_OPEN':raise ValueError('Cap audit rejected')
    for key in ('pad_relationship_failures','surviving_contact_losses','clearance_errors','moved_pad_clearance_errors','courtyard_overlap'):
        if cap[key]:raise ValueError('Cap independent audit errors: '+key)
    if escape['verdict']!='HOST_READY_NATIVE_ELECTRICAL_OPEN' or escape['geometry_errors'] or escape['existing_plane_contacts_removed']:raise ValueError('Signal independent audit rejected')
    if att['verdict']!='NATIVE_FLIP_POSE_PAD_ATTESTATION_PASS' or sha(fp)!=att['output_chunk_sha256']:raise ValueError('Exact native flip attestation rejected')
    if cap['source_sha256']!=sha(source) or escape['board_source_sha256']!=sha(source):raise ValueError('Recipes have different physical baselines')
    p=recipe['proposal'];owned=p['footprint_uuid'];removed=set(p['delete_copper_uuids']);new={}
    if owned!='f2a18ff9-2826-4c67-94dc-d26f5bb1906b' or b'(property "Reference" "C11068"' not in current[3][owned]:raise ValueError('Unauthorized footprint move')
    for route in p['routes']:
        for a,b in zip(route['points_mm'],route['points_mm'][1:]):
            u,ch=names.serial_segment(route['net'],route['layer'],a,b,route['width_mm']);new[u]=ch
    audited={r['uuid']:r['exact_serialized_chunk'].encode() for r in cap['added_items']}
    if new!=audited or removed!={r['uuid'] for r in cap['deleted_items']}:raise ValueError('Cap operation recipe reconstruction differs')
    capnew=dict(new)
    rows=[r for r in plan['results'] if r['paths']]
    if len(rows)!=1:raise ValueError('One signal path expected')
    row=rows[0];route=row['paths'][0];net=names.raw(row['net']);signal={}
    for layer,points in [(route['source_escape']['outer_layer'],route['source_escape']['outer_path']['points_mm']),('In3.Cu',route['inner_path']['points_mm']),(route['target_escape']['outer_layer'],route['target_escape']['outer_path']['points_mm'])]:
        for a,b in zip(points,points[1:]):u,ch=signal_segment(net,layer,a,b);signal[u]=ch
    for via in route['new_signal_vias']:u,ch=signal_via(net,via['at']);signal[u]=ch
    if signal!={r['uuid']:r['raw_chunk'].encode() for r in escape['new_items']}:raise ValueError('Signal path reconstruction differs')
    if (set(new)|removed|{owned})&set(signal) or (set(new)|set(signal))&set(current[3]):raise ValueError('Operation UUID collision')
    caponly=current[0]+b''.join(fp if C.pcbtext.chunk_uuid(ch)==owned else ch for ch in current[1] if C.pcbtext.chunk_uuid(ch) not in removed)+b''.join(new.values())+current[2]
    if C.inventory(caponly)[3]!=C.inventory(ident(spec,'cap_candidate'))[3] or sha(ident(spec,'cap_candidate'))!=comp['candidate_sha256']:raise ValueError('Cap complete board differs from audited native recipe')
    # Changes are on disjoint physical regions. Include removed holes/tracks and
    # both old/new footprint extents, rather than only the new route centrelines.
    capbody=unary_union([body(c) for c in capnew.values()]+[body(current[4][u]) for u in removed]+[Point(318.788,52.6).buffer(3),Point(318.8,51.7).buffer(3)])
    signalbody=unary_union([body(c) for c in signal.values()])
    separation=capbody.distance(signalbody)
    if separation<2:raise ValueError('Independent regional audits do not prove combined clearance')
    if any(v['existing_return']['return_via_uuid'] in removed for v in escape['new_items'] if v['kind']=='via'):raise ValueError('Cap recipe removes signal return')
    new.update(signal)
    data=current[0]+b''.join(fp if C.pcbtext.chunk_uuid(ch)==owned else ch for ch in current[1] if C.pcbtext.chunk_uuid(ch) not in removed)+b''.join(new.values())+current[2]
    exact=C.inventory(data);r07=C.inventory(ident(spec,'r07'))
    if footprint_map(r07)!=footprint_map(current):raise ValueError('Measurement r07 differs from recipe footprint baseline')
    wantedfp=footprint_map(current);wantedfp[owned]=fp
    if footprint_map(exact)!=wantedfp or exact[0]!=current[0] or exact[2]!=current[2]:raise ValueError('Owned exact native footprint contract differs')
    if any(exact[3].get(u)!=ch for u,ch in current[3].items() if u not in removed|{owned}):raise ValueError('Unowned native entity changed')
    names.assert_chunks(exact[4]);rawproof=names.assert_no_collisions(data)
    return data,{'verdict':'PASS','evidence_class':'exact owned native footprint and copper reconstruction; independent actual-shape regional audits','source_sha256':sha(source),'candidate_sha256':sha(data),'removed_items':len(removed),'new_segments':sum(C.pcbtext.chunk_kind(c)=='segment' for c in new.values()),'new_vias':sum(C.pcbtext.chunk_kind(c)=='via' for c in new.values()),'owned_footprint_changes':[owned],'retained_footprints_exact_except_attested_owned_move':True,'retained_native_entities_exact':True,'raw_native_net_identity':rawproof,'combined_regional_copper_separation_mm':separation,'native_refill_drc_connectivity':'OPEN','adopted':False}
def validate_construction(path,candidate):
    spec=json.loads(Path(path).read_bytes());construction_hashes(path)
    if spec['schema']!='native-cap-and-signal-r1':raise ValueError('Unknown owned native constructor schema')
    expected,proof=reconstruct(spec);actual=Path(candidate).read_bytes()
    if actual!=expected:raise ValueError('Candidate differs from exact reconstructed native operations')
    if sha(actual)!=spec['candidate_sha256']:raise ValueError('Frozen candidate identity differs')
    return proof
