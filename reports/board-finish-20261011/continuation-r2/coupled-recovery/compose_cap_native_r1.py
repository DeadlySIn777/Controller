"""Compose exact198b plus attested native C11068 flip and r4 copper recipe.
No native call/source save. Unowned items and all project sources stay exact.
"""
import json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import net_identity_exact as N
import audit_aux_exact_raw as A
P,G,S,C=N.P,N.P.G,N.P.S,N.P.C
from shapely.ops import unary_union

def main():
    out=HERE/'aux-cap-native-composition-r1.json';target=HERE/'aux-cap-native-r1-host-only.kicad_pcb'
    if out.exists() or target.exists():raise ValueError('Distinct frozen output required')
    source=A.read(G.SOURCE);now=C.inventory(source);identity=N.SourceNets(source)
    if C.sha(source)!=A.SOURCE_SHA:raise ValueError('Exact198b source differs')
    recipe=json.loads(A.read(HERE/'aux-cap-bside-r4-exact-native-nets.json'));proposal=recipe['proposal']
    native_path=HERE.parent/'cap-native-r3/native-attestation.json';native=json.loads(A.read(native_path));chunk=A.read(native['output_chunk'])
    if native['verdict']!='NATIVE_FLIP_POSE_PAD_ATTESTATION_PASS' or C.sha(chunk)!=native['output_chunk_sha256']:raise ValueError('Native attestation/chunk differs')
    source_attest=[h for p,h in native['input_files'].items() if p.endswith('board.kicad_pcb')]
    if source_attest!=[A.SOURCE_SHA]:raise ValueError('Native source authority differs')
    fp=proposal['footprint_uuid']
    if native['owned_footprint_uuid']!=fp or C.pcbtext.chunk_uuid(chunk)!=fp:raise ValueError('Owned footprint UUID differs')
    if (native['actual_reference'],native['actual_value'],native['actual_layer'],native['actual_centre_mm'],native['actual_angle_degrees'])!=('C11068',proposal['value'],'B.Cu',proposal['target_pose']['xy_mm'],proposal['target_pose']['angle_degrees']):raise ValueError('Native footprint pose/value/layer differs')
    padproof=[]
    for actual,wanted in zip(native['pads'],proposal['expected_pads']):
        if (actual['uuid'],actual['num'],actual['net'],actual['at_mm'],actual['actual_layer'])!=(wanted['uuid'],wanted['num'],wanted['net'],wanted['at_mm'],'B.Cu'):raise ValueError('Actual native pad identity/pose/layer differs')
        actualbody=unary_union(S.poly(A.polys(actual['polygon_rings'])))
        expectedbody=unary_union(S.poly(wanted['layers']['B.Cu']))
        deviation=actualbody.hausdorff_distance(expectedbody)
        if deviation>.005:raise ValueError('Native pad polygon outside export-error bound')
        padproof.append({'uuid':actual['uuid'],'hausdorff_mm':deviation,'export_inside_error_bound_mm':.005,'actual_native_polygon_used_in_final_audit':True})
    removes=set(proposal['delete_copper_uuids']);added={}
    for route in proposal['routes']:
        if route['raw_native_net']!=identity.raw(route['net']):raise ValueError('Route raw native name differs')
        for row in route['serialized_new_chunks']:
            ch=row['chunk'].encode();uid=row['uuid']
            if C.sha(ch)!=row['sha256'] or C.pcbtext.chunk_uuid(ch)!=uid or S.overlay_tool.netname(ch)!=route['raw_native_net']:raise ValueError('Exact new serialized chunk differs')
            if uid in now[3] or uid in added:raise ValueError('New item UUID collision')
            added[uid]=ch
    if len(removes)!=17 or len(added)!=18:raise ValueError('Frozen recipe item count differs')
    candidate=now[0]+b''.join(chunk if C.pcbtext.chunk_uuid(ch)==fp else ch for ch in now[1] if C.pcbtext.chunk_uuid(ch) not in removes)+b''.join(added.values())+now[2]
    final=C.inventory(candidate);netproof=identity.assert_no_collisions(candidate);identity.assert_chunks(final[4])
    if netproof['raw_net_count']!=2384:raise ValueError('Raw native net count changed')
    if set(now[3])-set(final[3])!=removes or set(final[3])-set(now[3])!=set(added):raise ValueError('Owned UUID set differs')
    changed=[uid for uid,ch in now[3].items() if uid in final[3] and ch!=final[3][uid]]
    if changed!=[fp]:raise ValueError('Unowned source entity changed '+repr(changed))
    if now[0]!=final[0] or now[2]!=final[2]:raise ValueError('Board header/trailer changed')
    for uid,ch in now[3].items():
        if uid not in removes|{fp} and final[3][uid]!=ch:raise ValueError('Retained item byte identity differs')
    target.write_bytes(candidate)
    result={'schema':'aux-cap-native-composition-r1','verdict':'FROZEN_COMPLETE_CANDIDATE_NATIVE_MEASUREMENT_OPEN','candidate':str(target.resolve()),'candidate_sha256':C.sha(candidate),'source_sha256':A.SOURCE_SHA,'native_attestation_sha256':C.sha(native_path.read_bytes()),'native_footprint_chunk_sha256':C.sha(chunk),'raw_native_net_identity':netproof,'changed_existing_items':changed,'removed_owned_copper':sorted(removes),'added_owned_copper':sorted(added),'retained_entity_byte_count':len(now[3])-len(removes)-1,'actual_pad_polygon_comparison':padproof,'recipe_sha256':C.sha((HERE/'aux-cap-bside-r4-exact-native-nets.json').read_bytes()),'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Independent host audit using actual native pad polygons','Fresh full native refill/DRC/API partitions and complete dual native r06/live no-loss','Complete AUX current/drop/RTN/support/thermal and controlled-source electrical gates']}
    out.write_text(json.dumps(result,indent=1)+'\n')
    print(json.dumps({'candidate':str(target),'sha256':C.sha(candidate),'native_net_identity':netproof,'pad_polygons':padproof,'retained':result['retained_entity_byte_count']}))
if __name__=='__main__':main()
