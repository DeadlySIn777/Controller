"""Populate an existing reviewed motherboard without discarding routed copper.

The reconcile receipt bounds each previously unrouted pad-name change. No
track or filled-zone net may change here. This is native placement engineering,
not a manufacturing export or electrical/loop/mechanical qualification.
"""
import argparse,collections,json,shutil,subprocess,sys
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import (ROOT,REPORT,CLI,sha,load,write,copper_pad,
    footprint_name,native_parts_and_nets,native_pin_functions,load_exact_footprint,
    pad_template,verify_population,native_retained_objects,watchdog_clear_source_check,
    courtyard_relative,Occupancy,place_cluster,bb)
from hardware_route_logic_return import identity,pad_identity,xy

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--reconcile',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();base=a.board.resolve();source=a.source.resolve();out=a.out.resolve()
    if out.exists() or not out.is_relative_to(REPORT):raise ValueError('Use a fresh owned report directory')
    model=load(source/'design.json');parts=model['components'];mapping=load(source/'assembly-map.json')
    native,nodes=native_parts_and_nets(source/'netlist.xml',parts)
    reviewed=load(a.reconcile);ledger=reviewed['changes']
    if reviewed['base_sha256']!=sha(base) or reviewed['physical_parts']!=len(parts):raise ValueError('Stale reconcile receipt')
    permitted={(r['reference'],r['pin']):(r['old_native_net'],r['new_native_net']) for r in ledger}
    if len(permitted)!=len(ledger):raise ValueError('Duplicate reconciliation')
    clear=watchdog_clear_source_check(model,nodes)
    if not clear['ok']:raise ValueError(str(clear['errors']))
    inputs=[base,source/'design.json',source/'netlist.xml',source/'assembly-map.json',a.reconcile.resolve()]
    hashes={str(f):sha(f) for f in inputs};board=pcbnew.LoadBoard(str(base));board.BuildConnectivity()
    retained={f.GetReference():f for f in board.GetFootprints()}
    if not set(retained)<=set(parts):raise ValueError('Source removed a retained component')
    old_tracks={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    old_pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):pad_identity(p) for p in board.GetPads() if copper_pad(p)}
    old_fps={r:(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),footprint_name(f)) for r,f in retained.items()}
    nets={str(n.GetNetname()):n for n in board.GetNetsByName().values()};code=max(n.GetNetCode() for n in nets.values())+1
    for name in sorted(set(nodes.values())-set(nets)):
        n=pcbnew.NETINFO_ITEM(board,name,code);board.Add(n);nets[name]=n;code+=1
    observed_changes=set()
    for ref,fp in retained.items():
        if footprint_name(fp)!=parts[ref]['footprint']:raise ValueError('Unreviewed retained footprint replacement '+ref)
        for pad in fp.Pads():
            if not copper_pad(pad):continue
            key=ref,pad.GetNumber();expected=nodes[key];before=pad.GetNetname()
            if expected==before:continue
            if permitted.get(key)!=(before,expected):raise ValueError('Unreviewed pad rename '+repr(key))
            if any(t.GetNetname()==before for t in board.GetTracks()) or any(z.GetNetname()==before for z in board.Zones()):
                raise ValueError('Reconciliation would abandon existing copper/plane '+repr(key))
            pad.SetNet(nets[expected]);observed_changes.add(key)
    if observed_changes!=set(permitted):raise ValueError('Reconciliation includes unused or missing changes')
    added={};templates={};footprint_inputs={}
    for ref,c in parts.items():
        if ref in retained:continue
        fp,file=load_exact_footprint(c['footprint'],source,base);footprint_inputs[str(file)]=sha(file)
        templates[ref]=[pad_template(q) for q in fp.Pads()]
        fp.SetReference(ref);fp.SetValue(c['value']);fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.F_Fab);fp.Reference().SetTextSize(xy((.65,.65)));fp.Reference().SetTextThickness(pcbnew.FromMM(.1))
        fp.SetDNP(c.get('dnp',False));component=native[ref]
        fp.SetPath(pcbnew.KIID_PATH(component.find('sheetpath').attrib['tstamps']+component.findtext('tstamps')))
        board.Add(fp)
        if {q.GetNumber() for q in fp.Pads() if copper_pad(q)}!={pin for r,pin in nodes if r==ref}:
            raise ValueError('Exact numbered pad inventory differs '+ref)
        for pad in fp.Pads():
            if copper_pad(pad):pad.SetNet(nets[nodes[ref,pad.GetNumber()]])
        added[ref]=fp
    occupied=Occupancy([courtyard_relative(f) for f in retained.values()])
    fixed={'J15001':(334.,308.,0.),'J15002':(368.,308.,0.),
           'J16001':(446.,337.,180.),'J16002':(423.14,337.,180.),
           'R18001':(44.3,27.,0.),'R18002':(42.,11.,90.),
           'R18003':(17.2,61.6,-90.),'R18004':(27.,131.,0.),'R18005':(132.,131.,0.)}
    placements=[]
    for ref,(x,y,angle) in fixed.items():
        if ref not in added:continue
        fp=added[ref];fp.SetOrientationDegrees(angle);fp.SetPosition(xy((x,y)))
        bounds=courtyard_relative(fp)
        if ref.startswith('R180') and occupied.collision(bounds,.35):
            # Keep power parts local to the exact modified endpoint while
            # avoiding every real courtyard; no module mating pitch moves.
            offsets=sorted(((dx*.5,dy*.5) for dx in range(-8,9) for dy in range(-8,9)),key=lambda p:p[0]**2+p[1]**2)
            for dx,dy in offsets:
                fp.SetPosition(xy((x+dx,y+dy)));trial=courtyard_relative(fp)
                if not occupied.collision(trial,.35):
                    x+=dx;y+=dy;bounds=trial;break
        if occupied.collision(bounds,.35):raise ValueError('Actual module socket conflicts '+ref)
        occupied.append(bounds);placements.append(dict(reference=ref,position_mm=[x,y],rotation_degrees=angle,
            region='local power correction' if ref.startswith('R180') else 'exact purchased-module mating geometry'))
    # Whole-module reservations exclude every other package under compute and
    # ESP bodies; their fixed sockets are the only intended exceptions.
    occupied.append((331.,278.,371.,333.));occupied.append((421.87,275.7,447.27,338.57))
    regions={'motherboard_io_control':(10.,167.,210.,68.),
        'motherboard_operator':(10.,239.,210.,96.),
        'motherboard_power_entry':(225.,95.,229.,182.),
        'motherboard_process':(225.,273.,128.,63.),
        'motherboard_acc_control':(225.,239.,125.,33.),
        'motherboard_analog_output':(354.,194.,99.,78.),
        'motherboard_compute':(372.,278.,45.,58.),
        'motherboard_esp_socket':(410.,275.,44.,62.)}
    functions=native_pin_functions(source/'netlist.xml')
    remaining={r:f for r,f in added.items() if r not in fixed}
    for block,rect in regions.items():
        refs=[r for r in remaining if parts[r]['source_block']==block]
        if not refs:continue
        placements.extend(dict(row,region=block) for row in place_cluster(board,refs,added,parts,nodes,rect,{},functions,occupied))
        for r in refs:remaining.pop(r)
        print('Placed '+block+': '+str(len(refs)),flush=True)
    if remaining:raise ValueError('Unplanned new physical regions '+repr(list(remaining)))
    out.mkdir(parents=True);dest=out/'motherboard-populated-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    for origin in (base.parent,source):
        for folder in origin.iterdir():
            if folder.is_dir() and (folder.name.endswith('.pretty') or folder.name.endswith('.3dshapes') or folder.name=='3dmodels'):
                shutil.copytree(folder,out/folder.name,dirs_exist_ok=True)
        if (origin/'fp-lib-table').is_file():shutil.copyfile(origin/'fp-lib-table',out/'fp-lib-table')
    snapshot=out/'source-inputs';snapshot.mkdir()
    for name in ('design.json','netlist.xml','assembly-map.json'):shutil.copyfile(source/name,snapshot/('motherboard-'+name))
    write(out/'placement-ledger.json',placements);write(out/'exact-source-pad-templates.json',templates)
    write(out/'mechanical-reservations.json',[])
    board.BuildConnectivity();pcbnew.SaveBoard(str(dest),board)
    drc_run=subprocess.run([str(CLI),'pcb','drc','--format','json','--output',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
    (out/'drc-command.txt').write_text(drc_run.stdout+drc_run.stderr)
    drc=load(out/'drc.json');fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
    verification=verify_population(fresh,model,nodes,old_tracks,old_pads,old_fps,ledger,templates)
    verification['native_object_retention']=native_retained_objects(base,dest,ledger)
    verification['ok'] &= verification['native_object_retention']['ok']
    verification['source_inputs_unchanged']=all(sha(Path(f))==h for f,h in hashes.items())
    verification['ok'] &= verification['source_inputs_unchanged']
    report=dict(schema_version=1,source_board_sha256=hashes[str(base)],candidate_board_sha256=sha(dest),
        source_inputs_sha256=hashes,exact_footprint_inputs_sha256=footprint_inputs,population=verification,
        added_footprints=len(added),retained_footprints=len(retained),watchdog_clear_source_check=clear,
        layers=fresh.GetCopperLayerCount(),thickness_mm=pcbnew.ToMM(fresh.GetDesignSettings().GetBoardThickness()),
        dimensions_mm=[460,340],final_outline=False,mechanical_reservations=[],
        native_drc=dict(exit_code=drc_run.returncode,regular_violations=len(drc['violations']),ignored_checks=drc.get('ignored_checks',[]),
            capped_unconnected_items=len(drc.get('unconnected_items',[]))),
        uncapped_native_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        exact_unrouted_pad_reconciliation=ledger,module_socket_mating_geometry='34mm same rotation compute;22.86mm same rotation ESP',
        RF_mechanical_thermal_qualification=False,local_bypass_and_converter_loop_placement_complete=False,
        final_placement=False,routing_complete=False,manufacturing_ready=False)
    write(out/'report.json',report)
    print(json.dumps(dict(population=verification,native_drc=report['native_drc'],missing_joins=report['uncapped_native_missing_joins'])))
    if not verification['ok']:raise ValueError('Independent population/retention checks failed')

if __name__=='__main__':main()
