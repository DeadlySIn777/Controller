"""Prepare a bounded public board-review snapshot without editing source projects."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/board-finish-20261017"
DEST = ROOT / "tmp/github-controller-public-20261018"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def cache_free(data):
    # KiCad filled_polygon nodes are derived fill caches. Preserve every other byte.
    spans = []
    for match in re.finditer(rb"\(filled_polygon(?=\s)", data):
        start = match.start()
        if spans and start < spans[-1][1]:
            continue
        depth, quoted, escaped = 0, False, False
        for end in range(start, len(data)):
            c = data[end]
            if quoted:
                if escaped:
                    escaped = False
                elif c == 92:
                    escaped = True
                elif c == 34:
                    quoted = False
            elif c == 34:
                quoted = True
            elif c == 40:
                depth += 1
            elif c == 41:
                depth -= 1
                if depth == 0:
                    spans.append((start, end + 1))
                    break
        else:
            raise ValueError("Unterminated filled_polygon")
    assert spans, "Expected cached fills"
    chunks, cursor = [], 0
    for start, end in spans:
        chunks.append(data[cursor:start])
        cursor = end
    chunks.append(data[cursor:])
    stripped = b"".join(chunks)
    # Independently reconstruct the original from the output and removed slices.
    rebuilt, cursor, removed = [], 0, 0
    for start, end in spans:
        offset = start - removed
        rebuilt.extend((stripped[cursor:offset], data[start:end]))
        cursor = offset
        removed += end - start
    rebuilt.append(stripped[cursor:])
    assert b"".join(rebuilt) == data
    assert not re.search(rb"\(filled_polygon(?=\s)", stripped)
    return stripped, {"removed_derived_filled_polygon_nodes": len(spans),
                      "removed_cache_bytes": removed,
                      "all_other_bytes_preserved": True,
                      "original_reconstruction_SHA256": sha(data)}

def allowed(path):
    return (path.suffix in {".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_sch",
                            ".kicad_sym", ".kicad_mod"}
            or path.name in {"fp-lib-table", "sym-lib-table"})

def main():
    DEST.mkdir(parents=True, exist_ok=False)
    (DEST / "archives").mkdir()
    provenance = {}
    projects = {
        "baseline": ("corrected-baseline-r1/native", "8c9fb98f44aa0d31b9d71e32f041c47139cb745c355e2364a45de40a93614eff"),
        "staged": ("combined-route-stage-r4/native", "ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55"),
    }
    for label, (relative, expected) in projects.items():
        source = REPORT / relative
        original = (source / "board.kicad_pcb").read_bytes()
        assert sha(original) == expected
        editable, stripping = cache_free(original)
        out = DEST / "board" / label
        out.mkdir(parents=True)
        archive = DEST / "archives" / f"{label}-full-cached-project.zip"
        input_hashes = {}
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as z:
            for src in sorted(source.rglob("*")):
                if not src.is_file() or not allowed(src):
                    continue
                rel = src.relative_to(source)
                contents = src.read_bytes()
                input_hashes[rel.as_posix()] = sha(contents)
                z.writestr(rel.as_posix(), contents)
                target = out / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(editable if rel.as_posix() == "board.kicad_pcb" else contents)
        with zipfile.ZipFile(archive) as z:
            assert sha(z.read("board.kicad_pcb")) == expected
            assert z.testzip() is None
        for name, expected_input in input_hashes.items():
            assert sha((source / name).read_bytes()) == expected_input
        provenance[label] = {"workspace_source": f"reports/board-finish-20261017/{relative}",
                             "original_cached_board_SHA256": expected,
                             "editable_cache_free_board_SHA256": sha(editable),
                             "original_cached_board_bytes": len(original),
                             "editable_cache_free_board_bytes": len(editable),
                             "source_files": input_hashes,
                             "source_files_unchanged": True, **stripping}
    extras = {
        "routing/stage4-native-raw.dsn": "global-router-handoff-r1/stage4-native-raw.dsn",
        "evidence/baseline-drc.json": "corrected-baseline-r1/cached-native-drc/drc.json",
        "evidence/baseline-native-drc-receipt.json": "corrected-baseline-r1/cached-native-drc/receipt.json",
        "evidence/native-export-census.json": "global-router-handoff-r1/native-export-census.json",
        "evidence/raw-export-ready.json": "global-router-handoff-r1/raw-export-ready.json",
        "review/power-and-stackup-review.txt": "power-review/setup-and-bulk-routing-review-r1/review.txt",
        "review/power-and-stackup-summary.json": "power-review/setup-and-bulk-routing-review-r1/summary.json",
    }
    for name, rel in extras.items():
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPORT / rel, target)
    contract_names = ["MOTHERBOARD_IS2.md", "DISPLAY_TIERS.md"]
    (DEST / "requirements").mkdir()
    for name in contract_names:
        shutil.copyfile(ROOT / "docs" / name, DEST / "requirements" / name)
    shutil.copyfile(ROOT / "hardware/motherboard/requirements.json", DEST / "requirements/motherboard.json")
    (DEST / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    (DEST / ".gitignore").write_text("*.lck\n*.kicad_prl\n*-backups/\n", encoding="utf-8")
    (DEST / "README.md").write_text('''# Controller motherboard — public routing review

Actual editable KiCad 10 motherboard source and Specctra routing interchange, published 18 October 2026. **The board is unfinished and not ready for fabrication or assembly.**

## Open the actual files

- [Verified baseline project](board/baseline/board.kicad_pro), [PCB](board/baseline/board.kicad_pcb), [custom rules](board/baseline/board.kicad_dru), and the adjacent complete schematic/local libraries.
- [Latest staged project](board/staged/board.kicad_pro), [PCB](board/staged/board.kicad_pcb), and [custom rules](board/staged/board.kicad_dru). This contains unqualified routing/power-zone changes and has no completed current native refill/DRC.
- [Raw six-layer Specctra DSN](routing/stage4-native-raw.dsn). Native export alone does **not** translate every custom DRU isolation/return/current requirement; inspect the KiCad rules before routing.
- [Exact baseline project with its saved fill cache](archives/baseline-full-cached-project.zip) and [exact staged project with its saved fill cache](archives/staged-full-cached-project.zip). Extract into separate directories and open `board.kicad_pro`.
- [Setup findings](SETUP_REVIEW.md), [power/stackup review](review/power-and-stackup-review.txt), [native baseline DRC](evidence/baseline-drc.json), and [file hashes/provenance](MANIFEST.json).

The loose `.kicad_pcb` files omit only derived `(filled_polygon ...)` cache nodes to fit normal GitHub file limits. All other bytes are retained. Their source zones, tracks, vias, pads and placement are unchanged. A refill is required before judging filled copper or current connectivity. ZIP archives retain the complete original cached board bytes, verified against the source SHA-256; use those to inspect the measured baseline without refilling. The staged cache is inherited evidence and does not validate its edited zones.

## Measured status

The corrected baseline has **1,172 required pad-island joins**, **1,183 API unconnected items**, and **499 CLI unconnected diagnostic rows**. These are different counters for the same incomplete board. Cached native DRC reports zero other errors, 332 warnings and zero schematic parity issues. This is not a zero-error completed board. Latest staged changes have no new measured full native AFTER count.

The board is 450 × 235 mm, six copper layers, 2,723 footprints and 9,971 pads. Current staged source contains 86,456 track segments and 8,014 vias. Signal routing occupies mainly F.Cu, In3.Cu and B.Cu; the remaining inner layers largely carry split power/reference zones. Raw export census reports 82,946 locked copper objects out of 94,470 tracks/vias. Historical locks must be reviewed for coordinated global routing rather than assumed electrical requirements.

One active motherboard retains the soldered FPGA, all twelve fitted motor interfaces with individual enable/alarm, four ABZ encoders, 24 DI and 16 smart DO plus the other required interfaces. Existing machine settings, electrical limits, galvanic domains and fault/recovery behavior remain requirements. No channel removal, domain merge or blanket clearance reduction is authorized by this snapshot.

This repository is a bounded engineering-review snapshot, including actual native sources and selected evidence. It does not include vendor installers, machine configurations, the historical report/cache tree or manufacturing outputs. No new software or hardware license grant is added here.
''', encoding="utf-8")
    (DEST / "SETUP_REVIEW.md").write_text('''# Setup and bulk-routing review

Local micro-repairs did not materially reduce the remaining 1,172 joins. The next routing revision needs coordinated plane/source planning, placement review and global rerouting, followed by native refill/DRC and electrical validation.

1. Assign source-connected per-domain reference regions on In1/In4 and current-sized power paths on In2. In2 is already a split power layer, not spare signal capacity. Source polygons and inherited fill caches cannot prove source-rooted current paths.
2. Review historical copper locks and bank-level placement. The actual export census has 82,946 locked copper objects; forcing all old routes to remain immutable prevents useful global rip-up. Preserve the electrical/fault contract and assess lost/new connections after a redesign.
3. Translate the real custom rules into the routing setup. The 26 project classes share nominal 0.15 mm clearance / 0.2 mm track / 0.6 mm via / 0.3 mm drill defaults. Cross-domain 0.6 mm rules, plated-barrel isolation and scoped exceptions live in the `.kicad_dru`; nominal defaults do not qualify domain isolation or current capacity.
4. Review the 109 keepout areas (107 board-level plus two footprint areas), high-density banks, escape paths and layer transitions. Hard safety/isolation constraints remain; optional host planning margins need separate justification.
5. Reconcile the stackup with a real manufacturer stackup: nominal six 35 µm copper layers plus dielectric/masks total 1.55 mm, while board general thickness is 1.6 mm. This affects impedance/current/thermal qualification.
6. Run the global router on an isolated candidate. Re-import results, refill all zones, compare physical connectivity, run full native DRC/parity and check source/current/return paths. Freerouting completion alone is insufficient.

These findings identify setup obstacles; they do not establish that the present placement is globally routable or impossible. No global routing completion or manufacturing readiness is claimed.
''', encoding="utf-8")
    files = {p.relative_to(DEST).as_posix(): {"bytes": p.stat().st_size, "SHA256": sha(p.read_bytes())}
             for p in sorted(DEST.rglob("*")) if p.is_file()}
    assert all(v["bytes"] < 90 * 1024 * 1024 for v in files.values())
    manifest = {"snapshot_date": "2026-10-18", "purpose": "public engineering routing review",
                "manufacturing_ready": False, "board_complete": False,
                "baseline_required_joins": 1172, "latest_staged_native_after_count": None,
                "project_provenance": provenance, "files_excluding_this_manifest": files}
    (DEST / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "SNAPSHOT_READY_NOT_PUBLISHED", "directory": str(DEST),
                      "files": len(files) + 1, "total_bytes": sum(x["bytes"] for x in files.values()),
                      "projects": {k: {a:b for a,b in v.items() if a != "source_files"}
                                   for k,v in provenance.items()}}, indent=2))

if __name__ == "__main__":
    main()
