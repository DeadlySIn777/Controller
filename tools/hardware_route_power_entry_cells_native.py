"""Actual three TPS2663 cell routing on an immutable native-board copy.
Power-path polygons and parallel conventional vias are separate from quiet
support traces. This does not qualify factory copper, thermal or rail delivery.
"""
from pathlib import Path
import pcbnew,argparse,hashlib,json,math,collections,shutil,subprocess,heapq
from hardware_route_power_groups_native import inside,hits
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_logic_return import xy,mm,identity,pad_identity,segment_distance
from hardware_build_assembly import parse,dump,child,value
from hardware_power_entry_cell_layout import recipes
ROOT=Path(__file__).resolve().parents[1]
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);before=sha(a.board);b=pcbnew.LoadBoard(str(a.board.resolve()));rec=recipes();fs={f.GetReference():f for f in b.GetFootprints()};entries=[e for e in rec['entries']if e['efuse']in fs];groups={e['name']:rec['groups'][e['name']]for e in entries};scope={r for g in groups.values()for r in g};assert len(scope)in(15,45)
    old_cu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};old_pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};netrefs=collections.defaultdict(set)
    for p in b.GetPads():
        if p.GetNetname():netrefs[p.GetNetname()].add(p.GetParentFootprint().GetReference())
    private={n for n,rs in netrefs.items()if rs<=scope};removed=[dict(uuid=t.m_Uuid.AsString(),identity=identity(t),reason='Every actual pad of this local private net belongs to the reviewed moved entry cell')for t in b.GetTracks()if t.GetNetname()in private];ids={r['uuid']for r in removed};tree=parse(a.board.read_text());tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in ids)];cleared=a.out/'private-cleared-input.kicad_pcb';cleared.write_text(dump(tree)+'\n');b=pcbnew.LoadBoard(str(cleared.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};pads={}
    for r,f in fs.items():
        for p in f.Pads():
            if p.GetNumber():pads.setdefault((r,p.GetNumber()),[]).append(p)
    pg=GeometryIndex();ti={l:GeometryIndex()for l in [pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In3_Cu]};holes=[]
    def pad(ref,pin):return pads[(ref,str(pin))][0]
    def rebuild():
        nonlocal pg,ti,holes
        pg=GeometryIndex();ti={l:GeometryIndex()for l in ti};holes=[]
        for p in [p for f in fs.values()for p in f.Pads()]:
            if not p.IsOnCopperLayer():continue
            pol=p.GetEffectivePolygon(pcbnew.F_Cu)
            polys=[[mm(pol.Outline(k).CPoint(i))for i in range(pol.Outline(k).PointCount())]for k in range(pol.OutlineCount())]
            bb=p.GetBoundingBox();box=(pcbnew.ToMM(bb.GetLeft()),pcbnew.ToMM(bb.GetTop()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
            pg.add((p.GetNetname(),p.GetParentFootprint().GetReference(),polys,p.IsOnLayer(pcbnew.F_Cu),p.IsOnLayer(pcbnew.B_Cu)),box)
        for t in b.GetTracks():obstacle(t)
    def obstacle(t):
        via=isinstance(t,pcbnew.PCB_VIA);width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if via else t.GetWidth());s,e=mm(t.GetStart()),mm(t.GetEnd())
        for l in ti:
            if t.IsOnLayer(l):ti[l].add((t.GetNetname(),s,e,width),(min(s[0],e[0])-width/2,min(s[1],e[1])-width/2,max(s[0],e[0])+width/2,max(s[1],e[1])+width/2))
        if via:holes.append((s,pcbnew.ToMM(t.GetDrillValue())))
    def clear(ps,net,layer,width):
        gap=width/2+.16
        for s,e in zip(ps,ps[1:]):
            if layer in [pcbnew.F_Cu,pcbnew.B_Cu]:
                for n,ref,polys,top,bot in pg.candidates(s,e,gap):
                    if n==net or not(top if layer==pcbnew.F_Cu else bot):continue
                    if any(hits(s,e,poly,gap)for poly in polys):return False
            for n,ta,tb,w in ti[layer].candidates(s,e,gap):
                if n!=net and segment_distance(s,e,ta,tb)<gap+w/2-1e-6:return False
        return True
    def via_clear(pt,net):
        if not clear([pt,pt],net,pcbnew.F_Cu,.5)or not clear([pt,pt],net,pcbnew.B_Cu,.5)or not clear([pt,pt],net,pcbnew.In3_Cu,.5):return False
        return not any(math.dist(pt,p)<.1+d/2+.251 for p,d in holes)
    def grid_path(s,e,net,layer,width=.2,step=.2,pad=3):
        """Bounded actual-copper maze search; every final segment is screened."""
        low=(min(s[0],e[0])-pad,min(s[1],e[1])-pad);high=(max(s[0],e[0])+pad,max(s[1],e[1])+pad)
        q=[(math.dist(s,e),0,(0,0))];prev={};cost={(0,0):0};end=None
        def pt(k):return(s[0]+k[0]*step,s[1]+k[1]*step)
        while q and len(cost)<35000:
            _,d,k=heapq.heappop(q)
            if d>cost[k]+1e-8:continue
            p=pt(k)
            if math.dist(p,e)<=step*1.5 and clear([p,e],net,layer,width):end=k;break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                t=(k[0]+dx,k[1]+dy);r=pt(t)
                if not(low[0]<=r[0]<=high[0]and low[1]<=r[1]<=high[1])or not clear([p,r],net,layer,width):continue
                nd=d+step*math.hypot(dx,dy)
                if nd>=cost.get(t,float('inf'))-1e-8:continue
                cost[t]=nd;prev[t]=k;heapq.heappush(q,(nd+math.dist(r,e),nd,t))
        if end is None:return None
        out=[e,pt(end)];k=end
        while k!=(0,0):k=prev[k];out.append(pt(k))
        out.reverse();simple=[]
        for p in out:
            if simple and math.dist(simple[-1],p)<1e-8:continue
            while len(simple)>1:
                x,y=simple[-2],simple[-1]
                if abs((y[0]-x[0])*(p[1]-y[1])-(y[1]-x[1])*(p[0]-y[0]))>1e-8:break
                simple.pop()
            simple.append(p)
        assert clear(simple,net,layer,width)
        return simple
    additions=[];connections=[];unrouted=[];zones=[]
    def trace(net,ps,width=.2,layer=pcbnew.F_Cu,kind='support'):
        items=[]
        for s,e in zip(ps,ps[1:]):
            if math.dist(s,e)<1e-6:continue
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(width));t.SetLayer(layer);b.Add(t);obstacle(t);items.append(t);additions.append(dict(uuid=t.m_Uuid.AsString(),kind=kind,net=net,identity=identity(t)))
        return items
    def via(net,pt,kind='return_stitch'):
        v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);obstacle(v);additions.append(dict(uuid=v.m_Uuid.AsString(),kind=kind,net=net,identity=identity(v)));return v
    def zone(net,layer,points,kind,priority=20):
        z=pcbnew.ZONE(b);z.SetNet(b.FindNet(net));z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority+len(zones))
        o=z.Outline();o.NewOutline()
        for pt in points:o.Append(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
        b.Add(z);zones.append(dict(uuid=z.m_Uuid.AsString(),kind=kind,net=net,layer=b.GetLayerName(layer),polygon_mm=points,pad_connection='solid',thermal_ampacity_qualified=False));return z
    rebuild();primary=set();endpoints=[]
    def direct(net,pts,width=.2,layer=pcbnew.F_Cu,kind='local_support'):
        if not clear(pts,net,layer,width):raise ValueError('Obstructed '+kind+' '+net+' '+str(pts))
        trace(net,pts,width,layer,kind)
    def checked_via(net,pt,kind):
        if not via_clear(pt,net):raise ValueError('Obstructed via '+kind+' '+net+' '+str(pt))
        via(net,pt,kind)
    for row in entries:
        u=row['efuse'];rev=row['reverse_fet'];q=row['fast_pulldown'];ox,oy=mm(fs[u].GetPosition());rel=lambda x,y:(ox+x,oy+y);poly=lambda ps:[rel(x,y)for x,y in ps];gn=pad(u,25).GetNetname();raw=pad(u,5).GetNetname();inp=pad(u,1).GetNetname();out=pad(u,17).GetNetname();primary.update([gn,raw,inp,out])
        assert pad(row['raw_cap'],1).GetNetname()==raw and pad(row['dvdt_cap'],1).GetNetname()==pad(u,9).GetNetname()and pad(row['in_cap'],1).GetNetname()==inp and pad(row['out_cap'],1).GetNetname()==out,'Exact native capacitor/source role mismatch'
        # Ground references remain bounded to this same-domain protection cell.
        for l in [pcbnew.F_Cu,pcbnew.B_Cu]:zone(gn,l,poly([(-18,-6.2),(6.8,-6.2),(6.8,8.5),(-18,8.5)]),'entry_own_domain_return',1)
        # Shared package power lands are connected by wide polygons, never
        # through the 0.15/0.2 mm quiet-control route below.
        rawpoly=[(-10.8,-1.1),(-7.45,-1.1),(-7.45,-.52),(-5.46,-.52),(-5.46,.525),(-7.45,.525),(-7.45,1.1),(-10.8,1.1)]
        zone(raw,pcbnew.F_Cu,poly(rawpoly),'reverse_FET_source_RAW',70)
        zone(raw,pcbnew.B_Cu,poly([(-10.8,-1.1),(-4.13,-1.1),(-4.13,1.7),(-10.8,1.7)]),'parallel_RAW_to_actual_IN_SYS_bypass',70)
        cinpoly=[(-7.45,-2.95),(-4.565,-2.95),(-4.565,-1.625),(-1.55,-1.625),(-1.55,-.625),(-4.565,-.625),(-4.565,-.4),(-7.45,-.4)]
        zone(inp,pcbnew.F_Cu,poly(cinpoly),'reverse_FET_drain_to_dual_eFuse_IN',70)
        zone(inp,pcbnew.B_Cu,poly([(-7.45,-2.95),(-2.9,-2.95),(-2.9,-1.4),(-7.45,-1.4)]),'parallel_fused_IN_bridge',70)
        zone(out,pcbnew.F_Cu,poly([(1.55,-1.625),(3.45,-1.625),(3.45,-.575),(1.55,-.575)]),'dual_eFuse_OUT_bank_escape',70)
        zone(out,pcbnew.B_Cu,poly([(1.55,-1.625),(3.45,-1.625),(3.45,-.575),(1.55,-.575)]),'parallel_dual_eFuse_OUT_bank_escape',70)
        # Conventional arrays on both sides of input/output supply bridges.
        for x,y in [(-8.8,-.65),(-8.8,.2),(-8.8,.95)]:checked_via(raw,rel(x,y),'RAW_parallel_power_via')
        for x,y in [(-4.0,-2.0),(-3.2,-2.0)]:checked_via(inp,rel(x,y),'IN_parallel_power_via')
        for x,y in [(2.85,-1.3),(2.85,-.65)]:checked_via(out,rel(x,y),'OUT_parallel_power_via')
        # Supply capacitors on B-side have their own positive and return loops.
        for key,n,x in [('in_cap',inp,-2.9),('out_cap',out,2.85)]:
            c=row[key];cp=mm(pad(c,1).GetPosition());vp=rel(x,-3.25);checked_via(n,vp,'actual_input_output_bypass_supply');direct(n,[cp,vp],.4,pcbnew.B_Cu,'actual_input_output_bypass_supply');bank=rel(x,-1.1);route=[vp,bank]if key=='in_cap'else[vp,rel(2.85,-1.3),rel(2.85,-.65)];direct(n,route,.5,pcbnew.F_Cu,'actual_input_output_bypass_supply')
        direct(inp,[rel(-4,-2),rel(-3.2,-2),rel(-2.9,-3.25)],.8,pcbnew.B_Cu,'parallel_IN_supply_bridge')
        direct(inp,[rel(-4,-2),rel(-3.2,-2),rel(-3.2,-1.1)],.8,pcbnew.F_Cu,'parallel_IN_supply_bridge')
        direct(raw,[mm(pad(row['uv_top'],1).GetPosition()),rel(-10.4,7.0125),rel(-10.4,.8)],.2,kind='UV_actual_RAW_feed')
        direct(out,[mm(pad(row['pg_top'],1).GetPosition()),rel(2.85,-.65)],.2,kind='PGTH_actual_protected_OUT_feed')
        # IN_SYS low-current monitor branch is independently returned to the
        # real source bypass, rather than borrowed from a remote shared plane.
        rv=rel(-3.5,1.35);direct(raw,[mm(pad(u,5).GetPosition()),rel(-2.75,.75),rv],.2,kind='IN_SYS_actual_RAW_bypass');checked_via(raw,rv,'IN_SYS_bypass_via');direct(raw,[rv,mm(pad(row['raw_cap'],1).GetPosition())],.2,pcbnew.B_Cu,'IN_SYS_actual_RAW_bypass')
        # True gate/source and fast pulldown loop. DRV crosses on a private
        # inner trace, with both escapes outside actual capacitor lands.
        gate=pad(u,3).GetNetname();direct(gate,[mm(pad(u,3).GetPosition()),rel(-3.0,-.25),rel(-4.55,-.25),mm(pad(rev,4).GetPosition()),mm(pad(q,3).GetPosition())],.2,kind='short_reverse_FET_gate_loop')
        drv=pad(u,4).GetNetname();v1,v2=rel(-3.5,.5),rel(-7.85,.9);direct(drv,[mm(pad(u,4).GetPosition()),rel(-2.8,.25),v1],.2,kind='fast_pulldown_DRV_escape');checked_via(drv,v1,'fast_DRV_via');checked_via(drv,v2,'fast_DRV_via');direct(drv,[v1,v2],.2,pcbnew.In3_Cu,'fast_pulldown_private_DRV');direct(drv,[v2,mm(pad(q,1).GetPosition())],.2,kind='fast_pulldown_DRV_escape')
        direct(raw,[mm(pad(q,2).GetPosition()),rel(-8.8,3.45),rel(-8.8,.95)],.4,kind='fast_pulldown_true_source_return')
        uv=pad(u,6).GetNetname();uvs,uve=rel(-3.4,2.3),rel(-7.65,4.55);direct(uv,[mm(pad(u,6).GetPosition()),uvs],.2,kind='UV_quiet_package_escape');checked_via(uv,uvs,'UV_quiet_support_via');checked_via(uv,uve,'UV_quiet_support_via');direct(uv,[uvs,uve],.2,pcbnew.In3_Cu,'UV_quiet_support');direct(uv,[uve,mm(pad(row['uv_mid'],1).GetPosition())],.2,kind='UV_divider_short_escape')
        # EP array is deliberately own ground; factory thermal-via solder
        # wicking/stencil qualification remains required.
        for x in [-.65,.65]:
            for y in [-.65,.65]:checked_via(gn,rel(x,y),'own_GND_EP_thermal')
        # Every fitted ground support pad gets an actual close return stitch.
        for r in groups[row['name']]:
            if r.startswith('U'):continue
            for p in fs[r].Pads():
                if not p.GetNumber()or p.GetNetname()!=gn:continue
                layer=pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu)else pcbnew.F_Cu;s=mm(p.GetPosition());cands=[(s[0]+dx,s[1]+dy)for d in [.7,.9,1.1,1.4,1.8]for dx,dy in [(0,d),(0,-d),(d,0),(-d,0)]];ev=next((e for e in cands if via_clear(e,gn)and clear([s,e],gn,layer,.2)),None)
                if not ev:unrouted.append(dict(ref=r,pin=p.GetNumber(),reason='No close own-return stitch'));continue
                direct(gn,[s,ev],.2,layer,'actual_own_return_stitch');checked_via(gn,ev,'actual_own_return_stitch')
        endpoints.append(dict(entry=row['name'],efuse=u,ground=gn,raw=raw,protected_input=inp,protected_output=out))
    # Quiet support nets are routed independently of all major supply currents.
    bynet=collections.defaultdict(list)
    for r in scope:
        for p in fs[r].Pads():
            n=p.GetNetname()
            if p.GetNumber()and n and not n.startswith('unconnected-')and n not in primary:bynet[n].append(p)
    for net,ps in sorted(bynet.items(),key=lambda x:(len(x[1]),x[0])):
        while True:
            b.BuildConnectivity();clusters={}
            for p in ps:
                ids0=tuple(sorted({t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T}|{p.m_Uuid.AsString()}));clusters.setdefault(ids0,[]).append(p)
            if len(clusters)<2:break
            vv=list(clusters.values());pairs=sorted([(math.dist(mm(p.GetPosition()),mm(q.GetPosition())),p,q)for i,c in enumerate(vv)for d in vv[i+1:]for p in c for q in d],key=lambda x:x[0]);choice=None
            for span,p,q in pairs:
                s,e=mm(p.GetPosition()),mm(q.GetPosition());selected=next((pp for pp in paths(s,e)if clear(pp,net,pcbnew.F_Cu,.2)),None)or grid_path(s,e,net,pcbnew.F_Cu,.2,step=.15,pad=2)
                if selected:choice=(p,q,selected,None);break
            if not choice:
                for span,p,q in pairs:
                    s,e=mm(p.GetPosition()),mm(q.GetPosition());starts=[(s[0]+d*x,s[1]+d*y)for d in [.75,1,1.4,2]for x,y in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]];ends=[(e[0]+d*x,e[1]+d*y)for d in [.75,1,1.4,2]for x,y in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]]
                    starts={v:next((pp for pp in paths(s,v)if clear(pp,net,pcbnew.F_Cu,.2)),None)for v in starts if via_clear(v,net)};ends={v:next((pp for pp in paths(v,e)if clear(pp,net,pcbnew.F_Cu,.2)),None)for v in ends if via_clear(v,net)};starts={v:pp for v,pp in starts.items()if pp};ends={v:pp for v,pp in ends.items()if pp}
                    for sv,ev in sorted(((x,y)for x in starts for y in ends),key=lambda v:math.dist(*v)):
                        selected=next((pp for pp in paths(sv,ev)if clear(pp,net,pcbnew.In3_Cu,.2)),None)
                        if selected:choice=(p,q,selected,(sv,ev,starts[sv],ends[ev]));break
                    if choice:break
            if not choice:unrouted.append(dict(net=net,clusters=len(clusters),reason='No exact quiet local support path'));break
            p,q,pp,vs=choice
            if vs:
                sv,ev,ss,es=vs;direct(net,ss,.2);checked_via(net,sv,'quiet_support_escape');direct(net,pp,.2,pcbnew.In3_Cu);checked_via(net,ev,'quiet_support_escape');direct(net,es,.2)
            else:direct(net,pp,.2)
            connections.append(dict(net=net,from_pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),to_pad=q.GetParentFootprint().GetReference()+'.'+q.GetNumber(),kind='quiet_support'))
        print(net,len(connections),flush=True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'power-entry-cells-routed-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:
        p=a.board.with_suffix(suffix)
        if p.exists():shutil.copyfile(p,dest.with_suffix(suffix))
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()));qq=pcbnew.LoadBoard(str(dest));qq.BuildConnectivity();after={t.m_Uuid.AsString():identity(t)for t in qq.GetTracks()};assert old_pads=={p.m_Uuid.AsString():pad_identity(p)for p in qq.GetPads()};assert all(after[k]==v for k,v in old_cu.items()if k not in ids);assert all(after[r['uuid']]==r['identity']for r in additions),'Added Cu changed after fill';assert all(t.GetIsFree()for t in qq.GetTracks()if t.m_Uuid.AsString()in{r['uuid']for r in additions}and isinstance(t,pcbnew.PCB_VIA));run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0;dd=json.loads((a.out/'drc.json').read_text());assert sha(a.board)==before
    result=dict(source_board=str(a.board),source_sha256=before,source_unchanged=True,scope_refs=sorted(scope),exact_removed_private_copper=removed,exact_added_copper=additions,exact_added_zones=zones,connections=connections,remaining_local_routing=unrouted,entries=endpoints,all_retained_pad_and_copper_identity_preserved=True,new_vias_free_true_all_annuli_retained=True,native_drc_types=dict(collections.Counter(r['type']for r in dd['violations'])),native_uncapped_unconnected=qq.GetConnectivity().GetUnconnectedCount(False),candidate_sha256=sha(dest),factory_copper_and_ampacity_qualified=False,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('exact_removed_private_copper','exact_added_copper','exact_added_zones','scope_refs','connections')}))
if __name__=='__main__':main()
