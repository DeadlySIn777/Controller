"""Move only newly populated parts clear of retained copper; native DRC verifies.

No net, pad, old footprint or retained copper is replaced. Plane definitions
remain identical and their generated fills are recalculated. Own-footprint
manufacturer constraints remain reported for a separate reviewed rule fix.
"""
import argparse,collections,json,math,re,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import (sha,load,write,courtyard_relative,Occupancy,pad_template)
from hardware_route_logic_return import identity,xy,mm,segment_hits_box
from hardware_reconcile_motherboard_peripheral_pcb import piece
from hardware_route_local_signals import GeometryIndex

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for v in ('board','retained','drc','out'):p.add_argument('--'+v,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if out.exists():raise ValueError('Fresh output required')
    b=pcbnew.LoadBoard(str(a.board));base=pcbnew.LoadBoard(str(a.retained))
    fps={f.GetReference():f for f in b.GetFootprints()};oldrefs={f.GetReference() for f in base.GetFootprints()}
    added=set(fps)-oldrefs
    tracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    allpads={(r,p.m_Uuid.AsString()):piece(p) for r,f in fps.items() for p in f.Pads()}
    geometry={r:collections.Counter(pad_template(p) for p in f.Pads()) for r,f in fps.items()}
    poses={r:(tuple(f.GetPosition()),f.GetOrientationDegrees()) for r,f in fps.items()}
    issues=load(a.drc)['violations'];move=set();mark=set();allowed_uuid=set()
    for issue in issues:
        refs={m.group(1) for v in issue['items'] if (m:=re.search(r'of ([A-Z]+[0-9]+)',v['description']))}
        if issue['type'] in ('shorting_items','solder_mask_bridge','clearance'):
            targets=refs&added
            if not targets:raise ValueError('Unreviewed existing geometry violation '+str(issue))
            move.update(targets)
        elif issue['type'] in ('text_height','text_thickness'):
            if not refs<=added:raise ValueError('Unreviewed existing marking')
            mark.update(refs);allowed_uuid.update(v['uuid'] for v in issue['items'])
    occupied=Occupancy(courtyard_relative(f) for r,f in fps.items() if r not in move)
    # Full purchased-mate envelopes, independently recorded at placement.
    ledger=load(a.board.parent/'placement-ledger.json')
    for row in ledger:
        if 'mating_wire_tool_reservation_mm' in row:occupied.append(tuple(row['mating_wire_tool_reservation_mm']))
    occupied.append((331.,278.,371.,333.));occupied.append((421.87,260.7,447.27,338.57))
    obstacles=GeometryIndex()
    for t in b.GetTracks():
        if not t.IsOnLayer(pcbnew.F_Cu):continue
        start,end=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth())
        box=(min(start[0],end[0])-w/2,min(start[1],end[1])-w/2,max(start[0],end[0])+w/2,max(start[1],end[1])+w/2)
        obstacles.add((str(t.GetNetname()),box),box)
    def clear(f):
        for pad in f.Pads():
            if not pad.IsOnLayer(pcbnew.F_Cu):continue
            bb=pad.GetBoundingBox();box=(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
            for net,tbox in obstacles.candidates((box[0],box[1]),(box[2],box[3]),.2):
                if net!=str(pad.GetNetname()) and segment_hits_box((tbox[0],tbox[1]),(tbox[2],tbox[3]),box,.2):return False
        return True
    edits=[]
    for ref in sorted(move):
        f=fps[ref];before=mm(f.GetPosition());f.SetPosition(xy((0,0)));box=courtyard_relative(f)
        # Keep each correction local. A later loop review determines any
        # stricter IC bypass or Kelvin proximity; no topology is fabricated.
        choices=[]
        for dx in range(-40,41):
            for dy in range(-40,41):choices.append((dx*dx+dy*dy,before[0]+dx/2,before[1]+dy/2))
        for _,x,y in sorted(choices):
            bounds=(x+box[0],y+box[1],x+box[2],y+box[3])
            if bounds[0]<1 or bounds[1]<1 or bounds[2]>459 or bounds[3]>339 or occupied.collision(bounds,.35):continue
            f.SetPosition(xy((x,y)))
            if clear(f):occupied.append(bounds);break
        else:raise ValueError('No actual local copper-clear correction '+ref)
        edits.append(dict(reference=ref,before_mm=before,after_mm=mm(f.GetPosition()),reason='New pad collided with retained native copper'))
    for ref in mark:
        for item in fps[ref].GraphicalItems():
            if isinstance(item,pcbnew.PCB_TEXT) and item.m_Uuid.AsString() in allowed_uuid:
                item.SetLayer(pcbnew.F_Fab);item.SetTextSize(xy((.8,.8)));item.SetTextThickness(pcbnew.FromMM(.1))
    # Keep the prominent engineering warning in the drawing layer, where it
    # cannot obscure a connector's physical pin-one assembly marking.
    for item in b.Drawings():
        if isinstance(item,pcbnew.PCB_TEXT) and 'NOT FOR MANUFACTURE' in item.GetText():item.SetLayer(pcbnew.Dwgs_User)
    out.mkdir(parents=True)
    for f in a.board.parent.iterdir():
        if f.is_dir():shutil.copytree(f,out/f.name)
        elif f.suffix in ('.kicad_pro','.kicad_dru') or f.name in ('fp-lib-table','placement-ledger.json','bypass-owner-inputs.json'):
            shutil.copyfile(f,out/f.name)
    dest=out/a.board.name;pcbnew.SaveBoard(str(dest),b)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','--output',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native DRC failed to execute')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();observed={f.GetReference():f for f in fresh.GetFootprints()}
    assert set(observed)==set(fps)
    assert {t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}==tracks
    for r,f in observed.items():
        assert collections.Counter(pad_template(p) for p in f.Pads())==geometry[r],r
        if r not in move:
            assert (tuple(f.GetPosition()),f.GetOrientationDegrees())==poses[r],r
            assert all(piece(p)==allpads[r,p.m_Uuid.AsString()] for p in f.Pads()),r
        else:
            assert all(str(p.GetNetname())==allpads[r,p.m_Uuid.AsString()][2] for p in f.Pads()),r
    d=load(out/'drc.json')
    receipt=dict(inputs={str(a.board):sha(a.board),str(a.retained):sha(a.retained),str(a.drc):sha(a.drc)},
        board_sha256=sha(dest),physical_parts=len(observed),exact_new_part_moves=edits,
        exact_new_marking_refs=sorted(mark),retained_copper_unchanged=True,all_native_pad_lands_and_nets_unchanged=True,
        native_DRC_regular=len(d['violations']),native_DRC_ignored=d.get('ignored_checks',[]),
        uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    write(out/'receipt.json',receipt);print(json.dumps({k:receipt[k] for k in ('physical_parts','native_DRC_regular','uncapped_missing_joins')}))

if __name__=='__main__':main()
