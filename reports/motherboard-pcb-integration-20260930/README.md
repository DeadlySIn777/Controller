# Additive motherboard PCB population — 2026-09-30

`populated-r02/motherboard-populated-candidate.kicad_pcb` contains all **880 physical footprints / 878 fitted components** from the corrected 880-part source snapshot. The live source has subsequently grown to 980 parts; these 100 later parts are deliberately absent from this frozen candidate. This is a source-reconciled partial board, not a finished layout or fabrication package.

The candidate preserves the retained 327 footprints, their placement and native fields, all 1,907 tracks/vias, five filled-zone definitions, and the original project/rule files. The sole retained pad changes are the exact 64 former FPGA NC nets allowed by the parent assembly-map ledger. It adds 553 actual-source footprints and their exact numbered copper pads and unnumbered stencil apertures. Independent comparison covers 3,317 numbered copper pads and preserves 228 paste-only apertures without counting them as electrical nodes.

Native KiCad DRC reports **zero regular violations, zero ignored checks and 499 capped unconnected items**. The uncapped native connectivity inventory reports **1,637 missing joins**. No copper was added by this population step. The six-layer, 1.6 mm board has one provisional 460 × 340 mm outline; it is not the final enclosure, fabrication size, power-plane implementation or cost commitment.

The 12 DI receiver regions now each contain the actual two input channels and one ISO1212 rather than being grouped by sensor-power bank. Their bypasses target actual VCC1 pin 2 and are within 3 mm of that pad. The placement ledger names 79 actual supply-pad bypass targets. Ten other targets remain over 3 mm, with a maximum of 7.54 mm. These and all routed supply/return paths require further placement/routing review; the report records each target and distance. Neither proximity nor a clean DRC establishes qualified decoupling.

The independent watchdog-clear ownership check proves that the source command reaches U4018 input pins 1 and 3 through the intended resistors, defaults LOW through 100 kΩ, and does not drive the U4019 output pins. It does not claim those new command paths are physically routed. `populated-r01` is retained as superseded evidence: its earlier source wrongly drove push-pull clear outputs, despite matching source pins and having no regular DRC violations. See `superseded-r01.json`.

All 17 native population and mutation checks pass. They cover source pad/net parity, exact package/stencil geometry, retained object/zone/copper preservation, unapproved-net-change rejection, watchdog-clear ownership/default rejection, and actual DI pair/bypass placement. All 139 frozen source input files match their archived hashes. Native PDF export and its rendered PNG were visually inspected: the 12 DI regions, motor regions, retained source area and explicit empty module/terminal reservations are visible within the expanded outline. The PDF is a board review, not an assembly drawing for manufacture.

There are **zero implemented compute, ESP, storage or external terminal connector footprints** in this candidate. The marked module and terminal envelopes are nonphysical reservations. Exact sockets, mates, installed orientation, heights, antenna/thermal keepouts and field wiring still require source and mechanical implementation. Required analog/comms, sensor power, common I/O controls and other later source work remain incomplete or absent from this 880-part freeze. The report does not fabricate connector footprints, NC exceptions, routed nets, manufacturing outputs or hardware measurements.

Main evidence:

- `populated-r02/report.json`: exact inventory, source hashes, native DRC, retained geometry and open bypass targets.
- `populated-r02/placement-ledger.json`: actual component placements and supply-pad targets.
- `populated-r02/board-review.pdf` and `board-review.png`: native plot and inspected render.
- `frozen-source-r02/snapshot-sha256.json`: 139-file source freeze.
- `test-errors-r02-second.txt`: 17 passing native checks.
- `RETAINED_MC_AUDIT.md` and `retained-mc-inventory.csv`: actual retained 327-part function audit. No reviewed removal is implemented.

No Gerbers, drills, final CPL, manufacturing readiness or physical qualification are asserted here.
