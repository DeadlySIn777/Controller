"""Reconcile exact retained routes that enter real isolation-package gaps.

Only the enumerated native UUIDs may change geometry. Real source endpoints,
lands and nets are fixed. Added detours preserve the old same-net physical
pad clusters. This is an engineering correction, not a DRC suppression.
"""
from __future__ import annotations
import argparse,copy,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import ROOT,sha,write
from hardware_build_assembly import parse,dump,child,value,children
from hardware_route_logic_return import identity,pad_identity
from hardware_route_selected_additive import immutable_objects
from hardware_zone_motherboard_returns import functional_barrier,add_keepout
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def vec(p):return pcbnew.VECTOR2I(*(pcbnew.FromMM(x)for x in p))


def native_pad_clusters(board,nets):
    board.BuildConnectivity();out=[];seen=set()
    for p in board.GetPads():
        if not p.GetNumber() or p.GetNetname()not in nets or p.m_Uuid.AsString()in seen:continue
        items=list(board.GetConnectivity().GetConnectedItems(p))+[p]
        ids={q.m_Uuid.AsString()for q in items if isinstance(q,pcbnew.PAD)and q.GetNumber()and q.GetNetname()==p.GetNetname()}
        seen|=ids;out.append(dict(net=p.GetNetname(),pad_UUIDs=sorted(ids)))
    return out


def apply_hand_candidate_superseded(board):
    exact={t.m_Uuid.AsString():t for t in board.GetTracks()};ledger=[];added=[]
    def edit(uid,net,start,end,old_start,old_end):
        t=exact[uid]
        if t.GetNetname()!=net or tuple(t.GetStart())!=tuple(vec(old_start))or tuple(t.GetEnd())!=tuple(vec(old_end)):
            raise ValueError('Exact reviewed retained route precondition changed '+uid)
        old=identity(t);t.SetStart(vec(start));t.SetEnd(vec(end))
        ledger.append(dict(uuid=uid,before=old,after=identity(t),net=net,reason='Exact package functional isolation gap correction'))
    def new(model_uid,start,end):
        original=exact[model_uid];t=pcbnew.PCB_TRACK(board);t.SetNet(original.GetNet())
        t.SetLayer(original.GetLayer());t.SetWidth(original.GetWidth());t.SetStart(vec(start));t.SetEnd(vec(end));board.Add(t)
        added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
    sda='/motherboard_safety_sensor/DIC_SENSOR_SDA';scl='/motherboard_safety_sensor/DIC_SENSOR_SCL'
    edit('77ce933c-03ed-49af-a643-c0d32d5b296a',sda,[117.2,175.865],[117.2,175.865],[121.325,175.865],[121.325,175.865])
    edit('9e7ea7ed-97e0-4f74-88ae-4c8dcf999903',sda,[117.2,175.865],[118.525,175.865],[121.325,175.865],[118.525,175.865])
    edit('58c55e90-7861-467f-b6a7-3f7182708bb8',sda,[121.325,167.7071],[117.2,175.865],[121.325,167.7071],[121.325,175.865])
    edit('c09a5148-4c21-49a0-8acc-1fb04ab87d19',scl,[116.2,177.135],[116.2,177.135],[121.325,177.135],[121.325,177.135])
    edit('0e12292a-3515-4893-a3cc-764dd51fc344',scl,[116.2,177.135],[118.525,177.135],[121.325,177.135],[118.525,177.135])
    edit('268ca875-9ac6-45ff-8502-c81fd7c994c6',scl,[129.675,169],[116.2,172.5],[129.675,169],[121.325,177.135])
    new('268ca875-9ac6-45ff-8502-c81fd7c994c6',[116.2,172.5],[116.2,177.135])
    chassis='0df65ce4-7666-4119-a8ea-96e783bba855'
    edit(chassis,'/CHASSIS',[420,27.5],[414,27.5],[420,28],[414,28]);new(chassis,[420,28],[420,27.5]);new(chassis,[414,27.5],[414,28])
    mpg='ae43fd60-995c-4b41-bffb-c85530d90492'
    edit(mpg,'/motherboard_operator/MPG_SEL_Y',[89.8821,301],[102.25,302],[89.8821,296.7071],[102.25,302]);new(mpg,[89.8821,296.7071],[89.8821,301])
    cond='075108d5-7295-4d62-8794-a06af67d0347'
    edit(cond,'/motherboard_operator/MPG_SEL_Y_CONDITIONED',[93.71997,288.3],[106.3375,288.3],[93.71997,291.35],[106.3375,291.35]);new(cond,[93.71997,291.35],[93.71997,288.3]);new(cond,[106.3375,288.3],[106.3375,291.35])
    fault='/motherboard_operator/PRB0_FAULT_GOOD_ISO'
    edit('d4afb6ba-ff4b-4222-8413-50264fea6d5f',fault,[102.65,294.365],[104.4,294.365],[102.65,294.365],[95.1375,294.365])
    edit('247f83ae-65ff-4227-bfd1-54e6593a66e3',fault,[104.4,302.05],[95.1375,302.05],[95.1375,294.365],[95.1375,302.05])
    new('d4afb6ba-ff4b-4222-8413-50264fea6d5f',[104.4,294.365],[104.4,302.05])
    ao='/motherboard_acc_control/AO_I2C_SDA_HOST'
    edit('0cd3817e-fb12-44b4-9f87-0a20e04bdab8',ao,[413.03003,254.87003],[409,245],[413.03003,254.87003],[413.03003,241.35997])
    edit('7f769cc1-832d-4d0c-90da-f6ec781a0190',ao,[409,245],[410.01997,241.35997],[413.03003,241.35997],[410.01997,241.35997])
    return ledger,added


def apply(board):
    """Solve the exact corrections against every native pad/track obstacle."""
    import heapq
    from hardware_route_local_signals import GeometryIndex
    from hardware_route_logic_return import mm,segment_hits_box,segment_distance,distance
    ids={'77ce933c-03ed-49af-a643-c0d32d5b296a','9e7ea7ed-97e0-4f74-88ae-4c8dcf999903','58c55e90-7861-467f-b6a7-3f7182708bb8',
        'c09a5148-4c21-49a0-8acc-1fb04ab87d19','0e12292a-3515-4893-a3cc-764dd51fc344','268ca875-9ac6-45ff-8502-c81fd7c994c6',
        '0df65ce4-7666-4119-a8ea-96e783bba855','ae43fd60-995c-4b41-bffb-c85530d90492','075108d5-7295-4d62-8794-a06af67d0347',
        'd4afb6ba-ff4b-4222-8413-50264fea6d5f','247f83ae-65ff-4227-bfd1-54e6593a66e3',
        '0cd3817e-fb12-44b4-9f87-0a20e04bdab8','7f769cc1-832d-4d0c-90da-f6ec781a0190'}
    exact={t.m_Uuid.AsString():t for t in board.GetTracks()};old={u:identity(exact[u])for u in ids}
    layers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]
    pads=GeometryIndex();tracks={l:GeometryIndex()for l in layers};holes=[];barriers=[]
    #Use the actual full-source pad-side map, not footprint-name guesses.
    mapping=json.loads((ROOT/'reports/motherboard-return-zoning-20261001/substrate-native-domain-map-r01/domain-map.json').read_text())
    for row in mapping['barriers']:
        p=functional_barrier(row)
        if p.OutlineCount():
            box=p.BBox();barriers.append((pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())))
    for p in board.GetPads():
        if not p.IsOnCopperLayer():continue
        box=p.GetBoundingBox();bounds=tuple(pcbnew.ToMM(v)for v in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()])
        pads.add((p.GetNetname(),bounds,{l for l in layers if p.IsOnLayer(l)}),bounds)
    def obstacle(t):
        via=isinstance(t,pcbnew.PCB_VIA);width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if via else t.GetWidth())
        s,e=mm(t.GetStart()),mm(t.GetEnd());record=(t.GetNetname(),s,e,width)
        for l in layers:
            if t.IsOnLayer(l):tracks[l].add(record,(min(s[0],e[0])-width/2,min(s[1],e[1])-width/2,max(s[0],e[0])+width/2,max(s[1],e[1])+width/2))
        if via:holes.append((s,pcbnew.ToMM(t.GetDrillValue())))
    for t in board.GetTracks():
        if t.m_Uuid.AsString()not in ids:obstacle(t)
    def clear(s,e,net,layer,width=.2):
        radius=width/2+.151
        if any(segment_hits_box(s,e,box,width/2+.001)for box in barriers):return False
        for name,box,on in pads.candidates(s,e,radius):
            if name!=net and layer in on and segment_hits_box(s,e,box,radius):return False
        for name,a,b,w in tracks[layer].candidates(s,e,radius):
            if name!=net and segment_distance(s,e,a,b)<radius+w/2:return False
        return True
    def via_clear(p,net):
        if any(segment_hits_box(p,p,box,.251)for box in barriers):return False
        for name,box,on in pads.candidates(p,p,.451):
            if name!=net and segment_hits_box(p,p,box,.451):return False
        for l in layers:
            for name,a,b,w in tracks[l].candidates(p,p,.451):
                if name!=net and distance(p,a,b)<.451+w/2:return False
        return not any(math.dist(p,q)<.1+d/2+.3for q,d in holes)
    def maze(start,end,net,layer,width=.2):
        if clear(start,end,net,layer,width):return[start,end]
        step=.25;a,b=tuple(round(x/step)for x in start),tuple(round(x/step)for x in end)
        box=(min(a[0],b[0])-56,min(a[1],b[1])-56,max(a[0],b[0])+56,max(a[1],b[1])+56)
        def p(n):return(n[0]*step,n[1]*step)
        beginnings=[];goals=set()
        for dx in range(-2,3):
            for dy in range(-2,3):
                n=a[0]+dx,a[1]+dy
                if clear(start,p(n),net,layer,width):beginnings.append(n)
                n=b[0]+dx,b[1]+dy
                if clear(p(n),end,net,layer,width):goals.add(n)
        queue=[];cost={};parents={};cache={}
        for n in beginnings:
            g=math.dist(start,p(n));cost[n]=g;parents[n]=None;heapq.heappush(queue,(g+math.dist(p(n),end),g,n))
        while queue:
            _,g,n=heapq.heappop(queue)
            if cost[n]!=g:continue
            if n in goals:
                path=[n]
                while parents[n]is not None:n=parents[n];path.append(n)
                points=[start]+[p(v)for v in reversed(path)]+[end];compact=[points[0]]
                for x,y,z in zip(points,points[1:],points[2:]):
                    ux,uy=y[0]-x[0],y[1]-x[1];vx,vy=z[0]-y[0],z[1]-y[1]
                    if abs(ux*vy-uy*vx)>1e-8 or ux*vx+uy*vy<0:compact.append(y)
                compact.append(end)
                return[q for i,q in enumerate(compact)if i==0 or math.dist(q,compact[i-1])>1e-8]
            if len(cost)>120000:break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                v=n[0]+dx,n[1]+dy
                if not box[0]<=v[0]<=box[2]or not box[1]<=v[1]<=box[3]:continue
                edge=tuple(sorted((n,v)))
                if edge not in cache:cache[edge]=clear(p(n),p(v),net,layer,width)
                if not cache[edge]:continue
                c=g+step*math.hypot(dx,dy)
                if c<cost.get(v,float('inf')):cost[v]=c;parents[v]=n;heapq.heappush(queue,(c+math.dist(p(v),end),c,v))
        return None
    ledger=[];added=[]
    def commit_path(net,points,layer,uids,width=.2):
        legs=[(s,e)for s,e in zip(points,points[1:])if math.dist(s,e)>1e-8]
        if len(legs)<len(uids):raise ValueError('Exact old UUID count exceeds path legs')
        for i,(s,e)in enumerate(legs):
            if i<len(uids):
                t=exact[uids[i]];t.SetStart(vec(s));t.SetEnd(vec(e));t.SetLayer(layer)
                ledger.append(dict(uuid=uids[i],before=old[uids[i]],after=identity(t),net=net,reason='Source-endpoint-preserving geometric correction outside exact package gap'))
            else:
                t=pcbnew.PCB_TRACK(board);t.SetNet(board.FindNet(net));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));t.SetStart(vec(s));t.SetEnd(vec(e));board.Add(t)
                added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
            obstacle(t)
    def relocate_receiver(vuid,fuid,buid,start,end):
        v=exact[vuid];net=v.GetNetname();chosen=None
        for d in [1.4,2.,2.8,4.,.8,1.]:
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-.7071,-.7071),(-.7071,.7071)]:
                q=(round(end[0]+dx*d,6),round(end[1]+dy*d,6))
                if not via_clear(q,net)or not clear(q,end,net,pcbnew.F_Cu):continue
                path=maze(start,q,net,pcbnew.B_Cu)
                if path:chosen=q,path;break
            if chosen:break
        if not chosen:raise ValueError('No physically clear outward receiver via '+vuid)
        q,path=chosen;v.SetPosition(vec(q));ledger.append(dict(uuid=vuid,before=old[vuid],after=identity(v),net=net,reason='Move inward via outside actual all-layer isolation gap'))
        obstacle(v);commit_path(net,[q,end],pcbnew.F_Cu,[fuid]);commit_path(net,path,pcbnew.B_Cu,[buid])
    relocate_receiver('77ce933c-03ed-49af-a643-c0d32d5b296a','9e7ea7ed-97e0-4f74-88ae-4c8dcf999903','58c55e90-7861-467f-b6a7-3f7182708bb8',[121.325,167.7071],[118.525,175.865])
    relocate_receiver('c09a5148-4c21-49a0-8acc-1fb04ab87d19','0e12292a-3515-4893-a3cc-764dd51fc344','268ca875-9ac6-45ff-8502-c81fd7c994c6',[129.675,169],[118.525,177.135])
    for uid,start,end in [
        ('0df65ce4-7666-4119-a8ea-96e783bba855',[420,28],[414,28]),
        ('ae43fd60-995c-4b41-bffb-c85530d90492',[89.8821,296.7071],[102.25,302]),
        ('075108d5-7295-4d62-8794-a06af67d0347',[93.71997,291.35],[106.3375,291.35])]:
        t=exact[uid];path=maze(start,end,t.GetNetname(),t.GetLayer(),pcbnew.ToMM(t.GetWidth()))
        if not path:raise ValueError('No clear package-gap detour '+uid)
        commit_path(t.GetNetname(),path,t.GetLayer(),[uid],pcbnew.ToMM(t.GetWidth()))
    ao='/motherboard_acc_control/AO_I2C_SDA_HOST';path=maze([413.03003,254.87003],[410.01997,241.35997],ao,pcbnew.B_Cu)
    if not path:raise ValueError('No actual AOhost SDA gap detour')
    if len(path)==2:path.insert(1,((path[0][0]+path[1][0])/2,(path[0][1]+path[1][1])/2))
    commit_path(ao,path,pcbnew.B_Cu,['0cd3817e-fb12-44b4-9f87-0a20e04bdab8','7f769cc1-832d-4d0c-90da-f6ec781a0190'])
    fault='/motherboard_operator/PRB0_FAULT_GOOD_ISO';start=(102.65,294.365);end=(95.1375,302.05)
    #This crowded logic receiver is allowed a real two-via B-side detour; every
    #candidate is checked against foreign pads/traces on all six copper layers.
    escapes=[]
    for p in [start,end]:
        options=[]
        for d in [1.4,2.,2.8,4.,.8,1.]:
            for dx,dy in [(1,0),(-1,0),(0,-1),(0,1),(.7071,.7071),(-.7071,-.7071)]:
                q=(round(p[0]+dx*d,6),round(p[1]+dy*d,6))
                if via_clear(q,fault)and clear(p,q,fault,pcbnew.F_Cu):options.append(q)
        escapes.append(options)
    chosen=None
    for q,r in sorted(((q,r)for q in escapes[0]for r in escapes[1]),key=lambda v:math.dist(*v)):
        path=maze(q,r,fault,pcbnew.B_Cu)
        if path:chosen=q,r,path;break
    if not chosen:raise ValueError('No actual fault-receiver package-gap detour')
    q,r,path=chosen;commit_path(fault,[start,q],pcbnew.F_Cu,['d4afb6ba-ff4b-4222-8413-50264fea6d5f']);commit_path(fault,[r,end],pcbnew.F_Cu,['247f83ae-65ff-4227-bfd1-54e6593a66e3']);commit_path(fault,path,pcbnew.B_Cu,[])
    for point in [q,r]:
        v=pcbnew.PCB_VIA(board);v.SetNet(board.FindNet(fault));v.SetPosition(vec(point));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);board.Add(v)
        added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v)));obstacle(v)
    if {r['uuid']for r in ledger}!=ids:raise ValueError('Exact bounded old-copper ledger differs')
    return ledger,added


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--map',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    base=a.board.resolve();out=a.out.resolve();mapping=json.loads(a.map.read_text(encoding='utf-8'))
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('New report directory required')
    if mapping['input_sha256'].get(str(base))!=sha(base):raise ValueError('Map input differs from exact board')
    out.mkdir(parents=True);(out/'inputs').mkdir()
    for f in [base,a.map.resolve(),Path(__file__)]:shutil.copy2(f,out/'inputs'/f.name)
    dest=out/'motherboard-functional-isolation-corrected-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
    for f in base.parent.iterdir():
        if f.is_dir()and(f.name.endswith('.pretty')or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
    shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    board=pcbnew.LoadBoard(str(base));old_cu={t.m_Uuid.AsString():identity(t)for t in board.GetTracks()}
    old_pads={p.m_Uuid.AsString():pad_identity(p)for p in board.GetPads()};old_zones={z.m_Uuid.AsString()for z in board.Zones()}
    net_names={t.GetNetname()for t in board.GetTracks()if t.m_Uuid.AsString()in {
        '77ce933c-03ed-49af-a643-c0d32d5b296a','c09a5148-4c21-49a0-8acc-1fb04ab87d19','0df65ce4-7666-4119-a8ea-96e783bba855',
        'ae43fd60-995c-4b41-bffb-c85530d90492','075108d5-7295-4d62-8794-a06af67d0347','d4afb6ba-ff4b-4222-8413-50264fea6d5f','7f769cc1-832d-4d0c-90da-f6ec781a0190'}}
    before_clusters=native_pad_clusters(board,net_names);ledger,added=apply(board)
    all_layers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]
    for row in mapping['barriers']:add_keepout(board,functional_barrier(row),all_layers,'ISO_FUNCTIONAL_BOUNDARY_'+row['reference'],tracks=True,vias=True)
    donor=out/'native-donor.kicad_pcb';pcbnew.SaveBoard(str(donor),board)
    old_tree=parse(base.read_text(encoding='utf-8'));new_tree=parse(donor.read_text(encoding='utf-8'))
    changed={r['uuid']for r in ledger};newids={r['uuid']for r in added}
    replacements={value(child(n,'uuid')[1]):n for n in new_tree[1:]if isinstance(n,list)and n and n[0]in ['segment','via','zone']}
    final=copy.deepcopy(old_tree)
    for i,n in enumerate(final):
        if isinstance(n,list)and n and n[0]in ['segment','via']and value(child(n,'uuid')[1])in changed:final[i]=copy.deepcopy(replacements[value(child(n,'uuid')[1])])
    final.extend(copy.deepcopy(n)for u,n in replacements.items()if u in newids or(n[0]=='zone'and u not in old_zones))
    dest.write_text(dump(final)+'\n',encoding='utf-8')
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    fresh=pcbnew.LoadBoard(str(dest));actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    if any(actual.get(u)!=v for u,v in old_cu.items()if u not in changed):raise ValueError('Unreviewed old copper changed')
    if {p.m_Uuid.AsString():pad_identity(p)for p in fresh.GetPads()}!=old_pads:raise ValueError('Source-pad lands or names changed')
    if any(actual[r['uuid']]!=r['after']for r in ledger):raise ValueError('Reviewed edited geometry differs after native save')
    if any(actual[r['uuid']]!=r['identity']for r in added):raise ValueError('New route net/geometry differs after native save')
    after_clusters=native_pad_clusters(fresh,net_names)
    if any(not any(old['net']==new['net']and set(old['pad_UUIDs'])<=set(new['pad_UUIDs'])for new in after_clusters)for old in before_clusters):raise ValueError('An old actual stationary source-pad cluster was disconnected')
    drc=json.loads((out/'drc.json').read_text(encoding='utf-8'))
    receipt=dict(board_sha256=sha(dest),input_board_sha256=sha(base),exact_native_copper_geometry_ledger=ledger,exact_new_copper=added,
        exact_added_zone_UUIDs=sorted(u for u,n in replacements.items()if n[0]=='zone'and u not in old_zones),
        old_stationary_source_pad_clusters_preserved=True,source_pad_cluster_evidence=dict(before=before_clusters,after=after_clusters),
        all_actual_source_pad_lands_and_names_preserved=True,native_errors=sum(v['severity']=='error'for v in drc['violations']),
        native_warnings=sum(v['severity']=='warning'for v in drc['violations']),native_ignored=drc.get('ignored_checks',[]),
        manufacturing_ready=False,physical_qualification=False)
    receipt['passed']=not receipt['native_errors']and not receipt['native_ignored'];write(out/'receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items()if k not in ['exact_native_copper_geometry_ledger','exact_new_copper','exact_added_zone_UUIDs','source_pad_cluster_evidence']},indent=2));raise SystemExit(not receipt['passed'])


if __name__=='__main__':main()
