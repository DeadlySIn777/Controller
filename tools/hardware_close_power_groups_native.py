"""Close independently observed local power-group gaps on a native COPY."""
from pathlib import Path
import argparse,collections,hashlib,json,math,heapq,shutil,subprocess
import pcbnew
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_logic_return import mm,xy,segment_distance,identity
from hardware_route_power_groups_native import hits
from hardware_build_assembly import parse,dump,child,value
ROOT=Path(__file__).resolve().parents[1];CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--inspect',action='store_true');ap.add_argument('--finish',action='store_true');a=ap.parse_args()
    assert not a.out.exists()and a.out.resolve().is_relative_to(ROOT/'reports');a.out.mkdir(parents=True);initial=sha(a.board);tool=sha(Path(__file__));prior=json.loads(a.receipt.read_text());assert prior['board_sha256']==initial
    kelvin_kinds={'shunt_Kelvin_IC_escape','shunt_Kelvin_via','separate_shunt_Kelvin','shunt_inner_pad_Kelvin_tap'}
    removed_new={r['uuid']:r for r in prior['added_copper']if r['net'].endswith(('CORE_CORE_CONFIG','MOTION_CORE_CONFIG','CORE_CORE_5V_PG','MOTION_CORE_5V_PG','CORE_CORE_RT','MOTION_CORE_RT'))or(r['kind']in kelvin_kinds and r['net']in ['/mc_local_power/CORE_5V','/motherboard_power_entry/MOTION_5V_RAW'])}if not(a.inspect or a.finish)else {}
    if a.finish:removed_new={r['uuid']:r for r in prior['added_copper']if(r['kind']=='reviewed_control_receiver_route'and r['net'].endswith('C_PGOOD'))or r['net'].endswith('FIELD_FIELD_5V_PGOOD')}
    if a.finish:
        fa_near_source={'ef94dec6-7fda-465d-b89f-a1500d6cfa07','4e7c2d97-40b0-4212-b425-26b04d7d4711','993df734-f43b-4a52-9cfd-52464f47e3eb','ea9fbc4f-8688-4c0b-97e8-fe0566080b71'}
        reviewed={r['uuid']:r for r in prior['added_copper']if r['uuid']in fa_near_source};assert set(reviewed)==fa_near_source
        removed_new.update(reviewed)
    read_board=a.board
    if removed_new:
        tree=parse(a.board.read_text());tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in ['segment','via','arc']and value(child(x,'uuid')[1])in removed_new)];read_board=a.out/'reviewed-new-CONFIG-cleared.kicad_pcb';read_board.write_text(dump(tree)+'\n')
        for suffix in ['.kicad_pro','.kicad_dru']:
            if a.board.with_suffix(suffix).exists():shutil.copyfile(a.board.with_suffix(suffix),read_board.with_suffix(suffix))
    b=pcbnew.LoadBoard(str(read_board.resolve()));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};groups=json.loads(a.recipes.read_text())['groups'];scope={r for g in groups.values()for r in g};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()};pg=GeometryIndex();ti={l:GeometryIndex()for l in [pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In3_Cu]};holes=[];added=[];connections=[];pending=[]
    for p in b.GetPads():
        if not p.IsOnCopperLayer():continue
        po=p.GetEffectivePolygon(pcbnew.F_Cu);polys=[[mm(po.Outline(k).CPoint(i))for i in range(po.Outline(k).PointCount())]for k in range(po.OutlineCount())];bb=p.GetBoundingBox();pg.add((p.GetNetname(),polys,p.IsOnLayer(pcbnew.F_Cu),p.IsOnLayer(pcbnew.B_Cu)),tuple(pcbnew.ToMM(x)for x in [bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()]))
    def obstacle(t):
        via=isinstance(t,pcbnew.PCB_VIA);w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if via else t.GetWidth());s,e=mm(t.GetStart()),mm(t.GetEnd())
        for l in ti:
            if t.IsOnLayer(l):ti[l].add((t.GetNetname(),s,e,w),(min(s[0],e[0])-w/2,min(s[1],e[1])-w/2,max(s[0],e[0])+w/2,max(s[1],e[1])+w/2))
        if via:holes.append((s,pcbnew.ToMM(t.GetDrillValue())))
    for t in b.GetTracks():obstacle(t)
    def clear(ps,n,l,w=.2):
        gap=w/2+.151
        for s,e in zip(ps,ps[1:]):
            if l in [pcbnew.F_Cu,pcbnew.B_Cu]:
                for net,polys,top,bot in pg.candidates(s,e,gap):
                    if net!=n and(top if l==pcbnew.F_Cu else bot)and any(hits(s,e,p,gap)for p in polys):return False
            for net,x,y,width in ti[l].candidates(s,e,gap):
                if net!=n and segment_distance(s,e,x,y)<gap+width/2-1e-6:return False
        return True
    def vc(p,n,diameter=.5):return all(clear([p,p],n,l,diameter)for l in ti)and not any(math.dist(p,q)<.1+d/2+.251 for q,d in holes)
    def maze(s,e,n,l,step=.2,pad=2):
        low=(min(s[0],e[0])-pad,min(s[1],e[1])-pad);hi=(max(s[0],e[0])+pad,max(s[1],e[1])+pad);cost={(0,0):0};prev={};q=[(math.dist(s,e),0,(0,0))];end=None
        pt=lambda k:(s[0]+k[0]*step,s[1]+k[1]*step)
        while q and len(cost)<22000:
            _,d,k=heapq.heappop(q)
            if d>cost[k]+1e-8:continue
            p=pt(k)
            if math.dist(p,e)<step*1.5 and clear([p,e],n,l):end=k;break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                t=(k[0]+dx,k[1]+dy);v=pt(t)
                if not(low[0]<=v[0]<=hi[0]and low[1]<=v[1]<=hi[1])or not clear([p,v],n,l):continue
                nd=d+step*math.hypot(dx,dy)
                if nd>=cost.get(t,float('inf'))-1e-8:continue
                cost[t]=nd;prev[t]=k;heapq.heappush(q,(nd+math.dist(v,e),nd,t))
        if end is None:return None
        out=[e,pt(end)];k=end
        while k!=(0,0):k=prev[k];out.append(pt(k))
        out.reverse();simple=[]
        for p in out:
            if simple and math.dist(simple[-1],p)<1e-8:continue
            while len(simple)>1:
                x,y=simple[-2:]
                if abs((y[0]-x[0])*(p[1]-y[1])-(y[1]-x[1])*(p[0]-y[0]))>1e-8:break
                simple.pop()
            simple.append(p)
        return simple
    def route(ps,n,l=pcbnew.F_Cu,w=.2,kind='local_observed_support_gap'):
        assert clear(ps,n,l,w)
        for s,e in zip(ps,ps[1:]):
            if math.dist(s,e)<1e-8:continue
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(l);t.SetWidth(pcbnew.FromMM(w));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);obstacle(t);added.append(dict(uuid=t.m_Uuid.AsString(),kind=kind,net=n,identity=identity(t)))
    def via(p,n,kind='local_observed_support_via',diameter=.5):
        assert vc(p,n,diameter);v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(p));v.SetWidth(pcbnew.FromMM(diameter));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);b.Add(v);obstacle(v);added.append(dict(uuid=v.m_Uuid.AsString(),kind=kind,net=n,identity=identity(v),diameter_mm=diameter,drill_mm=.2,position_mm=p))
    def reachable(p):return {q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T}|{p.m_Uuid.AsString()}
    if a.inspect:
        rows=[]
        for ref,pin in [('U11007','9'),('U11007','13'),('U11009','1')]:
            p=pads[(ref,pin)];s=mm(p.GetPosition());n=p.GetNetname();rr=[]
            for dx in [-1.2,-.9,-.6,-.3,0,.3,.6,.9,1.2]:
                for dy in [-1.2,-.9,-.6,-.3,0,.3,.6,.9,1.2]:
                    if not(dx or dy):continue
                    v=(s[0]+dx,s[1]+dy);clear_layers={b.GetLayerName(l):clear([v,v],n,l,.5)for l in ti};drill=not any(math.dist(v,q)<.1+d/2+.251 for q,d in holes);route_ok=any(clear(z,n,pcbnew.F_Cu)for z in paths(s,v))
                    if all(clear_layers.values())and drill:rr.append(dict(offset=[dx,dy],point=v,escape_clear=route_ok))
            rows.append(dict(ref=ref,pin=pin,net=n,start=s,valid_via_candidates=rr))
        detail=[]
        ox,oy=mm(fs['U11007'].GetPosition())
        for pin,v in [('9',(ox-2,oy+2.1)),('13',(ox+.5,oy+2.1)),('13',(ox+.5,oy+1.95))]:
            n=pads[('U11007',pin)].GetNetname();block=[]
            for net,polys,top,bot in pg.candidates(v,v,.401):
                if net!=n and top and any(hits(v,v,p,.401)for p in polys):block.append(dict(kind='pad',net=net,polys=polys))
            for l in ti:
                for net,x,y,width in ti[l].candidates(v,v,.401):
                    if net!=n and segment_distance(v,v,x,y)<.401+width/2-1e-6:block.append(dict(kind='track',layer=b.GetLayerName(l),net=net,start=x,end=y,width=width))
            for q,d in holes:
                if math.dist(v,q)<.1+d/2+.251:block.append(dict(kind='hole',position=q,drill=d))
            detail.append(dict(pin=pin,point=v,blockers=block))
        rows.append(dict(explicit_points=detail))
        (a.out/'inspect.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows));return
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
    # Independent output-voltage Kelvin pickup moves left of CONFIG's escape;
    # BIAS remains a separate branch and every measurement via stays .50/.20.
    for u,shunt in ([]if a.finish else[('U11007','R11022'),('U11008','R11030')]):
        ox,oy=mm(fs[u].GetPosition());p=pads[(u,'12')];q=pads[(shunt,'2')];n=p.GetNetname();s=mm(p.GetPosition());old_tap=next(r for r in removed_new.values()if r['net']==n and r['kind']=='shunt_inner_pad_Kelvin_tap');x=old_tap['identity'][2][0]/1e6;sv=(ox-.48,oy+3.35);ev=(x,oy+3.3);tap=(x,oy+1.25)
        assert vc(sv,n)and vc(ev,n)and clear([s,sv],n,pcbnew.F_Cu)and clear([ev,tap],n,pcbnew.F_Cu),(u,'Kelvin relocated escape obstruction')
        middle=[sv,(sv[0],oy+4.15),(ev[0],oy+4.15),ev]
        assert clear(middle,n,pcbnew.B_Cu),(u,'reviewed Kelvin corridor obstructed')
        assert middle
        route([s,sv],n,kind='shunt_Kelvin_IC_escape');via(sv,n,'shunt_Kelvin_via');route(middle,n,pcbnew.B_Cu,kind='separate_shunt_Kelvin');via(ev,n,'shunt_Kelvin_via');route([ev,tap],n,kind='shunt_inner_pad_Kelvin_tap')
    # Four explicitly reviewed low-current control escapes. The 0.10 mm
    # nominal ring is an advanced-PCB quotation/DFM request, not PCBWay's
    # standard 0.15 mm annulus, and never applies to power or thermal vias.
    scoped_vias=[]
    for u,en,config in ([]if a.finish else[('U11007','R11027','R11025'),('U11008','R11035','R11033')]):
        ox,oy=mm(fs[u].GetPosition())
        for pin,ref,rpin,offset in [('9',en,'2',(-2.35,3.18)),('13',config,'1',(.38,3.45))]:
            p,q=pads[(u,pin)],pads[(ref,rpin)];n=p.GetNetname();s,e=mm(p.GetPosition()),mm(q.GetPosition());sv=(ox+offset[0],oy+offset[1])
            ss=[s,sv]if pin=='9'else[s,(ox+.4,oy+3.2),sv]
            if not(vc(sv,n,.4)and clear(ss,n,pcbnew.F_Cu)):
                diagnostics=[]
                for l in ti:
                    for net,x,y,width in ti[l].candidates(sv,sv,.351):
                        if net!=n and segment_distance(sv,sv,x,y)<.351+width/2-1e-6:diagnostics.append(dict(layer=b.GetLayerName(l),net=net,start=x,end=y,width=width))
                (a.out/'blocked-control-escape.json').write_text(json.dumps(dict(ref=u,pin=pin,point=sv,tracks=diagnostics),indent=2)+'\n')
                assert False,(u,pin,'reviewed escape obstructed')
            choice=None
            for dx,dy in sorted([(dx,dy)for dx in [-2,-1.5,-1.1,-.8,-.4,0,.4,.8,1.1,1.5,2]for dy in [-2,-1.5,-1.1,-.8,-.4,0,.4,.8,1.1,1.5,2]if dx or dy],key=lambda v:math.hypot(*v)):
                ev=(e[0]+dx,e[1]+dy)
                if not vc(ev,n):continue
                es=next((z for z in paths(ev,e)if clear(z,n,pcbnew.F_Cu)),None)or maze(ev,e,n,pcbnew.F_Cu,step=.1,pad=2)
                if not es:continue
                for l in [pcbnew.B_Cu,pcbnew.In3_Cu]:
                    middle=next((z for z in paths(sv,ev)if clear(z,n,l)),None)or maze(sv,ev,n,l,pad=4)
                    if middle:choice=(ev,es,l,middle);break
                if choice:break
            assert choice,(u,pin,'reviewed control receiver path obstructed')
            ev,es,l,middle=choice;route(ss,n,kind='reviewed_control_fine_pitch_escape');via(sv,n,'reviewed_low_current_control_040_020',.4);scoped_vias.append(added[-1]);route(middle,n,l,kind='reviewed_control_receiver_route');via(ev,n,'reviewed_control_receiver_050_020');route(es,n,kind='reviewed_control_receiver_land')
            connections.append(dict(group='CORE7'if u=='U11007'else'MOTION6',from_pad=u+'.'+pin,to_pad=ref+'.'+rpin,net=n))
    if a.finish:
        for u in ['U11007','U11008']:
            ox,oy=mm(fs[u].GetPosition());n=pads[(u,'9')].GetNetname();sv=(ox-2.35,oy+3.18);turn=(ox-4.8,oy+2.05);escape=[sv,(sv[0],turn[1]),turn];end_vias=[r for r in prior['added_copper']if r['net']==n and r['kind']=='reviewed_control_receiver_050_020'];ev=min((tuple(r['position_mm'])for r in end_vias),key=lambda v:math.dist(v,sv))
            assert clear(escape,n,pcbnew.In3_Cu),'Reviewed enable west escape';middle=next((z for z in paths(turn,ev)if clear(z,n,pcbnew.In3_Cu)),None)or maze(turn,ev,n,pcbnew.In3_Cu,pad=4);assert middle
            route(escape,n,pcbnew.In3_Cu,kind='reviewed_control_receiver_route');route(middle,n,pcbnew.In3_Cu,kind='reviewed_control_receiver_route')
        for u,pull in [('U11007','R11029'),('U11008','R11037')]:
            p,q=pads[(u,'7')],pads[(pull,'1')];n=p.GetNetname();assert n==q.GetNetname();ox,oy=mm(fs[u].GetPosition());s,e=mm(p.GetPosition()),mm(q.GetPosition());sv=(ox-2.05,oy+1.45)
            assert vc(sv,n)and clear([s,sv],n,pcbnew.F_Cu),(u,'PG escape')
            choice=None
            for dx,dy in [(0,-.8),(0,.8),(-.8,0),(.8,0),(-1.1,0),(1.1,0),(0,-1.1),(0,1.1)]:
                ev=(e[0]+dx,e[1]+dy)
                if not vc(ev,n):continue
                es=next((z for z in paths(ev,e)if clear(z,n,pcbnew.F_Cu)),None)
                if not es:continue
                for l in [pcbnew.B_Cu,pcbnew.In3_Cu]:
                    middle=next((z for z in paths(sv,ev)if clear(z,n,l)),None)or maze(sv,ev,n,l,pad=4)
                    if middle:choice=(ev,es,l,middle);break
                if choice:break
            assert choice,(u,'PG receiver');ev,es,l,middle=choice;route([s,sv],n,kind='regulator_PG_local_escape');via(sv,n,'regulator_PG_050_020');route(middle,n,l,kind='regulator_PG_local_receiver');via(ev,n,'regulator_PG_050_020');route(es,n,kind='regulator_PG_pull_land')
            connections.append(dict(group='CORE7'if u=='U11007'else'MOTION6',from_pad=u+'.7',to_pad=pull+'.1',net=n))
        ox,oy=mm(fs['U11009'].GetPosition());p=pads[('U11009','4')];n=p.GetNetname();s=mm(p.GetPosition());ps=[s,(s[0],oy+1.25),(ox-2.4,oy+1.25),(ox-3,oy+1)];assert clear(ps,n,pcbnew.F_Cu,.35),'LMR VIN input-cap loop relocation';route(ps,n,w=.35,kind='field_VIN_loop')
        p=pads[('U11009','3')];n=p.GetNetname();sv=(ox-1.6,oy+.56);ev=(ox-2.975,oy+2);escape=[mm(p.GetPosition()),(sv[0],mm(p.GetPosition())[1]),sv];assert vc(sv,n)and clear(escape,n,pcbnew.F_Cu),'LMR EN relocation';middle=next((z for z in paths(sv,ev)if clear(z,n,pcbnew.B_Cu)),None)or maze(sv,ev,n,pcbnew.B_Cu,pad=2);assert middle;route(escape,n,kind='LMR_EN_local_escape');via(sv,n,'LMR_EN_050_020');route(middle,n,pcbnew.B_Cu,kind='LMR_EN_local_receiver')
        p,q=pads[('U11009','2')],pads[('R11040','2')];n=p.GetNetname();sv=(ox-1.47,oy-.29);ev=(ox+3.575,oy-5.5);escape=[mm(p.GetPosition()),sv]
        assert vc(sv,n)and vc(ev,n)and clear(escape,n,pcbnew.F_Cu)and clear([ev,mm(q.GetPosition())],n,pcbnew.F_Cu),('LMR PG relocation',vc(sv,n),vc(ev,n),clear(escape,n,pcbnew.F_Cu),clear([ev,mm(q.GetPosition())],n,pcbnew.F_Cu));middle=next((z for z in paths(sv,ev)if clear(z,n,pcbnew.B_Cu)),None)or maze(sv,ev,n,pcbnew.B_Cu,pad=4);assert middle
        route(escape,n,kind='LMR_PG_local_escape');via(sv,n,'LMR_PG_050_020');route(middle,n,pcbnew.B_Cu,kind='LMR_PG_local_receiver');via(ev,n,'LMR_PG_050_020');route([ev,mm(q.GetPosition())],n,kind='LMR_PG_pull_land');connections.append(dict(group='FIELD_A5',from_pad='U11009.2',to_pad='R11040.2',net=n))
        p,q=pads[('U11009','1')],pads[('C11053','1')];n=p.GetNetname();start=(ox-.65,oy-1.1);ps=[start,(ox-.65,oy-1.55),(ox-2.4,oy-1.55),mm(q.GetPosition())]
        assert clear(ps,n,pcbnew.F_Cu),'LMR actual RT-pad upper lobe escape';route(ps,n,kind='LMR36506_RT_actual_pad_lobe_VCC_tie');connections.append(dict(group='FIELD_A5',from_pad='U11009.1',to_pad='C11053.1',net=n))
    # Grounded controls and the FIELD_B LDO thermal/input return islands need
    # actual ground stitches; top-zone assignment alone does not join them.
    for name,g in groups.items():
        u=next(r for r in g if r.startswith('U'));gp='30'if name in ['CORE7','MOTION6']else'9'if name.startswith('FIELD')else'4';reference=pads[(u,gp)];gn=reference.GetNetname()
        for r in g:
            for p in fs[r].Pads():
                if p.GetNetname()!=gn:continue
                b.BuildConnectivity()
                if reference.m_Uuid.AsString()in reachable(p):continue
                s=mm(p.GetPosition());cand=[(s[0]+d*x,s[1]+d*y)for d in [.65,.85,1.1,1.4,1.7]for x,y in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]]
                pick=next((v for v in cand if vc(v,gn)and clear([s,v],gn,pcbnew.F_Cu)),None)
                if pick:route([s,pick],gn,kind='actual_isolated_ground_land_stitch');via(pick,gn,'actual_isolated_ground_land_via')
                else:pending.append(dict(ref=r,pin=p.GetNumber(),net=gn,reason='Ground land needs a reviewed return escape'))
    # Actual MC input current has a short fine-pitch escape followed by a
    # wide local reservoir path; do not substitute a long .2 mm input feed.
    for u,cap in ([]if a.finish else[('U2001','C2001'),('U2002','C2004')]):
        p,q=pads[(u,'6')],pads[(cap,'1')];s,e=mm(p.GetPosition()),mm(q.GetPosition());ox,oy=mm(fs[u].GetPosition());mid=(ox+1.6,oy-.25);n=p.GetNetname();wide=[mid,(e[0],mid[1]),e]
        if clear([s,mid],n,pcbnew.F_Cu)and clear(wide,n,pcbnew.F_Cu,.8):route([s,mid],n,kind='MC_VIN_fine_pitch_escape');route(wide,n,w=.8,kind='MC_VIN_wide_reservoir_feed')
        else:pending.append(dict(ref=u,pin='6',reason='MC input reservoir wide feed obstructed'))
        q=pads[(u,'2')];coil='L2001'if u=='U2001'else'L2002';r=pads[(coil,'1')];s,e=mm(q.GetPosition()),mm(r.GetPosition());n=q.GetNetname();mid=(ox-1.6,s[1]);wide=[mid,(e[0],mid[1]),e]
        if clear([s,mid],n,pcbnew.F_Cu)and clear(wide,n,pcbnew.F_Cu,.8):route([s,mid],n,kind='MC_SW_fine_pitch_parallel_escape');route(wide,n,w=.8,kind='MC_SW_wide_local_coil_feed')
        else:pending.append(dict(ref=u,pin='2',reason='MC wide SW-to-coil feed obstructed'))
    # Correct the one observed split SW polygon with actual short terminal
    # escapes and a broad connection outside the IC land envelope.
    for u,coil in [('U11007','L11001'),('U11008','L11002')]:
        p,q=pads[(u,'21')],pads[(coil,'1')];n=p.GetNetname();b.BuildConnectivity()
        if q.m_Uuid.AsString()in reachable(p):continue
        ox,oy=mm(fs[u].GetPosition());s,e=mm(p.GetPosition()),mm(q.GetPosition());mid=(ox+4.1,s[1]);wide=[mid,(e[0],mid[1]),e]
        if clear([s,mid],n,pcbnew.F_Cu)and clear(wide,n,pcbnew.F_Cu,1.5):route([s,mid],n,kind='SW_land_bank_escape');route(wide,n,w=1.5,kind='SW_polygon_gap_bridge')
        else:pending.append(dict(ref=u,pin='21',reason='SW current-bank polygon gap remains'))
    # Full actual local connectivity drives these support branches, including
    # bootstrap capacitors, BIAS/enable pulls and the regulator-ground return.
    for name,g in groups.items():
        nn=collections.defaultdict(list)
        for r in g:
            for p in fs[r].Pads():
                n=p.GetNetname()
                if n and not n.startswith('unconnected-')and 'GND'not in n and not n.endswith('_0V'):nn[n].append(p)
        def priority(row):
            n,pp=row;return(0 if n.endswith('_RT')else 1 if n.endswith('_COMP')else 3 if n.endswith('_CONFIG')else 2,len(pp),n)
        for n,pp in sorted(nn.items(),key=priority):
            for iteration in range(len(pp)):
                b.BuildConnectivity();seen=set();cc=[]
                for p in pp:
                    if p.m_Uuid.AsString()in seen:continue
                    rr=reachable(p);seen.update(rr);cc.append([q for q in pp if q.m_Uuid.AsString()in rr])
                if len(cc)<2:break
                pairs=sorted([(math.dist(mm(p.GetPosition()),mm(q.GetPosition())),p,q)for i,c in enumerate(cc)for d in cc[i+1:]for p in c for q in d if not(p.GetParentFootprint().GetReference()in ['U11007','U11008']and p.GetNumber()in ['11','12'])and not(q.GetParentFootprint().GetReference()in ['U11007','U11008']and q.GetNumber()in ['11','12'])],key=lambda z:z[0]);choice=None
                for dist,p,q in pairs:
                    s,e=mm(p.GetPosition()),mm(q.GetPosition());ps=next((v for v in paths(s,e)if clear(v,n,pcbnew.F_Cu)),None)or maze(s,e,n,pcbnew.F_Cu)
                    if ps:choice=(p,q,ps,None);break
                    offsets=[-1.2,-.9,-.6,-.5,-.3,0,.3,.5,.6,.9,1.2];starts=[(s[0]+dx,s[1]+dy)for dx in offsets for dy in offsets if dx or dy];ends=[(e[0]+dx,e[1]+dy)for dx in [-1.4,-.7,0,.7,1.4]for dy in [-1.4,-.7,0,.7,1.4]if dx or dy]
                    starts={v:next((path for path in paths(s,v)if clear(path,n,pcbnew.F_Cu)),None)or maze(s,v,n,pcbnew.F_Cu,step=.1,pad=1)for v in starts if vc(v,n)};ends={v:next((path for path in paths(v,e)if clear(path,n,pcbnew.F_Cu)),None)or maze(v,e,n,pcbnew.F_Cu,step=.1,pad=1)for v in ends if vc(v,n)};starts={v:ps for v,ps in starts.items()if ps};ends={v:ps for v,ps in ends.items()if ps}
                    for sv,ev in sorted([(x,y)for x in starts for y in ends],key=lambda z:math.dist(*z))[:250]:
                        if math.dist(sv,ev)<.451:continue
                        for l in [pcbnew.B_Cu,pcbnew.In3_Cu]:
                            middle=next((v for v in paths(sv,ev)if clear(v,n,l)),None)or maze(sv,ev,n,l)
                            if middle:choice=(p,q,middle,(sv,ev,starts[sv],ends[ev],l));break
                        if choice:break
                    if choice:break
                if not choice:pending.append(dict(group=name,net=n,clusters=len(cc),reason='Actual local physical cluster remains open'));break
                p,q,ps,vv=choice
                if vv:
                    sv,ev,ss,es,l=vv;route(ss,n);via(sv,n);route(ps,n,l);via(ev,n);route(es,n)
                else:route(ps,n)
                connections.append(dict(group=name,from_pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),to_pad=q.GetParentFootprint().GetReference()+'.'+q.GetNumber(),net=n))
            print(json.dumps(dict(group=name,net=n,closed_additional_connections=len(connections))),flush=True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());dest=a.out/'power-groups-routed-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:
        if a.board.with_suffix(suffix).exists():shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    rules_before=dest.with_suffix('.kicad_dru').read_text()
    nets=sorted({r['net']for r in scoped_vias})
    rule='\n# Exact four LM706A0/LM70660 EN/CONFIG low-current escape vias ONLY.\n# PCBWay ADVANCED capability 3mil annulus; factory stackup/DFM/price approval required.\n(rule "Four low-current converter control escapes"\n  (condition "A.Type == \'Via\' && ('+' || '.join('A.NetName == \'%s\''%n for n in nets)+')")\n  (constraint via_diameter (min 0.40mm))\n  (constraint hole_size (min 0.20mm))\n  (constraint annular_width (min 0.10mm)))\n'
    if a.finish:shutil.copyfile(a.board.parent/'scoped-control-via-rule.json',a.out/'scoped-control-via-rule.json')
    else:
        dest.with_suffix('.kicad_dru').write_text(rules_before+rule)
        (a.out/'scoped-control-via-rule.json').write_text(json.dumps(dict(standard_annular_width_mm=.15,advanced_published_annular_width_mm=.0762,requested_nominal_annular_width_mm=.10,exact_vias=scoped_vias,rule_added=rule,original_rule_sha256=hashlib.sha256(rules_before.encode()).hexdigest(),advanced_factory_dfm_confirmed=False,source_urls=['https://www.pcbway.com/advanced-pcb-capabilities.html','https://www.pcbway.com/capabilities.html']),indent=2)+'\n')
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text())
    run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0
    drc=json.loads((a.out/'drc.json').read_text());final=pcbnew.LoadBoard(str(dest));final.BuildConnectivity();after={t.m_Uuid.AsString():identity(t)for t in final.GetTracks()};assert all(after.get(k)==v for k,v in old.items());assert sha(a.board)==initial and sha(Path(__file__))==tool
    receipt=dict(prior);receipt.update(board_sha256=sha(dest),added_copper=[r for r in prior['added_copper']if r['uuid']not in removed_new]+added,connections=[r for r in prior['connections']if not r['net'].endswith(('CORE_CORE_CONFIG','MOTION_CORE_CONFIG'))]+connections,remaining_local_routing=pending,native_drc_types=dict(collections.Counter(r['type']for r in drc['violations'])),native_uncapped_unconnected=final.GetConnectivity().GetUnconnectedCount(False),native_unconnected_items=len(drc['unconnected_items']),closure_source_board_sha256=initial,closure_tool_sha256=tool,exact_replaced_new_CONFIG_copper=list(removed_new.values()),all_original_and_unrelated_native_copper_unchanged=True);(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k]for k in ['native_drc_types','native_uncapped_unconnected','remaining_local_routing','board_sha256']}))
if __name__=='__main__':main()
