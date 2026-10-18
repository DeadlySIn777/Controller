# Live board CAD review

30 September 2026. User-requested physical design view, backed by editable native KiCad placement files. Open `http://127.0.0.1:8788/index.html` in the Codex right panel while the local review server runs. It serves only this review folder on loopback; it does not connect to a machine or require an online service.

The viewer offers top CAD, native KiCad 3D renders, pan/zoom, component search, source part and pin-net inspection, highlighted changes/review focus and a revision selector. It polls the published manifest every three seconds. A newly published revision updates the latest view; an intentionally selected old revision stays visible until the user selects the update. The server does **not** regenerate CAD when schematics change: the engineering update procedure below publishes that change.

## Current published revision: 20260930-20

Published native CAD **20260930-20** contains the frozen **880-footprint / 878 fitted** snapshot, all source-backed. It preserves the original 327 footprints and all **1,907 track/via items and five filled zones**. Independent uncapped connectivity finds **1,637 missing joins**, 81 of 637 multi-pad nets fully joined, 556 incomplete, 3,317 numbered copper pads, 120 native NC pads and no orphan copper. Native DRC reports **zero regular violations, no ignored checks, 499 capped unconnected items**; this is a failing routing result. The **460 × 340 mm, six-layer, 1.6 mm** outline remains provisional; existing planes occupy the retained core region rather than completing the field/whole-board distribution.

The reconciled electrical source has **980 physical footprints: 960 purchased fitted parts, 18 bare PCB test pads and two DNP footprints**, across twelve source blocks. It includes all twelve motor interfaces, four ABZ receiving paths, 24 DI, 16 smart DO, power-health and actual I/O acquisition/control. Native integrated ERC is **zero errors, 94 warnings, no ignored checks**; 92 isolated-pin labels and two ground-name warnings remain explicitly unresolved. Independent native pin/MPN/footprint and bounded original-pin/topology checks pass, with **19 integration tests passed**. The 100 I/O-control footprints are not yet populated on the published 880-part PCB.

Complete protected entry/power distribution, module sockets, actual field terminals, probes/pendant/process/PWM, analog/comms, status indications and their routing/mechanics remain engineering work. The 20 ms requirement, partial-power behavior, target firmware, vendor FPGA package fit/timing and physical/EMC/thermal qualification are unproved. No Gerbers, drills, assembly CPL/drawings or final stackup have been released; manufacturing_ready remains false. The single active motherboard and all twelve onboard motor interfaces are resolved decisions; old thirteen-card/rack/cage/P1/P2/MX4/XTB requirements are superseded physical history.

The native [PCB](revisions/20260930-20/motherboard-populated-candidate.kicad_pcb), [publication](revisions/20260930-20/publication.json), [DRC](revisions/20260930-20/publication-drc.json) and [independent connectivity](revisions/20260930-20/publication-connectivity/review.json) are exact frozen source-backed engineering files. Boxes for modules/terminals are reservations, not fitted connectors. Previous revisions retain their original source, geometry and evidence.

The frozen **980-part source cost snapshot** prices 60 MPNs and leaves 34 unpriced (185 fitted pieces per board). Known-priced consumed component value per board at **1/10/100 units is US$379.67/$314.26/$280.60**, excluding unpriced parts, missing circuits, PCB/assembly/test and purchased compute/ESP/storage/screens. Catalogue cash includes MOQ excess and is not a stock-covered purchasing basket. Every complete manufacture/controller/package total remains null. Bare copper test pads have no purchased part or assembly placement.

## Historical initial CAD scope: revisions 01–03

The following table and observations describe the initial placement studies, not the current integrated MC. Their original native files, source review and DRC records remain historical evidence. Later integration and partial routing are recorded above.

| Study | Current physical review content | Important boundary |
|---|---|---|
| MC motion card | 70 FPGA-core component candidates, 411 pads, 214 represented nets | Proposed IS-1 220 × 100 mm card envelope; not a complete motion card |
| Dual-watchdog circuit | 22 component candidates, 68 pads, 18 represented nets | Separate unintegrated circuit on a provisional 60 × 45 mm review canvas; not an adopted product module |

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
