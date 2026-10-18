# Visual CNC controller — engineering workspace

**Current work, 1 October 2026:** continue the single motherboard with all twelve motor interfaces and replaceable commodity compute, ESP and storage modules. The adopted Source26/ROOT102 board has 2,688 footprints and **3,524 required joins remaining**; regular native DRC is **0 errors/0 warnings**, while ERC has **0 errors/70 unsuppressed warnings**. Routing, physical power/fault qualification, full CNC3/LinuxCNC integration and vendor FPGA fit/timing remain unfinished. The current source, board hashes, scoped results and release blockers are in [engineering status](reports/ENGINEERING_STATUS.md), [project memory](PROJECT_MEMORY.md) and [acceptance gates](docs/CURRENT_ACCEPTANCE_GATES.md). The earlier records below retain their original dates and scopes; they do not supersede the current single-board architecture or establish manufacturing readiness.

Run the disconnected pre-hardware bench from PowerShell:

```powershell
./validate_controller.ps1 --full
```

The equivalent command is `python -X utf8 tools/validate_controller.py --full`; use `--inventory` to inspect available tools without running the full bench. Each execution creates a new evidence directory under `reports/pre-hardware-validation-*`. Missing tools and unfinished integration remain explicit `BLOCKED` stages, and physical tests stay unrun. The command does not connect to a machine, flash hardware or generate fabrication files. Set `CONTROLLER_PYTHON` to select a Python 3.11+ runtime; native KiCad and the prepared WSL laboratory are separately required for their stages. A successful component simulation never authorizes a hardware rating.

**30 September audit:** [complete project audit and score](reports/audit-2026-09-30/AUDIT_REPORT.md) traces 64 requirements and all 200 proposals, including the separate Claude IS-1/CNC3 worktree. Current acceptance is in [22 named gates](docs/CURRENT_ACCEPTANCE_GATES.md). Main host checks pass 670 tests with five Windows symlink skips; 28 fresh native exports match. Independent datasheet review nevertheless found a wrong reset-buffer physical pin map, a watchdog that misses 20 ms and unclosed power/I/O integration. The controller is not ready for manufacture or sale. Earlier status and numerical records below remain dated evidence, not proof of the complete product.

The product is a controller that feels as approachable as the existing Octopus/MR-1 interface: bring in a machine, plate, vise and workpiece, arrange the setup visually, and operate without editing code or learning CAD. That existing interface is the visual reference; locating and confirming its source is still in progress.

The controller owns real-time machining locally. The intended product includes touchscreen options in 7-, 10-, 12-, 14-, 18- and 21-inch classes and further qualified sizes, with a Windows/macOS laptop or tablet as an additional interface. A shared responsive application is planned for those sizes. The proposed ESP role includes supporting-equipment automation, direct monitoring, diagnostics and service; current ESP firmware is diagnostic-only. Processor selection remains open until cost, machining features, the local visual workload and timing resources are demonstrated.

**Stage: integrated software prototypes, synthesized FPGA logic and partial electrical design.** Actual LinuxCNC/RTL simulation now includes saved-calibration recovery across launches. The synthesized circuit passes compiled-driver checks, and six-joint transmitter/two-ABZ receiver schematics exist. There is no complete manufacturing release or firmware qualified to drive a physical machine; the design is **not ready for PCBWay manufacture** ([submission checklist](manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md)).

**The first motion connection now works:** [actual LinuxCNC → compiled CNC1 driver → simulated FPGA RTL → returned joint feedback](reports/CNC1_INTEGRATION.md). The run verifies movement/reversal, encoder/index feedback and link-failure handling without automatic restart. The current [CNC1 record](cnc1/evidence/manifest.json) (2026-09-28T20:56:18Z) has 27 volatile runtime checks, 68 persistent checks across nine launches and 220 compiled driver/RTL assertions. Its Verilator transport is software-only; physical bus and real-time qualification remain open.

## Start here

**Full project briefing:** [everything learned, current decisions and next work](PROJECT_BRIEFING.md). This consolidates the architecture, compute choices, hardware scope, actual prototypes, UI/modules/AI, cost problem and development sequence in one place.

**Commercial and licensing direction:** [commercial model, offline licensing and compatibility policy](docs/COMMERCIAL_MODEL_AND_LICENSING.md) records the 29 September decision to sell the controller, paid software licences, expansion modules and complete tested kits while allowing customers to source ordinary supported peripherals elsewhere.

**Commercial status:** [commercial direction and licensing status](reports/COMMERCIAL_DIRECTION.md) records the release gates and the current boundary between requirement and implemented evidence.

**Current progress:** [thirteen connected hardware circuit blocks](reports/CONNECTED_CONTROLLER.md) now have one editable KiCad project and a combined review BOM. The project includes twelve differential STEP/DIR pairs, a T20 FPGA candidate with separate configuration/user reset paths, independent machine permission and an ESP32-S3 service boundary alongside the power, sequencing and isolated-input circuits. Native export reports **0 ERC errors and 22 explicit substrate warnings**; focused assembly, FPGA and permission checks pass. This is still partial hardware: twelve STEP/DIR pairs are not twelve complete runtime channels, and the expanded power screen exceeds the historical 6 A rail in several required cases. Historical connected-hardware archives retain their original source identities; the new final snapshot is regenerated only after source freeze. The latest full Python run passed **579 tests (5 Windows symlink skips)**; its [raw output](reports/audit-2026-09-28/python-tests.txt) is a working-tree observation. [Project memory](PROJECT_MEMORY.md) preserves the user's decisions, including [CLI-first customization](docs/CONFIGURATION_AND_CLI.md) and [coordinated fuse/eFuse protection](docs/POWER_PROTECTION.md).

**Latest planning updates:** [screen tiers and complete package costs](docs/DISPLAY_TIERS.md) alongside the [platform roadmap and modular upgrade plan](docs/PLATFORM_ROADMAP.md), preserving 200 feature proposals, the required eight-standard/four-motor plug-in expansion, replaceable plasma interfaces and third-party Modbus support. The [compute-carrier strategy](docs/COMPUTE_CARRIER_STRATEGY.md) evaluates the CM4/CM5-style footprint and [BTT alternatives](research/BTT_COMPUTE_REVIEW.md). These are planning/source-review additions, not an implemented responsive UI or new qualified hardware. US$400 is a preliminary controller-only reference; complete kits are separately priced.

**Cost evidence:** the [new compute/carrier/display matrix](research/COMPUTE_DISPLAY_MATRIX.md) covers CM4/CM5/CB2 and all six screen classes at 1 / 10 / 100 / 1,000 units, keeping six/two and eight/four separate. It records merchandise prices and unknowns; complete manufactured costs remain incomplete. The [earlier three-approach report/workbook](research/HARDWARE_COST_COMPARISON.md) retains its historical 21.5-inch/six-joint scope. PCBWay turnkey is the selected manufacturing route after design. [Optional AI compute](research/AI_ADDON_PLAN.md) remains separate. Local Linux plus custom FPGA/I/O and ESP remains the architecture; exact production parts and selling prices by package are not frozen. See the [cost-first build plan](docs/BUILD_PLAN.md).

| Artifact | What it answers |
|---|---|
| [Integration milestone](docs/INTEGRATION_MILESTONE.md) | Actual LinuxCNC through CNC1 to simulated RTL, feedback/fault proof and parallel configuration/cost work |
| [Runtime configuration](reports/RUNTIME_CONFIGURATION.md) | Guarded scale changes and actual unhome/rehome/pulse proof in LinuxCNC and simulated RTL |
| [Recovery CLI](reports/RECOVERY_CLI.md) | Public cartridge and replacement commands using the shared file-backed services |
| [Linux SPI implementation](reports/SPI_TRANSPORT_IMPLEMENTATION.md) | Compiled laboratory spidev backend, mocked syscall checks and remaining physical timing limits |
| [Configuration demo](reports/CONFIGURATION_DEMO.md) | Executable shared service and CLI for virtual profiles, conflicts, wiring, disarmed transactions and restore |
| [Modular repair and machine memory](docs/MODULAR_REPAIR_AND_MEMORY.md) | Retained wiring, grouped replacement sections, protected settings cartridge, module calibration and offline service requirements |
| [Commercial model and licensing](docs/COMMERCIAL_MODEL_AND_LICENSING.md) | Paid offline software, expansion modules, complete tested kits, customer-sourceable peripherals and third-party licence boundaries |
| [Replacement recovery demo](reports/MODULE_REPLACEMENT_DEMO.md) | File-backed cartridge records, virtual input-bank replacement and explicit new-compute import through the shared configuration service |
| [ESP accessory automation](docs/ESP_ACCESSORY_AUTOMATION.md) | Proposed request/readiness sequences, output ownership, sensors and essential-service failure behavior |
| [Industrial qualification](docs/INDUSTRIAL_QUALIFICATION.md) | Whole-unit power/I/O/EMC/environment/factory/service requirements, HDPE enclosure study and later pilot |
| [Display tiers](docs/DISPLAY_TIERS.md) | Shared UI and controller across screen sizes; per-package power, mounting, cost and qualification |
| [Feature catalogue](docs/FEATURE_CATALOG.md) | All 200 supplied proposals with stable IDs and source provenance |
| [Expanded hardware target](docs/EXPANDED_HARDWARE_TARGET.md) | Eight/four versus six/two interface, power, timing and costing deltas |
| [Plasma module system](docs/PLASMA_MODULE_SYSTEM.md) | Equipment upgrades using separate module, harness, process and calibration records |
| [Third-party Modbus](docs/THIRD_PARTY_MODBUS.md) | Supported ordinary adapters and accessories without a proprietary VFD dependency |
| [Product experience](docs/PRODUCT_EXPERIENCE.md) | What dropping models into the existing interface should actually do; the supported-machine path and guided custom setup |
| [Existing UI candidate audit](research/UI_REFERENCE_AUDIT.md) | Read-only findings and minimal extension points; candidate still needs identification as the intended MR-1 interface |
| [Requirements and evidence](docs/REQUIREMENTS_AND_EVIDENCE.md) | What “better” must mean in observable behavior, and which claims remain unproved |
| [Controller investigation](CNC_CONTROLLER_INVESTIGATION.md) | Acorn, Mesa, Octopus, MASSO context and recent technology research |
| [LinuxCNC integration](reports/LINUXCNC_INTEGRATION.md) | Actual runtime acceptance and service adapter; no hardware transport claim |
| [FPGA implementation](reports/GATEWARE_VALIDATION.md) and [actual synthesis](reports/FPGA_SYNTHESIS.md) | Six-step/two-encoder RTL, protocol checks and Efinix-family mapping; device routing/timing remain open |
| [ESP32-S3 firmware](reports/ESP_SERVICE_BUILD.md) | Actual diagnostic firmware builds and parser/freshness tests |
| [Electrical design package](docs/ELECTRICAL_DESIGN.md) | Machine-readable allocation, power/BOM review, real KiCad circuit and release blockers |
| [Six-joint transmitter circuit](reports/SIX_JOINT_TRANSMITTER.md) | Editable twelve-signal STEP/DIR block, actual KiCad ERC and checked terminal/pin mapping |
| [Two-ABZ encoder receiver circuit](reports/ENCODER_RECEIVERS.md) | Six differential inputs, termination/defaults and checked encoder-terminal mapping; actual KiCad ERC |
| [Core/field power entry](reports/POWER_ENTRY.md) | Two actual fuse/eFuse circuit drafts, reverse blocking, diagnostics, corner calculator and unresolved fuse/startup coordination |
| [Encoder supply protection](reports/ENCODER_POWER.md) | Two current-limited 5 V branches, checked pin maps and bounded current/voltage analysis |
| [Persistent runtime calibration](reports/PERSISTENT_RUNTIME.md) | Saved XYZ scales, explicit restart reconciliation and interrupted-save recovery in actual LinuxCNC/RTL |
| [Initial firmware feasibility](research/FIRMWARE_FEASIBILITY.md) | Earlier pinned upstream source audit, builds and advanced-feature limitations |
| [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md) | Open choices and provisional decisions |
| [Hardware pre-design](docs/HARDWARE_PRE_DESIGN.md) | Power/reset/clock/output ownership, interfaces and resource constraints before schematic work |
| [Core terminal and cost worksheet](docs/CORE_INTERFACE_COSTING.md) | Proposed six-joint channel allocations, 54 digital signals, electrical decisions and all product cost blocks |
| [SPI feasibility audit](research/SPI_FEASIBILITY.md) | Pinned LinuxCNC CM5 recognition, custom-board support work and the link test required before final PCB layout |
| [Recommended hardware baseline](docs/HARDWARE_BASELINE.md) | Embedded x86 + supported FPGA reference + ESP helper for engineering; historical CM5 comparison, superseded by the open CM4/CM5/CB2 carrier study |
| [Timing study](docs/TIMING_AND_RESOURCE_BUDGET.md) | Configurable demand calculations and deliberately exposed sample failures |
| [Supervisory contract](docs/SUPERVISORY_CONTRACT.md) | Proposed command ownership, disconnect, replay and fault semantics |
| [Validation record](reports/VALIDATION.md) | Actual test results, expected study failures and unresolved upstream timeouts |

## Run the offline engineering checks

Python 3.11+; the in-house Python studies use the standard library. From this directory:

```powershell
python -m unittest discover -s tests -v
python -m examples.configuration.demo
python -m examples.configuration.replacement_demo
python -m examples.configuration.recovery_cli_demo
python tools/build_compute_display_matrix.py --check
python tools/build_feature_catalog.py --check
python tools/build_hardware_cost_data.py --check
python tools/power_entry_analysis.py
python -m controller_lab.run_scenarios
python tools/analyze_requirements.py config/machine-study.json --output reports/timing-budget.json
python -m controller_lab.scene_manifest examples/mr1-scene-draft.json
```

The three `--check` commands are read-only research-data checks (source inspection and arithmetic), not hardware evidence. The scenario runner records seven abstract supervisor traces in `reports/supervisor-scenarios.json`. It injects backend events; it does not execute G-code. The timing report estimates demand from explicitly assumed machine settings. Its mill scenario intentionally exceeds some assumed limits; a test passing means the calculator correctly reports that failure.

The scene manifest work validates the relationship between asset identity, units, frames, a machine profile and commissioning records. A valid manifest is not permission to move. The draft MR-1 scene uses illustrative placeholders, not MR-1 measurements or real CAD assets. Its expected result is structurally valid, visual-only, with explicit registration blockers and `motion_authorized: false`. The CLI returns success for valid draft structure, not for control readiness. It never fetches imported asset URIs.

Upstream firmware experiments and their separate reproducibility instructions live in [the feasibility report](research/FIRMWARE_FEASIBILITY.md). Keep their build/simulation results distinct from these Python contract tests and from future physical measurements.

## Working direction

1. Preserve the exact interface the user likes; verify the reference before changing a UI.
2. Develop the full first-use flow in simulation: machine profile → model import → plate/vise placement → measured registration → job preview → controller acceptance.
3. Connect and qualify local LinuxCNC, the custom FPGA timing layer and the bounded ESP role. Compare exact compute modules and transports within that architecture.
4. Keep the external laptop outside the hard real-time loop. Ethernet is the initial service link; USB-C or wireless can carry the same high-level interface where supported.
5. Provide specifically rated, replaceable electrical modules. Broad machine compatibility comes from the right interface modules, relays, contactors and drives—not an unspecified universal-voltage terminal.
6. Resolve architecture, software and resource questions before buying parts. Physical verification remains a later engineering stage with specific measurements to make.

## Current boundaries

No finished CAD importer, collision engine, production service/transport, full PCB, electrical protection qualification or physical motion testing is present. CNC1 connects actual LinuxCNC to actual RTL simulation through compiled HAL, including durable XYZ-scale configuration. The broader profile/cartridge CLI remains a disconnected prototype. The KiCad project connects thirteen partial circuit blocks ([connected controller scope](reports/CONNECTED_CONTROLLER.md)); compute carrier/display selection, full motor enables/alarms and I/O, field outputs, analog interfaces, board layout, power qualification and physical qualification remain unfinished. The FPGA still needs vendor fit, routed timing, bitstream, full I/O and runtime protocol expansion. Existing UI candidates remain unmodified. No hardware has been ordered or connected by this project.
