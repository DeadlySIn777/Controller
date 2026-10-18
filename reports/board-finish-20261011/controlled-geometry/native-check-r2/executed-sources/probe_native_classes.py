"""Read-only LoadBoard check of original versus isolated proposed net classes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "final-bundle/native-open"))
from open_check_shared import inventory,require
from probe_native_open import snapshot as baseline_snapshot
import pcbnew

def nc_values(nc,class_names):
    out={name:str(nc.GetName()) if name=="GetName" else getattr(nc,name)() for name in
         ("GetName","GetPriority","GetClearance","GetTrackWidth","GetViaDiameter","GetViaDrill",
          "GetDiffPairWidth","GetDiffPairGap","GetDiffPairViaGap")}
    # The pointer-vector getter is opaque in the installed SWIG build. This
    # purpose-built native predicate exposes each real constituent by exact name.
    out["constituents"]=[name for name in sorted(class_names) if nc.ContainsNetclassWithName(name)]
    return out

def inspect(path,manager):
    path=path.resolve();pro=path.with_suffix(".kicad_pro")
    before=inventory(path.parent)
    print("NATIVE_CLASS_LOAD "+str(path),flush=True)
    board=pcbnew.LoadBoard(str(path));require(board is not None,"board load failed")
    project=manager.GetProject(str(pro));require(project is not None,"real sibling project absent")
    try:
        snap=baseline_snapshot(board,manager,pro)
        ds=board.GetDesignSettings()
        class_names=[str(name) for name in board.GetAllNetClasses().keys()]
        declared={str(name):nc_values(nc,class_names) for name,nc in board.GetAllNetClasses().items()}
        netnames=sorted(str(name) for name in board.GetNetsByName().keys())
        effective={name:nc_values(ds.m_NetSettings.GetEffectiveNetClass(name),class_names) for name in netnames}
    finally:
        board.ClearProject();unloaded=manager.UnloadProject(project,False);del board
    after=inventory(path.parent)
    return {"board_path":str(path),"project_path":str(pro),"directory_before_sha256":before,
            "directory_after_sha256":after,"directory_unchanged":before==after,
            "project_unloaded_without_save":bool(unloaded),"binding_and_minima":snap,
            "declared_classes":declared,"all_named_net_effective_classes":effective}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--baseline",required=True,type=Path)
    ap.add_argument("--proposal",required=True,type=Path);ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    require(not a.out.exists(),"report already exists")
    require(not a.out.resolve().is_relative_to(a.baseline.resolve().parent) and not a.out.resolve().is_relative_to(a.proposal.resolve().parent),"report aliases input directory")
    manager=pcbnew.GetSettingsManager()
    result={"schema_version":1,"native_version":str(pcbnew.GetBuildVersion()),
            "baseline":inspect(a.baseline,manager),"proposal":inspect(a.proposal,manager),
            "probe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "refill":False,"DRC":False,"Save":False,"GUI":False}
    a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("NATIVE_CLASS_OBSERVATIONS_WRITTEN",flush=True)

if __name__=="__main__":main()
