"""Exact reversible AUX copper-replacement contract for native measurement."""
import hashlib,json,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import compose_additions as C
def sha(raw):return hashlib.sha256(raw).hexdigest()
def checked(p,h):
    raw=Path(p).read_bytes()
    if sha(raw)!=h:raise ValueError('Frozen construction input changed '+str(p))
    return raw
def construction_hashes(path):
    spec=json.loads(Path(path).read_bytes());pins=dict(spec['inputs']);pins[str(Path(path).resolve())]=sha(Path(path).read_bytes());pins[str(Path(__file__).resolve())]=sha(Path(__file__).read_bytes())
    for p,h in pins.items():checked(p,h)
    return pins
def segment(net,layer,a,b,width):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-coupled-r2/'+net+'/'+layer+'/'+repr((a,b,width))));f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    return uid,(f'\t(segment\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(width {f(width)})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
def validate_construction(path,candidate):
    spec=json.loads(Path(path).read_bytes());construction_hashes(path)
    if spec['schema']!='native-aux-recipe-r1':raise ValueError('Unknown construction schema')
    source=checked(spec['source']['path'],spec['source']['sha256']);old=checked(spec['original_r06']['path'],spec['original_r06']['sha256']);after=Path(candidate).read_bytes()
    audit=json.loads(checked(spec['audit']['path'],spec['audit']['sha256']));recipe=json.loads(checked(spec['recipe']['path'],spec['recipe']['sha256']))
    if sha(after)!=audit['candidate_sha256'] or sha(source)!=audit['source_sha256']:raise ValueError('Source/candidate audit identity mismatch')
    if audit['clearance_errors'] or audit['surviving_contact_losses'] or audit['pad_relationship_failures']:raise ValueError('Affected copper host audit failed')
    current,original,actual=C.inventory(source),C.inventory(old),C.inventory(after);removed=set(audit['deleted_items']);restored=set(audit['restored_original_items']);new={}
    for route in recipe['proposal']['paths']:
        for a,b in zip(route['points_mm'],route['points_mm'][1:]):
            uid,ch=segment(route['net'],route['layer'],a,b,route['width_mm']);new[uid]=ch
    if set(new)!=set(audit['new_items']):raise ValueError('Reconstructed path item set differs')
    restored_chunks={u:original[4][u] for u in restored}
    expected=current[0]+b''.join(ch for ch in current[1] if C.pcbtext.chunk_uuid(ch) not in removed)+b''.join(restored_chunks.values())+b''.join(new.values())+current[2]
    # Original constructor iterates its dictionaries in source/route order. The
    # native top-level item ordering can differ; every chunk and all noncopper
    # definitions must reproduce exactly with no extra/deleted entities.
    inv=C.inventory(expected)
    if actual[0]!=current[0] or actual[2]!=current[2] or actual[5]!=current[5] or actual[3]!=inv[3]:raise ValueError('Exact native copper recipe differs')
    return {'verdict':'PASS','evidence_class':'exact source/native copper replacement plus frozen independent host audit','candidate_sha256':sha(after),'removed_items':len(removed),'restored_items':len(restored),'new_segments':len(new),'noncopper_definitions_unchanged':True,'retained_native_entities_exact':True,'source_attributes_pad_nets_and_poses_unchanged':True,'native_refill_drc_connectivity':'OPEN','adopted':False}
