# Controller documentation index

Reviewed **18 October 2026**. Start with the [project briefing](../PROJECT_BRIEFING.md), [project memory](../PROJECT_MEMORY.md) and [engineering status](../reports/ENGINEERING_STATUS.md). [Workspace entry](../README.md) · [Documentation review record](../reports/documentation-refresh-20261018/README.md)

## Read scope before capability

The active product contract is [IS-2](MOTHERBOARD_IS2.md): one active motherboard, soldered FPGA, all twelve motor interfaces fitted with individual enable/alarm, four base ABZ, 24 general DI and 16 smart general DO, plus the remaining specified interfaces. Purchased compute, ESP and storage/settings modules remain replaceable. Screen size and licensing do not remove required fitted resources. Whole-board service and commodity-module exchange preserve settings and offline entitlement with deliberate inhibited restart.

The [17 October continuation](../reports/board-finish-20261017/README.md) separates adopted CAD30 from isolated R299/corrected/candidate revisions. Recovered R299 has 1,172 required joins; the corrected baseline cached-fill DRC is 0 ordinary errors/332 warnings/0 parity issues. These are distinct sources/checks. The canonical disconnected SIM2 core now maps at 17,912 LUT4+ADD and has fresh eight-/twelve-joint virtual integration. Full physical-wrapper implementation, routed timing, complete electrical/assembly qualification and manufacture remain open. No current guide grants a physical rating from source inspection or simulation.

## Topic guides

### Planning and release

| Guide | Reading scope |
| --- | --- |
| [Build plan: working quality, then cost](BUILD_PLAN.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Platform roadmap and modular upgrades](PLATFORM_ROADMAP.md) | Current guidance; requirements and implemented evidence remain distinct |
| [CNC controller architecture decisions](ARCHITECTURE_DECISIONS.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Current controller acceptance gates](CURRENT_ACCEPTANCE_GATES.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Requirements and evidence register](REQUIREMENTS_AND_EVIDENCE.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Rev A software baseline and qualification](REV_A_QUALIFICATION.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Feature catalogue — 200 supplied proposals](FEATURE_CATALOG.md) | Generated F001–F200 proposal catalogue; source wording and IDs preserved |

### Motherboard, power and compute

| Guide | Reading scope |
| --- | --- |
| [Motherboard interface revision IS-2](MOTHERBOARD_IS2.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Motor capacity: all twelve interfaces on one motherboard](MOTION_EXPANSION_8_TO_12.md) | Current twelve-interface target with explicitly retained historical expansion records |
| [Electrical design review package](ELECTRICAL_DESIGN.md) | Current guidance; requirements and implemented evidence remain distinct |
| [CNC controller hardware pre-design](HARDWARE_PRE_DESIGN.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Physical fuses and electronic protection](POWER_PROTECTION.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Controller status indicators](STATUS_INDICATORS.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Compute carrier: CM4/CM5-style footprint](COMPUTE_CARRIER_STRATEGY.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Compute-module selector: cold-start profile selection](COMPUTE_MODULE_SELECTOR.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Boot storage and offline provisioning](BOOT_STORAGE_AND_PROVISIONING.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Configurable field I/O — versioned proposal](FIELD_IO_CONFIGURATION_PROPOSAL.md) | Current guidance; requirements and implemented evidence remain distinct |

### Setup, runtime and operator experience

| Guide | Reading scope |
| --- | --- |
| [Disconnected setup workbench](SETUP_WORKBENCH.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Customization and guided commissioning](CONFIGURATION_AND_CLI.md) | Current guidance; requirements and implemented evidence remain distinct |
| [AI-assisted CNC setup: execution and acceptance contract](AI_SETUP_CONTRACT.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Controller OS experience and image contract](CONTROLLER_OS.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Diagnostics, machine state and portable packages](DIAGNOSTICS_AND_PACKAGES.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Product experience: keep the existing interface, make setup approachable](PRODUCT_EXPERIENCE.md) | Current guidance; requirements and implemented evidence remain distinct |
| [One supported machine, one complete experience](FLAGSHIP_WORKFLOW.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Connect the existing controller pieces](INTEGRATION_MILESTONE.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Proposed supervisory contract](SUPERVISORY_CONTRACT.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Timing study and current resource evidence](TIMING_AND_RESOURCE_BUDGET.md) | Current guidance; requirements and implemented evidence remain distinct |
| [ESP32 accessory automation and condition monitoring](ESP_ACCESSORY_AUTOMATION.md) | Current guidance; requirements and implemented evidence remain distinct |

### Packages, service and accessories

| Guide | Reading scope |
| --- | --- |
| [Commercial model, licensing and compatibility](COMMERCIAL_MODEL_AND_LICENSING.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Touchscreen sizes and product packages](DISPLAY_TIERS.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Replaceable electronics and machine memory](MODULAR_REPAIR_AND_MEMORY.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Reliability, qualification and first commercial release](INDUSTRIAL_QUALIFICATION.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Plasma module system — proposed platform contract](PLASMA_MODULE_SYSTEM.md) | Current guidance; requirements and implemented evidence remain distinct |
| [Third-party Modbus devices and replaceable adapters](THIRD_PARTY_MODBUS.md) | Current guidance; requirements and implemented evidence remain distinct |

### Historical studies retained for comparison

| Guide | Reading scope |
| --- | --- |
| [Historical hardware baseline and current implementation direction](HARDWARE_BASELINE.md) | Historical study; use IS-2 and current status for the active board |
| [Historical six-joint core: terminal allocation and cost worksheet](CORE_INTERFACE_COSTING.md) | Historical study; use IS-2 and current status for the active board |
| [Historical expanded hardware target: eight motor channels and four encoders](EXPANDED_HARDWARE_TARGET.md) | Historical study; use IS-2 and current status for the active board |

## Manufacturing

[PCBWay turnkey submission checklist](../manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md) records the actual release requirements. No placeholder fabrication files, supplier upload, order or release is created by this documentation review.

## Source-bound component documentation

These READMEs describe their own code/circuit version and supported commands. Some belong to immutable source/test closures. They are inventoried here without changing those bytes or claiming that their historical resource counts describe the current complete controller. Read current scope in the topic guides and exact continuation receipts.

| Component README | Scope |
| --- | --- |
| [cnc1/README.md](../cnc1/README.md) | Historical six-joint/two-encoder baseline |
| [cnc3_runtime/README.md](../cnc3_runtime/README.md) | Versioned runtime/source record; use latest SIM2 continuation for corrected-source evidence |
| [cnc3_runtime/providers/README.md](../cnc3_runtime/providers/README.md) | Versioned runtime/source record; use latest SIM2 continuation for corrected-source evidence |
| [controller_backend/README.md](../controller_backend/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [controller_os/README.md](../controller_os/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [examples/configuration/README.md](../examples/configuration/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [firmware/esp32_service/README.md](../firmware/esp32_service/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [firmware/motherboard_iol1_readonly/README.md](../firmware/motherboard_iol1_readonly/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [gateware/motherboard_bringup/README.md](../gateware/motherboard_bringup/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [gateware/motherboard_iol1_target_bringup/README.md](../gateware/motherboard_iol1_target_bringup/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [gateware/synthesis/README.md](../gateware/synthesis/README.md) | Historical six-joint/two-encoder baseline |
| [gateware/synthesis/postmap/README.md](../gateware/synthesis/postmap/README.md) | Historical six-joint/two-encoder baseline |
| [gateware/v3/README.md](../gateware/v3/README.md) | Versioned runtime/source record; use latest SIM2 continuation for corrected-source evidence |
| [hardware/board_review/README.md](../hardware/board_review/README.md) | Published native CAD revision and component resources; distinct from isolated finishing candidates |
| [hardware/is1_watchdogs/README.md](../hardware/is1_watchdogs/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/mc_local_power/README.md](../hardware/mc_local_power/README.md) | Historical MC circuit/package source reused by the integrated motherboard |
| [hardware/mc_motor_buffers/README.md](../hardware/mc_motor_buffers/README.md) | Historical MC circuit/package source reused by the integrated motherboard |
| [hardware/motherboard_analog_input/README.md](../hardware/motherboard_analog_input/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_analog_output/README.md](../hardware/motherboard_analog_output/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_do/README.md](../hardware/motherboard_do/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_fast_inputs/README.md](../hardware/motherboard_fast_inputs/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_io3_upgrade/README.md](../hardware/motherboard_io3_upgrade/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_io3_window/README.md](../hardware/motherboard_io3_window/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_io_control/README.md](../hardware/motherboard_io_control/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_power_entry/README.md](../hardware/motherboard_power_entry/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_probe_limit_upgrade/README.md](../hardware/motherboard_probe_limit_upgrade/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_safety_sensor/README.md](../hardware/motherboard_safety_sensor/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motherboard_status/README.md](../hardware/motherboard_status/README.md) | Component source and its recorded evidence; no complete-system qualification |
| [hardware/motion_card/CNC_Motion.pretty/README.md](../hardware/motion_card/CNC_Motion.pretty/README.md) | Historical MC circuit/package source reused by the integrated motherboard |
| [hardware/octopus_external_adapter/r0_1/README.md](../hardware/octopus_external_adapter/r0_1/README.md) | Component source and its recorded evidence; no complete-system qualification |

## Dated research and design studies

The following research retains its original prices, supplier observations, technical assumptions and source citations. This documentation pass performs no new web research or procurement verification. Current decisions and complete cost limits are in the topic guides and engineering status.

| Research document | Original title |
| --- | --- |
| [AI_ADDON_PLAN.md](../research/AI_ADDON_PLAN.md) | Optional AI compute — expansion proposal |
| [BTT_COMPUTE_REVIEW.md](../research/BTT_COMPUTE_REVIEW.md) | BTT compute-module review |
| [COMPUTE_DISPLAY_MATRIX.md](../research/COMPUTE_DISPLAY_MATRIX.md) | Compute, carrier and touchscreen comparison |
| [CORE_CONVERTER_REVIEW.md](../research/CORE_CONVERTER_REVIEW.md) | Core 24 V to 5 V converter: bounded feasibility review |
| [DISPLAY_COST_STUDY.md](../research/DISPLAY_COST_STUDY.md) | Included touchscreen: sourcing and product cost |
| [EXPANDED_POWER_REVIEW.md](../research/EXPANDED_POWER_REVIEW.md) | Expanded motor power review — proposal only |
| [FIELD_OUTPUT_PROTECTION_GAP.md](../research/FIELD_OUTPUT_PROTECTION_GAP.md) | Field-output protection gap found during integration |
| [FIRMWARE_FEASIBILITY.md](../research/FIRMWARE_FEASIBILITY.md) | Firmware feasibility before buying hardware |
| [HARDWARE_COST_COMPARISON.md](../research/HARDWARE_COST_COMPARISON.md) | Hardware sourcing comparison — 28 September 2026 |
| [MARKET_LANDSCAPE.md](../research/MARKET_LANDSCAPE.md) | CNC controller market landscape |
| [POWER_ENTRY_REVIEW.md](../research/POWER_ENTRY_REVIEW.md) | Historical r0.1 power-entry source review |
| [SPI_FEASIBILITY.md](../research/SPI_FEASIBILITY.md) | CM5–FPGA SPI: source review and proof gates |
| [UI_REFERENCE_AUDIT.md](../research/UI_REFERENCE_AUDIT.md) | Existing UI candidate: static source audit |

The [initial controller investigation](../CNC_CONTROLLER_INVESTIGATION.md) and [route-s3 notes](../reports-notes.md) also retain their dated scope.

## Evidence records

Dated reports keep their recorded source, profile, limits, counts and failures. Older six-joint/two-encoder results are historical baseline evidence; passing software, ERC or ordinary DRC does not establish a physical machine rating. The latest unfinished board work is in the [17 October continuation](../reports/board-finish-20261017/README.md); the following top-level reports are primarily historical/component evidence.

| Record | Scope |
| --- | --- |
| [CNC1: actual LinuxCNC to actual FPGA RTL](../reports/CNC1_INTEGRATION.md) | Dated evidence; preserve the original source, profile and limits |
| [Commercial direction and licensing status](../reports/COMMERCIAL_DIRECTION.md) | 29 September commercial decision/status record |
| [Disconnected configuration service demonstration](../reports/CONFIGURATION_DEMO.md) | Dated evidence; preserve the original source, profile and limits |
| [Connected controller circuit review](../reports/CONNECTED_CONTROLLER.md) | Historical thirteen-sheet connected circuit, not the complete motherboard |
| [Core 5V converter circuit](../reports/CORE_CONVERTER.md) | Dated evidence; preserve the original source, profile and limits |
| [Baseline 22-channel digital-input circuit — review r0.1](../reports/DIGITAL_INPUTS.md) | Dated evidence; preserve the original source, profile and limits |
| [Two independent encoder power branches](../reports/ENCODER_POWER.md) | Dated evidence; preserve the original source, profile and limits |
| [Baseline two-ABZ receiver schematic block](../reports/ENCODER_RECEIVERS.md) | Dated evidence; preserve the original source, profile and limits |
| [Controller engineering status](../reports/ENGINEERING_STATUS.md) | Current source-bound status with dated chronological records |
| [ESP service implementation evidence](../reports/ESP_SERVICE_BUILD.md) | Dated evidence; preserve the original source, profile and limits |
| [ESP32-S3 service and recovery circuit](../reports/ESP_SERVICE_HARDWARE.md) | Dated evidence; preserve the original source, profile and limits |
| [Expanded motor-capacity power review](../reports/EXPANDED_POWER_REVIEW.md) | Dated evidence; preserve the original source, profile and limits |
| [Field-side 5 V power block — review r0.1](../reports/FIELD_POWER.md) | Dated evidence; preserve the original source, profile and limits |
| [FPGA core candidate review](../reports/FPGA_CORE.md) | Dated evidence; preserve the original source, profile and limits |
| [Actual FPGA synthesis: six STEP/DIR, two ABZ, CNC1 ABI2](../reports/FPGA_SYNTHESIS.md) | Dated evidence; preserve the original source, profile and limits |
| [FPGA reference endpoint validation — 28 September 2026](../reports/GATEWARE_VALIDATION.md) | Dated evidence; preserve the original source, profile and limits |
| [LinuxCNC integration: actual software execution](../reports/LINUXCNC_INTEGRATION.md) | Dated evidence; preserve the original source, profile and limits |
| [Baseline low-voltage regulator implementation](../reports/LOGIC_POWER.md) | Dated evidence; preserve the original source, profile and limits |
| [Independent watchdog and edge-armed output permission](../reports/MACHINE_PERMISSION.md) | Dated evidence; preserve the original source, profile and limits |
| [Disconnected module replacement and machine cartridge demonstration](../reports/MODULE_REPLACEMENT_DEMO.md) | Dated evidence; preserve the original source, profile and limits |
| [Durable calibration across actual LinuxCNC restarts](../reports/PERSISTENT_RUNTIME.md) | Dated evidence; preserve the original source, profile and limits |
| [Core and field power-entry circuits](../reports/POWER_ENTRY.md) | Dated evidence; preserve the original source, profile and limits |
| [Autonomous rail qualification and reset candidate](../reports/POWER_SEQUENCE.md) | Dated evidence; preserve the original source, profile and limits |
| [Independent processor integration review](../reports/PROCESSOR_INTEGRATION_REVIEW.md) | Dated evidence; preserve the original source, profile and limits |
| [Cartridge and module recovery through the common CLI](../reports/RECOVERY_CLI.md) | Dated evidence; preserve the original source, profile and limits |
| [Actual-runtime stopped configuration](../reports/RUNTIME_CONFIGURATION.md) | Dated evidence; preserve the original source, profile and limits |
| [Hardware-supervised SBC supply](../reports/SBC_POWER.md) | Dated evidence; preserve the original source, profile and limits |
| [Six-joint differential transmitter schematic block](../reports/SIX_JOINT_TRANSMITTER.md) | Dated evidence; preserve the original source, profile and limits |
| [CNC1 Linux SPI transport implementation](../reports/SPI_TRANSPORT_IMPLEMENTATION.md) | Dated evidence; preserve the original source, profile and limits |
| [Twelve-channel STEP/DIR circuit](../reports/TWELVE_CHANNEL_TRANSMITTER.md) | Dated evidence; preserve the original source, profile and limits |
| [Validation record](../reports/VALIDATION.md) | Historical validation ledger; newer receipts are linked from engineering status |

## Evidence classes

| Evidence | What it establishes |
| --- | --- |
| Source inspection | Recorded declarations, pin/contract review and document consistency |
| Host tests | Behavior under the named host fixtures; no electrical or mechanical rating |
| Target compilation | An exact target toolchain compiles/links that source; no executed hardware behavior |
| HDL simulation | Digital behavior under specified clocks, stimulus and models |
| FPGA synthesis/mapping | Structural/resource results for the named core/tool options; no physical-wrapper or routed timing closure unless separately demonstrated |
| Circuit ERC | Schematic rule-check results with their retained warnings |
| Board DRC/native connectivity | Rules and copper/pad relationships for an exact saved/refilled/cached board; no automatic current, SI, assembly or safety qualification |
| Physical measurements | Only the actual instruments, hardware, conditions and limits recorded |

This review updates active guidance. It preserves generated catalogue IDs, user source notes, historical reports, frozen evidence, original machine configurations and the external IS-1 archive. See the [review record](../reports/documentation-refresh-20261018/README.md) for coverage and checks.
