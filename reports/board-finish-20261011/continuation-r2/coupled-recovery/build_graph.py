"""Read-only conflict/component graph for coupled recovery of measured198b.

Uses exact source chunks and native r06 shapes, not a new native load. Restored
clones are normalized by recorded provenance only for graph identity, without
changing source bytes. No clearance waiver, board output, or native invocation.
"""
import collections, hashlib, json, math, sys, time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPORT=HERE.parent.parent
C06=REPORT/'recovery-composite/c06'
sys.path.insert(0,str(REPORT));sys.path.insert(0,str(C06));sys.path.insert(0,str(C06/'alternate-r07'))
import compose_additions as C
import screen_c06 as S
import screen_r07 as R
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree

SOURCE=REPORT/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
LOSSES=C06/'four-fag/next-closure/remaining-r06-losses.json'
RECOVERY=Path('Z:/pcb-runs/claude-finish/agent-work/codex-recovery-20261011/recovery.json')
READS={}
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();READS[str(p)]=hashlib.sha256(raw).hexdigest();return raw
def parse(uid,ch,arcs):
    kind=C.pcbtext.chunk_kind(ch);net=S.norm(S.overlay_tool.netname(ch))
    if kind=='segment':
        a=S.overlay_tool.numbers(ch,'start');b=S.overlay_tool.numbers(ch,'end');w=S.overlay_tool.scalar(ch,'width')
        return dict(uuid=uid,net=net,kind=kind,layer=C.pcbtext.chunk_layer(ch),a=a,b=b,w=w,shape=LineString([a,b]).buffer(w/2))
    if kind=='via':
        at=S.overlay_tool.numbers(ch,'at');d=S.overlay_tool.scalar(ch,'size');drill=S.overlay_tool.scalar(ch,'drill')
        return dict(uuid=uid,net=net,kind=kind,at=at,d=d,drill=drill,shape=Point(at).buffer(d/2))
    if uid not in arcs:raise ValueError('Unmodeled arc '+uid)
    a=arcs[uid];return dict(uuid=uid,net=net,kind=kind,layer=a['layer'],shape=S.overlay_tool.base.body(a))
def serial(r):return {k:v for k,v in r.items() if k!='shape'}
def main():
    started=time.time();HERE.mkdir(parents=True,exist_ok=True)
    for p in (Path(__file__),Path(C.__file__),Path(C.pcbtext.__file__),Path(S.__file__),Path(R.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__)):
        read(p)
    old_raw=read(S.overlay_tool.base.BASE);r07_raw=read(R.R07);raw=read(SOURCE)
    if C.sha(old_raw)!=S.overlay_tool.base.BASE_SHA or C.sha(r07_raw)!=R.R07_SHA or C.sha(raw)!='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab':raise ValueError('Source pin mismatch')
    old,r07,now=map(C.inventory,(old_raw,r07_raw,raw))
    if old[0]!=now[0] or old[2]!=now[2] or old[5]!=now[5]:raise ValueError('Noncopper source/plane definitions differ')
    losses=json.loads(read(LOSSES));parts=json.loads(read(REPORT/'measure/r07-four-fag-shared/partitions.json'))
    old_parts=json.loads(read(R.R06_PART));live_parts=json.loads(read(R.R07_PART))
    if parts['sha256']!=C.sha(raw):raise ValueError('Partition source mismatch')
    g=json.loads(read(S.overlay_tool.base.GEOM));domains={S.norm(n):d for n,d in g['nets'].items()}
    arcs={t['uuid']:t for t in g['tracks'] if t.get('kind')=='arc'}
    orig={u:parse(u,c,arcs) for u,c in old[4].items()};curr={u:parse(u,c,arcs) for u,c in now[4].items()}
    prior=json.loads(read(RECOVERY));clones={r['original']:r['r07_recreated'] for r in prior['normalization']}
    # A verified equivalent clone satisfies old geometry; it is not absent.
    equivalents={};clone_rounding=[]
    for uid,clone in clones.items():
        if clone in curr:
            a,b=orig[uid],curr[clone]
            if a['net']!=b['net'] or a['kind']!=b['kind']:raise ValueError('Restored clone role mismatch '+json.dumps([serial(a),serial(b)]))
            deviation=a['shape'].hausdorff_distance(b['shape'])
            if deviation>1e-8:
                if a['kind']!='segment' or a['layer']!=b['layer'] or a['w']!=b['w'] or deviation>.0015:raise ValueError('Restored clone geometry mismatch '+json.dumps([serial(a),serial(b)]))
                clone_rounding.append({'original':uid,'clone':clone,'max_body_deviation_mm':deviation,'old':serial(a),'current':serial(b),'scope':'Graph provenance identity only; actual source bytes and native component obligations retained'})
            if a['kind']=='via' and (a['at']!=b['at'] or a['d']!=b['d'] or a['drill']!=b['drill']):raise ValueError('Restored clone via mismatch')
            equivalents[uid]=clone
    missing={u:r for u,r in orig.items() if now[4].get(u)!=old[4][u] and u not in equivalents}
    by_layer=collections.defaultdict(list)
    for r in curr.values():
        for layer in (g['copper_layers'] if r['kind']=='via' else [r['layer']]):by_layer[layer].append(r)
    trees={l:STRtree([r['shape'] for r in rows]) for l,rows in by_layer.items()}
    new_holes=[r for u,r in curr.items() if r['kind']=='via' and u not in orig and u not in equivalents.values()]
    hole_tree=STRtree([Point(r['at']).buffer(r['drill']/2) for r in new_holes])
    edges=[];rows=[];all_blocker_nets=set()
    for target in losses['rows']:
        net=S.norm(target['net']);removed=[r for r in missing.values() if r['net']==net];local=[]
        for r in removed:
            for layer in (g['copper_layers'] if r['kind']=='via' else [r['layer']]):
                for i in trees[layer].query(r['shape'].buffer(.7),predicate='intersects'):
                    b=by_layer[layer][i]
                    if b['net']==net:continue
                    clearance=.15 if domains.get(net)==domains.get(b['net']) else .6
                    gap=r['shape'].distance(b['shape'])
                    if gap+1e-8>=clearance:continue
                    edge={'restore_net':net,'restore_uuid':r['uuid'],'blocker_net':b['net'],'blocker_uuid':b['uuid'],'layer':layer,'kind':'copper_clearance','gap_mm':gap,'required_mm':clearance,'blocker_origin':'r06 retained' if b['uuid'] in orig else 'r07 restored clone' if b['uuid'] in equivalents.values() else 'r07 new' if b['uuid'] in r07[4] else 'combined new'}
                    edges.append(edge);local.append(edge);all_blocker_nets.add(b['net'])
            if r['kind']=='via':
                p=Point(r['at']);hole=p.buffer(r['drill']/2)
                for i in hole_tree.query(hole.buffer(.3),predicate='intersects'):
                    b=new_holes[i];gap=hole.distance(Point(b['at']).buffer(b['drill']/2));center=math.dist(r['at'],b['at'])
                    if gap>=.25-1e-8 and center>=.8-1e-8:continue
                    edge={'restore_net':net,'restore_uuid':r['uuid'],'blocker_net':b['net'],'blocker_uuid':b['uuid'],'kind':'hole_or_ordinary_spacing','hole_edge_gap_mm':gap,'center_gap_mm':center,'blocker_origin':'r07 new' if b['uuid'] in r07[4] else 'combined new'}
                    edges.append(edge);local.append(edge);all_blocker_nets.add(b['net'])
        grouped=collections.defaultdict(list)
        for edge in local:grouped[edge['blocker_net']].append(edge)
        rows.append({'net':net,'domain':target['domain'],'native_lost_relationships':target['relationships'],'policy':target['controlled_policy'],'missing_original_items':[serial(r) for r in removed],
                     'blocked_original_items':len({e['restore_uuid'] for e in local}),'conflict_edges':len(local),'blocking_nets':{n:{'edge_count':len(es),'item_uuids':sorted({e['blocker_uuid'] for e in es})} for n,es in sorted(grouped.items())}})
    obligations={}
    for net in sorted(all_blocker_nets):
        native_net=next(n for n in parts['nets'] if S.norm(n)==net)
        obligations[net]={'current_pad_groups':parts['nets'][native_net],'r06_pad_groups':old_parts['nets'][native_net],'r07_pad_groups':live_parts['nets'][native_net],
            'current_copper_items':len([r for r in curr.values() if r['net']==net]),'blocking_item_uuids':sorted({e['blocker_uuid'] for e in edges if e['blocker_net']==net})}
    # Nets connected by a conflict must be solved together, not withdrawn.
    uf=S.UF()
    for row in rows:uf.find(row['net'])
    for edge in edges:uf.join(edge['restore_net'],edge['blocker_net'])
    clusters=collections.defaultdict(list)
    for net in uf.p:clusters[uf.find(net)].append(net)
    for p,h in READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Read input changed '+p)
    result={'schema':'coupled-r06-r07-recovery-conflict-graph-v1','verdict':'GRAPH_ONLY_NATIVE_AND_ELECTRICAL_OPEN','candidate_sha256':C.sha(raw),'native_loss_count':14,'restored_clone_equivalents':len(equivalents),
            'lost_route_rows':rows,'conflict_edges':edges,'blocker_component_obligations':obligations,'coupled_net_clusters':[sorted(v) for v in clusters.values()],'recorded_clone_rounding':clone_rounding,
            'source_files_sha256':READS,'seconds':time.time()-started,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,
            'scope':['Exact14native physical relationships and blocking current copper/hole topology only','All original stored source/plane definitions held','Via annuli projected on every layer for conservative collision; no return proof inferred','Conflicts use actual .15/.6 requirements; reroute candidates require .025 margin/full electrical gates','Current and both baseline pad groups are mandatory coupled obligations, never whole-group rollback credit']}
    (HERE/'conflict-graph.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'missing_items':sum(len(r['missing_original_items']) for r in rows),'edges':len(edges),'blocker_nets':len(obligations),'clusters':result['coupled_net_clusters'],'summary':[{k:r[k] for k in ('net','blocked_original_items','conflict_edges','blocking_nets')} for r in rows]}),flush=True)
if __name__=='__main__':main()
