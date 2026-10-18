"""Incrementally populate exact native parts while preserving routed objects.

Local capacitor owners come from reviewed pin/return manifests. Connector
placement reserves the complete mating and wiring envelope. This is an
engineering intermediate; native DRC and complete routing remain required.
"""
import argparse,collections,math,re,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import (REPORT,CLI,sha,load,write,
    copper_pad,footprint_name,native_parts_and_nets,native_pin_functions,
    load_exact_footprint,pad_template,courtyard_relative,Occupancy,place_cluster)
from hardware_route_logic_return import identity,xy,mm
from hardware_reconcile_motherboard_peripheral_pcb import piece

def capacitor_owners(files,parts,nodes):
    result={}
    for file in files:
        data=load(file)
        for row in data.get('capacitors',data.get('actual_owner_paths',[])):
            if 'capacitor_reference' in row:
                cap=row['capacitor_reference'];owner=row['real_owner_reference']
                spec=dict(owner=owner,owner_power_pin=row['real_owner_signal_pin'],
                    owner_return_pins=row['real_owner_matching_return_pins'],
                    capacitor_power_pin=row['capacitor_signal_pad'],
                    capacitor_return_pin=row['capacitor_return_pad'],
                    limit_mm=row['placement_target_pad_distance_mm'],
                    path=row['exact_connection_path'],category=row['category'])
            else:
                cap=row['capacitor'];spec=dict(row,limit_mm=3.,category='IC_local_bypass')
            if cap not in parts or spec['owner'] not in parts:raise ValueError('Missing actual bypass owner '+cap)
            returns={nodes[spec['owner'],str(pin)] for pin in spec['owner_return_pins']}
            if nodes[cap,str(spec['capacitor_return_pin'])] not in returns:
                raise ValueError('Bypass crosses independent returns '+cap)
            if cap in result and result[cap]!=spec:raise ValueError('Duplicated inconsistent bypass ownership '+cap)
            result[cap]=spec
    # Compute source records the actual owner reference directly, not a
    # guessed nearest regulator on a common rail.
    for ref,c in parts.items():
        if not ref.startswith('C') or ref in result or c.get('source_block')!='motherboard_compute':continue
        # Some generated roles concatenate 'U15018' and '5V' without a
        # space. Match an actual source reference, never absorb that voltage
        # digit into a fictitious IC name.
        owners=[r for r in parts if r.startswith('U') and c.get('role','').startswith(r)]
        if not owners:continue
        owner=max(owners,key=len)
        functions=native_pin_functions_cache[owner]
        capnets={nodes[ref,p] for p in c['pins']}
        power=[p for p,f in functions.items() if nodes.get((owner,p)) in capnets and
            f.get('type') in ('power_in','power_out') and re.match(r'^(VCC|VDD|VIN|IN$|VS$|OUT$)',f.get('name',''))]
        ground=[p for p,f in functions.items() if nodes.get((owner,p)) in capnets and
                re.search(r'GND|VSS',f.get('name',''))]
        if len(power)!=1 or not ground:continue
        cp=[p for p in c['pins'] if nodes[ref,p]==nodes[owner,power[0]]]
        cg=[p for p in c['pins'] if nodes[ref,p] in {nodes[owner,g] for g in ground}]
        if len(cp)!=1 or len(cg)!=1:continue
        result[ref]=dict(owner=owner,owner_power_pin=power[0],owner_return_pins=ground,
            capacitor_power_pin=cp[0],capacitor_return_pin=cg[0],limit_mm=3.,category='source_named_owner')
    if 'C11088' in parts:
        if (parts['C11088']['mpn'],parts['C11029']['mpn'])!=('16SVPG330M','16SVPG330M'):
            raise ValueError('Exact reviewed additive core output reservoir differs')
        for pin in ('1','2'):
            if nodes['C11088',pin]!=nodes['C11029',pin]:raise ValueError('Output bulk polarity/domain differs')
        result['C11088']=dict(owner='C11029',owner_power_pin='1',owner_return_pins=['2'],
            capacitor_power_pin='1',capacitor_return_pin='2',limit_mm=15.,category='additive_existing_output_reservoir')
    return result

def connector_envelope(fp):
    """Phoenix fitted header +18.7mm mate + conservative wire/tool corridor.

    Stock header mating direction is local+Y. The extra corridor is a
    mechanical design reservation; external enclosure clearance is separate.
    """
    box=courtyard_relative(fp);angle=math.radians(-fp.GetOrientationDegrees())
    dx,dy=-math.sin(angle),math.cos(angle)
    # Board coordinates use KiCad clockwise-negative screen rotation.
    direction=mm(fp.GetPosition())
    # Derive direction from actual transformed pad row rather than assume
    # the library has a particular board-rotation convention.
    p1=next(p for p in fp.Pads() if p.GetNumber()=='1')
    p2=next(p for p in fp.Pads() if p.GetNumber()=='2')
    x1,y1=mm(p1.GetPosition());x2,y2=mm(p2.GetPosition())
    length=math.hypot(x2-x1,y2-y1);dx,dy=-(y2-y1)/length,(x2-x1)/length
    extension=18.
    return (box[0]+min(0.,dx*extension)-1.,box[1]+min(0.,dy*extension)-1.,
            box[2]+max(0.,dx*extension)+1.,box[3]+max(0.,dy*extension)+1.)

def place_terminal(fp,occupied,desired):
    options=[]
    for angle in (0.,90.,180.,270.):
        fp.SetPosition(xy((0,0)));fp.SetOrientationDegrees(angle)
        box=courtyard_relative(fp);env=connector_envelope(fp)
        # Prefer all edge-accessible candidates. Conservative mating
        # reservations may extend off the PCB, but the actual header cannot.
        xmin=math.ceil(1.-box[0]);xmax=math.floor(459.-box[2])
        ymin=math.ceil(1.-box[1]);ymax=math.floor(339.-box[3])
        for x in range(xmin,xmax+1,2):
            for y in range(ymin,ymax+1,2):
                bounds=(x+box[0],y+box[1],x+box[2],y+box[3])
                reserve=(x+env[0],y+env[1],x+env[2],y+env[3])
                if occupied.collision(reserve,.5):continue
                edge=min(bounds[0],460-bounds[2],bounds[1],340-bounds[3])
                outward=reserve[0]<0 or reserve[1]<0 or reserve[2]>460 or reserve[3]>340
                score=(0 if outward else 100000)+edge*100+math.dist((x,y),desired)
                options.append((score,x,y,angle,bounds,reserve))
    if not options:raise ValueError('No full connector mating/wire clearance '+fp.GetReference())
    _,x,y,angle,box,reserve=min(options)
    fp.SetPosition(xy((x,y)));fp.SetOrientationDegrees(angle);occupied.append(reserve)
    return dict(reference=fp.GetReference(),position_mm=[x,y],rotation_degrees=angle,
        courtyard_mm=list(box),mating_wire_tool_reservation_mm=list(reserve),
        full_mate_collision_check=True,enclosure_clearance_verified=False)

def main():
    global native_pin_functions_cache
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--review',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--capacitor-owners',action='append',type=Path,default=[])
    a=p.parse_args();base=a.board.resolve();source=a.source.resolve();out=a.out.resolve()
    if out.exists() or not out.is_relative_to(REPORT):raise ValueError('Fresh owned output required')
    review=load(a.review);model=load(source/'design.json');parts=model['components']
    if review['base_sha256']!=sha(base) or review['source_netlist_sha256']!=sha(source/'netlist.xml'):
        raise ValueError('Stale actual native review')
    if review['removed_references'] or review['footprint_replacements'] or review['changes']:
        raise ValueError('Apply independently reviewed retained-source corrections first')
    native,nodes=native_parts_and_nets(source/'netlist.xml',parts)
    native_pin_functions_cache=native_pin_functions(source/'netlist.xml')
    bypass=capacitor_owners(a.capacitor_owners,parts,nodes)
    inputs=[base,source/'design.json',source/'netlist.xml',source/'assembly-map.json',a.review,*a.capacitor_owners]
    hashes={str(f.resolve()):sha(f) for f in inputs}
    b=pcbnew.LoadBoard(str(base));b.BuildConnectivity()
    retained={f.GetReference():f for f in b.GetFootprints()}
    tracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    pads={(f.GetReference(),p.m_Uuid.AsString()):piece(p) for f in b.GetFootprints() for p in f.Pads()}
    fps={r:(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),footprint_name(f)) for r,f in retained.items()}
    nets={str(n.GetNetname()):n for n in b.GetNetsByName().values()};code=max(n.GetNetCode() for n in nets.values())+1
    for name in sorted(set(nodes.values())-set(nets)):
        n=pcbnew.NETINFO_ITEM(b,name,code);b.Add(n);nets[name]=n;code+=1
    added={};templates={};land_hashes={}
    for ref,c in parts.items():
        if ref in retained:continue
        fp,file=load_exact_footprint(c['footprint'],source,base);land_hashes[str(file)]=sha(file)
        templates[ref]=[pad_template(q) for q in fp.Pads()]
        fp.SetReference(ref);fp.SetValue(c['value']);fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.F_Fab);fp.Reference().SetTextSize(xy((.65,.65)))
        fp.Reference().SetTextThickness(pcbnew.FromMM(.1));fp.SetDNP(c.get('dnp',False))
        component=native[ref];fp.SetPath(pcbnew.KIID_PATH(component.find('sheetpath').attrib['tstamps']+component.findtext('tstamps')))
        b.Add(fp)
        for pad in fp.Pads():
            if copper_pad(pad):pad.SetNet(nets[nodes[ref,pad.GetNumber()]])
        added[ref]=fp
    allfps={**retained,**added};occupied=Occupancy([courtyard_relative(f) for f in retained.values()])
    # Exact existing purchased module bodies. Do not populate below them.
    occupied.append((331.,278.,371.,333.));occupied.append((421.87,260.7,447.27,338.57))
    placements=[];remaining=dict(added)
    for ref in sorted(r for r in added if r.startswith('J195')):
        fp=added[ref]
        meaningful={nodes[ref,p] for p in parts[ref]['pins'] if not re.search(r'GND|0V|V_PROTECTED|V_LIMITED|unconnected-',nodes[ref,p])}
        locations=[mm(f.GetPosition()) for r,f in retained.items() if any(nodes.get((r,p.GetNumber())) in meaningful for p in f.Pads())]
        desired=tuple(sum(v[i] for v in locations)/len(locations) for i in (0,1)) if locations else (230.,170.)
        placements.append(place_terminal(fp,occupied,desired));remaining.pop(ref)
        print('Mating clearance placed '+ref,flush=True)
    regions={
        # Large real computer ports must reserve space before the smaller
        # status/comms passives consume the bottom perimeter.
        'motherboard_compute':(223.,225.,231.,111.),
        'motherboard_analog_input':(10.,104.,211.,230.),
        'motherboard_safety_sensor':(10.,104.,211.,230.),
        'motherboard_comms':(223.,10.,231.,266.),
        'motherboard_status':(223.,10.,231.,266.),
        'motherboard_identity_io':(10.,104.,211.,230.),
        'motherboard_operator':(10.,239.,211.,95.),
        'motherboard_power_entry':(225.,95.,229.,182.),
        'motherboard_terminals':(10.,104.,444.,230.)}
    targets={cap:spec['owner'] for cap,spec in bypass.items()}
    for block,rect in regions.items():
        refs=[r for r in remaining if parts[r]['source_block']==block]
        if not refs:continue
        placements.extend(dict(row,region=block) for row in place_cluster(
            b,refs,allfps,parts,nodes,rect,targets,native_pin_functions_cache,occupied,bypass))
        for ref in refs:remaining.pop(ref)
        print('Populated '+block+': '+str(len(refs)),flush=True)
    if remaining:raise ValueError('Unplanned physical source additions '+str(sorted(remaining)))
    out.mkdir(parents=True);dest=out/'motherboard-populated-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    for origin in (base.parent,source):
        for folder in origin.iterdir():
            if folder.is_dir() and (folder.name.endswith('.pretty') or folder.name=='3dmodels'):
                shutil.copytree(folder,out/folder.name,dirs_exist_ok=True)
        if (origin/'fp-lib-table').is_file():shutil.copyfile(origin/'fp-lib-table',out/'fp-lib-table')
    snap=out/'source-inputs';snap.mkdir()
    for name in ('design.json','netlist.xml','assembly-map.json'):shutil.copyfile(source/name,snap/('motherboard-'+name))
    write(out/'placement-ledger.json',placements);write(out/'bypass-owner-inputs.json',bypass)
    b.BuildConnectivity();pcbnew.SaveBoard(str(dest),b)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--format','json','--output',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(run.stdout+run.stderr)
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();observed={f.GetReference():f for f in fresh.GetFootprints()};errors=[]
    if set(observed)!=set(parts):errors.append('Complete source reference inventory differs')
    if {t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}!=tracks:errors.append('Routed copper changed during population')
    for ref,fp in observed.items():
        if ref in fps and (fp.m_Uuid.AsString(),tuple(fp.GetPosition()),fp.GetOrientationDegrees(),footprint_name(fp))!=fps[ref]:
            errors.append('Retained physical part changed '+ref)
        if ref in templates and collections.Counter(pad_template(p) for p in fp.Pads())!=collections.Counter(templates[ref]):
            errors.append('Exact new native pad geometry differs '+ref)
        for pad in fp.Pads():
            if ref in retained and piece(pad)!=pads.get((ref,pad.m_Uuid.AsString())):errors.append('Retained physical pad changed '+ref)
            if copper_pad(pad) and str(pad.GetNetname())!=nodes.get((ref,pad.GetNumber())):errors.append('Native pin/net mismatch '+ref+'.'+pad.GetNumber())
    if not all(sha(Path(f))==h for f,h in hashes.items()):errors.append('Frozen input changed during population')
    drc=load(out/'drc.json');report=dict(source_hashes=hashes,board_sha256=sha(dest),land_pattern_hashes=land_hashes,
        physical_parts=len(observed),added_parts=len(added),retained_parts=len(retained),retained_track_via_items=len(tracks),
        exact_population_and_copper_retention_pass=not errors,errors=errors,native_DRC_regular=len(drc['violations']),
        native_DRC_ignored=drc.get('ignored_checks',[]),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        local_bypass_and_converter_loop_placement_complete=False,final_mechanical_qualification=False,
        routing_complete=False,manufacturing_ready=False)
    write(out/'receipt.json',report);print(str({k:report[k] for k in ('physical_parts','added_parts','native_DRC_regular','uncapped_missing_joins','errors')}))
    if errors:raise ValueError('Independent exact population checks failed')

if __name__=='__main__':main()
