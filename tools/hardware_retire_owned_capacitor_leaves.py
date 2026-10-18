"""Retire only literal old capacitor leaf branches for a subsequent relocation.

Every via, shared junction, interior contact and unchanged physical pad anchors
the graph. Independent native connectivity of every unmoved source pad must
remain identical. This is a bounded cleanup candidate, never completed routing.
"""
import argparse,collections,copy,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity,mm,segment_hits_box,distance
from hardware_di_leaf_routes import leaf_branches
from hardware_build_assembly import parse,dump,children,child,value
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def box(p):
    b=p.GetBoundingBox();return tuple(pcbnew.ToMM(v)for v in (b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()))
def observer_clusters(board,moving,net_names):
    board.BuildConnectivity();conn=board.GetConnectivity()
    eligible={p.m_Uuid.AsString():p for p in board.GetPads()if p.GetParentFootprint().GetReference()not in moving and p.GetNetname()in net_names}
    return {uid:sorted({uid}|{v.m_Uuid.AsString()for v in conn.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T and v.m_Uuid.AsString()in eligible})for uid,p in eligible.items()}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('board','owners','recipes','out'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--native-dangling-only',action='store_true',help='Retire only actual native-confirmed old dangling items; no leaf graph guesses')
    ap.add_argument('--moving-refs',help='Exact comma-separated already relocated capacitors owning the native dangling review')
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable report required')
    review=json.loads(a.owners.read_text());recipes=json.loads(a.recipes.read_text())
    if review['board_sha256']!=sha(a.board)or not review['own_pin_match_pass']:raise ValueError('Exact current native owner review required')
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
    source=json.loads((Path(__file__).resolve().parents[1]/'hardware/motherboard/design.json').read_text())['components']
    excluded={r for g in recipes['groups'].values()for r in g}
    rows=[r for r in review['rows']if r['geometric_supply_target_met']is False and r['ref']not in excluded and r['owner']not in excluded and not(r['ref'].startswith(('C60','C80','C81','C195'))or source[r['owner']].get('mpn','').startswith('ISOW'))]
    moving={r['ref']for r in rows};nets={str(p.GetNetname())for ref in moving for p in fps[ref].Pads()}
    if a.native_dangling_only:
        if not a.moving_refs:raise ValueError('Explicit owned capacitor scope required')
        moving=set(a.moving_refs.split(','))
        if not moving<=set(fps)or not moving<=set(r['ref']for r in review['rows']):raise ValueError('Non-source capacitor scope')
        nets={str(p.GetNetname())for ref in moving for p in fps[ref].Pads()}
    old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};native={t.m_Uuid.AsString():t for t in b.GetTracks()}
    bynet=collections.defaultdict(list);padsbynet=collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetNetname()in nets:bynet[str(t.GetNetname())].append(t)
    for p in b.GetPads():
        if p.GetNetname()in nets:padsbynet[str(p.GetNetname())].append(p)
    removed=set();proof=[]
    for net,tracks in bynet.items():
        if a.native_dangling_only:continue
        lines=[t for t in tracks if not isinstance(t,pcbnew.PCB_VIA)]
        vias=[t for t in tracks if isinstance(t,pcbnew.PCB_VIA)]
        edges={t.m_Uuid.AsString():(tuple(t.GetStart())+(t.GetLayer(),),tuple(t.GetEnd())+(t.GetLayer(),))for t in lines}
        vertices={v for e in edges.values()for v in e};anchors=set();starts=set();protected=set()
        pads=padsbynet[net]
        fixed=[p for p in pads if p.GetParentFootprint().GetReference()not in moving]
        caps=[p for p in pads if p.GetParentFootprint().GetReference()in moving]
        for v in vertices:
            pt=pcbnew.VECTOR2I(v[0],v[1])
            if any(p.IsOnLayer(v[2])and p.HitTest(pt)for p in fixed)or any(v[:2]==tuple(t.GetPosition())for t in vias):anchors.add(v)
            if any(p.IsOnLayer(v[2])and p.HitTest(pt)for p in caps):starts.add(v)
        # A physical T-junction or pad/via in the middle of a line must not be
        # mistaken for an unbranched two-endpoint graph edge.
        for t in lines:
            s,e=mm(t.GetStart()),mm(t.GetEnd());uid=t.m_Uuid.AsString();layer=t.GetLayer();width=pcbnew.ToMM(t.GetWidth())
            if any(p.IsOnLayer(layer)and not p.HitTest(t.GetStart())and not p.HitTest(t.GetEnd())and segment_hits_box(s,e,box(p),width/2)for p in fixed):protected.add(uid)
            if any(tuple(v.GetPosition())not in (tuple(t.GetStart()),tuple(t.GetEnd()))and t.HitTest(v.GetPosition())for v in vias):protected.add(uid)
            for v in vertices:
                if v[2]!=layer or v[:2]in (tuple(t.GetStart()),tuple(t.GetEnd())):continue
                if distance((v[0]/1e6,v[1]/1e6),s,e)<1e-7:protected.add(uid);break
        ids,paths=leaf_branches(edges,starts,anchors,protected);removed.update(ids)
        proof.extend(dict(net=net,**v)for v in paths)
    # Every unremoved attachment remains a blocker for that capacitor. Do not
    # silently turn its retained current path into an intentional no-connect.
    blocked=[];eligible=[]
    for ref in sorted(moving):
        attached={t.m_Uuid.AsString()for p in fps[ref].Pads()for t in bynet.get(str(p.GetNetname()),[])if t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd())}
        retained=attached-removed
        (blocked if retained else eligible).append(dict(ref=ref,remaining_attached_UUIDs=sorted(retained)))
    before=observer_clusters(b,moving,nets)
    a.out.mkdir(parents=True);dest=a.out/'motherboard-capacitor-leaves-cleared-candidate.kicad_pcb';tree=parse(a.board.read_text())
    tree[:]=[v for v in tree if not(isinstance(v,list)and v and v[0]in ('segment','via','arc')and value(child(v,'uuid')[1])in removed)]
    dest.write_text(dump(tree)+'\n')
    for resource in a.board.parent.iterdir():
        if resource.is_dir()and(resource.suffix=='.pretty'or resource.name=='3dmodels'):shutil.copytree(resource,a.out/resource.name)
        elif resource.name=='fp-lib-table':shutil.copyfile(resource,a.out/resource.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True)
    (a.out/'drc.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native cleanup DRC execution failed')
    pruning=[]
    for attempt in range(12):
        d=json.loads((a.out/'drc.json').read_text())
        unsafe=[v for v in d['violations']if v['type']not in ('via_dangling','track_dangling')]
        if unsafe:raise ValueError('Unexpected geometry outside bounded dangling cleanup')
        candidates={i['uuid']:v for v in d['violations']for i in v['items']}
        if not candidates:break
        current=pcbnew.LoadBoard(str(dest));current.BuildConnectivity()
        actual_tracks={t.m_Uuid.AsString():t for t in current.GetTracks()}
        for uid,issue in candidates.items():
            if uid not in old or uid not in actual_tracks or actual_tracks[uid].GetNetname()not in nets:raise ValueError('Dangling item outside exact old affected nets')
            pruning.append(dict(uuid=uid,native_description=issue['description'],native_type=issue['type'],native_iteration=attempt,observer_cluster_retention_required=True))
        removed.update(candidates)
        t=parse(dest.read_text());t[:]=[v for v in t if not(isinstance(v,list)and v and v[0]in ('segment','via','arc')and value(child(v,'uuid')[1])in candidates)]
        dest.write_text(dump(t)+'\n')
        test=pcbnew.LoadBoard(str(dest))
        if observer_clusters(test,moving,nets)!=before:raise ValueError('Dangling cleanup breaks an actual unmoved pad cluster')
        prior=a.out/f'drc-{attempt:02}.json';shutil.copyfile(a.out/'drc.json',prior)
        run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True)
        (a.out/f'drc-{attempt+1:02}.txt').write_text(run.stdout+run.stderr)
        if run.returncode:raise ValueError('Native dangling-prune DRC execution failed')
    now=pcbnew.LoadBoard(str(dest));now.BuildConnectivity()
    after=observer_clusters(now,moving,nets)
    if before!=after:raise ValueError('Unmoved actual physical-pad connectivity changed')
    tracks={t.m_Uuid.AsString():identity(t)for t in now.GetTracks()}
    if set(old)-set(tracks)!=removed or any(tracks.get(uid)!=v for uid,v in old.items()if uid not in removed):raise ValueError('Other retained copper changed')
    d=json.loads((a.out/'drc.json').read_text())
    eligible=[];blocked=[]
    for ref in sorted(moving):
        cap=next(f for f in now.GetFootprints()if f.GetReference()==ref)
        retained={t.m_Uuid.AsString()for p in cap.Pads()for t in now.GetTracks()if str(t.GetNetname())==str(p.GetNetname())and(t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd()))}
        (blocked if retained else eligible).append(dict(ref=ref,remaining_attached_UUIDs=sorted(retained)))
    result=dict(input_sha256={str(v):sha(v)for v in (a.board,a.owners,a.recipes)},board_sha256=sha(dest),exact_removed_leaf_copper=[dict(uuid=uid,before=old[uid])for uid in sorted(removed)],literal_leaf_graph_proof=proof,native_dangling_pruning_proof=pruning,
        affected_capacitors=sorted(moving),ready_for_local_relocation=eligible,still_blocked_by_unremoved_actual_copper=blocked,
        all_unmoved_actual_pad_cluster_identities_preserved=True,observer_pads_checked=len(before),native_DRC_regular=len(d['violations']),native_DRC_types=dict(collections.Counter(v['type']for v in d['violations'])),ignored_checks=d.get('ignored_checks',[]),uncapped_missing_joins=now.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    write(a.out/'receipt.json',result);print(dict(removed_leaves=len(removed),eligible_caps=len(eligible),still_attached_caps=len(blocked),native_DRC_regular=len(d['violations']),native_DRC_types=result['native_DRC_types']))
if __name__=='__main__':main()
