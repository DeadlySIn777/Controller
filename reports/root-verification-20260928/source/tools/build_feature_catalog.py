"""Normalize the supplied roadmap; this does not enable controller capabilities."""

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/user-notes/2026-09-28-feature-platform.txt"
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


def main():
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
    provenance = []
    for name in ["feature-platform", "plasma-upgrades", "modbus-expansion"]:
        path = ROOT / f"research/user-notes/2026-09-28-{name}.txt"
        provenance.append({"path": path.relative_to(ROOT).as_posix(),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    data = {
        "schema_version": 1, "revision": "2026-09-28", "status": "planning_only",
        "purpose": "Preserve 200 supplied proposals; never use as the installed capability manifest.",
        "sources": provenance,
        "evidence_index": "reports/ENGINEERING_STATUS.md",
        "source_flag_caveat": "Missing H/R marks do not prove hardware-free or easy implementation.",
        "acceptance_strategy": "docs/PLATFORM_ROADMAP.md",
        "features": items,
    }
    (ROOT / "research/feature-roadmap.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
    (ROOT / "docs/FEATURE_CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Preserved exactly 200 ordered feature IDs and three source hashes; catalogue is planning-only.")


if __name__ == "__main__":
    main()
