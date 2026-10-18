"""Lightweight exact parent ownership check; no geometry/numerical imports."""
import hashlib,json,re,sys
from pathlib import Path
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent.parent
sys.path.insert(0,str(REPORT))
import compose_additions as C
SOURCE=REPORT/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
PARENT=HERE.parent/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb'
SOURCE_SHA='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab'
PARENT_SHA='1beb9a2296ae451daed4b905383ccc5bd3ee083b3400cf5ef2e3ab2e7b7dae6b'
READS={}
def read(q):
    q=Path(q).resolve();data=q.read_bytes();READS[str(q)]=C.sha(data);return data
def scalar(ch,key):
    m=re.search(rb'\('+key.encode()+rb'\s+([-+.\deE]+)\)',ch)
    return float(m.group(1)) if m else None
def point(ch,key):
    m=re.search(rb'\('+key.encode()+rb'\s+([-+.\deE]+)\s+([-+.\deE]+)\)',ch)
    return [float(v) for v in m.groups()] if m else None
def bound(ch):
    k=C.pcbtext.chunk_kind(ch)
    if k=='via':a=point(ch,'at');r=scalar(ch,'size')/2;return [a[0]-r,a[1]-r,a[0]+r,a[1]+r]
    ps=[point(ch,n) for n in ('start','mid','end')];ps=[p for p in ps if p];r=(scalar(ch,'width') or 0)/2
    return [min(p[0] for p in ps)-r,min(p[1] for p in ps)-r,max(p[0] for p in ps)+r,max(p[1] for p in ps)+r] if ps else None
def main():
    out=HERE/'xf-parent-ownership-r1.json'
    if out.exists():raise ValueError('Fresh ownership receipt required')
    for q in (Path(__file__),Path(C.__file__),Path(C.pcbtext.__file__)):read(q)
    raw=read(SOURCE);parent_raw=read(PARENT)
    if C.sha(raw)!=SOURCE_SHA or C.sha(parent_raw)!=PARENT_SHA:raise ValueError('Frozen source/parent differs')
    source,parent=C.inventory(raw),C.inventory(parent_raw)
    graph=json.loads(read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']=='/motherboard_operator/XF_REQUEST_BUFFER')
    deleted=set(row['blocking_nets']['/motherboard_operator/XF_POWER_EN_GATED']['item_uuids'])|{'03e2bee6-9fdc-432c-aec5-8451c2ae9f07','080a7f61-2fe7-43cb-94fc-3bf3ecd6d0a9','32b7bab4-0c0d-4838-8724-aac6a6581d8c','52297947-2877-445e-9db1-32b6cd3535a7','dee6379c-951a-4cad-bf92-76d52e355bc4','fc2efac7-c002-4006-9117-e46fc1c0f1fe'}
    restored={r['uuid'] for r in row['missing_original_items']}-{'b1bde65e-ae89-4c0d-9caf-bf5d95d85600','a7198170-18ee-42dd-858d-061a27366980','3dadaf02-aad8-4d65-ad43-99096cf08382','5350f7dd-02b4-40be-8c0d-3fecb2805543','5568a777-bb7f-423f-a181-96f36d9376a1','139229ed-d773-4742-9431-88372f838056','2eb80f08-7b8b-4437-b5af-bdf8be4dc990'}
    owned_errors=[u for u in deleted if source[4].get(u)!=parent[4].get(u)]
    collision=sorted(restored&set(parent[4]))
    root_deleted=set(source[4])-set(parent[4]);root_added=set(parent[4])-set(source[4]);root_modified={u for u,ch in source[4].items() if u in parent[4] and ch!=parent[4][u]}
    changed=[];near=[]
    # This is nomination only. Exact polygon/refill/contact comparison is separate.
    roi=[293,96,328,112]
    for u in sorted(root_added|root_modified):
        ch=parent[4][u];b=bound(ch);m=re.search(rb'\(net\s+"([^"]*)"\)',ch)
        z={'uuid':u,'kind':C.pcbtext.chunk_kind(ch),'exact_serialized_body_bound_mm':b,'raw_net':m.group(1).decode() if m else None,'chunk_sha256':C.sha(ch)};changed.append(z)
        if b and not(b[2]+1<roi[0] or b[0]-1>roi[2] or b[3]+1<roi[1] or b[1]-1>roi[3]):near.append(z)
    cm=json.loads(read(HERE/'cm-coupled-returns-r4.json'));cm_raw=read(HERE/'cm-coupled-returns-r4-host-only.kicad_pcb');cm_inv=C.inventory(cm_raw)
    if C.sha(cm_raw)!='0bf996aeb28b21c0f2a84fa589c25bea6151d1114223fc98df21b47b28364426':raise ValueError('Frozen CM candidate differs')
    cm_added=set(cm_inv[4])-set(source[4]);cm_removed=set(source[4])-set(cm_inv[4])
    cm_errors=[u for u in cm_added if parent[4].get(u)!=cm_inv[4][u]]+[u for u in cm_removed if u in parent[4]]
    definitions_changed=[{'uuid':u,'kind':C.pcbtext.chunk_kind(ch),'source_definition_sha256':C.sha(C.definition(ch)),'parent_definition_sha256':C.sha(C.definition(parent[3][u])) if u in parent[3] else None} for u,ch in source[3].items() if C.pcbtext.chunk_kind(ch) not in ('segment','via','arc') and (u not in parent[3] or C.definition(parent[3][u])!=C.definition(ch))]
    for q,h in READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen input changed '+q)
    result={'schema':'xf-exact-parent-ownership-r1','verdict':'EXACT_OWNERSHIP_PASS_GEOMETRY_REFERENCE_OPEN' if not(owned_errors or collision or cm_errors) else 'EXACT_OWNERSHIP_FAIL','source_sha256':SOURCE_SHA,'parent_sha256':PARENT_SHA,'xf_deleted_owned':sorted(deleted),'xf_restored_original':sorted(restored),'xf_owned_chunk_changes_on_parent':owned_errors,'xf_restored_uuid_collisions':collision,'exact_cm_added_count':len(cm_added),'exact_cm_deleted_count':len(cm_removed),'exact_cm_parent_errors':cm_errors,'root_deleted_copper':sorted(root_deleted),'root_modified_copper':sorted(root_modified),'root_added_copper':changed,'root_changed_copper_near_xf_roi_plus_1mm':near,'nomination_roi_mm':roi,'root_changed_non_copper_definitions':definitions_changed,'read_files_sha256':READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'limits':['Exact source ownership/chunk comparison only; body bounds nominate potential interactions and are not clearance authority','Root changed footprint/pad/net definitions require matching-stem native provenance, not reuse of198b pads for full merged-parent qualification','All combined physical contacts, full-body root-connected reference and source fill component/contact cuts require full geometric audit and fresh merged native guards']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':result['verdict'],'owned_errors':len(owned_errors),'cm_errors':len(cm_errors),'near_xf':len(near),'changed_definitions':len(definitions_changed),'receipt':str(out)}),flush=True)
if __name__=='__main__':main()
