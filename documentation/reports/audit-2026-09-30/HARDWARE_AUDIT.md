# Independent hardware audit

30 September 2026. Read-only inspection of current editable circuits, native XML exports, their builders and validators, primary manufacturer material, the connected evidence snapshot and the latest user decisions in `PROJECT_MEMORY.md`. No schematic was regenerated, board built, device programmed, machine connected, supplier contacted or old evidence overwritten for this audit. This report is an engineering assessment, not an electrical approval.

The hardware has substantial circuit work, but it does not yet implement the adopted product. The most serious new source defect found is the wrong physical pin map for the Nexperia Schmitt buffer in the FPGA user-reset path. The most serious retained requirement mismatch is the approximately 64–72 ms independent watchdog versus the required 20 ms fault-to-inhibit bound. The eight-standard/four-expansion implementation, individual enables, full general I/O, fixed wiring base, complete diagnostics and power budget remain unfinished.

## Evidence actually inspected

`tools/hardware_build_assembly.py:17–33` enumerates thirteen blocks and the explicit sheet-crossing nets. Native XML exports contain the following component counts; these include review boundary connectors and candidate components, not a released fitted manufacturing BOM.

| Block | Exported components | Recorded ERC | Actual scope and principal limit |
|---|---:|---|---|
| `power_entry` | 44 | 0 errors / 0 warnings | Separate core and field TPS26630 paths, reverse-blocking FETs, fuse positions, IMON/FLT/PG boundaries; fuse ratings, output clamp and source coordination unselected. |
| `core_converter` | 31 | 0 / 0 | LM70660 6 A main converter candidate; conditional compensation/unload arithmetic, no stability/thermal/transient measurement; expanded load exceeds it. |
| `logic_power` | 29 | 0 / 0 | Three TPS62901 1 A branches; cold-start arithmetic and nominal component choices, but total integrated capacitance and arbitrary power transitions unqualified. |
| `field_power` | 18 | 0 / 0 | LMR36506 fixed 5 V field-logic buck; isolation/status/load permission and full load budget unfinished. |
| `encoder_power` | 21 | 0 / 0 | Two TPS2553 current-limited encoder supplies; four required base encoder paths are not populated. |
| `tx_twelve` | 80 | 0 / 0 | Six AM26C31 banks for twelve STEP/DIR pairs; all on one study sheet, no plug-in four-motor module and no individual drive-enable circuit. |
| `rx_abz` | 16 | 0 / 0 | Six used receiver channels, two physical ABZ ports; terminated-disconnect validity, line protection and expanded feedback remain open. |
| `sbc_power` | 18 | 0 / 0 | Delayed TPS3890/TPS22990 computer branch; exact compute/carrier absent, warm-delay retention and backfeed unqualified. |
| `power_sequence` | 46 | 0 / 0 | Four LTC2962 window monitors and destination-powered reset buffers; cost, thresholds, retained rails and shutdown behavior open. |
| `digital_inputs` | 115 | 0 / 22 warnings | Eleven ISO1212 devices, twenty-two inputs total with explicit floating substrate islands; no implemented 24-general-input plus eight-alarm product allocation. |
| `fpga_core` | 80 | 0 / 0 | Sourced T20F256I4 ball allocation, flash, oscillator and reset support; reset-buffer physical pin defect, no vendor implementation/timing/bitstream, no full I/O implementation. |
| `machine_permission` | 28 | 0 / 0 | Independent watchdog, async-cleared arm latch, reset/CDONE/interlock path and global TX gate; selected watchdog cannot meet 20 ms. |
| `esp_service` | 44 | 0 / 0 | ESP32-S3 diagnostic/service module, USB switch, UART buffering, boot/reset boundaries; no accessory output/sensor system or full diagnostics acquisition. |

The stored evidence package `reports/processor-hardware-20260929/review.json` records 291 scoped host tests, zero skips, 521 copied source files, fresh native exports and 49 permission RTL checks. Its explicit `not_proved` list excludes a complete controller, PCB/DRC, device timing, physical power/safety/EMC, complete manufactured price, eight/twelve runtime, individual enable/alarm circuits and expanded power closure. Those exclusions are correct. This audit did not rerun that broad evidence suite.

Passing connectivity tests are useful evidence that the exported circuit matches its expected model. They do not prove that the expected model matches the manufacturer's physical pins, a real regulator is stable, a fault timer meets a requirement or the product's required interfaces exist.

## Findings: existing source defects and integration failures

### H01 — Critical physical pin error in FPGA reset buffer

As inspected, `tools/hardware_build_fpga_core.py:49` defines the `74LVC1G17GW` buffer as A=1, GND=2, NC=3, Y=4, VCC=5. The same incorrect map appears in the U4 connections at lines 105–107 and in `tools/hardware_validate_fpga_core.py:20`. The native `hardware/fpga_core/netlist.xml:3126–3129` connects U4.1 to the RC node, line 3354 connects U4.2 to ground, and lines 3699–3700 mark U4.3 unconnected.

Nexperia's actual [74LVC1G17 Rev.16.1, Table 3](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf) assigns the GW/TSSOP5 package **NC=1, A=2, GND=3, Y=4, VCC=5**. The local primary extraction `research/fpga-core/74LVC1G17.txt:279–311` states that map. The drawn component would have its real input grounded and its real ground unconnected; its reset-delay behavior is therefore invalid. Circuit ERC cannot infer this error because the custom symbol itself carries the wrong semantics. Mutation tests mirror that wrong map and consequently pass.

Repair requires a corrected custom symbol, builder, validator expectation and primary-source pin assertion; fresh standalone and assembly exports; refreshed applicable evidence while preserving the old snapshot. This is a source correctness finding, distinct from later physical qualification.

### H02 — Existing watchdog contradicts the retained 20 ms requirement

`PROJECT_MEMORY.md:18` explicitly retains the 20 ms fault-to-inhibit requirement. `tools/hardware_build_machine_permission.py:79,105,121–123` instead fixes TPS3431SDRBR with 120 pF and 64.288 ms nominal. `tools/hardware_validate_machine_permission.py:50–60` calculates approximately 57.712–70.968 ms with the stated tolerances, and 71.815 ms including its assumed 10 pF parasitic. Its formula contains a 55 ms offset; merely choosing a smaller timing capacitor cannot reach 20 ms.

The five-millisecond internal RTL watchdog is separate evidence and depends on the FPGA clock. It cannot substitute for the independent clock-stall watchdog. `gateware/board_review/tb_permission_connection.sv:117–121` stops that clock and manually drives the watchdog-health input low; it verifies the digital gate's response after injection, not the real watchdog's timeout. Select and design a genuinely independent timer that meets the total worst-case 20 ms bound, including detection, propagation and permission withdrawal. Preserve the current candidate as rejected timing evidence rather than changing the requirement.

### H03 — Main power is insufficient for the current expanded connection

The retained 6 A converter and entry cannot inherit the six-channel arithmetic. `research/EXPANDED_POWER_REVIEW.md:5,17–27` calculates 6.0601 A twelve-motor normal operation, 6.2272 A with encoder fault loads, 6.1260 A eight-motor host startup and 6.5260 A twelve-motor host startup. The existing core-entry ILIM screen bottoms at 2.1493 A while the twelve-motor host-start input calculation is 2.2376 A. The report honestly marks these as conditional design screens, not measurements.

A dedicated protected transmitter supply or properly redesigned higher-current main rail is still a proposal. The new hardware remains connected to the old rail in `tools/hardware_build_assembly.py`. A 10 A label alone does not approve shunt, inductor, compensation, input limit, connectors, fuses or sequencing. The report's proposed alternatives are not implemented and do not resolve every protection case.

### H04 — AM26C31 powered-off input compliance remains unclosed

The twelve-channel circuit uses 5 V AM26C31 drivers and 3.3 V FPGA inputs through 33 ohms. The [TI AM26C31 absolute-rating table](https://www.ti.com/lit/ds/symlink/am26c31.pdf) limits the ordinary logic input to VCC+0.5 V. If CORE_5V collapses while IO_3V3 remains energized, a series resistor alone does not ensure that voltage limit. The new reset/permission logic does not automatically establish that all data and enable pins remain compliant over arbitrary partial-power states.

`research/EXPANDED_POWER_REVIEW.md`, section “Option B,” records this exact gap and a possible 3.3 V AM26LV31E solution. That is a proposed electrical redesign requiring receiver-profile compatibility; it is not a drop-in claim that all 5 V optocoupler drives remain supported.

### H05 — Integrated low-voltage output capacitance/stability acceptance is incomplete

`hardware/logic_power/design-envelope.json:265–272` declares 50 µF maximum allowed effective output capacitance at the selected 1 MHz mode and a 32.208 µF local tolerance/temperature maximum. The added FPGA I/O bypass screen is 44.920 µF and the permission bypass screen is 0.9662 µF; combined with the regulator-local screen this is **78.0942 µF**. ESP adds 28.658 µF to the same 32.208 µF local maximum, or **60.866 µF**. Additional receiver/input/support loads can add more.

[TI TPS62901 Rev.A, Table 5.3](https://www.ti.com/lit/ds/symlink/tps62901.pdf) permits 6–50 µF directly at the output in 1 MHz operation and explicitly allows more when associated series resistance exists. These maximum screens therefore require a real effective-capacitance/impedance partition, stability study or circuit revision. Unknown DC-bias reduction cannot be assumed to solve the upper limit; no qualified series impedance or actual effective-capacitance envelope was found. This is an unclosed integration constraint, not proof that the regulator oscillates. Increasing only startup-current allowance is insufficient.

### H06 — Reset-release/retained-charge behavior is still a qualification gap

After correcting H01, the current candidate is still CDONE → 10 kΩ → 1 µF → Schmitt U4, followed by U5 AND service-run; configuration reset drives a different FPGA pin. `tools/hardware_build_fpga_core.py:105–114,121–125,140–144` defines that topology. The CDONE pull-up adds source resistance during charging. A ten-millisecond RC label is not the actual bounded hold interval.

No cold/warm numerical corner calculation for RC initial voltage, CDONE sink/pull-up loading, leakage, effective capacitance and Schmitt thresholds is present in `tools/hardware_validate_fpga_core.py:67–90`; those calculations still concern the separate local-reset divider. `reports/FPGA_CORE.md:5` properly leaves delay, discharge, JTAG handoff, partial power and startup synchronizers open. The ideal RTL bench externally assigns `user_reset_n`; it does not derive it from the analog network.

Service-run low can directly hold U5's output low. For JTAG, CDONE alone is insufficient: `research/fpga-core/an006.txt:1706–1714` requires ENTERUSER plus tUSER and recommends keeping the interface reset until that time. A qualified programmer handoff and release synchronizer are still required. Short upstream reset/brownout with retained RC charge must be analyzed separately from a fully discharged cold boot. Do not promote the new candidate to a guaranteed reset sequence.

### H07 — Field-output protection is unresolved, rather than an implemented safe stage

The historical ledger proposes TPS4H160BQPWPRQ1. `research/FIELD_OUTPUT_PROTECTION_GAP.md:5–11` records the concrete mismatch: 48 V transient device limit versus the reference SMCJ30CA clamp of 48.4 V, before ringing and other allowances. An eFuse's finite cutoff is not an instantaneous clamp. The similarly named TPS274C65 has a 36 V operating maximum; “65” denotes resistance, not a 65 V rating.

No general-output sheet is in the thirteen-block assembly, and no exact replacement plus complete isolation, acquisition/current-measurement, clamp, permission and diagnostic path is implemented. This gap must not be hidden by listing an output IC in the historical BOM.

## Findings: adopted requirements not yet implemented

### H08 — Eight standard motors plus a separate four-motor expansion is not built

`PROJECT_MEMORY.md:18` fixes the product structure: eight standard, motors 9–12 on a plug-in module, optionally factory-fitted. `hardware/tx_twelve/allocation.json` instead explicitly describes all six banks fitted on one circuit and an eight-channel variant needing separate BOM/export. `reports/TWELVE_CHANNEL_TRANSMITTER.md:3` still calls plug-in expansion a future choice. Twelve transmitter capacity is useful predesign work, but it does not satisfy the physical product structure.

`hardware/fpga_core/design.json:7–13` reports zero individual-enable circuits and six alarm circuits. The additional enable/home/alarm/encoder names are logical reserves, not working stages. `gateware/rtl/cnc_endpoint.v:17–23` still exposes two encoders and six STEP/DIR outputs, with no complete field-input/output ports. The eight-standard/full twelve runtime, protocol, driver, timing and electrical acceptance remain separate work. Global TX_PERMIT is not an individual motor enable.

### H09 — 24 general inputs, 16 general outputs and full diagnostic acquisition are missing

`tools/hardware_build_digital_inputs.py:31–33,71–76` deliberately instantiates the historical twenty-two-input allocation. It comprises six homes, six alarms and ten named auxiliary inputs; it is not twenty-four general inputs plus the required per-motor alarms. No general-output block is included by `tools/hardware_build_assembly.py:17–19`.

Power-entry IMON/FLT/PG and local power-good nets are real circuit boundaries. They are not a complete measurement system: no full ADC/multiplexer/isolation/acquisition/calibration path, per-output measured current, temperature instrumentation, validity/data-age implementation or local power-loss-tolerant fault-history hardware is demonstrated. `reports/ESP_SERVICE_HARDWARE.md`, sections “Serial, firmware and reserved GPIO” and “Verification,” explicitly leaves accessory control absent. GPIO reserves do not constitute protected customer interfaces or qualified condition sensors.

The rule that unavailable/stale measurements remain unavailable/stale is recorded at `PROJECT_MEMORY.md:20`; hardware and deployed diagnostic firmware must support that contract before displaying measurements.

### H10 — Fixed wiring base, replaceable motion card and memory cartridge are still specifications

The thirteen sheets are function blocks in one review hierarchy. There is no routed fixed wiring base, selected card/backplane connector, mechanical retention/keying, presence/identity circuitry, protected removable memory interface or separately fitted four-motor expansion board. FPGA J1–J10 are explicitly `schematic_boundary_not_orderable` in `tools/hardware_build_fpga_core.py:146–153`. The ESP USB connector's physical pad map and all footprints remain unassigned per `reports/ESP_SERVICE_HARDWARE.md`.

The requirement to replace service modules without soldering, wire disturbance, manual flashing or configuration loss is in `PROJECT_MEMORY.md:18,31–33`. Virtual module-replacement and file-storage tests cannot qualify connectors, off-state electronics, actual cartridge interrupted writes or preprogrammed spare logistics. The physical acceptance test remains entirely outstanding.

### H11 — Compute/network/display/AI hardware integration remains open

The SBC switch powers a logical computer boundary; it is not a selected CM4/CM5/CB2 carrier. Shared two-connector mechanics do not establish pin compatibility. Ethernet magnetics/connectors, selected host recovery, display/touch power, USB roles, cooling and complete memory/graphics/real-time budgets remain open. The six requested screen classes are retained in `docs/DISPLAY_TIERS.md`, but no offered panel/host package is electrically or physically qualified.

ESP32-S3 provides shared 2.4 GHz Wi-Fi/Bluetooth LE, not simultaneous independent 5 GHz plus Classic Bluetooth data paths. `reports/ESP_SERVICE_HARDWARE.md:9` preserves that limit. It is a cheap service module, not a backup hard real-time motion controller. The AI companion remains a separately powered network proposal; no selected installed module or complete measured inference/UI integration is claimed.

### H12 — Manufacturing and economics gates are correctly blocked

No `.kicad_pcb`, routed fabrication Gerbers or drill files were found under the current `hardware`/`manufacturing` inventory. `manufacturing/release-manifest.json:8–24,29–34` records partial circuits, no layout, blocked fabrication/placement/DRC, no PCBWay quote, required physical prototype and incomplete final cost. This correctly prevents a turnkey manufacturing claim.

The connected review BOM currently contains **570 rows**, of which **240 have no MPN** and **126 have no footprint**. These counts include review connectors/boundaries and are indicators of unfinished selection; they are not a parts-cost total or a count of independently unresolved engineering requirements. `hardware/controller_assembly/review-bom.csv:11–15` alone includes unselected output clamps and physical fuses. Complete controller, replacement-card, expansion and screen-kit prices remain unknown. Commercial willingness to pay for improved engineering does not close sourcing or manufacturing cost.

## Adopted unmerged IS-1 specification: credited separately from drawn circuits

The additional worktree at `C:/Users/Gluis/claude-worktrees/controller-interface-spec` was clean at `claude/interface-spec` HEAD `67b1bfc`. Its frozen interface specification is commit `0d879b26057dd7fa576835a7f9501cfabf14a71f` (21 added files, 43,295 lines), dated 29 September 2026. The later HEAD adds a CNC3 host codec/driver core; the software audit accounts for that implementation separately. This hardware audit did not merge, modify or regenerate the worktree. Frozen IS-1 should receive a subsequent revision for corrections rather than in-place edits.

The inspected IS-1 hardware source consists of the master document, sections 02/03/04, their machine-readable contracts, the related protocol/history definitions and the cross-reference validator. There are **six JSON contracts, five detailed sections plus the master, 13 module definitions, 15 card-boundary groups, 45 field connectors and 451 terminal records (315 standard plus 136 expansion), six machine allocation sheets, 21 containment requirements, 25 terminal test procedures and 174 HAL-pattern definitions**. On this audit run, `python tools/interface_spec_validate.py --check --json` passed **12,858 specification checks, zero problems**; it renders only into a temporary directory and left the worktree clean. The frozen commit also records 946 protocol arithmetic checks and 42 unit tests; those are recorded prior results, not rerun hardware tests here.

This is substantial engineering definition and must be credited. It is neither conversation-only nor fourteen new manufactured boards. No new IS-1 schematic, ERC, PCB, DRC, vendor FPGA implementation, prototype, physical timing or turnkey quotation is supplied by these contracts. Section 02 explicitly preserves those evidence limits at lines 544–565.

### IS-1 solutions specified for current main-checkout gaps

| Existing finding | Actual adopted IS-1 solution | Evidence and remaining implementation |
|---|---|---|
| H02: drawn TPS3431 misses 20 ms | Two TPS3851G18SDRBT timers with 3.3 nF C0G; falling progress pulse per accepted command; SET1 enable; WDO/RESET wired-AND; distinct motion/output arm latches; self-tests | `04-safety-power-timing.md:196–246`. Arithmetic includes a ±10 nA leakage allowance: 13.02 ms worst timer, 17.33 ms motion/14.02 ms output allocations. These selected parts and logic are **not drawn**. Toshiba NC-switch closure at 0–55 °C remains a measurement requirement, not a guaranteed datasheet bound. |
| H03: expanded main-rail overload | Separate ≥3 A MOTION_5V branch, expansion supply, EX8 converter and ≥3.61 A minimum core entry; separate FIELD_A/FIELD_B entries for sixteen 0.5 A outputs | `04:392–436`. Correctly separates the power reservations. The retained 18 V input minimum, startup peaks, efficiencies, fuse coordination and hot ratings remain unclosed. |
| H08: no enables/alarms or plug-in MX4 | Eight-motor MIA plus four-motor MX4; per motor TLP3640A normally-open and TLP4176A normally-closed enable contacts, LED driver and ISO1212 alarm; DM542T V4 profile and explicit whole-power-loss exception | `02:64–75`; `03:29–57`; `04:68–158`. All twelve individual circuits now have a specified design, but zero are drawn in the main checkout. NO/NC contacts are commanded states, not measured contact feedback. |
| H09: incomplete general I/O/diagnostics | DIC24 + two DO8 cards; TPS274C65ASRHAR and ISO7762FDBQR; isolated AO/AI; INA238 entry monitors; card identity/temperature; 29 slot status conductors; validity/age and source-backed diagnostic facts | `02:63–75,151,312–339,523–529`; `03:579–613`. Full interface and measurements are defined; acquisition, isolated domains, firmware and physical qualification remain unfinished. |
| H10: service architecture undecided | Passive fixed BASE, replaceable motion/specialist cards, separately fitted passive XTB expansion terminals and SCART cartridge; exact connector families, conductor budgets, identity and offline restore | `02:28–38,77–80,98–188,253–299,356–390`. Adopted choices must replace the older alternatives in current planning. The selected mate geometry still needs reconciliation (IS-H04 below). |
| H11: compute/display/AI unclear | CM5102016 is the first qualification/cost reference, other CM4-family modules separately qualified; six screen package studies; customer Ethernet/Wi-Fi on compute; service-only ESP; network AI companion | `02:64,74,460–470`; `03:619–629`. These are product requirements and cost scenarios, not qualified installed hardware. |

Independent primary-source checks support the TPS3851 standard timing formula/capacitor range and the AT30TSE752A's full-array reversible write protection requiring factory high voltage on A0. They also support two TPS274C65AS devices sharing one addressable SPI chip-select. These selected solutions are technically grounded; their schematic/layout/measurement gates still apply. Sources: [TI TPS3851 Rev. B, §7.1.1.2](https://www.ti.com/lit/ds/symlink/tps3851.pdf), [Microchip AT30TSE752A/754A/758A §10.5](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-8854-DTS-AT30TSE752A-754A-758A-Datasheet.pdf), [TI TPS274C65 Rev. C, §8.3.1](https://www.ti.com/lit/ds/symlink/tps274c65.pdf).

### IS-H01 — Price feasibility fails the recorded product reference

`02-modules-and-boundaries.md:414–441` estimates quantity-100 controller cost at **US$955–1,500 for eight motors**, US$1,093–1,723 for twelve motors, and US$1,136–1,790 for twelve motors/twelve encoders. The recommended eight-motor selling price is US$1,739–2,729 at the assumed 45% margin (`02:474–478`). This is 2.4–3.8 times the US$400 **selling-price** reference before margin, without a display, and excludes yield/rework, freight, warranty and certification. Package estimates also explicitly exclude enclosures, field supplies, harnesses, packaging and setup assistance.

This is useful cost-accounting work and an adverse feasibility result, not a quotation or an implemented cost reduction. BASE/cage US$243–384 plus 315-position field plugs US$110–189 alone can exceed the entire US$400 reference. The earlier screen-inclusive Mesa-price objective is further out of reach. A commercially workable design cannot be declared complete while this discrepancy remains. Keep required capability/service outcomes visible; re-engineer the component/connector/card solution and obtain actual costing rather than publishing the calculated selling price or silently dropping requirements.

### IS-H02 — Specified fault-history records do not retain the promised facts

`04-safety-power-timing.md:468–471` requires commanded rates, emitted counts per motor, output current/validity, temperatures, communication error counters and module identity/PGOOD for the two-second-before/two-second-after snapshot. However, the actual host ring defined at `01-protocol-and-schedule.md:1268–1321` has only HR1 and HR2, 64 bytes each. HR1 has no emitted motor counts, no encoder counts, no sampled output currents or temperatures and no complete identity/measurement payload; HR2 stores twelve command rates and requested analog/PWM settings. A non-real-time historian reading only these two records cannot reconstruct facts omitted by the real-time writer. Separate telemetry/event records and their temporal association must be specified and implemented, rather than inferred from the diagram.

The persistent F-RAM claim of approximately 90 records for a complete four-second snapshot and four retained snapshots in 512 records (`04:471`) lacks a defined persistent summary format or maximum event/fragment budget. Even copying HR1 and HR2 at 20 Hz needs 160 records per four seconds before missing count/measurement/event records; four such windows exceed 512 records. Compression or a smaller declared cartridge summary could work, but neither can be credited as the current specified complete snapshot. This is a frozen contract/capacity defect, not proof that F-RAM itself is unsuitable.

### IS-H03 — Encoder short/terminated fail-safe explanation is false

IS-1 correctly says single encoder-line faults are not detected electrically, but then claims the AM26LV32E fail-safe holds its output high for open or shorted lines (`04:493`; `01:1212`; steady-level claim also at `03:591–592`). [TI AM26LV32E Rev. E, revision history and §8.3.2](https://www.ti.com/lit/ds/symlink/am26lv32e.pdf) explicitly removed shorted/terminated fail-safe claims in December 2020. [TI's manufacturer clarification](https://e2e.ti.com/support/interface-group/interface/f/interface-forum/1267973/am26lv32e-question-about-failsafe) confirms only open, unterminated inputs have that protection; shorted or terminated inputs have no defined fail-safe output.

With the specified termination, a disconnected cable need not produce a clean steady level or simple legal back-and-forth counts. The commissioning/fault-injection plan must handle the actual undefined-output behavior. The honest 'not electrically detected' limitation remains; replace the incorrect mechanism explanation in a new revision and close the biasing/receiver/input-protection design before making validity claims.

### IS-H04 — Exact HB160 connector orientation is not reconciled with standing cards

The specified standard mechanical arrangement is 100 × 220 mm cards standing in guides on a common passive base (`02:29`). The HB160 pair is card-side female HARTING **02 04 160 1101** and base-side male **02 01 160 1101** (`02:186`, `spec/modules.json.connectors.HB160`). HARTING identifies [the exact card-side female as angled](https://www.harting.com/en-IT/p/DIN-Signal-harbus64-160FS-30C1-1-Trans-02041601101) and [the exact base-side male as angled](https://www.harting.com/en-US/p/DIN-Signal-harbus64-160MR-30C1-1-V4-02011601101). Two angled PCB halves do not establish the same orthogonal card/base arrangement as the other angled-card/straight-base slot pairs.

IS-1 already asks Codex to confirm the mating drawing in the JSON. That is a material feasibility dependency, not a footprint clerical task: establish both mating axes, PCB planes, row orientation, retention and XTB placement in a dimensional assembly drawing, or select the proper mate in the next revision. Gender, 160-contact count and vendor-family compatibility alone do not prove that the selected pair fits the adopted card cage. No mechanical failure is claimed for a nonexistent assembly; the unclosed exact-part/layout contradiction is the finding.

### IS-H05 — Ioff buffers do not by themselves prove required electrical fault containment

`02:32,65,400` specifies Ioff buffers on the MC and describes a shorted card-bound line as affecting the buffer channel rather than the FPGA. No exact buffer/protection path is selected. Ioff describes partial-power-down leakage behavior, not 24 V fault isolation. The containment requirement for 24 V on STEP+/DIR+ (`04:490`) still needs actual protection and a qualified interface path.

The main H04 issue also remains unless specifically solved: an MC-powered STEP/DIR buffer may drive 3.3 V into a collapsing or unpowered 5 V AM26C31 on MIA/MX4. A pull-down or disabled output-driver G input does not enforce the AM26C31 logic-input absolute voltage bound while a high signal is retained. The selected buffers, rail sensing, OE timing and current/voltage paths must close this case, including arbitrary rail sequencing. The required result is now recorded clearly; Ioff alone is not implemented evidence of it.

### Further IS-1 qualification limits retained

- The 175-of-189 FPGA signal budget uses at least 38 LVDS-as-GPIO pins (`02:218`). It is arithmetic, not a bank/voltage allocation or vendor fit; no release claim should promote it to proven twelve-channel hardware.
- The specified 195,312.5 steps/s cap explicitly leaves the prior 2,000,000 steps/s qualification goal unmet (`CONTROLLER_INTERFACE_SPEC.md:79`). A future CAP3 bit does not qualify the higher rate or guarantee that no board change is needed.
- The 18 V input arithmetic is deliberately retained as an open conflict with the current 19 V converter study (`04:392,403–411`). Voltage drop through fuse/eFuse/reverse protection must also be reconciled with the selected AI converter's 18 V minimum; input current alone cannot qualify minimum supply voltage.
- TPS274C65's 40 V continuous and 60 V sub-millisecond ON-state figures are **absolute maximum stresses**, not its 36 V recommended operating limit. IS-1 acknowledges that the retained 48.4 V clamp still needs ON/OFF-state surge-duration coordination (`04:426`). The new driver improves the proposed path, but does not automatically close H07. [TI TPS274C65 Rev. C, §6.1–6.3](https://www.ti.com/lit/ds/symlink/tps274c65.pdf).
- 'Hardware-enforced' 0.5 A channel/2 A bank limits (`04:424`; `03:613`) still need a drawn enforcement definition. The selected default current limit is 0.62–0.82 A; the higher allowed code reaches 1.00 A, and there is no selected separate 2 A bank trip. Ratings, declared-load validation, measured firmware thresholds and independent electrical protection must remain distinguishable.
- Config memory, AI ADC, isolated RS-485/CAN transceivers, ARM_LAMP driver, small port limiters and enable-loop clamp remain explicit BOM selections (`02:520–529`). Card-local regulation, PCB pad maps, fuse/source coordination, signed identity provisioning and actual loaded 72-hour/fault/module-swap tests remain unfinished.

## Traceability and stale instructions

Important user decisions are present in memory, but some downstream documents still describe superseded choices as active. `docs/EXPANDED_HARDWARE_TARGET.md:3`, `docs/BUILD_PLAN.md:13` and the expanded-controller row/next-hardware section of `docs/PLATFORM_ROADMAP.md` still call eight channels a preferred candidate. `docs/MODULAR_REPAIR_AND_MEMORY.md` and the build/status prose still compare a fixed base against removable terminal groups, although memory now fixes a wiring base and replaceable motion card. The connected transmitter report still treats plug-in expansion as undecided. The earlier inclusive-screen pricing objective and later controller-alone US$400 reference are not consistently reconciled throughout the plan.

These are traceability conflicts to correct while retaining historical studies unchanged. A requirement being recorded once in chat or memory is not sufficient if design/specification files subsequently permit a contradictory implementation. The 54-item historical electrical-ledger list also contains superseded observations (for example useful-progress WDI absent, unspecified package mapping) and should be identified as historical rather than the complete current defect count. The current RTL has progress WDI; its physical timer still fails H02.

## Rating recommendation

Recommend **32/100 for hardware completion against the current adopted product**, including the newly audited unmerged IS-1 definition, using this explicit audit rubric:

| Area | Earned / available | Reason |
|---|---:|---|
| Requirements and interface definition | 10 / 10 | The unmerged adopted IS-1 contains a complete shared card/expansion/terminal contract and explicit open items; its newly identified defects need a subsequent revision. |
| Circuit implementation and source correctness | 14 / 25 | Thirteen real connected circuit blocks; critical physical reset-pin defect and unresolved power/protection cases. |
| Complete required motion/I/O/diagnostics | 2 / 20 | Historical runtime and partial transmitter/input work; adopted enables/full I/O/diagnostics/modularity unimplemented. |
| FPGA/host implementation and timing | 4 / 15 | Real family mapping and HDL/host evidence; no vendor fit/bitstream or physical target timing. |
| PCB, manufacturing, service and complete cost | 2 / 15 | Release gate and artifacts structured honestly; no PCB, complete BOM/quote or qualified replaceable modules. |
| Physical qualification | 0 / 15 | No custom board, whole-unit measurements, endurance/EMC/thermal/fault or module-replacement test. |
| **Total** | **32 / 100** | **Engineering progress, not a sale-ready controller.** |

This score assesses completed hardware outcomes, not ambition, documentation volume or cumulative test count. A separate requirements-accounting score can be much higher without changing the hardware readiness score. Hardware production qualification is currently **0/100** because no product hardware has been manufactured and qualified.

The priority order is H01 source correction; reconcile/continue the adopted IS-1 contract with the main hardware (without restarting the work); revise the specific frozen-contract defects above; draw its selected independent watchdog, eight-plus-four card/base and individual enable/alarm/full I/O/measurement paths; close power/PDN/protection/connector geometry and complete cost; perform vendor FPGA implementation and the bounded physical link test; then complete PCB/manufacturing/service and whole-unit qualification.
