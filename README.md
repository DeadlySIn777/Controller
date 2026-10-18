# Controller motherboard — public routing review

Actual editable KiCad 10 motherboard source and Specctra routing interchange, published 18 October 2026. **The board is unfinished and not ready for fabrication or assembly.**

## Open the actual files

- [Verified baseline project](board/baseline/board.kicad_pro), [PCB](board/baseline/board.kicad_pcb), [custom rules](board/baseline/board.kicad_dru), and the adjacent complete schematic/local libraries.
- [Latest staged project](board/staged/board.kicad_pro), [PCB](board/staged/board.kicad_pcb), and [custom rules](board/staged/board.kicad_dru). This contains unqualified routing/power-zone changes and has no completed current native refill/DRC.
- [Baseline six-layer Specctra DSN](routing/corrected-R299-baseline-native-raw.dsn), and [raw staged six-layer Specctra DSN](routing/stage4-native-raw.dsn). Native export alone does **not** translate every custom DRU isolation/return/current requirement; inspect the KiCad rules before routing.
- [Exact baseline project with its saved fill cache](archives/baseline-full-cached-project.zip) and [exact staged project with its saved fill cache](archives/staged-full-cached-project.zip). Extract into separate directories and open `board.kicad_pro`.
- [Measured whole-board review and figure](review/REVIEW.md), [setup findings](SETUP_REVIEW.md), [power/stackup review](review/power-and-stackup-review.txt), [native baseline DRC](evidence/baseline-drc.json), and [file hashes/provenance](MANIFEST.json).

The loose `.kicad_pcb` files omit only derived `(filled_polygon ...)` cache nodes to fit normal GitHub file limits. All other bytes are retained. Their source zones, tracks, vias, pads and placement are unchanged. A refill is required before judging filled copper or current connectivity. ZIP archives retain the complete original cached board bytes, verified against the source SHA-256; use those to inspect the measured baseline without refilling. The staged cache is inherited evidence and does not validate its edited zones.

## Measured status

The corrected baseline has **1,172 required pad-island joins**, **1,183 API unconnected items**, and **499 CLI unconnected diagnostic rows**. These are different counters for the same incomplete board. Cached native DRC reports zero other errors, 332 warnings and zero schematic parity issues. This is not a zero-error completed board. Latest staged changes have no new measured full native AFTER count.

The board is 450 × 235 mm, six copper layers, 2,723 footprints and 9,971 pads. Current staged source contains 86,456 track segments and 8,014 vias. Signal routing occupies mainly F.Cu, In3.Cu and B.Cu; the remaining inner layers largely carry split power/reference zones. Raw export census reports 82,946 locked copper objects out of 94,470 tracks/vias. Historical locks must be reviewed for coordinated global routing rather than assumed electrical requirements.

One active motherboard retains the soldered FPGA, all twelve fitted motor interfaces with individual enable/alarm, four ABZ encoders, 24 DI and 16 smart DO plus the other required interfaces. Existing machine settings, electrical limits, galvanic domains and fault/recovery behavior remain requirements. No channel removal, domain merge or blanket clearance reduction is authorized by this snapshot.

This repository is a bounded engineering-review snapshot, including actual native sources and selected evidence. It does not include vendor installers, machine configurations, the historical report/cache tree or manufacturing outputs. No new software or hardware license grant is added here.


## Controller documentation

The [complete documentation index](documentation/docs/README.md), [current project briefing](documentation/PROJECT_BRIEFING.md) and [engineering status](documentation/reports/ENGINEERING_STATUS.md) were reconciled on 18 October 2026. They cover the motherboard, software/CLI/UI, compute, displays, service/recovery, costing and qualification requirements.

The [publication scope and source hashes](documentation/PUBLICATION.md) distinguish active guidance, historical evidence and workspace-only references. This documentation addition preserves the board-review files, their measured status and the manufacturing limitations above.
