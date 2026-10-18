"""Independent current-source retention and staged-group redundancy check."""
from pathlib import Path
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='2'
import collections,hashlib,json,math,pickle,re,sys
from decimal import Decimal
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import from_wkb
import find_paired_return_sites as F
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
RUN=HERE/sys.argv[1];OUT=RUN/'independent-current-source-verification';OUT.mkdir()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def physical(r):return {k:v for k,v in r.items() if k!='chunk_sha256'}
def shape(r):
    if r['kind']=='segment':return LineString([[v/1e6 for v in r['start_IU']],[v/1e6 for v in r['end_IU']]]).buffer(r['width_IU']/2e6,quad_segs=256)
    return Point([v/1e6 for v in r['at_IU']]).buffer(max(r['diameters_IU'].values())/2e6,quad_segs=256)
def fp_chunk(text,uid):
    i=text.index('"'+uid+'"');s=text.rfind('\n\t(footprint ',0,i)+2;assert s>1
    return F.chunk_at(text,s)
receipt=RUN/'receipt.json';r=json.loads(receipt.read_text());assert r['inputs_unchanged']
current=ROOT/'reports/board-finish-20261017/combined-route-stage-r1'
oldfile=F.OLD/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json'
model=F.CACHE/'actual-combined-full-after-model.pkl';graph=F.CACHE/'actual-combined-full-after-all-net-groups.pkl'
flash=F.OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/actual-full-refill-via-flashes.json'
paths=[receipt,current/'native/board.kicad_pcb',current/'all-copper-expected.json',oldfile,model,graph,flash,F.BASE,
       HERE/'current-native-local-clearance-census.json',HERE/'inspect_exact_local_clearances.py',Path(__file__),Path(F.__file__)]
pins={str(f):sha(f) for f in paths}
assert pins[str(current/'native/board.kicad_pcb')]==r['frozen_current_peer_SHA256']=='758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad'
assert pins[str(model)]=='c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806'
assert pins[str(graph)]=='c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd'
h=pickle.loads(model.read_bytes());groups=pickle.loads(graph.read_bytes());masks=json.loads(flash.read_text())['vias']
old=json.loads(oldfile.read_text())['copper'];cur=json.loads((current/'all-copper-expected.json').read_text())['copper']
added={u:v for u,v in cur.items() if u not in old};removed=set(old)-set(cur)
changed={u:v for u,v in cur.items() if u in old and physical(v)!=physical(old[u])}
hash_only=[u for u,v in cur.items() if u in old and v!=old[u] and physical(v)==physical(old[u])]
put('physical-current-delta.json',{'added':len(added),'removed':len(removed),'changed_physical':len(changed),'chunk_hash_only':len(hash_only),'added_UUIDs':sorted(added),'removed_UUIDs':sorted(removed)})
actual_text=F.BASE.read_bytes().decode();current_text=(current/'native/board.kicad_pcb').read_bytes().decode()
hp={q['uuid']:q for q in h['pads']};hv={q['uuid']:q for q in h['vias']};checks=[];eligible=[];reject=[];allops=[]
for packet in r['packets']:
    net=packet['net'];ly=packet['layer'];wf=Path(packet['body_WKB_file']);pins[str(wf)]=sha(wf)
    assert pins[str(wf)]==packet['body_WKB_file_SHA256'];whole=from_wkb(wf.read_bytes())
    source=[]
    for end in packet['endpoints']:
        uid=end['uuid']
        if end['kind']=='track':
            assert uid in cur and uid in old and physical(cur[uid])==physical(old[uid])
            source.append({'UUID':uid,'kind':'track','actual_retained_physical_native_ledger_exact':True,'current_chunk_SHA256':cur[uid]['chunk_sha256']})
        else:
            assert end['kind']=='pad' and hp[uid]['smd']
            before=fp_chunk(actual_text,uid);after=fp_chunk(current_text,uid)
            assert before==after,'Endpoint footprint changed; needs native physical equivalence before use'
            source.append({'UUID':uid,'kind':'SMD_pad','ref':end['ref'],'pin':end['pin'],'complete_native_footprint_chunk_literal':True,'chunk_SHA256':hashlib.sha256(after.encode()).hexdigest()})
    for cap in packet.get('qualified_inherited_unchanged_owner_apertures',[]):
        uid=cap['signal_UUID'];v=hv[uid]
        assert uid in cur and uid in old and physical(cur[uid])==physical(old[uid])
        assert masks[uid]==v['flashed'] and ly in masks[uid]
        assert cap['radius_expansion_mm']==0 and cap['immutable_owned_radius_mm']==v['d']/2+.275
        assert cap['finite_existing_same_layer_annulus_contact_mm2']>.000001 and cap['finite_actual_root_fill_overlap_mm2']>.000001
    # Independent prospective UF for actual groups already joined by current
    # peer additions. This removes alternate-route credits for staged R310.
    peers=[(u,q) for u,q in {**added,**changed}.items() if F.norm(q['raw_net'])==net]
    nodes=[]
    for uid,q in peers:
        layers=[q['layer']] if q['kind']=='segment' else F.K.LAYERS
        for l in layers:nodes.append({'uuid':uid,'layer':l,'shape':shape(q)})
    parent={}
    def find(q):
        parent.setdefault(q,q)
        while parent[q]!=q:parent[q]=parent[parent[q]];q=parent[q]
        return q
    def join(a,b):parent[find(a)]=find(b)
    for i,node in enumerate(nodes):
        for j,other in enumerate(nodes[:i]):
            if node['uuid']==other['uuid'] or (node['layer']==other['layer'] and node['shape'].distance(other['shape'])<=.000002):join(('peer',i),('peer',j))
        for gi,gg in enumerate(groups[net]):
            if any(q['uuid'] not in removed and q['layer']==node['layer'] and q['shape'].distance(node['shape'])<=.000002 for q in gg):join(('peer',i),('actual',gi))
    edge=packet['actual_required_group_edge'];already=find(('actual',edge[0]))==find(('actual',edge[1]))
    touched=[gi for gi,gg in enumerate(groups[net]) if any(q['uuid'] not in removed and q['layer']==ly and q['shape'].intersection(whole).area>.000001 for q in gg)]
    required=[gi for gi in touched if any(q['kind']=='pad' and q.get('pin') for q in groups[net][gi])]
    assert set(edge)<=set(required)
    tokens=[]
    for t,op in zip(packet['tracks'],packet['operations']):
        f=Path(op['file']);pins[str(f)]=sha(f);assert pins[str(f)]==op['SHA256'];tree=F.parse(f.read_text())
        assert tree[0]=='segment' and F.field(tree,'uuid')==[op['UUID']]==[t['uuid']]
        a=[float(v) for v in F.field(tree,'start')];b=[float(v) for v in F.field(tree,'end')]
        assert a==t['a'] and b==t['b'] and F.field(tree,'net')==[t['net']] and F.norm(t['net'])==net
        assert F.field(tree,'layer')==[ly] and float(F.field(tree,'width')[0])==t['w']==.2
        assert all(Decimal(v)*1000000==(Decimal(v)*1000000).to_integral_value() for v in F.field(tree,'start')+F.field(tree,'end'))
        assert t['uuid'] not in cur
        tokens.append({'UUID':t['uuid'],'width_IU':200000,'all_native_coordinates_integer_nm':True})
    row={'candidate_index':packet['candidate_index'],'net':net,'layer':ly,'named_actual_groups_touched':required,'already_staged_group_join':already,
         'current_same_net_true_peer_UUIDs':[u for u,_ in peers],'retained_endpoint_source':source,'exact_native_fragment_tokens':tokens,
         'required_named_pads_by_group':{str(gi):sorted({(q['ref'],str(q['pin'])) for q in groups[net][gi] if q['kind']=='pad' and q.get('pin')}) for gi in required}}
    checks.append(row)
    if already:reject.append({'packet':packet,'reason':'Alternate route for already staged current peer join','proof':row})
    else:eligible.append(packet);allops.extend(packet['operations'])
for i,a in enumerate(eligible):
    sa=from_wkb(Path(a['body_WKB_file']).read_bytes())
    for b in eligible[:i]:
        if a['layer']!=b['layer'] or a['net']==b['net']:continue
        sb=from_wkb(Path(b['body_WKB_file']).read_bytes());required=.175 if h['domains_normalized'].get(a['net'])==h['domains_normalized'].get(b['net']) else .625
        assert sa.distance(sb)>=required
local=json.loads((HERE/'current-native-local-clearance-census.json').read_text())
assert local['native_source_SHA256']==pins[str(current/'native/board.kicad_pcb')]
assert all(q['ref'].startswith('FID') and set(q['numeric_local_clearances_mm'])=={.6} or set(q['numeric_local_clearances_mm'])=={0.} for q in local['numeric_local_clearance_footprints'])
assert all(not q['net'] for q in h['pads'] if q['ref'].startswith('FID')),'Explicit .6 local fid clearance must be covered by .6 net-less guard'
out={'status':'INDEPENDENT_SOURCE_AND_CURRENT_GROUP_REDUNDANCY_SCREEN_COMPLETE_NATIVE_GATES_OPEN','eligible_new_nonredundant_packets':eligible,'rejected_alternate_staged_joins':reject,'checks':checks,
     'exact_additive_operations':allops,'new_bridges':len(eligible),'new_nets':len({q['net'] for q in eligible}),'new_tracks':len(allops),'new_vias':0,'removed_Cu':0,
     'frozen_current_source_SHA256':pins[str(current/'native/board.kicad_pcb')],'all_input_SHA256':pins,'inputs_unchanged':all(sha(Path(f))==v for f,v in pins.items()),
     'source_parity_full_native_refill_all_old_relationships_old_reference_current_watchdog_timing_SI':'OPEN_REQUIRED','PCB_written':False,'adopted':False,'manufacturing_ready':False}
put('exact-reviewed-additive-packet.json',out)
print(json.dumps({k:out[k] for k in ('new_bridges','new_nets','new_tracks','inputs_unchanged')}))
