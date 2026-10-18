# Live board CAD review

**Latest verified increment — Source26/ROOT102:** two existing capacitor poses and six conductors complete two additional owned bypass loops; no electrical source, parts, pin nets or rating changed. Actual native and independent connectivity agree on **3,524 required joins remaining**, with zero orphan copper. Native regular DRC is **0 errors/0 warnings/no ignored checks**; ERC remains **0 errors/70 unsuppressed warnings**. [Full disconnected r05](../../reports/pre-hardware-validation-20261001/full-two-cap-r05/report.json) passed **17 stages**, left **9 blocked** and **1 physical stage unrun**, with **0 failed stages**; **1,876 host cases and 235 native KiCad cases pass**, five Windows symlink cases remain skipped, and all **3,327 scoped source hashes** stayed unchanged. This supersedes the earlier r101 regression as the current exact-board run. [Current adoption](../../reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06/adoption.json).

[Updated characterization](../../reports/pre-hardware-characterization-20261001/characterization-register-r02/requirements-and-coverage.json) retains all 15 subsystem, 22 fault and nine machine requirements. Twelve changing-speed/reversal pulse generators pass 43,200,324 edge/count checks; four ideal-input encoder components and actual CNC3 structural SPI/codec RTL pass their scoped sweeps. The real manufacturer OPA buffer model passes 12 simultaneous four-channel cases, alongside 96 passive filter cases and two numerical-sensitivity studies. **Complete stateful CNC3/HAL/machine integration and whole-circuit analog qualification remain open.** Failed full-chain amplifier convergence and the encrypted ADC model are recorded; ideal boundaries are not physical substitutes.

[Native drill/land screening](../../reports/motherboard-pcb-integration-20261001/two-cap-full-drill-SMD-audit-r01/receipt.json) identifies **275 existing drilled vias overlapping 279 same-net paste SMD lands**. This is a lower bound: exact tangency and assembly registration margins need further checking. Each location needs layout correction or an explicitly qualified filled/capped fabrication/assembly disposition; ordinary DRC and tenting do not close this work. No fabrication package or manufacturing readiness is claimed.


30 September 2026. User-requested physical design view, backed by editable native KiCad placement files. Open `http://127.0.0.1:8788/index.html` in the Codex right panel while the local review server runs. It serves only this review folder on loopback; it does not connect to a machine or require an online service.

The viewer offers top CAD, native KiCad 3D renders, pan/zoom, component search, source part and pin-net inspection, highlighted changes/review focus and a revision selector. It polls the published manifest every three seconds. A newly published revision updates the latest view; an intentionally selected old revision stays visible until the user selects the update. The server does **not** regenerate CAD when schematics change: the engineering update procedure below publishes that change.

## Current published revision: 20261001-28; working PCB: Source26/r102

The published manifest and adopted working board now contain the same native PCB, SHA-256 `769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5`: **2,688 footprints, 11,641 track/via items, 1,521 native zones/rule areas and 3,524 uncapped missing joins**. Native DRC reports zero regular errors/warnings and no ignored checks. Its capped 499-item unconnected display is not the routing total. The independent count agrees with native all-cluster connectivity and finds zero orphan copper.

The [published native project](revisions/20261001-28/motherboard-native-candidate.kicad_pcb), [native 3D view](revisions/20261001-28/motherboard-3d.png), [publication proof](revisions/20261001-28/publication.json), [adoption and current circuit proofs](../../reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06/adoption.json) and [independent connectivity](revisions/20261001-28/publication-connectivity/review.json) are tied to that exact board. A separate [publication ledger](../../reports/motherboard-cad-publication-20261001/CAD24-to-ROOT101-ledger-r01/receipt.json) records every old-copper, placement, pad, zone, Source and stackup change from CAD24. The actual referenced footprint libraries are copied locally, with 92 used-library land-pattern checks. The [resource addendum](../../reports/motherboard-cad-publication-20261001/ROOT101-model-resource-restoration-r01.json) restores the exact manufacturer compute-socket STEP model omitted by the older publisher's directory filter.

The board is **not manufacturing-ready**. Current scoped proofs cover 108 bypass loops, 221 receiving-return endpoints, 188 Source-anchored filled reference resources, 54 retained return-bridge groups, 82 motor control segments and 20 health-supply continuity endpoints. They preserve all 5,969 prior connected Source-pad groups. U11020/U11026 receiving/control returns, staged Source27 circuit corrections, full power/current/thermal analysis, remaining routing, FPGA implementation and physical fault timing remain unfinished. Native DRC, ERC, host tests and physical qualification are separate evidence.

The provisional board remains 460 × 340 mm, six layers and 1.6 mm thick. The native image was visually inspected and the side-panel opening was queued by the desktop app; actual visible navigation is not independently confirmed. Failed publication revisions 20261001-25 and 20261001-27 are retained as unpublished attempts and are not in the revision selector. Revision28 packages the exact previously checked local footprints and 3D resources with the unchanged ROOT102 board bytes.

## Historical published revision: 20260930-21

Published native CAD **20260930-21** contains the separate frozen **880-footprint / 878 fitted** snapshot. It preserves the original 327 footprints, **2,088 track/via items and five filled zones**. Independent uncapped connectivity finds **1,600 missing joins**. Native DRC reports **zero regular violations, no ignored checks and 499 capped unconnected items**; routing fails. The **460 × 340 mm, six-layer, 1.6 mm** outline remains provisional; existing planes cover the retained core rather than the whole motherboard.

The reconciled electrical source has **1585 physical footprints: 1557 purchased fitted parts, 26 bare PCB test pads and two DNP footprints**, across eighteen source blocks. It contains all twelve motor interfaces, four ABZ receiving paths, 24 DI, 16 smart DO, power-health, actual I/O controllers, protected power entry, probe/pendant supplies, purchased-module compute/ESP sockets and process control with its fourth actual acquisition controller. Native integrated ERC is **zero errors, 72 warnings, no ignored checks** (70 isolated-pin labels and two ground-name warnings). Independent native fitted pin/MPN/footprint and exact original-pin/topology checks pass. The 23 root integration, 26 FPGA allocation, 33 ACC, 35 process and 10 ESP focused tests pass; these do not prove firmware execution or physical behavior.

The additional source parts are being populated onto the existing PCB without discarding its routed copper. Storage and compute raw peripherals, analog/comms, status indicators, actual field terminals, complete power/return routing and mechanical/thermal reconciliation remain engineering work. Logic-rail startup load and monitor-window corrections are under review. The 20 ms inhibit requirement, partial-power behavior, target firmware, vendor FPGA package fit/timing and physical/EMC/thermal qualification remain unproved. Gerbers, drills, final assembly CPL/drawings and a final stackup have not been released; manufacturing_ready remains false. Original six-joint/two-encoder runtime results remain historical baseline evidence; twelve fitted interfaces are not twelve proven coordinated axes.

[Native PCB](revisions/20260930-21/motherboard-populated-candidate.kicad_pcb), [publication receipt](revisions/20260930-21/publication.json), [uncapped connectivity](revisions/20260930-21/publication-connectivity/review.json).

## Historical initial CAD scope: revisions 01â€“03

The following table and observations describe the initial placement studies, not the current integrated MC. Their original native files, source review and DRC records remain historical evidence. Later integration and partial routing are recorded above.

| Study | Current physical review content | Important boundary |
|---|---|---|
| MC motion card | 70 FPGA-core component candidates, 411 pads, 214 represented nets | Proposed IS-1 220 Ã— 100 mm card envelope; not a complete motion card |
| Dual-watchdog circuit | 22 component candidates, 68 pads, 18 represented nets | Separate unintegrated circuit on a provisional 60 Ã— 45 mm review canvas; not an adopted product module |

MC imports 68 footprint assignments from the electrical source and makes **two placement-only** assignments for U1 and Y1. Their pad numbering/body geometry was independently checked in [the source review](../../reports/board-cad-20260930/SOURCE_REVIEW.md); their source schematic/BOM assignments remain unchanged. Logical boundary symbols are recorded but have not been turned into fabricated connectors. All fitted native-board pad nets round-trip against the source netlists. No copper tracks, planes, vias, stackup qualification, final connector placement, mounting holes or fabrication exports exist here. The study's 1.6 mm thickness is an explicit assumption.

The MC's card-local power, identity, Ioff buffering, final permission/self-test circuits and connector allocation remain incomplete. The watchdogs are not integrated into MC; their known startup and conditioning issues remain open. Other controller cards and the passive wiring base have no new board layout in this delivery. The historical six/two runtime and required eight/twelve product scope remain distinct from CAD placement evidence.

The top view shows every imported footprint. Installed 3D models cover **68/70 MC parts** and **20/22 watchdog parts**. The native 3D render omits the body models for MC U1/Y1 and watchdog U1/U2; their actual pads remain present. The viewer states these omissions explicitly rather than inventing package heights.

Native DRC ran on revision `20260930-03`: no other reported rule violations, but **197 MC and 50 watchdog unconnected items** remain. This is an **unrouted DRC result, not a DRC pass or manufacturing approval**. Schematic parity, board-level electrical completeness and physical measurements are not established by this review. Raw native reports and independent placement review are under `reports/board-cad-20260930/`.

The [independent native placement QA](../../reports/board-cad-20260930/PLACEMENT_QA.md) checks source pin sets, pad nets, manifest geometry/hashes and conservative pad/component/courtyard envelopes. It found no intersecting or outside checked envelopes. Watchdog U1/U2 have **no source courtyard shapes**, so their courtyard check remains incomplete. The native study files use KiCad's default two copper layers; that is a review-file default, **not** the selected production stackup.

## Updating the view as engineering changes

For a routed candidate, preserve the prior published native copper and compare both source-pin/net parity and actual physical connectivity before publishing. `tools/publish_routed_board_review.py` publishes a reviewed routed board under a new unique revision, with optional staged placement inputs, fresh native DRC/render and a publication receipt. The builder example below remains the placement-study workflow; rebuilding placement alone is not a substitute for preserving and verifying existing routed geometry. Do not report the capped native unconnected list as an uncapped routing total. Keep the independent all-net inventory synchronized with the actual published board hash.

1. Update the electrical circuit through its existing generator/review workflow, preserving the user sources and machine configurations.
2. Update `placement.json` with reviewed positions, allocations or placement-only footprint candidates. Keep physical quantities and omitted circuitry explicit. The native studies are separate from any future production routed board, and archived native files remain editable in KiCad.
3. Build a **new unique revision** with KiCad's bundled Python. The builder refuses to overwrite a revision, imports source pad nets, verifies native save/reload and source integrity, compares component geometry/content with the preceding published revision and atomically publishes `board-view.json`. Differences and unchanged engineering focus receive distinct reasons.
4. Render both new native boards and save fresh DRC reports. Review geometry/footprint assignments and record remaining violations. The viewer updates in the same browser panel; previous revisions stay selectable.

Example from the project directory, replacing the revision and label with the actual new increment:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' tools/build_board_review.py --revision 20261001-01 --label 'Describe the actual engineering change'
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' pcb render --output hardware/board_review/revisions/20261001-01/motion-card-3d.png --width 1600 --height 900 --background opaque --rotate '-35,0,0' --zoom 1.5 hardware/board_review/revisions/20261001-01/motion-card-placement.kicad_pcb
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' pcb render --output hardware/board_review/revisions/20261001-01/watchdogs-3d.png --width 1200 --height 900 --background opaque --rotate '-35,0,0' --zoom 1.5 hardware/board_review/revisions/20261001-01/watchdogs-placement.kicad_pcb
```

Restart the local viewer server after a reboot if needed:

```powershell
python -X utf8 tools/serve_board_review.py --port 8788
```

Published history: `20260930-01` initial placement; `20260930-02` readable native labels/custom-library portability; `20260930-03` change-comparison metadata; `20260930-04` integrated 203-part MC; `20260930-05` placement/local-power geometry review; `20260930-06` partial copper; `20260930-10` integrated 327-part MC partial copper; `20260930-12` historical r0.3/active-cap partial routing; `20260930-14` current r0.4, exact oscillator source assignment, custom courtyards, tube-packaged supervisors and strict native review retaining all 673 copper items. The manifest's revision selector is the published-history authority; unpublished staging directories are separate evidence. The interrupted `20260930-01-build-incomplete` directory remains excluded from the viewer. No listed revision establishes a finished controller or fabrication approval.
