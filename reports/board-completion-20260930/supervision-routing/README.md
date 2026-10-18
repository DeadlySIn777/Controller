# Eleven supervision joins — native copper review

Current accepted review candidate: [manual-v5/motion-card-supervision-routed.kicad_pcb](manual-v5/motion-card-supervision-routed.kicad_pcb). [Review receipt](manual-v5/review.json) is PASS. [Route bundle](manual-v5/route-bundle.json) provides exact removed-item, replacement-item and added-route geometry for controlled integration into a later board.

The input is immutable revision 06, containing 203 fitted components, 867 physical pads and 296 track/via items. Its 41 selected supervision nets had eleven missing physical cluster joins. The candidate connects **all 41 selected nets in one physical copper cluster per net**, reducing the uncapped native unconnected-edge count from **508 to 497**. Other nets and interfaces remain incomplete; this is not a fully routed controller.

## Actual changes

The eleven joins are WD_M_OK, WD_M_SET1_BUF, WD_O_OK, WD_O_SET1_BUF, ARM_O_Q, PERMIT_OUT_DRIVE, PERMIT_OUT_REQ, TAMPER_CLEAR_N, WD_M_TRIP_CLEAR_N, WD_M_TRIP_Q and WD_M_HEALTH_RAW. The bundle identifies their actual pad endpoints and native geometric copper members.

294 original routing items remain exactly unchanged. Two short F.Cu WDI segments near U3001 are removed and replaced with four segments on the same net, `/watchdog_conditioning/WD_M_WDI_BUF`. This bounded local change opens the previously enclosed HEALTH pad cluster while preserving complete WDI physical continuity. The exact two removed UUIDs/coordinates and four replacement UUIDs/coordinates are retained in the bundle and receipt. No published revision or source board is changed.

The eleven joins add 73 track/via items; the WDI replacement adds four. Final count is **371 items**: 294 retained plus 77 added. All new signals use 0.2 mm tracks and 0.6 mm diameter / 0.3 mm drill through vias, giving a nominal 0.15 mm annulus. There are no microvias, buried vias, new planes or changed electrical net assignments. Inner signal-layer assignments use the existing six-layer review candidate and remain subject to complete stackup/reference-plane review.

## Evidence

- Native DRC reports **zero regular violations and 497 unconnected items**. At this count the report is below KiCad's 499 unconnected-category ceiling; the independent native geometric count is also 497. The baseline's capped report of 499 corresponds to its actual 508 uncapped count.
- `GetConnectedItems()` is used for actual geometric clusters, independently of assigned-net membership. All source pads in each of the 41 selected nets belong to one cluster; no orphan copper cluster without a source pad remains.
- All 867 pad positions, sizes, drills, orientations, layers and assigned nets are exactly preserved through native save/reload. Every retained or added track/via item's native identity, geometry, width, layer set and net also remains exact.
- Removing only the newly added ARM_O_Q join copper in an unsaved control restores physical disconnection without changing pad net labels and increases the uncapped count to 498. The accepted PCB stays unchanged.
- All five recorded original inputs stayed unchanged during verification and are copied under `manual-v5/source/` with matching hashes. The routed PCB's saved SHA-256 matches the receipt.

## Boundaries and reproducibility

Run `tools/hardware_route_mc_supervision.py` using KiCad's bundled Python and a fresh `--output` report directory. The tool requires the exact revision-06 scope, rejects changed pad endpoints or pre-existing joins, preserves the original input, copies its project/library context, saves and reloads the candidate, runs native DRC and retains physical-cluster evidence. The two-segment local WDI replacement is explicit; other original copper cannot silently disappear.

`manual-v1` and `manual-v4` are retained failed clearance candidates. `manual-v2` and `manual-v3` contain interrupted native-wrapper runs before a completed board/receipt. Only **manual-v5** is the current PASS candidate; the escape-suggestion JSON files are preliminary screens, not accepted routes.

This closes selected supervision routing only. Power/reference planes, BGA escape, complete rail/sense distribution, all remaining interfaces, the full card and assembled controller, vendor stackup/process approval, signal/fault timing, thermal/EMC measurements and fabrication release remain unfinished. No fabrication files or manufacturing-readiness claim follow from this receipt.
