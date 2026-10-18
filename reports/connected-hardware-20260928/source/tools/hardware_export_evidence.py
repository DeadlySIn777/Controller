"""Bind stored circuit evidence to fresh native KiCad exports of frozen inputs.

Only this project's ten circuit blocks and combined assembly are supported. Inputs
are captured once and copied into a private working mirror; KiCad never receives
the supplied source-root as its working project. This checks circuit evidence,
not PCB layout, physical ratings, or manufacturing readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

BLOCKS = (
    "power_entry", "core_converter", "logic_power", "field_power", "encoder_power",
    "tx_six", "rx_abz", "sbc_power", "power_sequence", "digital_inputs",
    "controller_assembly",
)
EXPECTED_EXPORTS = len(BLOCKS) * 2
DEFAULT_KICAD = Path("C:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
INPUT_SUFFIXES = {".kicad_sch", ".kicad_pro", ".kicad_sym", ".kicad_mod"}
INPUT_NAMES = {"sym-lib-table", "fp-lib-table", "netlist.xml", "erc.json", "assembly-map.json"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def inventory(root: Path) -> dict[str, Path]:
    """Include actual native inputs and every path named by the assembly receipt."""
    paths = {}
    for block in BLOCKS:
        folder = root / "hardware" / block
        required = [folder / (block + ".kicad_sch"), folder / (block + ".kicad_pro"),
                    folder / "sym-lib-table", folder / "netlist.xml", folder / "erc.json"]
        for path in required:
            if not path.is_file():
                raise ValueError("Missing required input: " + str(path))
        for path in folder.rglob("*"):
            if path.is_file() and (path.suffix in INPUT_SUFFIXES or path.name in INPUT_NAMES):
                paths[path.relative_to(root).as_posix()] = path
    manifest = root / "hardware/controller_assembly/assembly-map.json"
    if not manifest.is_file():
        raise ValueError("Missing assembly input receipt")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    declared = data.get("input_sha256")
    if not isinstance(declared, dict) or not declared:
        raise ValueError("Empty or invalid assembly input receipt")
    for name in declared:
        if not isinstance(name, str):
            raise ValueError("Invalid assembly source path")
        path = root / name
        if path.is_absolute() and not path.resolve().is_relative_to(root):
            raise ValueError("Assembly source escapes snapshot: " + name)
        if not path.is_file():
            raise ValueError("Missing declared assembly input: " + name)
        paths[path.relative_to(root).as_posix()] = path
    for name, path in paths.items():
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError("External or linked input is unsupported: " + name)
    return dict(sorted(paths.items()))


def portable_path(text: str) -> str:
    """Remove only the environment prefix, preserving the project-relative path."""
    normalized = text.replace("\\", "/")
    if "/hardware/" in normalized:
        return "${SOURCE_ROOT}/hardware/" + normalized.rsplit("/hardware/", 1)[1]
    # Project library URIs already use ${KIPRJMOD}; preserve them verbatim.
    # Unknown absolute paths remain different rather than hiding an external source.
    return normalized


def reject_erc_exclusions(raw: bytes, name: str) -> None:
    """The comparable ERC report omits exclusions, so prohibit stored waivers."""
    data = json.loads(raw)

    def visit(item, path=()):
        if isinstance(item, dict):
            for key, value in item.items():
                lower = key.lower()
                if value and (lower == "erc_exclusions" or ("erc" in path and "exclusion" in lower)):
                    raise ValueError("Project ERC exclusions are unsupported: " + name)
                visit(value, path + (lower,))
        elif isinstance(item, list):
            for value in item:
                visit(value, path)

    visit(data)


def canonical_netlist(raw: bytes):
    root = ET.fromstring(raw)
    if root.tag != "export":
        raise ValueError("Not a KiCad XML netlist")
    for section in ("components", "libparts", "nets"):
        found = root.find(section)
        if found is None or not len(found):
            raise ValueError("Empty or missing netlist section: " + section)

    def visit(node, path=""):
        path += "/" + node.tag
        if path == "/export/design/date":
            return None  # Export wall-clock time; UUID/tstamps fields are retained.
        text = (node.text or "").strip()
        if path in ("/export/design/source", "/export/libraries/library/uri"):
            text = portable_path(text)
        entries = [v for c in node if (v := visit(c, path)) is not None]
        # XML collection ordering is immaterial; duplicates remain in the list.
        entries.sort(key=lambda x: json.dumps(x, sort_keys=True))
        return [node.tag, sorted(node.attrib.items()), text, entries]

    return visit(root)


def canonical_erc(raw: bytes):
    data = json.loads(raw)
    for field in ("source", "sheets", "ignored_checks", "included_severities", "kicad_version"):
        if field not in data:
            raise ValueError("Missing ERC field: " + field)
    if not isinstance(data["sheets"], list) or not data["sheets"]:
        raise ValueError("ERC has no sheets")
    levels = set(data["included_severities"])
    if not {"error", "warning"} <= levels or levels - {"error", "warning", "exclusion"}:
        raise ValueError("ERC did not include errors and warnings")
    data.pop("date", None)  # Only export time is removed, never UUIDs or issue data.
    data["source"] = portable_path(data["source"])

    def visit(item):
        if isinstance(item, dict):
            return {k: visit(v) for k, v in sorted(item.items())}
        if isinstance(item, list):
            return sorted((visit(v) for v in item), key=lambda v: json.dumps(v, sort_keys=True))
        return item

    return visit(data)


def differences(left, right, path="$", limit=30):
    """Bounded diagnostic differences; equality itself always compares everything."""
    output = []

    def walk(a, b, p):
        if len(output) >= limit or a == b:
            return
        if type(a) is not type(b):
            output.append({"path": p, "stored": a, "fresh": b})
        elif isinstance(a, dict):
            for key in sorted(set(a) | set(b)):
                if key not in a or key not in b:
                    output.append({"path": p + "/" + key, "stored": a.get(key), "fresh": b.get(key)})
                else:
                    walk(a[key], b[key], p + "/" + key)
                if len(output) >= limit:
                    break
        elif isinstance(a, list):
            if len(a) != len(b):
                output.append({"path": p, "stored_length": len(a), "fresh_length": len(b)})
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, p + "/" + str(i))
        else:
            output.append({"path": p, "stored": a, "fresh": b})

    walk(left, right, path)
    return output


def run_command(command, cwd: Path, log: Path):
    started = time.monotonic()
    result = {"argv": [str(x) for x in command], "cwd": str(cwd), "returncode": None}
    try:
        process = subprocess.run(result["argv"], cwd=cwd, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=60)
        result.update(returncode=process.returncode, stdout=process.stdout, stderr=process.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["error"] = str(exc)
    result["elapsed_s"] = time.monotonic() - started
    write_json(log, result)
    return result


def export_evidence(source_root: Path, output_dir: Path, executable: str | None = None):
    source_root = source_root.resolve(strict=True)
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ValueError("Refusing to overwrite existing output directory")
    if output_dir.is_relative_to(source_root):
        raise ValueError("Output directory must be outside the supplied source root")
    output_dir.mkdir(parents=True)
    report = {"schema_version": 1, "checks_pass": False, "manufacturing_ready": False,
              "source_root": str(source_root), "scope": list(BLOCKS),
              "expected_exports": EXPECTED_EXPORTS, "completed_exports": 0,
              "errors": [], "blocks": {}, "input_sha256": {}, "output_sha256": {},
              "helper_sha256": digest(Path(__file__).read_bytes()),
              "normalization": "Collection order, export wall-clock dates and workspace path prefixes only; UUIDs, pin types, component fields, net codes, issue positions and suppression settings retained",
              "not_proved": ["complete controller", "PCB DRC", "physical qualification", "manufacturing release"]}
    captured = {}
    try:
        paths = inventory(source_root)
        work = output_dir / "workspace"
        for name, path in paths.items():
            raw = path.read_bytes()
            if path.suffix == ".kicad_pro":
                reject_erc_exclusions(raw, name)
            captured[name] = raw
            report["input_sha256"][name] = digest(raw)
            dest = work / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
        if inventory(source_root).keys() != paths.keys():
            raise ValueError("Input inventory changed during capture")
        candidate = executable or (str(DEFAULT_KICAD) if DEFAULT_KICAD.is_file() else shutil.which("kicad-cli"))
        if not candidate:
            raise ValueError("Native kicad-cli is unavailable")
        cli = Path(shutil.which(candidate) or candidate).resolve(strict=True)
        report["kicad_cli"] = {"path": str(cli), "sha256": digest(cli.read_bytes())}
        version = run_command([cli, "--version"], work, output_dir / "commands/version.json")
        if version["returncode"] != 0:
            raise ValueError("KiCad version command failed")
        report["kicad_cli"]["version"] = version["stdout"].strip()
        for block in BLOCKS:
            sch = work / "hardware" / block / (block + ".kicad_sch")
            fresh_dir = output_dir / "exports" / block
            fresh_dir.mkdir(parents=True)
            row = {"checks_pass": False, "exports": {}}
            report["blocks"][block] = row
            for kind, filename, canonicalizer in (("netlist", "netlist.xml", canonical_netlist),
                                                   ("erc", "erc.json", canonical_erc)):
                dest = fresh_dir / filename
                name = "hardware/" + block + "/" + filename
                command = ([cli, "sch", "export", "netlist", "--format", "kicadxml"] if kind == "netlist"
                           else [cli, "sch", "erc", "--format", "json", "--severity-error", "--severity-warning"])
                # Stored exports use both legitimate masks. Reproduce that exact
                # mask; never normalize away a changed inspection setting.
                if kind == "erc":
                    stored_erc = canonical_erc(captured[name])
                    if "exclusion" in stored_erc["included_severities"]:
                        command.append("--severity-exclusions")
                command += ["--output", dest, sch]
                run = run_command(command, sch.parent, output_dir / "commands" / (block + "-" + kind + ".json"))
                entry = {"command_exit_code": run["returncode"], "matches_stored": False}
                row["exports"][kind] = entry
                if run["returncode"] != 0 or not dest.is_file() or dest.stat().st_size == 0:
                    report["errors"].append(block + "/" + kind + ": CLI error or missing/empty export")
                    continue
                report["completed_exports"] += 1
                raw = dest.read_bytes()
                entry["fresh_sha256"] = digest(raw)
                entry["stored_sha256"] = digest(captured[name])
                try:
                    stored = canonicalizer(captured[name])
                    fresh = canonicalizer(raw)
                    entry["matches_stored"] = stored == fresh
                    write_json(fresh_dir / (kind + "-stored-canonical.json"), stored)
                    write_json(fresh_dir / (kind + "-fresh-canonical.json"), fresh)
                    if stored != fresh:
                        entry["differences"] = differences(stored, fresh)
                        report["errors"].append(block + "/" + kind + ": fresh export differs from stored evidence")
                    if kind == "erc":
                        violations = [v for s in fresh["sheets"] for v in s["violations"]]
                        entry["violations"] = len(violations)
                        entry["error_count"] = sum(v["severity"] == "error" for v in violations)
                        if entry["error_count"]:
                            report["errors"].append(block + ": native ERC reports errors")
                        if any(v["severity"] not in ("error", "warning") for v in violations):
                            report["errors"].append(block + ": native ERC contains excluded or unknown issue severity")
                except (ValueError, TypeError, KeyError, ET.ParseError) as exc:
                    report["errors"].append(block + "/" + kind + ": invalid export: " + str(exc))
            row["checks_pass"] = all(e["matches_stored"] for e in row["exports"].values()) and len(row["exports"]) == 2
        after = inventory(source_root)
        if after.keys() != paths.keys():
            report["errors"].append("Source inventory changed during exports")
        for name, original in captured.items():
            path = source_root / name
            if not path.is_file() or path.read_bytes() != original:
                report["errors"].append("Supplied source changed during exports: " + name)
            if (work / name).read_bytes() != original:
                report["errors"].append("Native export mutated a captured input: " + name)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report["errors"].append(str(exc))
    if report["completed_exports"] != EXPECTED_EXPORTS:
        report["errors"].append("Expected exactly22 completed native exports")
    report["checks_pass"] = (not report["errors"] and len(report["blocks"]) == len(BLOCKS)
                             and all(x["checks_pass"] for x in report["blocks"].values()))
    for folder in (output_dir / "commands", output_dir / "exports"):
        for path in sorted(folder.rglob("*")) if folder.exists() else []:
            if path.is_file():
                report["output_sha256"][path.relative_to(output_dir).as_posix()] = digest(path.read_bytes())
    write_json(output_dir / "summary.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--kicad-cli", help="Optional explicit native KiCad executable")
    args = parser.parse_args()
    try:
        result = export_evidence(args.source_root, args.output_dir, args.kicad_cli)
    except (OSError, ValueError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps({"checks_pass": result["checks_pass"], "expected_exports": EXPECTED_EXPORTS,
                      "completed_exports": result["completed_exports"], "errors": result["errors"],
                      "summary": str(args.output_dir.resolve() / "summary.json")}, indent=2))
    return 0 if result["checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
