"""Repackage the frozen review archive for PCBWay's 1 MB portal limit."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / "OEA-r0.1-PCBWay-REVIEW-NOT-FOR-ORDER.zip"
EXPECTED_SOURCE_SHA256 = "e793a8df3aa2d4ee4738202a399ca24aefa6719ff602262008ed0fb78a198534"
LIMIT = 1_000_000
PREFIX = "OEA-r0.1-review/"
INSTRUCTION_NAME = "PORTAL-READ-FIRST.txt"
FILENAMES = [
    "OEA-r0.1-01-Native-CAD-REVIEW-ONLY.zip",
    "OEA-r0.1-02-Assembly-Harness-REVIEW-ONLY.zip",
    "OEA-r0.1-03-Previews-Evidence-REVIEW-ONLY.zip",
]
NATIVE = {
    "adapter-assembly-review.step", "adapter.kicad_pcb", "adapter.kicad_pro",
    "adapter.kicad_sch", "Adapter.kicad_sym", "adapter.net.xml",
    "fp-lib-table", "sym-lib-table", "build_pcb.py", "build_schematic.py",
    "make_review_zip.py", "package_review.py", "route_candidate.py",
    "verify_schematic.py", "pad_coordinates.json", "parts.json", "routes.json",
    "review_package_manifest.json",
}
ASSEMBLY = {
    "adapter-schematic.pdf", "cable_bom.csv", "cable_pinmap.csv",
    "FUNCTIONAL_TEST.md", "HARNESS_SPEC.md", "header-61300711121.pdf",
    "header-61300811121.pdf", "header-7pin-datasheet-review.json",
    "header-datasheet-review.json", "header-drawing-preview.png",
    "PCBWay_BOM_DRAFT.csv", "PCBWay_CPL_DRAFT.csv", "PCBWAY_QUOTE_DRAFT.md",
    "README.md", "SOURCES.md",
}
PREVIEWS = {
    "adapter-3d.png", "assembly-review.png", "assembly-review.svg",
    "board-bottom.svg", "board-top.svg", "schematic-preview.png",
    "schematic-connectivity.json", "verification.json",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def group(name):
    relative = name.removeprefix(PREFIX)
    if relative in NATIVE or relative.startswith("Adapter.pretty/"):
        return 0
    if relative in ASSEMBLY:
        return 1
    if relative in PREVIEWS or relative.startswith("evidence/"):
        return 2
    raise ValueError(f"Unassigned original entry: {name}")

def main():
    original_bytes = SOURCE.read_bytes()
    assert sha(original_bytes) == EXPECTED_SOURCE_SHA256
    with zipfile.ZipFile(SOURCE) as archive:
        assert archive.testzip() is None
        infos = archive.infolist()
        assert len({i.filename for i in infos}) == len(infos)
        contents = {i.filename: archive.read(i.filename) for i in infos}
    groups = [[], [], []]
    for info in infos:
        groups[group(info.filename)].append(info)
    instructions = (
        "OEA r0.1 - PCBWay portal upload package\n\n"
        "ENGINEERING / DFM REVIEW AND QUOTATION ONLY. NOT RELEASED FOR MANUFACTURE.\n"
        "Do not procure parts or fabricate until a separate written build release.\n\n"
        "Download all three ZIP files and extract each into THE SAME destination folder:\n"
        + "\n".join(FILENAMES) + "\n\n"
        "These are independently extractable ZIP archives, not multipart ZIP volumes.\n"
        "Together they reproduce all 45 original entries with unchanged relative paths\n"
        "and byte-for-byte contents beneath the OEA-r0.1-review folder.\n"
        "The original review_package_manifest.json remains unchanged and validates its\n"
        "original 44-file set. This added instruction is outside that manifest set.\n\n"
        "Full turnkey quote scope: five assembled boards and five finished cable harnesses.\n"
        "Five sets and 500 mm harness length are provisional quotation assumptions.\n"
        "Refer to PCBWAY_QUOTE_DRAFT.md, HARNESS_SPEC.md and FUNCTIONAL_TEST.md for scope\n"
        "and unresolved release conditions. No Gerbers or drill files are included.\n\n"
        "The frozen original archive includes pre-submission status wording; it records\n"
        "design/package status at creation, not subsequent email or portal transmission.\n\n"
        f"Original archive: {SOURCE.name}\n"
        f"Original archive SHA256: {EXPECTED_SOURCE_SHA256}\n"
    ).encode("utf-8")
    packages = []
    observed = {}
    for index, (filename, group_infos) in enumerate(zip(FILENAMES, groups)):
        target = HERE / filename
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
            if index == 0:
                out.writestr(INSTRUCTION_NAME, instructions)
            for info in group_infos:
                out.writestr(info, contents[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        assert target.stat().st_size < LIMIT, (filename, target.stat().st_size)
        with zipfile.ZipFile(target) as check:
            assert check.testzip() is None
            for name in check.namelist():
                data = check.read(name)
                if name == INSTRUCTION_NAME:
                    assert index == 0 and data == instructions
                    continue
                assert name not in observed
                assert data == contents[name]
                observed[name] = sha(data)
        packages.append({
            "path": str(target), "filename": filename,
            "bytes": target.stat().st_size, "sha256": sha(target.read_bytes()),
            "original_entry_count": len(group_infos),
            "additional_entry_count": 1 if index == 0 else 0,
            "original_entries": [i.filename for i in group_infos],
        })
    assert set(observed) == set(contents)
    manifest = json.loads(contents[PREFIX + "review_package_manifest.json"])
    for relative, digest in manifest["files"].items():
        assert observed[PREFIX + relative] == digest
    assert sha(SOURCE.read_bytes()) == EXPECTED_SOURCE_SHA256
    receipt = {
        "status": "portal_packaging_verified_not_submitted",
        "source_path": str(SOURCE), "source_bytes": len(original_bytes),
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "original_archive_unchanged": True,
        "maximum_attachment_bytes_exclusive": LIMIT,
        "archive_count": len(packages), "original_entry_count": len(contents),
        "original_entries_recovered_exactly_once": len(observed),
        "original_entry_hashes_match": True, "original_manifest_file_count": len(manifest["files"]),
        "original_manifest_valid": True, "crc_checks_pass": True,
        "added_instruction_entry": INSTRUCTION_NAME,
        "added_instruction_sha256": sha(instructions),
        "fabrication_authorized": False, "external_submission_performed_by_this_script": False,
        "packages": packages, "original_entry_sha256": observed,
    }
    (HERE / "portal-packaging-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k not in {"original_entry_sha256", "packages"}}, indent=2))
    print(json.dumps([{k: v for k, v in p.items() if k != "original_entries"} for p in packages], indent=2))

if __name__ == "__main__":
    main()
