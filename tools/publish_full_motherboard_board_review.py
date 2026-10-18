"""Prepare or publish a freshly verified full-source motherboard CAD revision.

Native geometry/connectivity are rechecked on exact frozen files. Placement may
change with source evolution; retained copper changes require an exact UUID
ledger. No fabrication or physical qualification is implied. Preparation is the
default; --publish is required to update the side-panel manifest.
"""
from __future__ import annotations
import argparse,json,re,shutil,sys
from pathlib import Path
import pcbnew as p
from publish_motherboard_board_review import ROOT,REVIEW,CLI,sha,read,write,run,component
from hardware_route_logic_return import identity

def verify_adoption(adoption,source):
    if adoption.get('native_ERC_errors')!=0 or adoption.get('ignored_checks')!=0:
        raise ValueError('Electrical source has unresolved ERC errors or ignored checks')
    independent=[adoption[k] for k in ('independent_source_validation','independent_validation_pass') if k in adoption]
    if not independent or not all(v is True for v in independent):
        raise ValueError('Independent source validation is missing')
    if adoption.get('focused_tests_passed',0)<=0 or ('focused_tests_run' in adoption and adoption['focused_tests_run']!=adoption['focused_tests_passed']):
        raise ValueError('Electrical source focused tests did not pass')
    hashes=adoption['hashes']
    for name,h in hashes.items():
        f=source/name
        if not f.is_file() or sha(f)!=h:raise ValueError('Frozen electrical source changed: '+name)
    for required in ['design.json','netlist.xml','assembly-map.json']:
        if required not in hashes:raise ValueError('Adoption lacks actual source '+required)
    model=read(source/'design.json')
    if len(model['components'])!=adoption['physical_parts']:
        raise ValueError('Exclusive physical source count disagrees with adoption')
    return model

def copper_delta(base,candidate,ledger):
    old={t.m_Uuid.AsString():identity(t)for t in base.GetTracks()}
    now={t.m_Uuid.AsString():identity(t)for t in candidate.GetTracks()}
    changed={uid for uid,obj in old.items()if now.get(uid)!=obj}
    allowed=ledger.get('changes',[]) if ledger else []
    records={v['uuid']:v for v in allowed}
    if len(records)!=len(allowed)or set(records)!=changed:
        raise ValueError('Retained copper changes require an exact no-extra/no-missing UUID ledger')
    for uid,r in records.items():
        if not r.get('reason') or r.get('old_identity')!=json.loads(json.dumps(old[uid])) or r.get('new_identity')!=json.loads(json.dumps(now.get(uid))):
            raise ValueError('Changed copper identity or reason not reviewed: '+uid)
    return {'retained_previous_items':len(old),'unchanged_previous_items':len(old)-len(changed),
            'explicit_changed_previous_items':len(changed),'additional_items':len(set(now)-set(old)),
            'exact_changed_ledger':allowed}

def edges(board):
    result=[]
    for d in board.Drawings():
        if not isinstance(d,p.PCB_SHAPE)or d.GetLayer()!=p.Edge_Cuts:continue
        xy=lambda v:[round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
        if d.GetShape()==p.SHAPE_T_SEGMENT:result.append({'kind':'line','start':xy(d.GetStart()),'end':xy(d.GetEnd())})
        elif d.GetShape()==p.SHAPE_T_ARC:result.append({'kind':'arc','start':xy(d.GetStart()),'mid':xy(d.GetArcMid()),'end':xy(d.GetEnd())})
        else:raise ValueError('Unsupported actual Edge.Cuts shape; do not replace it with a rectangle')
    if not result:raise ValueError('Actual native outline absent')
    return result

def library_land(footprint):
    """Exact pad pieces, independent of board net assignment or file formatting."""
    return sorted([(v.GetNumber(),tuple(v.GetPosition()),tuple(v.GetSize()),
                    tuple(v.GetDrillSize()),v.GetDrillShape(),v.GetShape(),
                    tuple(v.GetOffset()),v.GetLayerSet().FmtBin(),v.GetAttribute(),
                    v.GetRoundRectRadiusRatio(),v.GetChamferPositions(),
                    v.GetChamferRectRatio(),v.GetOrientationDegrees())
                   for v in footprint.Pads()],key=repr)

def verify_layout_member(fid,baseline,project,overrides):
    nickname,name=fid.split(':',1)
    original=p.FootprintLoad(str(baseline.parent),name)
    actual=p.FootprintLoad(str(project.parent),name)
    if original is None or actual is None or library_land(original)!=library_land(actual):
        raise ValueError('Layout library changed a physical land or pin: '+fid)
    if sha(project)!=sha(baseline):
        record=overrides.get(fid)
        if not record or record.get('original_sha256')!=sha(baseline) or record.get('project_copy_sha256')!=sha(project) or record.get('identical_land_pass')is not True:
            raise ValueError('Layout library differs without exact reviewed graphics receipt: '+fid)
    return {'FPID':fid,'source_sha256':sha(baseline),'project_sha256':sha(project),
            'physical_land_unchanged':True,'reviewed_graphic_override':sha(project)!=sha(baseline)}

def copy_layout_resources(board_path,source,folder,board,receipt_path):
    """Keep native project's reviewed silk/Fab edits without changing source lands."""
    project=board_path.parent;overrides={}
    if receipt_path:
        receipt=read(receipt_path)
        if receipt.get('native_DRC_regular_violations')!=0 or receipt.get('native_DRC_ignored_checks') or receipt.get('all_native_pad_geometry_pin_nets_piece_counts_and_poses_unchanged')is not True:
            raise ValueError('Layout graphics receipt is not a passing land-preserving review')
        for r in receipt['project_copied_library_overrides']:
            if r['FPID']in overrides:raise ValueError('Duplicate layout override FPID')
            overrides[r['FPID']]=r
        shutil.copyfile(receipt_path,folder/'layout-graphics-review.json')
    stock=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints');checked=[]
    for fid in sorted({str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())for f in board.GetFootprints()}):
        nickname,name=fid.split(':',1);relative=Path(nickname+'.pretty')/(name+'.kicad_mod')
        baseline=source/relative
        if not baseline.is_file():baseline=stock/relative
        if not baseline.is_file():raise ValueError('Actual footprint baseline absent: '+fid)
        actual=project/relative
        if actual.is_file():checked.append(verify_layout_member(fid,baseline,actual,overrides))
        elif fid in overrides:raise ValueError('Reviewed project footprint override is missing: '+fid)
    resources=[project/'fp-lib-table']+[f for directory in project.iterdir()if directory.is_dir()and(directory.suffix=='.pretty'or directory.name=='3dmodels')for f in directory.rglob('*')if f.is_file()]
    if not(project/'fp-lib-table').is_file():raise ValueError('Actual layout footprint lookup table absent')
    frozen={str(f.relative_to(project)):sha(f)for f in resources}
    for f in resources:
        dest=folder/f.relative_to(project);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
        if sha(dest)!=frozen[str(f.relative_to(project))]:raise ValueError('Layout resource copy changed')
    return {'project':str(project),'receipt_sha256':sha(receipt_path)if receipt_path else None,
            'files_sha256':frozen,'used_footprint_land_checks':checked}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board',type=Path,required=True);ap.add_argument('--board-sha256',required=True)
    ap.add_argument('--source-adoption',type=Path,required=True);ap.add_argument('--source-folder',type=Path,required=True)
    ap.add_argument('--base',required=True);ap.add_argument('--revision',required=True)
    ap.add_argument('--copper-changes',type=Path);ap.add_argument('--output',type=Path)
    ap.add_argument('--layout-library-receipt',type=Path)
    ap.add_argument('--publish',action='store_true');a=ap.parse_args()
    if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v)for v in [a.base,a.revision]):raise ValueError('Unsafe revision ID')
    current=read(REVIEW/'board-view.json')
    if current['current_revision']!=a.base:raise ValueError('Current published revision changed')
    if sha(a.board)!=a.board_sha256:raise ValueError('Root-frozen native board hash changed')
    adoption=read(a.source_adoption);model=verify_adoption(adoption,a.source_folder)
    folder=(REVIEW/'revisions'/a.revision)if a.publish else a.output
    if folder is None:raise ValueError('Preparation requires a report-only --output directory')
    if folder.exists():raise ValueError('Never replace a published or attempted revision')
    folder.mkdir(parents=True);source=folder/'source-inputs';source.mkdir()
    for name,h in adoption['hashes'].items():
        dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.source_folder/name,dest)
        if sha(dest)!=h:raise ValueError('Copied source changed')
    shutil.copyfile(a.source_adoption,folder/'electrical-source-adoption.json')
    dest=folder/'motherboard-native-candidate.kicad_pcb';shutil.copyfile(a.board,dest)
    for suffix in ['.kicad_pro','.kicad_dru']:
        f=a.board.with_suffix(suffix)
        if not f.is_file():raise ValueError('Native manufacturing rule/project file absent '+suffix)
        shutil.copyfile(f,dest.with_suffix(suffix))
    board=p.LoadBoard(str(dest));parts={f.GetReference():f for f in board.GetFootprints()}
    if set(parts)!=set(model['components']):raise ValueError('Native board is not exactly populated from frozen exclusive source')
    layout=copy_layout_resources(a.board,a.source_folder,folder,board,a.layout_library_receipt)
    write(folder/'layout-resource-land-validation.json',layout)
    previous=p.LoadBoard(str(REVIEW/current['boards'][0]['board_file']))
    delta=copper_delta(previous,board,read(a.copper_changes)if a.copper_changes else None)
    write(folder/'previous-copper-delta.json',delta)
    run([str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--output',str(folder/'native-drc.json'),str(dest)],folder/'native-drc.txt')
    drc=read(folder/'native-drc.json')
    if drc.get('violations')or drc.get('ignored_checks'):raise ValueError('Native geometry check failed or ignored checks exist')
    inventory=folder/'publication-connectivity'
    run([sys.executable,str(ROOT/'tools/motion_card_routing_inventory.py'),'--board',str(dest),'--netlist',str(source/'netlist.xml'),'--source-design',str(source/'design.json'),'--out',str(inventory)],folder/'connectivity-command.txt')
    conn=read(inventory/'review.json')
    if not conn['source_net_checks_pass']or not conn['complete_source_population_pass']or conn['orphan_copper_items']:
        raise ValueError('Independent source/connectivity check failed')
    outline=edges(board);points=[pt for v in outline for pt in [v['start'],v['end']]+([v['mid']]if v['kind']=='arc'else [])]
    if min(q[0]for q in points)!=0 or min(q[1]for q in points)!=0:
        raise ValueError('Viewer origin handling must be extended for nonzero native outline origin')
    width=max(q[0]for q in points);height=max(q[1]for q in points)
    tracks=[]
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA):tracks.append({'kind':'via','net':t.GetNetname(),'x':p.ToMM(t.GetPosition().x),'y':p.ToMM(t.GetPosition().y),'diameter_mm':p.ToMM(t.GetWidth(p.F_Cu)),'drill_mm':p.ToMM(t.GetDrillValue()),'layer':board.GetLayerName(t.TopLayer())+'/'+board.GetLayerName(t.BottomLayer())})
        else:tracks.append({'kind':'segment','net':t.GetNetname(),'layer':board.GetLayerName(t.GetLayer()),'x1':p.ToMM(t.GetStart().x),'y1':p.ToMM(t.GetStart().y),'x2':p.ToMM(t.GetEnd().x),'y2':p.ToMM(t.GetEnd().y),'width_mm':p.ToMM(t.GetWidth())})
    image=folder/'motherboard-3d.png'
    run([str(CLI),'pcb','render','--output',str(image),'--width','1600','--height','1000','--background','opaque','--rotate','-25,0,0','--zoom','1.0','--quality','basic',str(dest)],folder/'render-command.txt')
    missing=conn['independent_physical_cluster_missing_joins'];relative='revisions/'+a.revision+'/'
    components=[component(f,model['components'][r],source)for r,f in sorted(parts.items())]
    for c in components:
        fp=parts[c['reference']]
        for pad,record in zip([v for v in fp.Pads()if v.GetNumber()and v.IsOnCopperLayer()],c['pads']):
            record['drill_mm']=p.ToMM(pad.GetDrillSize().x)
    zones=[{'net':z.GetNetname(),'layer':board.GetLayerName(z.GetLayer()),'filled':z.IsFilled(),'filled_area_mm2':z.GetFilledArea()/1e12,'local_clearance_mm':p.ToMM(z.GetLocalClearance())}for z in board.Zones()]
    limits=[f'{missing} independently counted missing copper joins; final full-board routing and power/return planes require completion.',
            'Actual module sockets, field terminals and required circuit regions are populated from the frozen source; this render does not qualify purchased modules or firmware.',
            'Native source reconciliation and ordinary DRC are checked; FPGA vendor fit, target timing, physical20ms fault response, loaded power/thermal, EMC and actual mated enclosure fit remain separate gates.',
            'The460x340mm six-layer outline/stackup remains a prototype candidate until the final manufacturing and assembly rules are reviewed.']
    spec={'id':'motion-card','title':'One motherboard — actual complete source population','source_block':'motherboard',
          'summary':f'{len(parts)} actual source footprints, {len(tracks)} tracks/vias and {len(zones)} filled planes. {missing} copper joins remain.',
          'status':'Partially routed circuit candidate','width_mm':width,'height_mm':height,'thickness_mm':p.ToMM(board.GetDesignSettings().GetBoardThickness()),'copper_layers':board.GetCopperLayerCount(),
          'outline_status':'Actual native outline and RF profile; manufacturing/fit qualification remains open','native_edge_cuts':outline,
          'components':components,'tracks':tracks,'copper_zones':zones,'zones':[],'board_file':relative+dest.name,'image_3d':relative+image.name,
          'open_work':limits,'unresolved':[],'source_hashes':adoption['hashes'],
          'stats':{'footprints':len(parts),'components':len(parts),'source_fitted_footprints':len(parts),'source_footprint_assignments':len(parts),'placement_only_candidates':0,'assembly_fitted_parts':model['assembly_fitted_parts'],
                   'routed_tracks':len(tracks),'routed_segments':sum(v['kind']=='segment'for v in tracks),'routed_vias':sum(v['kind']=='via'for v in tracks),'fitted_pads':conn['fitted_pads'],'copper_zones':len(zones),'filled_copper_zones':sum(v['filled']for v in zones),
                   'reported_unconnected_items':len(drc['unconnected_items']),'uncapped_unconnected_ratsnest_edges':missing,'native_unconnected_report_limit':499},
          'evidence':{'source_backed':True,'native_board':True,'routing':True,'native_geometry_violations':0,'independent_source_population_and_connectivity':True,'drc_pass':False,'physical_measurement':False,'manufacturing_ready':False}}
    doc={'schema_version':1,'current_revision':a.revision,'revision_label':f'{len(parts)}-part motherboard; {missing} missing copper joins','scope':'Actual frozen full-source PCB candidate; manufacturing and prototype qualification unfinished.','boards':[spec],
         'revisions':current['revisions']+[{'id':a.revision,'label':f'{len(parts)}-part actual motherboard','path':relative+'board-view.json'}]}
    write(folder/'board-view.json',doc)
    publication={'base_revision':a.base,'revision':a.revision,'native_pcb_sha256':sha(dest),'source_population':len(parts),'source_adoption_sha256':sha(a.source_adoption),'native_regular_drc_violations':0,'ignored_checks':drc.get('ignored_checks',[]),
                 'uncapped_missing_joins':missing,'reported_unconnected_items':len(drc['unconnected_items']),'actual_edge_cuts':outline,'manufacturing_ready':False,'published':a.publish}
    write(folder/'publication.json',publication)
    if sha(a.board)!=a.board_sha256:raise ValueError('Input board changed during preparation')
    for name,h in layout['files_sha256'].items():
        if sha(a.board.parent/name)!=h:raise ValueError('Input layout resources changed during preparation: '+name)
    verify_adoption(adoption,a.source_folder)
    if read(REVIEW/'board-view.json')['current_revision']!=a.base:raise ValueError('Public base changed during preparation')
    if a.publish:
        temp=REVIEW/'board-view.next.json';write(temp,doc);temp.replace(REVIEW/'board-view.json')
    print(json.dumps(publication))

if __name__=='__main__':main()
