"""Exact41-part probe/safety cell relocation and bounded old-leaf retirement."""
from pathlib import Path
import argparse,collections,json,math,shutil,subprocess,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,dump,child,children,value
from hardware_populate_motherboard_pcb import sha,footprint_name,pad_template
from hardware_route_logic_return import identity,mm,xy,segment_hits_box,distance
from hardware_di_leaf_routes import leaf_branches
from hardware_retire_owned_capacitor_leaves import observer_clusters
from hardware_route_local_signals import GeometryIndex
from motherboard_mechanical_audit import graphic_box,body_box,overlap,grown,rect,transformed_box
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def targets():
    moves={}
    for u,base,cap in [('U19001',19001,19001),('U19002',19007,19004),('U19003',19013,19007)]:
        moves[u]=(u,0.,0.,0.)
        for slot,sign in enumerate((-1,1)):
            r=base+3*slot
            moves[f'R{r}']=(u,12.5,sign*4.2,180.)
            moves[f'R{r+1}']=(u,5.35,sign*1.5,0.)
            moves[f'R{r+2}']=(u,-5.7,.2 if slot==0 else 2.5,180.)
            moves[f'C{cap+slot}']=(u,5.8,sign*3.8,0.)
        moves[f'C{cap+2}']=(u,-5.3,-1.5875,180.)
    u='U14031';moves[u]=(u,0.,0.,0.)
    for slot,sign in enumerate((-1,1)):
        r=14069+3*slot
        moves[f'R{r}']=(u,12.5,sign*4.2,180.)
        moves[f'R{r+1}']=(u,5.35,sign*1.5,0.)
        moves[f'R{r+2}']=(u,-5.7,.2 if slot==0 else 2.5,180.)
        moves[f'D{14013+slot}']=(u,19.0,sign*4.2,0.)
    moves['C14058']=(u,-5.3,-1.5875,180.)
    moves['C14059']=(u,-5.3,-4.2,180.)
    assert len(moves)==41
    return moves

def padbox(p):
    r=p.GetBoundingBox();return [pcbnew.ToMM(v)for v in (r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom())]
def gap(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def retire_leaves(b,moving):
    affected={str(p.GetNetname())for f in b.GetFootprints()if f.GetReference()in moving for p in f.Pads()if p.GetNumber()}
    tracks=collections.defaultdict(list);pads=collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetNetname()in affected:tracks[str(t.GetNetname())].append(t)
    for p in b.GetPads():
        if p.GetNumber()and p.GetNetname()in affected:pads[str(p.GetNetname())].append(p)
    removed=set();proof=[];dedicated=[]
    for net,items in tracks.items():
        fixed=[p for p in pads[net]if p.GetParentFootprint().GetReference()not in moving]
        own=[p for p in pads[net]if p.GetParentFootprint().GetReference()in moving]
        if not fixed:
            removed.update(t.m_Uuid.AsString()for t in items);dedicated.append(net);continue
        lines=[t for t in items if not isinstance(t,pcbnew.PCB_VIA)]
        vias=[t for t in items if isinstance(t,pcbnew.PCB_VIA)]
        edges={t.m_Uuid.AsString():(tuple(t.GetStart())+(t.GetLayer(),),tuple(t.GetEnd())+(t.GetLayer(),))for t in lines}
        vertices={v for e in edges.values()for v in e};anchors=set();starts=set();protected=set()
        for v in vertices:
            pt=pcbnew.VECTOR2I(v[0],v[1])
            if any(p.IsOnLayer(v[2])and p.HitTest(pt)for p in fixed)or any(v[:2]==tuple(t.GetPosition())for t in vias):anchors.add(v)
            if any(p.IsOnLayer(v[2])and p.HitTest(pt)for p in own):starts.add(v)
        for t in lines:
            start,end=mm(t.GetStart()),mm(t.GetEnd());uid=t.m_Uuid.AsString();layer=t.GetLayer()
            if any(p.IsOnLayer(layer)and not p.HitTest(t.GetStart())and not p.HitTest(t.GetEnd())and segment_hits_box(start,end,padbox(p),pcbnew.ToMM(t.GetWidth())/2)for p in fixed):protected.add(uid)
            if any(tuple(v.GetPosition())not in (tuple(t.GetStart()),tuple(t.GetEnd()))and t.HitTest(v.GetPosition())for v in vias):protected.add(uid)
            if any(v[2]==layer and v[:2]not in (tuple(t.GetStart()),tuple(t.GetEnd()))and distance((v[0]/1e6,v[1]/1e6),start,end)<1e-7 for v in vertices):protected.add(uid)
        ids,paths=leaf_branches(edges,starts,anchors,protected);removed.update(ids)
        proof.extend(dict(net=net,**p)for p in paths)
    return removed,affected,dict(dedicated_wholly_owned_pad_nets=dedicated,shared_leaf_graph_paths=proof)

def place(b,fps,moves,retired,obstacle_board=None):
    obstacles=GeometryIndex();copper=GeometryIndex();selected=[];ledger=[]
    for ref,f in fps.items():
        if ref in moves:continue
        box=graphic_box(f,pcbnew.F_CrtYd)or body_box(f)[0]
        obstacles.add((ref,box),box)
    if obstacle_board:
        future=pcbnew.LoadBoard(str(obstacle_board))
        current_copper={t.m_Uuid.AsString()for t in b.GetTracks()}
        for f in future.GetFootprints():
            if f.GetReference()in moves:continue
            box=graphic_box(f,pcbnew.F_CrtYd)or body_box(f)[0]
            obstacles.add(('future:'+f.GetReference(),box),box)
        for t in future.GetTracks():
            if t.m_Uuid.AsString()not in current_copper:copper.add(t,rect(t.GetBoundingBox()))
    # Exact primary mating corridors retain the previously reviewed poses.
    mate=ROOT/'reports/motherboard-mechanical-20260930/r24f-complete-mate-proposal-r05/review.json'
    mr=json.loads(mate.read_text());assert mr['pass']
    for ref,row in mr['actual40_ports_mutually_checked'].items():
        for k,box in row['envelopes_mm'].items():obstacles.add((ref+':'+k,box),box)
    for ref,box in [('J15001',[-3,-30,37,25]),('J16001',[-1.27,-1.565,24.13,61.3])]:
        box=transformed_box(fps[ref],box);obstacles.add((ref+':MODULE',box),box)
    for ref in [f'H{22001+i}'for i in range(6)]:
        x,y=mm(fps[ref].GetPosition());box=[x-4.25,y-4.25,x+4.25,y+4.25];obstacles.add((ref+':WASHER',box),box)
    for t in b.GetTracks():
        if t.m_Uuid.AsString()not in retired:copper.add(t,rect(t.GetBoundingBox()))
    for owner in ('U14031','U19001','U19002','U19003'):
        refs=[r for r,v in moves.items()if v[0]==owner];oldcenter=mm(fps[owner].GetPosition())
        for ref in refs:
            f=fps[ref]
            if f.GetLayer()!=pcbnew.F_Cu:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            _,dx,dy,angle=moves[ref];f.SetPosition(xy((dx,dy)));f.SetOrientationDegrees(angle)
        boxes=[graphic_box(fps[r],pcbnew.F_CrtYd)or body_box(fps[r])[0]for r in refs]
        for i,one in enumerate(boxes):
            for j,two in enumerate(boxes[i+1:],i+1):
                if overlap(one,two):raise ValueError('Internal whole-cell courtyard overlap '+refs[i]+'/'+refs[j])
        local=[min(x[0]for x in boxes)-.3,min(x[1]for x in boxes)-.3,max(x[2]for x in boxes)+.3,max(x[3]for x in boxes)+.3]
        candidates=sorted((math.dist((x,y),oldcenter),x,y)for x in range(12,442,2)for y in range(108,322,2))
        pick=None
        for _,x,y in candidates:
            box=[local[0]+x,local[1]+y,local[2]+x,local[3]+y]
            if box[0]<.8 or box[1]<.8 or box[2]>459.2 or box[3]>339.2:continue
            if any(overlap(grown(box,.25),other)for _,other in obstacles.candidates(box[:2],box[2:],.25)):continue
            if any(overlap(grown(box,.25),rect(t.GetBoundingBox()))for t in copper.candidates(box[:2],box[2:],.25)):continue
            pick=(x,y,box);break
        if not pick:raise ValueError('No actual clear whole-cell geometry '+owner)
        x,y,box=pick;obstacles.add((owner+':CELL',box),box);selected.append(dict(owner=owner,origin_mm=[x,y],envelope_mm=box,refs=refs))
        for ref in refs:
            _,dx,dy,angle=moves[ref];fps[ref].SetPosition(xy((x+dx,y+dy)))
    return selected,{str(mate.relative_to(ROOT)):sha(mate)}

def prune_raw(path,removed):
    tree=parse(path.read_text());found={value(child(v,'uuid')[1])for v in tree if isinstance(v,list)and v and v[0]in ('segment','via','arc')and value(child(v,'uuid')[1])in removed}
    if found!=removed:raise ValueError('Exact serialized retirement UUIDs missing')
    tree[:]=[v for v in tree if not(isinstance(v,list)and v and v[0]in ('segment','via','arc')and value(child(v,'uuid')[1])in removed)]
    path.write_text(dump(tree)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--obstacle-board',type=Path);a=p.parse_args()
    assert not a.out.exists();a.out.mkdir(parents=True)
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};moves=targets()
    old_poses={r:[*mm(f.GetPosition()),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer())]for r,f in fps.items()}
    old_pieces={p.m_Uuid.AsString():pad_template(p)for p in b.GetPads()}
    old_copper={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
    removed,nets,leaf=retire_leaves(b,moves);before_clusters=observer_clusters(b,moves,nets)
    original=pcbnew.LoadBoard(str(ROOT/'reports/board-completion-20260930/local-signal-routing-v2/local-signal-routes-candidate.kicad_pcb'))
    protected={t.m_Uuid.AsString()for t in original.GetTracks()}
    if removed&protected:raise ValueError('Retirement crosses original327 copper')
    cells,mate_hash=place(b,fps,moves,removed,a.obstacle_board)
    if a.obstacle_board:mate_hash[str(a.obstacle_board)]=sha(a.obstacle_board)
    rows=[]
    for owner,rt,rs,ci in [('U14031','R14069','R14070',None),('U14031','R14072','R14073',None),
            ('U19001','R19001','R19002','C19001'),('U19001','R19004','R19005','C19002'),
            ('U19002','R19007','R19008','C19004'),('U19002','R19010','R19011','C19005'),
            ('U19003','R19013','R19014','C19007'),('U19003','R19016','R19017','C19008')]:
        ext=next(q for q in fps[rt].Pads()if q.GetNumber()=='1')
        targets_=[(owner,None),(rs,None)]+([(ci,None)]if ci else [])
        choices=[(gap(padbox(ext),padbox(q)),r,q.GetNumber())for r,_ in targets_ for q in fps[r].Pads()if q.GetNumber()]
        dist,r,pin=min(choices);assert dist>=4
        rows.append(dict(RTHR=rt,external_pad=1,minimum_actual_protected_pad_gap_mm=dist,nearest_ref=r,nearest_pin=pin))
    for owner,cap in [('U14031','C14058'),('U19001','C19003'),('U19002','C19006'),('U19003','C19009')]:
        cp=next(p for p in fps[cap].Pads()if p.GetNumber()=='1');v=next(p for p in fps[owner].Pads()if p.GetNumber()=='2')
        d=math.dist(mm(cp.GetPosition()),mm(v.GetPosition()));assert d<=2 and fps[cap].GetLayer()==fps[owner].GetLayer()==pcbnew.F_Cu
        rows.append(dict(bypass=cap,owner=owner,actual_positive_to_VCC2_mm=d,same_device_side=True))
    dest=a.out/'motherboard-probe-safety-cells-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b);prune_raw(dest,removed)
    for resource in a.board.parent.iterdir():
        if resource.is_dir()and(resource.suffix=='.pretty'or resource.name=='3dmodels'):shutil.copytree(resource,a.out/resource.name)
        elif resource.name=='fp-lib-table':shutil.copyfile(resource,a.out/resource.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    baseline=json.loads(a.board.with_name('drc.json').read_text())
    baseline_pairs={(v['type'],tuple(sorted(i['uuid']for i in v['items'])))for v in baseline['violations']}
    old_native={t.m_Uuid.AsString():t for t in b.GetTracks()};causal=[]
    for iteration in range(14):
        outdrc=a.out/f'drc-{iteration:02}.json'
        result=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(outdrc),str(dest)],capture_output=True,text=True)
        (a.out/f'drc-{iteration:02}.txt').write_text(result.stdout+result.stderr);assert result.returncode==0
        drc=json.loads(outdrc.read_text());assert not drc['ignored_checks']
        new=[v for v in drc['violations']if (v['type'],tuple(sorted(i['uuid']for i in v['items'])))not in baseline_pairs]
        if not new:break
        assert all(v['type']in ('via_dangling','track_dangling')for v in new),[(v['type'],v['description'])for v in new]
        ids={i['uuid']for v in new for i in v['items']}
        assert not ids&protected and all(uid in old_native and old_native[uid].GetNetname()in nets for uid in ids)
        candidate=pcbnew.LoadBoard(str(dest));candidate.BuildConnectivity()
        # An obsolete dangling native branch is removable only if the full
        # independent physical-pad observer partition survives its deletion.
        prune_raw(dest,ids);test=pcbnew.LoadBoard(str(dest))
        assert observer_clusters(test,moves,nets)==before_clusters
        causal.extend(dict(iteration=iteration,UUID=uid,native_reason=v['description'])for v in new for i in v['items']for uid in [i['uuid']])
        removed.update(ids)
    else:raise ValueError('Causal dangling cleanup did not converge')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();ff={f.GetReference():f for f in fresh.GetFootprints()}
    assert observer_clusters(fresh,moves,nets)==before_clusters
    now={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    assert set(old_copper)-set(now)==removed and all(now.get(uid)==v for uid,v in old_copper.items()if uid not in removed)
    fp_ledger=[]
    for r,f in ff.items():
        pose=[*mm(f.GetPosition()),f.GetOrientationDegrees(),fresh.GetLayerName(f.GetLayer())]
        if r not in moves:assert pose==old_poses[r]
        else:fp_ledger.append(dict(ref=r,before_pose=old_poses[r],after_pose=pose))
    # Account for legitimate mirroring when B bypasses move to their IC side.
    src=pcbnew.LoadBoard(str(a.board));source_fps={f.GetReference():f for f in src.GetFootprints()}
    for r in moves:
        sf=source_fps[r]
        nf=ff[r]
        if sf.GetLayer()!=nf.GetLayer():sf.Flip(sf.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        sf.SetPosition(nf.GetPosition());sf.SetOrientationDegrees(nf.GetOrientationDegrees())
        assert collections.Counter(pad_template(p)for p in sf.Pads())==collections.Counter(pad_template(p)for p in nf.Pads()),r
    scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=sorted(moves),
        reviewed_removed_copper_UUIDs=sorted(removed),reviewed_modified_copper_UUIDs=[],reviewed_added_copper_UUIDs=[],
        reviewed_modified_zone_UUIDs=[],reviewed_added_zone_UUIDs=[],
        reviewed_scope_reason='Four role-correct ISO1212 cells: same-side actualVCC bypass,own field-side SENSE/RSENSE/CIN,external RTHR4mm spacing; only proven old local Cu/causal leaves retired.')
    (a.out/'merge-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    receipt=dict(input_board=str(a.board),input_board_SHA256=sha(a.board),board_SHA256=sha(dest),
        physical_parts=len(ff),track_via_items=len(now),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        exact_ref_poses=fp_ledger,cells=cells,source_spacing_evidence=rows,
        exact_old_copper_removed=[dict(UUID=uid,before=old_copper[uid])for uid in sorted(removed)],
        old_leaf_graph_proof=leaf,causal_native_dangling_proof=causal,
        all_unmoved_actual_pad_clusters_preserved=True,all_other_native_copper_and_pad_lands_preserved=True,
        original327_copper_preserved=True,baseline_native_DRC_regular=len(baseline['violations']),
        candidate_native_DRC_regular=len(drc['violations']),new_native_DRC_regular=len(new),ignored_checks=[],
        reservation_SHA256=mate_hash,source_23_probe_two_pad_reconciliation_pending=any(
            next(p for p in ff[r].Pads()if p.GetNumber()=='2').GetNetname()!=next(
                p for p in ff['U14031'].Pads()if p.GetNumber()==pin).GetNetname()
            for r,pin in [('R14069','16'),('R14072','11')]),
        manufacturing_ready=False,physical_qualification=False,
        scope='Bounded source-preserving cell layout correction; oldr32 power/dangling violations remain explicit. Root must merge source24 two-pad delta and cleaned baseline,then rerun full DRC/connectivity. No local routing or return-plane qualification is claimed.')
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k]for k in ['physical_parts','track_via_items','uncapped_missing_joins','candidate_native_DRC_regular','new_native_DRC_regular']}))
if __name__=='__main__':main()
