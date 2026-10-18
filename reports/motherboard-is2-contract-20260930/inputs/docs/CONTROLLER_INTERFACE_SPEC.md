Interface specification revision: IS-1, frozen for implementation

# Controller interface specification IS-1 (master document)

Frozen on 29 September 2026 after the integration pass over sections 01-04, and repaired the same day, before its first commit, after an independent three-lens review (safety timing, completeness, machine use); the repair decisions are I-16 to I-30 in section 4 and section 05 was added. Codex's hardware work (schematics, power and protection, connectors, PCB, hardware BOM) and Claude's implementation (FPGA logic, CNC1 protocol and LinuxCNC driver, card firmware, configuration and diagnostics service) both reference **IS-1**. Any change to a frozen item needs a new revision identifier (IS-2) and a re-run of the validator; nothing here is edited in place.

## 1. Scope and status

- **This is a specification.** Nothing it defines is implemented, drawn, laid out, built, simulated, synthesized or measured, and nothing in it is ready for manufacture. No card, base, connector footprint, gateware, driver, firmware or service described here exists yet.
- The six-joint/two-encoder CNC1 endpoint (ABI v1/v2, its RTL tests and its synthesis result) remains **historical baseline evidence**. It is not eight- or twelve-channel evidence and is never relabelled as such.
- Codex's drawn hardware in the main checkout (`hardware/controller_assembly/assembly-map.json`, dated 28 September 2026 21:44, and `hardware/fpga_core/pin-allocation.json`, sha256 24d4f7a4…) predates IS-1. Every difference is a named hardware change in section 1.1 (the same table is `changes_to_codex_drawn_hardware` in `spec/modules.json` and 02 §16.1).

### 1.1 Changes required to Codex's drawn hardware

| Drawn file / block | Drawn value | IS-1 value | Reason |
|---|---|---|---|
| `fpga_core/pin-allocation.json` | 22 dedicated FPGA machine inputs: HOME0-11, PROBE (G12), TOOLSETTER (G15), DOOR_STATUS, PROTECTIVE_STATUS (G16), SPINDLE_FAULT, SPINDLE_READY, FEED_HOLD, CYCLE_START, LUBE_STATUS, SPARE | Homes and machine status on the 24 general DI (DIC, IOL1 L0); G16 → EXT_PERMIT status copy, G15 → PRB1, G12 → PRB0; other balls return to the IS-1 ball plan | All 24 DI with validated transport; FPGA pins go to 12 motors, 12 encoders and the safety logic |
| `fpga_core/pin-allocation.json` | DRIVE_ENABLE0-11_FPGA_RESERVED | EN0-11_N_FPGA per-channel enables | Individual enable (decision 3) |
| `fpga_core/design.json` | individual_enable_circuits_present 0; alarm_circuits_present 6 | 12 NO + NC enable circuits; 12 alarm inputs | Eight motors standard, twelve with MX4 |
| `power_entry` | Two protected entries (CORE_24V_PROTECTED, FIELD_24V_PROTECTED) | Three entries: CORE ≥ 3.61 A, FIELD_A ≥ 5.08 A, FIELD_B ≥ 5.32 A current-limit minimum | 16 × 0.5 A outputs and single-short containment |
| `encoder_power` | ENC0/ENC1 supplies only | ENC0-3 on the EIA, ENC4-11 on the EX8, one TPS2553DBVR-1 each | 4 encoders + 8-port expansion |
| `machine_permission` | TPS3431 (≈57.7-71.9 ms), one arm latch, six-G-input fan-out | 2 × TPS3851G18SDRBT + CL10C332JB8NNNC with CWD guard ring, arm_latch_M/arm_latch_O with latch_clear_n / latch_clear_O_n, IS-1 fan-out with PERMIT_OUT_REQ, OPI_TX/A/B/BOE/OUT, DIC_OK and permit pull-downs | 20 ms fault-to-inhibit; repair-round safety findings |
| Host SPI (assembly map) | One chip select, SN74AVC4T774PWR (4 bits) | CS_FB + CS_CMD, five buffered channels | Two fixed-length transactions per cycle |
| Output driver (assembly map) | TPS4H160BQPWPRQ1, CS to a test point | 2 × TPS274C65ASRHAR per 8 outputs, ISO7762FDBQR, OUT_EN latch, STM32G031K8T6 | T1 |
| `tx_twelve` / `tx_bank` | 10-contact motor plug; receiver-input idle pulls not stated | 14-position plug (13 used); 10 kΩ pull-downs on every AM26C31 STEP/DIR input | Enable NO/NC, AUX supplies; no floating counted edge |
| Base and MC connectors | Slot presence/power-good of DIC, DOA, DOB, ACC, ESC, CMC, XS, SCART not routed | 29 lines to the MC slot status register | Module power-good diagnostics (A2) |

Parts that set interface figures but are Codex BOM choices are recorded with the limits they must meet in 02 §16.2 (cartridge configuration memory, ACC AI ADC, isolated RS-485 and CAN transceivers, ARM_LAMP driver, port limiters, enable-loop TVS). The ACC AI-group isolated supply is selected: RECOM REC3.5-2424SRW/R8/A (18-36 V in, 24 V 145 mA, 84 %, DigiKey listing, CAD 61.39 at qty 100).
- Evidence classes used by every number in IS-1: **[DS]** manufacturer datasheet or product page read for IS-1; **[DDR]** datasheet desk review recorded earlier in the repository; **[AR]** arithmetic from stated inputs; **[SI]** source inspection; **[REQ]** requirement or allocation set by IS-1 (not evidence that anything meets it); **[RES]** reservation; **estimate** engineering estimate shown as a range; **recorded price** a price ladder already in `research/*.json`; **[ME]** physical measurement. **There are no [ME] figures in IS-1**, no HDL simulation, no synthesis, no place-and-route, no ERC/DRC and no bench test of anything in it. Unknown prices stay unknown, never zero.

## 2. Confirmed decisions this revision implements

From [PROJECT_MEMORY.md](../PROJECT_MEMORY.md) (entries of 28 September 2026):

1. At least **eight motor channels standard**; motors 9-12 on a plug-in expansion module (MX4), with a twelve-motor version sold with it factory-fitted.
2. The **FPGA on a replaceable motion card** (MC) with its clock, configuration flash and supervisory circuitry, behind a **fixed wiring base** whose field terminals never move (pluggable terminal blocks where they help replace the base itself).
3. **Individual enable and individual alarm on every motor channel**, both enable polarities including controller-power-loss behaviour; unsupported drive behaviour listed as explicit exceptions; a global power interlock is never counted as a per-channel enable. The DM542T V4 reference drive is supported.
4. **All 24 general inputs and 16 general outputs**; serial transport to I/O cards only with module identity, sequence/freshness and CRC validated before outputs change, and a local watchdog that advances only on fully accepted transactions.
5. **4 ABZ encoders** plus an encoder-expansion path (EX8, 8 more ports) and a dedicated MPG/handwheel port; the full expanded I/O of [EXPANDED_HARDWARE_TARGET.md](EXPANDED_HARDWARE_TARGET.md).
6. The **20 ms fault-to-inhibit requirement** is retained (never relaxed). The recorded candidate was TPS3851G18SDRBT with 4.7 nF; see decision I-1 in section 4 for the capacitor used by IS-1.
7. **Commercial model** (supersedes the all-inclusive bundle target): US$400 is a preliminary reference price for the controller assembly only; packages (screens, power supplies, enclosures, harnesses, setup assistance, the $15 AI setup allowance) are costed and priced separately; required hardware is never removed to fit an assumed bundle; every cost-driving choice shows its cost difference, capability gained, replacement-card cost and whether it is standard or optional.
8. **Ownership split:** Codex owns hardware; Claude owns FPGA logic, the CNC1 protocol/driver and configuration-service integration; both work from this one specification.
9. **Acceptance test:** replace every designated service module with power off, without soldering, disturbing individual machine wires, manually flashing firmware or losing machine configuration; recovery works offline, rejects incompatible hardware and never resumes motion automatically.
10. **Product direction** (28 September 2026): hardware-backed diagnostics first, then the complete validated motion/I/O path, then the setup-and-repair experience (targets in section 11).

Corrections from the latest review, and where IS-1 carries them: (1) full-I/O protocol and one per-cycle schedule, [01 §3-6](interface-spec/01-protocol-and-schedule.md); (2) interruption latches a fault and invalidates position, rejected noise never changes an output, [04 §4](interface-spec/04-safety-power-timing.md) and [01 §3.15](interface-spec/01-protocol-and-schedule.md); (3) serial I/O validate-before-commit, [01 §4.6-4.7](interface-spec/01-protocol-and-schedule.md); (4) individual enable for both polarities with DM542T V4 supported, [04 §3](interface-spec/04-safety-power-timing.md). Targeted corrections: T1 output driver, [02 §11.2](interface-spec/02-modules-and-boundaries.md); T2 timing split, [01 §3.12, §8](interface-spec/01-protocol-and-schedule.md) and [04 §2](interface-spec/04-safety-power-timing.md); T3 700 us endpoints and separate bounds, [01 §5.1-5.3](interface-spec/01-protocol-and-schedule.md); T4 display rule, [01 §8.3](interface-spec/01-protocol-and-schedule.md) and [03 §6](interface-spec/03-terminals-and-allocations.md).

## 3. Section index

| Section | Content | Machine-readable source |
|---|---|---|
| [01 Protocol and schedule](interface-spec/01-protocol-and-schedule.md) | CNC1 ABI 3 (CS_FB 176 B, CS_CMD 96 B), opcodes, fault and safety words, event ring, telemetry mirror and map, IOL1 card link, per-cycle schedule, every advertised connection, HAL pin registry, diagnostics transport, history records | [spec/protocol.json](../spec/protocol.json) |
| [02 Modules and boundaries](interface-spec/02-modules-and-boundaries.md) | Slot map, card contents, conductors across every boundary, board-to-board connectors, FPGA pin budget and expansion reserve, identity (MIR-1), firmware restore, T1 driver selection, replacement and containment, costs and prices | [spec/modules.json](../spec/modules.json) |
| [03 Terminals and allocations](interface-spec/03-terminals-and-allocations.md) | 45 field connectors and 451 terminals with net, domain, target, protection, owner, resource, CNC1 field, HAL pin, states and test id; six machine allocation sheets | [spec/terminals.json](../spec/terminals.json), [spec/allocations.json](../spec/allocations.json) |
| [04 Safety, power and timing](interface-spec/04-safety-power-timing.md) | Timing classes, per-channel NO/NC enable, alarm, interruption rule, watchdogs, permission chain, fault-to-inhibit budgets, safety-interface behaviour, output fault states, power, evidence chain, containment matrix, 72-hour test | [spec/safety.json](../spec/safety.json) |
| [05 Service contract](interface-spec/05-service-contract.md) | `hw.modules`, both setup routes, device profiles and the question rule, validator rule ids, preview data contract, export/import, update states, offline operation | [spec/service.json](../spec/service.json) |

Checks: [tools/interface_spec_validate.py](../tools/interface_spec_validate.py) (cross-reference validator), [tools/is1_protocol_check.py](../tools/is1_protocol_check.py) (frame, CRC and schedule arithmetic), [tests/test_interface_spec.py](../tests/test_interface_spec.py). Renderers: [tools/interface_spec/](../tools/interface_spec/) (section 13).

## 4. Integration decisions at the freeze

The four sections were written in parallel. These are the inconsistencies found and how IS-1 resolves them. Each is an engineering decision taken under the delegated authority, with its reason.

| # | Inconsistency | IS-1 resolution and reason |
|---|---|---|
| I-1 | Watchdog capacitor: the user record names 4.7 nF (CL10C472JB8NNNC, 13.40/15.56/17.87 ms); section 04 uses 3.3 nF | **3.3 nF CL10C332JB8NNNC (9.51/11.04/12.67 ms [DDR][AR]) with one progress pulse per accepted command.** The 20 ms limit is the requirement; the capacitor is how it is met. With the normally-closed enable switch that correction (4) needs (TLP4176A tOFF up to 3 ms, 4 ms allocated), 4.7 nF gives 17.87 + 4.31 = 22.18 ms, which fails; 3.3 nF gives 16.98 ms [AR]. Same TPS3851G18SDRBT part. |
| I-2 | Output driver: sections 01/03 assumed TPS274C65AS and deferred T1; section 02 selected it | **TPS274C65ASRHAR** everywhere, with the complete-path comparison in [02 §11.2](interface-spec/02-modules-and-boundaries.md) and the isolator fixed as **ISO7762FDBQR** (4 forward: SCLK, SDI, CS_N, DO_EN; 2 reverse: SDO, wired-OR FLT; default-low outputs) [DS: TI product page]. Default current-limit setting 0.72 A (0.62-0.82 A [DS]); settings above 0.85 A (max 1.00 A [DS]) and the 2x/2.2 A inrush modes are rejected by the card, so the 1.0 A per-channel maximum holds. |
| I-3 | Current-sense accuracy: section 01 and 03 quoted different spreads | One basis: spread relative to the midpoint of the datasheet min/max sense current, ±3.2 % at 1 A, ±4.7 % at 500 mA, ±9.9 % at 200 mA, ±15 % at 100 mA, ±46 % at 50 mA [AR on DS]; declared display range 0.10-0.50 A; verified at 0.10, 0.25 and 0.50 A at both ambient extremes [ME required]. |
| I-4 | MX4 Ioff buffer "on the base" (04) vs "on the MC" (02) | **On the motion card**; the base stays passive. Section 04 section 6.3 and `safety.json` updated. |
| I-5 | EXTERNAL_PERMIT / PROCESS_PERMIT_EXT on "an I/O card" (04) vs the DIC XS1 interface (03, 02) | **DIC XS1.2 / XS1.3, hard-wired to the MC.** Section 04 section 6.1 updated. |
| I-6 | PERMIT_OUT (XS1.10-11) adds a TX_PERMIT receiver missing from the fan-out (R03-1) | Added to the TX_PERMIT fan-out in section 04 section 6.3 and `safety.json`; Codex re-runs the permission validator for the IS-1 fan-out. |
| I-7 | Host SPI: two chip selects in 01, "CS_N + IRQ" in 02 | **SCLK, MOSI, MISO, CS_FB, CS_CMD**; the protocol is polled, so the IRQ line is dropped; conductor and pin counts stay 5. The host buffer needs one more channel than the recorded SN74AVC4T774PWR. |
| I-8 | Motion-card temperature: "no sensor allocated" (01) vs AT30TSE752A on every card (02) | The AT30TSE752A-XM8M-T on the MC is its board sensor (host I2C, 1 Hz, with validity and age). |
| I-9 | XS synchronized-expansion slot: FPGA pins and contacts reserved (02) but no protocol fields (01) | CNF3 byte 173 `port_status_L4_XS`, CONFIGURE_IO page 0 byte 18 `expected_port_class_L4`, telemetry source 0x04 and HAL port `l4` reserved; always zero until a module class is defined (01 D01-11). |
| I-10 | Compute module: CM4/CM5/CB2 family (03) vs CM5102016 (02) | Dual 100-pin CM4/CM5-family socket; **CM5102016** is the reference module for costing and first timing qualification; others are qualified separately before being offered (consistent with PROJECT_MEMORY: CM5 is not mandatory). |
| I-11 | CNC1 field and HAL names in `terminals.json` did not all exist in section 01 | Normalised: every terminal now names frame fields (`STS.*`, `CMD.*`), event types, telemetry-map entries (`TEL.*`) or host-side sources (`HOST.*`), and every HAL pin resolves to the new `hal_pins` registry in `protocol.json`. Entry monitoring is the INA238AIDGSR on the PSM (host I2C, 10 Hz); per-port 5 V/24 V limiter voltages are **not measured** in IS-1 (fault flag only, shown as "not measured"). |
| I-12 | Analog I/O terminals listed as direct FPGA pins; section 01 carries AO/AI over IOL1 port L3 | AO0-1 and AI0-3 are IOL1 port L3 resources of the ACC card controller. |
| I-13 | Old expansion slots J_EXP 2x20 + J_EXPF (03 §8) | Superseded by the C096 P1/P2 slots and the XTB har-bus 64 connector (02 §7). |
| I-14 | Step-rate cap | **195,312.5 steps/s per channel** (MAX_RATE 0x01000000, 2 µs timing minimum) [SI]. The DM542T V4 accepts at most 200 kHz [DS]. The expanded target's 2,000,000 steps/s qualification goal is not met by IS-1; a higher cap is a later option under a CAP3 feature bit, with no layout change (01 D01-12). |
| I-15 | Author generators existed only in a scratch directory | Archived as `tools/interface_spec/` (renderers for 01 and 03, generators for 02 and the safety JSON). The integrated JSON files are the frozen source; the validator checks that every rendered document is current. |
| I-16 | Review: the output arm latch had no clear term, so OUT_PERMIT returned after each WDO pulse in a clock stall | `latch_clear_O_n = out_base_ok AND WD_O_OK AND FPGA_ENDPOINT_READY`; OPI_OUT latch on the MC; an OUT_EN latch on every DO/ACC card holds outputs off after any accepted OUT_PERMIT drop until a new epoch and IO_ENABLE (04 §4.2, §6.2; 01 §4.7) |
| I-17 | Review: a bank-B Ioff OE pulse rejected by the MX4 receiver could float STEP/DIR unrecorded | The qualified OE net clears an OPI_BOE latch on the MC; 10 kΩ pull-downs on every AM26C31 STEP/DIR input; OE glitch tests 0.1/0.3/1/2 µs (04 §4.2, §14) |
| I-18 | Review: permit inputs had no absent-driver default | 10 kΩ pull-downs on EXT_PERMIT_3V3 and PROCESS_PERMIT_EXT_3V3 at the MC receiver and DIC_OK in base_ok/out_base_ok; the validator requires a default for every hardware permission input (04 §6.2-6.3) |
| I-19 | Review: the WD_M self-test closed PERMIT_OUT | PERMIT_OUT drive = TX_PERMIT AND PERMIT_OUT_REQ, low in SELFTEST; the two tests never overlap; containment rows and 100 power-up tests (04 §5.4, §13) |
| I-20 | Review: CWD leakage not in tWD | ±10 nA allowance: 9.26/11.04/13.02 ms, self-test window 9.06-13.37 ms, clock-stall t_inhibit 17.33 ms (motion) and 14.02 ms (outputs); guard-ring requirement on Codex |
| I-21 | Review: XS1 contactor/STO/reset-arm behaviour undefined | Fault bits 25 CONTACTOR_FEEDBACK, 26 STO_FEEDBACK, 27 ARM_REFUSED; CONFIGURE_IO page 1 bytes 39-53; SAFETY_INTERFACE event; ARM needs a qualified reset/arm release by default; generated machine-enable chain (01 §3.4a, §7.2; 04 §8.1) |
| I-22 | Review: slot presence/power-good had no path to the FPGA | MC slot status register (40 bits, marker, double read), CNS3 bytes 82-85 `slot_status`, 29 lines on the MC connector, 3 FPGA pins (01 §4.10; 02 §6) |
| I-23 | Review: DI/AI could be reported valid beyond the published age | DI/AI invalid at the earlier of the stale limit and the port fault; limits restricted to 250-440 µs; worst valid DI age 747.08 µs at 5 MHz, target ≤ 750 µs (01 §5.3) |
| I-24 | Review: telemetry priority requests could starve the rotation | Priority at most every other slot: every entry within 90 ms, output current ≤ 93.05 ms old, inside its 100 ms stale limit; one stale rule (fixed per-source limits) |
| I-25 | Review: PWM inversion made the inhibited level active | Inversion removed; PWM row in the output fault-state table; validator rule V-EL-10 |
| I-26 | Review: AUX_5V could leave the DM542T ENA in its undefined band | AUX_5V chain: XMn.11 ≥ 4.75 V while AUX5_OK is high, worst-case ENA 4.69 V ≥ 4.5 V with ≤ 1.25 Ω cable loop; commissioning ENA ≥ 4.60 V (04 §3.2) |
| I-27 | Review: encoder line faults claimed but undetectable with the AM26LV32E | Stated plainly: single-line open/short is not detected electrically in IS-1; supply faults are; line faults surface as following error, preview disagreement and the commissioning count check |
| I-28 | Review: allocation sheets had no machine-readable HAL mapping | `hal` block per assignment and `hal_map` per sheet (joints, extra joints for indexers, feedback source, homing groups, probe net, spindles); the validator generates the net list and refuses two writers, missing feedback, unequal gantry HOME_SEQUENCE, mislabelled selectors, bus-only spindles, DO peaks above 0.62 A without a relay |
| I-29 | Review: sheet E ran spindles over Modbus only; XS1.3 was labelled a spindle permit | DO12-DO14 hardware run-enables in sheet E; Modbus variants in A and B keep DO0 as run-enable; XS1.3 renamed "process-enable interlock (XPC0/XPC1 only)" everywhere |
| I-30 | Review: setup, repair and preview interfaces were only acceptance rows | Section 05 and `spec/service.json` define them, with validator coverage |

## 5. Connection inventory

Counts are per unit with MX4, XTB and EX8 fitted (twelve motors, twelve encoders); an eight-motor unit carries 315 of the 451 field terminals [AR from terminals.json]. Update rates and ages are design bounds at 5 MHz host SPI [AR on REQ allocations]; "servo" means carried in every 1 ms exchange (T2).

| Connection | Qty | Terminals (card) | Transport | Update rate | Max data age at use | Fault response | HAL |
|---|---:|---|---|---|---|---|---|
| Differential STEP/DIR | 12 ch | XM0-7 (MIA), XM8-11 on XTB (MX4) | CMD.motor[i].rate (CS_CMD) | 1 kHz | command to commit ≤ 184.08 µs | any fault disarms all; continuity cleared unless clean DISARM | `cnc1.N.position-cmd/-fb` |
| Enable, NO and NC floating switches | 12 ch | XMn.8-10 | ARM channel mask; STS.enable_cmd_state | on ARM/DISARM/fault | switch times TLP3640A ≤ 0.5 ms, TLP4176A ≤ 3 ms [DS] | LED string dark: NO open, NC closed; a per-channel request drop while armed disarms all cleanly (01 §3.4a) | `cnc1.N.enable` |
| Drive alarm | 12 ch | XMn.14 (ISO1212) | STS.alarm / alarm_latched | 10 µs sampling, 1 kHz report | 30-40 µs filter + 307.08 µs | DRIVE_ALARM, disarm all | `cnc1.N.alarm` |
| AUX 5 V / 24 V loop supplies | 2 banks | XMn.11-13 (PSM) | safety word bits 12-15 | 1 kHz | snapshot | AUX_SUPPLY_FAULT, ARM refused | `cnc1.safety.aux*-ok-*` |
| ABZ encoders | 4 + 8 | XE0-3 (EIA), XE4-11 on XTB (EX8) | STS.enc[k].count, masks; INDEX_CAPTURE events | 1 kHz | 307.08 µs; index exact to the core tick | ENCODER_FAULT (illegal transition, port supply) if required by an armed joint; single-line faults not detected electrically | `cnc1.encoder.K.*` |
| MPG and pendant | 1 port | XH1, XH2 (EIA) | STS.mpg.count/status/select | 1 kHz; pendant bits read every 100 µs | ≤ 204.16 µs (pendant) | counts frozen while invalid | `cnc1.mpg.*` |
| Fast probes with FPGA capture | 2 | XPR (EIA) | STS.probe.state; PROBE_CAPTURE events | per event | capture 2-3 core ticks + filter | overrun sticky, result rejected | `cnc1.probe.N.*` |
| Frequency inputs | 2 | XF (EIA) | STS.freq[k].count/last_edge | 1 kHz | NO_SIGNAL after configured time, never 0 Hz | invalid | `cnc1.freq.N.*` |
| General inputs | 24 | XDI0-2 (DIC) | IOL1 L0 → STS.din, din_age | 10 kHz link, 1 kHz report | ≤ 547.68 µs at use (≤ 747.08 µs worst valid case) + debounce | older than the stale limit (250-440 µs) or port fault → all DI invalid, never read as low | `cnc1.din.N` |
| General outputs, 0.5 A | 16 | XDO0-1 (DOA/DOB) | CMD.dout → IOL1 L1/L2; readback and faults per cycle; current as telemetry | 1 kHz command, 10 kHz link | command to driver ≤ 344.48 µs + switching | output forced off and latched; card watchdog ≤ 2 ms; OUT_PERMIT | `cnc1.dout.N*` |
| PWM with OUT_PERMIT-gated buffer | 2 | XPW (ACC) | CMD.pwm[k].duty | 1 kHz, new duty at PWM period boundary | commit + one PWM period | buffer disabled in hardware and held off by the ACC OUT_EN latch; no inverted mode | `cnc1.pwm.N.*` |
| Process enables, hardware-gated | 2 | XPC0-1 (ACC) | CMD.proc_en; gated by PROC_PERMIT (XS1.3 gates only these two contacts) | 1 kHz | commit + photorelay switching | opened in hardware | `cnc1.proc-en.N.*` |
| Isolated 0-10 V outputs | 2 | XAO (ACC, one domain each) | CMD.ao → IOL1 L3 | 1 kHz, 10 kHz link | ≤ 160.4 µs + DAC settling | zero clamp on link loss or OUT_PERMIT | `cnc1.aout.N.*` |
| Protected analog inputs | 4 | XAI (ACC, isolated group) | IOL1 L3 → STS.ai, ain_age | ≥ 1 kHz sampling | card period + 240.6 µs | stale or out of range → invalid | `cnc1.ain.N.*` |
| RS-485, isolated | 1 | XB1 (ACC transceiver, host UART) | kernel RS-485 tty, MB2HAL | profile-defined, outside the servo thread | per transaction | profile hold/inhibit; never the only run-enable path | `mb2hal.*` |
| CAN, isolated | 1 | XB2 (ACC transceiver, MCP2518FDT-E/SL on the CMC) | SocketCAN, `cnc1can` | profile-defined, outside the servo thread | carried per signal | bus-off reported | `cnc1can.*` |
| Safety interface | 1 | XS1 (DIC): external permit, process-enable interlock, chain status, reset/arm + lamp, contactor and STO feedback, PERMIT_OUT | direct FPGA/hardware; safety word bits 10-11, 23-26, 30 | 1 kHz report | EXT_PERMIT input filter ≤ 1 ms + snapshot | EXT_PERMIT low: hardware inhibit; CONTACTOR_FEEDBACK, STO_FEEDBACK, ARM_REFUSED (01 §3.4a) | `cnc1.safety.*` |
| Supply entries | 3 | XP1 CORE, XP2 FIELD_A, XP3 FIELD_B (PSM) | host I2C INA238 (not CNC1); power-good in safety word | 10 Hz / 1 kHz | stale after 500 ms | eFuse protection; POWER_FAULT | `cnc1.supply.*`, `cnc1.power.*` |
| Synchronized expansion (XS) | reserved | slot S12 | IOL1 L4, CNF3 byte 173 (always 0) | - | - | nonzero class rejected in IS-1 | `cnc1.io.l4.*` |

The complete per-connection table with every field is [01 §6](interface-spec/01-protocol-and-schedule.md); every terminal is in [03 §5](interface-spec/03-terminals-and-allocations.md). The validator confirms that all 27 connection rows carry a rate, an age, a fault response and registered HAL pins, and that every fault or event name used in a fault response or terminal fault state is defined.

## 6. Per-cycle schedule (T2, T3)

One 1 ms servo cycle carries motion commands, all machine-control I/O, feedback, latched faults and data validity in two SPI transactions: CS_FB (176 B, read before LinuxCNC computes) and CS_CMD (96 B, written after). Currents, temperatures and history are sampled on the cards, timestamped and reported separately (one 22-byte telemetry mirror entry per cycle, 45 entries, every value at least every 45 ms without and every 90 ms with host priority requests, output current age ≤ 93.05 ms against its 100 ms stale limit). Local protection and the hardware inhibit path never depend on telemetry.

| Quantity | 5 MHz | 6.25 MHz | Basis |
|---|---:|---:|---|
| Wire time + guards per cycle | 436.16 µs | 349.12 µs | [AR] |
| Host allocations before commit (wake 80, ioctl entries/returns 65, decode 10, LinuxCNC 60, encode 5) | 220.00 µs | 220.00 µs | [REQ], **not measured** |
| Completion C(k) = T(k) to CS_CMD release (FPGA commit) | 656.16 µs | 569.12 µs | [AR on REQ] |
| Margin to the 700 µs target / to the 1 ms period | 43.84 / 343.84 µs | 130.88 / 430.88 µs | [AR on REQ] |
| Host overhead allowed for C(k) ≤ 700 µs | 263.84 µs | 350.88 µs | [AR] |
| Counter data age at use (bound ≤ 400 µs) | 307.08 µs | 250.76 µs | [AR on REQ] |
| DI age at use, no rejected frame / worst valid case (bounds ≤ 600 / ≤ 750 µs + debounce) | 547.68 / 747.08 µs | 491.36 / 690.76 µs | [AR on REQ] |
| Motion command to commit (bound ≤ 250 µs) | 184.08 µs | 153.36 µs | [AR on REQ] |
| DO command to driver (bound ≤ 400 µs + switching) | 344.48 µs | 313.76 µs | [AR on REQ] |

- **Endpoints of the 700 µs target:** start at the nominal period boundary T(k) (scheduling delay counts); end at the CS_CMD release of the accepted UPDATE; included: wake latency, ioctl overheads before commit, both wire times and guards, decode, all LinuxCNC computation, encode, DMA gaps. The 700 µs figure is an engineering-margin target: a miss is a recorded finding, not a fault.
- **Kept distinct:** 1 ms servo deadline; 700 µs completion target; 5 ms FPGA command watchdog; external watchdog 9.26-13.02 ms (with the CWD leakage allowance); 20 ms fault-to-inhibit. Input data age and output update latency have their own bounds.
- **Schedule decision rules:** budgeted at 5 MHz (the recorded host buffer rating); 6.25 MHz only after the host buffer path is qualified; write-behind only as a measured fallback; no rate, timeout or limit is raised to make the budget fit. 2 kHz is not feasible (wire time is 87.2 % of 500 µs [AR]).

## 7. Modules

Power-off service only. Every electronic card carries an AT30TSE752A-XM8M-T (identity record MIR-1 plus temperature). Costs: USD at qty 100, estimate ranges plus recorded prices, no quotation; spare prices are targets [recommendation].

| Slot | Card | Contents (short) | Firmware | Cost estimate | Spare target |
|---|---|---|---|---:|---:|
| - | Fixed wiring base | passive copper, 315 standard terminal positions, fuse holders, shield bonding, slot connectors | none | $243-384 (+ plugs $110-189) | not a 5-minute module |
| S0 | PSM power and service | 3 entry eFuses, CORE_5V, MOTION_5V, AUX limiters and monitors (AUX_5V chain of 04 §3.2), slot feeds, rail supervision, tamper latches, 3 x INA238 | none | $64-119 | $199 |
| S1 | CMC compute carrier | CM4/CM5-family socket (CM5102016 reference), Ethernet, HDMI, USB, antenna, identity-bus switches, MCP2518FD | eMMC image | $136-167 | $279 |
| S2 | MC motion card | T20F256 FPGA, 50 MHz clock, W25Q32 flash, 2 x TPS3851 + 3.3 nF, arm latches, OPI_TX/BOE/OUT latches, PERMIT_OUT_REQ gate, DIC_OK filter, slot status register, permission gates, Ioff buffers | gateware, host-restored offline | $64-115 | $219 |
| S3 | MIA motor interface M0-M7 | 4 x AM26C31 (STEP/DIR inputs pulled down), 8 x (TLP3640A + TLP4176A), LED drivers, 4 x ISO1212, OPI_A | none | $46-77 | $149 |
| S4 | MX4 motor expansion M8-M11 | as MIA for 4 channels, EXP_5V supervisor | none | $34-56 | $159 |
| S5 | EIA encoders and fast inputs | 4 x AM26LV32E (ENC0-3, FREQ, MPG), port limiters, probes, pendant register, XF bridge | none | $38-60 | $129 |
| S6 | EX8 encoder expansion | 6 x AM26LV32E, 8 port limiters, own converter, status register | none | $43-67 | $139 (= EX8 price) |
| fixed once | XTB expansion terminals | 136 positions for XM8-11, XE4-11, one har-bus 64 connector | none | $104-167 | $199 |
| S7 | DIC digital inputs + safety | 12 x ISO1212 (24 DI), group limiters, XS1, PERMIT_OUT, STM32G031C8T6 on IOL1 L0 | bootloader + app, host-updated | $46-68 | $119 |
| S8, S9 | DOA/DOB outputs (one part) | 2 x TPS274C65ASRHAR, ISO7762FDBQR, OUT_EN latch, STM32G031K8T6 on IOL1 L1/L2 | bootloader + app | $27-48 each | $99 |
| S10 | ACC analog, bus, process | 2 isolated AO, 4 AI with REC3.5-2424SRW/R8/A sensor supply, PWM buffers, process contacts, OUT_EN and PEN latches, RS-485/CAN transceivers, STM32G031K8T6 on L3 | bootloader + app | $121-159 | $249 (reason recorded) |
| S11 | ESC ESP32-S3 service | service USB, UART to host; no motion or permission authority | ESP-IDF, 2 OTA slots | $22-39 | $79 |
| XCART1 | SCART settings cartridge | protected configuration memory, FM24V02A-G history ring | records | $11-27 | $39 |
| S12 | XS synchronized expansion | reserved slot, link, sync strobe, permission | set by a future module | - | - |

**Commercial summary (estimates, not quotes).** Controller on its own: 8 motors **$955-1,500**, 12 motors $1,093-1,723, 12 motors + 12 encoders $1,136-1,790, against the US$400 controller-only reference (2.4-3.8x). Recommended selling price at 45 % gross margin (rounded up to the next $10, less $1): **US$1,739-2,729** for the eight-motor controller; MX4 + XTB upgrade US$279-449; EX8 US$89-139 (50 % margin on spares and expansions). Packages with a 7-21 inch screen, control PSU, HDMI cable and the $15 AI allowance: $1,045-1,726 in cost and $1,873-3,073 recommended (controller and add-on prices rounded separately), excluding enclosure, field supplies, harnesses, packaging and setup assistance (unknown, not zero). No required function was removed to approach $400. The cost-driving choices, each with cost difference, capability, replacement-card effect and standard/optional status, are in [02 §15.2](interface-spec/02-modules-and-boundaries.md) (for example retained screw-flange plugs +$144-248, the modular base +$176-292, expansion readiness +$27-41 on every unit, the isolated AI sensor supply +$42-47, the repair-round safety parts +$3-6). Publish no price until PCBWay and distributor quotes replace the estimate lines; the TPS274C65ASRHAR, ISO7762FDBQR, AT30TSE752A, TLP3640A/TLP4176A, INA238, TPS3851 and HARTING prices are unknown.

## 8. Acceptance tests

| Test | Pass condition | Where defined |
|---|---|---|
| Module replacement (user acceptance test) | Every designated card (PSM, CMC, MC, MIA, MX4, EIA, EX8, DIC, DOA, DOB, ACC, ESC, SCART) replaced with power off, no soldering, no individual wire moved, no manual flashing, configuration kept; recovery offline; incompatible card (wrong class, revision, signature, capability) refused; motion never resumes automatically; the listed checks run before re-enable | 02 §9, §10, §13; 04 §11 |
| Protection and containment | Each fault of the containment matrix contained to its port or card, detected and recorded as a fact; nothing outside the stated boundary affected | 04 §13; 02 §14 |
| Fault-to-inhibit | t_inhibit ≤ 20 ms on every path including clock stall (allocation 17.33 ms motion, 14.02 ms outputs, with the CWD leakage allowance); every scenario has a numeric bound; t_detect, t_inhibit, t_stop recorded separately | 04 §5.5, §7 |
| Interruption rule | Glitches below the qualification window never change a physical output; accepted gate transitions always latch OPI (TX, A, B, BOE, OUT) and clear continuity; an accepted OUT_PERMIT drop keeps that card's outputs off until IO_ENABLE; DISARM proof test on every disarm; PERMIT_OUT never closes during a self-test | 04 §4, §5.4, §14 |
| Serial I/O | A frame failing any identity, epoch, sequence or CRC check changes no output; accept timer 1.0 ms and IWDG ≤ 2 ms turn outputs off | 01 §4.6-4.7, §5.8 |
| 72-hour combined load, then fault injection | Section 11 row B3 | 04 §14; 01 §5.8 |
| Enable polarity | Per channel: disarmed ⇒ drive disabled for NO and NC wiring, DM542T V4 in NC-5V mode with ENA ≥ 4.60 V measured while disarmed, controller logic power loss keeps it disabled; with four channels armed, dropping one `cnc1.N.enable` disarms all cleanly; a required channel's request low blocks ARM | 04 §3.2-3.4; 01 §3.4a |
| Safety interface | Contactor and STO feedback mismatches latch their faults; ARM without a qualified reset/arm release is refused; machine-enable chain drops on EXT_PERMIT, fault or stale DI | 04 §8.1; 01 §3.4a, §7.2 |

## 9. Superseded records

[MOTION_EXPANSION_8_TO_12.md](MOTION_EXPANSION_8_TO_12.md) (revision 3) is design history where it conflicts with IS-1: §5 (symmetric 128-byte CNC3 draft, status layout, NOP + UPDATE per cycle, link budget) by 01 §3-5; §5.1 progress toggle by 04 §5.1; §5.4 and U11 (no enable polarity, DM542T V4 with ENA unconnected) by 04 §3; §7.2 (10-contact motor plug, J_EXP/J_EXPF slots) by 03 D03-3 and 02 §7; §8 (unfiltered Ioff OE, single enable switch) by 04 §4 and §3.3; §8.1/U15 (watchdog open) by 04 §5; §9 HAL names by 01 §7; §14.2 (DI/DO shift registers) by IOL1; §14.3 (latch placement) by 04 §6. The rest of that record, the historical six-joint ABI v1/v2 ([gateware/PROTOCOL.md](../gateware/PROTOCOL.md), [cnc1/PROTOCOL_V2.md](../cnc1/PROTOCOL_V2.md)) and the 96-position `hardware/terminal-map.csv` stay unchanged as baseline evidence.

## 10. Ownership split

**Codex implements in hardware (IS-1 requirements):**
- Card set and base to the boundary counts of 02 §6: HARTING C096/C032 slots, two har-bus 64 for the MC, one for the XTB, H15 for the PSM, coding per class, slot straps on base copper, presence contacts at both connector ends.
- The hardware changes of section 1.1 and the BOM limits of 02 §16.2.
- Per-channel enable circuit (TLP3640A(TPL,E) + TLP4176A(TP,F) on one LED current, SN74LVC07APWR, TPS22918DBVR, TVS parts to select), 14-position motor plug with contact numbers of 03 D03-3, AUX_5V/AUX_24V per bank with monitors and the AUX_5V chain (setpoint ±1.5 %, limiter and distribution drops ≤ 0.05 V, AUX5_OK trip ≥ 4.80 V), 10 kΩ pull-downs on every AM26C31 STEP/DIR input (04 §3, §4.2, §10.3).
- MC supervisory circuitry: 2 x TPS3851G18SDRBT with CL10C332JB8NNNC and a CWD guard ring, wired-AND WDO/RESET, SET1 on the request, sticky trip flags, both arm latches with latch_clear_n and latch_clear_O_n, OPI_TX/OPI_BOE/OPI_OUT latches, PERMIT_OUT_REQ gate, DIC_OK filter, permit-input pull-downs, the slot status register, RC + Schmitt qualification filters, final gates, Ioff buffers including the MX4 path, pull-downs at every receiver; re-run of the permission validator for the IS-1 fan-out (04 §4-6).
- Power: MOTION_5V ≥ 3 A, EXP_5V, 4 A-class core entry (≥ 3.61 A current-limit minimum), two field entries (FIELD_A ≥ 5.08 A, FIELD_B ≥ 5.32 A), bank limits, thermal and connector ratings; TVS clamp coordination with the TPS274C65ASRHAR (40 V continuous, 60 V < 1 ms ON state); RECOM REC3.5-2424SRW/R8/A on the ACC (04 §10).
- DOA/DOB with 2 x TPS274C65ASRHAR, ISO7762FDBQR, OUT_PERMIT AND OUT_EN latch AND CARD_EN gate; DIC, ACC and EIA/EX8 front ends; STM32G031 card controllers with SWD factory pads; AT30TSE752A-XM8M-T on every electronic card; 2 x TCA9548APWR on the CMC; 3 x INA238AIDGSR on the PSM; FM24V02A-G on the cartridge.
- Host SPI path with CS_FB and CS_CMD (one more buffer channel), SERVO_MARK test point, qualification at 6.25 MHz if wanted; MCP2518FDT-E/SL on a separate host SPI bus.
- FPGA ball plan for the 175 signals of 02 §8.1 (14 spare of 189; fit to be confirmed by Efinity).

**Claude implements (FPGA, protocol, driver, firmware, service):**
- Gateware: two-chip-select SPI endpoint (176/96 B), CNF3/CNS3 snapshots, 12 step generators with clean commanded stop, 12 quadrature counters, index and probe capture into the 256-entry event ring, frequency counters, PWM, four IOL1 masters with CRC-32C and port rules, EIA/EX8/MC-slot status readers, telemetry mirror with the every-other-slot priority limit, fault and safety words, progress pulses per accepted command, OPI inputs (TX, A, B, BOE, OUT) and proof test, SELFTEST state with PERMIT_OUT_REQ low, safety-interface qualifier (reset/arm window, contactor and STO feedback), `pos_continuity`, L4 reservation.
- Protocol tooling: ABI 3 encoder/decoder and reference vectors; the validator and checks of section 13.
- LinuxCNC driver `cnc1` (ABI 3 only, no fallback) with every pin of the `hal_pins` registry, the per-channel enable rules of 01 §3.4a, HR1/HR2 history ring, `halui.joint.J.unhome` through the channel-to-joint map and `VOLATILE_HOME = 1`, timing instrumentation; the generated nets of 01 §7.2 (extra joints for indexers, probe or2, spindle speed-in/at-speed, MPG enable gating, machine-enable chain); `cnc1can` component.
- STM32G031 card firmware: IOL1 endpoint with validate-before-commit, accept timer, IWDG, OUT_EN latch handling, readback, telemetry pages, write-protected bootloader with the SRAM erase/program routine that keeps the IWDG alive, and the MAINT update path.
- Configuration and diagnostics service (section 05): MIR-1 parser and compatibility rules, `hw.modules`, offline restore of gateware and card firmware from the local image store, the validator rules V-EL/V-CH/V-ML/V-TM, fact/diagnosis record types, display rule (validity and age on every value, one stale rule), both setup routes, the preview data contract, machine-bundle export/import, update state machines, replacement workflow.

## 11. Product acceptance targets

Owners: **C** = Claude, **X** = Codex, **U** = user (purchase or build decision). Every target is a requirement to test against, not a claim about the prototype. "Verification" names the test or calculation that closes it.

| # | Target | Owner | Verification method | Status |
|---|---|---|---|---|
| A1 | Per-output overcurrent/short, thermal, load current and open-load/wire-break on all 16 DO | X (TPS274C65ASRHAR circuit), C (card firmware, telemetry, HAL) | Fault injection per output on a built DO card; current reading checked at 0.10/0.25/0.50 A at both ambient extremes against a reference ammeter | specified; no hardware |
| A2 | Field-supply voltage monitoring (3 entries, DO bank VS, DI sensor groups, safety supply, AI sensor supply) and module power-good | X, C | Supply-dip and short tests on the prototype; readings against a reference meter; stale/disconnected paths shown as unavailable | specified |
| A3 | Temperature monitoring on every card and the compute module | X, C | Heat-gun and ambient tests; reading with validity and age | specified |
| A4 | Encoder port-supply faults (single-line open/short is not detected electrically in IS-1; it surfaces as following error and preview disagreement); communication error counters (host SPI, IOL1 both sides, RS-485, CAN) | X, C | Short each encoder supply; open/short each line and confirm it appears as disagreement or following error; bit-error injection on each link; every counted error traced to an injection | specified |
| A5 | Every diagnostic signal has a physical source, transport field, update rate, HAL/service name and fault response | C | `tools/interface_spec_validate.py` on the IS-1 files (passes; see section 13) and the same check on the implemented driver's pin list | spec check passes |
| A6 | Timestamped, power-loss-tolerant fault history ring (FPGA event ring + FM24V02A-G + host mirror); measured facts separate from diagnoses; AI never produces facts | C, X (F-RAM) | Power removal during recording at random points (torn record detected by CRC, previous records intact); diagnosis citing a missing fact rejected | specified |
| A7 | Every displayed measurement carries validity and age; disconnected or stale paths never shown as a plausible zero; accuracy verified across the declared range | C | UI and service tests with disconnected and delayed sources; accuracy per A1 | specified |
| B1 | Reliable 1 kHz servo with the full motion + I/O + diagnostics exchange | C, U (compute module) | Section 5.7 bench method of 01 on the target compute module under every load condition | blocked: compute module, prototype |
| B2 | C(k) ≤ 700 µs of each 1 ms cycle under the defined worst-case load, including scheduling delay; input age and output latency within their own bounds | C | Logic analyser on SERVO_MARK, CS_FB, CS_CMD; histograms and 99.9999th percentile; counts of C(k) > 700 µs and period overruns | blocked: compute module, prototype, analyser |
| B3 | 72-hour combined-load test (12 motors, 12 encoders, all I/O, analog, buses, touchscreen 3D preview, network, config cycles): no unexplained resets, deadline overruns or pulse-count discrepancies; then deliberate fault injection | C, X, U | 04 §14 and 01 §5.8: independent pulse counters on all 12 STEP outputs, generators, 259.2 million cycles [AR] | blocked: full prototype set, drives, instruments |
| B4 | No silent interruption of step outputs; interruption latches a fault and invalidates position | X (filters, OPI), C (gateware, driver) | Glitch tests of 04 §14; OPI proof test on every disarm | specified |
| B5 | Reserve for the 4-motor expansion and the encoder expansion at the same time: FPGA pins (56 reserved, 14 spare after the repair round), MC contacts (58 reserved + 48 spare), base connector positions, protocol fields (12 + 12 field sets), power (4 A-class core entry) | X, C | Validator (allocation sheet E: 12 motors + 12 encoders fits); Efinity place-and-route of the full pin set; power measurement with both expansions fitted | spec check passes; fit blocked on Efinity |
| C1 | Two equally usable setup routes: supported CAD assembly (identify moving groups, propose axis assignments, verify orientation and travel) and no-CAD (layout + dimensions → simplified moving model) | C | Scripted service tests on reference assemblies; the usability study C4 on both routes | interface specified (05 §3); not implemented |
| C2 | Verified drive, sensor and spindle profiles generate terminal-by-terminal wiring and configuration together; unknown information produces a specific question, never an invented setting | C | Profile tests: every generated terminal exists in `terminals.json` and passes the allocation rules; missing profile data yields a question | interface specified (05 §4); not implemented |
| C3 | AI proposes, a deterministic validator checks electrical compatibility, channel allocation and motion limits before anything is applied; expert editor and ordinary offline setup always available | C | Service tests with adversarial proposals (over-rating, double allocation, stale proposal) all refused; complete setup with AI disabled and no network | rule ids specified (05 §5), allocation-level rules enforced on the IS-1 sheets; service not implemented |
| C4 | On a defined, already-wired reference machine at least 8 of 10 first-time users reach a verified low-speed jog within 15 minutes without editing HAL/INI files or opening a terminal | C, U (participants, reference machine) | Moderated study, 10 first-time users, timed from power-on to verified jog; both setup routes | blocked: reference machine built on the prototype |
| C5 | Field-facing motor interfaces and output banks replaceable separately from compute and FPGA; faults contained to a port or card as stated | X, C | Containment matrix of 04 §13 and 02 §14 by fault injection | specified |
| C6 | Physical card replacement under 5 minutes after safe power-down, no wires disturbed, automatic compatible configuration recovery, identified checks before re-enable; commissioning and rehoming timed separately | X (mechanics), C (recovery workflow) | Timed replacement of every card on the prototype (procedure 320 s including the drive-power confirmation and the fixed 60 s discharge fallback; 200 s after safe power-down, estimate); recovery offline | blocked: prototype and card cage |
| C7 | Spare-module cost targets per card; no field-facing spare above 10 % of the controller price | X (BOM), U (pricing) | Quoted BOM per card against the targets of section 7 | blocked: quotes |
| C8 | 3D preview shows active tool, work offset, homed state, travel limits and which positions are measured; commanded-versus-measured overlay where encoders exist, excessive disagreement and stale feedback highlighted; without feedback labelled "commanded position"; clearance warnings only for modeled, registered components | C | UI tests with simulated encoder disagreement (warn 0.5 × FERROR, alarm 1.0 × FERROR) and stale feedback (> 3 ms); no collision-prevention claim in any text | data contract specified (05 §6); not implemented |
| C9 | Cloud independence: operation, local diagnostics, saved previews, configuration recovery and module replacement with no internet or AI credit; power-loss-tolerant configuration storage; recoverable updates; exportable settings; published module/interface specification (this document) | C | Tests that interrupt updates by power removal at every stage and remove connectivity; card firmware update interrupted and resumed offline under the IWDG | export format and update states specified (05 §7); not implemented |
| C10 | Unaided end-to-end demonstration: a new user configures a supported machine, the controller helps identify an introduced fault, the user swaps the affected module without rewiring, and the machine passes re-verification | C, X, U | Scripted demonstration on the prototype with an injected output-card fault | blocked: prototype |

## 12. Open items (genuine blockers only)

Engineering choices are made in IS-1; these items need hardware, a purchase, a measurement or an unavailable tool.

| Item | Owner | Exact dependency | Test or calculation that closes it |
|---|---|---|---|
| FPGA fit of all IS-1 logic (two SPI frame channels, 12 step generators, 12 encoders, 4 IOL1 masters with CRC-32C, status registers, 256-entry event ring, telemetry mirror, safety logic) and the 175-pin ball plan | C (run), U (install) | Efinix Efinity place-and-route, not installed | Efinity synthesis/place-and-route report: LUT/BRAM use, timing closure at 50 MHz, bank-voltage audit |
| Host overhead, jitter, C(k) distribution, input age, output latency | C, U | Target compute module (CM5102016 reference) purchased, motion-card prototype, logic analyser ≥ 200 MS/s | 01 §5.7 bench method; histograms under every load condition |
| Card MCU processing inside the 59.6 µs window, 20 µs apply allocation, IWDG ≤ 2 ms over LSI tolerance, bootloader erase/program under the IWDG | C, U | STM32G031 development board (purchase) or built cards | Firmware timing measured with a logic analyser; IWDG timeout measured at temperature extremes; complete update with the IWDG running |
| TPS386000 undervoltage-to-RESET assertion time (datasheet gives only a 4 µs minimum detectable pulse) | X, U | Built power module and a supply-dip generator | Measured assertion time inside the 0.05 ms allocation |
| USD price of the REC3.5-2424SRW/R8/A | U | Distributor quote in USD | Replaces the $42-47 estimate |
| TPS274C65ASRHAR complete ADC round-robin period and current accuracy over 0.10-0.50 A | X (card), C (firmware) | Built DO card, reference ammeter, climatic exposure | Measurement at 0.10/0.25/0.50 A per channel at both ambient extremes |
| Photorelay timing over temperature, WDO-to-inhibit, OPI capture, glitch tests, t_detect/t_inhibit/t_stop, thermal | X, C | Fabricated prototype boards (schematics and layout not complete; PCBWay order not placed) and bench instruments | 04 §7 and §14 measurements; t_inhibit ≤ 20 ms on every path |
| DM542T V4 compatibility (opto input with AM26C31 drive, NC-5V enable, alarm polarity) | C, U | DM542T V4 drive and motor (purchase) | Profile tests TT-XMn-01..04 of 03 §5 |
| 72-hour combined-load test, fault injection, usability study, replacement timing, unaided demonstration | C, X, U | Complete prototype set (all cards, base, card cage), drives, generators, pulse counters, reference machine, participants | Targets B3, C4, C6, C10 |
| Selling and spare prices | X (BOM), U (purchasing) | PCBWay turnkey quotation on complete design files; distributor quotes (DigiKey refused automated access) | Quoted BOM per card replaces every estimate line in 02 §15 |
| Connector mating drawing for har-bus 64 (card-side gender taken from a distributor listing) | X | HARTING drawing or sample (purchase) | Footprint check against the manufacturer drawing |

## 13. Reproducing and checking IS-1

| Command | What it does | Result at freeze (29 Sep 2026) |
|---|---|---|
| `python tools/interface_spec_validate.py` | Cross-reference validation of all six spec files, the six markdown files and the rendered documents, including the recomputed watchdog and fault-to-inhibit budgets, arm-latch clear terms, permission-input defaults, self-test containment, power budgets, allocation net lists, pricing rule and service rule ids (read-only; `--check` is the default and only mode; `--no-render`, `--json`, `--root`) | 12,858 checks passed, 0 problems (repair round, 29 Sep 2026) |
| `python tools/is1_protocol_check.py [--hd]` | Frame contiguity, CRC placement and known answers, reference vectors, schedule arithmetic, opcode/chip-select tables; `--hd` runs the exhaustive CRC Hamming-distance search | 946 passed, 0 failed; `--hd` re-run in the repair round: Hamming distance CRC-16/CCITT 4 at 1,408/768 bits, CRC-32C 6 at 320 bits (CRC-32/IEEE 5) [AR, exhaustive search] |
| `python -m unittest discover -s tests -p test_interface_spec.py` | Runs the validator on the real files and proves by fault injection that it catches a missing terminal, a double allocation, a frame overlap, a removed enable terminal, a schedule over budget, a missing arm-latch clear term, an undefined permit default, PERMIT_OUT during self-test, a non-numeric fault bound, two writers on one HAL pin, a bus-only spindle and more | 42 tests pass (22 before the repair round). Full suite `python -m unittest discover -s tests` in this worktree: 744 tests, 1 failure, 5 skipped (the count includes the ABI 3 reference tests being written beside this specification); the failure is the known, unrelated `test_hardware_assembly` source-hash test (Codex's schematic changed after its assembly map was recorded) |
| `python tools/interface_spec/render_01.py`, `render_03.py`, `gen_02.py`, `gen_04_json.py` | Re-render sections 01 and 03 from the frozen JSON; regenerate section 02 (JSON and markdown, field counts from `terminals.json`) and `safety.json` | outputs identical to the committed files |

All checks are specification checks (source consistency and arithmetic). None of them tests RTL, firmware, a schematic or hardware.

---

Interface specification revision IS-1. Nothing in this document is implemented, measured or ready for manufacture.
