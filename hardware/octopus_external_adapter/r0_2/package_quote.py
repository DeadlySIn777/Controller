"""Package actual OEA r0.2 files for PCBWay quotation/DFM after final checks.

Run deliberately with KiCad's Python:
  & 'C:/Program Files/KiCad/10.0/bin/python.exe' package_quote.py --build

No source CAD is edited. Existing final directories/ZIPs are never overwritten.
Initial reports must pass, and copied CAD is checked again before real exports.
Any failure leaves only an explicitly named staging directory for diagnosis;
it does not create the final package or ZIP. No upload or order is performed.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import uuid
import zipfile

import pcbnew as p


ROOT = Path(__file__).resolve().parent
DEST = ROOT.parent / "submissions" / "20261006" / "r02-online-quote"
FINAL = DEST / "final-candidate"
ZIP = DEST / "OEA-r0.2-PCBWay-QUOTE-DFM.zip"
CLI = Path("C:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "F.SilkS", "B.SilkS",
          "F.Mask", "B.Mask", "F.Paste", "B.Paste", "Edge.Cuts"]
THT = {"J1", "J2", "J3", "J4", "SW1"}
NATIVE = ["adapter.kicad_pcb", "adapter.kicad_sch", "adapter.kicad_pro",
          "adapter.kicad_dru", "Adapter.kicad_sym", "sym-lib-table", "fp-lib-table"]
DOCS = ["QUOTE_SCOPE.txt", "ASSEMBLY_AND_WIRING.txt", "FUNCTIONAL_TEST.txt"]
DRAWINGS = ["adapter-schematic.pdf", "assembly-review.pdf", "assembly-review.svg", "assembly-review.png"]
EVIDENCE = ["bom-pcb-review.json", "document-consistency-review.json",
            "schematic-connectivity.json", "schematic-visual-review.json",
            "independent-schematic-review.json", "mechanical-review.json",
            "j4-footprint-derivative-review.json"]
ATTRIBUTION = "Adapter.pretty/KICAD-J4-ATTRIBUTION.txt"


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def check_drc(path):
    report = read_json(path)
    need(report.get("source") == "adapter.kicad_pcb", f"Wrong DRC source: {path}")
    for category in ("violations", "unconnected_items", "schematic_parity"):
        need(category in report and report[category] == [], f"DRC {category} is not empty: {path}")
    need(not report.get("ignored_checks"), f"DRC has ignored categories: {path}")
    need(set(report.get("included_severities", [])) == {"error", "warning", "exclusion"},
         f"DRC must include errors, warnings and exclusions: {path}")
    return report


def check_erc(path):
    report = read_json(path)
    need(report.get("source") == "adapter.kicad_sch", f"Wrong ERC source: {path}")
    need(report.get("sheets"), f"ERC has no sheets: {path}")
    need(all(sheet.get("violations") == [] for sheet in report["sheets"]),
         f"ERC has violations or an incomplete sheet report: {path}")
    need(set(report.get("included_severities", [])) == {"error", "warning", "exclusion"},
         f"ERC must include errors, warnings and exclusions: {path}")
    # Ignored categories are recorded verbatim. They are not zero-violation exclusions.
    return report


def check_hash_map(hashes, folder=ROOT):
    for name, expected in hashes.items():
        path = folder / name
        need(path.is_file() and sha(path) == expected, f"Stale review hash: {path}")


def preflight():
    need(not FINAL.exists(), f"Final directory already exists; preserve it: {FINAL}")
    need(not ZIP.exists(), f"ZIP already exists; preserve it: {ZIP}")
    need(CLI.is_file(), f"KiCad CLI missing: {CLI}")
    parts = read_json(ROOT / "parts.json")["parts"]
    custom = sorted({spec["footprint"].split(":", 1)[1] + ".kicad_mod"
                     for spec in parts.values() if spec["footprint"].startswith("Adapter:")})
    need(len(custom) == 6 and all("TPS7A16" not in name for name in custom),
         "Expected only the six currently used custom footprints")
    required = [*NATIVE, *DOCS, *DRAWINGS, *EVIDENCE, "parts.json", "BOM.csv",
                "evidence/final-drc.json", "evidence/final-erc.json", ATTRIBUTION]
    required += ["Adapter.pretty/" + name for name in custom]
    for name in required:
        path = ROOT / name
        need(path.is_file() and path.stat().st_size > 0, f"Required final artifact missing/empty: {path}")
    initial_drc = check_drc(ROOT / "evidence/final-drc.json")
    initial_erc = check_erc(ROOT / "evidence/final-erc.json")
    bom_check = read_json(ROOT / "bom-pcb-review.json")
    need(bom_check["status"].startswith("PASS"), "BOM native review did not pass")
    check_hash_map(bom_check["source_sha256"])
    need(bom_check["bom_sha256"] == sha(ROOT / "BOM.csv"), "BOM changed after native review")
    need(bom_check["parts_per_board"] == 50 and bom_check["bom_lines"] == 32
         and bom_check["mounting_counts"] == {"SMT": 45, "THT": 5}, "BOM count mismatch")
    doc_check = read_json(ROOT / "document-consistency-review.json")
    need(doc_check["status"].startswith("PASS") and all(doc_check["checks"].values()),
         "Document consistency checks did not pass")
    check_hash_map(doc_check["sha256"])
    for name in ("QUOTE_SCOPE.txt", "ASSEMBLY_AND_WIRING.txt"):
        wording = " ".join((ROOT / name).read_text(encoding="utf-8").split()).lower()
        need("purple solder mask, white legend and enig" in wording,
             f"Latest purple solder-mask / white-legend requirement missing: {name}")
    sch_check = read_json(ROOT / "schematic-connectivity.json")
    need(sch_check["status"].startswith("PASS") and sch_check["fitted_parts"] == 50,
         "Native schematic connectivity review missing")
    check_hash_map(sch_check["sha256"])
    visual = read_json(ROOT / "schematic-visual-review.json")
    need(visual["status"].startswith("PASS"), "Schematic visual review missing")
    check_hash_map(visual["sha256"])
    independent = read_json(ROOT / "independent-schematic-review.json")
    need(independent["status"].startswith("PASS"), "Independent schematic source review did not pass")
    check_hash_map(independent["sha256"])
    derivative = read_json(ROOT / "j4-footprint-derivative-review.json")
    need(derivative["reversible_text_comparison_passed"]
         and derivative["pads_fab_courtyard_and_models_unchanged"], "J4 derivative geometry review did not pass")
    need(sha(ROOT / "Adapter.pretty" / derivative["derivative"]) == derivative["derivative_sha256"],
         "J4 derivative footprint changed after review")
    mech = read_json(ROOT / "mechanical-review.json")
    need(mech["board_sha256"] == sha(ROOT / "adapter.kicad_pcb"),
         "Mechanical/assembly drawing review predates final board; regenerate")
    need(mech["header_top_tail_screen"]["overlaps"] == [], "Assembly envelope overlap unresolved")
    need(mech["board_mm"] == [15.24, 38.1], "Mechanical dimensions differ from quote")
    drawing = ROOT / "assembly-review.svg"
    need(mech["board_sha256"][:28] in drawing.read_text(encoding="utf-8"),
         "Assembly SVG does not identify the current native board")
    for name in ("assembly-review.pdf", "assembly-review.png"):
        need((ROOT / name).stat().st_mtime >= drawing.stat().st_mtime - 1,
             f"Rendered assembly drawing predates its SVG: {name}")
    return parts, custom, required, initial_drc, initial_erc


def native_bom_check(board_path, parts, bom_path):
    board = p.LoadBoard(str(board_path))
    footprints = list(board.GetFootprints())
    fps = {fp.GetReference(): fp for fp in footprints}
    need(len(footprints) == len(fps) == 50 and set(fps) == set(parts), "Native footprint set mismatch")
    smt = set()
    for ref, spec in parts.items():
        fp = fps[ref]
        fields = {f.GetName(): f.GetText() for f in fp.GetFields()}
        fid = fp.GetFPID()
        need(fields.get("MPN") == spec["mpn"] and fields.get("Manufacturer") == spec["manufacturer"],
             f"Native MPN/manufacturer mismatch: {ref}")
        need(fp.GetValue() == spec["value"] and
             f"{fid.GetLibNickname()}:{fid.GetLibItemName()}" == spec["footprint"], f"Native value/footprint mismatch: {ref}")
        is_tht = bool(fp.GetAttributes() & p.FP_THROUGH_HOLE)
        is_smt = bool(fp.GetAttributes() & p.FP_SMD)
        need(is_tht == (ref in THT) and is_smt == (ref not in THT), f"Mounting mismatch: {ref}")
        need(not (fp.GetAttributes() & p.FP_DNP), f"Unexpected DNP component: {ref}")
        if is_smt:
            smt.add(ref)
        pins = {pad.GetNumber(): pad.GetNetname() for pad in fp.Pads() if pad.GetNumber()}
        need(set(pins) == set(spec["pins"]), f"Native pad set mismatch: {ref}")
        for number, net in spec["pins"].items():
            need((net is None and pins[number].startswith("unconnected-(")) or pins[number] == "/" + str(net),
                 f"Native pad net mismatch: {ref}.{number}")
    with bom_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    seen = []
    for row in rows:
        refs = [ref.strip() for ref in row["Designators"].split(",")]
        need(int(row["Quantity per board"]) == len(refs) and int(row["Quantity for 5 boards"]) == len(refs) * 5,
             "BOM quantities do not match references")
        need(row["Fit"] == "Yes", "BOM contains non-fitted row")
        for ref in refs:
            need(ref in parts and parts[ref]["mpn"] == row["Manufacturer part number"]
                 and parts[ref]["manufacturer"] == row["Manufacturer"], f"BOM source mismatch: {ref}")
        seen.extend(refs)
    need(len(rows) == 32 and len(seen) == len(set(seen)) == 50 and set(seen) == set(parts), "BOM reference coverage mismatch")
    need(len(smt) == 45 and board.GetCopperLayerCount() == 4, "Native SMT/layer count mismatch")
    return board, fps, smt


def run(command, stage, logs):
    result = subprocess.run([str(CLI), *map(str, command)], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", cwd=stage / "native")
    portable = [str(arg).replace(str(stage), "<PACKAGE_ROOT>") for arg in command]
    entry = {"command": [CLI.name, *portable], "exit_code": result.returncode,
             "stdout": result.stdout, "stderr": result.stderr}
    logs.append(entry)
    dump(stage / "verification/export-command-log.json", logs)
    need(result.returncode == 0, f"KiCad command failed: {' '.join(map(str, command))}\n{result.stdout}\n{result.stderr}")


def check_positions(path, fps, smt, board):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    need(rows and {"Ref", "PosX", "PosY", "Rot", "Side"} <= set(rows[0]), "Unexpected native CSV columns")
    refs = [row["Ref"] for row in rows]
    need(len(refs) == len(set(refs)) == 45 and set(refs) == smt, "Position CSV must contain all and only 45 SMT refs")
    origin = board.GetDesignSettings().GetAuxOrigin()
    side_counts = {"top": 0, "bottom": 0}
    for row in rows:
        fp = fps[row["Ref"]]
        x, y, angle = (float(row[key]) for key in ("PosX", "PosY", "Rot"))
        need(all(math.isfinite(n) for n in (x, y, angle)), "Non-finite placement coordinate")
        need(abs(x - p.ToMM(fp.GetPosition().x - origin.x)) < 0.002
             and abs(y - p.ToMM(origin.y - fp.GetPosition().y)) < 0.002,
             f"Native placement origin/coordinate mismatch: {row['Ref']}")
        side = row["Side"].lower()
        expected = "bottom" if fp.IsFlipped() else "top"
        need(side == expected, f"Native placement side mismatch: {row['Ref']}")
        side_counts[side] += 1
    need(side_counts == {"top": 9, "bottom": 36}, "SMT side totals differ from quote")
    return {"rows": len(rows), "side_counts": side_counts,
            "format": "KiCad native CSV, mm, drill/place origin, bottom X not negated",
            "native_origin_mm": [p.ToMM(origin.x), p.ToMM(origin.y)]}


def build():
    parts, custom, required, prior_drc, prior_erc = preflight()
    source_hashes = {name: sha(ROOT / name) for name in required}
    # A staging name, not the final-candidate name, is used until every check passes.
    DEST.mkdir(parents=True, exist_ok=True)
    stage = DEST / (".staging-r02-" + uuid.uuid4().hex[:12])
    for name in ("native/Adapter.pretty", "documentation", "assembly", "verification", "fabrication"):
        (stage / name).mkdir(parents=True, exist_ok=True)
    for name in NATIVE:
        shutil.copy2(ROOT / name, stage / "native" / name)
    for name in custom:
        shutil.copy2(ROOT / "Adapter.pretty" / name, stage / "native/Adapter.pretty" / name)
    shutil.copy2(ROOT / ATTRIBUTION, stage / "native" / ATTRIBUTION)
    for name in DOCS:
        shutil.copy2(ROOT / name, stage / "documentation" / name)
    for name in DRAWINGS:
        shutil.copy2(ROOT / name, stage / "assembly" / name)
    shutil.copy2(ROOT / "BOM.csv", stage / "assembly/BOM.csv")
    for name in EVIDENCE + ["parts.json"]:
        shutil.copy2(ROOT / name, stage / "verification" / name)
    shutil.copy2(ROOT / "evidence/final-drc.json", stage / "verification/source-final-drc.json")
    shutil.copy2(ROOT / "evidence/final-erc.json", stage / "verification/source-final-erc.json")
    native = stage / "native/adapter.kicad_pcb"
    schematic = stage / "native/adapter.kicad_sch"
    logs = []
    run(["pcb", "drc", "--format", "json", "--all-track-errors", "--schematic-parity",
         "--severity-all", "--exit-code-violations", "--output", stage / "verification/final-drc.json", native], stage, logs)
    drc = check_drc(stage / "verification/final-drc.json")
    run(["sch", "erc", "--format", "json", "--severity-all", "--exit-code-violations",
         "--output", stage / "verification/final-erc.json", schematic], stage, logs)
    erc = check_erc(stage / "verification/final-erc.json")
    board, fps, smt = native_bom_check(native, parts, stage / "assembly/BOM.csv")
    run(["pcb", "export", "gerbers", "--layers", ",".join(LAYERS), "--no-protel-ext",
         "--use-drill-file-origin", "--precision", "6", "--subtract-soldermask",
         "--output", str(stage / "fabrication") + "/", native], stage, logs)
    run(["pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot",
         "--excellon-units", "mm", "--excellon-zeros-format", "decimal", "--excellon-separate-th",
         "--excellon-oval-format", "route", "--generate-map", "--map-format", "pdf",
         "--generate-report", "--report-path", stage / "fabrication/drill-report.txt",
         "--output", str(stage / "fabrication") + "/", native], stage, logs)
    run(["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
         "--smd-only", "--exclude-fp-th", "--exclude-dnp", "--use-drill-file-origin",
         "--output", stage / "assembly/SMT-placement.csv", native], stage, logs)
    placement = check_positions(stage / "assembly/SMT-placement.csv", fps, smt, board)
    expected_gerbers = {f"adapter-{layer.replace('.', '_')}.gbr" for layer in LAYERS}
    actual_gerbers = {file.name for file in (stage / "fabrication").glob("*.gbr")}
    need(expected_gerbers == actual_gerbers, f"Gerber file set mismatch: {actual_gerbers}")
    for name in expected_gerbers:
        data = (stage / "fabrication" / name).read_text(encoding="utf-8")
        need("%FSL" in data and "M02*" in data, f"Incomplete Gerber: {name}")
    for suffix in ("PTH", "NPTH"):
        file = stage / "fabrication" / f"adapter-{suffix}.drl"
        need(file.is_file() and file.stat().st_size > 0, f"Missing native {suffix} drill file")
        text = file.read_text(encoding="utf-8")
        need("M48" in text and "M30" in text and "METRIC" in text, f"Incomplete/incorrect-unit drill file: {file}")
    for name in DRAWINGS:
        path = stage / "assembly" / name
        if path.suffix == ".pdf":
            need(path.read_bytes().startswith(b"%PDF-"), f"Invalid PDF header: {name}")
    # Export commands must not change any master or copied native source.
    need(source_hashes == {name: sha(ROOT / name) for name in required}, "Master source changed during packaging; do not finalize")
    for name in NATIVE:
        need(sha(stage / "native" / name) == source_hashes[name], f"Copied native source changed: {name}")
    ignored = erc.get("ignored_checks", [])
    verification = {
        "status": "PASS - native file checks and real export completeness; QUOTE/DFM ONLY",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "native_checks_rerun_on_packaged_copies": True,
        "drc": {"violations": 0, "unconnected_items": 0, "schematic_parity": 0,
                "ignored_checks": drc.get("ignored_checks", []), "included_severities": drc["included_severities"]},
        "erc": {"enabled_check_violations": 0, "ignored_check_categories": ignored,
                "included_severities": erc["included_severities"], "SPICE_simulation_performed": False},
        "BOM": {"rows": 32, "installed_parts_per_board": 50, "SMT": 45, "THT": 5, "board_quantity": 5},
        "manufacturing_finish": {"solder_mask": "purple", "legend": "white", "surface_finish": "ENIG"},
        "placement": placement, "gerber_layers": LAYERS, "drills": ["PTH", "NPTH"],
        "source_sha256": source_hashes,
        "limits": ["No physical prototype measurements", "No universal host/driver fit or compatibility claim",
                   "No EMC, thermal or safety certification", "No component procurement or fabrication release",
                   "No website submission, payment or publication performed by this script"],
    }
    dump(stage / "verification/PACKAGE_VERIFICATION.json", verification)
    ignore_lines = "\n".join("  - " + str(item.get("key", item)) + ": " + item.get("description", "") for item in ignored) or "  - None"
    readme = f"""OEA r0.2 - PCBWay quotation and DFM package
QUOTE / DFM ONLY - NOT A PRODUCTION RELEASE

Quote five fully assembled adapters and five finished 500 mm harnesses.
The included native CAD and manufacturing exports describe this r0.2 candidate.
Do not procure parts or fabricate from this quotation without a separate
written release. First-article fit and electrical measurements remain required;
remaining manufacture follows approval of that first article and its test limits.
The earlier r0.1 submission and preliminary r0.2 scope ZIP are superseded for
this quote and are not fabrication inputs.

Start with documentation/QUOTE_SCOPE.txt, ASSEMBLY_AND_WIRING.txt and
FUNCTIONAL_TEST.txt. External screw-terminal power is required in BOTH modes:
12/24 V input with selector 5V supplies nominal 5 V minus diode/wiring losses;
regulated 5 V or 24 V input with selector EXT uses that external voltage.
12 V EXT requires an individually approved driver. The adapter is a common-
positive current-sink interface; it is not isolated or universally compatible.

Board: 15.24 x 38.10 mm, 4 copper layers, proposed 1.60 mm FR-4 / 1 oz each
layer / ENIG / purple solder mask / white legend, subject to agreed factory stackup.
F.Cu: signals/GND fill; In1.Cu: continuous GND reference;
In2.Cu: signal crossings/GND fill; B.Cu: signals/GND fill.
The board extends 17.78 mm beyond the previous StepStick length at the DIR end.
Host socket pinout, adjacent-slot clearance and underside fit must be confirmed.

assembly/BOM.csv: 32 MPN rows, 50 fitted parts per board; quantities for one
and five boards. 45 SMT parts (9 top, 36 bottom) and 5 THT parts (J1/J2 below;
J3/J4/SW1 above). The five complete harnesses are additional to the PCB BOM
and are fully specified in ASSEMBLY_AND_WIRING.txt. No customer crimping or
soldering is part of delivery. Include the harness work in the turnkey quote.

assembly/SMT-placement.csv is the native KiCad CSV for all 45 SMT refs, in mm,
using the board's drill/place origin, with bottom X not negated. Gerbers and
drills use this same origin. KiCad rotations are retained; verify physical
pin-1 polarity and underside orientation against the assembly/native files.
All five through-hole components are excluded from the SMT placement CSV
but remain fully fitted BOM items and factory assembly work.

fabrication/ contains 11 actual Gerber layers, separate PTH/NPTH Excellon
drills, and native drill maps/report. native/ contains the actual KiCad 10
project, source, symbol library and only the six used custom footprints,
including the J4 derivative's license/attribution notice.
Standard footprints require the normal KiCad 10 libraries. No manufacturer
datasheet PDFs, old revision files or internal routing history are included.

The copied native board was checked again: zero reported DRC violations,
zero unconnected items, zero schematic-parity findings and no DRC exclusions.
The copied schematic has zero violations among enabled ERC checks, including
error/warning/exclusion severities. Ignored ERC categories are listed exactly:
{ignore_lines}
No SPICE simulation was performed. File checks are distinct from physical
measurements; see verification/PACKAGE_VERIFICATION.json for precise scope.

manifest.json lists payload file sizes and SHA-256 hashes. SHA256SUMS.txt also
covers the manifest. A separate receipt outside the ZIP gives the ZIP hash.
This package is prepared for the PCBWay website; its creation does not prove
upload, quotation submission, publication, order placement or payment.
"""
    (stage / "README.txt").write_text(readme, encoding="utf-8")
    # CLI lock/cache artifacts are not manufacturing inputs and must not slip in.
    for file in stage.rglob("*"):
        if file.is_file():
            need(file.suffix not in {".kicad_prl", ".lck"} and not file.name.startswith("~"),
                 f"Unexpected transient file in staging: {file}")
    files = sorted(file for file in stage.rglob("*") if file.is_file())
    manifest = {"package": ZIP.name, "revision": "OEA r0.2", "purpose": "Quotation and DFM only",
                "production_release": False,
                "files": [{"path": file.relative_to(stage).as_posix(), "bytes": file.stat().st_size,
                           "sha256": sha(file)} for file in files]}
    dump(stage / "manifest.json", manifest)
    checksum_files = sorted(file for file in stage.rglob("*") if file.is_file())
    (stage / "SHA256SUMS.txt").write_text("\n".join(f"{sha(file)}  {file.relative_to(stage).as_posix()}"
                                                for file in checksum_files) + "\n", encoding="utf-8")
    # All required checks and exports passed; only now publish final directory/ZIP.
    pending_zip = DEST / (stage.name + ".zip")
    with zipfile.ZipFile(pending_zip, "x", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(path for path in stage.rglob("*") if path.is_file()):
            archive.write(file, file.relative_to(stage).as_posix())
    with zipfile.ZipFile(pending_zip) as archive:
        need(archive.testzip() is None, "ZIP CRC validation failed")
    for path in (stage, FINAL, pending_zip, ZIP):
        need(path.resolve().is_relative_to(DEST.resolve()), f"Package move escapes intended destination: {path}")
    need(not FINAL.exists() and not ZIP.exists(), "Final destination appeared during build; preserve it")
    stage.rename(FINAL)
    pending_zip.rename(ZIP)
    receipt = {"created_utc": datetime.now(timezone.utc).isoformat(), "package": ZIP.name,
               "bytes": ZIP.stat().st_size, "sha256": sha(ZIP), "manifest_sha256": sha(FINAL / "manifest.json"),
               "file_count": len(list(path for path in FINAL.rglob("*") if path.is_file())),
               "status": "Built for quotation/DFM only; no website submission performed"}
    dump(DEST / "OEA-r0.2-PCBWay-QUOTE-DFM-receipt.json", receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Build only after final native checks and reviews pass")
    args = parser.parse_args()
    if not args.build:
        parser.error("Explicit --build is required; no exports or package created")
    build()
