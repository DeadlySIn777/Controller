"""Correct misplaced owned local capacitors without changing circuit/net/land.

The six converter groups and already-attached pad copper are separate
bounded routing transactions. This copy changes only explicit capacitor poses;
it never declares placement or a nominal pad distance a completed current loop.
"""
import argparse,collections,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,write,courtyard_relative,pad_template,bb
from hardware_route_logic_return import identity,mm,xy,distance,segment_hits_box
from hardware_route_local_signals import GeometryIndex

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def side_box(f):
    layers=pcbnew.LSET();layers.AddLayer(pcbnew.B_CrtYd if f.GetLayer()==pcbnew.B_Cu else pcbnew.F_CrtYd)
    q=f.GetLayerBoundingBox(layers)
    if q.GetWidth()==0 or q.GetHeight()==0:raise ValueError('Missing actual side courtyard '+f.GetReference())
    return bb(q)

class MutableOccupancy:
    """Keep every pending/failed part occupied; replace only one reviewed pose."""
    def __init__(self):self.index=GeometryIndex();self.versions={};self.hard=[]
    def update(self,ref,side,box):
        generation=self.versions.get(ref,0)+1;self.versions[ref]=generation
        self.index.add((ref,side,box,generation),box)
    def collision(self,ref,side,box,gap):
        from hardware_populate_motherboard_pcb import intersects
        if any(intersects(box,b,gap)for b,layer in self.hard if layer is None or layer==side):return True
        for other,layer,b,generation in self.index.candidates(box[:2],box[2:],gap):
            if other!=ref and layer==side and generation==self.versions[other]and intersects(box,b,gap):return True
        return False

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('board','owners','recipes','power-board','mates','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--reservations',type=Path,help='Actual concurrently reviewed whole-cell reservation receipt')
    p.add_argument('--defer-ref-regex',help='Explicit whole-cell owner transaction; not a waived required loop')
    p.add_argument('--defer-owner-mpn-prefix',help='Exact manufacturer cell awaiting its separately reviewed layout recipe')
    p.add_argument('--only-refs',help='Comma-separated exact capacitor scope for a subsequent local correction')
    p.add_argument('--include-reviewed-unscored',action='store_true',help='Explicit --only-refs may include filters/storage with no inherited numeric placement screen')
    p.add_argument('--retained-shared-leaf-receipt',type=Path,help='Exact native-cleared leaf ledger; preserve shared trunks and every other pad cluster')
    p.add_argument('--search-radius-mm',type=float,default=6.,help='Bounded local search; larger bulk bodies may need additional space')
    a=p.parse_args();out=a.out.resolve()
    if a.include_reviewed_unscored and not a.only_refs:raise ValueError('Exact reviewed unscored capacitor scope required')
    if not 0<a.search_radius_mm<=20:raise ValueError('Bounded local placement radius required')
    if out.exists():raise ValueError('Fresh owned output required')
    review=json.loads(a.owners.read_text());recipes=json.loads(a.recipes.read_text());mates=json.loads(a.mates.read_text())
    if sha(a.board)!=review['board_sha256']or not review['own_pin_match_pass']:raise ValueError('Frozen exact owner parity required')
    b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
    source_parts=json.loads((Path(__file__).resolve().parents[1]/'hardware/motherboard/design.json').read_text())['components']
    power=pcbnew.LoadBoard(str(a.power_board));powerfps={f.GetReference():f for f in power.GetFootprints()}
    excluded={r for g in recipes['groups'].values()for r in g}
    old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldposes={r:(mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())for r,f in fps.items()}
    oldlands={r:collections.Counter(pad_template(p)for p in f.Pads())for r,f in fps.items()}
    oldnets={(r,p.m_Uuid.AsString()):str(p.GetNetname())for r,f in fps.items()for p in f.Pads()}
    reviewed_shared=set()
    if a.retained_shared_leaf_receipt:
        ledger=json.loads(a.retained_shared_leaf_receipt.read_text())
        cleared=a.retained_shared_leaf_receipt.parent/'motherboard-capacitor-leaves-cleared-candidate.kicad_pcb'
        if ledger['native_DRC_regular'] or ledger['ignored_checks'] or not ledger['all_unmoved_actual_pad_cluster_identities_preserved'] or sha(cleared)!=ledger['board_sha256']:
            raise ValueError('Exact native-cleared capacitor leaf proof required')
        cb=pcbnew.LoadBoard(str(cleared));cfps={f.GetReference():f for f in cb.GetFootprints()}
        if {t.m_Uuid.AsString():identity(t)for t in cb.GetTracks()}!=old:raise ValueError('Shared-trunk copper changed since leaf proof')
        for row in ledger['still_blocked_by_unremoved_actual_copper']:
            ref=row['ref'];first,last=cfps[ref],fps[ref]
            if (mm(first.GetPosition()),first.GetOrientationDegrees(),first.GetLayer())!=oldposes[ref] or collections.Counter(pad_template(q)for q in first.Pads())!=oldlands[ref]:
                raise ValueError('Shared capacitor pose/lands changed since leaf proof '+ref)
            reviewed_shared.add(ref)
    def pads(ref,pin):return [v for v in fps[ref].Pads()if v.GetNumber()==pin]
    selected=[];deferred=[]
    for r in review['rows']:
        if r['geometric_supply_target_met']is not False and not(a.include_reviewed_unscored and r['geometric_supply_target_met']is None):continue
        if a.only_refs and r['ref']not in a.only_refs.split(','):continue
        if a.defer_owner_mpn_prefix and source_parts[r['owner']].get('mpn','').startswith(a.defer_owner_mpn_prefix):
            deferred.append(dict(ref=r['ref'],reason='Exact manufacturer cell owns its separately reviewed same-side layout'));continue
        if a.defer_ref_regex:
            import re
            if re.fullmatch(a.defer_ref_regex,r['ref']):deferred.append(dict(ref=r['ref'],reason='Explicit independently reviewed whole-cell owner transaction'));continue
        if r['ref']in excluded or r['owner']in excluded:
            deferred.append(dict(ref=r['ref'],reason='Exact six-converter routing recipe owns this loop'));continue
        cap_pads=list(fps[r['ref']].Pads())
        attached=[t.m_Uuid.AsString()for t in b.GetTracks()if any(str(t.GetNetname())==str(cap.GetNetname())and(t.HitTest(cap.GetPosition())or cap.HitTest(t.GetStart())or cap.HitTest(t.GetEnd()))for cap in cap_pads)]
        if attached and r['ref']not in reviewed_shared:
            deferred.append(dict(ref=r['ref'],reason='Existing pad copper requires its own bounded branch reroute',UUIDs=attached));continue
        selected.append(r)
    wanted={r['ref']for r in selected}
    protected_clusters=None
    if reviewed_shared:
        from hardware_retire_owned_capacitor_leaves import observer_clusters
        observed_nets={str(p.GetNetname())for ref in wanted for p in fps[ref].Pads()}
        protected_clusters=observer_clusters(b,wanted,observed_nets)
    occupancy=MutableOccupancy()
    for ref,f in fps.items():occupancy.update(ref,f.GetLayer(),side_box(f))
    # Real forthcoming plug/service corridors, compute/RF modules, and the
    # actual fixed converter groups remain reserved during local placement.
    for r,port in mates['actual40_ports_mutually_checked'].items():
        for key in ('header','full_plug','withdraw_wire_service'):occupancy.hard.append((tuple(port['envelopes_mm'][key]),pcbnew.F_Cu))
    occupancy.hard.extend([((331,278,371,333),pcbnew.F_Cu),((421.87,277.3,447.27,346.45),pcbnew.F_Cu)])
    if a.reservations:
        reservations=json.loads(a.reservations.read_text())
        cells=reservations.get('reserved_DI_cells',[])
        for v in cells:
            points=v['reserved_cell_polygon_mm'];occupancy.hard.append(((min(q[0]for q in points),min(q[1]for q in points),max(q[0]for q in points),max(q[1]for q in points)),None))
        for v in reservations.get('reserved_whole_cell_boxes_mm',[]):
            bounds=tuple(v['box_mm'])
            if len(bounds)!=4 or not bounds[0]<bounds[2] or not bounds[1]<bounds[3]:raise ValueError('Invalid reviewed whole-cell reservation')
            occupancy.hard.append((bounds,None))
    for ref in excluded:occupancy.hard.append((side_box(powerfps[ref]),None))
    for f in fps.values():
        if f.GetReference().startswith('H220'):x,y=mm(f.GetPosition());occupancy.hard.append(((x-4.25,y-4.25,x+4.25,y+4.25),None))
    tracks={pcbnew.F_Cu:GeometryIndex(),pcbnew.B_Cu:GeometryIndex()}
    for t in b.GetTracks():
        start,end=mm(t.GetStart()),mm(t.GetEnd());via=isinstance(t,pcbnew.PCB_VIA)
        width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if via else t.GetWidth())
        for layer in tracks:
            if t.IsOnLayer(layer):tracks[layer].add((str(t.GetNetname()),start,end,width),(min(start[0],end[0])-width/2,min(start[1],end[1])-width/2,max(start[0],end[0])+width/2,max(start[1],end[1])+width/2))
    pad_index=GeometryIndex();pad_versions={}
    def update_pad_obstacles(f):
        ref=f.GetReference();generation=pad_versions.get(ref,0)+1;pad_versions[ref]=generation
        for pad in f.Pads():
            q=pad.GetBoundingBox();box=bb(q)
            pad_index.add((ref,generation,str(pad.GetNetname()),box,pad.IsOnLayer(pcbnew.F_Cu),pad.IsOnLayer(pcbnew.B_Cu),pad.GetAttribute()in (pcbnew.PAD_ATTRIB_NPTH,pcbnew.PAD_ATTRIB_PTH)),box)
    for f in fps.values():update_pad_obstacles(f)
    def copper_clear(f):
        cy=side_box(f)
        for ref,generation,net,other,top,bottom,thru in pad_index.candidates(cy[:2],cy[2:],.25):
            if ref==f.GetReference()or generation!=pad_versions[ref]or not thru:continue
            from hardware_populate_motherboard_pcb import intersects
            if intersects(cy,other,.25):return False
        for pad in f.Pads():
            q=pad.GetBoundingBox();bb=tuple(pcbnew.ToMM(v)for v in (q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()))
            layer=f.GetLayer()
            for net,start,end,w in tracks[layer].candidates(bb[:2],bb[2:],.3):
                if net!=str(pad.GetNetname())and segment_hits_box(start,end,bb,.15+w/2):return False
            for ref,generation,net,other,top,bottom,thru in pad_index.candidates(bb[:2],bb[2:],.3):
                if ref==f.GetReference()or generation!=pad_versions[ref]:continue
                if not(thru or (top if layer==pcbnew.F_Cu else bottom)):continue
                from hardware_populate_motherboard_pcb import intersects
                if thru and intersects(side_box(f),other,.25):return False
                if (thru or net!=str(pad.GetNetname()))and intersects(bb,other,.25 if thru else .15):return False
        return True
    steps=round(a.search_radius_mm*4);offsets=sorted(((i/4,j/4)for i in range(-steps,steps+1)for j in range(-steps,steps+1)),key=lambda v:v[0]*v[0]+v[1]*v[1])
    changes=[];failed=[]
    for r in sorted(selected,key=lambda r:(r['target']if r['target']is not None else float('inf'),r['actual_supply_pad_distance_mm'],r['ref'])):
        f=fps[r['ref']];choices=[];nodes=[p for n in r['power_nodes']for p in pads(n['ref'],n['pin'])]
        require_owner_side=r.get('manufacturer_required_same_device_layer',False)or source_parts[r['owner']].get('mpn','').startswith('ISOW')
        sides=(fps[r['owner']].GetLayer(),)if require_owner_side else (pcbnew.F_Cu,)if source_parts[r['ref']].get('polarized',False)else (pcbnew.F_Cu,pcbnew.B_Cu)
        for side in sides:
          if f.GetLayer()!=side:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
          for angle in (0.,90.,180.,270.):
            f.SetOrientationDegrees(angle);f.SetPosition(xy((0,0)));relative=side_box(f)
            cp=pads(r['ref'],r['cap_power'])[0];dx,dy=mm(cp.GetPosition())
            for pin in nodes:
                sx,sy=mm(pin.GetPosition())
                for ox,oy in offsets:
                    x,y=sx-dx+ox,sy-dy+oy
                    box=(relative[0]+x,relative[1]+y,relative[2]+x,relative[3]+y)
                    if box[0]<.5 or box[1]<.5 or box[2]>459.5 or box[3]>339.5 or occupancy.collision(r['ref'],side,box,.25):continue
                    f.SetPosition(xy((x,y)))
                    if not copper_clear(f):continue
                    d=math.dist(mm(cp.GetPosition()),(sx,sy));choices.append((d+(3.2 if side==pcbnew.B_Cu else 0.),d,math.dist((x,y),oldposes[r['ref']][0]),x,y,angle,side,box));break
        if not choices:
            if f.GetLayer()!=oldposes[r['ref']][2]:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            f.SetPosition(xy(oldposes[r['ref']][0]));f.SetOrientationDegrees(oldposes[r['ref']][1])
            failed.append(dict(ref=r['ref'],owner=r['owner'],reason='No clear actual local pad-level placement in bounded neighbourhood',search_radius_mm=a.search_radius_mm));continue
        _,d,_,x,y,angle,side,box=min(choices)
        if f.GetLayer()!=side:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetPosition(xy((x,y)));f.SetOrientationDegrees(angle)
        if protected_clusters is not None and observer_clusters(b,wanted,observed_nets)!=protected_clusters:
            if f.GetLayer()!=oldposes[r['ref']][2]:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            f.SetPosition(xy(oldposes[r['ref']][0]));f.SetOrientationDegrees(oldposes[r['ref']][1])
            failed.append(dict(ref=r['ref'],owner=r['owner'],reason='Original capacitor lands bridge actual shared trunks; explicit same-net copper reroute required'));continue
        occupancy.update(r['ref'],side,box);update_pad_obstacles(f)
        f.Reference().SetLayer(pcbnew.B_Fab if side==pcbnew.B_Cu else pcbnew.F_Fab)
        changes.append(dict(ref=r['ref'],owner=r['owner'],old_pose=oldposes[r['ref']],new_pose=[[x,y],angle],old_supply_distance_mm=r['actual_supply_pad_distance_mm'],new_supply_distance_mm=d,
            side=b.GetLayerName(side),target_mm=r['target'],target_is_manufacturer_numeric_limit=False,actual_local_loop_routing_complete=False,
            assembly_reference_on_fabrication_layer=True,backside_interconnect_inductance_requires_actual_loop_review=side==pcbnew.B_Cu))
        if len(changes)%20==0:print(dict(placed=len(changes),failed=len(failed)),flush=True)
    expected_lands={r:collections.Counter(pad_template(p)for p in f.Pads())for r,f in fps.items()}
    out.mkdir(parents=True);dest=out/'motherboard-local-capacitors-candidate.kicad_pcb'
    for resource in a.board.parent.iterdir():
        if resource.is_dir()and(resource.suffix=='.pretty'or resource.name=='3dmodels'):shutil.copytree(resource,out/resource.name)
        elif resource.name=='fp-lib-table':shutil.copyfile(resource,out/resource.name)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    pcbnew.SaveBoard(str(dest),b)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();nowfps={f.GetReference():f for f in fresh.GetFootprints()}
    if old!={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}:raise ValueError('Retained copper changed')
    for ref,f in nowfps.items():
        if collections.Counter(pad_template(p)for p in f.Pads())!=expected_lands[ref]:raise ValueError('Exact native mirrored/rotated land changed '+ref)
        if any(str(p.GetNetname())!=oldnets[ref,p.m_Uuid.AsString()]for p in f.Pads()):raise ValueError('Exact pin/net changed '+ref)
        if ref not in wanted and (mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())!=oldposes[ref]:raise ValueError('Unselected part moved '+ref)
    d=json.loads((out/'drc.json').read_text());result=dict(inputs={str(v):sha(v)for v in (a.board,a.owners,a.recipes,a.power_board,a.mates)},board_sha256=sha(dest),
        exact_changed_poses=changes,failed_local_placements=failed,deferred_to_bounded_other_transactions=deferred,
        physical_lands_pin_nets_and_all_existing_copper_preserved=True,native_DRC_regular=len(d['violations']),native_DRC_ignored=d.get('ignored_checks',[]),
        uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
    if protected_clusters is not None:
        if observer_clusters(fresh,wanted,observed_nets)!=protected_clusters:raise ValueError('Unmoved actual shared-pad cluster changed on native reload')
        result['retained_shared_leaf_proof_sha256']=sha(a.retained_shared_leaf_receipt)
        result['all_unmoved_actual_pad_clusters_preserved']=True
    write(out/'receipt.json',result);print(dict(changed=len(changes),failed=len(failed),deferred=len(deferred),native_DRC_regular=len(d['violations']),unconnected=result['uncapped_missing_joins']))

if __name__=='__main__':main()
