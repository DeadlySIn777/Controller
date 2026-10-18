# MC local buck routing review — 30 September 2026

The current candidate is [routed-v2/motion-card-power-routed.kicad_pcb](routed-v2/motion-card-power-routed.kicad_pcb). It routes ten reviewed local converter connections with **24 native F.Cu track segments** on a separate PCB copy. [routed-v2/route-bundle.json](routed-v2/route-bundle.json) contains the integrated and original reference identities, native net names, UUIDs, exact endpoints and widths for merging into the combined PCB. The original revision-05 board, all circuit sources and the live viewer are unchanged by this tool.

## Checks performed

- [Current review](routed-v2/review.json): PASS. All seven hashed source inputs remained unchanged during the run and were copied under `routed-v2/source/` with matching hashes.
- All ten pairs fail the geometric native-connectivity check on the unrouted board and pass it on the saved/reloaded routed copy. Assigned net names alone are not used as evidence of electrical contact.
- All 24 track UUIDs, start/end coordinates, widths, layers and net identities survive native save/reload. Coordinates permit at most 2 nm conversion tolerance; no practical clearance is relaxed by that tolerance.
- [Baseline native DRC](routed-v2/baseline-drc.json) and [routed native DRC](routed-v2/routed-drc.json) both report **zero violations and 499 unconnected items**. The partial board remains globally unconnected; the unconnected count is reported as observed, not used to claim ten completed nets or a completed board.
- [Separate clearance negative control](negative-control/review.json): PASS. Widening one 0.2 mm RPJ SW pad escape to 0.6 mm on another copy causes three native clearance violations involving that track. The accepted routed copy remains unchanged. This exercises actual native clearance enforcement.

## Selected copper and limits

Each regulator has one short SW-to-inductor path, one inductor-to-local-output-capacitor path, an independent VOS-to-output-capacitor sense path, one VIN-to-input-capacitor path and one paired input-capacitor return. The existing pad-backed placement derives from [TI TPS62901 layout guidance, page 41](https://www.ti.com/lit/ds/symlink/tps62901.pdf); ADI precision-supervisor Kelvin/layout guidance remains recorded in the placement source.

The small RPJ package escapes and VOS connections use 0.2 mm width. SW/VIN/input-return copper widens to 0.4 mm outside the package; inductor-to-output-capacitor paths use 0.6 mm. These are provisional geometry choices under the current 0.15 mm clearance / 0.2 mm signal proposal. They **do not establish current capacity, thermal behavior or production stackup approval**.

No planes, vias, fabrication outputs or new ratings were added. Low-inductance output-capacitor returns, complete power distribution, thermal copper/vias, measured-load Kelvin sense/return, connectors and the rest of the motion card still need layout. Six copper layers and 1.6 mm thickness remain review assumptions. Physical startup, loaded reset, fault timing, thermal and EMC measurements remain outstanding; manufacturing is blocked.

The tool is `tools/hardware_route_mc_power.py`, run with KiCad's bundled Python. It refuses output into the hardware tree, output over an existing evidence directory, a base with planes, pre-existing selected connections, changed placement coordinates or mismatched circuit/native pad nets. Run with a fresh `--output` directory for a new candidate. `routed-v1` is the earlier same-geometry result before the explicit unrouted-connectivity negative control was added; the top-level `baseline-drc.*` files are from an interrupted initial hierarchy-net-name check before any tracks were saved.
