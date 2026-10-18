"""Freeze one explicitly selected experimental ROOT106 candidate after native proof.

No native job, refill, save, live/adopted edit, or fabrication export is performed.
The native folder is editable; evidence files preserve the accepted starting bytes.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
sys.path.insert(0, str(WORK / "gate-repair"))
from partition_guard import compare
sys.path.insert(0, str(WORK.parent / "routing-resume-20261011"))
from finish_bridge_proof import ReadSet, digest, require, library_inventory, check_summary, PROJECT_NAMES
sys.path.insert(0, str(WORK / "parity-repair"))
from run_native_parity import gate_report
from host_parity import load_parser
from fresh_export import canonical
from symbol_resources import inventory as symbol_inventory

R06_SHA = "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53"
GUARD_SHA = "40f8df302033a4dd2729acf260c75621a5d1636ebc5d18f24699ab8de4c4a61b"
BINDING_AUDIT_SHA = "11d1f30e96e2e465549bb928bcd8d49fab1bae078a17ffeee38f194524f50194"
OFFICIAL_HELPER_SHA = "306aa7dee506e2b593ddad79e3d11ab943bf3c80cdcf25ca75f0e3f8b53d2e35"


def assert_complete(status, proof, board_sha):
    require(status.get("phase") == "COMPLETE" and status.get("verdict") == "PASS",
            "native measurement is incomplete or failed")
    require(proof.get("verdict") == "PASS" and proof.get("candidate_sha256") == board_sha,
            "proof is failed or for a different candidate")
    require(proof.get("adopted") is False and proof.get("manufacturing_ready") is False,
            "proof scope differs from experimental, unadopted candidate")


def assert_identity(inputs, board_sha):
    require(re.fullmatch(r"[0-9a-f]{64}", board_sha) is not None, "invalid requested board SHA")
    require(inputs.get("before_sha256") == R06_SHA and inputs.get("after_sha256") == board_sha,
            "native measurement is not exact requested candidate against repaired r06")


def assert_guard(guard):
    require(guard.get("verdict") == "PASS" and type(guard.get("lost")) is int and guard["lost"] == 0
            and guard.get("api_not_increased") is True and guard.get("partition_identity_check") is True,
            "strict native connectivity/API guard did not pass")


def check_cli_rule_diagnostics(log):
    suspicious = []
    for line in log.splitlines():
        lower = line.casefold()
        if any(token in lower for token in ("error parsing", "parse error", "failed to parse", "syntax error")):
            suspicious.append(line)
            continue
        if not ("rule" in lower or ".kicad_dru" in lower):
            continue
        if re.search(r"(?:no|zero|0)\s+errors?", lower):
            continue
        if re.search(r"\b(?:errors?|failed|failure|invalid|unexpected|unrecognized|syntax|parse)\b", lower):
            suspicious.append(line)
    require(not suspicious, "CLI reports failed or invalid custom-rule loading: " + repr(suspicious))
    return {"status": "NO_RULE_PARSE_FAILURE_DIAGNOSTIC", "log_sha256": digest(log.encode("utf-8")),
            "scope": "log diagnostic check only; full native DRC/raw receipts remain required"}


def assert_binding_receipt(receipt, project_hashes, native_version):
    require(receipt.get("schema_version") == 1 and receipt.get("verdict") == "PASS", "binding audit did not pass")
    state, runtime, effective = receipt["input"], receipt["runtime"], receipt["effective_settings"]
    require(state["board_sha256"] == R06_SHA and state["input_directory_unchanged"] is True,
            "binding probe input identity or unchanged state failed")
    require(state["project_sha256"] == project_hashes["board.kicad_pro"]
            and state["rules_sha256"] == project_hashes["board.kicad_dru"],
            "final measured sibling project/rules differ from binding probe")
    require(runtime["native_build_version"] == runtime["cli_report_version"] == runtime["official_tag"] == native_version == "10.0.4",
            "binding probe, final native version, and official source tag differ")
    require(all(effective[key] is True for key in ("all_observed_groups_equal", "raw_project_rules_match", "raw_project_netclass_values_match"))
            and effective["api_observation_errors"] == [], "effective project observation differs or has API errors")
    init = receipt["rule_initialization"]
    require(all(init[key] is True for key in ("LoadBoard_implicitly_binds_sibling_project", "LoadBoard_source_initializes_sibling_custom_rules",
            "CLI_source_uses_same_LoadBoard_helper", "SetProject_source_preserves_existing_rule_engine", "ZONE_FILLER_source_uses_existing_rule_engine",
            "aggregate_rule_engine_observation_unchanged")), "source-backed rule engine binding requirement failed")
    require(init["rule_init_silent_exception_catch"] is True and init["complete_rule_equivalence_proved"] is False,
            "binding audit must retain the bounded rule-observation limitation")
    require(receipt["refill_required_due_to_observed_binding_difference"] is False,
            "binding difference requires new bound partition proof")


def bind_project_state(args, project_hashes, native_version, reads):
    receipt = json.loads(tracked(reads, args.binding_audit, BINDING_AUDIT_SHA))
    assert_binding_receipt(receipt, project_hashes, native_version)
    for path, expected in receipt["read_set_sha256"].items():
        tracked(reads, path, expected)
    probe_info = receipt["probe"]
    probe = json.loads(tracked(reads, probe_info["path"], probe_info["sha256"]))
    tracked(reads, probe_info["script_path"], probe_info["script_sha256"])
    tracked(reads, receipt["checker_path"], receipt["checker_sha256"])
    spec = importlib.util.spec_from_file_location("bound_project_host_checks", receipt["checker_path"])
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    raw_project = json.loads(reads.read(args.measure / "copy/board.kicad_pro"))
    require(checker.validate_probe(probe, raw_project) == receipt["effective_settings"],
            "raw native binding probe differs from strict effective-settings receipt")
    board = Path(receipt["input"]["board_path"]).resolve()
    require(board.with_suffix(".kicad_pro") == Path(receipt["input"]["project_path"]).resolve()
            and board.with_suffix(".kicad_dru") == Path(receipt["input"]["rules_path"]).resolve(),
            "probed project and rules do not use board's exact sibling stem")
    sources = receipt["official_sources"]
    require({Path(s["path"]).name for s in sources} == {"pcbnew_scripting_helpers.cpp", "board.cpp", "pcbnew_jobs_handler.cpp", "zone_filler.cpp", "board_design_settings.cpp"},
            "official source inventory incomplete")
    for record in sources:
        require(record["tag"] == "10.0.4" and record["url"].startswith("https://gitlab.com/kicad/code/kicad/-/raw/10.0.4/"),
                "official source provenance differs")
        raw = tracked(reads, record["path"], record["sha256"])
        require(len(raw) == record["bytes"], "official source size differs")
        if Path(record["path"]).name == "pcbnew_scripting_helpers.cpp":
            require(record["sha256"] == OFFICIAL_HELPER_SHA, "official LoadBoard helper pin differs")
    for path, expected in receipt["runtime"]["installed_file_hashes"].items():
        tracked(reads, path, expected)
    for name in ("board.kicad_pro", "board.kicad_dru"):
        tracked(reads, args.measure / "copy" / name, project_hashes[name])
    return {"status": "PASS_OBSERVED_BINDING_AND_SETTINGS_EQUIVALENCE", "audit_path": str(args.binding_audit.resolve()),
            "audit_sha256": BINDING_AUDIT_SHA, "official_helper_sha256": OFFICIAL_HELPER_SHA,
            "native_build_version": native_version, "effective_settings": receipt["effective_settings"],
            "complete_rule_equivalence_proved": False,
            "limits": receipt["limits"], "raw_receipt": receipt}


def bind_export(receipt, saved_sha, fresh_sha, saved, fresh):
    require(receipt.get("verdict") == "PASS" and receipt.get("native_exit_code") == 0
            and receipt.get("frozen_source_inputs_unchanged") is True, "fresh export receipt did not pass")
    require(receipt.get("saved_export_sha256") == saved_sha and receipt.get("fresh_export_sha256") == fresh_sha,
            "fresh export hashes do not match exact files")
    sections = {k: saved[k] != fresh[k] for k in saved}
    require(not any(sections.values()) and receipt.get("semantic_difference_sections") == sections,
            "fresh source export differs semantically")
    return sections


def tracked(reads, path, expected):
    require(re.fullmatch(r"[0-9a-f]{64}", expected or "") is not None,
            "invalid pinned input hash")
    data = reads.read(path)
    require(digest(data) == expected, "changed pinned input: " + str(path))
    return data


def frozen_inputs(out, reads):
    inputs = reads.json(out / "inputs.json")
    require(inputs.get("host_parity") == "PASS" and inputs.get("source_component_identity") == "PASS",
            "source portable precheck failed")
    for relative, expected in inputs["snapshots"].items():
        path = (out / relative).resolve()
        require(path.is_relative_to(out) and path != out, "unsafe snapshot path")
        tracked(reads, path, expected)
    return inputs


def evaluate(args):
    reads = ReadSet()
    tracked(reads, WORK / "gate-repair/partition_guard.py", GUARD_SHA)
    tracked(reads, args.board, args.sha256)
    measure, parity, exported = args.measure.resolve(), args.parity.resolve(), args.source_export.resolve()
    inputs, proof = reads.json(measure / "inputs.json"), reads.json(measure / "proof.json")
    assert_identity(inputs, args.sha256)
    assert_complete(reads.json(measure / "status.json"), proof, args.sha256)
    for path, expected in proof["observed_file_hashes"].items():
        tracked(reads, path, expected)
    if "inputs_sha256" in proof:
        tracked(reads, measure / "inputs.json", proof["inputs_sha256"])
    for role, identity in proof.get("native_binaries", {}).items():
        tracked(reads, identity["path"], identity["sha256"])
    for path, expected in inputs["construction_file_hashes"].items():
        tracked(reads, path, expected)
    before, after = reads.json(measure / "baseline-partitions.json"), reads.json(measure / "partitions.json")
    require(before["sha256"] == R06_SHA and after["sha256"] == args.sha256, "stale native partitions")
    tracked(reads, inputs["before_board"], R06_SHA)
    tracked(reads, measure / "copy/board.kicad_pcb", args.sha256)
    guard = compare(before, after)
    assert_guard(guard)
    require(proof["connectivity"] == guard, "proof and independently computed guard disagree")
    raw, summary = reads.json(measure / "drc.json"), reads.json(measure / "summary.json")
    drc = check_summary(raw, after, summary, args.sha256)
    require(drc["errors"] == 0 and drc == proof["drc"]["after"], "raw DRC contains errors or stale proof")
    project_binding = bind_project_state(args, proof["project_hashes"], drc["kicad"], reads)
    libraries = library_inventory(measure / "copy", reads)
    require(libraries == inputs["library_inventory_at_start"], "effective footprint resources changed")
    for name in PROJECT_NAMES:
        tracked(reads, measure / "copy" / name, proof["project_hashes"][name])
    pinputs = frozen_inputs(parity, reads)
    require(pinputs["board_sha256"] == args.sha256, "API parity is for another candidate")
    preceipt, report = reads.json(parity / "native-receipt.json"), reads.json(parity / "native-parity.json")
    require(preceipt.get("verdict") == "PASS" and preceipt.get("board_sha256") == args.sha256
            and preceipt.get("native_tool_exit_code") == 0
            and preceipt.get("native_report_sha256") == digest(reads.read(parity / "native-parity.json")),
            "API parity receipt did not pass or report changed")
    require(preceipt.get("frozen_inputs_verified_after") is True
            and preceipt.get("project_clone_verified_after") is True
            and report.get("project_settings_binding", {}).get("explicit_board_set_project") is True,
            "API project binding/frozen inputs are unconfirmed")
    native = gate_report(report, pinputs, reads.json(parity / "host-parity.json"))
    require(native["summary"] == preceipt["summary"], "API receipt summary disagrees with raw report")
    clone = reads.json(parity / "project-clone.json")
    for relative, expected in clone["snapshots"].items():
        path = (parity / relative).resolve()
        require(path.is_relative_to(parity / "native-project"), "unsafe API clone path")
        tracked(reads, path, expected)
    require(digest(reads.read(measure / "copy/sch.net")) == pinputs["netlist_sha256"],
            "measured/API source netlists differ")
    export_prepared = exported.parent
    einputs = frozen_inputs(export_prepared, reads)
    require(einputs["netlist_sha256"] == pinputs["netlist_sha256"], "fresh export belongs to another source export")
    source_roles = {name: value for name, value in pinputs["snapshots"].items()
                    if name.startswith("source/")}
    require(source_roles == {name: value for name, value in einputs["snapshots"].items() if name.startswith("source/")},
            "fresh export and candidate parity source hierarchy differ")
    require(len([name for name in source_roles if name.endswith(".kicad_sch")]) == 27,
            "expected exact 27-file motherboard source hierarchy")
    export_receipt = reads.json(exported / "receipt.json")
    fresh = reads.read(exported / "fresh.net")
    parser_path = parity / "tools/netlist_parity.py"
    parser = load_parser(parser_path)
    saved_semantic = canonical(parser["read_netlist"](parity / "source/sch.net"))
    fresh_semantic = canonical(parser["read_netlist"](exported / "fresh.net"))
    bind_export(export_receipt, pinputs["netlist_sha256"], digest(fresh), saved_semantic, fresh_semantic)
    reads.read(exported / "invocation.json")
    reads.read(exported / "export.log")
    symbols = symbol_inventory(parity / "source", args.symbol_library_root.resolve(), parser_path, reads)
    log_bytes = reads.read(measure / "drc.log")
    log = log_bytes.decode("utf-8", errors="replace")
    cli_rule_diagnostics = check_cli_rule_diagnostics(log)
    cli_rule_diagnostics["log_sha256"] = digest(log_bytes)
    cli_parity = "NOT_EXECUTED" if ("Failed to fetch schematic netlist" in log or
                    "Schematic parity tests require" in log) else "UNCONFIRMED; no skipped-check diagnostic found"
    opens = {
        "routing": {"status": "OPEN", "pad_island_joins": after["pad_island_joins"],
                    "api_unconnected_count": after["api_unconnected_count"],
                    "drc_unconnected_items_reported_capped": len(raw["unconnected_items"])},
        "cli_schematic_parity": {"status": cli_parity, "separate_API_and_fresh_export": "PASS"},
        "symbol_library_reload": {"status": symbols["verdict"],
                   "definition_mismatches": len(symbols["definition_mismatches"]), "native_reload_validation": "NOT RUN"},
        "erc": {"status": "NOT RERUN", "prior_warnings": 3171},
        "drc_warnings": {"status": "OPEN" if drc["warnings"] else "ZERO", "count": drc["warnings"],
                         "categories": drc["categories"], "possibly_capped_categories": drc["possibly_capped_categories"]},
        "stored_zone_fill": {"status": "STALE_SOURCE_CACHE", "fresh_stored_fill": False,
            "note": "Native proof refills in memory; exact candidate bytes retain source cached fills. Refill/save changes SHA and requires new qualification."},
        "connectivity_project_binding": {"status": project_binding["status"],
            "complete_rule_equivalence_proved": False,
            "note": "Official 10.0.4 LoadBoard helper auto-binds exact sibling project/rules. Native observed effective settings equal explicit binding. Silent rule-init catch limits remain; exact final CLI raw DRC and no rule-parse failure are separately required. Every custom-rule condition is not directly observable through this API."},
        "SI": {"status": "OPEN; final candidate not qualified", "historical_fail": 11, "historical_not_routed": 52},
        "PDN": {"status": "OPEN; final candidate not qualified", "historical_fail": 81, "historical_not_routed": 368},
        "returns": {"status": "OPEN; final candidate not qualified", "historical_fail": 3468, "historical_not_routed": 960},
        "isolation": {"status": "OPEN; final candidate not qualified", "historical_fail": 31},
        "field_current_model": {"status": "OPEN", "FA_FAG_cluster_A": [5.036, 5.268], "FA_design_A": 4.58,
                                "FB_FBG_cluster_A": [6.55, 6.61], "FB_design_A": 4.82,
                                "assumption": "cluster maxima summed; no channel or current reduction"},
        "DFM": {"status": "limited source contract only; complete manufacturing qualification OPEN"},
        "electrical_thermal_transient_fault_physical": {"status": "OPEN; not measured"},
        "SBC_ROOT106": {"status": "host planning only; no qualified placement or power route"},
        "CAD30": {"status": "retained separate baseline; not replaced by experimental ROOT106"}
    }
    result = {"verdict": "PASS_EXPERIMENTAL_NATIVE_EVIDENCE", "adopted": False, "manufacturing_ready": False,
       "selection": {"candidate": str(args.board.resolve()), "sha256": args.sha256,
                      "measurement": str(measure), "parity": str(parity), "fresh_export": str(exported)},
       "evidence_class": "host revalidation of saved native refill/DRC/API and actual schematic export receipts",
       "connectivity": guard, "drc": drc, "native_parity": native["summary"],
       "source_export": export_receipt, "project_hashes": proof["project_hashes"],
       "cli_rule_diagnostics": cli_rule_diagnostics,
       "project_binding": project_binding,
       "library_inventory": libraries, "symbol_resources": symbols, "open_matrix": opens,
       "historical_counts_scope": "prior verify receipts cc05353; not final candidate remeasurements",
       "native_bundle_stem": "motherboard", "native_binding_alias": "measured board.* and API board.* files copied byte-exact to motherboard.*; stem alias has no independent native-open test",
       "editable": True, "cached_fill_preserved": True, "checker_sha256": digest(reads.read(__file__))}
    reads.read(HERE / "symbol_resources.py")
    reads.verify()
    result["observed_file_hashes"] = dict(reads.hashes)
    return result, reads


def create_bundle(args, result, reads):
    out = args.out.resolve()
    require(out.is_relative_to(HERE) and out != HERE and not out.exists(),
            "output must be a new isolated final-bundle child")
    require(not any(Path(path).resolve().is_relative_to(out) for path in reads.hashes),
            "output would contain protected input")
    native, evidence = out / "native", out / "evidence"
    mapping = {args.board.resolve(): native / "motherboard.kicad_pcb"}
    for old, new in [("board.kicad_pro", "motherboard.kicad_pro"), ("board.kicad_dru", "motherboard.kicad_dru"),
                     ("fp-lib-table", "fp-lib-table"), ("sch.net", "sch.net")]:
        mapping[args.measure.resolve() / "copy" / old] = native / new
    source = args.parity.resolve() / "source"
    for path in source.glob("*.kicad_sch"):
        mapping[path] = native / path.name
    mapping[source / "sym-lib-table"] = native / "sym-lib-table"
    binding = result["project_binding"]["raw_receipt"]
    binding_paths = [args.binding_audit.resolve(), Path(binding["probe"]["path"]), Path(binding["probe"]["script_path"]),
                     Path(binding["checker_path"])] + [Path(record["path"]) for record in binding["official_sources"]]
    for path in binding_paths:
        mapping[path.resolve()] = evidence / "project-binding" / path.name
    for directory in sorted((args.measure / "copy").glob("*.pretty")):
        for path in directory.rglob("*"):
            if path.is_file():
                mapping[path.resolve()] = native / directory.name / path.relative_to(directory)
    # Absolute effective footprint URIs stay exact; archival copies are not silently rebound.
    for uri in result["library_inventory"]["effective"]:
        if "${KIPRJMOD}" not in uri:
            root = Path(uri)
            for relative in result["library_inventory"]["effective"][uri]:
                mapping[(root / relative).resolve()] = out / "resources/effective-footprints" / root.name / relative
    mismatch_files = {entry["file"].replace(".kicad_sch", ".kicad_sym") for entry in result["symbol_resources"]["definition_mismatches"]}
    for name, record in result["symbol_resources"]["files"].items():
        src = Path(record["path"]).resolve()
        # All real originals are retained, but mismatched resources do not become effective editor libraries.
        mapping[src] = (out / "resources/original-symbols" / name) if name in mismatch_files else native / name
    for group, folder in [("measurement", args.measure), ("parity", args.parity), ("source-export", args.source_export)]:
        for path in folder.resolve().rglob("*"):
            if path.is_file() and (path.suffix in {".json", ".log", ".txt", ".py", ".sh", ".net"}
                                   or path.name in {"fp-lib-table", "sym-lib-table"}):
                dest = evidence / group / path.relative_to(folder.resolve())
                # A source can have multiple archival destinations; these are handled separately.
                if path in mapping:
                    continue
                mapping[path] = dest
    require(len({str(p.resolve()).casefold() for p in mapping.values()}) == len(mapping), "bundle output paths collide")
    for path in mapping:
        reads.read(path)
    reads.verify()
    native.mkdir(parents=True, exist_ok=False)
    manifest = {}
    for src, dst in sorted(mapping.items(), key=lambda pair: str(pair[1])):
        require(not src.is_symlink() and dst.resolve().is_relative_to(out), "unsafe bundle source/destination")
        data = reads.read(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        dst.chmod(stat.S_IREAD | stat.S_IWRITE if dst.is_relative_to(native) else stat.S_IREAD)
        require(digest(dst.read_bytes()) == digest(data), "bundle copy failed")
        manifest[dst.relative_to(out).as_posix()] = {"source": str(src), "sha256": digest(data)}
    # Keep immutable starting bytes as well as the editable, explicitly aliased native folder.
    originals = {"candidate-original.kicad_pcb": args.board.resolve(),
                 "measured-project/board.kicad_pro": args.measure.resolve() / "copy/board.kicad_pro",
                 "measured-project/board.kicad_dru": args.measure.resolve() / "copy/board.kicad_dru",
                 "measured-project/fp-lib-table": args.measure.resolve() / "copy/fp-lib-table",
                 "measured-project/sch.net": args.measure.resolve() / "copy/sch.net",
                 "source-original/sym-lib-table": source / "sym-lib-table"}
    originals.update({"source-original/" + p.name: p for p in source.glob("*.kicad_sch")})
    for relative, src in originals.items():
        dst = evidence / relative
        data = reads.read(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        require(not dst.exists(), "archival original path collides")
        dst.write_bytes(data)
        dst.chmod(stat.S_IREAD)
        require(digest(dst.read_bytes()) == digest(data), "archival original copy failed")
        manifest[dst.relative_to(out).as_posix()] = {"source": str(src), "sha256": digest(data)}
    reads.verify()
    require(digest((native / "motherboard.kicad_pcb").read_bytes()) == args.sha256, "bundle candidate bytes differ")
    result["observed_file_hashes"] = dict(reads.hashes)
    result["bundle"] = {"path": str(out), "candidate": str(native / "motherboard.kicad_pcb"),
                        "manifest": manifest, "native_files_editable": True,
                        "absolute_external_footprint_URIs_retained": [u for u in result["library_inventory"]["effective"] if "${KIPRJMOD}" not in u],
                        "mismatched_symbol_libraries_not_installed": sorted(mismatch_files)}
    text = ("Experimental ROOT106 native candidate; CAD30 remains separate.\n\n"
            f"Board SHA256: {args.sha256}\n"
            f"Native DRC errors: {result['drc']['errors']}; warnings: {result['drc']['warnings']}\n"
            f"Saved partition comparison vs repaired r06: {result['connectivity']['completed']} completed; {result['connectivity']['lost']} lost; observed project binding/settings equivalence PASS\n"
            f"Remaining pad-island joins: {result['open_matrix']['routing']['pad_island_joins']}; uncapped API: {result['open_matrix']['routing']['api_unconnected_count']}\n\n"
            "Open native/motherboard.kicad_pro for editable board and 27-sheet source. The matching motherboard stem is an explicit basename alias, not a native-open qualification.\n"
            "Exact source cached fills were retained and are stale. Refill and save changes the board hash and needs fresh checks.\n"
            "Absolute external footprint URIs remain in the exact fp-lib-table; archival copies are under resources/effective-footprints.\n"
            "Mismatched original symbol libraries are under resources/original-symbols and remain absent at their effective table URIs. Embedded schematic symbols retain the validated circuit.\n"
            "Source/API parity and actual fresh export passed. CLI schematic parity execution is separately recorded.\n"
            "Routing, power/return/isolation/SI, ERC warnings, DFM/manufacturing, stored fill, thermal/fault/physical qualification remain open; see qualification.json open_matrix.\n"
            "No fabrication exports or live/source adoption occurred. Editing this native folder invalidates the recorded initial hashes.\n")
    (out / "README.txt").write_text(text, encoding="utf-8")
    (out / "qualification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name in ("README.txt", "qualification.json"):
        (out / name).chmod(stat.S_IREAD)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("board", "measure", "parity", "source-export", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--binding-audit", type=Path, default=WORK / "power-audit/project-binding-audit.json")
    parser.add_argument("--symbol-library-root", type=Path,
                        default=Path("Z:/pcb-runs/claude-finish/review/schematic/erc_full"))
    args = parser.parse_args()
    result, reads = evaluate(args)
    out = create_bundle(args, result, reads)
    print(json.dumps({"verdict": result["verdict"], "out": str(out), "board_sha256": args.sha256,
                      "completed": result["connectivity"]["completed"], "lost": result["connectivity"]["lost"],
                      "drc_errors": result["drc"]["errors"], "manufacturing_ready": False, "adopted": False}))


if __name__ == "__main__":
    main()
