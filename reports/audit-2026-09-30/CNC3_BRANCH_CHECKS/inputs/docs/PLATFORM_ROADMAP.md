# Platform roadmap and modular upgrades

28 September 2026. This incorporates the feature/platform, plasma-upgrade and third-party Modbus notes, plus the compute-module discussion. It is a development plan, not a list of shipping capabilities. [Actual engineering status](../reports/ENGINEERING_STATUS.md) remains the authority for completed work.

The product should make a machine easier to wire, set up, verify, operate and recover. Preserve the preferred Octopus/MR-1 experience, local LinuxCNC/FPGA control, ESP diagnostics with proposed accessory automation, included touchscreen options in 7-, 10-, 12-, 14-, 18- and 21-inch classes and beyond, editable design files and common UI/CLI configuration interface. The supplied notes broaden the possible machine families; they do not solve the existing cost gap or qualify new hardware.

## What is now recorded

| Requirement group | Concrete planning artifact | Decision boundary |
|---|---|---|
| Repair without rebuilding setup | [Modular repair and machine memory](MODULAR_REPAIR_AND_MEMORY.md) | Power-off service with retained wiring, complete settings cartridge, separate factory calibration and affected verification; physical system still undesigned |
| Screen sizes and product packages | [Display-tier plan](DISPLAY_TIERS.md) | Shared responsive application; exact panels, launch range and per-tier complete cost remain to qualify; 21.5 inches is one option |
| ESP supporting-equipment role | [Accessory automation contract](ESP_ACCESSORY_AUTOMATION.md) | Current firmware diagnostic-only; future one-owner request/readiness control, sensor confirmation and dependency-based fault policy |
| Industrial reliability and first sale | [Whole-unit qualification plan](INDUSTRIAL_QUALIFICATION.md) | Power/I/O/EMC/environment/factory/service evidence; HDPE enclosure candidate and later bounded pilot; no current certification claim |
| All 200 numbered feature proposals | [Readable catalogue](FEATURE_CATALOG.md) and [JSON catalogue](../research/feature-roadmap.json) | Stable F001–F200 IDs; proposals remain separate from installed/qualified capabilities |
| Expanded controller | [Eight-motor/four-encoder target](EXPANDED_HARDWARE_TARGET.md) | Preferred expanded candidate to evaluate; separate from the current six-joint study and its costs |
| Replaceable plasma equipment | [Module, harness and process-profile contract](PLASMA_MODULE_SYSTEM.md) | Power-off replacement; compatibility and calibration checks; one owner of Z motion |
| Third-party accessories | [Modbus adapter/device plan](THIRD_PARTY_MODBUS.md) | Supported retail USB/RS-485, RTU and TCP hardware; no mandatory proprietary VFD adapter |
| Easy customization | [Common CLI/UI contract](CONFIGURATION_AND_CLI.md) | Same validation and configuration transactions for touchscreen, CLI and assistant |
| Compute and carrier choice | [CM4/CM5 carrier strategy](COMPUTE_CARRIER_STRATEGY.md) and [BTT review](../research/BTT_COMPUTE_REVIEW.md) | Prefer the dual-connector family for evaluation; exact module compatibility and complete cost still decide selection |

The original notes are archived unchanged in [feature/platform source](../research/user-notes/2026-09-28-feature-platform.txt), [plasma-upgrade source](../research/user-notes/2026-09-28-plasma-upgrades.txt) and [Modbus source](../research/user-notes/2026-09-28-modbus-expansion.txt). Their SHA-256 hashes and feature source-line locations are in the JSON catalogue. Pasted `chatgpt-content-reference` placeholders do not establish references; new technical decisions need identifiable documentation and engineering evidence.

## Product structure

1. **Common controller with screen-size options:** local jobs, machine configuration, motion coordination, ordinary supported-machine I/O, diagnostics, software recovery and the visual setup experience. Screen diagonal does not determine machine capability; adapt the shared UI to each qualified panel.
2. **Rated interface modules:** plasma measurement, printer thermal/driver hardware, additional encoders, analog servos, laser-source/galvo interfaces, specialty sensors and additional industrial I/O. Their cost and power appear against the configurations that actually require them.
3. **Verified harnesses:** keyed connections and explicit pin mapping for named drives, cutters and accessories. A recognizable cable does not prove its remote equipment or switch settings.
4. **Machine and process profiles:** table geometry and motion calibration separate from cutter/spindle/toolhead settings, consumables, measurement chains and material recipes. Update only the affected configuration and invalidate dependent checks.
5. **Optional compute accessories:** AI and demanding analysis can use a separate companion. Required normal operation remains local and independent of that accessory.

Supported third-party devices use the same profile and guided setup experience as our own modules. USB/RS-485 and Modbus TCP remain appropriate for accessory/VFD commands and status; dedicated FPGA paths retain motion pulses, spindle-angle feedback and critical event timing.

Module replacement in the first version is power-off service, followed by recognition and a guided check. A connector, EEPROM or software profile cannot grant an electrical rating, prove correct wiring, or establish current physical position after power loss.

The latest [repairability source note](../research/user-notes/2026-09-28-repairability-memory.txt) adds a configuration cartridge that stays with the machine when electronics are replaced. Extend package A with interrupted-save recovery, explicit machine binding for replacement compute, compatibility checking and preservation of unchanged assignments. The prototype and wider requirements remain separate; existing F001–F200 IDs are unchanged. The cartridge stores configuration data, not only a path into failed compute storage. A standard store-bound backup and a controlled import into a new compute store are distinct operations.

## Delivery order and acceptance gates

The user's latest [integration milestone](INTEGRATION_MILESTONE.md) takes priority for immediate work: connect the existing six/two FPGA and actual LinuxCNC through CNC1, demonstrate the shared disconnected configuration service, and compare compute/carrier/display costs in parallel. Retain the wider catalogue without adding features to this first connection milestone.

The catalogue preserves every idea without treating all 200 as prerequisites for the first board. These are proposed work packages, not dates or delivery promises.

| Package | Feature IDs / dependencies | Demonstration and exit evidence |
|---|---|---|
| A — Configuration foundation | F001–004, F029, F032, F059, F100, F193, F195, F199–200; typed hardware/module/profile identities | A disconnected virtual device can be discovered, configured, exported and restored through the same documented service calls the UI will use. Unknown pins, conflicting assignments, incompatible firmware and stale configuration changes produce specific errors. No imported data executes code or energizes outputs. |
| B — First supported CNC workflow | Bounded subset of F001–004, F006, F011, F021, F029, F031–032, F037, F100; exact UI and CAD/registration work | Select a machine, generate its wiring, identify switches, verify scale/direction, square a supported gantry, place/probe stock, preview a job, run in actual LinuxCNC simulation, reconnect and diagnose an injected fault. Save/reopen the full setup. The physical commissioning version follows later hardware qualification. |
| C — First modular plasma workflow | F059, F091–092, F199; dedicated timing/status/inhibit capability and measurement contract | Offline first: simulate two identified cutter/harness combinations, keep axis calibration, require the changed cutter/measurement checks, and reject incompatible, missing and stale module data. Later: qualify one divided-voltage module with two named source/harness configurations and measured fault responses. |
| D — Everyday CNC completeness | Probing/metrology, scoped collision checks, restart, updates, diagnostics, supported lathe/threading/tapping and tool changing from F011–060; F124, F145–149, F196 | Each feature has a named machine/profile, hardware and timing requirements, a reproducible operation, negative/fault cases and recovery evidence. A passed simulator case is not physical qualification. |
| E — Additional process families | Printer F061–080/F151–160; laser F081–090/F161–170; specialty processes F171–180; their modules | Select an execution design for each family. Demonstrate its timing and fault handling before advertising compatibility. A CAN port or Linux host does not establish Klipper toolhead compatibility or pressure advance. Only one validated execution system owns motion in an active mode. |
| F — Advanced control, inspection and shop features | Remaining F101–200; extra sensors, control algorithms, extension permissions and compute budgets | Separate scoped investigations with measurable benefit, bounded behavior and implementation/qualification records. Do not inflate every base board with their dedicated power stages or measurement circuits. |

The selected first-core-demo IDs are recorded in the catalogue for navigation. They are a subset to exercise, not a claim that every aspect of those features is included in the first demo. Plasma identification also depends on the configuration foundation and future controller-side frequency capture; current RTL does not implement that complete path.

## The next hardware decision

Carry two explicit candidates through the same cost and resource review:

- `baseline-6j-2enc`: current study, six STEP/DIR, two ABZ, 16 additional DI, eight additional DO and one analog command. Existing electrical files and cost workbook describe this scope, with known unresolved corrections and unpriced blocks.
- `expanded-8j-4enc`: new preferred expanded candidate, eight STEP/DIR, four ABZ, 24 additional DI, 16 additional DO, dedicated probes/frequency/PWM/process control, two AO, four AI and the proposed communications/expansion interfaces. This is a new allocation and cost exercise.

Do not call the second candidate a population option on the same PCB until a real layout and fitted-BOM comparison supports that. Its isolated switching enable proposal differs electrically from the existing sourcing outputs. The expanded design has 92 directly mapped logical digital signals before support buses and housekeeping; the previous 84-entry GPIO ledger is not its pin budget.

For each screen tier, compare the hardware candidates with the same exact screen package at prototype, 10, 100 and 1,000 units. Then compare complete packages across tiers. Count connectors, isolation, protected supplies, support components, PCB/assembly, cooling, factory fixtures/test time, display/touch electronics, cables, mounting/enclosure, packaging and procurement losses. Exact panels, currency, retail target by package and production quotes remain unresolved; do not assume every size sells for the same price. An unquoted block remains unknown, never zero. BTT compute modules are now candidates in this comparison; a module listing does not include an entire carrier and does not prove loaded real-time operation.

Keep plasma-source-specific voltage isolation and firing contacts in the module budget. Count any generic host timing/status/inhibit provision in the base budget explicitly. Required normal functionality for a promised machine must be included in that machine's complete price.

## Development contract for modules

An interface specification must define electrical ranges, power/inrush limits, grounding/shields, signal ownership/defaults, identification and compatible versions, calibration format, transport latency/freshness, removal behavior, fault response and the permitted update sequence. A short internal timing backplane and a remote accessory network are different interfaces and need separate qualification.

The SDK should provide editable example hardware, documented protocol/schema, virtual devices, host drivers and conformance cases. Third-party identity is descriptive evidence, not authorization to drive a terminal. The service must validate identity against installed hardware, allowed resources and commissioning records. Extensions cannot write around the single motion owner.

Expose proposed commands such as `module inspect`, `profile validate`, `config diff`, `wiring plan` and `commission` through the common service; these names remain design proposals. Discovery shows observed, selected and verified facts separately. For example, a detected plasma module plus a selected 50:1 profile does not prove the cutter's physical divider switch.

## Evidence required for an individual feature

Before moving an F-ID out of proposal status, record:

- The supported operation, specific machine/profile and implemented limits, including how it affects the existing UI and CLI.
- Exact hardware, firmware, calibration, power and timing dependencies; whether cost belongs to the base or an accessory.
- A normal-operation acceptance case, meaningful wrong-input/fault cases, and an explicit recovery path.
- What was inspected, simulated, compiled, synthesized, measured or physically qualified, with revision-linked evidence.
- Any setup changes that invalidate the result and any remaining unsupported behavior.

Use the catalogue for planning and the installed capability manifest for operation. A roadmap entry must never make `capabilities --json` advertise a function that its fitted hardware, deployed software and qualified machine profile cannot provide.
