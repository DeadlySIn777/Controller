# Live board CAD review

30 September 2026. User-requested physical design view, backed by editable native KiCad placement files. Open `http://127.0.0.1:8788/index.html` in the Codex right panel while the local review server runs. It serves only this review folder on loopback; it does not connect to a machine or require an online service.

The viewer offers top CAD, native KiCad 3D renders, pan/zoom, component search, source part and pin-net inspection, highlighted changes/review focus and a revision selector. It polls the published manifest every three seconds. A newly published revision updates the latest view; an intentionally selected old revision stays visible until the user selects the update. The server does **not** regenerate CAD when schematics change: the engineering update procedure below publishes that change.

## Current published revision: 20260930-14

The live manifest shows **MC r0.4**, with **327 source component candidates, all 327 footprint assignments in source, zero placement-only assignments, 317 3D models, 1,229 fitted pads, 382 represented nets and 673 tracks/vias** (643 segments and 30 vias). Five connected source groups cover the FPGA core, local rail generation/supervision, conditioned dual TPS3851 watchdogs, permission logic and motor/TX Ioff buffers. The [native routed candidate](revisions/20260930-14/motion-card-route-candidate.kicad_pcb), its [publication receipt](revisions/20260930-14/publication.json) and [DRC report](revisions/20260930-14/native-drc.json) remain editable, inspectable records. The [fresh native/source review](../../reports/board-completion-20260930/mc-integrated-r04/review.json) freezes 105 unchanged inputs; ERC is zero with `ignored_checks: []`.

The [fresh independent all-net inventory](../../reports/board-completion-20260930/mc-integrated-r04/fresh-native-routing-inventory/review.json) checks fitted source pins and physical copper clusters: **106 of 203 multi-pad nets are fully joined; 97 are incomplete, with 711 uncapped missing joins**. It records 106 declared native NC pads and no orphan copper. Fresh native DRC has **zero regular violations with `ignored_checks: []` and 499 unconnected items at its report cap**. All five normally ignored checks are explicitly enabled; no missing courtyard is hidden. The 499 capped report and the uncapped 711 physical count measure different scopes; neither is a pass or proof of full routing. Missing circuits/connectors are not treated as NC or completed interfaces.

[The custom courtyard closure](../../reports/board-completion-20260930/courtyard-closure/README.md) preserves all pads and copper while adding manufacturer-maximum body/copper envelopes with 0.25 mm allowance to nine footprints; its native review has no overlap pairs. [The exact ASE oscillator promotion](../motion_card/oscillator-footprint-promotion.json) places Y1001's assignment in parent source. The 317 model count includes review geometry and does not qualify mechanical clearance, assembly or package-height accuracy of the whole unit. Earlier revision-12/r0.3 and initial-CAD records remain historical.

The proposed **220 × 100 mm**, **six copper layers** and **1.6 mm thickness** remain layout assumptions. Planes, power-loop/BGA routing, other boundary Ioff paths, identity/presence/status/restore functions, upstream bank-B qualification and powered receiver enable bias, P1/P2 footprints/contact allocation and mating/cage geometry remain unfinished. GPIO/vendor FPGA fit, loaded timing, thermal/EMC and physical bring-up remain unqualified. There are **no fabrication outputs** and `manufacturing_ready: false`. The board is a partially routed MC candidate, not the complete controller.

The parent [replacement ledger](../motion_card/component-substitutions.json) retains the active bypass change and now records three exact H-grade LTC2962HUD#PBF tube devices in place of #TRPBF reel packaging, with unchanged circuitry and pads. [Current r0.4 cost](../../reports/board-completion-20260930/mc-bom-cost-r04/MC_BOM_COST.md) prices 42 of 52 MPNs (40 demand-matching/two MOQ-constrained); ten are null. Catalogue calculations are not available purchase baskets: 100-board supervisor demand 300 exceeds observed stock 71 by 229, and stock-covered/manufacture/controller totals remain null. The [old r0.3 sheet](../../reports/board-completion-20260930/MC_BOM_COST.md), including its reel MOQ, is historical. [Fresh post-r0.4 host checks](../../reports/board-completion-20260930/post-r04-host-validation/README.md) report 869 full-suite cases (864 passed/five Windows symlink skips) with 1,272 unchanged source/research hashes; focused eight-envelope and 16-integration sets are included in that full count. The user's newer one-custom-PCB direction conflicts with frozen IS-1's custom-card allocation and confirmed service/expansion boundaries; clarification remains pending. The CM4/CM5 dual-100-pin bay does not settle removable FPGA/I/O or eight-plus-four topology. No compute/ESP module is fitted to this MC.

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
