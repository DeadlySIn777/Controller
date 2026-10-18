# ROOT104 prototype readiness — 2 October 2026

**Not ready for manufacture.** The working PCB and published CAD30 have identical bytes. This is a verified routing increment, not a completed prototype package.

| Item | Exact current result |
|---|---|
| Routing | 633 fully joined and 1,101 incomplete multi-pad nets; **3,508 required joins remain**. Native and independent counts agree. Zero orphan copper. |
| Native ERC | 0 errors; 70 unsuppressed, individually documented warnings. |
| Native regular DRC | 0 errors, 0 warnings, no ignored checks. Unrouted connectivity remains a separate failing completion gate. |
| Board | 460 × 340 × 1.6 mm; six layers; vendor stackup not qualified. |
| Files | Native PCB/project/rules, source schematic/netlist, designator BOM and current CAD render. **No final Gerbers, drills, production CPL or final assembly package.** |
| Partial consumed BOM at 1 / 10 / 100 | US$1,091.51 / $877.37 / $796.51. 185 exact MPNs and 720 purchased fitted pieces remain unpriced. Modules, screens and manufacturing costs are separate unknowns. |
| Fresh full validation | 25 PASS, 9 BLOCKED, 1 physical NOT_RUN, 0 FAIL; 1,895 host and 238 native cases pass, five Windows symlink skips. All 4,041 tracked inputs unchanged during the run. |
| Additional evidence | 2,048 fresh actual SPI fault trials; 18 reset/fault mechanics scenarios; bounded diagnostic IOL1 and read-only IS2 profile; 37 release-guard tests pass after canonical report serialization was corrected. |

The increment adds 48 controlled copper objects and retains every prior copper object, pad, placement and zone definition. Scoped proofs now cover 120 bypass loops, 245 receiving returns and 188 Source-anchored filled resources. A saved/refilled removal of the additions restores the exact prior copper and Source clusters with 3,521 joins. These checks do not constitute whole-board completion.

The whole-board Freerouting trials did not produce usable routed output within their bounds. A protected local-region trial produced a real session but reported both selected joins still unrouted; native acceptance is tracked in the separate Freerouting evaluation. No Freerouting copper is included in ROOT104.

## Engineering still required

- 3508 required joins; all power/return and critical interface routing must be completed.
- Source27 reset/health circuit corrections and current-loop/global-reference reconciliation are staged and unadopted. Full20ms inhibit and startup/missing-module behavior are not yet proven across the actual complete circuit.
- 277 paste-land/drill intersections across274 inherited vias require layout correction or specifically qualified filled/capped fabrication and assembly.
- Complete HAL/CNC3/provider integration,ordinary output authority,record identity/provisioning and all9 machine profiles remain unfinished.
- FPGA composed implementation exceeds the current coarse resource screen; optimization and exact vendor package fit/timing remain open.
- Full analog chain convergence,return-path/power/current/thermal/cable/load qualification,mechanical interference and manufacturing stackup/rules remain incomplete.
- Complete quoted costing,production fabrication/drill/CPL/assembly outputs and final independent reviews remain unfinished.

## External and physical gates

- Exact Efinity device/package place-and-route and timing need the vendor toolchain.
- PCB fabricator/assembler must qualify exact stackup,via process,assembly limits and complete turnkey quote before release.
- Assembled prototype validation is required for20ms inhibit,fault/default-safe behavior,signal integrity,EMI,thermal/current and electrical ratings.

Internal engineering gates remain; the remaining blockers cannot honestly be described as only purchasing or physical prototype tests. The one-custom-board architecture and existing source scope remain in place.
