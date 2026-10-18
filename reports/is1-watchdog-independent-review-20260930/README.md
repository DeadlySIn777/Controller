# Independent final standalone-watchdog review

30 September 2026. The final `is1-watchdogs-r0.1` source and actual native circuit artifacts were reviewed without editing the block, its tests, frozen IS-1 or the connected assembly. Twenty-nine examined files are copied under `source/`, with SHA-256 bindings in `review.json`. The capture verifies that the examined originals did not change during review; it refuses to overwrite the completed receipt.

The manufacturer's physical package functions match independently reviewed manual fixtures, without importing builder/validator expectations:

| Part / native symbol | Reviewed physical functions |
|---|---|
| TPS3851 / DRB8 | VDD1, CWD2, MR3, GND4, SET1 5, WDI6, WDO7, RESET8; grounded exposed pad represented as pad9 |
| SN74LVC1G34 / DBV5 | NC1, A2, GND3, Y4, VCC5 |
| SN74LVC2G17 / DBV6 | 1A1, GND2, 2A3, 2Y4, VCC5, 1Y6 |

All five ICs' actual native conductors match the reviewed functional wiring. Both timers have explicit MR no-connects; their RESET and WDO pins share their own health node, with no cross-channel coupling. Separate rail buffers connect progress_M/O to WDI, and separate Schmitt channels return WD_M/O_OK. The DRB copper pad order follows TI's top-view pin order, and its exposed pad is grounded. No physical pin-map mismatch was found in this scoped review.

The native design contains **22 physical parts**, one unfitted internal boundary, **14 connected nets plus four no-connect nets**, and five ICs. It has no fitted field connector or full permission chain. Manufacturer sources for the physical tables and timing capacitor were read directly from retained TI/Samsung primary material; the T20 source was separately examined for reset/configuration states. Primary-source bindings are also recorded in `primary-source-sha256.json`.

Recorded native KiCad 10.0.4 ERC contains zero violations, with errors, warnings and exclusions covered and four inherited suppressions recorded. The final read-only validator was independently rerun with `--check`; it passed and wrote no block files. `validator.stdout.txt`/`validator.stderr.txt` record that actual run. The implementer reports **31 narrow mutation tests passing** in `reports/next-implementation-20260930/IS1_WATCHDOG_BLOCK.md`; this review did not rerun those tests, regenerate native ERC or claim physical measurements. The standalone schema correctly sets manufacturing readiness, assembly integration, physical qualification, complete permission chain and startup default qualification to false.

The principal unresolved finding is the **T20 weak-pull-up versus 100 kΩ default-state conflict**. Its source evidence, exact SET1/WDI distinction, 1 kΩ/1.8 kΩ screens, loaded-current costs and CDONE-containment limits are in `DEFAULT_STATE_SCREEN.md` and reproducible arithmetic is included in `review.json`. The implementation now explicitly records the conflict; documentation of it is not an electrical solution. It remains an integration blocker and requires a versioned interface/default-conditioning revision, without silently changing frozen IS-1.

Further limits are material: SET1 driven-low margin depends on a checked LVCMOS33 configuration; the 1.8 V-class G18 supervisor cannot qualify a 3.3 V rail by itself; the health node's guaranteed low margin at actual supply/loading, partial-power/brownout behavior and final permission receivers remain open. Timed WDO/RESET pulses do not implement sticky deliberate re-arm latches. Progress pulse firmware and self-test containment are not implemented by this circuit drawing. TI's nominal 150 µs SET1 setup value does not establish a guaranteed complete startup/self-test bound. CWD leakage/temperature/cleanliness, measured ≤20 ms fault-to-inhibit, whole-machine response, routing, thermal/paste/stencil design and manufacture remain unqualified.

This is useful new circuit implementation, separate from the historical single-watchdog machine-permission block and the connected assembly. It is not a controller release. Root owns the connected evidence package and final overall audit/rating.
