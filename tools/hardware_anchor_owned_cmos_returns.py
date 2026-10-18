"""Add bounded, actual source-owned low-current return stitches.

This does not create planes, change source, move parts, or qualify distribution.
Only native CMOS/MCU/low-current supervisor bypass-owner return pins are used.
Each new stitch must physically connect its numbered source pad to an existing
filled own-return resource on the adjacent layer. Existing copper, source pads,
and zone definitions are immutable; native DRC decides acceptance.
"""
import argparse, collections, json, math, shutil
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse, children, dump
from hardware_map_motherboard_domains import RAW_RETURNS
from hardware_zone_motherboard_returns import return_net
from hardware_route_owned_bypass_loops import Geometry, drc, connected, CATEGORIES
from hardware_route_logic_return import identity, mm, xy
from hardware_populate_motherboard_pcb import sha, write, pad_template
from hardware_check_return_corridors import ReturnCheck, circle, covered
from hardware_merge_bounded_pcb_delta import zone_definition

CMOS_PREFIXES=('SN74','74LVC','74AHCT','STM32G031','TCA9517','TCA9534',
               'TPS3808','TPS3839','TPS3851','TPS3700','TPS3702','LTC2962','LTC6994',
               'ISO7720','ISO7760','ISO7761','ISO7762','ISO1540','W25Q32')
EXCLUDED_ADC={f'C147{i}' for i in range(40,47)}|{'U14734'}
EXCLUDED_BLOCKS={'motherboard_power_entry','motherboard_di','motherboard_safety_sensor'}

def source_clusters(b):
    b.BuildConnectivity(); found=set(); groups=[]
    for p in b.GetPads():
        if not p.GetNumber() or not p.IsOnCopperLayer() or p.m_Uuid.AsString() in found:continue
        ids={v.m_Uuid.AsString() for v in b.GetConnectivity().GetConnectedItems(p)
             if isinstance(v,pcbnew.PAD) and v.GetNumber() and v.IsOnCopperLayer()}
        ids.add(p.m_Uuid.AsString()); found.update(ids); groups.append(ids)
    return groups

def warning_key(v):
    return v['type'],tuple(sorted(i['uuid'] for i in v['items'])),v.get('description','')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('board','map','owners','source','out'):ap.add_argument('--'+k,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    frozen={str(p.resolve()):sha(p) for p in (a.board,a.map,a.owners,a.source,Path(__file__))}
    mapping=json.loads(a.map.read_text()); owners=json.loads(a.owners.read_text()); source=json.loads(a.source.read_text())
    if mapping.get('errors') or not mapping['source_physical_population_complete']:raise ValueError('Complete native source-domain map required')
    if owners.get('errors') or owners.get('pending') or not owners['all_owner_mappings_verified']:raise ValueError('Complete source-verified bypass owners required')
    a.out.mkdir(parents=True); dest=a.out/'owned-cmos-return-stitches-candidate.kicad_pcb'
    shutil.copyfile(a.board,dest)
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    for f in a.board.parent.iterdir():
        if f.is_dir() and (f.suffix=='.pretty' or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
        elif f.name=='fp-lib-table':shutil.copyfile(f,a.out/f.name)
    baseline=drc(dest,a.out,'baseline')
    if any(v['severity']=='error' or v['type'] not in {'isolated_copper','via_dangling','track_dangling'} for v in baseline['violations']):
        raise ValueError('Baseline has unrelated or error-level native geometry issues')
    basekeys=collections.Counter(warning_key(v) for v in baseline['violations'])
    b=pcbnew.LoadBoard(str(dest)); b.BuildConnectivity(); g=Geometry(b); check=ReturnCheck(b,{})
    old={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    oldpads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p)) for p in b.GetPads()}
    raw_before=parse(dest.read_text())
    definitions={str(next(v[1] for v in children(z,'uuid'))):zone_definition(z) for z in children(raw_before,'zone')}
    # Map and board must describe the same actual native copper-pad objects.
    mapped={v['uuid']:v for v in mapping['pads']}
    for p in b.GetPads():
        if not p.GetNumber() or not p.IsOnCopperLayer():continue
        row=mapped.get(p.m_Uuid.AsString())
        if not row or row['reference']!=p.GetParentFootprint().GetReference() or row['pin']!=p.GetNumber() or row['net']!=p.GetNetname() or any(abs(x-y)>1e-6 for x,y in zip(row['position_mm'],mm(p.GetPosition()))):
            raise ValueError('Actual source-pad map differs '+p.GetParentFootprint().GetReference()+'.'+p.GetNumber())
    clusters=source_clusters(b); fps={f.GetReference():f for f in b.GetFootprints()}
    bypin={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints() for p in f.Pads() if p.GetNumber() and p.IsOnCopperLayer()}
    selected={}; exclusions=[]
    for cap in owners['capacitors']:
        if cap['category'] not in CATEGORIES:continue
        ref=cap['ref']; owner=cap['owner']; actual=source['components'][owner]
        if actual['mpn']!=cap['actual_owner_MPN']:raise ValueError('Owner MPN changed '+owner)
        if (ref in EXCLUDED_ADC or owner in EXCLUDED_ADC or actual['source_block'] in EXCLUDED_BLOCKS
            or not actual['mpn'].startswith(CMOS_PREFIXES)):
            exclusions.append(dict(ref=ref,owner=owner,MPN=actual['mpn'],reason='Dedicated cell, power/precision/current-switch group, or outside reviewed low-current CMOS scope'));continue
        for endpoint in [dict(ref=ref,pin=cap['cap_return'])]+cap['return_nodes']:
            p=bypin[endpoint['ref'],endpoint['pin']]; row=mapped[p.m_Uuid.AsString()]
            own=return_net(row)
            if own!=p.GetNetname() or own in RAW_RETURNS:raise ValueError('Own source-return identity is invalid '+ref)
            if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
            if p.GetParentFootprint().GetLayer() not in (pcbnew.F_Cu,pcbnew.B_Cu):raise ValueError('Unexpected source return layer')
            if not p.IsOnLayer(p.GetParentFootprint().GetLayer()):raise ValueError('Actual SMD source copper side differs')
            selected.setdefault(p.m_Uuid.AsString(),dict(pad=p,owner=owner,MPN=actual['mpn'],capacitor=ref,domain=row['domain']))
    groups=[]; already=[]; skips=[]; added={}
    def own_fill(pt,net,layer):
        try:return covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),check.reference(net,layer))
        except ValueError:return False
    for key,item in selected.items():
        p=item['pad']; net=p.GetNetname(); layer=p.GetParentFootprint().GetLayer(); adjacent=pcbnew.In1_Cu if layer==pcbnew.F_Cu else pcbnew.In4_Cu; start=mm(p.GetPosition())
        existing=[v for v in b.GetConnectivity().GetConnectedItems(p) if isinstance(v,pcbnew.PCB_VIA) and v.GetNetname()==net
                  and math.dist(mm(v.GetPosition()),start)<=2 and own_fill(mm(v.GetPosition()),net,adjacent)]
        if existing:
            already.append(dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),pad_uuid=key,return_net=net,adjacent_layer=b.GetLayerName(adjacent),actual_source_connected_via_UUIDs=[v.m_Uuid.AsString() for v in existing]));continue
        chosen=None
        for distance in (.7,.85,1.05,1.35,1.7,2.):
            for angle in range(16):
                pt=(round(start[0]+distance*math.cos(angle*math.pi/8),6),round(start[1]+distance*math.sin(angle*math.pi/8),6))
                if g.via(pt,net) and own_fill(pt,net,adjacent) and g.clear([start,pt],net,layer):chosen=pt;break
            if chosen:break
        if chosen is None:
            skips.append(dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),pad_uuid=key,return_net=net,reason='No legal short source-return escape into actual adjacent own fill'));continue
        track=pcbnew.PCB_TRACK(b);track.SetNet(b.FindNet(net));track.SetLayer(layer);track.SetStart(p.GetPosition());track.SetEnd(xy(chosen));track.SetWidth(pcbnew.FromMM(.2));b.Add(track);g.add(track)
        via=pcbnew.PCB_VIA(b);via.SetNet(b.FindNet(net));via.SetPosition(xy(chosen));via.SetWidth(pcbnew.FromMM(.5));via.SetDrill(pcbnew.FromMM(.2));via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetRemoveUnconnected(True);via.SetIsFree(True);b.Add(via);g.add(via)
        group=dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),pad_uuid=key,return_net=net,domain=item['domain'],owner=item['owner'],owner_MPN=item['MPN'],capacitor=item['capacitor'],adjacent_layer=b.GetLayerName(adjacent),via_uuid=via.m_Uuid.AsString(),new_copper_UUIDs=[track.m_Uuid.AsString(),via.m_Uuid.AsString()],escape_length_mm=math.dist(start,chosen),retained=True)
        groups.append(group);added.update({t.m_Uuid.AsString():identity(t) for t in (track,via)})
    write(a.out/'generation.json',dict(input_sha256=frozen,new_stitch_groups=groups,already_source_connected=already,required_remaining=skips,explicitly_excluded=exclusions))
    # Native DRC may reject only new exact groups; every pre-existing issue
    # stays explicitly reported. No ignored check or plane suppression is used.
    rejected=[]
    for attempt in range(5):
        pcbnew.SaveBoard(str(dest),b); report=drc(dest,a.out,'native-'+str(attempt)); b=pcbnew.LoadBoard(str(dest)); b.BuildConnectivity()
        unknown=[]; counts=collections.Counter()
        for v in report['violations']:
            k=warning_key(v); counts[k]+=1
            if counts[k]>basekeys[k] and v['type']!='isolated_copper':unknown.append(v)
        if not unknown:break
        new_to_group={u:i for i,v in enumerate(groups) if v['retained'] for u in v['new_copper_UUIDs']}; bad=set()
        for v in unknown:
            touched={new_to_group[x['uuid']] for x in v['items'] if x['uuid'] in new_to_group}
            if not touched:raise ValueError('Native refill found issue outside exact new stitch scope: '+v['type'])
            bad.update(touched)
        for index in bad:
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString() in groups[index]['new_copper_UUIDs']:b.Remove(t)
            groups[index]['retained']=False;rejected.append(index)
    else:raise ValueError('Native new-group repair bound exceeded')
    current={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}; kept={u for v in groups if v['retained'] for u in v['new_copper_UUIDs']}
    if any(current.get(u)!=x for u,x in old.items()) or set(current)!=set(old)|kept or any(current[u]!=added[u] for u in kept):raise ValueError('Native original or new copper identity changed')
    pads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p)) for p in b.GetPads()}
    if oldpads!=pads:raise ValueError('Native source pads or manufacturer lands changed')
    aftertree=parse(dest.read_text()); afterdefs={str(next(v[1] for v in children(z,'uuid'))):zone_definition(z) for z in children(aftertree,'zone')}
    if definitions!=afterdefs:raise ValueError('Existing zone definition changed')
    pad_by_uuid={p.m_Uuid.AsString():p for p in b.GetPads()}; freshcheck=ReturnCheck(b,{}); tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}; proofs=[]
    for group in groups:
        if not group['retained']:continue
        p=pad_by_uuid[group['pad_uuid']];via=tracks[group['via_uuid']];layer=b.GetLayerID(group['adjacent_layer'])
        if not connected(b,p,via) or not covered(circle(tuple(via.GetPosition()),pcbnew.FromMM(.24)),freshcheck.reference(group['return_net'],layer)):
            raise ValueError('Actual numbered-source-pad to adjacent filled resource is not closed')
        anchors=freshcheck.source_anchors(via,group['return_net'])
        if not any(v['pad_uuid']==group['pad_uuid'] for v in anchors):raise ValueError('Own numbered source pad missing from actual physical anchor proof')
        proofs.append(dict(via_uuid=group['via_uuid'],source_pad_uuid=group['pad_uuid'],adjacent_layer=group['adjacent_layer'],actual_numbered_source_pad_anchors=anchors))
    for ids in clusters:
        p=pad_by_uuid[next(iter(ids))]; actual={x.m_Uuid.AsString() for x in b.GetConnectivity().GetConnectedItems(p) if isinstance(x,pcbnew.PAD)}|{p.m_Uuid.AsString()}
        if not ids<=actual:raise ValueError('Prior actual source-pad cluster fragmented')
    if any(sha(Path(p))!=digest for p,digest in frozen.items()):raise ValueError('Input changed during native transaction')
    scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Source-owned low-current CMOS/MCU/supervisor short return stitches to actual adjacent own filled resources; exact old copper, zones, pads and poses immutable.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(kept),reviewed_added_zone_UUIDs=[])
    write(a.out/'bounded-scope.json',scope)
    receipt=dict(input_sha256=frozen,board_sha256=sha(dest),actual_source_owned_stitches=groups,actual_source_to_filled_reference_proofs=proofs,already_local_source_connected=already,required_remaining=skips,explicitly_excluded=exclusions,native_rejected_groups=rejected,all_old_source_pad_clusters_retained=True,old_copper_and_all_source_pads_and_zone_definitions_retained=True,native_DRC_types=dict(collections.Counter(v['type'] for v in report['violations'])),native_errors=sum(v['severity']=='error' for v in report['violations']),ignored_checks=[],uncapped_missing_joins=b.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,global_return_current_capacity_or_physical_loop_inductance_qualified=False)
    write(a.out/'receipt.json',receipt);print(dict(added_return_stitches=len(proofs),already_source_connected=len(already),remaining=len(skips),native_DRC_types=receipt['native_DRC_types'],uncapped_missing_joins=receipt['uncapped_missing_joins'],board_sha256=receipt['board_sha256']))

if __name__=='__main__':main()
