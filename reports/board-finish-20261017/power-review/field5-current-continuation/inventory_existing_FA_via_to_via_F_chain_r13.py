"""Exact native finite-contact inventory for moving an existing FA F series chain."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
from collections import deque
import hashlib,importlib.util,json,pickle,sys
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';OUT=HERE/'existing-FA-via-to-via-F-chain-r13';NET='/motherboard_power_entry/FA_SHDN_CONTACT';A='19ec6624-3e58-4b0c-a2ed-0a6a44d2a584';B='85f79857-7bd1-4f7d-9337-7a9496d53b0a'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();model=ACTUAL/'actual-combined-full-after-model.pkl';gp=ACTUAL/'actual-combined-full-after-all-net-groups.pkl';base=ROOT/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';inputs={str(p):sha(p)for p in(model,gp,base,hp,Path(__file__))};assert sha(base)=='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca';g=pickle.loads(model.read_bytes());groups=pickle.loads(gp.read_bytes())[NET];allF=[q for xs in groups for q in xs if q['layer']=='F.Cu'];tree=STRtree([q['shape']for q in allF]);ia=next(i for i,q in enumerate(allF)if q['kind']=='via'and q['uuid']==A);ib=next(i for i,q in enumerate(allF)if q['kind']=='via'and q['uuid']==B);adj={i:{}for i in range(len(allF))}
    for i,q in enumerate(allF):
        for j in tree.query(q['shape'],predicate='intersects'):
            j=int(j)
            if j<=i:continue
            area=q['shape'].intersection(allF[j]['shape']).area
            if area>0:adj[i][j]=area;adj[j][i]=area
    prev={ia:None};queue=deque([ia])
    while queue and ib not in prev:
        i=queue.popleft()
        for j in sorted(adj[i]):
            if j not in prev:prev[j]=i;queue.append(j)
    assert ib in prev,'No actual finite same-layer F path between these existing ports';path=[];i=ib
    while i is not None:path.append(i);i=prev[i]
    path.reverse();tracks=[i for i in path if allF[i]['kind']=='track'];assert len(tracks)==len(path)-2;retired={allF[i]['uuid']for i in tracks};assert {'f231adb1-b5c9-422a-82eb-c6a859d26a93','21702822-e41c-488c-a23a-db6e3e94614d'}<=retired
    external=[];internal=[]
    for i in tracks:
        for j,area in adj[i].items():
            if allF[j]['kind']=='track'and allF[j]['uuid']in retired:
                if j>i:internal.append({'first':T.describe(allF[i]),'second':T.describe(allF[j]),'finite_overlap_mm2':area})
            else:external.append({'retired':T.describe(allF[i]),'external':T.describe(allF[j]),'actual_finite_overlap_mm2':area})
    extkeys={(q['external']['kind'],q['external']['uuid'])for q in external};pure=extkeys=={('via',A),('via',B)};sp=importlib.util.spec_from_file_location('pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H);index={H.chunk_uuid(c):c for c in H.split(base.read_bytes())[1]if H.chunk_uuid(c)};operations=[]
    for i in tracks:
        q=allF[i];t=next(t for t in g['tracks']if t['uuid']==q['uuid']);p=OUT/(q['uuid']+'-exact-stage3-retirement-chunk');p.write_bytes(index[q['uuid']]);operations.append({'UUID':q['uuid'],'actual_native_track_record':t,'exact_stage3_chunk_file':str(p),'exact_stage3_chunk_SHA256':sha(p)})
    vias=[]
    for uid in(A,B):
        v=next(v for v in g['vias']if v['uuid']==uid);assert set(v['flashed'])==set(K.LAYERS);p=OUT/(uid+'-exact-stage3-retained-via-chunk');p.write_bytes(index[uid]);vias.append(v|{'exact_stage3_chunk_file':str(p),'exact_stage3_chunk_SHA256':sha(p),'all6_actual_native_flashes':True})
    remaining=g|{'tracks':[t for t in g['tracks']if t['uuid']not in retired]};post=K.physical(remaining,NET,K.hole_context(remaining))[1];rootold=K.root(groups,'J11004','1');rootpost=K.root(post,'J11004','1');oldpads={q['ref']+'.'+q['pin']for q in rootold if q['kind']=='pad'};postpads={q['ref']+'.'+q['pin']for q in rootpost if q['kind']=='pad'};result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_F_CHAIN_HAS_ONLY_TWO_EXISTING_ALL6_BARREL_EXTERNAL_CONTACTS'if pure else'ACTUAL_F_CHAIN_HAS_ADDITIONAL_EXTERNAL_CONTACTS_REPLACEMENT_MUST_PRESERVE_ALL','input_sha256':inputs,'source_board':str(base),'source_board_SHA256':sha(base),'actual_finite_F_path_records':[T.describe(allF[i])for i in path],'exact_retirement_operations':operations,'retained_vias':vias,'all_positive_finite_external_contacts':external,'all_positive_finite_internal_contacts':internal,'external_contact_keys':[[a,b]for a,b in sorted(extkeys)],'pure_two_barrel_contact_boundary':pure,'old_J11004_1_source_pads':sorted(oldpads),'source_pads_lost_when_chain_removed_without_replacement':sorted(oldpads-postpads),'replacement_must_rejoin_two_actual_barrels_with_finite_all6_retention':True,'source_ground_reference_DRC_and_In3_replacement_route':'OPEN with routing agent; no source contact or shutdown function is waived','new_drills_needed_by_this_topology_substitution':0,'all_simultaneous_loads_and_fault_function_limits_unchanged':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};put('receipt.json',result);print(json.dumps({'status':result['status'],'tracks':len(tracks),'external_contacts':external,'pads_lost_without_replacement':result['source_pads_lost_when_chain_removed_without_replacement']}),flush=True)
if __name__=='__main__':main()
