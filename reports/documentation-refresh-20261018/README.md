# Documentation reconciliation — 18 October 2026

This pass reconciles active controller guidance with project memory, IS-2 and the source-bound 17 October continuation. It updates documentation only: no new engineering test, synthesis, circuit/board check or physical measurement is claimed.

## Scope

All 37 topic guides in docs/ were reviewed. The 36 manually maintained guides were reconciled; the generated F001–F200 catalogue remains unchanged and its read-only generator check passes. The workspace overview and project briefing now describe the integrated twelve-interface motherboard, implemented disconnected software and actual qualification gaps. Project memory, agent navigation, initial research and routing notes identify current guidance and retain dated scope. The PCBWay checklist and engineering-status entry preserve adoption and release boundaries.

The [documentation index](../../docs/README.md) also inventories 30 component READMEs, 13 top-level research studies and 31 top-level report records. Component sources, dated reports, immutable evidence and archived user notes retain their original bytes and evidence identities unless explicitly listed as active entry-document edits below. The external IS-1 archive and machine configurations are outside the write scope.

## Corrections

- Replaced active fixed-base/removable-card and eight-plus-expansion descriptions with one active motherboard, soldered FPGA, all twelve fitted motor interfaces, individual enable/alarm, four ABZ, 24 DI and 16 smart DO plus required retained interfaces.
- Distinguished approved commodity-module exchange from whole-board service through keyed terminal/harness groups. Preserved settings, factory-calibration separation, protected recovery/mirror/export, offline entitlement and deliberate inhibited restart.
- Replaced stale six/two-only and future-first-integration descriptions with scoped eight-/twelve-joint disconnected LinuxCNC/C/SPI/SIM2/virtual-feedback results. Kept six/two evidence historical.
- Recorded corrected canonical SIM2 functional mapping at 17,912 LUT4+ADD while keeping full physical wrapper, I/O insertion, place/route, routed timing and physical qualification open.
- Kept adopted CAD30, recovered R299, corrected cached DRC and staged routing candidates distinct. No stale cached fill is promoted to new connectivity proof.
- Preserved all display classes, complete package costing, optional AI and shared CLI/UI transaction requirements. Dated partial costs remain incomplete and do not price later experimental boards.
- Updated the acceptance-gate descriptions without closing any complete-product gate. Generated feature IDs, existing fenced CLI examples and electrical/motion limits were preserved.

## Review and checks

Three parallel document reviews covered hardware, software and product/service/manufacturing guidance. An independent review of the new overview, briefing, index and product documents found two clarity issues: settings payload language implied completed physical media, and a pronoun attached a historical virtual-bank fixture to the appliance. Both are corrected.

The aggregate link/fence/whitespace/coverage results and byte comparisons are recorded in [checks.json](checks.json). [baseline.json](baseline.json) records 75 pre-existing entry-document backups under [before/](before/README.md). These are documentation snapshots, not newly validated engineering evidence.

Read-only catalogue verification: python tools/build_feature_catalog.py --check passed for 200 feature IDs, eight archived-note hashes and note references. Heavy engineering checks were not rerun for prose changes.

## Preserved evidence

The [17 October finishing report](../board-finish-20261017/README.md) remains the source for the exact current continuation. Its pending process statements are reported as that document's recorded state, not as a new live-process observation. No physical hardware, adopted board, calibration, firmware, fabrication output, upload to a manufacturer or purchasing action is performed by this documentation review.

The later GitHub publication requested by the user is a separate documentation-only copy. Its publication receipt records the destination and exact content, preserving the existing board-review package.
