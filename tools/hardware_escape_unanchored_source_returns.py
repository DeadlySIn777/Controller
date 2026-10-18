"""Add reviewed short source-ground escapes to actual own reference pockets.

This bounded operation covers status LED/diode returns, high-value resistor
returns, isolated digital receiver ground pins and local capacitor returns.
It does not route load FET sources, switching/Kelvin loops, raw ISOW returns,
precision acquisition paths, or claim complete power distribution/ampacity.
Every accepted branch needs an actual numbered source pad, same native net,
adjacent filled annulus and flashed/native-connected contact after refill.
"""
from __future__ import annotations
import argparse,collections,json,math,shutil
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import sha,write,RAW_RETURNS
from hardware_classify_unanchored_return_pockets import classify
from hardware_validate_motherboard_return_planes import validate,physical_reference_contact
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle,covered
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_stitch_owned_return_planes import definitions,ALLOWED_RETURNS
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive

# These exact source parts were independently inventoried against the frozen
# native source. Cap returns are branch connections, not sensor/load delivery.
ALLOWED_GROUND_PARTS={'R10007','R10027','R11066','R14765','R14614','U14623',
 'R19026','C19013','U19019','C19029','C10035','R19074','C19015','C19042','C19043',
 'R11059'}|{f'D170{i}'for i in range(39,69)}
PART_MPN_PREFIXES=('CRCW0603','TNPW0603','ISO7761FDWR','ISO7760FDWR',
 'GRM188','C0805C223','APT1608SGC','BAS16,215')

def eligible(ref,source):
    c=source['components'].get(ref)
    return ref in ALLOWED_GROUND_PARTS and c and c['mpn'].startswith(PART_MPN_PREFIXES)

def choose_escape(pad,net,fill,geometry):
    start=mm(pad.GetPosition());side=pad.GetParentFootprint().GetLayer()
    if side not in(pcbnew.F_Cu,pcbnew.B_Cu):return None
    for distance in(.65,.8,1.,1.2,1.5,1.8,2.,2.5,3.):
        for angle in range(24):
            pt=tuple(round(v,6)for v in(start[0]+distance*math.cos(angle*math.pi/12),start[1]+distance*math.sin(angle*math.pi/12)))
            if geometry.via(pt,net)and geometry.clear([start,pt],net,side,.3)and covered(circle(tuple(xy(pt)),pcbnew.FromMM(.26)),fill):return pt
    return None

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in('board','map','source','out'):ap.add_argument('--'+k,type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();base=a.board.resolve()
    if out.exists():raise ValueError('Fresh immutable output required')
    inputs=[base,a.map,a.source,Path(__file__),Path(__file__).parent/'hardware_collect_native_reference_fills.py',Path(__file__).parent/'hardware_validate_motherboard_return_planes.py']
    frozen={str(p.resolve()):sha(p)for p in inputs};out.mkdir(parents=True);(out/'inputs').mkdir()
    for p in inputs:shutil.copy2(p,out/'inputs'/p.name)
    b=pcbnew.LoadBoard(str(base));mapping=json.loads(a.map.read_text());source=json.loads(a.source.read_text());classification=classify(b,mapping)
    pads={p.m_Uuid.AsString():p for p in b.GetPads()};oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={u:pad_identity(p)for u,p in pads.items()};olddefs=definitions(base)
    nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets);fills=collect_native_reference_fills(b,ALLOWED_RETURNS,[pcbnew.In1_Cu,pcbnew.In4_Cu]);g=Geometry(b);groups=[];skips=[];done=set()
    print(dict(source_bearing_pockets=classification['source_bearing_count']),flush=True)
    for row in classification['rows']:
        if not row['source_projection_needed']:continue
        net=row['net'];layer=b.GetLayerID(row['reference_layer'])
        for endpoint in row['exact_owned_pad_projections']:
            ref=endpoint['reference'];uid=endpoint['pad_uuid'];p=pads[uid]
            if uid in done or p.GetNetname()!=net or p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
            if not eligible(ref,source):skips.append(dict(reference=ref,pin=p.GetNumber(),net=net,reason='Outside exact reviewed low-current source-pin scope'));continue
            side=p.GetParentFootprint().GetLayer();adjacent=pcbnew.In1_Cu if side==pcbnew.F_Cu else pcbnew.In4_Cu
            if layer!=adjacent:continue
            pt=choose_escape(p,net,fills[net,adjacent],g)
            if pt is None:skips.append(dict(reference=ref,pin=p.GetNumber(),net=net,reason='No all-layer-clear short escape/full adjacent filled annulus'));continue
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(side);t.SetStart(p.GetPosition());t.SetEnd(xy(pt));t.SetWidth(pcbnew.FromMM(.3));b.Add(t);g.add(t)
            v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v)
            groups.append(dict(reference=ref,pin=p.GetNumber(),source_pad_uuid=uid,mpn=source['components'][ref]['mpn'],net=net,adjacent_layer=b.GetLayerName(adjacent),via_uuid=v.m_Uuid.AsString(),new_copper_UUIDs=[t.m_Uuid.AsString(),v.m_Uuid.AsString()],length_mm=math.dist(mm(p.GetPosition()),pt),retained=True));done.add(uid)
    dest=out/'motherboard-short-source-return-candidate.kicad_pcb'
    for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
    for p in base.parent.iterdir():
        if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
        elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
    print(dict(new_source_ground_branches=len(groups),native_refill=True),flush=True)
    expected={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()if t.m_Uuid.AsString()not in oldcu};rejected=[]
    for attempt in range(5):
        pcbnew.SaveBoard(str(dest),b);native=drc(dest,out,'native-'+str(attempt));b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity()
        failures=[r for r in native['violations']if r['severity']=='error']
        if not failures:break
        byid={u:i for i,r in enumerate(groups)if r['retained']for u in r['new_copper_UUIDs']};bad=set()
        for issue in failures:
            indices={byid[r['uuid']]for r in issue['items']if r['uuid']in byid}
            if not indices:raise ValueError('Native error outside exact new source-return scope '+issue['type'])
            bad|=indices
        for i in bad:
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString()in groups[i]['new_copper_UUIDs']:b.Remove(t)
            groups[i]['retained']=False;rejected.append(i)
    else:raise ValueError('Native repair bound exceeded')
    current={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};kept={u for r in groups if r['retained']for u in r['new_copper_UUIDs']}
    if set(current)!=set(oldcu)|kept or any(current.get(u)!=v for u,v in oldcu.items())or any(current[u]!=expected[u]for u in kept):raise ValueError('Old/new copper identity changed')
    if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or olddefs!=definitions(dest):raise ValueError('Source pads or zone definitions changed')
    afterclusters=native_pad_clusters(b,nets);preserved=clusters_survive(oldclusters,afterclusters);write(out/'all-source-pad-cluster-proof.json',dict(before=oldclusters,after=afterclusters,passed=preserved))
    if not preserved:raise ValueError('Actual old source cluster split')
    fills=collect_native_reference_fills(b,ALLOWED_RETURNS,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pads={p.m_Uuid.AsString():p for p in b.GetPads()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};proof=[]
    for row in groups:
        if not row['retained']:continue
        pad=pads[row['source_pad_uuid']];via=cu[row['via_uuid']];layer=b.GetLayerID(row['adjacent_layer']);peerids={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(via)}
        if pad.m_Uuid.AsString()not in peerids or not physical_reference_contact(via,layer,b.GetConnectivity())or not covered(circle(tuple(via.GetPosition()),pcbnew.FromMM(.26)),fills[row['net'],layer]):raise ValueError('Source pad/actual flashed filled layer contact not proven '+row['reference'])
        proof.append(dict(source_pad_uuid=pad.m_Uuid.AsString(),via_uuid=via.m_Uuid.AsString(),reference_layer=row['adjacent_layer'],actual_source_pad_connected=True,actual_annulus_flashed=True,native_connected_on_layer=True,full_filled_annulus=True))
    if any(sha(Path(p))!=v for p,v in frozen.items()):raise ValueError('Frozen input changed')
    anchors=validate(b,mapping);anchors['board_sha256']=sha(dest);write(out/'physical-reference-anchors.json',anchors)
    write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason=__doc__,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(kept),reviewed_added_zone_UUIDs=[]))
    receipt=dict(input_sha256=frozen,board_sha256=sha(dest),source_owned_short_ground_branches=groups,post_native_actual_source_annulus_proofs=proof,required_remaining=skips,native_rejected_groups=rejected,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),native_errors=sum(r['severity']=='error'for r in native['violations']),ignored_checks=native['ignored_checks'],all_old_Cu_pads_zone_definitions_and_native_source_clusters_preserved=True,remaining_unanchored_resources=len(anchors['unanchored_components']),uncapped_missing_joins=b.GetConnectivity().GetUnconnectedCount(False),global_distribution_capacity_qualified=False,manufacturing_ready=False)
    write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in('input_sha256','source_owned_short_ground_branches','post_native_actual_source_annulus_proofs','required_remaining')},indent=2))

if __name__=='__main__':main()
