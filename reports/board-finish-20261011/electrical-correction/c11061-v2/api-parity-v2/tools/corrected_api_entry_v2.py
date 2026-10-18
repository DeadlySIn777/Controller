"""Exactly one explicitly project-bound LoadBoard; no save/fill/DRC/rebuild."""
import importlib.util
import json
from pathlib import Path
import sys
import pcbnew

def main(argv):
    tool_path,board_path,netlist_path,out_path=map(Path,argv)
    board_path=board_path.resolve()
    project_path=board_path.with_suffix(".kicad_pro")
    manager=pcbnew.GetSettingsManager()
    if manager is None or not manager.LoadProject(str(project_path)):
        raise ValueError("explicit corrected project load failed")
    project=manager.GetProject(str(project_path))
    if project is None:
        raise ValueError("corrected project unavailable")
    spec=importlib.util.spec_from_file_location("copied_corrected_parity",tool_path)
    tool=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    raw_load=pcbnew.LoadBoard
    binding={"project":str(project_path),"explicit_settings_manager_load":True,"explicit_board_set_project":False,"load_count":0,"save_requested":False,"refill_requested":False,"DRC_requested":False,"connectivity_rebuild_requested":False}
    correction={}
    def bound_load(path,*args):
        if Path(path).resolve()!=board_path or binding["load_count"]!=0:
            raise ValueError("unexpected board or second board load")
        board=raw_load(path,*args)
        board.SetProject(project)
        if board.GetProject() is None:
            raise ValueError("explicit project non-null binding failed")
        binding["load_count"]+=1
        binding["explicit_board_set_project"]=True
        binding["project_pointer_identity_checked"]=False
        matches=[foot for foot in board.GetFootprints() if foot.GetReference()=="C11061"]
        if len(matches)!=1:
            raise ValueError("corrected cap ref must be unique")
        foot=matches[0]
        correction.update(ref=foot.GetReference(),value=foot.GetValue(),MPN=foot.GetFieldText("MPN"),footprint=foot.GetFPIDAsString(),uuid=foot.m_Uuid.AsString())
        return board
    try:
        pcbnew.LoadBoard=bound_load
        code=tool.main([str(board_path),"--netlist",str(netlist_path.resolve()),"--no-connectivity","--examples","40",str(out_path.resolve())])
        report=json.loads(out_path.read_text(encoding="utf-8"))
        report["project_settings_binding"]=binding
        report["native_corrected_capacitor_fields"]=correction
        report["native_version"]=pcbnew.GetBuildVersion()
        report["native_pcbnew_module"]=str(Path(pcbnew.__file__).resolve())
        out_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        return code
    finally:
        pcbnew.LoadBoard=raw_load
        manager.UnloadProject(project,False)

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
