"""Compose only the field agent's pinned source/owned-copper operations.

Power polygons are deliberately held until their full contact/current checks.
The result is a partial review artifact, never an adoption candidate.
"""
import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
import native_pose_signal_contract as H
C=H.C
OUT=HERE/'combined-owned-host-r1'
PINS={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p,h=None):
    p=Path(p).resolve();raw=p.read_bytes();actual=sha(raw)
    if h and actual!=h:raise ValueError('Pinned owned recipe input changed '+str(p))
    PINS[str(p)]=actual;return raw
def chunk(row):return read(row['path'],row.get('chunk_sha256',row.get('sha256',row.get('after_sha256'))))
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh owned-operation directory required')
    read(Path(__file__));parent=HERE/'cap-reset-native-r4';pr=json.loads(read(parent/'receipt.json'))
    if pr['verdict']!='PASS_SOURCE_NATIVE_API_ONLY' or not pr['all13_added_vias_actual_six_annuli']:raise ValueError('Parent native API proof not clean')
    original=read(parent/'cap-reset-host-only.kicad_pcb',pr['candidate_sha256']);iv=C.inventory(original)
    r=json.loads(read(HERE/'field-power/candidate-recipe-r1/receipt.json'))
    source=json.loads(read(r['authoritative_six_part_combined_source']['native_receipt']['path'],r['authoritative_six_part_combined_source']['native_receipt']['sha256']))
    if source['verdict']!='PASS' or r['exact_existing_pad_net_moves']!=14 or r['raw_native_net_collision_count']:raise ValueError('Combined source or exact field recipe rejected')
    read(r['authoritative_six_part_combined_source']['fresh_netlist']['path'],r['authoritative_six_part_combined_source']['fresh_netlist']['sha256'])
    old=read(r['original_board']['path'],r['original_board']['sha256']);oi=C.inventory(old);replacements={};additions={};removed=set();roles={}
    for row in r['existing_footprint_replacements']:
        u=row['uuid'];ch=chunk(row)
        if sha(iv[3][u])!=row['before_sha256'] or iv[3][u]!=oi[3][u] or C.pcbtext.chunk_uuid(ch)!=u:raise ValueError('Owned old field footprint changed')
        replacements[u]=ch;roles[u]='EXACT_OLD_PAD_NET_ONLY'
    for row in r['new_field_footprint_additions']:
        u=row['uuid'];ch=chunk(row)
        if u in iv[3] or C.pcbtext.chunk_uuid(ch)!=u or C.pcbtext.chunk_kind(ch)!='footprint':raise ValueError('New field footprint collision/type')
        additions[u]=ch;roles[u]='SOURCE_BOUND_NEW_FIELD_PART'
    for row in r['private_net_only_replacements']:
        u=row['uuid'];ch=chunk(row);before=iv[4][u]
        if sha(before)!=row['before_sha256'] or before!=oi[4][u]:raise ValueError('Private copper baseline changed')
        expected=before.replace(('(net "'+row['old_raw_net']+'")').encode(),('(net "'+row['new_raw_net']+'")').encode())
        if ch!=expected or before==ch or C.pcbtext.chunk_uuid(ch)!=u:raise ValueError('Private retag changes geometry or unrelated attributes')
        replacements[u]=ch;roles[u]='PRIVATE_NATIVE_NET_ONLY'
    cuts=r['owned_pad_separation'];read(cuts['receipt']['path'],cuts['receipt']['sha256'])
    for row in cuts['rows']:
        u=row['uuid']
        if u in replacements or sha(iv[4][u])!=row['old_chunk_sha256'] or iv[4][u]!=oi[4][u]:raise ValueError('Overlapping/stale old field cut')
        segments=row['replacement_segments']
        if len(segments)>1:raise ValueError('Unexpected multi-item owned cut')
        if not segments:removed.add(u);roles[u]='OWNED_PAD_SEPARATION_REMOVAL'
        else:
            ch=chunk(segments[0])
            if C.pcbtext.chunk_uuid(ch)!=u:raise ValueError('Trimmed segment must retain UUID')
            replacements[u]=ch;roles[u]='OWNED_PAD_SEPARATION_TRIM'
    for row in r['new_local_segment_additions']:
        u=row['uuid'];ch=chunk(row)
        if u in additions or u in iv[3] or C.pcbtext.chunk_uuid(ch)!=u or C.pcbtext.chunk_kind(ch)!='segment':raise ValueError('New field segment collision/type')
        additions[u]=ch;roles[u]='SOURCE_BOUND_LOCAL_FANOUT'
    if len(removed)!=24 or len(replacements)!=75 or len(additions)!=42:raise ValueError('Unexpected exact field operation counts')
    wanted=iv[0]+b''.join(replacements.get(C.pcbtext.chunk_uuid(ch),ch) for ch in iv[1] if C.pcbtext.chunk_uuid(ch) not in removed)+b''.join(additions.values())+iv[2];ni=C.inventory(wanted)
    if ni[0]!=iv[0] or ni[2]!=iv[2] or any(ni[3].get(u)!=ch for u,ch in iv[3].items() if u not in set(replacements)|removed):raise ValueError('Unowned whole-board entity changed')
    names=H.N.SourceNets(wanted);names.assert_chunks(ni[4]);rawproof=names.assert_no_collisions(wanted)
    for p,h in PINS.items():
        if sha(Path(p).read_bytes())!=h:raise ValueError('Frozen operation input changed '+p)
    OUT.mkdir();candidate=OUT/'field-source-local-partial.kicad_pcb';candidate.write_bytes(wanted);read(candidate)
    write('construction.json',{'schema':'exact-combined-owned-operations-host-r1','verdict':'PASS_EXACT_FIELD_OPERATION_RECONSTRUCTION_ONLY','parent_candidate_sha256':sha(original),'partial_candidate_sha256':sha(wanted),'raw_native_net_identity':rawproof,'operations':[{'uuid':u,'role':roles[u],'before_sha256':sha(iv[3][u]) if u in iv[3] else None,'after_sha256':sha(ni[3][u]) if u in ni[3] else None} for u in sorted(roles)],'unowned_whole_board_entities_preserved':True,'partial_components':len([ch for ch in ni[3].values() if C.pcbtext.chunk_kind(ch)=='footprint']),'authoritative_source_components':2723,'source_completion_open':['Add source-bound C11094 footprint','Apply exact approved L11001/C11061 Value+MPN source property pairs'],'layout_completion_open':['Full field supply/return/PG/output copper','Joint SBC/CORE/control/cap changes','Plane contact restoration and current/thermal/drop checks','Both r07/r06 native no-loss and full DRC','Reset length/edge/return electrical review'],'prospective_power_polygons_added':0,'native_board_jobs':0,'input_hashes':PINS,'adopted':False,'manufacturing_ready':False})
    print(json.dumps({'verdict':'PASS_EXACT_FIELD_OPERATION_RECONSTRUCTION_ONLY','candidate_sha256':sha(wanted),'owned_replacements':len(replacements),'removed':len(removed),'additions':len(additions),'raw_native_net_identity':rawproof,'source_and_electrical_completion':'OPEN'}),flush=True)
if __name__=='__main__':main()
