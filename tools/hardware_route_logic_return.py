"""Add a real logic-return fill and conservative through-via escapes on a copy.

The retained core occupies a known low-voltage logic region. This tool never
joins isolated field returns to LOGIC_GND, moves parts, changes retained copper
or calls the provisional six-layer arrangement a final manufacturing stackup.
Native DRC rejects or removes new escape groups; retained items cannot be
removed by that repair. BGA escape/rail routing remain separate work.
Run with KiCad's pcbnew Python.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def xy(p):return pcbnew.VECTOR2I(pcbnew.FromMM(p[0]),pcbnew.FromMM(p[1]))
def mm(p):return (pcbnew.ToMM(p.x),pcbnew.ToMM(p.y))
def identity(t):
    return (t.m_Uuid.AsString(),t.GetNetname(),tuple(t.GetStart()),tuple(t.GetEnd()),t.GetLayer(),
            t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth(),
            t.GetDrillValue() if isinstance(t,pcbnew.PCB_VIA) else None)
def pad_identity(p):
    return (p.GetNetname(),tuple(p.GetPosition()),tuple(p.GetSize()),p.GetOrientationDegrees(),
            p.GetLayerSet().FmtBin(),p.GetShape(),p.GetAttribute())
def distance(p,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1];d=vx*vx+vy*vy
    t=max(0,min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vy)/d)) if d else 0
    return math.hypot(p[0]-a[0]-t*vx,p[1]-a[1]-t*vy)
def segment_hits_box(a,b,box,inflate):
    xmin,ymin,xmax,ymax=box;xmin-=inflate;ymin-=inflate;xmax+=inflate;ymax+=inflate
    lo,hi=0.,1.
    for start,delta,minimum,maximum in ((a[0],b[0]-a[0],xmin,xmax),(a[1],b[1]-a[1],ymin,ymax)):
        if abs(delta)<1e-12:
            if start<minimum or start>maximum:return False
        else:
            t0,t1=(minimum-start)/delta,(maximum-start)/delta
            lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
            if lo>hi:return False
    return True
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def segment_distance(a,b,c,d):
    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:return 0.
    return min(distance(a,c,d),distance(b,c,d),distance(c,a,b),distance(d,a,b))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=a.board.resolve();out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('Use a new immutable report directory')
    before={str(source):sha(source),str(source.with_suffix('.kicad_pro')):sha(source.with_suffix('.kicad_pro'))}
    board=pcbnew.LoadBoard(str(source));board.BuildConnectivity()
    if board.GetCopperLayerCount()!=6 or len(board.Zones()):raise ValueError('Expected retained six-layer candidate without planes')
    original={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    old_pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):pad_identity(p) for p in board.GetPads()}
    net=board.FindNet('/LOGIC_GND')
    if net is None:raise ValueError('Source-backed logic return absent')
    ground=[p for p in board.GetPads() if p.GetNetname()=='/LOGIC_GND']
    obstacles=[]
    for pad in board.GetPads():
        if pad.GetNetname()=='/LOGIC_GND':continue
        bb=pad.GetBoundingBox();obstacles.append((pad,(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))))
    group_items={};skipped=[];groups=[]
    retained_vias=[mm(t.GetPosition()) for t in board.GetTracks() if isinstance(t,pcbnew.PCB_VIA)]
    for pad in ground:
        key=pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber();start=mm(pad.GetPosition())
        if pad.GetParentFootprint().GetReference()=='U1001':skipped.append({'pad':key,'reason':'BGA dogbone geometry/process must be reviewed separately'});continue
        if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
        chosen=None
        for radius in (.8,1.,1.2,1.5,1.8):
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(.70710678,.70710678),(-.70710678,.70710678),(.70710678,-.70710678),(-.70710678,-.70710678)):
                end=(round(start[0]+radius*dx,6),round(start[1]+radius*dy,6))
                if not(.8<end[0]<219.2 and .8<end[1]<99.2):continue
                if any(math.dist(end,v)<.851 for v in retained_vias):continue
                if any(segment_hits_box(start,end,box,.251) and other.IsOnLayer(pcbnew.F_Cu) or
                       segment_hits_box(end,end,box,.451) for other,box in obstacles):continue
                blocked=False
                for track in board.GetTracks():
                    if track.GetNetname()=='/LOGIC_GND':continue
                    ta,tb=mm(track.GetStart()),mm(track.GetEnd());tw=pcbnew.ToMM(track.GetWidth(pcbnew.F_Cu) if isinstance(track,pcbnew.PCB_VIA) else track.GetWidth())
                    if distance(end,ta,tb)<.451+tw/2 or (track.IsOnLayer(pcbnew.F_Cu) and segment_distance(start,end,ta,tb)<.251+tw/2):blocked=True;break
                if not blocked:chosen=end;break
            if chosen is not None:break
        if chosen is None:skipped.append({'pad':key,'reason':'No conservative clear through-via escape in retained geometry'});continue
        t=pcbnew.PCB_TRACK(board);t.SetNet(net);t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(start));t.SetEnd(xy(chosen));t.SetWidth(pcbnew.FromMM(.2));board.Add(t)
        v=pcbnew.PCB_VIA(board);v.SetNet(net);v.SetPosition(xy(chosen));v.SetWidth(pcbnew.FromMM(.6));v.SetDrill(pcbnew.FromMM(.3));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);board.Add(v)
        ids=[t.m_Uuid.AsString(),v.m_Uuid.AsString()];index=len(groups)
        groups.append({'pad':key,'start_mm':start,'via_mm':chosen,'ids':ids,'retained':True})
        for i in ids:group_items[i]=index
        retained_vias.append(chosen)
    zone=pcbnew.ZONE(board);zone.SetNet(net);zone.SetLayer(pcbnew.B_Cu);zone.SetLocalClearance(pcbnew.FromMM(.15));zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline=zone.Outline();outline.NewOutline()
    for point in ((.5,.5),(219.5,.5),(219.5,99.5),(.5,99.5)):outline.Append(int(pcbnew.FromMM(point[0])),int(pcbnew.FromMM(point[1])))
    board.Add(zone);out.mkdir(parents=True);dest=out/'logic-return-route-candidate.kicad_pcb'
    dest.with_suffix('.kicad_pro').write_bytes(source.with_suffix('.kicad_pro').read_bytes())
    for path in source.parent.glob('*.pretty'):shutil.copytree(path,out/path.name)
    for name in ('3dmodels','fp-lib-table'):
        path=source.parent/name
        if path.is_dir():shutil.copytree(path,out/name)
        elif path.is_file():shutil.copyfile(path,out/name)
    repairs=[]
    for attempt in range(8):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones());pcbnew.SaveBoard(str(dest),board)
        report=out/f'drc-{attempt:02}.json'
        command=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(report),str(dest)]
        run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/f'drc-{attempt:02}.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Native DRC failed to run')
        data=json.loads(report.read_text(encoding='utf-8'));violations=data['violations']
        if not violations:break
        removable={group_items[item.get('uuid','')] for row in violations for item in row.get('items',[]) if item.get('uuid','') in group_items and groups[group_items[item.get('uuid','')]]['retained']}
        if not removable:raise ValueError('Native issue cannot be repaired by removing only new escapes; candidate preserved')
        remove_ids={i for g in removable for i in groups[g]['ids']}
        for item in list(board.GetTracks()):
            if item.m_Uuid.AsString() in remove_ids:board.Remove(item)
        for g in removable:groups[g]['retained']=False
        repairs.append({'attempt':attempt,'violations':dict(Counter(v['type'] for v in violations)),'removed_new_escape_groups':sorted(removable)})
    else:raise ValueError('Native geometry repair limit reached; candidate preserved')
    board=pcbnew.LoadBoard(str(dest));board.BuildConnectivity()
    if old_pads!={(p.GetParentFootprint().GetReference(),p.GetNumber()):pad_identity(p) for p in board.GetPads()}:raise ValueError('Retained pad changed')
    now={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    if any(now.get(k)!=v for k,v in original.items()):raise ValueError('Retained copper changed')
    if any(sha(Path(p))!=h for p,h in before.items()):raise ValueError('Input changed')
    receipt={'source_sha256':before,'board_sha256':sha(dest),'retained_copper_items':len(original),
        'total_track_via_items':len(board.GetTracks()),'new_ground_escape_groups':sum(g['retained'] for g in groups),
        'new_logic_return_zones':len(board.Zones()),'zone_layer':'B.Cu','zone_domain':'LOGIC_GND',
        'native_geometry_violations':0,'native_drc_ignored_checks':data.get('ignored_checks'),
        'capped_unconnected_items':len(data['unconnected_items']),
        'uncapped_unconnected_ratsnest_edges':board.GetConnectivity().GetUnconnectedCount(False),
        'retained_pad_geometry_net_and_copper_identity_unchanged':True,'escape_groups':groups,'skipped':skipped,'repairs':repairs,
        'fabrication_stackup_qualified':False,'manufacturing_ready':False,'physical_qualification':False,
        'scope':'Existing logic-region return candidate only; BGA, remaining rails, field isolation/high-current power and whole-controller routing are unfinished'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('escape_groups','skipped','repairs')}))


if __name__=='__main__':main()
