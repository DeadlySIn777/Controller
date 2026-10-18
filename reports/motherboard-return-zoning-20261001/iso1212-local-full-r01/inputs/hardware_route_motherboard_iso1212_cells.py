"""Route the adopted twelve DI and four probe/safety ISO1212 cells.

Exact native pad/net roles are authoritative, including the opposite RSENSE
pin orientation in the two probe channels. Local receiver loops and own
returns are routed; external field terminals, logic consumers and real IO3
distribution remain independently required. No SUB is joined to any ground.
"""
from __future__ import annotations
import argparse,collections,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import ROOT,sha,write
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_route_selected_additive import immutable_objects,zone_definitions
from hardware_build_assembly import parse,dump,children,child,value
from hardware_zone_motherboard_returns import dump_board
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def recipes():
    out=[]
    for i in range(12):
        out.append(dict(ic=f'U{8001+i}',bypass=f'C{8101+i}',channels=[dict(thr=f'R{8001+2*i+j}',rs=f'R{8101+2*i+j}',bias=f'R{8201+2*i+j}',cin=f'C{8001+2*i+j}')for j in range(2)]))
    out.append(dict(ic='U14031',bypass='C14058',bulk='C14059',channels=[dict(thr=f'R{14069+3*j}',rs=f'R{14070+3*j}',bias=f'R{14071+3*j}',tvs=f'D{14013+j}')for j in range(2)]))
    for i in range(3):
        out.append(dict(ic=f'U{19001+i}',bypass=f'C{19003+3*i}',channels=[dict(thr=f'R{19001+6*i+3*j}',rs=f'R{19002+6*i+3*j}',bias=f'R{19003+6*i+3*j}',cin=f'C{19001+3*i+j}')for j in range(2)]))
    return out


def references(rows=None):
    refs=set()
    for r in rows or recipes():
        refs|={r['ic'],r['bypass']}
        if 'bulk'in r:refs.add(r['bulk'])
        for c in r['channels']:refs|=set(c.values())
    return refs


def apply(b,selected=None):
    rows=recipes();rows=[r for r in rows if selected is None or r['ic']in selected]
    fs={f.GetReference():f for f in b.GetFootprints()};pads={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()}
    added=[];zones=[];checks=[];receiving=[];poses=[]
    def pad(r,p):return pads[r,str(p)]
    def trace(net,points,width=.2,kind='local_signal',layer=pcbnew.F_Cu):
        if not b.FindNet(net):raise ValueError('Missing actual native net '+net)
        for s,e in zip(points,points[1:]):
            if math.dist(s,e)<1e-6:continue
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(width));t.SetLayer(layer);b.Add(t)
            added.append(dict(uuid=t.m_Uuid.AsString(),kind=kind,identity=identity(t)))
    def via(net,p,kind):
        v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(p));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v)
        added.append(dict(uuid=v.m_Uuid.AsString(),kind=kind,identity=identity(v)))
        return v
    def zone(net,layer,points,kind):
        z=pcbnew.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet(net));z.SetZoneName(kind);z.SetAssignedPriority(30);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.2));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.Outline().NewOutline()
        for x,y in points:z.Outline().Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
        b.Add(z);zones.append(dict(uuid=z.m_Uuid.AsString(),net=net,layer=b.GetLayerName(layer),polygon_mm=points,kind=kind))
    def expect(items,kind):
        nets={pad(r,p).GetNetname()for r,p in items}
        if len(nets)!=1 or next(iter(nets)).startswith('unconnected-'):raise ValueError('Real pad/net role contradiction '+repr(items))
        checks.append(dict(kind=kind,net=next(iter(nets)),endpoints=[dict(reference=r,pin=str(p),pad_uuid=pad(r,p).m_Uuid.AsString())for r,p in items]))
        return next(iter(nets))
    for row in rows:
        u=row['ic'];f=fs[u]
        if abs(f.GetOrientationDegrees())>1e-6 or f.GetLayer()!=pcbnew.F_Cu:raise ValueError('Reviewed cell orientation/side differs '+u)
        ox,oy=mm(f.GetPosition());rel=lambda x,y:(ox+x,oy+y)
        if u!='U14031':
            #SENSE is physically above IN on both native ISO1212 channels.
            #Align the passive's real terminals to that order. The previous
            #horizontal near-SENSE/far-IN order forced an input crossing.
            for j,c in enumerate(row['channels']):
                for ref,pos,angle in [(c['rs'],rel(5.35,-1.5 if j==0 else 1.5),270),
                    (c['cin'],rel(8.05,-1 if j==0 else 1),0)]:
                    fp=fs[ref];before=dict(position_mm=mm(fp.GetPosition()),rotation_degrees=fp.GetOrientationDegrees(),layer=b.GetLayerName(fp.GetLayer()))
                    fp.SetPosition(xy(pos));fp.SetOrientationDegrees(angle)
                    poses.append(dict(reference=ref,before=before,after=dict(position_mm=mm(fp.GetPosition()),rotation_degrees=fp.GetOrientationDegrees(),layer=b.GetLayerName(fp.GetLayer())),reason='Native SENSE/IN terminal alignment and compact noncrossing input filter loop; refs/MPNs/relative lands/nets unchanged'))
        lg=expect([(u,1),(u,8),(row['bypass'],2)],'actual_logic_return')
        fg=expect([(u,9),(u,14)],'actual_own_field_return')
        vcc=expect([(u,2),(u,3),(row['bypass'],1)],'true_VCC_EN_bypass')
        if lg!='/LOGIC_GND' or vcc!='/IO_3V3' or fg not in ['/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V']:raise ValueError('Unexpected actual receiver domain '+u)
        for layer in [pcbnew.F_Cu,pcbnew.B_Cu]:
            zone(lg,layer,[rel(-7.8,-5.9),rel(-.3,-5.9),rel(-.3,5.9),rel(-7.8,5.9)],u+'_LOCAL_LOGIC_RETURN')
            zone(fg,layer,[rel(4,-5.9),rel(14.8,-5.9),rel(14.8,5.9),rel(4,5.9)],u+'_LOCAL_FIELD_RETURN_OUTSIDE_SUB')
        trace(vcc,[mm(pad(u,2).GetPosition()),mm(pad(row['bypass'],1).GetPosition())],kind='actual_VCC_bypass_short_loop')
        trace(vcc,[mm(pad(u,3).GetPosition()),rel(-3.8,-.9525),rel(-3.8,-1.5875)],kind='EN_true_VCC')
        p=rel(-4.525,-2.75);trace(vcc,[mm(pad(row['bypass'],1).GetPosition()),p],kind='receiving_IO3_escape');v=via(vcc,p,'receiving_IO3')
        receiving.append(dict(ic=u,net=vcc,uuid=v.m_Uuid.AsString(),position_mm=p,global_positive_feed_required=True))
        for pin,path in [(1,[rel(-2.7,-2.2225),rel(-3.85,-2.2225),rel(-3.85,-3.3)]),(8,[rel(-2.7,2.2225),rel(-3.6,2.2225),rel(-3.6,3.3)])]:
            trace(lg,path,kind='actual_logic_IC_return');via(lg,path[-1],'logic_IC_return')
        p=rel(-6.7,-2.6);trace(lg,[mm(pad(row['bypass'],2).GetPosition()),p],kind='own_bypass_return');via(lg,p,'bypass_return')
        if 'bulk'in row:
            expect([(row['bulk'],1),(u,2)],'actual_probe_bulk_supply');expect([(row['bulk'],2),(u,1)],'actual_probe_bulk_return')
            trace(vcc,[mm(pad(row['bulk'],1).GetPosition()),rel(-4.525,-4.2),rel(-4.525,-2.75)],kind='actual_bulk_supply')
            p=rel(-6.7,-4.2);trace(lg,[mm(pad(row['bulk'],2).GetPosition()),p],kind='own_bulk_return');via(lg,p,'bulk_return')
        path=[rel(2.7,-.9525),rel(3.8,-.9525),rel(3.8,0),rel(4.5,0)];trace(fg,path,kind='field_IC_return_14');via(fg,path[-1],'field_IC_return_14')
        path=[rel(2.7,2.2225),rel(2.7,3.3)];trace(fg,path,kind='field_IC_return_9');via(fg,path[-1],'field_IC_return_9')
        trace(fg,[rel(2.7,3.3),rel(4.5,3.3)],kind='own_field_return_OUTSIDE_SUB',layer=pcbnew.B_Cu)
        for j,c in enumerate(row['channels']):
            spin,ipin,opin=(16,15,4)if j==0 else(11,10,5)
            sense=pad(u,spin).GetNetname();inp=pad(u,ipin).GetNetname();rs_s=next((p for p in [1,2]if pad(c['rs'],p).GetNetname()==sense),None);rs_i=next((p for p in [1,2]if pad(c['rs'],p).GetNetname()==inp),None)
            if rs_s is None or rs_i is None or rs_s==rs_i:raise ValueError('RSENSE physical pin assignment mismatch '+c['rs'])
            expect([(u,spin),(c['rs'],rs_s),(c['thr'],2)],'actual_SENSE_RTHR_RSENSE')
            expect([(u,ipin),(c['rs'],rs_i)],'actual_IN_RSENSE')
            sp=mm(pad(u,spin).GetPosition());rp=mm(pad(c['rs'],rs_s).GetPosition())
            if u=='U14031':
                y=-2.35 if j==0 else .55
                points=[sp,rel(3.75,sp[1]-oy),rel(3.75,y),rel(rp[0]-ox,y),rp]
            else:points=[sp,(rp[0],sp[1]),rp]
            trace(sense,points,kind='compact_actual_SENSE_RSENSE')
            ip=mm(pad(u,ipin).GetPosition());rp=mm(pad(c['rs'],rs_i).GetPosition())
            trace(inp,[ip,(rp[0],ip[1]),rp],kind='compact_actual_IN_RSENSE')
            rp=mm(pad(c['rs'],rs_s).GetPosition());tp=mm(pad(c['thr'],2).GetPosition())
            if 'cin'in c:
                expect([(c['cin'],1),(u,spin)],'actual_CIN_SENSE');expect([(c['cin'],2),(u,14)],'actual_CIN_field_return')
                cp=mm(pad(c['cin'],1).GetPosition());trace(sense,[rp,(cp[0],rp[1]),cp],kind='compact_CIN_SENSE')
                y=-4.2 if j==0 else 3.5
                trace(sense,[cp,(cp[0],oy+y),rel(tp[0]-ox,y),tp],kind='actual_RTHR_to_CIN_SENSE')
                gp=mm(pad(c['cin'],2).GetPosition());p=(gp[0]-.7,gp[1]+1.2);trace(fg,[gp,p],kind='CIN_own_field_return');via(fg,p,'CIN_field_return')
            else:
                y=-3.6 if j==0 else 3.6
                trace(sense,[rp,(rp[0],oy+y),rel(tp[0]-ox,y),tp],kind='actual_RTHR_to_probe_SENSE')
            out=expect([(u,opin),(c['bias'],1)],'actual_logic_OUT_bias');expect([(c['bias'],2),(u,1)],'actual_bias_logic_return')
            qp=mm(pad(u,opin).GetPosition());bp=mm(pad(c['bias'],1).GetPosition())
            points=[qp,(bp[0],qp[1]),bp]if j==0 else[qp,rel(-3.9,.3175),rel(-3.9,1.4),bp]
            trace(out,points,kind='actual_receiver_output_to_bias')
            p=rel(-7.1,.2 if j==0 else 1.9);trace(lg,[mm(pad(c['bias'],2).GetPosition()),p],kind='bias_own_logic_return');via(lg,p,'bias_logic_return')
            if 'tvs'in c:
                field=expect([(c['thr'],1),(c['tvs'],1)],'actual_external_RTHR_TVS');expect([(c['tvs'],2),(u,14)],'actual_TVS_field_return')
                trace(field,[mm(pad(c['thr'],1).GetPosition()),mm(pad(c['tvs'],1).GetPosition())],.4,kind='actual_RTHR_external_TVS')
                p=rel(22.7,-3.3 if j==0 else 3.3);trace(fg,[mm(pad(c['tvs'],2).GetPosition()),p],.4,kind='own_TVS_return');via(fg,p,'TVS_return')
                trace(fg,[p,rel(14.4,-3.3 if j==0 else 3.3)],.4,kind='own_TVS_return_to_local_field_plane',layer=pcbnew.B_Cu)
    return dict(exact_added_copper=added,exact_added_zones=zones,local_endpoint_checks=checks,actual_receiving_IO3_vias=receiving,scope_refs=sorted(references(rows)),exact_passive_pose_changes=poses)


def validate_local(b,checks):
    b.BuildConnectivity();pads={p.m_Uuid.AsString():p for p in b.GetPads()};failed=[]
    for row in checks:
        ids={p['pad_uuid']for p in row['endpoints']};first=pads[next(iter(ids))]
        connected={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(first)if isinstance(x,pcbnew.PAD)}|{first.m_Uuid.AsString()}
        if not ids<=connected:failed.append(dict(**row,missing=sorted(ids-connected)))
    return dict(passed=not failed,checked_local_endpoint_groups=len(checks),failed=failed)


def land_inventory(b):
    """Local native lands stay exact through a reviewed placement rotation."""
    return {p.m_Uuid.AsString():(f.GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetFPRelativePosition()),tuple(p.GetSize()),p.GetShape(),p.GetAttribute(),tuple(p.GetDrillSize()),
        round((p.GetOrientationDegrees()-f.GetOrientationDegrees())%360,6),tuple(p.GetLayerSet().Seq()))for f in b.GetFootprints()for p in f.Pads()}


def validate_spacing(b,rows=None):
    """Exact copper edges of RTHR external versus protected component pins."""
    fs={f.GetReference():f for f in b.GetFootprints()};result=[]
    def rect_distance(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
    def box(p):
        q=p.GetBoundingBox();return [pcbnew.ToMM(x)for x in [q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()]]
    for row in rows or recipes():
        u=row['ic'];protected=[p for p in fs[u].Pads()if p.GetNumber()in ['9','10','11','12','13','14','15','16']]
        for c in row['channels']:
            protected.extend(p for p in fs[c['rs']].Pads()if p.GetNumber())
            if 'cin'in c:protected.extend(p for p in fs[c['cin']].Pads()if p.GetNumber())
        for c in row['channels']:
            external=next(p for p in fs[c['thr']].Pads()if p.GetNumber()=='1');minimum=min(rect_distance(box(external),box(p))for p in protected)
            result.append(dict(external_ref=c['thr'],ic=u,minimum_external_to_protected_copper_mm=minimum,required_mm=4,passed=minimum>=4))
    return dict(passed=all(r['passed']for r in result),channels=result)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--fixture',action='store_true');a=ap.parse_args()
    base=a.board.resolve();out=a.out.resolve()
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('New immutable report directory required')
    out.mkdir(parents=True);inputs=out/'inputs';inputs.mkdir();shutil.copy2(base,inputs/base.name);shutil.copy2(Path(__file__),inputs/Path(__file__).name)
    b=pcbnew.LoadBoard(str(base));old_cu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};old_pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};old_zones={z.m_Uuid.AsString()for z in b.Zones()}
    if a.fixture:
        refs=references();tree=parse(base.read_text(encoding='utf-8'))
        tree[:]=[n for n in tree if not(isinstance(n,list)and n and n[0]in ['segment','via','arc','zone'])]
        #Native footprint property order is not assumed in the actual filter.
        tree=[n for n in tree if not(isinstance(n,list)and n and n[0]=='footprint'and not any(value(p[1])=='Reference'and value(p[2])in refs for p in children(n,'property')))]
        f=out/'fixture-source.kicad_pcb';f.write_text(dump_board(tree),encoding='utf-8');b=pcbnew.LoadBoard(str(f));old_cu={};old_zones=set();old_pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
    old_lands=land_inventory(b);metadata=apply(b)
    if land_inventory(b)!=old_lands:raise ValueError('Relative source lands/nets/UUID changed outside reviewed placement')
    spacing=validate_spacing(b);write(out/'RTHR-external-copper-spacing.json',spacing)
    if not spacing['passed']:raise ValueError('Actual RTHR external-to-protected copper violates TI4mm spacing')
    new_pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};dest=out/'motherboard-iso1212-cells-routed-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
    if(base.parent/'fp-lib-table').exists():(out/'fp-lib-table').write_text((base.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',base.parent.as_posix()),encoding='utf-8')
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    d=json.loads((out/'drc.json').read_text());fresh=pcbnew.LoadBoard(str(dest));now={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    if any(now.get(k)!=v for k,v in old_cu.items())or new_pads!={p.m_Uuid.AsString():pad_identity(p)for p in fresh.GetPads()}:raise ValueError('Old copper or reviewed post-pose source pad identity changed')
    if any(now.get(r['uuid'])!=r['identity']for r in metadata['exact_added_copper']):raise ValueError('Added native copper net/geometry changed')
    local=validate_local(fresh,metadata['local_endpoint_checks']);write(out/'local-endpoint-proof.json',local)
    receipt=dict(**metadata,source_board=str(base),source_sha256=sha(base),board_sha256=sha(dest),native_DRC_types=dict(collections.Counter((x['type'])for x in d['violations'])),native_ignored=d['ignored_checks'],source_relative_lands_nets_UUIDs_and_old_Cu_preserved=True,exact_global_pad_pose_delta_only_for_reviewed60_passives=True,RTHR4mm_all32_channels_proven=spacing['passed'],local_loop_proof=local['passed'],global_positive_feeds_implemented=False,fixture_only=a.fixture,manufacturing_ready=False,physical_qualification=False)
    write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in metadata},indent=2))


if __name__=='__main__':main()
