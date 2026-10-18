"""Bind passing actual-R299 route checks to the original frozen chunk bytes."""
import hashlib, json, runpy, shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ns=runpy.run_path(str(HERE/'audit_and_stage_actual_R299_routes_r1.py'))
K=ns['K'];OLD=ns['OLD'];SOURCE=ns['SOURCE'];sha=ns['sha'];L=ns['L']
OUT=HERE/'actual-R299-original-frozen-R310-candidate-r2'

def main():
    assert not OUT.exists();OUT.mkdir()
    first=HERE/'actual-R299-R310-R315-audit-and-candidate-r1'
    r=json.loads((first/'receipt.json').read_bytes());assert r['selected_new_tracks']==3
    groups=json.loads((first/'route-group-audit.json').read_bytes())
    assert {x['name'] for x in groups if x['host_gate']=='PASS'}=={'R310-1','R310-13'}
    original=OLD/'short-ESD-ground-and-watchdog-exact-current-native-add-only-r310/minimal-exact-ground-watchdog-native-add-manifest.json'
    assert sha(original)=='e5370fbefa8dcf3c9584e799c7684ebef95043632ac495278044dc77b0614c40'
    manifest=json.loads(original.read_bytes());assert len(manifest['operations'])==3
    raw=SOURCE.read_bytes();assert sha(SOURCE)==manifest['baseline_SHA256'];iv=K.C.inventory(raw)
    selected={x['UUID']:Path(x['file']).read_bytes() for x in json.loads((first/'native-add-only-manifest.json').read_bytes())['operations']}
    adds={};ops=[]
    for op in manifest['operations']:
        uid=op['UUID'];chunk=Path(op['file']).read_bytes();assert hashlib.sha256(chunk).hexdigest()==op['SHA256']
        before=K.A.G.parse(uid,selected[uid],{});exact=K.A.G.parse(uid,chunk,{})
        assert before==exact and uid not in iv[3]
        adds[uid]=chunk;p=OUT/('add-'+uid+'.native-chunk');p.write_bytes(chunk)
        ops.append({**op,'file':str(p),'actual_R299_host_requalification_receipt':str(first/'receipt.json'),'actual_R299_host_requalification_receipt_SHA256':sha(first/'receipt.json')})
    at=raw.rfind(b')');addition=b''.join(adds.values());candidate=raw[:at]+addition+raw[at:]
    after=K.C.inventory(candidate)
    assert set(after[3])==set(iv[3])|set(adds) and all(after[3][u]==ch for u,ch in iv[3].items())
    assert candidate[:at]+candidate[at+len(addition):]==raw
    dest=OUT/'candidate';dest.mkdir();board=dest/'board.kicad_pcb';board.write_bytes(candidate)
    for item in SOURCE.parent.iterdir():
        if item.name=='board.kicad_pcb' or item.name.endswith('.lck'):continue
        if item.is_dir():shutil.copytree(item,dest/item.name)
        else:shutil.copy2(item,dest/item.name)
    assert sha(board)=='663ff51190dc59c52a21baf99f5dfed2a29a7ece15bc8839b5d60d68e28138d0'
    (OUT/'native-add-only-manifest.json').write_text(json.dumps({**manifest,'operations':ops,'requalified_actual_full_R299_geometry_source_and_rules':True,'native_AFTER':'OPEN'},indent=1)+'\n')
    receipt={'status':'ORIGINAL_FROZEN_R310_BYTES_REBOUND_TO_ACTUAL_FULL_R299_PASS_NATIVE_AFTER_OPEN','board_file':str(board),'board_SHA256':sha(board),'tracks_added':3,'vias_added':0,'deletions':0,'all98030_original_chunks_literal':True,'all_original_header_tail_literal':True,'all_three_new_chunks_exact_frozen_R310_bytes':True,'parsed_new_geometry_identical_to_completed_actual_R299_audit':True,'actual_host_requalification_receipt_SHA256':sha(first/'receipt.json'),'original_manifest_SHA256':sha(original),'new_manifest_SHA256':sha(OUT/'native-add-only-manifest.json'),'native_jobs':0,'adopted':False,'manufacturing_ready':False,'native_AFTER_full_refill_contacts_masks_reference_DRC_current_ESD_watchdogtiming_SI':'OPEN','inputs_SHA256':{str(p):sha(p) for p in (Path(__file__),SOURCE,first/'receipt.json',first/'native-add-only-manifest.json',original)}}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps(receipt,indent=1))

if __name__=='__main__':main()
