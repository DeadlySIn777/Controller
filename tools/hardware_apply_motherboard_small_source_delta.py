"""Apply exactly four counter taps, twenty functional NCs and source22/C18001.

All old native lands, poses and copper are invariant. New parts use actual
manufacturer lands; five diagnostic and reset bypasses have explicit owners.
"""
import argparse,collections,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import (sha,load,write,native_parts_and_nets,load_exact_footprint,
    copper_pad,pad_template,courtyard_relative,Occupancy)
from hardware_route_logic_return import identity,xy,mm,segment_hits_box
from hardware_route_local_signals import GeometryIndex
from hardware_reconcile_motherboard_peripheral_pcb import piece
from hardware_build_assembly import parse,dump,child,children,value

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('board','source','review','out'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();base=a.board.resolve();source=a.source.resolve();out=a.out.resolve()
    if out.exists():raise ValueError('Fresh owned output required')
    review=load(a.review);model=load(source/'design.json');parts=model['components']
    if review['base_sha256']!=sha(base) or review['source_netlist_sha256']!=sha(source/'netlist.xml'):
        raise ValueError('Frozen exact source delta stale')
    if review['removed_references'] or review['footprint_replacements']:raise ValueError('No removed part or land replacement allowed')
    native,nodes=native_parts_and_nets(source/'netlist.xml',parts)
    nc={(r['reference'],r['pin']) for r in load(source/'assembly-map.json')['native_unused_functional_dispositions_allowed']}
    counter={('U13001','44'),('U13004','29'),('U13008','29'),('U14501','44')}
    changes={(r['reference'],r['pin']):r for r in review['changes']}
    if set(changes)!=nc|counter or len(nc)!=20:raise ValueError('Only exact24 existing pin changes allowed')
    if any(r['old_net_copper_items'] or r['old_net_zones'] for r in changes.values()):
        raise ValueError('No old copper may be abandoned by the source delta')
    b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
    oldtracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    oldpieces={(r,p.m_Uuid.AsString()):piece(p) for r,f in fps.items() for p in f.Pads()}
    poses={r:(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees()) for r,f in fps.items()}
    templates={r:collections.Counter(pad_template(p) for p in f.Pads()) for r,f in fps.items()}
    nets={str(n.GetNetname()):n for n in b.GetNetsByName().values()};code=max(n.GetNetCode() for n in nets.values())+1
    for name in sorted(set(nodes.values())-set(nets)):
        n=pcbnew.NETINFO_ITEM(b,name,code);b.Add(n);nets[name]=n;code+=1
    for ref,f in fps.items():
        for pad in f.Pads():
            key=(ref,pad.GetNumber())
            if key in changes:
                if str(pad.GetNetname())!=changes[key]['old_native_net']:raise ValueError('Old native pin changed '+str(key))
                pad.SetNet(nets[nodes[key]])
    added={};lands={}
    wanted={'R13057','R13058','R13059','R14533','C18001'}|{
        'U22001','U22002','U22003','R22001','R22002'}|{f'C2200{i}' for i in range(1,6)}|{
        f'TP2200{i}' for i in range(1,5)}|{f'H2200{i}' for i in range(1,7)}
    if set(parts)-set(fps)!=wanted:raise ValueError('Exact25 new native footprints required')
    occupied=Occupancy(courtyard_relative(f) for f in fps.values())
    occupied.append((331.,278.,371.,333.));occupied.append((421.87,277.3,447.27,340.165))
    index=GeometryIndex()
    for t in b.GetTracks():
        if not t.IsOnLayer(pcbnew.F_Cu):continue
        start,end=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth())
        box=(min(start[0],end[0])-w/2,min(start[1],end[1])-w/2,max(start[0],end[0])+w/2,max(start[1],end[1])+w/2)
        index.add((str(t.GetNetname()),box),box)
    def clear(f):
        for pad in f.Pads():
            if not pad.IsOnLayer(pcbnew.F_Cu):continue
            bb=pad.GetBoundingBox();box=tuple(pcbnew.ToMM(v) for v in (bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()))
            for net,tbox in index.candidates((box[0],box[1]),(box[2],box[3]),.2):
                if net!=str(pad.GetNetname()) and segment_hits_box(tbox[:2],tbox[2:],box,.2):return False
        return True
    placements=[];reserved={}
    def add(ref,desired,owner=None,near_limit=40.,fixed=None):
        fp,file=load_exact_footprint(parts[ref]['footprint'],source,base);lands[str(file)]=sha(file)
        fp.SetReference(ref);fp.SetValue(parts[ref]['value']);fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.F_Fab);fp.Reference().SetTextSize(xy((.65,.65)));fp.Reference().SetTextThickness(pcbnew.FromMM(.1))
        fp.SetDNP(parts[ref].get('dnp',False));component=native[ref]
        fp.SetPath(pcbnew.KIID_PATH(component.find('sheetpath').attrib['tstamps']+component.findtext('tstamps')))
        b.Add(fp)
        for pad in fp.Pads():
            if copper_pad(pad):pad.SetNet(nets[nodes[ref,pad.GetNumber()]])
        options=[]
        for angle in ([0.] if fixed else (0.,90.,180.,270.)):
            fp.SetOrientationDegrees(angle);fp.SetPosition(xy((0,0)));box=courtyard_relative(fp)
            if owner:
                target,signal,grounds=owner;tp=next(p for p in fps[target].Pads() if p.GetNumber()==signal)
                cp=next(p for p in fp.Pads() if p.GetNumber()=='1');sx,sy=mm(tp.GetPosition());cx,cy=mm(cp.GetPosition())
                want=(sx-cx,sy-cy);radius=5.
            else:want=desired;radius=near_limit
            if fixed:positions=[fixed]
            else:positions=[(want[0]+i/2,want[1]+j/2) for i in range(-int(radius*2),int(radius*2)+1) for j in range(-int(radius*2),int(radius*2)+1)]
            for x,y in positions:
                bb=(x+box[0],y+box[1],x+box[2],y+box[3])
                halo=3. if ref.startswith('U220') else 0.
                room=(bb[0]-halo,bb[1]-halo,bb[2]+halo,bb[3]+halo)
                if room[0]<.4 or room[1]<.4 or room[2]>459.6 or room[3]>339.6 or occupied.collision(room,.25):continue
                from hardware_populate_motherboard_pcb import intersects
                if any(intersects(room,other,.25) for r,other in reserved.items() if not owner or r!=owner[0]):continue
                fp.SetPosition(xy((x,y)))
                if not clear(fp):continue
                distance=None;rd=None
                if owner:
                    cp=next(p for p in fp.Pads() if p.GetNumber()=='1');cg=next(p for p in fp.Pads() if p.GetNumber()=='2')
                    distance=math.dist(mm(cp.GetPosition()),mm(tp.GetPosition()))
                    rd=min(math.dist(mm(cg.GetPosition()),mm(p.GetPosition())) for p in fps[target].Pads() if p.GetNumber() in grounds)
                    # The retained SOT23 reset buffer already has a ground
                    # stitch into the adjacent, continuous logic reference.
                    # Its bypass uses the same reference through its own
                    # nearby stitch, rather than a long top-side trace around
                    # the package. 3.5 mm is an engineering placement screen,
                    # not a manufacturer maximum between capacitor and both
                    # IC pads. The other five new bypasses fit that screen.
                    if distance>3.5 or (ref!='C18001' and rd>3.5):continue
                options.append((math.dist((x,y),want),x,y,angle,bb,distance,rd))
        if not options:raise ValueError('No copper-clear exact local placement '+ref)
        _,x,y,angle,bb,distance,rd=min(options);fp.SetOrientationDegrees(angle);fp.SetPosition(xy((x,y)));occupied.append(bb)
        if ref.startswith('U220'):reserved[ref]=(bb[0]-3.,bb[1]-3.,bb[2]+3.,bb[3]+3.)
        fps[ref]=fp;added[ref]=fp;templates[ref]=collections.Counter(pad_template(p) for p in fp.Pads())
        placements.append(dict(reference=ref,position_mm=[x,y],rotation_degrees=angle,local_owner=owner,
            own_supply_pad_distance_mm=distance,own_return_pad_distance_mm=rd,actual_bypass_routed=False))
    for ref,target in [('U22001','U10003'),('U22002','U13004'),('U22003','U13008')]:add(ref,mm(fps[target].GetPosition()),near_limit=60.)
    caps={'C22001':('U22001','5',['2']), 'C22002':('U22002','3',['1','8']),
        'C22003':('U22002','14',['9','16']),'C22004':('U22003','3',['1','8']),
        'C22005':('U22003','14',['9','16']),'C18001':('U2006','5',['3'])}
    for ref,owner in caps.items():add(ref,(0,0),owner=owner)
    for ref,target in [('R22001','U22001'),('R22002','U22003'),('R13057','U13001'),('R13058','U13004'),('R13059','U13008'),('R14533','U14501')]:
        add(ref,mm(fps[target].GetPosition()),near_limit=30. if ref in ('R13057','R13058','R13059','R14533') else 12.)
    for i,ball in enumerate(('A3','C6','A4','E5'),1):
        tp=next(p for p in fps['U1001'].Pads() if p.GetNumber()==ball);add(f'TP2200{i}',mm(tp.GetPosition()),near_limit=20.)
    for i,pos in enumerate(((6,13),(454,6),(454,320),(17,323),(230,17),(234,334)),1):add(f'H2200{i}',pos,fixed=pos)
    reset_cap={p.GetNumber():p for p in fps['C18001'].Pads()}
    reset_ic={p.GetNumber():p for p in fps['U2006'].Pads()}
    # Complete the actual local capacitor loop now. The existing receiving
    # buffer ground stitch is independent of the regulator damping node.
    ground_stitches=[t for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA)
        and str(t.GetNetname())=='/LOGIC_GND'
        and math.dist(mm(t.GetPosition()),mm(reset_ic['3'].GetPosition()))<1.1]
    if len(ground_stitches)!=1:raise ValueError('Exact existing U2006 own-ground stitch required')
    local_routes=[]
    def local_track(net,start,end):
        t=pcbnew.PCB_TRACK(b);t.SetLayer(pcbnew.F_Cu);t.SetNet(nets[net]);t.SetStart(xy(start));t.SetEnd(xy(end));t.SetWidth(pcbnew.FromMM(.3));b.Add(t)
        local_routes.append(t.m_Uuid.AsString())
    local_track('/IO_3V3',mm(reset_cap['1'].GetPosition()),mm(reset_ic['5'].GetPosition()))
    cp=mm(reset_cap['2'].GetPosition());vp=(cp[0],cp[1]-.8)
    local_track('/LOGIC_GND',cp,vp)
    via=pcbnew.PCB_VIA(b);via.SetNet(nets['/LOGIC_GND']);via.SetPosition(xy(vp));via.SetWidth(pcbnew.FromMM(.5));via.SetDrill(pcbnew.FromMM(.2));via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetRemoveUnconnected(True);b.Add(via)
    local_routes.append(via.m_Uuid.AsString())
    for row in placements:
        if row['reference']=='C18001':row.update(actual_bypass_routed=True,
            return_strategy='Own close through-via to adjacent LOGIC_GND reference; existing U2006.3 ground stitch retained',
            capacitor_return_stitch_mm=vp,IC_return_stitch_mm=mm(ground_stitches[0].GetPosition()),
            placement_screen_is_manufacturer_maximum=False)
    out.mkdir(parents=True);dest=out/'motherboard-current-source-candidate.kicad_pcb'
    for f in base.parent.iterdir():
        if f.is_dir():shutil.copytree(f,out/f.name)
        elif f.suffix in ('.kicad_pro','.kicad_dru') or f.name in ('fp-lib-table','placement-ledger.json','bypass-owner-inputs.json'):
            shutil.copyfile(f,out/f.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    for folder in source.glob('*.pretty'):
        target=out/folder.name;target.mkdir(exist_ok=True)
        for file in folder.iterdir():
            if not (target/file.name).exists():shutil.copyfile(file,target/file.name)
    table=parse((out/'fp-lib-table').read_text());names={value(child(l,'name')[1]) for l in children(table,'lib')}
    for lib in children(parse((source/'fp-lib-table').read_text()),'lib'):
        if value(child(lib,'name')[1]) not in names:table.append(lib)
    (out/'fp-lib-table').write_text(dump(table)+'\n')
    snap=out/'source-inputs'
    if snap.exists():
        prior=out/'source-inputs-before-r23'
        if not snap.resolve().is_relative_to(out) or not prior.resolve().is_relative_to(out) or prior.exists():
            raise ValueError('Prior copied snapshot archive target is not a fresh owned child')
        shutil.move(str(snap),str(prior))
    snap.mkdir()
    for name in ('design.json','netlist.xml','assembly-map.json'):shutil.copyfile(source/name,snap/('motherboard-'+name))
    b.BuildConnectivity();pcbnew.SaveBoard(str(dest),b)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','--output',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native DRC did not execute')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();observed={f.GetReference():f for f in fresh.GetFootprints()}
    assert set(observed)==set(parts)
    current_tracks={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    assert all(current_tracks.get(k)==v for k,v in oldtracks.items())
    assert set(current_tracks)-set(oldtracks)==set(local_routes)
    for ref,f in observed.items():
        assert collections.Counter(pad_template(p) for p in f.Pads())==templates[ref],ref
        if ref not in added:assert (f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees())==poses[ref]
        for pad in f.Pads():
            if copper_pad(pad):assert str(pad.GetNetname())==nodes[ref,pad.GetNumber()]
            if ref not in added:
                old=oldpieces[ref,pad.m_Uuid.AsString()];new=piece(pad)
                assert new[:2]+new[3:]==old[:2]+old[3:]
                if (ref,pad.GetNumber()) not in changes:assert new==old
    d=load(out/'drc.json');receipt=dict(inputs={str(base):sha(base),str(a.review):sha(a.review),str(source/'netlist.xml'):sha(source/'netlist.xml'),str(source/'design.json'):sha(source/'design.json')},
        board_sha256=sha(dest),physical_parts=len(observed),added_parts=len(added),exact_changed_pins=list(changes.values()),
        placement_ledger=placements,land_pattern_sha256=lands,all_existing_copper_geometry_UUIDs_preserved=True,
        new_reset_bypass_copper_UUIDs=local_routes,
        exact_pad_piece_land_and_existing_pose_preservation_pass=True,native_DRC_regular=len(d['violations']),
        native_DRC_ignored=d.get('ignored_checks',[]),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    write(out/'receipt.json',receipt);print({k:receipt[k] for k in ('physical_parts','added_parts','native_DRC_regular','uncapped_missing_joins')})

if __name__=='__main__':main()
