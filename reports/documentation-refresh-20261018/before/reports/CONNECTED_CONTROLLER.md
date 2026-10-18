# Connected controller circuit review

**30 September implementation after the audit:** the reset-buffer physical pin map is now corrected and propagated into this connected assembly, including its native netlist and drawing. The [scoped reset repair](reset-pin-fix-20260930/README.md) and [new implementation package](next-implementation-20260930/README.md) distinguish the repaired sources from the unchanged audit. The historical permission block in this assembly still misses the retained 20ms external watchdog requirement; the separate IS-1 dual-watchdog candidate is not yet integrated with complete permission/self-test logic. Expanded power/full-I/O/modular-product gates remain open. The earlier 291-test/49-check processor snapshot and [audit findings](audit-2026-09-30/HARDWARE_AUDIT.md) remain preserved; passing source, host or ERC checks is not electrical or manufacturing qualification.

29 September 2026. Thirteen editable KiCad circuit blocks are now assembled in one hierarchical review project. The project connects the actual source netlists and preserves the historical six-joint/two-encoder work as a baseline; it does not claim a complete eight- or twelve-channel machine controller, a production PCB or a PCBWay release.

Open [controller_assembly.kicad_pro](../hardware/controller_assembly/controller_assembly.kicad_pro) in KiCad. The [root schematic](../hardware/controller_assembly/controller_assembly.kicad_sch), [combined drawing](../hardware/controller_assembly/controller_assembly.pdf), [netlist](../hardware/controller_assembly/netlist.xml), [assembly map](../hardware/controller_assembly/assembly-map.json), [review BOM](../hardware/controller_assembly/review-bom.csv) and [validation](../hardware/controller_assembly/validation.json) describe the same regenerated source snapshot.

## Current connected scope

| Block | Connected review scope | Boundary still open |
|---|---|---|
| Power entry | Separate protected core/field paths, physical fuse positions, reverse blocking and diagnostics | Fuse/source coordination, surge and clamp selection |
| Core converter | LM70660 5 V candidate, sensing, storage and compensation candidate | Stability, thermal, transient and expanded-current qualification |
| Logic power | Separate 1.2 V, 3.3 V and ESP 3.3 V candidate branches | Ramp, transient, PDN and compute/display load qualification |
| Field power | Fixed 5 V field-side candidate buck | Full field load and fault behavior |
| Encoder power | Two independently limited 5 V branches | External encoder compatibility and response |
| Twelve-channel transmitter | Six AM26C31 banks, all twelve differential STEP/DIR pairs, permits and default pull-downs | Twelve complete channels need enable/alarm stages, line protection, timing and power qualification |
| ABZ receiver | Two populated differential receiver groups and reserved expansion boundaries | Full encoder population, protection, calibration and timing |
| SBC power | Delayed supervised 5 V computer branch | Exact CM4/CM5/CB2 carrier, screen tiers, warm reset and current qualification |
| Power sequence | Independent rail windows, core-before-I/O ordering and separate FPGA/ESP reset paths | Precision-monitor cost, reset handoff and partial-power tests |
| Digital inputs | Twenty-two isolated input channels with distinct substrate returns | Field-voltage range, EMC and machine-level qualification |
| FPGA core | T20F256 candidate pin allocation, flash, clock, configuration reset, separate post-CDONE user reset and twelve STEP/DIR capacity | Efinity fit/timing/bitstream, PCB/PDN, physical package and complete motion I/O |
| Machine permission | Watchdog, CDONE/reset/interlock AND path, async arm-latch clear and final transmitter permit | Physical timing, stopping response and independent machine safety remain unqualified |
| ESP service | ESP32-S3 service/reset/USB/UART diagnostic boundary with no motion authority | RF/USB/partial-power tests and production firmware |

Only explicitly named nets cross sheets. `LOGIC_GND` and `FIELD_GND` remain separate. `EXT_PERMIT_3V3` is deliberately aliased to `PROTECTIVE_STATUS_FPGA` inside the machine-permission block; this is a fixed active-high hardware reservation, not a configurable software mapping and not a safety certification.

The FPGA candidate now distinguishes `FPGA_LOCAL_RESET_N` (configuration reset) from `FPGA_USER_RESET_N` (CDONE-qualified delayed user-logic reset). The latter uses a 10 kΩ/1 µF candidate RC and a Schmitt buffer/AND gate; the time and threshold are not guaranteed. The permission gate independently removes transmitter permission on reset, CDONE loss, watchdog fault or protective interlock. The connected RTL bench exercises the separate user-reset hold, but uses ideal digital gates and explicit watchdog fault injection; it does not model the analog circuit or physical stopping distance.

## Evidence and limits

Native KiCad export of the regenerated project reports zero ERC errors and the same twenty-two explicit ISO1212 floating-substrate warnings. The independent assembly validator and focused assembly tests pass, including all twelve STEP/DIR unions, reserved interlock alias, configuration reset path and source identity. The independent FPGA validator passes its 26 mutation tests and the permission RTL bench passes 49 checks. These are source inspection, host tests, HDL simulation and circuit ERC results. They are not PCB DRC, vendor FPGA synthesis/fit, real-time twelve-channel runtime, power measurement, EMC, thermal, machine stopping or industrial certification evidence.

The expanded-power screen shows the old 6 A CORE_5V path is exceeded by steady-state twelve-motor arithmetic and by eight-motor startup cases. A redesigned higher-current rail or separately protected transmitter rail must be costed and qualified; the existing six-channel power result cannot be relabelled as the new product result. See [expanded power review](EXPANDED_POWER_REVIEW.md).

The screen catalogue remains independent of I/O: 7-, 10-, 12-, 14-, 18- and 21-inch classes are separate compute/display/package choices. Ordinary drives, displays, relays, adapters, VFDs, cables and power accessories remain customer-sourceable compatibility items; a complete kit is a convenience/integration/support offer. Paid offline software licensing, module replacement continuity, published compatibility records and third-party licence obligations are recorded in [the commercial policy](../docs/COMMERCIAL_MODEL_AND_LICENSING.md).

## Remaining release gates

1. Freeze the compute carrier and exact display/package variants after complete cost and thermal/load comparison.
2. Complete eight-motor standard and twelve-motor expansion electrical channels, including individual enables, alarms, field protection and protocol capacity.
3. Resolve the expanded power tree, AM26C31 partial-power behavior, field-output protection and all connector/footprint choices.
4. Run Efinity package fit/timing/bitstream, full PCB layout/DRC, PDN/thermal/EMC and physical fault/recovery tests.
5. Implement and qualify production LinuxCNC/FPGA/ESP firmware, offline licensing, module identity/replacement and customer-supplied peripheral compatibility.
6. Produce complete fitted BOMs, replacement-card costs, screen-tier kit costs and a PCBWay turnkey quotation only after those prerequisites pass.

No machine was connected, firmware flashed, hardware ordered, supplier contacted or fabrication release made by this review.
