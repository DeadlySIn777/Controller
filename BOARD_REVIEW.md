# Controller motherboard â€” public routing review

Actual editable KiCad 10 motherboard source and Specctra routing interchange, published 18 October 2026. **The board is unfinished and not ready for fabrication or assembly.**

## Start with the current board and setup

[Current source ZIP, exact design rules and both current DSN inputs](review/current-routing-setup-20261018/README.md). This entry identifies the exact a210 starting board and distinguishes historical full results from current cached measurements. Use it for the requested global routing/setup review.

## Corrected literal LED net source

[Corrected editable a210 project](review/literal-net-source-correction-20261018/README.md) fixes 17 blank net fields in the d798 candidate without changing physical geometry. All 94,334 copper records pass the finite source/interchange check; no new routing or full-refill result is claimed.

## New isolated physical source candidate

[Complete three-clamp source project and native cached evidence](review/three-clamp-source-20261018/README.md). All six clamp-pad root relationships now pass cached native checks. Full refill/DRC, return-floor correction and electrical qualification remain open; the candidate is unadopted and separate from the global routing input.

## Actual bulk result rejected; pre-route contact mismatch measured

[Read the source-bound failure evidence](review/router-contact-model-failure-20261018/README.md). The first Rust routed result is HELD: cached native joins worsen **1,693 → 2,192** with 502 old groups split. A separate original-engine experiment with no routing already misses **631 ordinary native joins** in its optimistic normal-contact graph; tail cleanup loses more source relationships. An actual inactive-layer copper violation is independently proved. These are routing-model/setup failures under diagnosis; no new routing gain or accepted board is claimed.

## Completed cached DRC diagnostic - 18 October

The older R7 additive candidate now has [actual cached native DRC](evidence/R7-cached-native-drc.json): **61 clearance errors and 46 hole-clearance errors**, plus **499 unconnected diagnostic rows**, with zero schematic parity issues. Every one of the 107 clearance errors involves saved zone copper (13 track/zone, 48 via/zone and 46 via-hole/zone); there are no discrete-copper/discrete-copper error pairs in this report. This is not a clean DRC result or evidence that a refill will automatically fix every error. Actual filled apertures and retained plane connectivity/current/return paths still need verification. [Scope receipt](evidence/R7-cached-native-drc-scope.json) confirms unchanged inputs and no refill. This older candidate differs from the current a693 global input.

## Latest global experiment input

[Current exact joint PCB project, DSN, rules and limitations](current-global-R3/README.md). This is the actual input of the new global routing experiment; acceptance and full native AFTER checks are pending. Earlier snapshots below retain their own source and measurement scope.

[Subsequent native preservation PASS and two runtime fixes](review/router-runtime-corrections-20261018.md): the interchange now retains all current source copper records and via masks; actual routed AFTER remains pending.

## Router interchange update

[New measured failures and setup corrections](review/router-interchange-findings.md): the corrected native reference is **1,193 joins / 1,210 API items**. The early R6 cached round trip loses five connections and is rejected. The R8 partial-retrace correction passes exact segment preservation and router load/export; native cached round-trip verification now passes at the identical 1,193 joins / 1,210 API items, with all 8,001 via records and actual flashed layers unchanged. Full refill/DRC remains open. Historical blanket locks and lossy coordinate/via-mask import are also being corrected. Treat the earlier R6 DSN as a preserved diagnostic input.

The latest [bulk routing candidate and evidence](review/router-interchange-findings.md#measured-bulk-candidate-and-global-routing-setup) measures 1,193 → 1,181 joins in cached native validation, with no existing connectivity lost. Its exact editable project ZIP is included; full refill and DRC remain pending. R9 failed its native preservation check; the R10 replacement is being checked.

## Open the actual files

- [Current corrected global reroute start](board/global-reroute-start/board.kicad_pro), [PCB](board/global-reroute-start/board.kicad_pcb), [rules](board/global-reroute-start/board.kicad_dru), [exact source project ZIP](archives/global-reroute-start-source-project.zip), and [clean global DSN](routing/TMR-clean-plane-free-F-In3-B-domain600-r6.dsn). [Setup correction and router limitations](review/TMR-setup-correction.md) explain five restored converter keepouts, eight foreign source-plane cuts and 359 conflicting copper items removed for rerouting. This is an unqualified reroute start with no new native AFTER count.
- [Verified baseline project](board/baseline/board.kicad_pro), [PCB](board/baseline/board.kicad_pcb), [custom rules](board/baseline/board.kicad_dru), and the adjacent complete schematic/local libraries.
- [Historical staged project](board/staged/board.kicad_pro), [PCB](board/staged/board.kicad_pcb), and [custom rules](board/staged/board.kicad_dru). This contains unqualified routing/power-zone changes and has no completed current native refill/DRC.
- [Baseline six-layer Specctra DSN](routing/corrected-R299-baseline-native-raw.dsn), and [raw staged six-layer Specctra DSN](routing/stage4-native-raw.dsn). Native export alone does **not** translate every custom DRU isolation/return/current requirement; inspect the KiCad rules before routing.
- [Exact baseline project with its saved fill cache](archives/baseline-full-cached-project.zip) and [exact staged project with its saved fill cache](archives/staged-full-cached-project.zip). Extract into separate directories and open `board.kicad_pro`.
- [Measured whole-board review and figure](review/REVIEW.md), [setup findings](SETUP_REVIEW.md), [power/stackup review](review/power-and-stackup-review.txt), [native baseline DRC](evidence/baseline-drc.json), and [file hashes/provenance](MANIFEST.json).

The loose `.kicad_pcb` files omit only derived `(filled_polygon ...)` cache nodes to fit normal GitHub file limits. All other bytes are retained. Their source zones, tracks, vias, pads and placement are unchanged. A refill is required before judging filled copper or current connectivity. ZIP archives retain the complete original cached board bytes, verified against the source SHA-256; use those to inspect the measured baseline without refilling. The staged cache is inherited evidence and does not validate its edited zones.

## Measured status

The corrected baseline has **1,172 required pad-island joins**, **1,183 API unconnected items**, and **499 CLI unconnected diagnostic rows**. These are different counters for the same incomplete board. Cached native DRC reports zero other errors, 332 warnings and zero schematic parity issues. This is not a zero-error completed board. Latest staged changes have no new measured full native AFTER count.

The board is 450 Ã— 235 mm, six copper layers, 2,723 footprints and 9,971 pads. Current staged source contains 86,456 track segments and 8,014 vias. Signal routing occupies mainly F.Cu, In3.Cu and B.Cu; the remaining inner layers largely carry split power/reference zones. Raw export census reports 82,946 locked copper objects out of 94,470 tracks/vias. Historical locks must be reviewed for coordinated global routing rather than assumed electrical requirements.

One active motherboard retains the soldered FPGA, all twelve fitted motor interfaces with individual enable/alarm, four ABZ encoders, 24 DI and 16 smart DO plus the other required interfaces. Existing machine settings, electrical limits, galvanic domains and fault/recovery behavior remain requirements. No channel removal, domain merge or blanket clearance reduction is authorized by this snapshot.

This repository is a bounded engineering-review snapshot, including actual native sources and selected evidence. It does not include vendor installers, machine configurations, the historical report/cache tree or manufacturing outputs. No new software or hardware license grant is added here.

## Latest measured KiCad candidate — 18 October 2026

[Download the complete KiCad project and inspect supporting files](review/kicad-candidate-a76e13de-20261018/README.md). Six cached native joins closed with zero old pad pairs lost; routing and manufacturing qualification remain incomplete.

## Later routed KiCad progress

[New complete project and native measurements](review/routing-progress-20261018-r1/README.md): 1,688 → 1,687 cached joins, zero prior pad pairs lost. Full refill/DRC and manufacture remain open.

## Later routed KiCad progress

[New complete project and native measurements](review/routing-progress-20261018-r2/README.md): 1,687 → 1,680 cached joins, zero prior pad pairs lost. Full refill/DRC and manufacture remain open.

## Current measured routing progress

[Complete project and native receipts](review/routing-progress-20261018-r5/README.md): 1,665 → 1,649 cached joins, zero old pad pairs lost. Full refill/DRC remains open.
