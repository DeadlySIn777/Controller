"""Reproduce corrected AUX r4 candidate and B-cap r4 exact operation recipe.

Frozen r2/r3 geometry is reused. Net tokens and deterministic added UUIDs are
regenerated from the unique exact frozen source registry. Existing target
outputs must match byte-for-byte; they are never overwritten or adopted.
"""
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import net_identity_exact as N
P,G,S,C=N.P,N.P.G,N.P.S,N.P.C

def verify_or_write(path,raw):
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Existing frozen output differs '+str(path))
    else:path.write_bytes(raw)

def main():
    raw=G.SOURCE.read_bytes();identities=N.SourceNets(raw)
    if C.sha(raw)!='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab':raise ValueError('Source identity differs')
    now=C.inventory(raw);old=C.inventory(S.overlay_tool.base.BASE.read_bytes())
    frozen=json.loads((HERE/'aux-power-escape-r2.json').read_text())
    removes=set(frozen['owned_power_items'])|set(frozen['delete_ILIM_items']);restores=set(frozen['restore_original_DVDT_items'])
    additions={}
    for path in frozen['proposal']['paths']:
        for a,b in zip(path['points_mm'],path['points_mm'][1:]):
            uid,ch=identities.serial_segment(path['net'],path['layer'],a,b,path['width_mm']);additions[uid]=ch
    candidate=now[0]+b''.join(ch for ch in now[1] if C.pcbtext.chunk_uuid(ch) not in removes)+b''.join(old[4][uid] for uid in sorted(restores))+b''.join(additions.values())+now[2]
    verdict=identities.assert_no_collisions(candidate)
    if verdict['raw_net_count']!=2384:raise ValueError('Native net count changed')
    verify_or_write(HERE/'aux-power-escape-r4-exact-native-nets-host-only.kicad_pcb',candidate)
    cap=json.loads((HERE/'aux-cap-bside-r4-exact-native-nets.json').read_text())
    for path in cap['proposal']['routes']:
        if path['raw_native_net']!=identities.raw(path['net']):raise ValueError('Raw cap net identity differs')
        generated=[identities.serial_segment(path['net'],path['layer'],a,b,path['width_mm']) for a,b in zip(path['points_mm'],path['points_mm'][1:])]
        if [uid for uid,ch in generated]!=path['new_items']:raise ValueError('Cap UUID recipe differs')
        for (uid,ch),serialized in zip(generated,path['serialized_new_chunks']):
            if uid!=serialized['uuid'] or C.sha(ch)!=serialized['sha256'] or ch.decode()!=serialized['chunk']:raise ValueError('Cap serialized chunk differs')
    print(json.dumps({'candidate_sha256':C.sha(candidate),'raw_native_net_identity':verdict,'cap_recipe_exact':True,'native_jobs':0,'gpu_jobs':0}))
if __name__=='__main__':main()
