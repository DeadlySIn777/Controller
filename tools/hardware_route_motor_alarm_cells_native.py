"""Route actual ISO1212 alarm cells on a copy with exact domain returns.

The package field-side B.Cu half stays reserved for separate floating SUB
thermal islands. This proof closes local cells, not external feeds, terminal
routes, safety certification or a finished whole board.
"""
from pathlib import Path
import argparse,collections,hashlib,json,shutil,subprocess,math
import pcbnew
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_build_assembly import parse,dump,child,value
from hardware_motor_alarm_layout import recipes

ROOT=Path(__file__).resolve().parents[1]
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert not a.out.exists()and a.out.resolve().is_relative_to(ROOT/'reports');a.out.mkdir(parents=True);before=sha(a.board)
    rec=recipes(json.loads((ROOT/'hardware/motherboard_motors/design.json').read_text()));b=pcbnew.LoadBoard(str(a.board.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};groups={n:g for n,g in rec['groups'].items()if next(r for r in g if r.startswith('U'))in fs};scope={r for g in groups.values()for r in g};assert len(scope)in(12,72)
    old_cu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};old_zones={z.m_Uuid.AsString()for z in b.Zones()};old_pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};netrefs=collections.defaultdict(set)
    for p in b.GetPads():
        if p.GetNetname()and not p.GetNetname().startswith('unconnected-'):netrefs[p.GetNetname()].add(p.GetParentFootprint().GetReference())
    private={n for n,refs in netrefs.items()if refs<=scope and '_SUB_'not in n};removed=[dict(uuid=t.m_Uuid.AsString(),identity=identity(t),reason='All actual fitted pads on this private alarm net belong to reviewed moving cells')for t in b.GetTracks()if t.GetNetname()in private]
    ids={r['uuid']for r in removed};tree=parse(a.board.read_text());tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in ids)];cleared=a.out/'private-cleared-input.kicad_pcb';cleared.write_text(dump(tree)+'\n');b=pcbnew.LoadBoard(str(cleared.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};pads={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()};additions=[];zones=[];channels=[]
    def pad(r,p):return pads[(r,str(p))]
    def trace(net,points,width=.2,kind='local_signal',layer=pcbnew.F_Cu):
        for s,e in zip(points,points[1:]):
            if math.dist(s,e)<1e-6:continue
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(width));t.SetLayer(layer);b.Add(t);additions.append(dict(uuid=t.m_Uuid.AsString(),kind=kind,net=net,identity=identity(t)))
    def via(net,pos,kind):
        v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pos));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);additions.append(dict(uuid=v.m_Uuid.AsString(),kind=kind,net=net,identity=identity(v),automatic_net_reassignment_disabled=True,all_layer_annuli_retained_for_clearance=True))
    def zone(net,layer,points,kind):
        z=pcbnew.ZONE(b);z.SetNet(b.FindNet(net));z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetAssignedPriority(100+len(zones));o=z.Outline();o.NewOutline()
        for p in points:o.Append(pcbnew.FromMM(p[0]),pcbnew.FromMM(p[1]))
        b.Add(z);zones.append(dict(uuid=z.m_Uuid.AsString(),net=net,layer=b.GetLayerName(layer),kind=kind,polygon_mm=points))
    for name,g in groups.items():
        u=next(r for r in g if r.startswith('U'));pidx=int(u[1:])-6035;ox,oy=mm(fs[u].GetPosition());rel=lambda x,y:(ox+x,oy+y);lg=pad(u,1).GetNetname();fg=pad(u,14).GetNetname();vcc=pad(u,2).GetNetname();bypass=f'C{6015+pidx*3}'
        for layer in [pcbnew.F_Cu,pcbnew.B_Cu]:
            zone(lg,layer,[rel(-7.8,-4.2),rel(-.3,-4.2),rel(-.3,4.2),rel(-7.8,4.2)],'logic_only_local_return')
            # Reserve B.Cu field package half (x .3..4) for separate SUB islands.
            lo=3.8 if layer==pcbnew.F_Cu else 4.0
            zone(fg,layer,[rel(lo,-5.9),rel(24.2,-5.9),rel(24.2,5.9),rel(lo,5.9)],'field_only_local_return_outside_SUB_half')
        trace(vcc,[mm(pad(u,2).GetPosition()),mm(pad(bypass,1).GetPosition())],kind='VCC_1p95mm_bypass')
        trace(vcc,[mm(pad(u,3).GetPosition()),rel(-3.8,-.9525),rel(-3.8,-1.5875)],kind='EN_true_VCC_tie')
        trace(vcc,[mm(pad(bypass,1).GetPosition()),rel(-4.65,-2.75)],kind='receiving_logic_rail_escape');via(vcc,rel(-4.65,-2.75),'receiving_logic_rail_via')
        for pin,points in [(1,[rel(-2.7,-2.2225),rel(-3.85,-2.2225),rel(-3.85,-3.3)]),(8,[rel(-2.7,2.2225),rel(-3.6,2.2225),rel(-3.6,3.3)])]:
            trace(lg,points,kind='logic_IC_return');via(lg,points[-1],'logic_IC_return_via')
        pos=mm(pad(bypass,2).GetPosition());ev=rel(-6.2,-2.6);trace(lg,[pos,ev],kind='own_bypass_return');via(lg,ev,'own_bypass_return_via')
        for pin,points in [(14,[rel(2.7,-.9525),rel(3.8,-.9525),rel(3.8,0),rel(4.5,0)]),(9,[rel(2.7,2.2225),rel(3.8,2.2225),rel(3.8,3.4),rel(4.5,3.4)])]:
            trace(fg,points,kind='field_IC_return_outside_SUB');via(fg,points[-1],'field_IC_return_via')
        for j in [0,1]:
            n=pidx*2+j;thr=f'R{6051+n*3}';rs=f'R{6052+n*3}';bias=f'R{6053+n*3}';cin=f'C{6013+pidx*3+j}';tvs=f'D{6025+n}';sense=pad(rs,1).GetNetname();inp=pad(rs,2).GetNetname();out=pad(bias,1).GetNetname();field=pad(thr,1).GetNetname();spin=16 if j==0 else 11;ipin=15 if j==0 else 10;opin=4 if j==0 else 5
            sp=mm(pad(u,spin).GetPosition());rp=mm(pad(rs,1).GetPosition());trace(sense,[sp,(rp[0],sp[1]),rp,mm(pad(cin,1).GetPosition())],kind='compact_SENSE_RSENSE_CIN')
            cp=mm(pad(cin,1).GetPosition());tp=mm(pad(thr,2).GetPosition());points=[cp,rel(cp[0]-ox,-3.65),rel(tp[0]-ox,-3.65),tp]if j==0 else[cp,(cp[0],tp[1]),tp];trace(sense,points,kind='RTHR_low_voltage_end_to_CIN')
            ip=mm(pad(u,ipin).GetPosition());rp=mm(pad(rs,2).GetPosition());trace(inp,[ip,rel(4.7,ip[1]-oy),rel(4.7,rp[1]-oy),rp],kind='compact_IN_RSENSE')
            trace(field,[mm(pad(thr,1).GetPosition()),mm(pad(tvs,1).GetPosition())],.4,kind='RTHR_external_to_TVS')
            ev=rel(9.15,-1.525 if j==0 else 1.775);trace(fg,[mm(pad(cin,2).GetPosition()),ev],kind='CIN_own_field_return');via(fg,ev,'CIN_field_return_via')
            ev=rel(23.5,-3.3 if j==0 else 3.3);trace(fg,[mm(pad(tvs,2).GetPosition()),ev],.4,kind='TVS_field_return');via(fg,ev,'TVS_field_return_via')
            qp=mm(pad(u,opin).GetPosition());bp=mm(pad(bias,1).GetPosition());points=[qp,(bp[0],qp[1]),bp]if j==0 else[qp,rel(-3.9,.3175),rel(-3.9,1.4),bp];trace(out,points,kind='actual_ALM_receiver_to_bias')
            ev=rel(-7.1,.2 if j==0 else 1.9);trace(lg,[mm(pad(bias,2).GetPosition()),ev],kind='bias_own_logic_return');via(lg,ev,'bias_logic_return_via')
            channels.append(dict(channel=n,ic=u,local_ref_set=[thr,rs,bias,cin,tvs,bypass],SUB_thermal_islands_not_part_of_local_signal_route=True))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'motor-alarm-cells-routed-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:
        p=a.board.with_suffix(suffix)
        if p.exists():shutil.copyfile(p,dest.with_suffix(suffix))
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
    # A clean DRC alone cannot detect automatic native via net reassignment.
    q=pcbnew.LoadBoard(str(dest));after={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};qpads={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};assert old_pads==qpads
    for uid,row in old_cu.items():
        if uid not in ids:assert row==after[uid],f'Unrelated retained copper changed {uid}'
    for row in additions:
        assert row['identity']==after[row['uuid']],f'Added copper net or geometry changed {row["uuid"]}'
    free={t.m_Uuid.AsString():t.GetIsFree()for t in q.GetTracks()if isinstance(t,pcbnew.PCB_VIA)}
    assert all(free[r['uuid']]for r in additions if r.get('automatic_net_reassignment_disabled'))
    run=subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());q.BuildConnectivity()
    assert sha(a.board)==before
    receipt=dict(source_board=str(a.board),source_sha256=before,source_unchanged=True,tool_sha256=sha(Path(__file__)),candidate_sha256=sha(dest),scope_refs=sorted(scope),channels=channels,exact_removed_private_copper=removed,exact_added_copper=additions,exact_added_zones=zones,all_retained_pads_and_other_copper_preserved=True,added_via_net_reassignment_disabled_and_post_fill_identity_verified=True,native_drc_types=dict(collections.Counter(r['type']for r in d['violations'])),actual_uncapped_whole_board_unconnected=q.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k not in('channels','exact_removed_private_copper','exact_added_copper','exact_added_zones','scope_refs')}))
if __name__=='__main__':main()
