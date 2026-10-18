# Motherboard interface revision IS-2

30 September 2026. **Authorized physical/topology revision; implementation incomplete.** The latest user instruction resolves the architecture conflict: build **one custom active motherboard**, fit all twelve motor interfaces directly, and use purchased replaceable compute, ESP/service, storage/settings and qualified accessory modules. The passive rack, thirteen custom card positions, removable motion/field cards and custom MX4/XTB motor expansion are superseded physical arrangements.

This is a local delta against the frozen external IS-1, not an in-place edit or a claim that the full controller exists. Its machine-readable contract is [hardware/motherboard/requirements.json](../hardware/motherboard/requirements.json). Exact read-only IS-1 inputs and the mapping receipt are preserved in [the source archive](../reports/motherboard-is2-contract-20260930/README.md). Existing MC r0.4/revision 14 schematic, parts, pad assignments and copper remain reusable partial work; this document changes no CAD, gateware, firmware, machine configuration or source test evidence.

## Physical decisions

The motherboard contains the FPGA, clock/configuration flash, watchdogs/permission, power/protection, all twelve STEP/DIR interfaces with individual enables and alarms, four base ABZ encoder ports, 24 general DI, 16 smart DO, fast probes/frequency inputs, MPG/pendant, PWM/process contacts, analog I/O, RS-485/CAN, status indicators, labelled pluggable terminals and the module detection/provisioning interface.

| IS-1 physical boundary | IS-2 implementation boundary |
| --- | --- |
| Passive BASE, cage, thirteen slots and large DIN/har-bus card connectors | One active custom PCB with reviewed electrical domains, commodity sockets and pluggable field connectors |
| PSM | Soldered power/protection/monitoring region; retain independent protected branches where needed, remove feeds that served nonexistent rack slots |
| CMC | Compute-bay circuitry on the motherboard; the purchased Linux module is the replaceable unit |
| MC with replaceable FPGA | Soldered FPGA/clock/flash/supervisory region; failure of this region requires motherboard repair or replacement |
| MIA + MX4 + motor portion of XTB | Twelve fully fitted motor interfaces and XM0–XM11 terminals on the motherboard, retaining bank A/B protection and interruption monitoring |
| EIA, DIC, DOA, DOB, ACC | Soldered encoder/fast-input, DI/safety, two DO banks and analog/process/comms regions; internal controllers and isolators can remain where their function is justified |
| Custom ESC | Purchased replaceable ESP32 board/module with a reviewed socket, power/reset, service connection and antenna clearance |
| SCART | Qualified replaceable storage/settings provision, retaining offline machine configuration and interrupted-write recovery; exact implementation still to select |
| EX8 encoder card and XS rack slot | Qualified optional accessory/standardized expansion interface; preserve encoder-growth capacity without selecting a new custom daughterboard family |

All twelve motor paths are fitted in the base motherboard. A machine may configure eight or fewer while retaining the fitted capability. No motor 9–12 card purchase or paid software unlock is promised here. Channels are not axes; a dual-motor gantry uses two motor channels.

The motherboard is a service unit. Pluggable harness terminals let it be exchanged plug by plug without unscrewing individual machine wires. Soldered functional regions are not independent solder-free field replacements. The old five-minute per-card replacement claim, fixed passive base that never moves and spare-card pricing no longer describe this product. Record actual motherboard exchange/recommissioning instructions and time when tested; do not transfer old rack service claims to the new assembly.

## Commodity compute, service and storage

Use the Raspberry Pi CM4/CM5 dual-100-pin mechanical ecosystem. Exact CM4, CM5, BTT CB2 and BTT CB1 variants are supported only after electrical and target qualification. Same shape is not the qualification. The [compute-bay audit](../reports/board-completion-20260930/COMPUTE_BAY_PIN_AUDIT.md), [selector proposal](COMPUTE_MODULE_SELECTOR.md) and [carrier strategy](COMPUTE_CARRIER_STRATEGY.md) remain the detailed input for pin conflicts and safe startup.

The cold-start selector assignments are AUTO/CM4/CM5/CB1/CB2/reserved. A qualified swap selects a prepared module-specific OS/device tree/transport profile without reflashing the motherboard FPGA or ESP. A newly unsupported module still needs electrical and software support. AUTO requires a proven independent ID or universally safe bootstrap; unsupported, ambiguous or wrong-profile states remain inhibited/service-only. An operator's switch setting does not prove the inserted module's identity or make wrong pre-boot wiring safe.

Select an ordinary purchased ESP32 board/module and a real, replaceable connector with exact pin map and clearance. The existing ESP firmware is diagnostic-only. ESP/service software has no authority to grant motion or bypass permission; missing/reset/service states must remain safe without its application. The module's radio and service feature set do not establish motion-network determinism.

[Storage and provisioning](BOOT_STORAGE_AND_PROVISIONING.md) distinguishes SD, eMMC and optional NVMe by exact compute module. SD/SSD is not automatically equivalent to the protected settings memory/history guarantees inherited below. Preserve machine lineage, calibration records, two committed generations, write integrity, offline restore and compatibility checks; specify actual media/controller/endurance/power-fail behavior before selection. NVMe/Optane is storage, not expandable RAM. RAM is upgraded by replacing the compute SoM with a supported capacity. The motherboard should function without optional SSD/AI.

Future verified adapters and ordinary communications/accessory modules are allowed. This does not authorize a proprietary family of new custom carriers or assume a $15–30 adapter can translate every electrical or high-speed interface.

## Function and terminal mapping

IS-1 uses zero-based M0–M11, ENC0–ENC11, DI0–DI23 and DO0–DO15. Retain that logical naming across the wiring map, service, HAL and silkscreen. The user's M1–M12 alarm LED labels are one-based display labels; the product mapping must explicitly connect them to M0–M11.

| Required function | IS-2 base quantity | Inherited logical terminal/net boundary |
| --- | --- | --- |
| Differential STEP/DIR | 12 STEP pairs + 12 DIR pairs | XM0–XM11; `M{i}_STEP_P/N`, `M{i}_DIR_P/N`; internal `STEP{i}_FPGA`, `DIR{i}_FPGA` |
| Individual enable | 12 NO/COM/NC contact sets | XM0–XM11; `M{i}_EN_NO/COM/NC`, `EN{i}_N_FPGA`; bank permit does not replace individual enable |
| Individual alarms | 12 | `M{i}_ALM_IN` to `ALM{i}_FPGA`; separate from all 24 general DI |
| Standard ABZ feedback | 4 | XE0–XE3 to `ENC{i}_A/B/Z_FPGA`, protected encoder supply/return/shield |
| Encoder growth | 8 additional functions reserved | ENC4–ENC11 logical resources; no exact accessory, connector or transport selected |
| General DI | 24 | XDI0–XDI2; retain full validated acquisition and sensor-supply diagnostics |
| Smart general DO | 16 | XDO0/XDO1, DO0–DO15; actual current/fault/temperature/supply observations |
| Dedicated fast/operator inputs | 2 probes, 2 frequency inputs, one MPG A/B and 10 pendant selector inputs | XPR, XF, XH1, XH2; `PRB0/1_FPGA`, `FREQ0/1_FPGA`, `MPG_A/B_FPGA`; accessory presence/identity and supply faults retained |
| PWM and process control | 2 PWM + 2 floating process contacts | XPW, XPC0/XPC1; `PWM0/1_FPGA`, `PEN0/1_CMD`; PWM safe-low and hardware process permission |
| Analog | 2 independently isolated 0–10 V AO + 4 AI in an isolated group | XAO/XAI; range, safe-zero clamp, acquisition/calibration, validity and age |
| Communications | Isolated RS-485 and CAN | XB1/XB2; declared termination and per-device rate/error/freshness |
| Machine permission interface | EXT_PERMIT, PROCESS_PERMIT, chain status, reset/arm, contactor/STO feedback, arm lamp and permission contact | XS1; dedicated direct receiver/feedback paths preserved |
| Power and chassis | Three protected entries plus PE/shield strategy | XP1 CORE, XP2 FIELD_A, XP3 FIELD_B, XPE1; fuse/eFuse/reverse/transient/monitoring functions retained |

Every one of the **451 IS-1 field positions** is mapped exactly once in requirements.json and [terminal-function-map.csv](../reports/motherboard-is2-contract-20260930/terminal-function-map.csv): **371 motherboard logical positions across 37 connectors**, and **80 optional encoder-accessory reference positions across eight connectors**. The base count is the old 315 plus 56 motor 9–12 positions. These are inherited logical positions, including supplies/returns/shields/spacing; they are not 371 signal pins, final production connector choices or new PCB placements.

The frozen field-resource list gives **77 distinct base direct FPGA field signals**, plus **24 optional encoder signals**. Four IOL1 local-controller ports plus the fast-input status register use another **19 base reference signals** before host SPI, clock/reset/configuration, watchdogs, health/status, indicators and expansion. This is arithmetic on the inherited function map. It does not establish a complete T20 bank/ball/resource fit. Original `codex_net` aliases and candidate balls are archived references; every production ball/footprint field remains unset until schematic, PCB, pin file and vendor implementation agree.

Retain the inherited logical field pin order until a separately identified terminal/electrical revision is made. Legacy references to a card, rack location, guide, connector or slot in the copied electrical text do not authorize that physical part. Production terminal family, coding item, loaded rating, mating orientation, clearance and shield/creepage strategy remain engineering tasks.

## Logical guarantees that survive consolidation

The **20 ms fault-to-inhibit maximum** remains mandatory. Inhibit includes the last STEP edge and every relevant motor, DO, PWM, process and AO inhibit/zero/contact response, as defined by IS-1; it is not a machine stop-time guarantee. Keep independent clock-stall watchdogs, separate motion/output arm latches, useful-progress-only watchdog refresh, sticky fault/interruption reporting, no automatic rearm and self-tests that cannot energize the field. Current numerical MC supervision work is not physical whole-controller timing proof.

Retain CNC3's baseline dual chip selects, exact 176-byte feedback and 96-byte command transactions, CRC/semantic validation, coherent feedback/capture, sequence discipline and commit after complete accepted transactions. Retain the 1 ms servo deadline and separate 700 µs completion margin target; do not confuse these with the 5 ms endpoint watchdog or 20 ms inhibit bound. Workstation/graphics, storage, compute and accessory load must be included in loaded qualification.

If the soldered I/O controllers use IOL1 L0–L3, they keep complete-frame CRC, class/port binding, epoch/sequence and freshness validation **before outputs change or watchdogs refresh**. Local accept timers/IWDG, real hardwired output permission, output-enable/rearm latches, readback comparison and invalid/stale DI/AI rules survive. Putting the controllers on the same PCB does not make a broken serial link, reset MCU or stale record healthy.

Retain output/current fault history and valid/age metadata. An unpowered, disconnected, reverse-blocked, stale or unqualified path shows unavailable/stale rather than a believable zero. Report command state separately where the contact or terminal voltage is not actually measured. AI can explain evidence but cannot invent measurements or bypass limits.

Reset, power-up, unconfigured FPGA, rail loss, missing compute/service/storage/accessory and failed qualification start or return to the appropriate inhibited state. External-permit and process-permit receivers have physical fail-closed defaults. Fault clearing, rail recovery, compatible replacement, booting Linux or restoring a saved profile never restores motion or verified position automatically. Recommission deliberately with affected joints unhomed and permissions revoked.

Retain one structured CLI/configuration/UI service, capability discovery, deterministic validation, preview/diff, reversible generation commit, offline provisioning/recovery and legitimate replacement without software repurchase. Commercial original software is not described as freeware and no open-source release is promised. Third-party licensing, third-party accessories and the [commercial policy](COMMERCIAL_MODEL_AND_LICENSING.md) remain applicable.

## Required semantic changes before implementation can agree

These are engineering work items, not another unresolved product choice. The motherboard decision is now explicit.

1. **Installed and presence are different.** All twelve fitted/qualified motor paths contribute to installed capability; the configured/armed mask can use fewer. Obsolete `mx4 installed`, card-present contacts, slot class, MIR-1 records and `hw.modules` entries cannot be tied true, forged or used to impersonate removable cards. Describe soldered functional domains and actual removable commodity modules separately, using real revision/health evidence.
2. **Permission health needs a real path.** `DIC_OK`, `PRESENT_A_OK`, bank-B presence/OE, card PGOOD and tamper terms now need explicitly reviewed onboard receiver/rail/domain-health/interruption equivalents. Retain all independent WD/CDONE/reset/EXT_PERMIT cuts, bank-B OPI_BOE and every actual receiver default. Removing a connector does not permit removing an interruption latch or replacing a health condition with a constant.
3. **Wire/status semantics must be versioned.** CNS3 slot status, expansion-installed/accepted bits, CAP3/IDP3, expected port/class bindings, module HAL/service records and firmware restore flows need an IS-2 topology declaration and coordinated RTL/driver/firmware/service update. No silent ABI-3 success with fake rack identities. The inherited frame discipline is the starting point; a final revised field/capability encoding is still required before implementation.
4. **DO settings must match the chip.** TPS274C65ASRHAR remains sourcing-only with the active **0.5 A/channel and 2 A/four-output-group** continuous limits. The device shares ILIM resources across pairs, so arbitrary independent per-channel trip settings must be represented or rejected. The [FIO-P1 proposal](FIELD_IO_CONFIGURATION_PROPOSAL.md) covers prospective 12/24 V, NPN/PNP, sinking and 1/2 A variants; this topology revision does not apply those circuit/profile changes.
5. **Local service boundaries must match reality.** Revise the replacement-unit inventory, restore/reverification procedures and calibrated board identity for whole motherboard versus purchased modules. Preserve offline configuration, entitlement and retained plug harnesses. Do not claim solder-free independent replacement of soldered FPGA or I/O regions.
6. **Compute/service selection must be built.** Qualify common/subset pins, optional default-off routing, selector inputs, wrong-setting behavior, independently checked identity, per-module images and loaded transport. No automatic pre-power ID or production module interchangeability is implemented by this document.
7. **Pins, power and geometry must be reconciled.** Reuse existing sound MC circuits/copper, source-check all remaining interfaces, then complete exact FPGA banks/balls, internal controller/indicator pins, isolation/return/chassis strategy, fuse/protection and complete loaded power budget. Removed slot feeds/connectors are not an excuse to copy an incomplete old rail rating or claim the old 220 × 100 mm six-layer placement fits the motherboard.
8. **Indications need observations.** Build the [seven labelled ordinary RGB indicators](STATUS_INDICATORS.md), 24 DI LEDs, 16 actual qualified DO-state LEDs, 12 alarm LEDs and independent WDT indication, including powered hardware fault-red priority. The LED command is not proof of the field state.

## Engineering and release evidence

The archived [consistency receipt](../reports/motherboard-is2-contract-20260930/receipt.json) checks input immutability, unique/exact terminal coverage, base/optional counts and direct-field-signal arithmetic. Those are source/data checks. It does not run native ERC/DRC, target firmware compilation, HDL simulation, FPGA vendor fit, real-time transport or physical measurements.

The existing six-joint/two-encoder endpoint tests remain historical baseline evidence. MC r0.4's native/host results remain scoped to that partially routed MC; consolidation does not turn them into full motherboard or twelve-channel runtime evidence. Complete all remaining required schematic functions, exact contacts/footprints, FPGA wrapper/pin map, decoupling and power/ground/return paths, routing and mechanical fit; run native full-controller ERC/DRC and independent uncapped connectivity; preserve/rerun relevant validation after material changes. Generate final stackup/rules and real Gerbers, drills, BOM, CPL, assembly/test drawings only from the reconciled design. Do not manufacture placeholder files or call this contract a fabrication package.

Cost the fully fitted motherboard at quantities 1/10/100 separately from compute, purchased ESP/storage/accessories, fabrication/assembly/programming/test and complete screen/PSU/enclosure packages. Old rack cost ranges and partial MC catalogue costs are historical scenarios, not new motherboard totals. Unknowns remain unknown. There is no proven saving figure until the complete new basket is costed.

Screen options remain the [7/10/12/14/18/21-inch classes and further qualified sizes](DISPLAY_TIERS.md), independent of machine I/O. Optional AI remains outside the base motion/control cost and authority. PCBWay turnkey remains the intended later manufacturing route after actual release gates pass; no order or upload is authorized by this document.
