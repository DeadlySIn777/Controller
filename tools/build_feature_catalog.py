"""Normalize the supplied roadmap; this does not enable controller capabilities.

Without arguments, regenerates research/feature-roadmap.json and docs/FEATURE_CATALOG.md.
--check is read-only: it regenerates both in memory, fails if either file differs, and
verifies that every archived-note reference in research/*.json (path, SHA-256 and line
range) still matches the archived file under research/user-notes/.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/user-notes/2026-09-28-feature-platform.txt"
NOTES_DIR = ROOT / "research/user-notes"
# Research records that cite archived notes; each reference must carry a matching hash.
NOTE_REFERENCES = {
    "research/feature-roadmap.json": lambda data: data["sources"],
    "research/expanded-hardware-target.json": lambda data: [data["source_notes"]],
}
GROUPS = [
    "Wiring and commissioning", "Registration and probing", "Preflight and simulation",
    "Recovery and diagnostics", "Advanced CNC", "Tool changing and automation",
    "Printer calibration and protection", "Advanced printing", "Laser setup and execution",
    "Plasma and platform services", "Motion development", "Lathe, mill and grinder",
    "Machine measurement", "Industrial interfaces", "Operator tools",
    "Specialized printing", "Advanced laser processing", "Other fabrication processes",
    "Machine and shop services", "Maintainability and extension",
]
FIRST_DEMO = {1, 2, 3, 4, 6, 11, 21, 29, 31, 32, 37, 100}
PLASMA_DEMO = {59, 91, 92, 199}
# Package A of docs/PLATFORM_ROADMAP.md; members also in a demonstration keep that focus.
CONFIG_FOUNDATION = {1, 2, 3, 4, 29, 32, 59, 100, 193, 195, 199, 200}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    items = []
    for line_number, line in enumerate(SOURCE.read_text(encoding="utf-8-sig").splitlines(), 1):
        match = re.match(r"^(\d{1,3})\. (.+?) — (.+)$", line)
        if not match:
            continue
        number = int(match[1])
        if not 1 <= number <= 200:
            continue
        text = match[3]
        links = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", text)
        flags = {
            "additional_hardware_marked_in_source": bool(re.search(r"\[(?:Hardware|H)\]", text)),
            "substantial_development_marked_in_source": bool(re.search(r"\[(?:Advanced|R)\]", text)),
        }
        description = re.sub(r':chatgpt-content-reference\{[^}]+\}', '', text)
        description = re.sub(r"\[[^\]]+\]\(https?://[^)]+\)", '', description)
        description = re.sub(r"`?\[(?:Hardware|Advanced|H|R)\]`?", '', description).strip()
        description = re.sub(r"\s{2,}", " ", description)
        items.append({
            "id": f"F{number:03d}", "number": number, "title": match[2],
            "description_from_supplied_note": description,
            "category": GROUPS[(number - 1) // 10],
            "source_line": line_number, "source_flags": flags,
            "delivery_focus": "first_core_demonstration" if number in FIRST_DEMO else
                "first_plasma_module_demonstration" if number in PLASMA_DEMO else
                "configuration_foundation" if number in CONFIG_FOUNDATION else "backlog",
            "product_status": "proposal", "physical_qualification": "not_established",
            "references_from_supplied_note": [
                {"label": label, "url": url, "verification": "not_rechecked_by_catalog_import"}
                for label, url in links
            ],
        })
    assert [item["number"] for item in items] == list(range(1, 201)), "Expected exactly IDs 1–200"
    # Every archived user note is hashed, not only the three the catalogue was first
    # built from, so an edit to any of them is detectable.
    # No fixed count: archiving another note adds its hash here, and --check then
    # reports feature-roadmap.json as stale instead of crashing.
    notes = sorted(NOTES_DIR.glob("*.txt"))
    assert notes, "no archived user notes found under research/user-notes"
    provenance = [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                  for path in notes]
    data = {
        "schema_version": 1, "revision": "2026-09-28", "status": "planning_only",
        "purpose": "Preserve 200 supplied proposals; never use as the installed capability manifest.",
        "sources": provenance,
        "evidence_index": "reports/ENGINEERING_STATUS.md",
        "source_flag_caveat": "Missing H/R marks do not prove hardware-free or easy implementation.",
        "acceptance_strategy": "docs/PLATFORM_ROADMAP.md",
        "features": items,
    }
    outputs = {ROOT / "research/feature-roadmap.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n"}
    lines = [
        "# Feature catalogue — 200 supplied proposals", "",
        "Imported 28 September 2026. All entries are **proposals**, not an installed feature list. "
        "The wording comes from the supplied notes; incidental claims about other products are not "
        "independently established by this import. Original citation placeholders are preserved only "
        "in the source archive, not treated as evidence.", "",
        "[Priorities and acceptance gates](PLATFORM_ROADMAP.md) · "
        "[Machine-readable catalogue](../research/feature-roadmap.json) · "
        "[Actual engineering evidence](../reports/ENGINEERING_STATUS.md)", "",
        "H = source explicitly marks additional hardware; R = substantial development. "
        "An absent mark does not mean a feature has no hardware or engineering dependency. "
        "The first demonstrations exercise a bounded subset of a feature; they do not qualify its full scope.",
    ]
    for index, group in enumerate(GROUPS):
        lines += ["", f"## {index * 10 + 1}–{index * 10 + 10}: {group}", ""]
        for item in items[index * 10:(index + 1) * 10]:
            flags = item["source_flags"]
            labels = []
            if flags["additional_hardware_marked_in_source"]:
                labels.append("H")
            if flags["substantial_development_marked_in_source"]:
                labels.append("R")
            if item["delivery_focus"] != "backlog":
                labels.append(item["delivery_focus"].replace("_", " "))
            suffix = " — " + ", ".join(labels) if labels else ""
            lines += [f"**{item['id']}. {item['title']}**{suffix}", "",
                      item["description_from_supplied_note"], ""]
    outputs[ROOT / "docs/FEATURE_CATALOG.md"] = "\n".join(lines) + "\n"
    return outputs, len(provenance)


def check_note_references():
    """Return problems with archived-note references recorded in research JSON."""
    problems = []
    for rel, extract in NOTE_REFERENCES.items():
        record = ROOT / rel
        if not record.is_file():
            problems.append(f"{rel}: missing")
            continue
        for ref in extract(json.loads(record.read_text(encoding="utf-8-sig"))):
            path = ROOT / ref["path"]
            if Path(ref["path"]).is_absolute() or NOTES_DIR not in path.resolve().parents:
                problems.append(f"{rel}: {ref['path']} is not a repository archived note")
                continue
            if not path.is_file():
                problems.append(f"{rel}: {ref['path']} does not exist")
                continue
            if ref.get("sha256") != sha256(path):
                problems.append(f"{rel}: {ref['path']} sha256 mismatch")
            if "line_end" in ref:
                count = len(path.read_text(encoding="utf-8-sig").splitlines())
                if not 1 <= ref["line_start"] <= ref["line_end"] <= count:
                    problems.append(f"{rel}: {ref['path']} lines {ref['line_start']}-"
                                    f"{ref['line_end']} outside 1-{count}")
    return problems


# Human-readable documents that quote an archived-note line range recorded in JSON.
DOC_RANGE_CITATIONS = {
    "docs/EXPANDED_HARDWARE_TARGET.md": "research/expanded-hardware-target.json",
}


def check_doc_citations():
    """Return warnings where a document's cited line range disagrees with its JSON.

    Warnings, not failures: the documents are maintained outside this generator.
    """
    warnings = []
    for doc_rel, json_rel in DOC_RANGE_CITATIONS.items():
        doc, record = ROOT / doc_rel, ROOT / json_rel
        if not doc.is_file() or not record.is_file():
            continue
        ref = json.loads(record.read_text(encoding="utf-8-sig"))["source_notes"]
        cited = re.findall(r"lines (\d+)\s*[–-]\s*(\d+) of `" + re.escape(ref["path"]) + "`",
                           doc.read_text(encoding="utf-8-sig"))
        expected = (str(ref["line_start"]), str(ref["line_end"]))
        for found in cited:
            if found != expected:
                warnings.append(f"WARNING {doc_rel}: cites lines {found[0]}-{found[1]} of "
                                f"{ref['path']}, but {json_rel} records {expected[0]}-{expected[1]}")
    return warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="read-only: fail if generated files or note references are stale")
    args = parser.parse_args(argv)
    outputs, note_count = build()
    if args.check:
        problems = [f"{p.relative_to(ROOT).as_posix()}: stale (rerun without --check)"
                    for p, text in outputs.items()
                    if not p.is_file() or p.read_bytes() != text.encode("utf-8")]
        problems += check_note_references()
        for warning in check_doc_citations():
            print(warning, file=sys.stderr)
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"read-only check passed: 200 feature IDs, {note_count} archived-note hashes, "
              "note references verified")
        return 0
    for path, text in outputs.items():
        # LF on every platform: newline="" stops Windows from writing CRLF.
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    problems = check_note_references()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"Preserved exactly 200 ordered feature IDs and {note_count} archived-note hashes; "
          "catalogue is planning-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
