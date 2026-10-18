"""Read-only context clone for optional explicit native API settings binding."""
import json
from pathlib import Path
import stat

from prepare_parity import EXTERNAL, sha, write


def clone_project(prepared):
    prepared = Path(prepared).resolve()
    clone = prepared / "native-project"
    receipt = prepared / "project-clone.json"
    if receipt.exists():
        result = json.loads(receipt.read_text())
        verify_clone(prepared, result)
        return result
    clone.mkdir(exist_ok=False)
    project = EXTERNAL / "integrate"
    mapping = {prepared / "board.kicad_pcb": clone / "board.kicad_pcb",
               prepared / "source/sch.net": clone / "sch.net",
               prepared / "source/sym-lib-table": clone / "sym-lib-table",
               project / "board.kicad_pro.good": clone / "board.kicad_pro",
               project / "board.kicad_dru": clone / "board.kicad_dru",
               project / "fp-lib-table": clone / "fp-lib-table"}
    for directory in project.glob("*.pretty"):
        for source in directory.rglob("*"):
            if source.is_file():
                if not source.resolve().is_relative_to(directory.resolve()):
                    raise ValueError("Footprint resource escapes its directory")
                mapping[source] = clone / directory.name / source.relative_to(directory)
    before = {str(source): sha(source) for source in mapping}
    snapshots = {}
    for source, dest in mapping.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        digest = sha(dest)
        if digest != before[str(source)]:
            raise ValueError("Context input changed during clone")
        snapshots[dest.relative_to(prepared).as_posix()] = digest
        dest.chmod(stat.S_IREAD)
    after = {str(source): sha(source) for source in mapping}
    if before != after:
        raise ValueError("Context inputs changed during clone")
    result = {"scope": "exact candidate and actual integration settings/resources clone; no native job",
              "originals_before": before, "originals_after": after, "originals_unchanged": before == after,
              "snapshots": snapshots, "board_sha256": sha(clone / "board.kicad_pcb"), "read_only": True}
    write(receipt, result); receipt.chmod(stat.S_IREAD)
    return result


def verify_clone(prepared, result):
    prepared = Path(prepared).resolve()
    for relative, digest in result["snapshots"].items():
        target = (prepared / relative).resolve()
        if not target.is_relative_to(prepared / "native-project") or sha(target) != digest:
            raise ValueError("Project context snapshot changed: " + relative)
    return True
