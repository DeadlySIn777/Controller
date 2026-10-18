# Argus routing handoff — ROOT104 / CAD30

Open `native/motherboard-native-candidate.kicad_pro`, then its PCB in KiCad 10. Work on an extracted copy of this bundle and return the native `.kicad_pcb`, matching `.kicad_pro` and `.kicad_dru`, route/change log and validation reports. The source schematic is the separate `native/source-inputs/motherboard.kicad_sch`. Keep both native directories intact. This is an engineering routing package, not fabrication data.

`ARGUS_PROMPT.txt` contains the routing brief. This package makes no assumption about which Argus product or import formats you use. It has not been uploaded anywhere.

## Exact starting point

- Adopted Source26 / ROOT104, published CAD30. PCB SHA-256: `70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc`.
- 2,688 footprints; 11,807 existing tracks/vias; 1,544 zones/rule areas.
- **3,508 required joins remain**, across 1,101 incomplete multi-pad nets. Another 633 multi-pad nets are fully joined. Native and independent uncapped counts agree; zero orphan copper.
- Native regular DRC: 0 errors / 0 warnings / no ignored checks. Connectivity is a separate failing completion gate. Source26 ERC: 0 errors / 70 unsuppressed, documented warnings.
- 460 × 340 mm; six copper layers; provisional 1.6 mm stackup. Exact fabrication stackup and process are unqualified.
- Scoped existing evidence: 120 owned bypass loops, 245 receiving returns, 188 Source-anchored filled reference resources. These are local proofs, not whole-board qualification.

## Preserve and route

Preserve all existing component identities, pad nets, placement, outline, cutouts, zones, net classes, custom rules and retained copper for the initial additive pass. Lock retained copper in the routing tool if needed. **No lock flags were changed in this byte-identical handoff.** Do not use global rip-up, automatic part movement, footprint regeneration or schematic-to-PCB updates without an explicit, reviewable change ledger. Necessary controlled corrections belong in a separate candidate so retained proofs can be rerun rather than silently discarded.

The previous reviewed unattended autorouting subset is supplied under `evidence/reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-allowlist-r04/`. It has 27 unfinished low-speed GPIO/configuration/visual nets on its ROOT103 baseline; it is a starting scope review, **not approval to autoroute every remaining net**. Rebind it to this exact ROOT104 board before use. Critical power, FPGA escapes, clocks, SPI/CNC3, STEP/DIR/enables/alarms, encoders, analog, watchdog/permission and high-current paths require controlled routing with their own current/timing/return constraints.

For new ordinary signal routing use the reviewed 0.20 mm minimum track width and 0.60 mm via diameter / 0.30 mm drill, with the actual project clearances. Existing explicit small-via and BGA neck exceptions are retained exceptions, not blanket permission to use those dimensions elsewhere. Power widths and layer changes require their actual circuit current and return analysis. Do not join separate ground/field domains or route over broken/unanchored references. Retain source-anchored return paths and verify signal-via return connections, not just matching net labels.

## Known changes and limitations to account for

**Source27 reset/health corrections are staged and are not included in this board.** Do not treat Source26 as electrically frozen for fabrication. The included `source27-successor-rebinding-plan-r02.json` identifies U11032.6 and U11034.6 CLR changes, revised conditioning identities and ten added parts. Its separately staged placement/routing is unadopted. Keep the motor-feed reset/health region available for reconciliation; avoid spending a final cleanup pass there before that merge. Do not import an older Source27 board over this current board.

There are **277 same-net paste-land/drill intersections involving 274 existing drilled vias**. No foreign-net intersections were found in that audit. This is a lower bound excluding tangency and registration margins. They need controlled layout repair or a specifically qualified filled/capped process; tenting and zero ordinary DRC errors do not resolve them. Do not add new unqualified via-in-pad geometry.

A prior Freerouting session contains no new routing; its native donor has **zero copper**. That donor and session are deliberately absent from this bundle. Always start with the native ROOT104 PCB above.

Complete hardware 20 ms inhibit/startup/missing-module proof, full power/analog/thermal/interface/mechanical validation, exact FPGA vendor fit/timing and manufacturing outputs remain open. Routing completion does not close those gates. Report-local RTL optimization has progressed separately; its coarse resource estimates are not a vendor fit or a change to this board's pin allocation.

## Returned-candidate acceptance

1. Compare the returned board with this exact baseline: source/pad nets, footprint geometry/poses, all existing copper, zone definitions/fills and project rules. Account individually for every required correction.
2. Refill and run native KiCad ERC/DRC without new suppressions. Recompute independent uncapped physical connectivity against the actual Source26 or explicitly reconciled successor. No removed features, fabricated NCs or disconnected required nets.
3. Recheck all retained source clusters, bypass loops, literal return corridors/annuli and global reference checks; review new and inherited drill/land geometry, actual power paths and current capacities.
4. Rerun affected regressions after material changes and the full suite before adoption. Prior unchanged-board evidence is 25 PASS / 9 BLOCKED / 1 physical NOT_RUN / 0 FAIL, with 1,895 host and 238 native cases passing; it is not a test of returned routing.
5. Return exact counts, remaining problems and native files. Generate final Gerbers/drills/assembly outputs only after the actual manufacturing gates close.

`SHA256-MANIFEST.json` verifies all payload files except itself. `origin-map.json` maps packaged snapshots back to original workspace paths. Included receipts retain their historical paths and source hashes; this is not a standalone copy of the entire regression toolchain. Global stock KiCad library resources may still use the standard KiCad 10 installation. Custom footprints and both project-local 3D models are included and resolved during packaging.
