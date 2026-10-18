"""Extract intended native chunks only; preserve every other stage3 byte."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];NATIVE=HERE/'single-outer-real-corridor-native-r9';OUT=HERE/'single-outer-power-diagnostic-packet-r11';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();digest=lambda b:hashlib.sha256(b).hexdigest();sp=importlib.util.spec_from_file_location('pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
def parsed(blob):
    tokens=re.findall(rb'"(?:[^"\\]|\\.)*"|[()]|[^\s()]+',blob);stack=[];out=[]
    for t in tokens:
        if t==b'(':stack.append([])
        elif t==b')':
            node=stack.pop()
            if stack:stack[-1].append(node)
            else:out.append(node)
        else:stack[-1].append(t)
    assert not stack and len(out)==1;return out[0]
def profile(c):
    tree=parsed(c);assert tree[0]==b'zone';result=[]
    for row in tree[1:]:
        if row[0]in(b'polygon',b'filled_polygon'):continue
        if row[0]==b'fill':row=[row[0]]+[x for x in row[1:]if x!=b'yes']
        result.append(row)
    return result
def main():
    assert not OUT.exists();OUT.mkdir();d=json.loads((NATIVE/'input.json').read_text());check=json.loads((NATIVE/'native-roundtrip-receipt-r10.json').read_text());assert check['status']=='ALL_SINGLE_OUTER_NATIVE_INTEGER_CONTOURS_HOLES_LOAD_SAVE_RELOAD_PASS_NO_FILL';base=Path(d['stage3_board']);assert sha(base)==d['stage3_board_SHA256'];raw=base.read_bytes();head,oldchunks,tail=H.split(raw);index={H.chunk_uuid(c):c for c in oldchunks if H.chunk_uuid(c)};native={H.chunk_uuid(c):c for c in H.split(Path(d['minimal_native_output']).read_bytes())[1]if H.chunk_uuid(c)};expected={H.chunk_uuid(c):c for c in H.split(Path(d['minimal_native_input']).read_bytes())[1]if H.chunk_uuid(c)};ops=[];replacements={};adds={}
    for row in d['zones']:
        uid=row['uuid'];after=native[uid];assert profile(after)==profile(expected[uid]);assert not H._depth2_blocks(after,b'filled_polygon');assert len(H._depth2_blocks(after,b'polygon'))==len(row['polygons_integer_IU'][0]);ap=OUT/(uid+'-after.exact-native-zone-chunk');ap.write_bytes(after);op={'action':row['action'],'UUID':uid,'family_original_UUID':row['family_original_UUID'],'template_UUID':row['template_UUID'],'after_file':str(ap),'after_SHA256':sha(ap),'native_single_outer':True,'native_hole_count':len(row['polygons_integer_IU'][0])-1,'all_non_geometry_profile_tokens_exact_after_fill_cache_flag_removed':True}
        if row['action']=='replace':
            before=index[uid];assert digest(before)==row['before_chunk_SHA256'];bp=OUT/(uid+'-before.exact-native-zone-chunk');bp.write_bytes(before);op.update(before_file=str(bp),before_SHA256=sha(bp));replacements[uid]=after
        else:assert uid not in index;adds[uid]=after
        ops.append(op)
    composed=head+b''.join(replacements.get(H.chunk_uuid(c),c)for c in oldchunks)+b''.join(adds.values())+tail;ch,cc,ct=H.split(composed);ni={H.chunk_uuid(c):c for c in cc if H.chunk_uuid(c)};assert ch==head and ct==tail;unchanged=set(index)-set(replacements);assert all(ni[u]==index[u]for u in unchanged);assert set(ni)==set(index)|set(adds);assert ni[d['original_FIELD5_zone_UUID_and_chunk_preserved']]==index[d['original_FIELD5_zone_UUID_and_chunk_preserved']];board=OUT/'stage3-plus-FIELD5-diagnostic-only.kicad_pcb';board.write_bytes(composed)
    files=[base,NATIVE/'input.json',NATIVE/'native-roundtrip-receipt-r10.json',Path(d['minimal_native_output']),HERE/'separate-real-corridor-zone-host-qualification-r7/receipt.json',HERE/'prospective-real-corridor-two-level-current-r7/receipt.json',hp,Path(__file__)];r={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXACT_STAGE3_SPARSE_SINGLE_OUTER_ZONE_DIAGNOSTIC_PACKET_NATIVE_AFTER_AND_BOTH_RAIL_CURRENT_OPEN','input_sha256':{str(p):sha(p)for p in files},'parent_board':str(base),'parent_SHA256':sha(base),'diagnostic_board':str(board),'diagnostic_board_SHA256':sha(board),'operations':ops,'replaced_existing_FG_zones':len(replacements),'new_FIELD5_zones':sum(x['template_UUID']==d['original_FIELD5_zone_UUID_and_chunk_preserved']for x in ops),'new_FG_split_fragment_zones':sum(x['action']=='add'and x['template_UUID']!=d['original_FIELD5_zone_UUID_and_chunk_preserved']for x in ops),'all_other_existing_UUID_chunks_exact':len(unchanged),'original_FIELD5_source_chunk_byte_identical':True,'all_original_tracks_vias_pads_footprints_board_outline_rules_settings_limits_and_stackup_bytes_exact':True,'new_drills':0,'no_ordinary_VIPPO_change':True,'full_native_fill_DRC_positive_retention_negative_effect_minimum_width_source_contacts_references_SI_and_signed_FIELD5_and_FG_return_current_thermal_voltage_budget':'OPEN; diagnostic packet only','all12_motor_outlet_and_other_planning_loads_unchanged':True,'native_fill_called':False,'adopted':False,'manufacturing_ready':False};(OUT/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'board_SHA256':sha(board),'ops':len(ops),'untouched_chunks':len(unchanged)}))
if __name__=='__main__':main()
