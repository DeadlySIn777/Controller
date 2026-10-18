"""Join remaining retained logic rail pads to existing real plane-connected pads.

Only low-voltage logic rail/return branches are considered. Native DRC removes
only newly proposed routes. Existing pad/copper geometry and actual net names
are preserved. This is not routing for field-power or high-current paths.
"""
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
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('Use immutable report directory')
    hashes={str(f):sha(f) for f in (source,source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_dru'))}
    b=pcbnew.LoadBoard(str(source));b.BuildConnectivity()
    if len(b.Zones())!=5:raise ValueError('Expected actual five-plane retained logic layout')
    old={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    old_pads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in b.GetPads()}
    groups=[];mapping={};skipped=[]
    pad_obstacles=[];track_obstacles=[]
    def clear(points,net):
        for start,end in zip(points,points[1:]):
            for center,bounds in pad_obstacles:
                if center is not None:
                    if distance(center,start,end)<.175+.1+.15-1e-6:return False
                elif segment_hits_box(start,end,bounds,.251):return False
            for ta,tb,w in track_obstacles:
                if segment_distance(start,end,ta,tb)<.251+w/2:return False
        return True
    def candidate_paths(s,e):
        yield [s,e]
        yield [s,(e[0],s[1]),e]
        yield [s,(s[0],e[1]),e]
        # Real two-bend outward escapes can reach a nearby decoupler's via
        # without moving a placed package or clearing a retained signal route.
        for d in (.5,.75,1.,1.5,2.,3.,4.,6.,8.):
            for sign in (-1,1):
                x=s[0]+d*sign;y=s[1]+d*sign
                yield [s,(x,s[1]),(x,e[1]),e]
                yield [s,(s[0],y),(e[0],y),e]
        for dx,dy in ((.5,.5),(.5,-.5),(-.5,.5),(-.5,-.5)):
            k=(s[0]+dx,s[1]+dy)
            yield [s,k,(e[0],k[1]),e]
            yield [s,k,(k[0],e[1]),e]
    for net in ('/CORE_1V2','/IO_3V3','/LOGIC_GND'):
        pad_obstacles=[];track_obstacles=[]
        for q in b.GetPads():
            if q.GetNetname()==net or not q.IsOnLayer(pcbnew.F_Cu):continue
            if q.GetParentFootprint().GetReference()=='U1001':pad_obstacles.append((mm(q.GetPosition()),None))
            else:
                box=q.GetBoundingBox();pad_obstacles.append((None,(pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom()))))
        for t in b.GetTracks():
            if t.GetNetname()==net or not t.IsOnLayer(pcbnew.F_Cu):continue
            track_obstacles.append((mm(t.GetStart()),mm(t.GetEnd()),pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth())))
        pads=[q for q in b.GetPads() if q.GetNetname()==net]
        while True:
            b.BuildConnectivity();clusters={}
            for q in pads:
                key=tuple(sorted(t.m_Uuid.AsString() for t in b.GetConnectivity().GetConnectedItems(q) if t.Type()==pcbnew.PCB_PAD_T))
                clusters.setdefault(key,[]).append(q)
            if len(clusters)<=1:break
            main=max(clusters.values(),key=len);others=[q for values in clusters.values() if values is not main for q in values]
            routed=False
            for q in others:
                start=mm(q.GetPosition());key=q.GetParentFootprint().GetReference()+'.'+q.GetNumber();chosen=None;anchor=None
                targets=sorted(main,key=lambda o:math.dist(start,mm(o.GetPosition())))
                for target in targets[:8]:
                    end=mm(target.GetPosition())
                    if math.dist(start,end)>30:continue
                    chosen=next((points for points in candidate_paths(start,end) if clear(points,net)),None)
                    if chosen is not None:anchor=target;break
                if chosen is None:continue
                items=[]
                for s,e in zip(chosen,chosen[1:]):
                    if math.dist(s,e)<1e-6:continue
                    t=pcbnew.PCB_TRACK(b);t.SetNet(q.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);items.append(t)
                idx=len(groups);ids=[t.m_Uuid.AsString() for t in items]
                groups.append({'net':net,'from':key,'to':anchor.GetParentFootprint().GetReference()+'.'+anchor.GetNumber(),'path_mm':chosen,'ids':ids,'retained':True});mapping.update({i:idx for i in ids})
                routed=True;break
            if not routed:
                skipped += [{'net':net,'pad':q.GetParentFootprint().GetReference()+'.'+q.GetNumber(),'reason':'No clear local top-layer plane anchor path; remains required routing'} for q in others]
                break
        print(json.dumps({'rail_route':net,'groups_now':len(groups)}),flush=True)
    out.mkdir(parents=True);dest=out/'logic-plane-gap-routes-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):dest.with_suffix(suffix).write_bytes(source.with_suffix(suffix).read_bytes())
    for path in source.parent.glob('*.pretty'):shutil.copytree(path,out/path.name)
    for name in ('3dmodels','fp-lib-table'):
        f=source.parent/name
        if f.is_dir():shutil.copytree(f,out/name)
        elif f.is_file():shutil.copyfile(f,out/name)
    rejected=[]
    for attempt in range(10):
        pcbnew.SaveBoard(str(dest),b);report=out/f'drc-{attempt:02}.json'
        cmd=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(report),str(dest)]
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/f'drc-{attempt:02}.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Native DRC command failed')
        data=json.loads(report.read_text(encoding='utf-8'))
        if data.get('ignored_checks'):raise ValueError('No ignored checks permitted')
        if not data['violations']:break
        remove=set()
        for issue in data['violations']:
            matched={mapping[i.get('uuid')] for i in issue.get('items',[]) if i.get('uuid') in mapping}
            if not matched:raise ValueError('Native violation outside new route scope: '+json.dumps(issue))
            remove.update(matched)
        for idx in remove:
            g=groups[idx]
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString() in g['ids']:b.Remove(t)
            g['retained']=False;rejected.append(idx)
    else:raise ValueError('Repair bound reached')
    r=pcbnew.LoadBoard(str(dest));r.BuildConnectivity()
    after={t.m_Uuid.AsString():identity(t) for t in r.GetTracks()}
    if any(after.get(i)!=v for i,v in old.items()):raise ValueError('Retained copper changed')
    if old_pads!={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in r.GetPads()}:raise ValueError('Retained source-pad geometry changed')
    if any(sha(Path(f))!=h for f,h in hashes.items()):raise ValueError('Input changed during routing')
    receipt={'source_hashes':hashes,'board_sha256':sha(dest),'retained_copper_items':len(old),'total_track_via_items':len(after),
      'local_plane_gap_routes':sum(g['retained'] for g in groups),'routes':groups,'skipped':skipped,'native_rejected_groups':rejected,
      'native_regular_drc_violations':len(data['violations']),'native_drc_ignored_checks':data.get('ignored_checks',[]),
      'actual_filled_zones':len(r.Zones()),'uncapped_unconnected_edges':r.GetConnectivity().GetUnconnectedCount(False),
      'retained_pad_net_geometry_and_copper_identity_unchanged':True,'manufacturing_ready':False,
      'scope':'Local0.2mm branches for retained logic rails only. Full-board routing/fieldpower/thermal/return and manufacturing qualification remain open.'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_hashes','routes','skipped')}))

if __name__=='__main__':main()
