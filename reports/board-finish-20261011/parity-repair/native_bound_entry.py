"""Use the unchanged parity tool with an explicit frozen PCB project context."""
import importlib.util
import json
from pathlib import Path
import sys

import pcbnew


def main(argv):
    tool_path, argv = Path(argv[0]), argv[1:]
    board_path = Path(argv[0]).resolve()
    project_path = board_path.with_suffix(".kicad_pro")
    if not project_path.is_file():
        raise ValueError("Matching frozen project file is required")
    manager = pcbnew.GetSettingsManager()
    if manager is None or not manager.LoadProject(str(project_path)):
        raise ValueError("Native settings manager could not load frozen project")
    project = manager.GetProject(str(project_path))
    if project is None:
        raise ValueError("Native project handle is unavailable")
    spec = importlib.util.spec_from_file_location("unchanged_frozen_parity", tool_path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    raw_load = pcbnew.LoadBoard
    binding = {"project": str(project_path), "explicit_settings_manager_load": True,
               "explicit_board_set_project": False, "settings_save_requested": False}

    def bound_load(path, *args):
        if Path(path).resolve() != board_path:
            raise ValueError("Parity tool requested another board")
        board = raw_load(path, *args)
        board.SetProject(project)
        if board.GetProject() is None:
            raise ValueError("Board project binding failed")
        binding["explicit_board_set_project"] = True
        return board

    try:
        pcbnew.LoadBoard = bound_load
        code = tool.main(argv)
        output_path = Path(argv[-1])
        result = json.loads(output_path.read_text(encoding="utf-8"))
        result["project_settings_binding"] = binding
        output_path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        return code
    finally:
        pcbnew.LoadBoard = raw_load
        manager.UnloadProject(project, False)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
