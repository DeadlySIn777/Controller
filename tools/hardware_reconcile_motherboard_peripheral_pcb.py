"""Apply only reviewed peripheral corrections to retained real routed copper.

This preserves unrelated tracks, planes, package geometry and placement. It
does not populate missing parent parts or generate manufacturing files.
"""
import argparse,collections,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import (sha,load,write,footprint_name,
    native_parts_and_nets,load_exact_footprint,copper_pad,pad_template)
from hardware_route_logic_return import identity,xy,mm
from hardware_build_assembly import parse,dump,children,child,value,q
from hardware_populate_motherboard_pcb import courtyard_relative,Occupancy

BASE_SHA='54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5'
PROBE_IC={'U14026','U14027'}
PROBE_PASSIVES={'R14057','R14058','R14059','R14060','R14063','R14064','R14065','R14066','C14044','C14049'}
OLD_CHASSIS='/motherboard_compute/CHASSIS'
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def piece(p):
    return (p.m_Uuid.AsString(),p.GetNumber(),str(p.GetNetname()),tuple(p.GetPosition()),
        tuple(p.GetSize()),p.GetOrientationDegrees()%360,p.GetLayerSet().FmtBin(),
        p.GetShape(),p.GetAttribute(),tuple(p.GetDrillSize()),p.GetDrillShape(),
        tuple(p.GetOffset()),p.GetRoundRectRadiusRatio(),p.GetChamferPositions(),p.GetChamferRectRatio())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',required=True,type=Path);p.add_argument('--source',required=True,type=Path)
    p.add_argument('--review',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--correction-set',choices=['probe','core7-analog'],default='probe')
    a=p.parse_args();base=a.board.resolve();source=a.source.resolve();out=a.out.resolve()
    phase=a.correction_set
    expected_base=BASE_SHA if phase=='probe' else '8b8921b5e38e46c5bc44b6dc2e1a8cced1c667801ffb98b0d0246430b35985f0'
    replaced=PROBE_IC if phase=='probe' else {'L11001','U14601','U14619'}
    value_edits=PROBE_IC|PROBE_PASSIVES if phase=='probe' else replaced|{'U11007','R11022'}
    expected_new={'U14026':('MAX17612AATB+T','CNC_MB_Operator:MAX17612_T1033_ADI'),
        'U14027':('MAX17612AATB+T','CNC_MB_Operator:MAX17612_T1033_ADI')} if phase=='probe' else {
        'L11001':('XAL1010-472MED','CNC_MB_Entry:XAL1010_Coilcraft'),
        'U14601':('TMR 4-2412WI','CNC_MB_AO:TMR4WI_SIP8_Traco'),
        'U14619':('TMR 4-2412WI','CNC_MB_AO:TMR4WI_SIP8_Traco')}
    if out.exists() or sha(base)!=expected_base:raise ValueError('Fresh output and exact retained routed snapshot required')
    review=load(a.review);model=load(source/'design.json');parts=model['components']
    if review['base_sha256']!=expected_base or review['source_netlist_sha256']!=sha(source/'netlist.xml'):
        raise ValueError('Stale native reconciliation evidence')
    if review['removed_references']:raise ValueError('Physical source must retain existing components')
    if {r['reference'] for r in review['footprint_replacements']}!=replaced:
        raise ValueError('Only the exact reviewed manufacturer corrections are authorized')
    _,nodes=native_parts_and_nets(source/'netlist.xml',parts)
    b=pcbnew.LoadBoard(str(base));b.BuildConnectivity()
    fps={f.GetReference():f for f in b.GetFootprints()}
    before_tracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    before_pads={(f.GetReference(),p.m_Uuid.AsString()):piece(p) for f in b.GetFootprints() for p in f.Pads()}
    before_fps={r:(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),footprint_name(f)) for r,f in fps.items()}
    before_zones={z.m_Uuid.AsString():(z.GetNetname(),z.GetLayer(),z.Outline().Format()) for z in b.Zones()}
    nets={str(n.GetNetname()):n for n in b.GetNetsByName().values()};code=max(n.GetNetCode() for n in nets.values())+1
    for name in sorted(set(nodes.values())-set(nets)):
        n=pcbnew.NETINFO_ITEM(b,name,code);b.Add(n);nets[name]=n;code+=1
    changes={(r['reference'],r['pin']):r for r in review['changes']}
    if len(changes)!=len(review['changes']):raise ValueError('Duplicate exact reconciliation pin')
    copper=[]
    # The corrected two probe ICs have a different land/pin table. Dedicated
    # old probe local routes are invalid; remove this bounded local scope only.
    # No rail/return/shared peripheral net is eligible for this removal.
    for t in list(b.GetTracks()):
        name=str(t.GetNetname());uid=t.m_Uuid.AsString()
        if phase=='probe' and name.startswith(('/motherboard_operator/PRB0_','/motherboard_operator/PRB1_')):
            copper.append(dict(uuid=uid,before=before_tracks[uid],action='remove',reason='Dedicated previous probe-controller topology; actual MAX17612 pin and control circuit differs'))
            b.Remove(t)
        elif phase=='probe' and name==OLD_CHASSIS:
            copper.append(dict(uuid=uid,before=before_tracks[uid],action='rename_net',new_native_net='/CHASSIS',reason='All former local shield lands now reach the real common chassis bond'))
            t.SetNet(nets['/CHASSIS'])
        elif phase=='core7-analog' and name in {
            '/motherboard_power_entry/CORE_CORE_SW',
            '/motherboard_power_entry/CORE_CORE_ISNS'}:
            copper.append(dict(uuid=uid,before=before_tracks[uid],action='remove',
                reason='Required larger power inductor changes actual land positions; dedicated old converter-current paths must be rerouted to the7A envelope with separate Kelvin sensing'))
            b.Remove(t)
    if any(z.GetNetname()==OLD_CHASSIS or z.GetNetname().startswith('/motherboard_operator/PRB') for z in b.Zones()):
        raise ValueError('No implicit plane removal/reassignment is allowed')
    changed_values=[];changed_pads=[];replacement_templates={};footprint_inputs={};replacement_uuids={};placement_edits=[]
    occupied=Occupancy([courtyard_relative(fp) for ref,fp in fps.items() if ref not in replaced])
    occupied.append((331.,278.,371.,333.))
    occupied.append((421.87,260.7,447.27,338.57))
    for ref,fp in list(fps.items()):
        target=parts[ref]
        if ref in replaced:
            if (target['mpn'],target['footprint'])!=expected_new[ref]:
                raise ValueError('Exact manufacturer correction differs '+ref)
            for pad in fp.Pads():
                if copper_pad(pad) and list(b.GetConnectivity().GetConnectedTracks(pad)):
                    # Connectivity is rebuilt below; test remaining live items
                    # by UUID so stale connectivity references cannot authorize
                    # removal of unrelated shared copper.
                    existing={t.m_Uuid.AsString() for t in b.GetTracks()}
                    if any(t.m_Uuid.AsString() in existing for t in b.GetConnectivity().GetConnectedTracks(pad)):
                        raise ValueError('Replacement would abandon retained shared copper '+ref+'.'+pad.GetNumber())
            new,file=load_exact_footprint(target['footprint'],source,base)
            replacement_templates[ref]=[pad_template(q) for q in new.Pads()]
            footprint_inputs[str(file)]=sha(file);new.SetReference(ref);new.SetValue(target['value'])
            new.SetPosition(fp.GetPosition());new.SetOrientation(fp.GetOrientation())
            bounds=courtyard_relative(new)
            if phase=='core7-analog' and occupied.collision(bounds,.35):
                original=tuple(new.GetPosition());sx,sy=mm(new.GetPosition())
                candidates=sorted(((dx*.5,dy*.5) for dx in range(-100,101) for dy in range(-100,101)),
                                  key=lambda v:v[0]*v[0]+v[1]*v[1])
                for dx,dy in candidates:
                    new.SetPosition(xy((sx+dx,sy+dy)));trial=courtyard_relative(new)
                    if (trial[0]>=1 and trial[1]>=1 and trial[2]<=459 and trial[3]<=339
                        and not occupied.collision(trial,.35)):
                        bounds=trial;break
                else:raise ValueError('New manufacturer body cannot fit locally '+ref)
                placement_edits.append(dict(reference=ref,before_nm=list(original),after_nm=list(new.GetPosition()),
                    reason='Required larger manufacturer land/body; zero old attached routed copper'))
            occupied.append(bounds)
            replacement_uuids[new.m_Uuid.AsString()]=fp.m_Uuid.AsString()
            new.SetPath(fp.GetPath());new.SetDNP(fp.IsDNP());new.Value().SetVisible(False)
            new.Reference().SetLayer(pcbnew.F_Fab);new.Reference().SetTextSize(xy((.65,.65)))
            new.Reference().SetTextThickness(pcbnew.FromMM(.1))
            b.Remove(fp);b.Add(new);fps[ref]=new;fp=new
        elif footprint_name(fp)!=target['footprint']:
            raise ValueError('Unreviewed retained land pattern change '+ref)
        if ref in value_edits and fp.GetValue()!=target['value']:
            changed_values.append(dict(reference=ref,before=fp.GetValue(),after=target['value']));fp.SetValue(target['value'])
        for pad in fp.Pads():
            if not copper_pad(pad):continue
            key=(ref,pad.GetNumber());after=nodes[key];before=str(pad.GetNetname())
            if ref in replaced:
                pad.SetNet(nets[after]);continue
            if before==after:continue
            row=changes.get(key)
            if row is None or (row['old_native_net'],row['new_native_net'])!=(before,after):
                raise ValueError('Unreviewed retained physical pin change '+repr(key))
            if before!=OLD_CHASSIS and any(t.GetNetname()==before for t in b.GetTracks()):
                raise ValueError('Pin rename would abandon retained copper '+repr(key))
            if any(z.GetNetname()==before for z in b.Zones()):raise ValueError('Pin rename would abandon retained plane '+repr(key))
            changed_pads.append(row);pad.SetNet(nets[after])
    b.BuildConnectivity();out.mkdir(parents=True);dest=out/'motherboard-reconciled-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    for origin in (base.parent,source):
        for folder in origin.iterdir():
            if folder.is_dir() and (folder.name.endswith('.pretty') or folder.name=='3dmodels'):
                shutil.copytree(folder,out/folder.name,dirs_exist_ok=True)
        if (origin/'fp-lib-table').is_file():
            shutil.copyfile(origin/'fp-lib-table',out/'fp-lib-table')
    snap=out/'source-inputs';snap.mkdir()
    for name in ('design.json','netlist.xml','assembly-map.json'):shutil.copyfile(source/name,snap/('motherboard-'+name))
    pcbnew.SaveBoard(str(dest),b)
    # KiCad10 exposes footprint UUID read-only in Python. Restore only the two
    # reviewed replacement object identities in the saved native document.
    native_tree=parse(dest.read_text(encoding='utf8'));restored=set()
    for fp in children(native_tree,'footprint'):
        item=child(fp,'uuid');uid=value(item[1])
        if uid in replacement_uuids:item[1]=q(replacement_uuids[uid]);restored.add(uid)
    if restored!=set(replacement_uuids):raise ValueError('Exact replaced native identity missing')
    dest.write_text(dump(native_tree)+'\n',encoding='utf8')
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--format','json','--output',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();actual={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    approved={r['uuid']:r for r in copper};errors=[]
    for uid,before in before_tracks.items():
        row=approved.get(uid);after=actual.get(uid)
        if row is None and after!=before:errors.append('Unrelated copper changed '+uid)
        elif row and row['action']=='remove' and after is not None:errors.append('Obsolete probe route remains '+uid)
        elif row and row['action']=='rename_net' and (after is None or after[:1]+after[2:]!=before[:1]+before[2:] or after[1]!='/CHASSIS'):
            errors.append('Shield alias changed geometry '+uid)
    if set(actual)-set(before_tracks):errors.append('Unexpected new route during reconciliation')
    observed={f.GetReference():f for f in fresh.GetFootprints()}
    if set(observed)!=set(before_fps):errors.append('Physical retained inventory changed')
    for ref,fp in observed.items():
        old=before_fps[ref];now=(fp.m_Uuid.AsString(),tuple(fp.GetPosition()),fp.GetOrientationDegrees(),fp.GetLayer(),footprint_name(fp))
        movement=next((r for r in placement_edits if r['reference']==ref),None)
        expected_position=tuple(movement['after_nm']) if movement else old[1]
        if now[:4]!=(old[0],expected_position,old[2],old[3]) or ref not in replaced and now!=old:
            errors.append('Unrelated footprint moved/replaced '+ref)
        if ref in replaced:
            if collections.Counter(pad_template(q) for q in fp.Pads())!=collections.Counter(replacement_templates[ref]):errors.append('New exact manufacturer lands differ '+ref)
        else:
            for pad in fp.Pads():
                old=before_pads[ref,pad.m_Uuid.AsString()];new=piece(pad)
                if new[:2]+new[3:]!=old[:2]+old[3:]:errors.append('Unrelated pad geometry changed '+ref+'.'+pad.GetNumber())
        for pad in fp.Pads():
            if copper_pad(pad) and pad.GetNetname()!=nodes[ref,pad.GetNumber()]:errors.append('Retained pad differs from actual native source '+ref+'.'+pad.GetNumber())
    zones={z.m_Uuid.AsString():(z.GetNetname(),z.GetLayer(),z.Outline().Format()) for z in fresh.Zones()}
    if zones!=before_zones:errors.append('Retained planes changed')
    drc=load(out/'drc.json')
    report=dict(source_board_sha256=expected_base,candidate_board_sha256=sha(dest),source_design_sha256=sha(source/'design.json'),
        source_netlist_sha256=sha(source/'netlist.xml'),physical_retained=len(observed),required_parent_parts=len(parts),
        missing_parent_parts=len(set(parts)-set(observed)),retained_track_via_items=len(actual),
        exact_copper_edits=copper,exact_pad_edits=changed_pads,exact_value_edits=changed_values,
        manufacturer_footprint_replacements=sorted(replaced),exact_local_placement_edits=placement_edits,footprint_inputs_sha256=footprint_inputs,
        native_DRC_regular=len(drc['violations']),native_DRC_ignored=drc.get('ignored_checks',[]),
        native_uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        retained_source_reconciliation_pass=not errors,errors=errors,
        population_complete=False,routing_complete=False,manufacturing_ready=False)
    write(out/'receipt.json',report)
    print(json.dumps({k:report[k] for k in ('physical_retained','missing_parent_parts','retained_track_via_items','native_DRC_regular','native_uncapped_missing_joins','retained_source_reconciliation_pass','errors')}))
    if errors:raise ValueError('Bounded physical/source checks failed')
if __name__=='__main__':main()
