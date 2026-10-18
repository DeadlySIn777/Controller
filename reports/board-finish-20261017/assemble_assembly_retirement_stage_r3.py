"""Compose the jointly proved CM OE drill/loop retirement, preserving all else."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
BASE=H/'combined-route-stage-r2'
OUT=H/'combined-route-stage-r3'
PACKET=H/'release-review/cm-oe-redundant-drill-r4/reviewable-retirement-packet.json'


def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()


def main():
    assert not OUT.exists()
    assert sha(PACKET)=='8a0ced0fba080939c384e15f91470fd2ba5e2cecbf913af4c70ee4b3a4195090'
    packet=json.loads(PACKET.read_bytes())
    parent=BASE/'native/board.kicad_pcb'
    assert sha(parent)==packet['native_current_parent_SHA256']=='9f075604a881b1e0d8cafe869e7389e246025ffbd37ec4dabb7cc5c1a7db225a'
    assert packet['inputs_unchanged'] and packet['final_whole_batch_simultaneously_proved']
    assert packet['retained_key_components_using_finite_overlap_only']==1
    assert packet['retained_native_keys']==157 and len(packet['retained_named_source_pads'])==10
    assert packet['no_new_or_reclassified_VIPPO'] and not packet['new_Cu'] and not packet['old_GND_or_power_reference_Cu_removed']
    helper=H.parent/'board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
    spec=importlib.util.spec_from_file_location('exact_pcbtext_stage3',helper)
    C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    pins={str(p):sha(p) for p in (Path(__file__),helper,PACKET,BASE/'all-copper-expected.json')}
    for path,digest in packet['input_SHA256'].items():
        assert sha(path)==digest; pins[path]=digest
    head,chunks,tail=C.split(parent.read_bytes())
    old={C.chunk_uuid(c):c for c in chunks if C.chunk_uuid(c)}
    expected=copy.deepcopy(json.loads((BASE/'all-copper-expected.json').read_bytes()))
    remove={}
    for op in packet['operations']:
        assert op['action']=='remove_exact_native_object'
        uid=op['UUID'];p=Path(op['file']);assert sha(p)==op['SHA256']
        assert old[uid]==p.read_bytes() and C.chunk_kind(old[uid])==op['kind']
        assert expected['copper'][uid]['raw_net']=='/motherboard_compute/CM_COMMS_OE_N'
        if op['kind']=='segment':assert expected['copper'][uid]['layer']=='B.Cu'
        remove[uid]=old[uid];pins[str(p)]=sha(p);del expected['copper'][uid]
    assert len(remove)==8 and sum(C.chunk_kind(c)=='via' for c in remove.values())==2
    new=head+b''.join(c for c in chunks if C.chunk_uuid(c) not in remove)+tail
    assert hashlib.sha256(new).hexdigest()==packet['counterfactual_source_SHA256_without_writing_PCB']
    nh,nc,nt=C.split(new);now={C.chunk_uuid(c):c for c in nc if C.chunk_uuid(c)}
    assert nh==head and nt==tail and set(now)==set(old)-set(remove)
    assert all(now[u]==c for u,c in old.items() if u not in remove)
    assert [c for c in chunks if C.chunk_kind(c)=='zone']==[c for c in nc if C.chunk_kind(c)=='zone']
    oldfiles={str(p.relative_to(BASE/'native')):sha(p) for p in (BASE/'native').rglob('*') if p.is_file() and p.suffix!='.lck'}
    OUT.mkdir();shutil.copytree(BASE/'native',OUT/'native',ignore=shutil.ignore_patterns('*.lck','__pycache__'))
    board=OUT/'native/board.kicad_pcb';board.write_bytes(new)
    assert all(sha(OUT/'native'/name)==v for name,v in oldfiles.items() if name!='board.kicad_pcb')
    assert all(sha(BASE/'native'/name)==v for name,v in oldfiles.items())
    assert all(sha(p)==v for p,v in pins.items())
    expected['board_sha256']=sha(board)
    (OUT/'all-copper-expected.json').write_text(json.dumps(expected,indent=1)+'\n')
    record={'status':'JOINT_ORDINARY_DRILL_AND_ORPHAN_LOOP_RETIREMENT_COMPOSED_NATIVE_AFTER_REQUIRED',
        'parent_SHA256':sha(parent),'candidate_SHA256':sha(board),'retired_via_UUIDs':packet['retired_via_UUIDs'],
        'retired_segment_UUIDs':[u for u,c in remove.items() if C.chunk_kind(c)=='segment'],
        'new_Cu_or_holes':0,'old_pad_footprint_mask_paste_zone_or_source_chunks_changed':0,
        'stale_zone_chunks':850,'new_join_count':'UNMEASURED',
        'physical_Cu_drill_union_identical':False,'joint_retained_finite_key_component_proof':str(PACKET),
        'in_pad_unregistered_drill_intersections_removed':2,'historical_VIPPO_scope_extended':False,
        'native_AFTER_masks_connectivity_source_reference_current_SI_assembly':'OPEN_REQUIRED',
        'earlier_stage1_running_input_untouched':True,'input_SHA256':pins,'parent_native_file_SHA256':oldfiles,
        'adopted':False,'manufacturing_ready':False}
    (OUT/'construction-receipt.json').write_text(json.dumps(record,indent=1)+'\n')
    print(json.dumps({k:record[k] for k in ('status','candidate_SHA256','in_pad_unregistered_drill_intersections_removed')}))


if __name__=='__main__':main()
