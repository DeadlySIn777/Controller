"""Native exact-candidate parity and actual added-via annuli; no Fill/DRC/Save."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import pcbnew

def main(argv):
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
        output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
        return 0
    finally:
        pcbnew.LoadBoard=original_load
        for board in captured:board.ClearProject()
        manager.UnloadProject(project,False)

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
