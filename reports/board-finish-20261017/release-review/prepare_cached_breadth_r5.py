"""Derive the wider search from frozen r4, reusing exact spatial records."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
src=H/'audit_owned_cap_bridges_r4.py';dest=H/'audit_owned_cap_bridges_r5.py'
assert not dest.exists()
s=src.read_text()
s=s.replace("OUT=HERE/'owned-cap-body-bridges-r4'","OUT=HERE/'owned-cap-body-bridges-r5'",1)
a=s.index("    seed=HERE/'inherited-port-cap-diagnostic-r1/receipt.json'")
b=s.index("    put('remaining-group-census.json',census)",a)
s=s[:a]+"    candidates=[{**c,'previous_r2_candidate_index':i} for i,c in enumerate(candidates)]\n"+s[b:]
a=s.index('    # Build actual geometry spatial indices only; no connectivity graph.')
b=s.index('    trees={ly:STRtree',a)
replacement='''    # Reuse the exact frozen r4 physical spatial records; no graph rebuild.
    cache_dir=HERE/'owned-cap-body-bridges-r4'
    binding_file=cache_dir/'spatial-record-cache-binding.json'
    cachefile=cache_dir/'exact-host-spatial-records.pkl'
    r4_receipt=cache_dir/'receipt.json'
    binding=json.loads(binding_file.read_text())
    for f in (binding_file,cachefile,r4_receipt,HERE/'audit_owned_cap_bridges_r4.py'):
        pins[str(f)]=sha(f)
    assert pins[str(cachefile)]==binding['SHA256']
    assert binding['actual_model_SHA256']==pins[str(files[0])]
    assert binding['current_peer_SHA256']==pins[str(files[3])]
    assert binding['executed_source_SHA256']==pins[str(HERE/'audit_owned_cap_bridges_r4.py')]
    assert json.loads(r4_receipt.read_text())['inputs_unchanged']
    records,holes=pickle.loads(cachefile.read_bytes())
    old=json.loads(files[6].read_text())['copper'];current=json.loads(files[4].read_text())['copper'];peer=[]
    for uid,r in current.items():
        if uid in old and {k:v for k,v in r.items() if k!='chunk_sha256'}=={k:v for k,v in old[uid].items() if k!='chunk_sha256'}:continue
        if r['kind']=='segment':
            a=[v/1e6 for v in r['start_IU']];b=[v/1e6 for v in r['end_IU']]
            peer.append((norm(r['raw_net']),r['layer'],outer(LineString([a,b]),r['width_IU']/2e6)))
'''
s=s[:a]+replacement+s[b:]
# R4's qualified MOTOR bridge is retained as a peer and provisional group edge.
marker="    gpu_trials=0\n"
assert s.count(marker)==1
replacement='''    frozen_packet=HERE/'owned-cap-body-bridges-r4/independent-current-source-verification/exact-reviewed-additive-packet.json'
    pins[str(frozen_packet)]=sha(frozen_packet)
    for q in json.loads(frozen_packet.read_text())['eligible_new_nonredundant_packets']:
        wf=Path(q['body_WKB_file']);pins[str(wf)]=sha(wf)
        selected.append({**q,'shape':shapely.from_wkb(wf.read_bytes())})
        a,b=q['actual_required_group_edge'];net=q['net'];parents[find((net,a))]=find((net,b))
    gpu_trials=0
'''
s=s.replace(marker,replacement,1)
s=s.replace("'R299-broad-existing-layer-bridge:'+str(ci)+':'+str(j)","'R299-broad-existing-layer-bridge-r5:'+str(ci)+':'+str(j)",1)
dest.write_text(s)
(H/'cached-breadth-r5-source-derivation.json').write_text(json.dumps({'parent_source':str(src),'parent_SHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'derived_source':str(dest),'derived_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'changes':['all435 cached-source endpoint pairs','reuse exact source-bound physical spatial records without graph rebuild','retain independently reviewed MOTOR bridge as same-layer peer and prospective group edge','new deterministic UUID namespace'],'executed_native_jobs':0},indent=1)+'\n')
print(str(dest))
