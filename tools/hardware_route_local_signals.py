"""Add short required logic-signal paths without replacing retained copper.

F.Cu paths are tried first, then conventional through-via/B.Cu paths. Power
rails and converter nodes are excluded: a signal-width route is not a power
distribution solution. Native DRC may reject only a newly proposed group.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import shutil
import subprocess

import pcbnew
from hardware_route_logic_return import identity, pad_identity, distance, segment_distance, segment_hits_box, xy, mm
from hardware_reconcile_motherboard_peripheral_pcb import piece

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

class GeometryIndex:
    """Conservative spatial candidates; exact collision predicates stay unchanged."""
    def __init__(self,cell_mm=5.):
        self.cell_mm=cell_mm;self.cells={};self.items=[]
    def cells_for(self,box):
        for x in range(math.floor(box[0]/self.cell_mm),math.floor(box[2]/self.cell_mm)+1):
            for y in range(math.floor(box[1]/self.cell_mm),math.floor(box[3]/self.cell_mm)+1):yield x,y
    def add(self,item,box):
        i=len(self.items);self.items.append(item)
        for key in self.cells_for(box):self.cells.setdefault(key,[]).append(i)
    def candidates(self,s,e,inflate):
        box=(min(s[0],e[0])-inflate,min(s[1],e[1])-inflate,max(s[0],e[0])+inflate,max(s[1],e[1])+inflate)
        ids=set()
        for key in self.cells_for(box):ids.update(self.cells.get(key,()))
        return (self.items[i] for i in sorted(ids))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def paths(s,e):
    yield [s,e]
    yield [s,(e[0],s[1]),e]
    yield [s,(s[0],e[1]),e]
    for d in (.6,1.,1.5,2.,3.,4.,6.,8.):
        for sign in (-1,1):
            x=s[0]+d*sign;y=s[1]+d*sign
            yield [s,(x,s[1]),(x,e[1]),e]
            yield [s,(s[0],y),(e[0],y),e]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-span-mm',type=float,default=18.)
    p.add_argument('--include-net-regex',help='Explicit bounded logic-net scope; does not override power exclusions')
    a=p.parse_args();source=a.board.resolve();out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('Use a new report directory')
    hashes={str(f):sha(f) for f in (source,source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_dru'))}
    b=pcbnew.LoadBoard(str(source));b.BuildConnectivity()
    old={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    old_pads={(q.GetParentFootprint().GetReference(),q.m_Uuid.AsString()):piece(q) for q in b.GetPads()}
    groups=[];mapping={};skip=[]
    # Cached geometry is updated as routes are committed. Conservative bounds
    # avoid repeated SWIG calls during every candidate-segment collision test.
    pad_geometry=GeometryIndex();tracks={pcbnew.F_Cu:GeometryIndex(),pcbnew.B_Cu:GeometryIndex()};holes=[]
    isolation_barriers=[]
    for fp in b.GetFootprints():
        name=str(fp.GetFPID().GetLibItemName()).upper()
        if not any(v in name for v in ('ISO1212','ISO772','ISO774','ISO776','TLP3640','TLP4176')):continue
        pads=list(fp.Pads())
        # Conservative centerline band across both rows of an isolation
        # package. This routing obstacle does not certify PCB creepage.
        # The reviewed packages have two facing rows. Reject unknown rotation.
        angle=fp.GetOrientationDegrees()%360
        if angle not in (0,90,180,270):raise ValueError('Review rotated isolation barrier '+fp.GetReference())
        x,y=mm(fp.GetPosition())
        coords=[mm(q.GetPosition()) for q in pads if q.IsOnCopperLayer()]
        if angle in (0,180):box=(x-.5,min(p[1] for p in coords)-.8,x+.5,max(p[1] for p in coords)+.8)
        else:box=(min(p[0] for p in coords)-.8,y-.5,max(p[0] for p in coords)+.8,y+.5)
        isolation_barriers.append((fp.GetReference(),box))
    outline=b.GetBoardEdgesBoundingBox()
    bounds=(pcbnew.ToMM(outline.GetX())+.8,pcbnew.ToMM(outline.GetY())+.8,
            pcbnew.ToMM(outline.GetRight())-.8,pcbnew.ToMM(outline.GetBottom())-.8)
    for q in b.GetPads():
        box=q.GetBoundingBox();boxmm=(pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom()))
        pad_geometry.add((q.GetNetname(),q.GetParentFootprint().GetReference(),mm(q.GetPosition()),boxmm,
                             q.IsOnLayer(pcbnew.F_Cu),q.IsOnLayer(pcbnew.B_Cu)),boxmm)
    def add_obstacle(t):
        via=isinstance(t,pcbnew.PCB_VIA)
        width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if via else t.GetWidth())
        record=(t.GetNetname(),mm(t.GetStart()),mm(t.GetEnd()),width)
        for layer in tracks:
            if t.IsOnLayer(layer):
                s,e=record[1:3]
                tracks[layer].add(record,(min(s[0],e[0])-width/2,min(s[1],e[1])-width/2,
                                          max(s[0],e[0])+width/2,max(s[1],e[1])+width/2))
        if via:holes.append((mm(t.GetPosition()),pcbnew.ToMM(t.GetDrillValue())))
    for t in b.GetTracks():add_obstacle(t)
    def clear(points,net,layer):
        pi=4 if layer==pcbnew.F_Cu else 5
        for s,e in zip(points,points[1:]):
            if any(segment_hits_box(s,e,box,.1) for ref,box in isolation_barriers):return False
            for name,ref,center,box,top,bottom in pad_geometry.candidates(s,e,.251):
                if name==net or not (top if pi==4 else bottom):continue
                if ref=='U1001':
                    if distance(center,s,e)<.175+.1+.15-1e-6:return False
                elif segment_hits_box(s,e,box,.251):return False
            for name,ta,tb,w in tracks[layer].candidates(s,e,.251):
                if name!=net and segment_distance(s,e,ta,tb)<.251+w/2-1e-6:return False
        return True
    def via_clear(point,net,ref):
        if not bounds[0]<point[0]<bounds[2] or not bounds[1]<point[1]<bounds[3]:return False
        if any(segment_hits_box(point,point,box,.25) for other,box in isolation_barriers):return False
        for name,other,center,box,top,bottom in pad_geometry.candidates(point,point,.451):
            if name==net:continue
            if other=='U1001':
                if math.dist(center,point)<.175+.25+(.125 if ref=='U1001' else .15)-1e-6:return False
            elif segment_hits_box(point,point,box,.401):return False
        for obs in tracks.values():
            for name,s,e,w in obs.candidates(point,point,.401):
                if name!=net and distance(point,s,e)<.401+w/2-1e-6:return False
        if any(math.dist(point,c)<.1+d/2+.25-1e-6 for c,d in holes):return False
        return True
    def escapes(q):
        s=mm(q.GetPosition());net=q.GetNetname();ref=q.GetParentFootprint().GetReference()
        if ref=='U1001':offsets=[(x,y) for x,y in ((-.4,-.4),(.4,-.4),(.4,.4),(-.4,.4))]
        else:offsets=[(d*x,d*y) for d in (.7,1.,1.4,2.,2.8,4.) for x,y in ((1,0),(-1,0),(0,1),(0,-1),(.7071,.7071),(-.7071,.7071),(.7071,-.7071),(-.7071,-.7071))]
        return [(s,(round(s[0]+dx,6),round(s[1]+dy,6))) for dx,dy in offsets
                if via_clear((s[0]+dx,s[1]+dy),net,ref) and clear([s,(s[0]+dx,s[1]+dy)],net,pcbnew.F_Cu)]
    by_net={}
    for q in b.GetPads():
        net=q.GetNetname()
        if not net or 'unconnected-' in net or any(token in net.upper() for token in
                ('GND','1V2','3V3','5V','12V','24V','VCC','VIN','SW_NODE','ISNS','_SW','_BST','_BOOT')):continue
        # All switching-regulator compensation/Kelvin/feedback and precision
        # acquisition wiring belongs to a reviewed current-loop placement.
        if net.startswith(('/motherboard_power_entry/','/mc_local_power/',
                           '/motherboard_analog_input/')):continue
        # Output power paths and terminal current returns cannot be assigned
        # the signal router's .2mm geometry. LED/measurement branches are
        # reviewed separately from these load-carrying parent nets.
        if re.search(r'/motherboard_do/DO\d\d(?:_SW)?$',net):continue
        if net.startswith('/motherboard_process/'):continue
        if re.search(r'/motherboard_motors/EN\d+_(?:COM|NO|NC)$',net):continue
        # Differential/high-speed host interfaces and precision analog loops
        # require their own impedance, pair geometry and return-path rules.
        # Never count arbitrary short independent P/N traces as completed.
        if net.startswith('/motherboard_compute/') and any(token in net.upper() for token in ('HDMI','USB','PCIE','ETH','SD_CLK','SD_CMD','SD_D')):continue
        if net.startswith('/motherboard_analog_output/'):continue
        if a.include_net_regex and not re.search(a.include_net_regex,net):continue
        by_net.setdefault(net,[]).append(q)
    for net,pads in sorted(by_net.items(),key=lambda item:(len(item[1]),item[0])):
        while True:
            b.BuildConnectivity();clusters={}
            for q in pads:
                ids=tuple(sorted(t.m_Uuid.AsString() for t in b.GetConnectivity().GetConnectedItems(q) if t.Type()==pcbnew.PCB_PAD_T))
                clusters.setdefault(ids,[]).append(q)
            if len(clusters)<2:break
            values=list(clusters.values());pairs=[]
            for i,first in enumerate(values):
                for other in values[i+1:]:
                    for q in first:
                        for r in other:
                            span=math.dist(mm(q.GetPosition()),mm(r.GetPosition()))
                            if span<=a.max_span_mm:pairs.append((span,q,r))
            selected=None
            for span,q,r in sorted(pairs,key=lambda pair:pair[0]):
                s,e=mm(q.GetPosition()),mm(r.GetPosition())
                chosen=next((ps for ps in paths(s,e) if clear(ps,net,pcbnew.F_Cu)),None)
                if chosen is not None:selected=(q,r,[(pcbnew.F_Cu,chosen)],[]);break
                starts=escapes(q)[:12];ends=escapes(r)[:12]
                for (_,sv),(_,ev) in sorted(((ss,ee) for ss in starts for ee in ends),key=lambda pair:math.dist(pair[0][1],pair[1][1])):
                    if math.dist(sv,ev)<.45:continue
                    chosen=next((ps for ps in paths(sv,ev) if clear(ps,net,pcbnew.B_Cu)),None)
                    if chosen is not None:selected=(q,r,[(pcbnew.F_Cu,[s,sv]),(pcbnew.B_Cu,chosen),(pcbnew.F_Cu,[ev,e])],[sv,ev]);break
                if selected:break
            if not selected:
                skip.append({'net':net,'physical_clusters':len(clusters),'reason':'No clear bounded local top/bottom route; required routing remains'})
                break
            q,r,routes,vias=selected;items=[]
            for layer,points in routes:
                for s,e in zip(points,points[1:]):
                    if math.dist(s,e)<1e-6:continue
                    t=pcbnew.PCB_TRACK(b);t.SetNet(q.GetNet());t.SetLayer(layer);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);items.append(t);add_obstacle(t)
            for point in vias:
                v=pcbnew.PCB_VIA(b);v.SetNet(q.GetNet());v.SetPosition(xy(point));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);b.Add(v);items.append(v);add_obstacle(v)
            ids=[t.m_Uuid.AsString() for t in items];idx=len(groups)
            groups.append({'net':net,'from':q.GetParentFootprint().GetReference()+'.'+q.GetNumber(),'to':r.GetParentFootprint().GetReference()+'.'+r.GetNumber(),'routes':[{'layer':b.GetLayerName(layer),'points_mm':ps} for layer,ps in routes],'via_centers_mm':vias,'ids':ids,'retained':True})
            mapping.update({i:idx for i in ids})
        if groups and len(groups)%20==0:print(json.dumps({'net':net,'new_local_route_groups':len(groups)}),flush=True)
    out.mkdir(parents=True);dest=out/'local-signal-routes-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):dest.with_suffix(suffix).write_bytes(source.with_suffix(suffix).read_bytes())
    for f in source.parent.iterdir():
        if f.name.endswith('.pretty') or f.name=='3dmodels':shutil.copytree(f,out/f.name)
        elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
    rejected=[]
    for attempt in range(10):
        pcbnew.SaveBoard(str(dest),b);report=out/f'drc-{attempt:02}.json'
        run=subprocess.run([str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(report),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/f'drc-{attempt:02}.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Native DRC failed')
        data=json.loads(report.read_text(encoding='utf-8'))
        if data.get('ignored_checks'):raise ValueError('No ignored checks allowed')
        if not data['violations']:break
        remove=set()
        for issue in data['violations']:
            matches={mapping[i.get('uuid')] for i in issue.get('items',[]) if i.get('uuid') in mapping}
            if not matches:raise ValueError('Violation outside new route scope '+json.dumps(issue))
            remove.update(matches)
        for idx in remove:
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString() in groups[idx]['ids']:b.Remove(t)
            groups[idx]['retained']=False;rejected.append(idx)
    else:raise ValueError('Native repair bound reached')
    r=pcbnew.LoadBoard(str(dest));r.BuildConnectivity()
    after={t.m_Uuid.AsString():identity(t) for t in r.GetTracks()}
    if any(after.get(i)!=v for i,v in old.items()):raise ValueError('Retained copper changed')
    if old_pads!={(q.GetParentFootprint().GetReference(),q.m_Uuid.AsString()):piece(q) for q in r.GetPads()}:raise ValueError('Retained physical pad piece changed')
    if any(sha(Path(f))!=h for f,h in hashes.items()):raise ValueError('Input changed')
    receipt={'source_hashes':hashes,'board_sha256':sha(dest),'retained_copper_items':len(old),'total_track_via_items':len(after),'local_signal_routes':sum(g['retained'] for g in groups),'routes':groups,'skipped':skip,'native_rejected_groups':rejected,'native_regular_drc_violations':len(data['violations']),'native_drc_ignored_checks':data.get('ignored_checks',[]),'actual_filled_zones':len(r.Zones()),'uncapped_unconnected_edges':r.GetConnectivity().GetUnconnectedCount(False),'retained_pad_net_geometry_and_copper_identity_unchanged':True,'manufacturing_ready':False,'scope':'Short 0.2 mm required logic-signal paths only; power rails/converter nodes excluded. Remaining full-board, analog, mechanical and manufacturing qualification remains open.'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_hashes','routes','skipped')}))

if __name__=='__main__':main()
