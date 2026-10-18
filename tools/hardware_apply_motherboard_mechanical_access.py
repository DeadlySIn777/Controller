"""Apply frozen connector-access poses and the verified ESP antenna notch.

Every native land/net and unrelated copper item is preserved. The bounded
CHASSIS branches attached to moved sockets are re-positioned with their actual
lands. Native DRC verifies the candidate; failures remain visible.
"""
import argparse,collections,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,load,write,pad_template
from hardware_route_logic_return import identity,xy,mm
from hardware_reconcile_motherboard_peripheral_pcb import piece

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def moved_point(pt,before,after):
    x,y=pt[0]-before[0],pt[1]-before[1]
    a=math.radians(after[2]-before[2]);c,s=math.cos(a),math.sin(a)
    return (round(after[0]+x*c+y*s,6),round(after[1]-x*s+y*c,6))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('board','proposal','notch','out'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();out=a.out.resolve()
    if out.exists():raise ValueError('Fresh owned candidate required')
    proposal=load(a.proposal);notch=load(a.notch)
    if sha(a.board)!=proposal['board_sha256'] or sha(a.board)!=notch['input_sha256']:
        raise ValueError('Frozen mechanical proposal does not describe this exact copper')
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity()
    fps={f.GetReference():f for f in b.GetFootprints()}
    oldtracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
    oldpads={(r,p.m_Uuid.AsString()):piece(p) for r,f in fps.items() for p in f.Pads()}
    templates={r:collections.Counter(pad_template(p) for p in f.Pads()) for r,f in fps.items()}
    oldposes={r:(mm(f.GetPosition()),f.GetOrientationDegrees()) for r,f in fps.items()}
    rows=proposal['proposal_checks'];ownership=collections.defaultdict(set)
    for ref,row in rows.items():
        if row['component_courtyard_conflicts'] or row['retained_foreign_track_pad_conflicts']:
            raise ValueError('Unclosed mechanical pose '+ref)
        if [*oldposes[ref][0],oldposes[ref][1]]!=row['old_pose']:raise ValueError('Pose stale '+ref)
        for t in row['old_attached_endpoints']:
            if t['track_net']!='/CHASSIS' or t['pad_net']!='/CHASSIS' or not t['same_actual_native_net_pass']:
                raise ValueError('Unreviewed relocated data/power branch '+ref)
            ownership[t['uuid']].add(ref)
    # One USB-C rear shell closing segment meets only shield-track endpoints,
    # so the direct pad-contact review cannot list it. Freeze this exact local
    # branch rather than leaving old-position orphan copper behind.
    local_usb_c='099048d5-e24d-4ccd-ba9d-003508ec6661'
    c=tracks.get(local_usb_c)
    if c is None or str(c.GetNetname())!='/CHASSIS' or {mm(c.GetStart()),mm(c.GetEnd())}!={
        (317.18,258.394999),(325.82,258.394999)}:
        raise ValueError('Exact USB-C local rear shield closure changed')
    ownership[local_usb_c].add('J15006')
    relocations=[]
    # Resolve endpoints before moving any pads. A shared USB shield branch
    # follows each of its actual connector pads, rather than both endpoints
    # being translated by one arbitrarily selected socket.
    appended=[]
    for uid,refs in ownership.items():
        t=tracks[uid];positions=[]
        for endpoint in (t.GetStart(),t.GetEnd()):
            candidates=[r for r in refs if any(p.HitTest(endpoint) for p in fps[r].Pads()
                if p.IsOnCopperLayer() and str(p.GetNetname())=='/CHASSIS')]
            if len(candidates)==1:ref=candidates[0]
            elif len(refs)==1:ref=next(iter(refs))
            else:raise ValueError('Shared shield endpoint has no unique actual socket land '+uid)
            positions.append(moved_point(mm(endpoint),rows[ref]['old_pose'],rows[ref]['new_pose']))
        if isinstance(t,pcbnew.PCB_VIA):raise ValueError('No unreviewed relocated shield via')
        if len(refs)>1:
            # Both ports now face the panel edge. Escape each shell outward
            # before crossing behind the USB-C signal row. A straight bridge
            # would short the recovery/data/CC contacts.
            path=[positions[0],(251.,positions[0][1]),(251.,331.),
                (230.,331.),(230.,positions[1][1]),positions[1]]
            t.SetStart(xy(path[0]));t.SetEnd(xy(path[1]))
            for start,end in zip(path[1:],path[2:]):
                item=pcbnew.PCB_TRACK(b);item.SetLayer(t.GetLayer());item.SetWidth(t.GetWidth());item.SetNet(t.GetNet())
                item.SetStart(xy(start));item.SetEnd(xy(end));b.Add(item);appended.append(item.m_Uuid.AsString())
        else:t.SetStart(xy(positions[0]));t.SetEnd(xy(positions[1]))
        relocations.append(dict(uuid=uid,owners=sorted(refs),before=oldtracks[uid],after=identity(t),
            reason='Dedicated actual CHASSIS branch reconciled with moved connector land; no signal or supply net changed'))
    for ref,row in rows.items():
        fps[ref].SetOrientationDegrees(row['new_pose'][2]);fps[ref].SetPosition(xy(row['new_pose'][:2]))
    marking_changes=[]
    # Housing outlines may overhang a panel-edge PCB. Preserve the complete
    # manufacturer body drawing on Fab while keeping clipped outlines off the
    # silkscreen; no pin-one text or copper/land geometry is suppressed.
    drc_before=load(a.board.parent.parent/'mechanical-access-r21/drc.json')
    silk={i['uuid'] for v in drc_before['violations'] if v['type']=='silk_edge_clearance' for i in v['items']}
    for ref in rows:
        for g in fps[ref].GraphicalItems():
            if g.m_Uuid.AsString() in silk and g.GetLayer()==pcbnew.F_SilkS:
                g.SetLayer(pcbnew.F_Fab);marking_changes.append(dict(reference=ref,uuid=g.m_Uuid.AsString(),reason='Actual panel-edge housing outline retained onFab; silk must not be clipped by milling'))
    edges=[d for d in b.Drawings() if isinstance(d,pcbnew.PCB_SHAPE) and d.GetLayer()==pcbnew.Edge_Cuts and
        {mm(d.GetStart()),mm(d.GetEnd())}=={(0.,340.),(460.,340.)}]
    if len(edges)!=1:raise ValueError('Expected exact straight bottom outline')
    bottom=edges[0];oldedge=identity(bottom) if hasattr(bottom,'GetNetname') else dict(start=mm(bottom.GetStart()),end=mm(bottom.GetEnd()))
    bottom.SetStart(xy((0,340)));bottom.SetEnd(xy((424.8,340)))
    def line(start,end):
        item=pcbnew.PCB_SHAPE(b);item.SetShape(pcbnew.SHAPE_T_SEGMENT);item.SetLayer(pcbnew.Edge_Cuts)
        item.SetWidth(pcbnew.FromMM(.05));item.SetStart(xy(start));item.SetEnd(xy(end));b.Add(item)
    for row in notch['proposed_edge_profile']:
        if row['type']=='line':line(row['start'],row['end'])
        else:
            item=pcbnew.PCB_SHAPE(b);item.SetShape(pcbnew.SHAPE_T_ARC);item.SetLayer(pcbnew.Edge_Cuts)
            item.SetWidth(pcbnew.FromMM(.05));item.SetArcGeometry(xy(row['start']),xy(row['mid']),xy(row['end']));b.Add(item)
    line((444.3,340),(460,340))
    out.mkdir(parents=True);dest=out/'motherboard-mechanical-candidate.kicad_pcb'
    for f in a.board.parent.iterdir():
        if f.is_dir():shutil.copytree(f,out/f.name)
        elif f.suffix in ('.kicad_pro','.kicad_dru') or f.name in ('fp-lib-table','bypass-owner-inputs.json','placement-ledger.json'):
            shutil.copyfile(f,out/f.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    pcbnew.SaveBoard(str(dest),b)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board',
        '--format','json','--output',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native DRC failed to execute')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();observed={f.GetReference():f for f in fresh.GetFootprints()}
    assert set(observed)==set(fps)
    actualtracks={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    assert set(actualtracks)==set(oldtracks)|set(appended)
    assert all(actualtracks[u]==v for u,v in oldtracks.items() if u not in ownership)
    for ref,f in observed.items():
        assert collections.Counter(pad_template(p) for p in f.Pads())==templates[ref],ref
        for p in f.Pads():
            if ref not in rows:assert piece(p)==oldpads[ref,p.m_Uuid.AsString()],ref
            else:assert str(p.GetNetname())==oldpads[ref,p.m_Uuid.AsString()][2],ref
    d=load(out/'drc.json');receipt=dict(board_sha256=sha(dest),inputs={str(a.board):sha(a.board),str(a.proposal):sha(a.proposal),str(a.notch):sha(a.notch)},
        physical_parts=len(observed),track_via_items=len(actualtracks),exact_pose_changes=rows,
        exact_chassis_copper_changes=relocations,unrelated_copper_unchanged=True,native_pad_lands_and_nets_preserved=True,
        exact_added_shield_route_UUIDs=appended,exact_silkscreen_body_outline_layer_changes=marking_changes,
        outline_only_change='Verified bottom ESP antenna notch with0.5mm inside corner radius; overall460x340 unchanged',
        native_DRC_regular=len(d['violations']),native_DRC_ignored=d.get('ignored_checks',[]),
        uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    write(out/'receipt.json',receipt);print({k:receipt[k] for k in ('physical_parts','track_via_items','native_DRC_regular','uncapped_missing_joins')})

if __name__=='__main__':main()
