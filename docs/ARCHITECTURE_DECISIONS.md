# CNC controller architecture decisions

Reviewed 18 October 2026. [Documentation index](README.md) · [current engineering evidence](../reports/ENGINEERING_STATUS.md). This is a chronological register: earlier alternatives remain dated decision history where later ADRs supersede them.

Status: chronological decision register, reconciled 30 September 2026. **Current requirement precedence:** ADR-024 adopts one active motherboard with a soldered FPGA and all twelve motor interfaces, four ABZ encoders, 24 general DI/16 smart DO and all remaining required interfaces; purchased compute/ESP/storage modules remain replaceable. The passive base/thirteen custom cards, removable FPGA/field cards and custom MX4/XTB motors-9–12 path are superseded physical scope. Retain per-motor enable/alarm, identity/sequence/freshness/CRC, independent fault-to-inhibit no greater than 20 ms, safe defaults, offline settings/licence recovery and no automatic restart. US$400 is a preliminary controller-only reference with separately complete costed screen kits. The untouched external IS-1/CNC3 work remains reusable logical/electrical/source history; the physical transition is [IS-2](MOTHERBOARD_IS2.md), not an unversioned change to a deployed interface. See [current gates](CURRENT_ACCEPTANCE_GATES.md), [project memory](../PROJECT_MEMORY.md) and [current audit](../reports/audit-2026-09-30/AUDIT_REPORT.md).

Statuses mean: **working baseline** = a reversible direction used for design work; **open** = competing choices still need evidence; **deferred** = explicitly outside the first implementation unless requirements bring it back; **user constraint** = stated by the user. A working baseline is not a purchase authorization.

## ADR-001 — Work deeply before procurement

**Status: user constraint.** The user wants to get as far as possible before ordering anything.

Decision: advance requirements, source audits, simulation, protocols, resource allocation, calculations, and CAD before procurement. Maintain a visible distinction between simulated, compiled, synthesized, and measured results. No component purchase or hardware commitment is implied.

Consequence: the project can make substantial progress now. Physical latency, EMC, thermal behavior, signal integrity, sensor/drive compatibility, and machine stopping behavior remain things that a later prototype must validate.

Evidence for closure: architecture and design review package with a specific question for each proposed prototype test, not merely a parts list.

## ADR-002 — Place motion authority inside the controller

**Status: working baseline, derived from the user's modern laptop/network interface preference.**

Decision: the external laptop supplies a browser/user interface. The enclosure contains the interpreter/planner/control execution needed for the selected operating mode. External communication carries jobs, requests, configuration, and telemetry.

Alternatives: a conventional external LinuxCNC real-time host; a host-planned timestamp stream; a full local MCU controller; embedded Linux plus timing hardware. The first remains a useful comparison/test architecture. The last two best fit the current appliance concept, subject to required machine features.

Consequence: laptop OS and USB-Ethernet adapters are mainly HMI choices. Controller-local storage, permissions, UI session handling, and a disconnect policy become product requirements. A host-planned buffered stream is not equivalent to autonomous full-job execution.

Revisit if a required application has an external-host dependency that is worth preserving.

## ADR-003 — Define real time by deadlines and behavior

**Status: timing requirements remain a working baseline; implementation narrowed by ADR-020 to PREEMPT_RT Linux/LinuxCNC plus FPGA.**

Decision: specify pulse timing, capture accuracy, maximum control-cycle age, queue horizons, and fault response. Evaluate bare-metal/RTOS MCU, PREEMPT_RT Linux, PIO, and FPGA implementations against those requirements.

Rationale: an FPGA does not supply a CNC interpreter; an RTOS does not automatically bound every driver; a real-time Linux kernel does not validate the complete machine. PREEMPT_RT scheduling mechanisms are relevant evidence, not a performance certificate. [Linux kernel documentation](https://docs.kernel.org/core-api/real-time/theory.html)

Consequence: userspace LinuxCNC under a real-time kernel remains a legitimate candidate. The phrase "kernel level" does not prematurely require a new kernel module.

Closure: quantified timing/feedback requirements and a mapping from each deadline to the executing hardware/software.

## ADR-004 — Earlier compute alternatives

**Status: superseded for the working implementation by ADR-020; alternatives retained as research.**

Candidates: A) supported MCU firmware with an ESP service processor when useful; B) embedded LinuxCNC plus FPGA/timing processor and optional ESP; C) new ESP32-S31/P4 architecture with explicit firmware-development scope.

Decision method: required machining features first; then software maturity, I/O/timing resources, memory, electrical integration, maintainability, and development scope. Clock speed and radio count do not determine the result.

No chip is selected. A buildable branch can serve as a simulation/reference implementation without forcing the eventual PCB to use it.

Closure: a pinned firmware build and machine-feature demonstration; feasible resource map; comparative implementation effort; no unresolved architectural blocker.

## ADR-005 — Give one controller exclusive motion ownership

**Status: working baseline.**

Decision: one selected motion source owns step, direction, enable, spindle, and auxiliary outputs. An ESP service processor requests actions through a checked interface. It does not drive parallel motor-command GPIOs.

If a later alternate firmware mode uses another processor, hand over only through a disarmed state with hardware-enforced mutual exclusion and a complete state/position-validity check. The selector must cover every actuator path, not just STEP.

Consequence: hot failover is deferred. Stopped recovery and useful diagnostics remain achievable.

Closure: output-ownership schematic/truth table and reset/handover test scenarios.

## ADR-006 — Separate service communication from motion timing

**Status: working baseline.**

Decision: Wi-Fi, Bluetooth, USB-C, and external Ethernet terminate in a bounded service interface. If a separate cyclic motion link exists inside the controller, give it an explicit deadline/resource budget and failure contract.

Rationale: uploading a file and delivering fresh servo commands are different uses of a link. Mesa's Ethernet driver has its own real-time networking constraints, which do not automatically apply to an autonomous controller's external browser connection. [hm2_eth requirements](https://linuxcnc.org/docs/2.9/html/man/man9/hm2_eth.9.html)

Consequence: Ethernet speed, USB connector type, and wireless throughput can be selected for actual interface workloads. A USB-C connector alone does not establish USB4, power delivery, or real-time behavior.

Closure: service/internal-link diagrams, capacity calculation, and disconnect/freshness behavior.

## ADR-007 — Define ESP help before calling it backup

**Status: open role, working service/recovery baseline.**

Candidate roles: networking/UI; panel/sensors; diagnostics and reset-cause logging; maintenance/recovery; standalone alternate operating mode; full motion controller. These roles can be combined only after resource and failure analysis.

Decision: model service/recovery assistance first. Do not assume seamless continued motion after primary failure. A helper on the same regulator, reset line, and software configuration has shared failure modes.

Consequence: independent power/reset control may be valuable, but redundant safety or hot takeover is not claimed. If ESP runs the actual CNC firmware, it is the primary motion controller in that mode and must meet all motion requirements.

Closure: named failure cases the ESP must handle, ownership messages, electrical separation, and tests.

## ADR-008 — Use external motor drives as the first interface model

**Status: working baseline, subject to actual machine.**

Decision: size the first concept around external step/direction or other selected servo drives. Keep high-power motor-current switching out of the controller core until there is a reason to integrate it.

Rationale: the investigation concerns a Mesa/Acorn-style controller; printer-board motor-driver modules are a different power/thermal/interface decision. This is a scope choice, not a claim that onboard motor drivers are inherently unsuitable.

Consequence: drive documentation determines pulse levels, enabling, feedback, and protective stop integration. Field electronics still need a real design.

Revisit if a known low-power machine benefits from integrated drives. EtherCAT, analog, or other external drive interfaces remain first-class candidates for the expanded platform.

## ADR-009 — Distinguish feedback roles

**Status: open requirements.**

Decision: label every encoder/scale channel as drive-local feedback, controller position-loop feedback, following-error monitor, spindle synchronization, homing/index reference, or display-only measurement. Do not use "closed loop" without saying which loop closes where.

Consequence: a pulse count returned by a step generator is commanded/generated motion evidence, not proof of table motion. Adding encoder connectors does not automatically implement control laws, threading, or scale compensation. [HostMot2 functions](https://linuxcnc.org/docs/2.9/html/man/man9/hostmot2.9.html)

Closure: control-loop block diagrams and exact machine programs/scenarios that need each feedback channel.

## ADR-010 — Historical six-joint and I/O sizing study

**Status: six-joint worksheet retained as historical sizing evidence; product capacity resolved by ADR-024.**

Decision: use the six-joint worksheet to expose pin, PIO, DMA, timer, bandwidth, and connector demands. Do not freeze it as the product specification.

Consequence: resource budgeting occurs before a processor/package is selected. Independent gantry joints, spindle feedback, probe capture, and drive faults cannot disappear merely to fit an attractive chip. Slow serial I/O expansion remains an option where its latency and fault behavior are acceptable.

Closure: agreed first machine profile and a complete resource ledger with reserved debug/recovery capacity.

## ADR-011 — Inhibit outputs through boot, reset, update, and invalid state

**Status: working baseline.**

Decision: output permission requires valid rails, initialized timing hardware, valid configuration, a current control session/state, and an explicit arming transition. Power restoration or a firmware reboot does not resume queued motion automatically.

Direction, step, enable, analog spindle, run command, and inductive auxiliaries each need their own reset truth table. Immediate removal of pulse commands, controlled deceleration, torque removal, and brake application are distinct mechanisms.

Consequence: use supervisor/gating hardware appropriate to the eventual design. A generic watchdog is an operational feature, not a claim of certified machine safety. Machine protective functions remain an explicitly designed system.

Closure: reset/partial-power/fault truth table, stop-response analysis, and schematic review.

## ADR-012 — Preserve a wired maintenance path and defined USB power behavior

**Status: working baseline.**

Decision: provide a recovery path independent of functioning Wi-Fi/application firmware, through boot controls plus wired programming/debug appropriate to the processor. USB-C device/service use is the leading external connector option; data speed and power role remain open.

Consequence: a USB-only session cannot grant machine output permission. Prevent rail backfeed and partial-power parasitic paths. Recovery does not depend on permanently exposing raw debug access over the network.

Closure: service-mode power diagram, programming procedure, interrupted-update recovery test plan, and debug connector contract.

## ADR-013 — Version configuration and firmware together

**Status: working baseline.**

Decision: store hardware identity, firmware/gateware versions, protocol ABI, and configuration schema/hash. Validate compatibility before arming. Configuration edits are proposed, checked, and committed atomically under a defined operating state.

Consequence: pins, scaling, polarity, encoder ratios, travel limits, and spindle settings must not change invisibly during execution. An image's checksum proves data integrity, not that it is correct for a board or machine.

Closure: version manifest, migration/rollback policy, configuration validation, and interrupted-update simulations.

## ADR-014 — Do not invent a protocol unless existing integration requires it

**Status: open implementation, working reuse baseline.**

Decision: audit existing firmware/networking, LinuxCNC/HAL, and supported endpoint interfaces before choosing a custom transport. For any new interface, specify joint atomicity, session identity, sequence numbers, freshness, queue bounds, acknowledgments, error reports, and cancellation.

Consequence: an experimental protocol simulator is useful pre-order work, but its existence does not justify replacing mature firmware or silently changing existing protocol semantics. A new FPGA does not become HostMot2 compatible by implementing similar register names.

Closure: documented reason for reuse/adaptation/new protocol, compatibility tests, and malformed/stale/duplicate/reordered message scenarios.

## ADR-015 — Use modular compute until integration earns its complexity

**Status: working baseline for Linux branch; open for MCU branches.**

Decision: compare a supported module/carrier architecture against bare-silicon design. For Linux, begin from a module's documented carrier interface rather than taking on CPU/DDR bring-up by default. For radio MCUs, compare module antenna/power/flash integration against discrete implementation.

Consequence: the first custom work can concentrate on machine I/O, timing, recovery, and integration. Module selection still needs lifecycle, thermal, connector, pin-access, firmware, and mechanical review. CM5 is a candidate example, not a selected part. [CM5 carrier information](https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf)

Closure: a documented reason to integrate further, with measurable benefit and closed implementation resources.

## ADR-016 — Freeze evidence before freezing a schematic

**Status: working baseline.**

Decision: selected parts require a compatible set of official datasheet, hardware guide, reference design, errata, SDK, toolchain, and silicon/package revision. Record document revision and access date. Resolve conflicts using the selected manufacturer's current authoritative documentation/support before layout.

Rationale: new devices such as S31 and P4 expose preliminary documentation and revision-specific behavior; broad family/marketing specifications are insufficient for pin and power design. [S31 datasheet](https://documentation.espressif.com/esp32-s31_datasheet_en.html), [P4 hardware guide](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/index.html)

Consequence: no guessed pin assignments, copied neighboring-chip footprints, or implied finished BOM. Firmware source support is checked separately from the vendor's availability announcement.

Closure: source/errata manifest and a reviewed schematic/package/peripheral map.

## ADR-017 — Build broad voltage support as a family of rated interfaces

**Status: retained typed-interface requirement; replaceable custom-bank implementation superseded by ADR-024.**

The user wants an extremely advanced controller that can support many relay/control voltages and machine systems. Decision: implement that ambition through typed, isolated/protected motherboard interfaces and compatible external relays, contactors, drives and qualified accessory modules. The required base I/O is soldered on one board; typed interface families do not require a new custom-card rack.

Each interface states its operating voltage/current range, AC/DC compatibility, load category, inrush, insulation/isolation, timing, connector, and failure behavior. Nominal 24 V digital I/O, differential step/encoder interfaces, 0–10 V/±10 V analog, 4–20 mA, dry contacts, serial fieldbuses, and networked servo interfaces belong to separate defined families.

Consequence: no connector accepts arbitrary voltage; software cannot change physical ratings. Coil ratings and contact/load ratings are separate, and high-energy switching stays outside the logic core in separately rated devices for this working architecture. The system can control many voltages by choosing the correct interface, without bringing every voltage onto one universal PCB.

Closure: module taxonomy, electrical contracts, isolation/power map, keyed connector strategy, and at least one complete channel design for each selected first-release family. [Phoenix Contact relay selection](https://assets.phoenixcontact.com/file/e21ac3ed-f64b-47b4-a441-dad823f566f8/media/original?US_PLC-Relay-Brochure-with-Cross-Section-Spread_20220823.pdf=), [TI configurable analog reference](https://www.ti.com/tool/TIDA-00118)

## ADR-018 — Separate platform extensibility from first-release feature claims

**Status: user ambition; requirements open.**

Decision: model advanced mill/lathe/plasma, spindle synchronization, rigid tapping, multi-axis kinematics, linear-scale feedback, tool changers/turrets, analog servos, and networked drives as explicit capability packages. Each has hardware, firmware, sequencing, and verification dependencies.

Consequence: the platform's expansion/ownership contracts should not prevent these functions, but adding ports does not implement them. ADR-020 selects the LinuxCNC/FPGA working direction; the earlier MCU candidates remain historical comparison studies. Avoid promising every advanced capability merely because a processor is fast.

Closure: feature dependency matrix and repeatable representative program/fault tests; one committed first-machine profile can validate the platform while other profiles remain development work.

## ADR-019 — Type expansion by deadline and electrical class

**Status: working baseline.**

Decision: separate slow machine I/O, sampled analog, timestamped events, encoder streams, and synchronized actuator commands in the module contract. Evaluate CAN/RS-485 for suitable distributed services and EtherCAT or another justified deterministic network for motion where needed; a general expansion bus is not assumed to satisfy every class.

Consequence: module enumeration/configuration is insufficient by itself. Each module has local output defaults, command freshness, a versioned interface, power/reset behavior, and a bounded failure effect. Replacement is power-off by default; hot-plug is a separate design feature.

Closure: bus/clock/power budget, module removal/failure scenarios, timing-class tests, and a reviewed electrical connector contract. [EtherCAT technology reference](https://www.ethercat.org/en/technology.html)

## Later decisions

The following later decisions narrow the working design; they do not authorize procurement or claim a validated product.

## ADR-020 — Use local LinuxCNC, FPGA timing and an ESP service helper

**Status: working baseline following the user's architecture discussion; exact parts remain open.**

Decision: PREEMPT_RT Linux/LinuxCNC supplies local machine execution. A custom FPGA supplies pulse generation, feedback capture and defined I/O/watchdog behavior. ESP-IDF firmware supplies diagnostics and stopped recovery. This replaces the earlier H7/grblHAL main-controller proposal rather than adding a fourth processor. CM5 remains a feasibility/cost reference, not a frozen production part.

The included touchscreen adds a local browser/graphics workload to the compute study. An external browser is additional access. Browser loss follows the selected local-job policy, with expired interactive jog authority handled separately. ESP failure handling depends on installed functions: diagnostic-only loss can be advisory under the machine policy, while loss of an essential ESP-managed service/readiness must produce the defined machine response and block restart. The later [accessory-automation contract](ESP_ACCESSORY_AUTOMATION.md) extends the proposed role without changing the current diagnostic firmware into an actuator implementation. Linux failure requires the defined machine fault response; seamless ESP takeover is not selected.

Closure: actual LinuxCNC integration, gateware/driver evidence, loaded timing with local graphics, and measured failure behavior. [Build plan](BUILD_PLAN.md)

## ADR-021 — Investigate internal SPI before adding internal Ethernet

**Status: working feasibility direction, not a selected production transport.**

Decision: evaluate dedicated CM5–FPGA SPI while retaining external Ethernet on the Linux host. LinuxCNC v2.9.10 explicitly recognizes CM5, but custom board identity and compatible FPGA semantics require deliberate host/gateware work. Compare full interface cost and implementation effort; no automatic savings or timing qualification is claimed.

Closure: pin/bank/driver-ownership review, compatible endpoint simulation and synthesis, then a bounded physical step/encoder/fault test before final production PCB layout. CAD import development proceeds independently. [Pinned SPI audit](../research/SPI_FEASIBILITY.md)

## ADR-022 — Include the display in the Mesa-price cost gate

**Status: display-tier requirement retained; the Mesa-priced bundled-cost direction below is historical and superseded by the controller-assembly/completely costed package commercial policy. Exact qualified panels and selling prices remain open.**

Decision, updated for the user's 28 September screen clarification: offer included-screen packages in 7-, 10-, 12-, 14-, 18- and 21-inch classes and further qualified sizes. The 21.5-inch FHD reference becomes one large-screen option; it no longer governs every package. Use a shared responsive application and keep display size separate from compute/I/O capacity. Reopen compute selection where complete cost demands it. Cost nominal 24 V industrial I/O through explicitly specified circuits; keep the original six-joint study distinct from the expanded candidate and cost each complete screen package before claiming prices. Margin examples and US$249 are illustrative, not a requirement for identical pricing across tiers. [Display-tier plan](DISPLAY_TIERS.md)

Closure: complete delivered and assembled unit cost at consistent quantities, actual display configuration, quoted unknown blocks and a supportable selling-price calculation. [Core terminal/cost worksheet](CORE_INTERFACE_COSTING.md), [display study](../research/DISPLAY_COST_STUDY.md)

## ADR-023 — Keep machine setup independent of replaceable electronics

**Status: retained recovery requirement; the physical alternatives below are historical and superseded by ADR-024. Storage implementation and physical qualification remain open.**

Retained decision: wiring stays terminated in keyed pluggable terminal/harness groups. ADR-024 resolves the repair units as purchased compute/ESP/storage modules and the whole motherboard; the earlier fixed-base/custom-card comparison is superseded. A protected, replaceable settings provision must carry complete machine settings, with validated redundant generations, main-storage mirror and offline export. Its exact physical implementation remains to qualify. It does not carry obsolete factory calibration into new measurement electronics. Module/board identity, calibration and firmware/recovery images have separate storage and lifecycle contracts.

Supported replacements arrive with compatible firmware installed, or have no application firmware. Power-off replacement restores compatible assignments while holding outputs inhibited and invalidating affected checks. New-compute import has explicit machine identity and cannot weaken normal same-store backup checks. No restored file establishes current homing, drive readiness, held workpiece registration or job authority. A verified offline update may still be needed; absence of manual reflashing is the product target, not a promise that software never changes.

Closure: [repair/memory specification](MODULAR_REPAIR_AND_MEMORY.md), bounded disconnected replacement and interrupted-save tests, measured storage workload, connector and fault-containment design, complete cost delta, then powered-off physical replacement with wiring retained and all affected verification demonstrated. The existing six/two evidence and expanded eight/four proposal remain distinct.

## Historical decision gate before ADR-024

The [platform roadmap](PLATFORM_ROADMAP.md) records the latest additions: all 200 supplied feature proposals, a separately costed eight-motor/four-encoder candidate, a power-off plasma module/harness/profile upgrade path and supported third-party Modbus accessories. The existing six-joint ledger/costs remain a named comparison baseline. These additions do not inherit its implementation evidence or freeze an expanded board.

The preferred next carrier study is the [CM4/CM5-style mechanical family](COMPUTE_CARRIER_STRATEGY.md), with exact supported modules determined by electrical, software, thermal, real-time and cost qualification. [BTT CB2](../research/BTT_COMPUTE_REVIEW.md) is an active alternative. Shared connectors do not establish a universal compatible socket. Earlier host studies remain comparison evidence rather than purchase selections.

The immediate gate is a credible definition of what the platform and first target machine must do, a working software model, and evidence that at least one architecture can provide it.

Work continues in parallel on topology-independent interfaces and state/fault behavior. Requirements still needed for final hardware include machine type, drive interfaces, feedback purpose, maximum rates, field loads/power, enclosure/cables, and mandatory machining functions. Until they are known, conditional circuit/resource options remain useful; manufacturing files and purchase quantities remain uncommitted.


## ADR-024 — Consolidate into one motherboard with commodity modules

**Status: explicit user decision, 30 September 2026; resolves the physical architecture conflict.**

Decision: one active custom PCB carries the FPGA/clock/configuration/supervision, all twelve complete differential STEP/DIR motor channels with individual enable/alarm, four standard ABZ encoders, 24 general DI, 16 smart DO with qualified diagnostics, probe/frequency/PWM/process paths, analog I/O, RS-485/CAN, protected power, independent watchdog/permission, labeled RGB/status indicators and terminal groups. Reuse validated circuit/source work; integrate and route the missing interfaces rather than restart processor architecture. MC r0.4/revision-14 is reusable historical partial 327-part circuit/native evidence. Later integrated source/CAD and isolated board continuations exist; none is a finished qualified motherboard.

Use actual sockets for qualified purchased CM4/CM5 compute modules, separately verified BTT CB2/CB1 alternatives, a replaceable ESP board/module and qualified storage/settings media. Optional standardized accessory connections and future verified adapters extend capabilities; they do not recreate mandatory custom motion, motor, input, output, power, analog/comms or service daughterboards. All twelve motor interfaces belong to the base target; neither eight-channel depopulation nor a paid unlock of fitted motors 9–12 is adopted.

Explicit supersession: the passive fixed wiring base, thirteen-position custom rack/cage, removable FPGA/custom field-interface cards and MX4/XTB motors-9–12 expansion path no longer define the product. Their requirements, source and cost studies remain preserved as dated history. The user-supplied rack-cost figures and all-twelve-interface saving are historical estimates requiring traceable complete BOM comparison; this decision does not establish a finished cheaper board or margin.

Retained contracts: machine capacity and interfaces, actual electrical ratings, protected power/defaults, independent no-greater-than-20-ms watchdog/inhibit, single output/motion owner, versioned identity/calibration, sequence/freshness/CRC before serialized outputs change, telemetry validity/age, configuration retention and offline provisioning, commercially paid offline entitlement across legitimate replacement, third-party licensing, simple wiring and common UI/CLI configuration, screens in 7/10/12/14/18/21-inch classes and further qualified sizes, optional AI and no automatic motion restart. The 12/24-V sourcing/sinking/2-A output proposal requires a qualified versioned circuit revision; it does not increase the retained 0.5-A/channel and 2-A/group contract by software.

Service consequence: purchased compute/ESP/settings modules exchange with power off. Failure of soldered motion/I/O/power circuitry requires whole-motherboard service through keyed pluggable terminal/harness groups, preserving conductor terminations and machine recovery data. Moving terminal groups and verifying a board-wide calibration/capability change is a separate service case from a commodity-module swap; no five-minute whole-board guarantee or old virtual-card proof is inherited. Program/test supported spare boards and modules for offline recovery; preserve licences without restoring position/homing/run authority.

Integration consequence: preserve external frozen IS-1 unchanged and use [MOTHERBOARD_IS2.md](MOTHERBOARD_IS2.md) for explicit physical supersession. Logical integrated regions use observed motherboard revision/identity, rated capabilities and calibration records; do not force old removable-card presence bits or fabricate card serials. Coordinate any identity/presence/protocol/schema/default-state changes with gateware, driver and service owners, preserve channel identities where feasible, and prove compatibility rather than claiming it.

Closure: reconciled complete schematic and exact FPGA bank/pin map; reviewed commodity module/socket/mechanics; routed complete PCB with uncapped connectivity/ERC/DRC closure; real stackup/rules/fabrication/BOM/CPL/assembly/program/test package; complete cost at 1/10/100 and later 1,000; and physical loaded timing/fault/power/thermal/EMC/service qualification. Source/host tests, synthesis and ERC alone cannot close it. No orders or supplier submission are authorized here.

Implementation checkpoint, 17 October: [board continuation](../reports/board-finish-20261017/README.md) recovers R299 at 1,172 remaining joins. Its isolated corrected cached native DRC is 0 ordinary errors/332 warnings/0 parity, while stage1 full refill remains pending and stage2–4 are input-only diagnostics. Real Efinity pin/bank checks pass; canonical disconnected SIM2 now maps at 15,805 LUT4 + 2,107 ADD = 17,912 with retained functions and event capacity. Complete physical-wrapper fit/routed timing, current/return/assembly and physical/manufacturing gates remain open. These evidence updates implement no architecture change and adopt no hardware revision.
