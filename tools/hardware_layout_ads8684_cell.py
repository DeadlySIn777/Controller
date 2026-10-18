"""Dedicated eight-part ADS8684A cell and seven F-only capacitor loops.

No generic bypass permission is used. Exact native source pin ownership,
manufacturer no-via requirements and real full-board obstacles constrain this
transaction. Every prior copper item and stationary physical pad is retained.
"""
from __future__ import annotations
import argparse,collections,heapq,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_logic_return import identity,mm,xy
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_build_ordinary_route_manifest import native
from hardware_build_assembly import parse,dump,child,value
from hardware_apply_adc_capacitor_pcb_delta import source_clusters

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
CAPS={'C14740':('5','6'),'C14741':('5','6'),'C14742':('7','6'),
      'C14743':('7','6'),'C14744':('9','8'),'C14745':('30','29'),'C14746':('34','33')}
POSES={'U14734':(0,0,0),'C14740':(-8.5,-3.5,90),'C14741':(-5.5,-3.8,90),
       'C14742':(-8.5,1.6,90),'C14743':(-5.5,-.6,-90),'C14744':(-5.5,2.7,-90),
       'C14745':(5.5,.2,-90),'C14746':(5.5,-3.55,90)}

def pose(fp):return dict(position_mm=mm(fp.GetPosition()),angle_deg=fp.GetOrientationDegrees(),layer=fp.GetLayerName())
def copper(b):return {t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
def pad_snapshot(b):return {(p.GetParentFootprint().GetReference(),p.m_Uuid.AsString()):dict(net=p.GetNetname(),number=p.GetNumber(),position_mm=mm(p.GetPosition()),template=pad_template(p))for p in b.GetPads()}

def route(g,s,e,net,bounds,width=.20):
    # Bounded, exact-F-only 0.10mm grid. Pad-centre-to-grid leads are explicitly
    # collision checked; the final path is checked again before adding copper.
    grid=.1;key=lambda p:tuple(round(v/grid)for v in p);point=lambda k:tuple(v*grid for v in k)
    sk,ek=key(s),key(e)
    if not g.clear([s,point(sk)],net,pcbnew.F_Cu,width)or not g.clear([point(ek),e],net,pcbnew.F_Cu,width):raise ValueError('Native pad escape blocked')
    def h(k):return math.dist(k,ek)
    queue=[(h(sk),0.,sk)];cost={sk:0.};parent={};visited=set();checks={};dirs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    while queue:
        _,d,k=heapq.heappop(queue)
        if k in visited:continue
        visited.add(k)
        if k==ek:
            rev=[ek]
            while rev[-1]!=sk:rev.append(parent[rev[-1]])
            ps=[s]+[point(v)for v in reversed(rev)]+[e]
            ps=[p for i,p in enumerate(ps)if not i or math.dist(p,ps[i-1])>1e-8]
            compressed=[ps[0]]
            for i in range(1,len(ps)-1):
                a,z=compressed[-1],ps[i+1];v=ps[i];cross=(v[0]-a[0])*(z[1]-v[1])-(v[1]-a[1])*(z[0]-v[0])
                if abs(cross)>1e-8:compressed.append(v)
            compressed.append(ps[-1])
            if not g.clear(compressed,net,pcbnew.F_Cu,width):
                # The conservative obstacle sampler can reject a compressed
                # long segment that was safe as its individually checked grid
                # steps. Retain those exact steps, never relax clearance.
                if not g.clear(ps,net,pcbnew.F_Cu,width):raise ValueError('Actual native local path differs')
                compressed=ps
            return compressed,len(visited)
        for dx,dy in dirs:
            n=k[0]+dx,k[1]+dy;p=point(n)
            if not bounds[0]<=p[0]<=bounds[2]or not bounds[1]<=p[1]<=bounds[3]:continue
            nd=d+math.hypot(dx,dy)
            if nd>=cost.get(n,float('inf')):continue
            pair=(min(k,n),max(k,n));clear=checks.get(pair)
            if clear is None:clear=g.clear([point(k),p],net,pcbnew.F_Cu,width);checks[pair]=clear
            if not clear:continue
            cost[n]=nd;parent[n]=k;heapq.heappush(queue,(nd+h(n),nd,n))
    raise ValueError('No bounded F-only ADC path')

def f_only_analysis(board_file,out):
    # Remove every plane, via and non-F segment BEFORE asking native KiCad
    # connectivity. Filtering its transitive answers afterward would permit
    # a path through an excluded plane/via to masquerade as an F-only loop.
    tree=parse(board_file.read_text())
    tree[:]=[v for v in tree if not(isinstance(v,list)and v and(
        v[0]in('zone','via')or(v[0]in('segment','arc')and value(child(v,'layer')[1])!='F.Cu')))]
    out.write_text(dump(tree)+'\n');b=pcbnew.LoadBoard(str(out));b.BuildConnectivity()
    if b.GetAreaCount()or any(isinstance(t,pcbnew.PCB_VIA)or t.GetLayer()!=pcbnew.F_Cu for t in b.GetTracks()):raise ValueError('Native F-only analysis retains another layer/via/plane')
    return b

def f_graph_connected(b,p,q):
    if p.GetNetname()!=q.GetNetname()or not(p.IsOnLayer(pcbnew.F_Cu)and q.IsOnLayer(pcbnew.F_Cu)):return False
    return q.m_Uuid.AsString()in{p.m_Uuid.AsString()}|{z.m_Uuid.AsString()for z in b.GetConnectivity().GetConnectedItems(p)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['board','source','adoption','out']:ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--origin',nargs=2,type=float,default=[160,263]);a=ap.parse_args();a.out=a.out.resolve()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    model=json.loads((a.source/'design.json').read_text());ad=json.loads(a.adoption.read_text());nodes,nets,func=native(model,a.source/'netlist.xml')
    for p,h in ad['source_hashes'].items():
        if sha(a.source/p)!=h:raise ValueError('Actual adopted source changed '+p)
    inputs={str(p.resolve()):sha(p)for p in [a.board,a.board.with_suffix('.kicad_pro'),a.board.with_suffix('.kicad_dru'),a.source/'design.json',a.source/'netlist.xml',a.adoption,Path(__file__)]}
    a.out.mkdir(parents=True);dest=a.out/'motherboard-adc-cell-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    for p in a.board.parent.iterdir():
        if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
        elif p.name=='fp-lib-table':shutil.copyfile(p,a.out/p.name)
    b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};old_cu=copper(b);old_pads=pad_snapshot(b);old_poses={r:pose(f)for r,f in fps.items()}
    old_clusters=source_clusters(b,set(POSES));conn=b.GetConnectivity()
    for r in POSES:
        if any(list(conn.GetConnectedTracks(p))for p in fps[r].Pads()):raise ValueError('Exact ADC cell already has attached copper '+r)
    movement=[]
    for r,(dx,dy,angle)in POSES.items():
        fp=fps[r]
        if fp.GetLayer()!=pcbnew.F_Cu:fp.Flip(fp.GetPosition(),False)
        fp.SetPosition(xy((a.origin[0]+dx,a.origin[1]+dy)));fp.SetOrientationDegrees(angle)
        movement.append(dict(reference=r,before=old_poses[r],after=pose(fp),MPN=model['components'][r]['mpn'],source_footprint=model['components'][r]['footprint']))
    b.BuildConnectivity();g=Geometry(b);bounds=(a.origin[0]-11.5,a.origin[1]-7.5,a.origin[0]+9.,a.origin[1]+8.);added=[];paths=[]
    def pin(ref,n):return next(p for p in fps[ref].Pads()if p.GetNumber()==n)
    order=['C14741','C14740','C14743','C14742','C14744','C14745','C14746']
    for side in ['1','2']:
        for ref in order:
            cp=pin(ref,side);op=pin('U14734',CAPS[ref][0 if side=='1'else 1]);net=cp.GetNetname()
            if net!=op.GetNetname()or net!=nodes[ref,side]:raise ValueError('Exact native ADC source/return changed '+ref)
            ps,visited=route(g,mm(cp.GetPosition()),mm(op.GetPosition()),net,bounds)
            ids=[]
            for s,e in zip(ps,ps[1:]):
                t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.20));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(t)
            paths.append(dict(reference=ref,cap_pin=side,owner='U14734',owner_pin=op.GetNumber(),net=net,layer='F.Cu',points_mm=ps,actual_length_mm=sum(math.dist(s,e)for s,e in zip(ps,ps[1:])),UUIDs=ids,search_visits=visited,no_vias=True))
    pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)]
    run=subprocess.run(cmd,capture_output=True,text=True);(a.out/'drc.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native ADC cell DRC did not execute')
    drc=json.loads((a.out/'drc.json').read_text());fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();actual=copper(fresh);nf={f.GetReference():f for f in fresh.GetFootprints()};np=pad_snapshot(fresh);errors=[]
    if drc.get('ignored_checks'):errors.append('Ignored native checks')
    if any(v['severity']=='error'for v in drc['violations']):errors.append('Native ADC cell geometry errors')
    if len(nf)!=2688 or len(np)!=len(old_pads):errors.append('Full native source population changed')
    if any(actual.get(u)!=v for u,v in old_cu.items()):errors.append('Existing native copper changed')
    if any(np.get(k)!=v for k,v in old_pads.items()if k[0]not in POSES):errors.append('Stationary physical pad changed')
    if {(k,v['number'],v['net'])for k,v in np.items()}!={(k,v['number'],v['net'])for k,v in old_pads.items()}:errors.append('Any actual source pad UUID/number/net changed')
    now_clusters=source_clusters(fresh,set(POSES))
    if any(not set(group)<=set(now_clusters.get(u,[]))for u,group in old_clusters.items()):errors.append('Prior stationary source-pad cluster fragmented')
    local=f_only_analysis(dest,a.out/'analysis-only-no-vias-or-planes.kicad_pcb');lf={f.GetReference():f for f in local.GetFootprints()};proofs=[]
    for ref,(power,ground)in CAPS.items():
        for cp,op in [('1',power),('2',ground)]:
            p=next(p for p in lf[ref].Pads()if p.GetNumber()==cp);q=next(p for p in lf['U14734'].Pads()if p.GetNumber()==op)
            okay=f_graph_connected(local,p,q);proofs.append(dict(cap=ref,cap_pin=cp,owner_pin=op,F_only_native_connected=okay))
            if not okay:errors.append('Missing actual F-only ADC loop '+ref+'.'+cp)
    added_ids=set(actual)-set(old_cu)
    if added_ids!={t.m_Uuid.AsString()for t in added}or any(isinstance(t,pcbnew.PCB_VIA)or t.GetLayer()!=pcbnew.F_Cu for t in fresh.GetTracks()if t.m_Uuid.AsString()in added_ids):errors.append('Actual added ADC copper contains an unreviewed layer/via')
    for p,h in inputs.items():
        if sha(p)!=h:errors.append('Frozen transaction input changed '+p)
    result=dict(passed=not errors,errors=errors,input_hashes=inputs,board_sha256=sha(dest),exact_eight_part_movement=movement,
        exact_added_copper_UUIDs=sorted(added_ids),old_copper_retained=True,all_source_pad_UUIDs_numbers_nets_retained=True,
        all_prior_stationary_source_pad_clusters_preserved=not any(not set(v)<=set(now_clusters.get(u,[]))for u,v in old_clusters.items()),
        F_only_analysis_removes_all_other_copper_layers_vias_and_planes=True,
        actual_local_paths=paths,actual_F_only_native_endpoint_proofs=proofs,native_DRC_counts=dict(collections.Counter(v['severity']for v in drc['violations'])),
        native_DRC_types=dict(collections.Counter(v['type']for v in drc['violations'])),ignored_checks=drc.get('ignored_checks',[]),
        uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),actual_all_source_parts=len(nf),
        source_or_live_PCB_mutated=False,manufacturing_ready=False,physical_qualified=False,
        reference_effective_C_and_startup_unqualified=True,ADC_inputs_SPI_and_plane_anchors_require_followup=True,
        REFIO_same_side_no_via_is_engineering_target=True,AVDD_DVDD_REFCAP_no_via_is_manufacturer_requirement=True)
    write(a.out/'receipt.json',result);print(json.dumps(dict(passed=not errors,errors=errors,moved=8,added_copper=len(added_ids),DRC=result['native_DRC_counts'],joins=result['uncapped_missing_joins'])));raise SystemExit(bool(errors))
if __name__=='__main__':main()
