"""Route reviewed six converter groups on an immutable full-board COPY.

Power polygons, local exact-domain reference fills, shunt Kelvin branches and
conventional thermal/stitch vias are separate from support-signal routing.
This does not qualify ampacity, stability, thermal performance or manufacture.
"""
from pathlib import Path
import argparse,hashlib,json,math,shutil,subprocess,collections,heapq
import pcbnew
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_logic_return import distance,segment_distance,xy,mm,identity
from hardware_build_assembly import parse,dump,child,value

ROOT=Path(__file__).resolve().parents[1]
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inside(p,poly):
    x,y=p;odd=False
    for a,c in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(c[1]>y) and x<(c[0]-a[0])*(y-a[1])/(c[1]-a[1])+a[0]:odd=not odd
    return odd
def hits(s,e,poly,margin):
    return inside(s,poly)or inside(e,poly)or any(segment_distance(s,e,a,c)<margin-1e-6 for a,c in zip(poly,poly[1:]+poly[:1]))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--reuse-cleanup-receipt',type=Path);a=ap.parse_args()
    if a.out.exists() or not a.out.resolve().is_relative_to(ROOT/'reports'):raise ValueError('New report COPY required')
    a.out.mkdir(parents=True);source=a.board.resolve();initial_sha=sha(source);tool_sha=sha(Path(__file__));recipe_sha=sha(a.recipes)
    b=pcbnew.LoadBoard(str(source));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
    groups=json.loads(a.recipes.read_text())['groups'];scope={r for g in groups.values()for r in g}
    old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};old_zones={z.m_Uuid.AsString()for z in b.Zones()}
    pads={};netrefs=collections.defaultdict(set)
    for p in b.GetPads():
        ref=p.GetParentFootprint().GetReference();pads.setdefault((ref,p.GetNumber()),[]).append(p)
        if p.GetNetname()and not p.GetNetname().startswith('unconnected-'):netrefs[p.GetNetname()].add(ref)
    removed=[]
    # Exact private support nets whose every actual fitted pad belongs to a
    # moving group. Shared rails and previously retained return copper stay.
    private={n for n,refs in netrefs.items()if refs<=scope}
    for t in list(b.GetTracks()):
        if t.GetNetname()in private:
            removed.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),identity=identity(t),reason='Every actual fitted pad belongs to the reviewed moved converter groups'))
    if a.reuse_cleanup_receipt:
        rr=json.loads(a.reuse_cleanup_receipt.read_text());prior=pcbnew.LoadBoard(rr['source_board']);prior_pads={p.m_Uuid.AsString():p for p in prior.GetPads()}
        for p in b.GetPads():
            if p.GetParentFootprint().GetReference()in scope:continue
            q=prior_pads[p.m_Uuid.AsString()];assert p.GetNetname()==q.GetNetname()and p.GetPosition()==q.GetPosition()and p.GetSize()==q.GetSize(),'Cleanup observer pad changed'
        already={r['uuid']for r in removed}
        for row in rr['exact_removed_private_copper']:
            assert row['uuid']in old and json.loads(json.dumps(old[row['uuid']]))==row['identity'],'Prior cleanup copper changed'
            if row['uuid']not in already:removed.append({**row,'cleanup_reuse_receipt_sha256':sha(a.reuse_cleanup_receipt),'unchanged_observer_pad_inventory_verified':True})
    # KiCad10 Windows SWIG invalidates cached pad wrappers after bulk native
    # Remove. Apply exact UUID removals to a private parsed native tree, then
    # reload it. Every nonremoved native object remains literally retained.
    remove_ids={r['uuid']for r in removed};tree=parse(source.read_text());tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in remove_ids)]
    cleared=a.out/'private-cleared-input.kicad_pcb';cleared.write_text(dump(tree)+'\n')
    for suffix in ['.kicad_pro','.kicad_dru']:
        p=source.with_suffix(suffix)
        if p.exists():shutil.copyfile(p,cleared.with_suffix(suffix))
    run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'cleared-baseline-drc.json'),str(cleared)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0
    baseline=json.loads((a.out/'cleared-baseline-drc.json').read_text());dangling_ids={i['uuid']for r in baseline['violations']if r['type']in('track_dangling','via_dangling')for i in r['items']}
    # Shared-rail remnants are removed only with native dangling evidence and
    # no physical intersection with any unchanged fitted pad. A conductor
    # still touching an unchanged component is retained for parent routing.
    trim=[]
    for t in b.GetTracks():
        if t.m_Uuid.AsString()not in dangling_ids or t.m_Uuid.AsString()in remove_ids:continue
        s,e=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())
        touching=[]
        for p in b.GetPads():
            if p.GetParentFootprint().GetReference()in scope or p.GetNetname()!=t.GetNetname():continue
            pol=p.GetEffectivePolygon(pcbnew.F_Cu)
            if any(hits(s,e,[mm(pol.Outline(k).CPoint(i))for i in range(pol.Outline(k).PointCount())],w/2)for k in range(pol.OutlineCount())):touching.append(p.GetParentFootprint().GetReference()+'.'+p.GetNumber())
        if not touching:trim.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),identity=identity(t),reason='Native pre-route dangling item; no geometric intersection with any unchanged fitted pad'))
    removed.extend(trim);remove_ids.update(r['uuid']for r in trim);tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in remove_ids)];cleared.write_text(dump(tree)+'\n')
    for iteration in range(1,10):
        report=a.out/f'cleared-baseline-drc-{iteration:02}.json';run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(report),str(cleared)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0
        d=json.loads(report.read_text());ids={i['uuid']for r in d['violations']if r['type']in('track_dangling','via_dangling')for i in r['items']};extra=[]
        for t in b.GetTracks():
            uid=t.m_Uuid.AsString()
            if uid not in ids or uid in remove_ids:continue
            s,e=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth());touching=False
            for p in b.GetPads():
                if p.GetParentFootprint().GetReference()in scope or p.GetNetname()!=t.GetNetname():continue
                pol=p.GetEffectivePolygon(pcbnew.F_Cu)
                if any(hits(s,e,[mm(pol.Outline(k).CPoint(i))for i in range(pol.Outline(k).PointCount())],w/2)for k in range(pol.OutlineCount())):touching=True;break
            if not touching:extra.append(dict(uuid=uid,net=t.GetNetname(),identity=identity(t),reason='Iterative native dangling cleanup; no geometric intersection with any unchanged fitted pad',native_report=report.name))
        if not extra:break
        removed.extend(extra);remove_ids.update(r['uuid']for r in extra);tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in remove_ids)];cleared.write_text(dump(tree)+'\n')
    b=pcbnew.LoadBoard(str(cleared.resolve()));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};pads={}
    for f in fs.values():
        for p in f.Pads():pads.setdefault((f.GetReference(),p.GetNumber()),[]).append(p)
    dest=a.out/'power-groups-routed-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:
        p=source.with_suffix(suffix)
        if p.exists():shutil.copyfile(p,dest.with_suffix(suffix))
    (a.out/'fp-lib-table').write_text((source.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',source.parent.as_posix()))
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
        gap=width/2+.151
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
        v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);b.Add(v);obstacle(v);additions.append(dict(uuid=v.m_Uuid.AsString(),kind=kind,net=net,identity=identity(v)));return v
    def zone(net,layer,points,kind,priority=20):
        z=pcbnew.ZONE(b);z.SetNet(b.FindNet(net));z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority+len(zones))
        o=z.Outline();o.NewOutline()
        for pt in points:o.Append(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
        b.Add(z);zones.append(dict(uuid=z.m_Uuid.AsString(),kind=kind,net=net,layer=b.GetLayerName(layer),polygon_mm=points,pad_connection='solid',thermal_ampacity_qualified=False));return z
    rebuild();exclude_auto=set()
    for name,seed in groups.items():
        u=next(r for r in seed if r.startswith('U'));ox,oy=mm(fs[u].GetPosition())
        def rel(x,y):return(ox+x,oy+y)
        def poly(points):return[rel(x,y)for x,y in points]
        gn=pad(u,'30'if name in ['CORE7','MOTION6']else'9'if name.startswith('FIELD')else'4').GetNetname()
        # Reserve actual underlying adjacent local same-domain references.
        coords=[mm(p.GetPosition())for r in seed for p in fs[r].Pads()if p.GetNumber()]
        bx=(min(p[0]for p in coords)-2,min(p[1]for p in coords)-2,max(p[0]for p in coords)+2,max(p[1]for p in coords)+2)
        rr=[(bx[0],bx[1]),(bx[2],bx[1]),(bx[2],bx[3]),(bx[0],bx[3])]
        zone(gn,pcbnew.F_Cu,rr,'local_exact_domain_top_return',1);zone(gn,pcbnew.In1_Cu,rr,'adjacent_continuous_local_reference',20)
        if name in ['CORE7','MOTION6']:
            zone(gn,pcbnew.In4_Cu,rr,'Kelvin_adjacent_reference',20)
            core=name=='CORE7';coil='L11001'if core else'L11002';sense='R11022'if core else'R11030'
            vin=pad(u,2).GetNetname();sw=pad(u,21).GetNetname();isns=pad(sense,1).GetNetname();out=pad(sense,2).GetNetname();exclude_auto.update([vin,sw,isns,out])
            zone(vin,pcbnew.F_Cu,poly([(-9,-12),(5,-12),(5,-3.1),(-.9,-3.1),(-.9,-.4),(-4.5,-.4),(-4.5,-2.1),(-9,-2.1)]),'input_hf_bus')
            # Native custom VIN lands include the top and left contacts.
            trace(vin,[mm(pad(u,2).GetPosition()),rel(-3.5,-2.5),rel(-3.5,-3.6)],.25,kind='VIN_package_escape')
            sw_x=mm(pad(coil,1).GetPosition())[0]-ox
            zone(sw,pcbnew.F_Cu,poly([(2.5,-2),(sw_x+1.1,-4.55),(sw_x+1.1,4.55),(sw_x-1.1,4.55),(3.5,.7)]),'compact_top_SW_to_coil')
            # Two short package-bank escapes join the broad coil-side region
            # even when the native fill divides the narrow package contour.
            for pin in [21,22]:
                s=mm(pad(u,pin).GetPosition());mid=rel(4.1,s[1]-oy)
                if clear([s,mid],sw,pcbnew.F_Cu,.4):trace(sw,[s,mid],.4,kind='parallel_SW_land_bank_escape')
            wide=[rel(4.1,-1.25),rel(sw_x,-1.25),rel(sw_x,0)]
            if clear(wide,sw,pcbnew.F_Cu,1.5):trace(sw,wide,1.5,kind='SW_land_bank_to_coil_bridge')
            sx=mm(pad(sense,1).GetPosition())[0]-ox;lx=mm(pad(coil,2).GetPosition())[0]-ox
            zone(isns,pcbnew.F_Cu,poly([(lx-.7,-1.65),(sx+.4,-1.65),(sx+.4,1.65),(lx-.7,1.65)]),'coil_to_shunt_power')
            output_x=mm(pad(sense,2).GetPosition())[0]-ox
            zone(out,pcbnew.F_Cu,poly([(output_x+.15,-12),(46,-12),(46,12),(output_x+.15,12)]),'shunt_to_output_bulk_power')
            # Source-anchored Kelvin branches: inner shunt pad edges, separate
            # from the outer high-current polygons and from BIAS supply.
            for pin,sp,dy in [('11','1',4.2),('12','2',5.1)]:
                q=pad(u,pin);r=pad(sense,sp);net=q.GetNetname();start=mm(q.GetPosition());x=mm(r.GetPosition())[0]+(.32 if sp=='1'else-.32)
                ev=(x,oy+(2.4 if pin=='11'else 3.3));rs=(x,oy+1.25)
                candidates=[(rel(-1.5,3.65),[start,rel(-1,3.4),rel(-1.5,3.65)])]if pin=='11'else[(p,[start,p])for p in [rel(.4,4.1),rel(.4,4.2),rel(.6,4.25)]]
                pick=next(((p,ps)for p,ps in candidates if via_clear(p,net)and clear(ps,net,pcbnew.F_Cu,.2)),None)
                if pick is None:unrouted.append(dict(group=name,pin=pin,reason='No valid source-anchored Kelvin escape'));continue
                sv,escape_path=pick
                layer=pcbnew.In3_Cu if pin=='11'else pcbnew.B_Cu
                parallel=[sv,rel(-3.6,3.65),rel(-3.6,7.3),(x,oy+7.3),ev]if pin=='11'else[sv,ev]
                route=parallel if clear(parallel,net,layer,.2)else None
                if route is None:unrouted.append(dict(group=name,pin=pin,reason='No independent inner Kelvin path'));continue
                trace(net,escape_path,.2,kind='shunt_Kelvin_IC_escape');via(net,sv,'shunt_Kelvin_via');trace(net,route,.2,layer,'separate_shunt_Kelvin');via(net,ev,'shunt_Kelvin_via');trace(net,[ev,rs],.2,kind='shunt_inner_pad_Kelvin_tap')
                connections.append(dict(kind='Kelvin',group=name,from_pad=u+'.'+pin,to_pad=sense+'.'+sp,net=net,branch_endpoint_mm=rs))
            # Array on actual ground thermal land; assembly via-in-pad process
            # remains an explicit PCBWay qualification gate.
            ep=mm(pad(u,30).GetPosition())
            for dx in [-1.05,-.35,.35,1.05]:
                for dy in [-.35,.35]:
                    pt=(ep[0]+dx,ep[1]+dy)
                    if via_clear(pt,gn):via(gn,pt,'EP_thermal')
            # BIAS is a low-current branch, not the current-sense path.
            q=pad(u,6);s=mm(q.GetPosition());ev=rel(-3.5,1.25);end=rel(output_x+2,8);bias=[ev,rel(-8,10),rel(output_x+2,10),end]
            if clear([s,ev],out,pcbnew.F_Cu,.2)and via_clear(ev,out)and via_clear(end,out)and clear(bias,out,pcbnew.B_Cu,.2):
                trace(out,[s,ev],.2,kind='separate_BIAS_branch');via(out,ev,'BIAS_supply_via');trace(out,bias,.2,pcbnew.B_Cu,'separate_BIAS_supply');via(out,end,'BIAS_supply_via')
            else:unrouted.append(dict(group=name,net=out,reason='Separate BIAS source branch obstructed'))
            # Reserve the fine-pitch RT escape before CONFIG/COMP support
            # routing can consume its only practical inter-pad corridor.
            q=pad(u,14);r=pad('R11024'if core else'R11032',1);net=q.GetNetname();s,e=mm(q.GetPosition()),mm(r.GetPosition());chosen=None
            for sv in [rel(x,y)for x,y in [(1,3.4),(1,3.5),(1,3.6),(1.2,3.65),(1.25,3.6),(1.3,3.7),(2.2,3.7),(1.1,4)]]:
                if not via_clear(sv,net):continue
                ss=next((ps for ps in paths(s,sv)if clear(ps,net,pcbnew.F_Cu,.2)),None)or grid_path(s,sv,net,pcbnew.F_Cu,pad=1)
                if not ss:continue
                for ev in [(e[0],e[1]+.875),(e[0]-.7,e[1]),(e[0]+.7,e[1])]:
                    if not via_clear(ev,net):continue
                    es=next((ps for ps in paths(ev,e)if clear(ps,net,pcbnew.F_Cu,.2)),None)
                    if not es:continue
                    for layer in [pcbnew.B_Cu,pcbnew.In3_Cu]:
                        middle=next((ps for ps in paths(sv,ev)if clear(ps,net,layer,.2)),None)or grid_path(sv,ev,net,layer,pad=1)
                        if middle:chosen=(sv,ev,ss,es,middle,layer);break
                    if chosen:break
                if chosen:break
            if chosen:
                sv,ev,ss,es,middle,layer=chosen;trace(net,ss,kind='RT_fine_pitch_escape');via(net,sv,'RT_support_via');trace(net,middle,.2,layer,'RT_quiet_support');via(net,ev,'RT_support_via');trace(net,es,kind='RT_resistor_escape');connections.append(dict(kind='RT_support',group=name,from_pad=u+'.14',to_pad=r.GetParentFootprint().GetReference()+'.1',net=net))
            else:unrouted.append(dict(group=name,net=net,reason='Fine-pitch RT escape is obstructed'))
        elif name.startswith('FIELD'):
            coil='L11003'if name=='FIELD_A5'else'L19001';vin=pad(u,4).GetNetname();sw=pad(u,5).GetNetname();out=pad(coil,2).GetNetname();exclude_auto.update([vin,sw,out])
            zone(vin,pcbnew.F_Cu,poly([(-8,-7),(-4,-7),(-4,8),(-8,8)]),'field_input_reservoir_bus')
            s=mm(pad(u,4).GetPosition());trace(vin,[s,rel(-3,1),rel(-5,1)],.35,kind='field_VIN_loop')
            s=mm(pad(u,5).GetPosition());e=mm(pad(coil,1).GetPosition());trace(sw,[s,rel(1.5,2.8),(e[0],oy+2.8),e],.6,kind='field_SW_to_coil')
            x=mm(pad(coil,2).GetPosition())[0]-ox
            zone(out,pcbnew.F_Cu,poly([(x-.8,-4),(27,-4),(27,4),(x-.8,4)]),'field_output_bus')
            q=pad(u,8);s=mm(q.GetPosition());trace(out,[s,rel(2.4,-2),rel(2.4,-4.4),rel(x,-4.4),rel(x,-3.5)],.2,kind='field_BIAS_output_sense')
            ep=mm(pad(u,9).GetPosition())
            for dx in [-.3,.3]:
                pt=(ep[0]+dx,ep[1]-.2)
                if via_clear(pt,gn):via(gn,pt,'EP_thermal')
        else:
            coil='L2001'if name=='MC_1V2'else'L2002';sw=pad(u,2).GetNetname();out=pad(coil,2).GetNetname();exclude_auto.update([sw])
            s=mm(pad(u,2).GetPosition());e=mm(pad(coil,1).GetPosition());trace(sw,[s,(e[0],s[1]),e],.2,kind='MC_SW_package_escape')
            # Local coil/output power link is .8mm outside fine-pitch lands;
            # regulator VOS pin remains a separate low-current Kelvin branch.
            cap='C2002'if name=='MC_1V2'else'C2005';s=mm(pad(coil,2).GetPosition());e=mm(pad(cap,1).GetPosition())
            power_path=next((ps for ps in paths(s,e)if clear(ps,out,pcbnew.F_Cu,.8)),None)
            if power_path is None:unrouted.append(dict(group=name,net=out,reason='No clear .8mm local coil-to-output path'))
            else:trace(out,power_path,.8,kind='MC_coil_output_power')
            # Distributed current does not travel through the .2 mm VOS/FB
            # support traces. Route an explicit .8 mm reservoir feed and a
            # three-conventional-via array into the existing supply plane.
            if name=='MC_IO3':
                start=mm(pad(cap,1).GetPosition());r=mm(pad('R18001',1).GetPosition())
                main=[start,(start[0],oy+7.5),(r[0],oy+7.5),r]
                if clear(main,out,pcbnew.F_Cu,.8):trace(out,main,.8,kind='IO3_main_reservoir_to_damping_power')
                else:unrouted.append(dict(group=name,net=out,reason='Explicit .8mm reservoir-to-damping feed obstructed'))
                net=pad('R18001',2).GetNetname();start=mm(pad('R18001',2).GetPosition());array=[rel(4.9,y)for y in [6,6.8,7.6]]
                feed=[start,array[0],array[-1]]
            else:
                net=out;start=mm(pad(cap,1).GetPosition());array=[rel(-.6,y)for y in [6,6.8,7.6]]
                feed=[start,(start[0],oy+5),array[0],array[-1]]
            if clear(feed,net,pcbnew.F_Cu,.8)and all(via_clear(p,net)for p in array):
                trace(net,feed,.8,kind='MC_main_distribution_plane_feed')
                for p in array:via(net,p,'MC_parallel_distribution_via')
            else:unrouted.append(dict(group=name,net=net,reason='Explicit .8mm main distributed-plane feed/via array obstructed'))
            q=pad(u,6);r=pad('C2001'if name=='MC_1V2'else'C2004',1);s,e=mm(q.GetPosition()),mm(r.GetPosition());n=q.GetNetname();mid=rel(1.6,-.25);wide=[mid,(e[0],mid[1]),e]
            if clear([s,mid],n,pcbnew.F_Cu,.2)and clear(wide,n,pcbnew.F_Cu,.8):trace(n,[s,mid],.2,kind='MC_VIN_fine_pitch_escape');trace(n,wide,.8,kind='MC_VIN_wide_reservoir_feed')
            else:unrouted.append(dict(group=name,net=n,reason='MC VIN input reservoir feed obstructed'))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
    # Stitch each actual same-domain cap return close to its negative pad.
    for name,seed in groups.items():
        u=next(r for r in seed if r.startswith('U'));gn=pad(u,'30'if name in ['CORE7','MOTION6']else'9'if name.startswith('FIELD')else'4').GetNetname()
        for r in seed:
            for p in fs[r].Pads():
                if p.GetNetname()!=gn:continue
                if not r.startswith('C'):
                    b.BuildConnectivity();reference=pad(u,'30'if name in ['CORE7','MOTION6']else'9'if name.startswith('FIELD')else'4')
                    if p==reference or reference.m_Uuid.AsString()in{q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)}:continue
                s=mm(p.GetPosition());cands=[(s[0]+d*x,s[1]+d*y)for d in [.65,.85,1.1,1.4]for x,y in [(0,1),(0,-1),(1,0),(-1,0)]]
                ev=next((e for e in cands if via_clear(e,gn)and clear([s,e],gn,pcbnew.F_Cu,.2)),None)
                if ev:trace(gn,[s,ev],.2,kind='actual_local_return');via(gn,ev,'actual_local_return_stitch')
                else:unrouted.append(dict(ref=r,pin=p.GetNumber(),net=gn,reason='No close conventional return stitch; plane may connect but reviewed stitch is pending'))
    bynet=collections.defaultdict(list)
    for r in scope:
        for p in fs[r].Pads():
            n=p.GetNetname()
            if n and not n.startswith('unconnected-')and 'GND'not in n and not n.endswith('_0V'):bynet[n].append(p)
    # Shared major supplies get independent local support routing sets; a
    # .2 mm support trace must never become a whole-board current feed.
    ref_group={r:name for name,refs in groups.items()for r in refs};main_supply=set(exclude_auto)
    main_supply.update(pad(u,6).GetNetname()for u in ['U2001','U2002']);main_supply.update([pad('R18001',2).GetNetname(),pad('L2001',2).GetNetname(),pad('L2002',2).GetNetname()])
    route_sets=[]
    for net,ps in bynet.items():
        if net in main_supply:
            local=collections.defaultdict(list)
            for p in ps:local[ref_group[p.GetParentFootprint().GetReference()]].append(p)
            route_sets.extend((net,pp)for pp in local.values())
        else:route_sets.append((net,ps))
    # Use ordinary .2mm only for local support signals, timing and bias.
    # Main current paths are the explicitly reviewed polygons above.
    for net,ps in sorted(route_sets,key=lambda x:(len(x[1]),x[0])):
        while True:
            b.BuildConnectivity();clusters={}
            for p in ps:
                ids=tuple(sorted({t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T}|{p.m_Uuid.AsString()}));clusters.setdefault(ids,[]).append(p)
            if len(clusters)<2:break
            vv=list(clusters.values());pairs=sorted([(math.dist(mm(p.GetPosition()),mm(q.GetPosition())),p,q)for i,c in enumerate(vv)for d in vv[i+1:]for p in c for q in d if not(p.GetParentFootprint().GetReference()in ['U11007','U11008']and p.GetNumber()in ['11','12'])and not(q.GetParentFootprint().GetReference()in ['U11007','U11008']and q.GetNumber()in ['11','12'])],key=lambda x:x[0]);choice=None
            for span,p,q in pairs:
                s,e=mm(p.GetPosition()),mm(q.GetPosition());selected=next((path for path in paths(s,e)if clear(path,net,pcbnew.F_Cu,.2)),None)
                if selected:choice=(p,q,selected,None);break
                starts=[(s[0]+d*x,s[1]+d*y)for d in [.7,.75,1,1.4,2,2.8]for x,y in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]]
                ends=[(e[0]+d*x,e[1]+d*y)for d in [.7,.75,1,1.4,2,2.8]for x,y in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]]
                starts={v:next((ps for ps in paths(s,v)if clear(ps,net,pcbnew.F_Cu,.2)),None)for v in starts if via_clear(v,net)};ends={v:next((ps for ps in paths(v,e)if clear(ps,net,pcbnew.F_Cu,.2)),None)for v in ends if via_clear(v,net)};starts={v:ps for v,ps in starts.items()if ps};ends={v:ps for v,ps in ends.items()if ps}
                for sv,ev in sorted(((x,y)for x in starts for y in ends),key=lambda v:math.dist(*v)):
                    if math.dist(sv,ev)<.451:continue
                    path=next((path for path in paths(sv,ev)if clear(path,net,pcbnew.B_Cu,.2)),None)
                    if path:choice=(p,q,path,(sv,ev,starts[sv],ends[ev]));break
                if choice:break
            if not choice:
                # Only local support branches use this maze fallback. Main
                # output currents above have their own explicit wide paths.
                for span,p,q in pairs:
                    s,e=mm(p.GetPosition()),mm(q.GetPosition())
                    if span>20:continue
                    selected=grid_path(s,e,net,pcbnew.F_Cu)
                    if selected:choice=(p,q,selected,None);break
            if not choice:unrouted.append(dict(net=net,clusters=len(clusters),reason='No clear local support path'));break
            p,q,path,vs=choice
            if vs:
                sv,ev,ss,es=vs;trace(net,ss);via(net,sv,'support_escape');trace(net,path,layer=pcbnew.B_Cu);via(net,ev,'support_escape');trace(net,es)
            else:trace(net,path)
            connections.append(dict(kind='support',from_pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),to_pad=q.GetParentFootprint().GetReference()+'.'+q.GetNumber(),net=net))
        print(json.dumps(dict(net=net,connections=len(connections))),flush=True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(dest),b)
    # Native DRC remains exhaustive, with no ignored or changed design rules.
    run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc-00.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');(a.out/'drc-00.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
    drc=json.loads((a.out/'drc-00.json').read_text());assert not drc.get('ignored_checks')
    final=pcbnew.LoadBoard(str(dest));final.BuildConnectivity();after={t.m_Uuid.AsString():identity(t)for t in final.GetTracks()};rem={r['uuid']for r in removed}
    assert all(after.get(k)==v for k,v in old.items()if k not in rem),'Unrelated retained copper changed'
    assert sha(source)==initial_sha,'Source PCB changed'
    assert sha(Path(__file__))==tool_sha and sha(a.recipes)==recipe_sha,'Routing tool/recipe changed during run'
    receipt=dict(source_board=str(source),source_sha256=initial_sha,source_unchanged=True,old_copper_items=len(old),retained_copper_items=len(old)-len(removed),exact_removed_private_copper=removed,added_copper=additions,added_zones=zones,connections=connections,remaining_local_routing=unrouted,native_drc_types=dict(collections.Counter(x['type']for x in drc['violations'])),native_uncapped_unconnected=final.GetConnectivity().GetUnconnectedCount(False),native_unconnected_items=len(drc['unconnected_items']),unrelated_copper_preserved=True,manufacturing_ready=False,ampacity_qualified=False,thermal_qualified=False,stability_qualified=False,source_hashes={str(a.recipes):recipe_sha,str(Path(__file__)):tool_sha},board_sha256=sha(dest))
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k not in ['added_copper','added_zones','connections','remaining_local_routing','exact_removed_private_copper']}))
if __name__=='__main__':main()
