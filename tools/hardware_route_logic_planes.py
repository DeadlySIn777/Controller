"""Route actual retained logic rail/return pads to native filled internal planes.

This is a source-backed routing increment, not a complete-board or thermal
qualification claim. Original pad geometry, native nets and copper remain.
Reference fills stay inside the retained low-voltage region; they must not be
extended across a later field-isolation boundary. Native DRC rejects only new
escape groups, with no check suppression. Run with KiCad pcbnew Python.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import pcbnew
from hardware_route_logic_return import identity, pad_identity, distance, segment_distance, segment_hits_box, xy, mm

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=a.board.resolve();out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('Use a new immutable report directory')
    sources=[source,source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_dru')]
    hashes={str(p):sha(p) for p in sources}
    b=pcbnew.LoadBoard(str(source));b.BuildConnectivity()
    if b.GetCopperLayerCount()!=6 or len(b.Zones())!=1:raise ValueError('Expected six-layer candidate with the retained B.Cu return fill')
    old={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    old_pads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in b.GetPads()}
    groups=[];mapping={};skipped=[]

    def add_group(items,record):
        ids=[t.m_Uuid.AsString() for t in items];idx=len(groups)
        groups.append({**record,'ids':ids,'retained':True});mapping.update({i:idx for i in ids})

    def clear_path(start,end,net,via_diameter=None,source_fp=None):
        for q in b.GetPads():
            if q.GetNetname()==net:continue
            fp=q.GetParentFootprint().GetReference()
            if fp=='U1001':
                center=mm(q.GetPosition())
                if q.IsOnLayer(pcbnew.F_Cu) and distance(center,start,end)<.175+.1+.15-1e-6:return False
                if via_diameter is not None and math.dist(center,end)<.175+via_diameter/2+(.125 if source_fp=='U1001' else .15)-1e-6:return False
            else:
                box=q.GetBoundingBox();bounds=(pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom()))
                if q.IsOnLayer(pcbnew.F_Cu) and segment_hits_box(start,end,bounds,.251):return False
                if via_diameter is not None and segment_hits_box(end,end,bounds,via_diameter/2+.151):return False
        for t in b.GetTracks():
            if t.GetNetname()==net:continue
            width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth());ta,tb=mm(t.GetStart()),mm(t.GetEnd())
            if t.IsOnLayer(pcbnew.F_Cu) and segment_distance(start,end,ta,tb)<.251+width/2:return False
            if via_diameter is not None and distance(end,ta,tb)<via_diameter/2+.151+width/2:return False
        if via_diameter is not None:
            # Same-net copper may overlap, but drilled holes must not collide.
            for t in b.GetTracks():
                if isinstance(t,pcbnew.PCB_VIA) and math.dist(end,mm(t.GetPosition()))<via_diameter/2+pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2+.15:return False
        return True

    # Join adjacent equal-rail balls before escapes. This avoids needlessly
    # consuming an interstitial drilled hole for every adjacent power ball.
    fp=next(f for f in b.GetFootprints() if f.GetReference()=='U1001')
    for net in ('/IO_3V3','/CORE_1V2'):
        pads=[q for q in fp.Pads() if q.GetNetname()==net]
        for i,q in enumerate(pads):
            for other in pads[i+1:]:
                start,end=mm(q.GetPosition()),mm(other.GetPosition())
                if not .79<math.dist(start,end)<.81 or not clear_path(start,end,net):continue
                t=pcbnew.PCB_TRACK(b);t.SetNet(q.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(start));t.SetEnd(xy(end));t.SetWidth(pcbnew.FromMM(.2));b.Add(t)
                add_group([t],{'kind':'adjacent_equal_rail_balls','pads':['U1001.'+q.GetNumber(),'U1001.'+other.GetNumber()],'net':net})

    planes=[('/LOGIC_GND',pcbnew.In1_Cu),('/IO_3V3',pcbnew.In2_Cu),('/CORE_1V2',pcbnew.In3_Cu),('/LOGIC_GND',pcbnew.In4_Cu)]
    for name,layer in planes:
        z=pcbnew.ZONE(b);z.SetNet(b.FindNet(name));z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        outline=z.Outline();outline.NewOutline()
        for point in ((.5,.5),(219.5,.5),(219.5,99.5),(.5,99.5)):outline.Append(int(pcbnew.FromMM(point[0])),int(pcbnew.FromMM(point[1])))
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
    # Prioritise BGA rail escapes, then other rail pads, then remaining GND pads.
    targets=[q for q in fp.Pads() if q.GetNetname() in ('/IO_3V3','/CORE_1V2')]
    targets += [q for q in b.GetPads() if q.GetParentFootprint().GetReference()!='U1001' and q.GetNetname() in ('/IO_3V3','/CORE_1V2')]
    targets += [q for q in b.GetPads() if q.GetNetname()=='/LOGIC_GND']
    for q in targets:
        b.BuildConnectivity();items=list(b.GetConnectivity().GetConnectedItems(q))
        if any(isinstance(t,pcbnew.PCB_VIA) or t.Type()==pcbnew.PCB_ZONE_T for t in items):continue
        if q.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or not q.IsOnLayer(pcbnew.F_Cu):continue
        start=mm(q.GetPosition());net=q.GetNetname();ref=q.GetParentFootprint().GetReference();diameter=.5
        if ref=='U1001':candidates=[(start[0]+x,start[1]+y) for x,y in ((-.4,-.4),(.4,-.4),(.4,.4),(-.4,.4))]
        else:candidates=[(start[0]+radius*x,start[1]+radius*y) for radius in (.7,.9,1.2,1.5,1.8,2.2,2.8,3.5) for x,y in ((1,0),(-1,0),(0,1),(0,-1),(.70710678,.70710678),(-.70710678,.70710678),(.70710678,-.70710678),(-.70710678,-.70710678))]
        chosen=next(((round(e[0],6),round(e[1],6)) for e in candidates if .8<e[0]<219.2 and .8<e[1]<99.2 and clear_path(start,e,net,diameter,ref)),None)
        key=ref+'.'+q.GetNumber()
        if chosen is None:skipped.append({'pad':key,'net':net,'reason':'No clear direct conventional via escape; require further route'});continue
        t=pcbnew.PCB_TRACK(b);t.SetNet(q.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(start));t.SetEnd(xy(chosen));t.SetWidth(pcbnew.FromMM(.2));b.Add(t)
        v=pcbnew.PCB_VIA(b);v.SetNet(q.GetNet());v.SetPosition(xy(chosen));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
        add_group([t,v],{'kind':'rail_return_escape','pad':key,'net':net,'start_mm':start,'via_mm':chosen})
    out.mkdir(parents=True);dest=out/'logic-planes-route-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):dest.with_suffix(suffix).write_bytes(source.with_suffix(suffix).read_bytes())
    for path in source.parent.glob('*.pretty'):shutil.copytree(path,out/path.name)
    for name in ('3dmodels','fp-lib-table'):
        path=source.parent/name
        if path.is_dir():shutil.copytree(path,out/name)
        elif path.is_file():shutil.copyfile(path,out/name)
    rejected=[]
    for attempt in range(10):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(dest),b)
        report=out/f'drc-{attempt:02}.json'
        cmd=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(report),str(dest)]
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/f'drc-{attempt:02}.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Native DRC failed to run')
        data=json.loads(report.read_text(encoding='utf-8'))
        if data.get('ignored_checks'):raise ValueError('No ignored checks permitted')
        if not data['violations']:break
        remove=set()
        for issue in data['violations']:
            found={mapping[item.get('uuid')] for item in issue.get('items',[]) if item.get('uuid') in mapping}
            if not found:raise ValueError('Native violation in retained geometry or plane: '+json.dumps(issue))
            remove.update(found)
        for idx in remove:
            g=groups[idx]
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString() in g['ids']:b.Remove(t)
            g['retained']=False;rejected.append(idx)
    else:raise ValueError('Native DRC repair bound reached')
    r=pcbnew.LoadBoard(str(dest));r.BuildConnectivity()
    if old_pads!={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in r.GetPads()}:raise ValueError('Source pad/net geometry changed')
    tracks={t.m_Uuid.AsString():identity(t) for t in r.GetTracks()}
    if any(tracks.get(i)!=value for i,value in old.items()):raise ValueError('Retained copper changed')
    if any(sha(Path(p))!=h for p,h in hashes.items()):raise ValueError('Source changed during routing')
    receipt={'source_hashes':hashes,'board_sha256':sha(dest),'retained_copper_items':len(old),'total_track_via_items':len(tracks),
             'actual_filled_zones':len(r.Zones()),'added_planes':[{'net':n,'layer':b.GetLayerName(l)} for n,l in planes],
             'new_retained_route_groups':sum(g['retained'] for g in groups),'route_groups':groups,'skipped_escape_candidates':skipped,'native_rejected_groups':rejected,
             'native_regular_drc_violations':len(data['violations']),'native_drc_ignored_checks':data.get('ignored_checks',[]),
             'capped_unconnected_items':len(data['unconnected_items']),'uncapped_unconnected_edges':r.GetConnectivity().GetUnconnectedCount(False),
             'retained_pad_net_geometry_and_copper_identity_unchanged':True,'manufacturing_ready':False,
             'scope':'Five real filled planes in retained logic region; source population, complete motherboard routing, power/brownout, impedance, current/thermal and isolation qualification remain incomplete.'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_hashes','route_groups','skipped_escape_candidates')}))

if __name__=='__main__':main()
