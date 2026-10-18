"""Independently finish the saved r05 In3 proof without invoking KiCad or adopting copper.

Run after run_bridge_proof.py completes. Only final-proof.json and
bridge-final-status.json are written. Existing native evidence stays untouched.
"""
import argparse
import collections
import datetime
import hashlib
import json
import re
from pathlib import Path

from partition_guard import compare

ROOT = Path("Z:/pcb-runs/claude-finish")
HERE = Path(__file__).resolve().parent
BASELINE = ROOT / "integrate/revs/r05-stitch-plane-pads-1.kicad_pcb"
CANDIDATE = ROOT / "agent-work/test-bridges3/applied.kicad_pcb"
BEFORE = ROOT / "integrate/measure/r05-stitch-plane-pads-1"
PINS = {"before": "594a1091d3a0eade7bff5d4fb83418f10640004afd36119faab92a3886f9e6c2",
        "after": "c28f6c9410cbf0b9bee8f7f1931ad78cffe30a03b401aeb102dc91c35650724e"}
GENERATOR_PIN = "2e16d3b8f0ca672b6bf201378302cc91628b5e2b4c395cbfbda8030da8dffdda"
TOOL_NAMES = {"step_measure.sh", "step_summary.py", "net_partitions.py", "heavyt.sh",
              "corridor_router_in3sv3.py"}
PROJECT_NAMES = {"board.kicad_pro", "board.kicad_dru", "sch.net", "fp-lib-table"}
FLAGS = "--refill-zones --severity-all --all-track-errors --schematic-parity"


class InvalidEvidence(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(path):
    return str(Path(path).resolve()).replace("\\", "/").casefold()


class ReadSet:
    """Bind each observation to bytes; reject concurrent changes at final evaluation."""
    def __init__(self):
        self.hashes = {}

    def read(self, path):
        path = Path(path)
        data = path.read_bytes()
        value = digest(data)
        key = str(path.resolve())
        require(key not in self.hashes or self.hashes[key] == value,
                f"evidence changed while reading: {path}")
        self.hashes[key] = value
        return data

    def json(self, path):
        return json.loads(self.read(path).decode("utf-8"))

    def verify(self):
        for path, expected in self.hashes.items():
            require(digest(Path(path).read_bytes()) == expected,
                    f"evidence changed during final check: {path}")


def manifest(data):
    result = {}
    for line in data.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        require(match is not None, "invalid sha256 manifest line")
        value, path = match.groups()
        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        role = "board.kicad_pcb" if name.endswith(".kicad_pcb") else name
        require(role not in result, f"duplicate manifest role: {role}")
        result[role] = value
    require(set(result) == PROJECT_NAMES | {"board.kicad_pcb"},
            "manifest must bind board, project, rules, schematic and footprint table")
    return result


def tree_files(directory, reads):
    directory = Path(directory)
    require(directory.is_dir(), f"missing footprint library: {directory}")
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            require(not path.is_symlink(), f"symlink footprint resource: {path}")
            files[path.relative_to(directory).as_posix()] = digest(reads.read(path))
    require(bool(files), f"empty footprint library: {directory}")
    return files


def library_inventory(copy_dir, reads):
    """Compare local copies and every effective library URI, including shared sources."""
    copy_dir = Path(copy_dir).resolve()
    result = {"local": {}, "effective": {}}
    for directory in sorted(copy_dir.glob("*.pretty")):
        result["local"][directory.name] = tree_files(directory, reads)
    table = reads.read(copy_dir / "fp-lib-table").decode("utf-8")
    uris = re.findall(r'\(uri "((?:\\.|[^"\\])*)"\)', table)
    require(bool(uris), "footprint table has no library URIs")
    for uri in uris:
        require(uri not in result["effective"], f"duplicate footprint URI: {uri}")
        resolved = uri.replace("${KIPRJMOD}", copy_dir.as_posix())
        require("${" not in resolved, f"unresolved footprint URI: {uri}")
        path = Path(resolved)
        if not path.is_absolute():
            path = copy_dir / path
        result["effective"][uri] = tree_files(path, reads)
    return result


def footprint_fingerprint(board):
    """Exact native footprint bytes protect UUIDs, duplicate-pad order, nets and poses.

    KiCad's saved board indentation places each complete footprint on one top-level
    expression. A strict byte comparison deliberately rejects any footprint edit.
    """
    blocks = re.findall(rb"(?ms)^\t\(footprint\b.*?^\t\)\r?$", board)
    require(bool(blocks), "no native serialized footprint expressions found")
    identities = []
    for block in blocks:
        uuid = re.search(rb'(?m)^\t\t\(uuid "([^"]+)"\)', block)
        require(uuid is not None, "footprint has no UUID")
        identities.append(uuid.group(1).decode("ascii"))
    require(len(set(identities)) == len(identities), "duplicate footprint UUID")
    return {"count": len(blocks), "digest": digest("\n".join(sorted(digest(b) for b in blocks)).encode())}


def check_summary(raw, partitions, summary, board_hash):
    require(isinstance(raw, dict), "raw DRC report must be an object")
    require(raw.get("ignored_checks") == [], "DRC contains ignored or omitted check inventory")
    require(set(raw.get("included_severities", [])) == {"error", "warning", "exclusion"},
            "raw DRC does not include all severities")
    require(raw.get("source") == "board.kicad_pcb", "unexpected DRC source board")
    require(raw.get("schematic_parity") == [], "native schematic parity violations remain")
    for key in ("tracks", "vias"):
        require(type(partitions.get(key)) is int and partitions[key] >= 0,
                f"invalid native item count: {key}")
    for key in ("violations", "unconnected_items"):
        require(isinstance(raw.get(key), list), f"missing native DRC {key}")
    categories = collections.Counter()
    for violation in raw["violations"]:
        require(isinstance(violation, dict) and isinstance(violation.get("type"), str)
                and violation["type"] and violation.get("severity") in {"error", "warning", "exclusion"},
                "invalid raw DRC category or severity")
        categories[f"{violation['type']} [{violation['severity']}]"] += 1
    errors = sum(n for key, n in categories.items() if key.endswith("[error]"))
    warnings = sum(n for key, n in categories.items() if key.endswith("[warning]"))
    capped = sorted(key for key, n in categories.items() if n in (199, 200, 499, 500))
    expected = {"board_sha256": board_hash, "kicad": raw.get("kicad_version"), "drc_flags": FLAGS,
                "drc_by_category": dict(categories), "drc_errors": errors, "drc_warnings": warnings,
                "drc_violations_total_excluding_unconnected": errors + warnings,
                "unconnected_items_in_drc_report_capped": len(raw["unconnected_items"]),
                "unconnected_api_uncapped": partitions["api_unconnected_count"],
                "missing_pad_joins": partitions["pad_island_joins"], "schematic_parity_items": 0,
                "tracks": partitions["tracks"], "vias": partitions["vias"]}
    for key, value in expected.items():
        require(type(summary.get(key)) is type(value) and summary[key] == value,
                f"summary disagrees with raw evidence: {key}")
    require(sorted(summary.get("possibly_capped_categories", [])) == capped,
            "summary truncation markers disagree with raw DRC")
    require(isinstance(raw.get("kicad_version"), str) and raw["kicad_version"], "missing KiCad version")
    return {"errors": errors, "warnings": warnings, "categories": dict(categories),
            "possibly_capped_categories": capped, "kicad": raw["kicad_version"]}


def evaluate(out, baseline_measure, before_board, after_board, *, pins=None,
             tool_root=None, generator_pin=GENERATOR_PIN, require_finished=True):
    """Pure read-only evaluation; injectable paths permit cheap host fixture tests."""
    out, baseline_measure = Path(out), Path(baseline_measure)
    pins = PINS if pins is None else pins
    tool_root = ROOT / "tools" if tool_root is None else Path(tool_root)
    reads = ReadSet()
    if require_finished:
        status = reads.json(out.parent / "bridge-status.json")
        require(status.get("phase") == "COMPLETE" and status.get("adoption") is False,
                "native runner has not completed; do not finalize an active or failed run")
    inputs = reads.json(out / "inputs.json")
    require(inputs.get("slot") == "test-kicad (one)" and inputs.get("new_gpu_jobs") == 0,
            "native run slot/scope record differs from the reviewed proof")
    boards = inputs.get("boards", {})
    require(isinstance(boards, dict), "invalid pinned board inventory")
    observed_boards = {canonical(path): value for path, value in boards.items()}
    wanted_boards = {canonical(before_board): pins["before"], canonical(after_board): pins["after"]}
    require(observed_boards == wanted_boards, "input manifest board identities differ from pinned proof")
    native_boards = {}
    for role, path in (("before", before_board), ("after", after_board)):
        native_boards[role] = reads.read(path)
        require(digest(native_boards[role]) == pins[role], f"pinned {role} board changed")
    footprints = {role: footprint_fingerprint(data) for role, data in native_boards.items()}
    require(footprints["before"] == footprints["after"],
            "footprint/pad UUID, net, geometry or ordering changed between proof boards")
    sources = inputs.get("tools")
    require(isinstance(sources, dict) and len(sources) == len(TOOL_NAMES), "missing frozen source inventory")
    tools = {}
    for name in sorted(TOOL_NAMES):
        path = tool_root / name
        matches = [(p, h) for p, h in sources.items() if canonical(p) == canonical(path)]
        require(len(matches) == 1, f"missing exact source path: {path}")
        expected = matches[0][1]
        require(re.fullmatch(r"[0-9a-f]{64}", expected) is not None, "invalid frozen tool digest")
        require(digest(reads.read(path)) == expected and digest(reads.read(out / name)) == expected,
                f"tool differs from frozen source: {name}")
        tools[name] = expected
    require(tools["corridor_router_in3sv3.py"] == generator_pin, "unexpected In3 router version")
    b = reads.json(out / "baseline-partitions.json")
    a = reads.json(out / "partitions.json")
    require(reads.read(out / "baseline-partitions.json") == reads.read(baseline_measure / "partitions.json"),
            "baseline partition snapshot differs from original measurement")
    require(reads.read(out / "baseline-summary.json") == reads.read(baseline_measure / "summary.json"),
            "baseline summary snapshot differs from original measurement")
    require(reads.read(out / "baseline-sha256.txt") == reads.read(baseline_measure / "sha256.txt"),
            "baseline project manifest snapshot differs from original measurement")
    require(b.get("sha256") == pins["before"] and a.get("sha256") == pins["after"],
            "partition receipts are stale for pinned boards")
    guard = compare(b, a)
    manifests = {"before": manifest(reads.read(out / "baseline-sha256.txt")),
                 "after": manifest(reads.read(out / "sha256.txt"))}
    for role, copy_dir in (("before", baseline_measure / "copy"), ("after", out / "copy")):
        require(manifests[role]["board.kicad_pcb"] == pins[role], "project manifest board hash mismatch")
        for name in PROJECT_NAMES | {"board.kicad_pcb"}:
            require(digest(reads.read(copy_dir / name)) == manifests[role][name],
                    f"{role} measured file differs from native manifest: {name}")
    for name in PROJECT_NAMES:
        require(manifests["before"][name] == manifests["after"][name],
                f"native project/rules/resources differ between boards: {name}")
    libs_before = library_inventory(baseline_measure / "copy", reads)
    libs_after = library_inventory(out / "copy", reads)
    require(libs_before == libs_after, "effective footprint library inventories differ")
    bs = reads.json(out / "baseline-summary.json")
    ass = reads.json(out / "summary.json")
    bdrc = check_summary(reads.json(baseline_measure / "drc.json"), b, bs, pins["before"])
    adrc = check_summary(reads.json(out / "drc.json"), a, ass, pins["after"])
    require(bdrc["kicad"] == adrc["kicad"], "native KiCad versions differ")
    start = (out / "inputs.json").stat().st_mtime_ns
    for name in ("sha256.txt", "partitions.json", "drc.json", "summary.json"):
        require((out / name).stat().st_mtime_ns >= start, f"native receipt predates this run: {name}")
    require((out / "summary.json").stat().st_mtime_ns >= (out / "drc.json").stat().st_mtime_ns,
            "native summary predates raw DRC")
    new_errors = {k: n - bdrc["categories"].get(k, 0) for k, n in adrc["categories"].items()
                  if k.endswith("[error]") and n > bdrc["categories"].get(k, 0)}
    verdict = "PASS" if guard["verdict"] == "PASS" and adrc["errors"] == 0 and not new_errors else "FAIL"
    reads.read(__file__)
    reads.read(HERE / "partition_guard.py")
    reads.verify()
    return {"verdict": verdict, "adopted": False, "source": "r05 In3 bridge candidate only",
            "evidence_class": "host computation: native KiCad DRC and uncapped refilled connectivity",
            "connectivity": guard, "drc": {"before": bdrc, "after": adrc,
                                             "new_error_categories": new_errors, "flags": FLAGS},
            "project_hashes": {name: manifests["after"][name] for name in sorted(PROJECT_NAMES)},
            "footprints": footprints["after"], "library_inventory": libs_after,
            "tools": tools, "checker_sources": {str(Path(__file__).resolve()): reads.hashes[str(Path(__file__).resolve())],
                 str(HERE / "partition_guard.py"): reads.hashes[str(HERE / "partition_guard.py")]},
            "observed_file_hashes": reads.hashes,
            "limits": ["Native DRC, connectivity and file comparison only; no copper adoption",
                       "CLI unconnected list is capped; connectivity uses uncapped pad partitions/API",
                       "Potential category truncation markers remain explicit in the DRC inventory",
                       "Local footprint copies match exactly; shared external libraries are hashed at final evaluation, not historically frozen",
                       "The raw DRC format has no board digest; binding uses the isolated fresh run, native copy, source freeze and project manifests",
                       "No electrical, current capacity, thermal, SI, manufacturing or physical proof",
                       "No application to r06, r07 or the live power candidate"]}


def write_atomic(path, value):
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=HERE / "bridge-native")
    args = ap.parse_args()
    require(args.out_dir.resolve() == (HERE / "bridge-native").resolve(), "CLI output must be the reviewed native run")
    try:
        receipt = evaluate(args.out_dir, BEFORE, BASELINE, CANDIDATE)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        receipt = {"verdict": "INVALID", "reason": str(exc), "adopted": False,
                   "evidence_class": "read-only native-evidence audit; incomplete or inconsistent proof"}
    receipt["checked_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_atomic(args.out_dir / "final-proof.json", receipt)
    write_atomic(HERE / "bridge-final-status.json", {"phase": "COMPLETE", "verdict": receipt["verdict"],
                 "updated_utc": receipt["checked_utc"], "adoption": False,
                 "proof": str(args.out_dir / "final-proof.json")})
    print(json.dumps({k: receipt[k] for k in ("verdict", "adopted", "evidence_class")}))
    return {"PASS": 0, "FAIL": 1, "INVALID": 2}[receipt["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
