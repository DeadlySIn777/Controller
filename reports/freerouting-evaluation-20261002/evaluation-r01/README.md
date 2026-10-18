# Freerouting evaluation — 2 October 2026

**Actual duplicate-board trials and native import completed; no Freerouting copper accepted.** The current board remains ROOT104/CAD30, with 3, 508 required joins. Its 13-join improvement came from separately controlled routing, not Freerouting.

The test base is the exact ROOT103 board with 11, 759 copper objects. Protected source pads, placements, existing copper and manufacturing rules remain immutable. Power, FPGA escapes, clocks/CNC3/SPI, motor and encoder paths, analog, watchdog and permission routes were excluded from autorouter goals.

| Trial | Actual result |
|---|---|
| Initial visual run | Rejected startup/configuration attempt; retained. |
| Original whole-board visual export | 900-second timeout, no session. |
| Convex full-board export | Independently covered every protected obstacle; 900-second timeout. |
| Convex export with bounded fanout | 900-second timeout; no session. Its 0.50 mm fanout search setting was inconsistent with ordinary 0.60 mm vias and was corrected in the successor, without changing native acceptance. |
| Legal polygon/window full-board export | Independent zero-undercoverage proof passed; 900-second parsing timeout, no session. |
| Local 30×30 mm protected window | Parsed and ran four passes in 113.21 seconds. Wrote a real SES; both selected joins remained unrouted. |
| Same local window, diagnostic one-pass run | 33.02 seconds; exactly the same SES hash and zero new routing. |

The complete initial reviewed low-speed inventory contained 64 rows, of which 27 nets had 48 unfinished joins. That does not mean all 3, 521 baseline joins were eligible for autorouting. The local workflow test selected only OBS8_INVERTED and OBS9_INVERTED and all four of their actual Source pads.

The initial KiCad filled-zone export contained 110 fractured contours unsuitable as simple polygons. Successive report-only transformations retained conservative coverage. The final local export contains 5, 247 convex objects; independent reconstruction proves coverage of all 7, 053 original obstacles with no area tolerance. Space outside the local region is deliberately blocked. Native board geometry was never cropped or changed.

## Native import result

The strict importer rejected the actual session with `Session contains no new approved route geometry`. The SES network output is empty. Its native donor and no-route placement control both have zero copper: protected netless copper was omitted by the writer. **The donor must never replace the original PCB.** The additive workflow retains the exact original 11, 759 copper objects and accepts only separately validated additions. None existed here, so no candidate was emitted and no complete candidate regression was warranted.

Freerouting’s 51, 088 diagnostic violations belong to the restricted exported model. They are not KiCad DRC results and have not been established as the cause of the routing failure. Independent endpoint checks show that the four pad centers and outward F-layer escape envelopes are clear of polygon/reference-void blockers; complete native-metal path access remains under investigation.

One export-rule discrepancy was found: ordinary classes offered 0.50/0.20 mm and 0.40/0.20 mm vias as well as the required 0.60/0.30 mm. The importer rejects unauthorized new sizes. Future exports must restrict new route choices while retaining existing small-via padstack definitions. No new via was returned in these trials.

The current ROOT104 board has native regular DRC 0 errors/0 warnings, zero orphan copper, and native/independent agreement on 3, 508 required joins. Its separate fresh full r08 run reports 25 PASS, 9 BLOCKED, 1 physical NOT_RUN and 0 FAIL. Neither the controller nor the manufacturing package is complete.

Official configuration reference: [Freerouting 2.4.1 RouterSettings](https://github.com/freerouting/freerouting/blob/v2.4.1/src/main/java/app/freerouting/settings/RouterSettings.java). Exact local receipts, tool hashes, failed attempts and unchanged-input witnesses are retained beside this report.
