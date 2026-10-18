"""Native exact-candidate parity and actual added-via annuli; no Fill/DRC/Save."""
import hashlib, importlib.util, json, sys, math
from pathlib import Path
import pcbnew

def main(argv):
    pose_ledger_path=Path(argv.pop(0))
    tool_path, spec_path = Path(argv[0]), Path(argv[1])
    tool_argv = argv[2:]
    board_path = Path(tool_argv[0]).resolve()
    project_path = board_path.with_suffix('.kicad_pro')
    expected = json.loads(spec_path.read_bytes())
    if hashlib.sha256(board_path.read_bytes()).hexdigest() != expected['board_sha256']:
        raise ValueError('Native parity candidate identity differs')
    manager = pcbnew.GetSettingsManager()
    if manager is None or not manager.LoadProject(str(project_path)):
        raise ValueError('Frozen native project load failed')
    project = manager.GetProject(str(project_path))
    if project is None: raise ValueError('Frozen native project unavailable')
    module_spec = importlib.util.spec_from_file_location('frozen_combined_parity', tool_path)
    tool = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(tool)
    original_load = pcbnew.LoadBoard
    captured = []
    def bound_load(path, *args):
        if Path(path).resolve()!=board_path: raise ValueError('Unexpected board load')
        board=original_load(path,*args);board.SetProject(project)
        if board.GetProject() is None:raise ValueError('Explicit board project binding failed')
        captured.append(board);return board
    try:
        pcbnew.LoadBoard=bound_load
        code=tool.main(tool_argv)
        if code or len(captured)!=1:raise ValueError('Native parity tool failed or loaded unexpected boards')
        board=captured[0]
        layer_ids=list(board.GetEnabledLayers().CuStack())
        layer_names=[str(board.GetLayerName(layer)) for layer in layer_ids]
        if layer_names!=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']:raise ValueError('Actual copper stack differs')
        actual={str(item.m_Uuid.AsString()):item for item in board.GetTracks() if isinstance(item,pcbnew.PCB_VIA)}
        diagnostic=[]
        for row in expected['added_vias']:
            item=actual.get(row['uuid'])
            if item is None:
                diagnostic.append({'expected':row,'missing':True});continue
            position=item.GetPosition()
            diagnostic.append({'expected':row,'actual_net_raw':str(item.GetNetname()),'actual_nm':[int(position.x),int(position.y)],'actual_mm':[pcbnew.ToMM(position.x),pcbnew.ToMM(position.y)],'actual_diameter_mm':pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)),'actual_drill_mm':pcbnew.ToMM(item.GetDrillValue()),'actual_flashed_layers':[str(board.GetLayerName(layer)) for layer in layer_ids if item.FlashLayer(layer)]})
        diagnostic_output=Path(tool_argv[-1]+'.actual-vias.json')
        diagnostic_output.write_text(json.dumps({'board_sha256':expected['board_sha256'],'rows':diagnostic,'no_fill_or_save':True},indent=1)+'\n',encoding='utf-8')
        annuli=[]
        for row in expected['added_vias']:
            via=actual.get(row['uuid'])
            if via is None:raise ValueError('Expected added via missing:'+row['uuid'])
            at=via.GetPosition();point=[pcbnew.ToMM(at.x),pcbnew.ToMM(at.y)]
            if str(via.GetNetname()).replace('{slash}','/')!=row['net'] or point!=row['at']:
                raise ValueError('Added native via net/position differs')
            if pcbnew.ToMM(via.GetWidth(pcbnew.F_Cu))!=row['d'] or pcbnew.ToMM(via.GetDrillValue())!=row['drill']:
                raise ValueError('Added native via diameter/drill differs')
            flashed=[str(board.GetLayerName(layer)) for layer in layer_ids if via.FlashLayer(layer)]
            if flashed!=layer_names:raise ValueError('Added ordinary through-via suppresses annuli:'+row['uuid'])
            annuli.append({**row,'actual_flashed_layers':flashed,'actual_via_type':int(via.GetViaType())})
        output=Path(tool_argv[-1]);report=json.loads(output.read_bytes())
        report['project_settings_binding']={'project':str(project_path),'explicit_settings_manager_load':True,'explicit_board_set_project':True,'settings_save_requested':False}
        report['added_via_annuli']={'verdict':'PASS','board_sha256':expected['board_sha256'],'rows':annuli,'no_fill_or_connectivity_rebuild':True}
        pose=json.loads(pose_ledger_path.read_bytes())
        footprints={str(f.GetReference()):f for f in board.GetFootprints()}
        pose_rows=[]
        for row in pose['rows']:
            fp=footprints[row['ref']]
            if str(fp.m_Uuid.AsString())!=row['native_footprint_uuid'] or str(fp.GetPath().AsString())!=row['schematic_path'] or str(fp.GetLayerName())!=row['layer']:raise ValueError('Native field footprint identity/path/side differs:'+row['ref'])
            position=fp.GetPosition();at=[pcbnew.ToMM(position.x),pcbnew.ToMM(position.y)]
            angle=fp.GetOrientationDegrees();planned=row['root_pose_mm_deg']
            if at!=planned[:2] or abs((angle-planned[2]+180)%360-180)>1e-9:raise ValueError('Native field root pose differs:'+row['ref'])
            pads={str(p.m_Uuid.AsString()):p for p in fp.Pads()}
            if set(pads)!={p['pad_uuid'] for p in row['pads']}:raise ValueError('Native field pad inventory differs:'+row['ref'])
            observed=[]
            for expected_pad in row['pads']:
                pad=pads[expected_pad['pad_uuid']];at_pad=pad.GetPosition();point=[pcbnew.ToMM(at_pad.x),pcbnew.ToMM(at_pad.y)]
                delta=math.dist(point,expected_pad['absolute_center_mm'])
                if str(pad.GetNumber())!=expected_pad['pin'] or str(pad.GetNetname())!=expected_pad['raw_net'] or delta>.003000001:raise ValueError('Native field absolute pad identity/net/pose differs:'+row['ref']+'/'+expected_pad['pin'])
                flashed=[str(board.GetLayerName(layer)) for layer in layer_ids if pad.FlashLayer(layer)]
                if set(flashed)!=set(expected_pad['actual_original_clone_native_flashes']):raise ValueError('Native field actual pad annuli differ:'+row['ref']+'/'+expected_pad['pin'])
                observed.append({'uuid':expected_pad['pad_uuid'],'pin':expected_pad['pin'],'net_raw':str(pad.GetNetname()),'actual_nm':[int(at_pad.x),int(at_pad.y)],'actual_mm':point,'host_absolute_center_delta_mm':delta,'actual_flashed_layers':flashed})
            pose_rows.append({'ref':row['ref'],'actual_root_pose_mm_deg':at+[angle],'pads':observed})
        report['source_owned_native_poses']={'verdict':'PASS','rows':pose_rows,'footprints':len(pose_rows),'exact_root_pose_required':True,'absolute_pad_center_planning_model_budget_mm':.003,'actual_pad_raw_nets_UUIDs_numbers_and_flash_masks_exact':True,'no_refill_DRC_or_save':True}
        output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
        return 0
    finally:
        pcbnew.LoadBoard=original_load
        for board in captured:board.ClearProject()
        manager.UnloadProject(project,False)

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
