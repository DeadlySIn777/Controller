"""Connect adjacent own-return planes with bounded physical transfer vias.

Only a source-anchored native reference component can anchor another component
of the same return. This is a physical plane connection, not a fabricated IC
pin connection. Source-pad clusters, original Cu, poses, nets and all zone
definitions remain immutable. Current capacity and entry-return distribution
need their separate engineering proofs.
"""
from __future__ import annotations
import argparse, collections, json, math, shutil
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,children,child,value
from hardware_map_motherboard_domains import SEEDS,RAW_RETURNS,sha,write
from hardware_validate_motherboard_return_planes import validate,physical_reference_contact
from hardware_zone_motherboard_returns import split_polygons,inflation
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_check_return_corridors import circle,covered
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_merge_bounded_pcb_delta import zone_definition,without_generated_fills

ALLOWED_RETURNS=set(SEEDS.values())-{'/CHASSIS'}-set(RAW_RETURNS)


def filled_resources(b):
    fills={}
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() not in ALLOWED_RETURNS:continue
        for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
            if z.HasFilledPolysForLayer(layer):
                fills.setdefault((z.GetNetname(),layer),pcbnew.SHAPE_POLY_SET()).BooleanAdd(z.GetFilledPolysList(layer))
    for p in fills.values():p.Simplify()
    return {key:list(split_polygons(p)) for key,p in fills.items()}


def candidate_points(shape):
    q=shape.BBox();bounds=[pcbnew.ToMM(x)for x in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())]
    mid=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2)
    points=[mid]
    # Try inward vertex offsets before a bounded native-grid search.
    for vertex in shape.COutline(0).CPoints():
        pt=mm(vertex);d=math.dist(pt,mid)
        if d>0:
            for step in (.4,.65,1.):
                if d>step:points.append((pt[0]+step*(mid[0]-pt[0])/d,pt[1]+step*(mid[1]-pt[1])/d))
    seen=set()
    for p in points:
        p=tuple(round(x,6)for x in p)
        if p not in seen:seen.add(p);yield p
    lo=(math.ceil(bounds[0]*2),math.ceil(bounds[1]*2));hi=(math.floor(bounds[2]*2),math.floor(bounds[3]*2))
    count=0
    for ix in range(lo[0],hi[0]+1):
        for iy in range(lo[1],hi[1]+1):
            p=(ix/2,iy/2)
            if p not in seen:yield p;seen.add(p)
            count+=1
            if count>=20000:return


def choose_transfer(net,piece,anchored_other,geometry):
    if net not in ALLOWED_RETURNS:raise ValueError('Forbidden return-transfer domain '+net)
    for other_index,other in anchored_other:
        overlap=pcbnew.SHAPE_POLY_SET();overlap.Append(piece);overlap.BooleanIntersection(other)
        # An exact native erosion prunes narrow/empty overlaps once. Final
        # 96-vertex full-circle coverage still independently decides acceptance.
        admissible=inflation(overlap,-.26)
        for region in split_polygons(admissible):
            for pt in candidate_points(region):
                if not region.Contains(xy(pt)):continue
                # The whole .50 mm native via annulus plus .01 mm margin must
                # lie in the actual filled copper on each adjacent plane.
                disk=circle(tuple(xy(pt)),pcbnew.FromMM(.26))
                if covered(disk,piece)and covered(disk,other)and geometry.via(pt,net):
                    return pt,other_index
    return None


def definitions(path):
    tree=parse(without_generated_fills(path.read_text(encoding='utf-8')))
    return {value(child(z,'uuid')[1]):zone_definition(z)for z in children(tree,'zone')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['board','map','out']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();base=a.board.resolve()
    if out.exists():raise ValueError('Fresh immutable report required')
    dependencies=[Path(__file__)]+[Path(__file__).parent/name for name in
        ['hardware_validate_motherboard_return_planes.py','hardware_zone_motherboard_returns.py',
         'hardware_route_owned_bypass_loops.py','hardware_check_return_corridors.py']]
    frozen={str(v.resolve()):sha(v)for v in[base,a.map]+dependencies}
    out.mkdir(parents=True);inputs=out/'inputs';inputs.mkdir()
    for v in[base,a.map]+dependencies:shutil.copy2(v,inputs/v.name)
    print('Reviewing actual native source/reference contacts',flush=True)
    mapping=json.loads(a.map.read_text(encoding='utf-8'));b=pcbnew.LoadBoard(str(base));initial=validate(b,mapping)
    resources=filled_resources(b);g=Geometry(b)
    anchored={(r['net'],b.GetLayerID(r['reference_layer']),r['filled_piece'])for r in initial['filled_components']if r['passed']}
    oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={v.m_Uuid.AsString():pad_identity(v)for v in b.GetPads()}
    olddefs=definitions(base);nets={v.GetNetname()for v in b.GetPads()if v.GetNumber()};oldclusters=native_pad_clusters(b,nets)
    added=[];blocked=[];reviewed_pairs=set()
    print(dict(initial_resources=len(initial['filled_components']),initial_unanchored=len(initial['unanchored_components'])),flush=True)
    # A qualified transfer can propagate a real source anchor through another
    # actual filled component. Never count a same-name disconnected component.
    for iteration in range(len(initial['filled_components'])+1):
        progress=False
        for (net,layer),pieces in resources.items():
            opposite=pcbnew.In4_Cu if layer==pcbnew.In1_Cu else pcbnew.In1_Cu
            candidates=[(i,s)for i,s in enumerate(resources.get((net,opposite),[]))if(net,opposite,i)in anchored]
            for index,piece in enumerate(pieces):
                if(net,layer,index)in anchored:continue
                pending=[(i,s)for i,s in candidates if(net,layer,index,i)not in reviewed_pairs]
                match=choose_transfer(net,piece,pending,g)
                # Geometry only gains more vias, so a previously rejected pair
                # cannot become legal in a later propagation pass.
                reviewed_pairs.update((net,layer,index,i)for i,s in pending)
                if match is None:continue
                pt,other_index=match;v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v)
                added.append(dict(uuid=v.m_Uuid.AsString(),net=net,position_mm=list(pt),unanchored_layer=b.GetLayerName(layer),unanchored_piece=index,source_anchored_layer=b.GetLayerName(opposite),source_anchored_piece=other_index,full_annulus_both_adjacent_planes_proved=True,iteration=iteration))
                anchored.add((net,layer,index));progress=True
        print(dict(propagation_pass=iteration,new_transfer_vias=len(added)),flush=True)
        if not progress:break
    for (net,layer),pieces in resources.items():
        for i in range(len(pieces)):
            if(net,layer,i)not in anchored:blocked.append(dict(net=net,reference_layer=b.GetLayerName(layer),filled_piece=i,reason='No all-layer-clear native annulus overlap with a physically source-anchored opposite own-return component'))
    dest=out/'motherboard-own-reference-transfer-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
    for v in base.parent.iterdir():
        if v.is_dir()and(v.name.endswith('.pretty')or v.name=='3dmodels'):shutil.copytree(v,out/v.name)
        elif v.name=='fp-lib-table':shutil.copy2(v,out/v.name)
    print(dict(native_refill_and_DRC=True,new_transfer_vias=len(added),unclosed_resources=len(blocked)),flush=True)
    native=drc(dest,out,'drc');fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();current={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()};newids={r['uuid']for r in added}
    if set(current)!=set(oldcu)|newids or any(current.get(k)!=v for k,v in oldcu.items())or oldpads!={v.m_Uuid.AsString():pad_identity(v)for v in fresh.GetPads()}or definitions(dest)!=olddefs:raise ValueError('Old native copper/source pad/zone definition changed')
    currentclusters=native_pad_clusters(fresh,nets);clusterpass=clusters_survive(oldclusters,currentclusters);write(out/'all-source-pad-cluster-proof.json',dict(before=oldclusters,after=currentclusters,passed=clusterpass))
    if not clusterpass:raise ValueError('Prior actual source-pad cluster fragmented')
    exact={t.m_Uuid.AsString():t for t in fresh.GetTracks()};post_resources=filled_resources(fresh);proof=[]
    for row in added:
        v=exact[row['uuid']];net=v.GetNetname();pos=v.GetPosition();disk=circle(tuple(pos),pcbnew.FromMM(.26));peers=list(fresh.GetConnectivity().GetConnectedItems(v));source=[dict(reference=x.GetParentFootprint().GetReference(),pin=x.GetNumber(),pad_uuid=x.m_Uuid.AsString())for x in peers if isinstance(x,pcbnew.PAD)and x.GetNumber()and x.IsOnCopperLayer()and x.GetNetname()==net]
        layers={}
        for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
            layers[fresh.GetLayerName(layer)]=physical_reference_contact(v,layer,fresh.GetConnectivity())and any(covered(disk,s)for s in post_resources.get((net,layer),[]))
        if not source or not all(layers.values()):raise ValueError('New transfer lacks actual source anchor/full filled annulus after native refill '+row['uuid'])
        proof.append(dict(uuid=row['uuid'],net=net,actual_numbered_source_pad_anchors=source,full_filled_annulus_by_layer=layers))
    if any(sha(Path(v))!=digest for v,digest in frozen.items()):raise ValueError('Inputs changed during native operation')
    final=validate(fresh,mapping);final['board_sha256']=sha(dest);write(out/'physical-reference-anchors.json',final)
    write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact source-anchored same-domain In1/In4 ground-resource transfer vias with full annuli and all-layer clearances; not entry-root or current-capacity qualification.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(newids),reviewed_added_zone_UUIDs=[]))
    receipt=dict(input_sha256=frozen,board_sha256=sha(dest),new_own_return_transfer_vias=added,post_refill_actual_anchor_proofs=proof,unclosed_reference_resources=blocked,all_old_copper_source_pads_zone_definitions_and_source_clusters_preserved=True,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),native_errors=sum(r['severity']=='error'for r in native['violations']),ignored_checks=native['ignored_checks'],all_reference_resources_source_anchored=final['passed'],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),global_entry_return_capacity_or_supply_delivery_qualified=False,manufacturing_ready=False)
    write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in['new_own_return_transfer_vias','post_refill_actual_anchor_proofs','unclosed_reference_resources']},indent=2))


if __name__=='__main__':main()
