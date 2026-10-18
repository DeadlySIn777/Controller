# Motherboard FPGA allocation review — 30 September 2026

The existing **T20F256I4 has enough package pins for the standard twelve-motor/four-ABZ motherboard while retaining every currently allocated FPGA ball**. This is a complete source-reviewed candidate, not a vendor fit, a schematic change or a routed-board result. No parent KiCad, PCB or RTL file was changed by this review.

The primary result is [fpga-allocation-proposal.json](../../hardware/motherboard/fpga-allocation-proposal.json). Every candidate signal includes its ball, bank, manufacturer function, workbook row, VCCIO, direction, logical function, provenance, physical-net label, startup obligation and implementation status. The three CSV files provide the same assignments for review.

## Exact pool and inherited-budget correction

| Item | Actual count |
|---|---:|
| GPIO in the exact official T20F256 worksheet | 195 |
| Ordinary GPIO, including dual-purpose configuration pins | 141 |
| LVDS-resource GPIO, including the RX clock pair | 54 |
| Currently wired flash/configuration/strap GPIO kept reserved | 12 |
| Available user-function GPIO, **including the 50 MHz clock** | **183** |
| Currently allocated user pins | 96 |
| Current oscillator clock on H3 | 1 |
| Currently NC user GPIO | 86: 32 ordinary + 54 LVDS |
| REF_RES R2 | Separate non-GPIO, remains NC |

The old IS-1 `189 usable / 137 full-feature` arithmetic does not match the exact package with the current circuit reservations. The present configuration consumes P3, M3, N3, L3, N1, D7, C7, B8, R16, L14, K13 and L12. This review releases none of those twelve pads. The usable ordinary pool is consequently **129**, with another **54** LVDS-resource GPIO. The twelve reserved functions are listed individually in the JSON. Dedicated CDONE, CRESET_N and JTAG pins are also preserved and do not enter this user-GPIO pool.

## Reconciled logical inventory

| Function | Base pins | Optional pins |
|---|---:|---:|
| Twelve STEP/DIR/individual EN_N/alarm sets | 48 | 0 |
| Four ABZ encoders | 12 | 24 for ENC4–11 |
| FREQ, MPG A/B, probes, PWM and process contacts | 10 | 0 |
| XS1 machine-permission/status/feedback/lamp interface | 7 | 0 |
| Four local IOL1 ports and base fast-status register | 19 | 3 optional encoder-status wires |
| Host SPI including separate CS_FB and CS_CMD | 5 | 0 |
| Actual motor-bank PGOOD, hardware tamper aggregate and rail readback | 4 | 0 |
| OPI_TX/A/B/BOE/OUT readbacks and two rearm strobes | 7 | 0 |
| Progress M/O, motion/output requests and endpoint-ready | 5 | 0 |
| WD_M/O_OK and TX/OUT/PROC readbacks plus RAW_INHIBIT_N | 6 | 0 |
| Watchdog trip latches and deliberate clear | 3 | 0 |
| Clock and qualified user reset | 2 | 0 |
| Four retained critical fault observations | 4 | 0 |
| Input-only onboard-health register | 3 | 0 |
| Independent permission-contact request | 1 | 0 |
| Previously reserved accessory link/sync/clock resources | 6 | 0 |
| **Required logical total** | **142** | **27** |

The inherited 175-pin total becomes **169** after removing only seven nonexistent soldered-region rack contacts/identity straps and adding the actual asynchronous inhibit input that the old sum omitted. MIA/MX4 power-good becomes genuine MOTION_A/B_PGOOD. The hardware tamper/interruption aggregate and **every OPI domain remain**. The 3-wire old SSR interface becomes an input-only onboard-health register; its versioned bit layout must be implemented, rather than presenting fictitious rack cards.

Three field aliases already appear explicitly in the frozen terminal map:

| Current physical net and ball | Logical field function |
|---|---|
| PROBE_FPGA, G12 | PRB0_FPGA |
| TOOLSETTER_FPGA, G15 | PRB1_FPGA |
| PROTECTIVE_STATUS_FPGA, G16 | EXT_PERMIT_FPGA |

The existing motor-enable/progress/inhibit aliases are inherited from the MC assembly map. HOST_SPI_CS_N at B2 is the proposed CS_FB logical alias; CS_CMD gets a separate pin. Logical aliases consume the same pad once. They require the root's explicit native-net/service ledger before implementation; this report does not rename copper.

Nineteen other existing pad reservations remain outside the required IS-2 field inventory: twelve HOME inputs, DOOR_STATUS, SPINDLE_FAULT, SPINDLE_READY, FEED_HOLD, CYCLE_START, LUBE_STATUS and SPARE. Their pin cost is visible rather than silently discarded.

## Candidates and exact remaining capacity

| Candidate | Required with historical pads | Assigned | Unassigned | Free GPIO |
|---|---:|---:|---:|---:|
| [Base; preserve all current balls](base_preserve_all_current.csv) | **161** | **161** | **0** | **22** |
| [All optional resources; preserve all current balls](full_preserve_all_current.csv) | **188** | 183 | **5** | 0 |
| [All optional resources; five explicit legacy-pad reuses](full_with_five_legacy_repurposes.csv) | **183** | **183** | **0** | **0** |

The base candidate promotes **64 current NC balls** and keeps all 96 allocated user pads plus H3. It uses 129 ordinary GPIO and 32 LVDS-resource GPIO, all the latter as **inputs**. The full reuse candidate promotes all **86 current NC balls** and uses 129 ordinary plus 54 LVDS-resource GPIO, again all LVDS resources as **inputs**. Required control outputs remain ordinary GPIO. No native LVDS links are introduced.

The five-pin-short candidate deliberately remains failed. Its deterministic ordering leaves ENC8_Z, ENC9_A/B/Z and EX8_SR_DATA unassigned. That is an allocation artifact showing the shortage, **not a proposed removal of those encoder capabilities**. A complete source cannot be made from that candidate by marking these required wires NC.

The separate full-fit proposal makes these five changes:

| Existing reservation | Ball | Proposed function |
|---|---|---|
| SPARE_FPGA | K14 | HOST_SPI_CS_CMD_N |
| SPINDLE_FAULT_FPGA | G14 | PERMIT_OUT_REQ |
| SPINDLE_READY_FPGA | H14 | FPGA_OUTPUT_REQUEST |
| LUBE_STATUS_FPGA | J15 | FPGA_PROGRESS_O |
| CYCLE_START_FPGA | H16 | OPI_REARM_O |

Ordinary spindle/lube/cycle inputs can use the existing 24-DI service. These historical pad reservations have no extra required protected IS-2 field frontend. Their reuse still needs a deliberate native schematic/PCB/software change; **it has not been applied**. All twelve HOME pads, DOOR_STATUS and FEED_HOLD remain in this minimal-reuse proposal. Releasing all fourteen remaining unnecessary historical pads would leave fourteen genuine spare pins, but that is a separately reviewable engineering choice.

## Real peripheral resources, not hidden FPGA GPIO

The four soldered IOL1 controllers retain their complete data/diagnostic contract. Twenty-four DI, sixteen smart DO and the analog ADC/DAC/current/fault transactions are counted through those **sixteen serial wires**, not through an invented direct pin per field channel. Their controllers, CRC/identity/freshness checks, output-permission cuts and local watchdog behavior still need actual circuit/firmware implementation. The frozen output rating stays **0.5 A per channel / 2 A per four-channel group**.

RS-485 remains a compute UART resource; CAN remains a separate host SPI-controller resource. Entry-current/voltage monitors, identity/settings and slower diagnostic devices remain host/local-controller resources. Compute selection, ESP service, storage, HDMI/USB/Ethernet and display are not added to the FPGA count. Their real compute-module profile wiring is a separate open engineering requirement.

The status indicator destination is explicitly a **dedicated service LED-driver bus outside the precision motion transport**, with independent hardware fault override using the retained FPGA fault observations and actual watchdog/reset/power/permission nets. Seven RGB LEDs plus 52 DI/DO/alarm single LEDs and the WDT indication do not require 73 direct FPGA pads. The LED driver parts and fault-override gates are **not selected or fitted by this review**; actual output-state indication must use valid observations, with stale data clearing healthy state. If implementation instead adds an FPGA LED bus, its extra pins must be budgeted by releasing further historical reservations; the fully packed optional candidate has none free.

The 40-bit HEALTH_SR candidate contains 31 proposed monitored inputs, five unused positions and a four-bit marker. Its measured source circuits are unimplemented. In particular, commodity-module presence requires a genuinely qualified sensor/electrical/identity path; the common BTB connector does not magically provide presence contacts. A source that lacks such a path remains invalid, never tied healthy. Versioned service fields must distinguish measured rails, controller health and commodity identity from soldered-region installation facts. Permission-critical health also cuts the hardware gate directly; the shift register is not the sole inhibit mechanism.

## Primary review and vendor-tool boundary

The latest official index lists T20 pinout v3.5 and datasheet v6.0. A fresh v6.0 PDF download exactly matched the existing archived SHA-256. The workbook was re-read independently from its XML, not accepted from the generator's extracted JSON. The direct workbook refresh encountered the vendor's web protection; the exact previously archived official workbook remains the hashed review input.

Efinix permits the relevant LVDS resources as 3.3 V GPIO. F256 lacks their DDIO, Schmitt, pulldown and adjustable drive/slew features; external defaults are necessary during configuration. The vendor recommends at most sixteen output/bidirectional LVDS-resource pins per bank. Both complete candidates use **zero** such outputs. REF_RES remains floating because no native LVDS is used. The reviewed global clock stays H3; GPIOB_CLKN/P0 are proposed ordinary digital input resources, with their actual Interface Designer legality still to be checked. [Datasheet v6.0](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf), [official documentation index](https://www.efinixinc.com/support/docs.php?p=t), [Trion Interfaces guide v9.1](https://www.efinixinc.com/support/docsdl.php?pn=UG-TINTF&s=ef).

[vendor-tool-probe.json](vendor-tool-probe.json) records no Efinity tools on PATH or in six declared common installation locations. This is a scoped lookup, not an exhaustive claim about every disk directory. No vendor compiler or license check was run. The host has 64-bit Windows 11 and roughly 127 GiB RAM, so its basic platform is adequate; vendor software/device data and authorization are the missing prerequisites.

Genuine proof requires a T20F256I4 project containing the **full final RTL**, all-bank 3.3 V Interface Designer resources, active-SPI-x1 configuration reservations, exact pin constraints, a 50 MHz clock and actual I/O/CDC/reset timing constraints. Run interface design checks, native synthesis, placement/routing, constrained static timing, bitstream generation and the appropriate post-fit/full-chip simulations. Archive warnings, utilization, slack/unconstrained paths, pin report, power estimate and exact build hashes. `efx_run.bat <project>.xml --flow interface` and `--flow compile` are the documented flow entry points, but no command here was executed against an absent installation. [Installation guide v4.1](https://www.efinixinc.com/support/docsdl.php?pn=UG-EFN-INSTALL&s=ef), [CLI guide v1.1](https://www.efinixinc.com/support/docsdl.php?pn=UG-EFN-CLI&s=ef).

The current `cnc_endpoint.v` remains historical six-channel/two-encoder CNC1 RTL; its Yosys family mapping cannot prove this motherboard's full feature fit, pin legality, timing or bitstream. The nominal core/IO current reservations also require actual post-fit power/toggle review, not acceptance from pin counts. The 20 ms fault-to-inhibit obligation remains a real hardware/target timing requirement.

## Validation receipt

[validation.json](validation.json) passes independent exact-workbook pin/bank/configuration/direction/voltage/reservation/coverage checks and **10 meaningful mutation checks**. Encoder signals are checked separately from EN_N tokens. Duplicate balls, moved retained STEP pads, 5 V claims, missing frequency inputs, unsupported LVDS features and false fit/readiness claims are rejected. All **30 existing FPGA-core host validation tests pass**; [historical-fpga-core-tests.txt](historical-fpga-core-tests.txt) records the rerun. This review did not rerun motherboard ERC/DRC, change routed copper or generate a bitstream.

Sixteen source inputs are archived byte-for-byte with hashes in [input-sha256.json](input-sha256.json). The allocation/build/validation source and output hashes are in [receipt.json](receipt.json). Parent CAD reconciliation and actual peripheral/health/LED implementation remain engineering work; vendor compile access and later SI/power/fault-injection measurements remain external-tool/prototype gates. There is **no forced FPGA-package change from the standard-base pin count**, and there is **no completed-board claim**.
