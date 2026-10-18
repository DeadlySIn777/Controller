# Historical expanded hardware target: eight motor channels and four encoders

**30 September physical-topology supersession:** The latest user directs one active custom motherboard with all twelve motor interfaces fitted, purchased compute/ESP/settings modules and qualified accessories. [MOTHERBOARD_IS2.md](MOTHERBOARD_IS2.md) is the governing physical contract. The eight-plus-custom-four, fixed-passive-base/removable-FPGA statements below and the linked machine-readable target are preserved historical studies; they do not select the current product topology. Logical field functions/limits and the distinct six-joint baseline remain relevant inputs.

28 September 2026, requirements reconciled 30 September 2026. **Eight motors standard, expandable to twelve, is the minimum product requirement. The detailed circuits and performance goals in `expanded-8j-4enc` remain an unfinished design study, not a completed board or frozen release specification.** The study translates the supplied architecture notes, lines 372–750 of `research/user-notes/2026-09-28-feature-platform.txt`, into engineering work. The existing `baseline-6j-2enc` remains the historical six-joint/two-encoder comparison with its own ledger, cost evidence and implementation limits; it is not a candidate minimum product.

**Adopted requirements take precedence over the earlier candidate wording:** motors 9–12 use a plug-in expansion module, with a twelve-motor version shipped factory-fitted; every motor preserves an individual enable and alarm, while a global interlock is not counted as an individual enable; all 24 general DI and 16 general DO remain additional to motor control resources. Use a fixed wiring base and removable FPGA motion card with clock, configuration flash and supervisory circuits. Preserve the 20 ms fault-to-inhibit bound. Serial general-I/O transport is permitted only with identity, sequence/freshness and CRC validated before outputs change. US$400 is the preliminary controller-assembly reference, with expansion, screens and other complete kits separately costed. These are memory-recorded user decisions requiring implementation and qualification, not evidence that the current design meets them. See [project memory](../PROJECT_MEMORY.md), [8-to-12 design record](MOTION_EXPANSION_8_TO_12.md) and [repair specification](MODULAR_REPAIR_AND_MEMORY.md).

This document and its [machine-readable target](../research/expanded-hardware-target.json) do not revise the existing schematic, pin map, power budget, gateware, prices or validation results. Existing tests and partial ERC evidence apply to the existing artifacts, not automatically to this expansion. See the [baseline electrical design](ELECTRICAL_DESIGN.md), [baseline costing scope](CORE_INTERFACE_COSTING.md), [current protocol](../gateware/PROTOCOL.md) and [engineering status](../reports/ENGINEERING_STATUS.md).

## Eight-motor scope and historical count reconciliation

“Additional” means physically separate resources. General DI exclude drive alarms, probes, frequency and encoder inputs. General DO exclude drive enables, PWM and process enables. Ordinary spindle forward/reverse and coolant functions consume assignments within the general DO group. The following original eight/four table is retained for count reconciliation; it does not allocate the extra four motors, card identities/integrity, supervisory circuitry or all simultaneous expansion resources. Complete those new allocations separately rather than treating 92 as the finished product GPIO count.

| Resource | Historical six-joint comparison | Original eight/four allocation study | Direct signals in that study |
|---|---:|---:|---:|
| Differential STEP/DIR motor commands | 6 motors | 8 motors, M0–M7 | 16 |
| Individual drive-enable commands | 6 sourcing outputs | 8 isolated switching interfaces | 8 |
| Individual drive-alarm inputs | 6 | 8 | 8 |
| Full differential A/B/index encoder ports | 2 | 4, ENC0–ENC3 | 12 |
| Additional general nominal-24-V DI | 16 | 24 | 24 |
| Additional general nominal-24-V DO | 8 | 16 | 16 |
| Additional fast probe inputs | 0; consume general DI | 2 | 2 |
| Additional frequency inputs | 0 | 2 | 2 |
| Hardware PWM commands | 0 dedicated | 2 | 2 |
| Independently inhibited process enables | 0 dedicated | 2 | 2 |
| **Direct digital signal total** | **54** | **92** | **92** |
| Analog command outputs | 1 | 2 isolated 0–10 V paths | Serial/control resources counted separately |
| Analog measurement inputs | 0 | 4 protected low-voltage paths | Serial/control resources counted separately |
| Field buses | Expansion not defined | 1 isolated RS-485, 1 isolated CAN | Controllers, bus pins and control/fault resources additional |
| Timing expansion | Interface not defined | 1 short internal synchronized backplane | Additional pins and power |

The increase is **38 direct digital signals**. Differential line pairs are one logical signal each here; terminal contacts are a different count. Host SPI, ADC/DAC buses, bus controllers, clocks, configuration, reset, useful-progress watchdog, permission gates, power/fault telemetry and expansion are excluded from 92. Reusing the baseline's 30 support reservations would give 122 signals arithmetically, but that is not an expanded allocation: the new analog, bus and expansion circuits can change that support count.

Motor channels are joints/actuators, not necessarily independent Cartesian axes. Profiles may map M0–M7 to a dual-drive gantry, five-axis machine, lathe accessories or printer motors. A lathe allocating ENC0 to spindle, ENC1/2 to linear scales and ENC3 to a handwheel consumes all four ports. Four encoders do not provide external feedback for eight motors. These are allocation examples, not implemented machine profiles.

## Electrical interfaces to specify

All values in this section are **proposed design envelopes**. Component absolute maxima, isolation test voltages and marketing interface names are not connector operating ratings.

| Interface | Starting design direction | Required before approving a circuit |
|---|---|---|
| STEP/DIR | Sixteen 5-V-supplied differential transmitters, driven by 3.3 V logic; retain baseline nonisolated signal-domain assumption until explicitly changed | Loaded differential voltage/current, compatible drive receiver, common mode, termination, cable length, pulse distortion, power-off behavior and protection. “5 V differential” alone does not establish compatibility with an optocoupler input. |
| Drive enable | Eight independently controlled, floating two-terminal isolated switches | DC voltage/current, permitted polarity, leakage, on-resistance, turn-on/off time, isolation grouping/working voltage, stuck-open/closed response and remote-drive disabled state. MPN and ratings unselected. This replaces the baseline 50 mA sourcing-enable topology; it is not just two extra outputs. |
| Alarm + general DI | 32 protected nominal-24-V DC inputs: 8 alarms plus 24 DI | Starting comparison envelope: 0–30 V, low 0–5 V, high 15–30 V, intermediate undefined; PNP/contact-to-positive wiring as baseline. Recalculate thresholds, currents, filters, transients and group isolation. NPN, AC or other voltage families need separately specified circuits/adapters. |
| General DO | Sixteen protected sourcing outputs; starting 18–30 V supply, 0.5 A/channel target | Decide simultaneous total and bank current, inrush duration, inductive clamp energy, thermal limits, leakage, diagnostics and off-state behavior. Cost all 16 separately from enables/process outputs. |
| Encoder | Four differential A/B/index ports, protected 5 V sensor power per port | Encoder current allocation, receiver common mode, open-wire behavior, termination, index width, edge skew, timing/filter options and supported single-ended adapter. Encoder supply and line inputs are not 24 V ports. |
| Fast probe | Two dedicated event inputs with protected, typed sensor supply/return | Dry-contact versus electronic-probe front ends, polarity, latency/jitter, minimum pulse, debounce, wire-break handling, timestamp and captured counter set. Do not assume ordinary DI filtering meets capture timing. |
| Frequency | Two differential receivers and hardware counters | At least 1 MHz qualification goal plus defined margin; voltage/common mode, minimum high/low times, gate/period measurement modes, timeout, overflow and calibration. A separately rated isolation module handles plasma measurement. |
| PWM | Two buffered logic commands | Select output voltage, load, polarity, fail state, frequency/resolution pairs and synchronization; no 24 V power implied. |
| Process enable | Two independently inhibited commands with process-specific conditioning | Select isolated contact/switch topology and electrical ratings for source control. Define independent inhibit, polarity and response time; ordinary general DO must not bypass it. |
| Analog outputs | Two isolated 0–10 V command paths | Minimum receiver load, output current, effective accuracy/resolution, settling, reference, calibration, zero clamp and run/enable withdrawal. Decide shared versus independent analog isolation domains explicitly. |
| Analog inputs | Four protected low-voltage measurement paths | Actual ranges, input impedance, common mode, bandwidth, sample rate, accuracy, reference, isolation groups and overload recovery. A 4–20 mA option needs a rated burden/protection circuit; raw plasma voltage never enters these ports. |
| RS-485 and CAN | One isolated physical interface each | Protocol/controller ownership, rates, cable/termination/bias, isolated power, fault states and software interoperability. A connector and transceiver do not implement Modbus or an accessory's CAN protocol. |

The input and output envelope intentionally remains bounded. Relay/contact modules may switch a separately supplied load only within their specified AC/DC voltage, current and load category. Higher-voltage power stays outside the logic core through explicitly rated modules or external equipment.

An enable switch that opens on controller power loss does not guarantee the drive disables. For example, the manufacturer’s **DM542T V4** manual specifies that applying its enable voltage disables the drive and documents an unconnected default. It also requires selecting the 5 V control-input setting when using 5 V signalling. Use this as a compatibility test case, not a declaration that the provisional transmitter can drive it. Every profile must define command polarity, startup, cable loss, controller power loss and the machine's independent stop/brake arrangement. [Manufacturer manual, connector and sequence sections](https://omc-stepperonline.com/download/DM542T_V4.0.pdf)

## Connector proposal, before footprint or pin approval

The notes contain the following **tentative contact order**. It is neither a vendor pinout nor a wiring instruction for an existing board. Connector family, keying, pitch, current, touch protection, shield arrangement, mating plug, harness and silkscreen are still open. No FPGA package balls are assigned here.

| Group | Tentative contact order from the notes |
|---|---|
| M0–M7, ten contacts each | 1 STEP+, 2 STEP−, 3 DIR+, 4 DIR−, 5 ENABLE_SW1, 6 ENABLE_SW2, 7 ALARM_IN, 8 ALARM_COM, 9 SIGNAL_0V, 10 SHIELD/CHASSIS |
| ENC0–ENC3, eight contacts each | 1 protected +5 V, 2 encoder 0 V, 3 A+, 4 A−, 5 B+, 6 B−, 7 INDEX+, 8 INDEX−; adjacent shield termination |
| Frequency group, six contacts | 1 protected +5 V, 2 signal 0 V, 3 FREQ0+, 4 FREQ0−, 5 FREQ1+, 6 FREQ1− |
| Probes, general I/O, analog, buses, expansion | Contact order deliberately unassigned pending electrical/keying review |

The motor and encoder suggestions alone total **112 contacts** (`8 × 10 + 4 × 8`), before general I/O, analog, power, buses or expansion. The baseline's 96-position connector allowance cannot price this design. Budget both board connectors and mating plugs/harnesses. Shield/chassis termination is distinct from signal return; the final shield arrangement may change this preliminary contact count. Motor winding terminals remain on external drives.

Generated wiring guidance must identify connector revision, drive/sensor model, voltage, signal direction, reference domain and permitted cable. Show compatible profiles and keyed adapters; prevent a 24 V supply from being mistaken for an encoder or PWM pin. Continuity/voltage checks precede motion in the guided commissioning procedure.

## Timing goals and implementation gap

| Function | Expanded qualification goal | Current evidence / required change |
|---|---|---|
| STEP rate | Up to 2,000,000 steps/s on each of eight channels simultaneously | Existing six-channel reference cap is **195,312.5 steps/s at assumed 50 MHz**; baseline electrical study goal is **250,000 steps/s**, also unachieved physically. These three figures have different status. |
| Drive timing | Per-channel programmable STEP high/low, DIR setup/hold and enable sequencing delay | Existing reference uses common build-time 100-tick defaults (2 µs at 50 MHz); no completed per-drive runtime configuration contract. |
| Encoder | 10,000,000 quadrature count transitions/s per encoder, all four together | New complete-path goal; existing two-encoder reference has no proven physical maximum. Specify cycles/s separately from ×4 counts/s and include index behavior. |
| Frequency | At least 1,000,000 input cycles/s with defined margin, both channels | New receiver/counter/protocol work; not ordinary debounced DI. |
| Probe | Hardware event timestamp and coherent relevant position capture | Define capture latency, skew, overrun, event sequence and LinuxCNC consumption; a latch alone does not change host probing semantics. |
| Host servo | Begin qualification at 1,000 Hz under representative workload | Full read/compute/write deadline, acknowledgement age and fault latency need a target real-time driver and measurements. |
| PWM | Published frequency/resolution combinations | Define synchronized update boundaries and physical off-state; no one frequency figure describes all resolutions. |

At 50 MHz, 2 MHz STEP has a 500 ns period: **25 core ticks total** for high and low. The current 100-tick high plus 100-tick minimum low needs at least 4 µs, so raising the rate constant alone cannot reach the proposed rate. Derive timing/register widths, quantization, DDS behavior, direction reversal, simultaneous-channel switching and the fault response, then simulate and synthesize the changed architecture. Preserve valid long pulse settings for slower drives.

The DM542T V4 example is limited to 200 kHz, with at least 2.5 µs high and low and 5 µs direction setup. A board capable of faster signalling cannot make that drive accept a higher rate. The profile's allowed rate must be the minimum of validated board, gateware, configured timing, drive, cable and machine limits. [Manufacturer timing requirements](https://omc-stepperonline.com/download/DM542T_V4.0.pdf)

Ten million quadrature transitions/s averages 100 ns between valid state changes, only five 50 MHz ticks. Budget receiver delay/skew, synchronizers, filtering, index coincidence, metastability and worst-case edge spacing; averaging alone cannot prove capture. As a sizing example, 4,096 encoder cycles/revolution at 24,000 RPM gives `4096 × 4 × 24000 / 60 = 6,553,600` count transitions/s. This is a bandwidth calculation, not an approved operating point.

The current CNC1 ABI has six command rates and two encoder result sets in fixed 64-byte frames. Expanded status, I/O, event capture and configuration require an explicit versioned protocol and capability negotiation. Do not repurpose reserved fields without revising validation. Specify atomic configuration while disarmed, coherent snapshots, event freshness, sequence/epoch handling, watchdog progress and full servo-cycle bus occupancy. Customer Ethernet/Wi-Fi/USB and the browser remain outside this internal hard-real-time link. [Current implementation contract](../gateware/PROTOCOL.md)

## Resource and BOM work for the next costing pass

Use a complete separately named BOM for the required eight-motor assembly, plug-in expansion and factory-fitted twelve-motor version at quantities 1, 10, 100 and 1,000; keep the six/two BOM historical. Do not multiply the earlier board total by 8/6. Component examples below are **counting references from the original eight/four study**, not selected expanded circuits or price claims.

| Block | Expanded quantity/circuit requirement | Costing consequence |
|---|---|---|
| Differential STEP/DIR | 16 channels; four quad transmitters if retaining AM26C31 | Baseline uses three. Include enables, defaults, damping, bypass and external line protection; physical 2 MHz performance remains unqualified. |
| Differential receivers | 12 ABZ plus 2 frequency = 14 channels; four quad receivers if one qualified family serves both | Baseline has two quad devices for six encoder signals. Two remaining receiver channels are only circuit spares; probes are separately specified. |
| Protected alarm/general inputs | 32 complete channels; 16 dual ISO1212 devices if retaining that architecture | Baseline has 22 channels/11 devices. Include threshold/sense/filter/protection parts. ISO1212 already isolates the logic boundary; do not add a second per-channel isolator or assume independent certified channel barriers. |
| General outputs | 16 protected sourcing channels; four quad output ICs if retaining that architecture | All four banks now serve general DO. The baseline four-bank allowance covered 8 general + 6 sourcing-enable outputs. Eight isolated enable switches and two process interfaces are new separate circuits. |
| Enable/process isolation | Eight drive switches plus two process-specific command interfaces | Select technology and rate each circuit, including default/fault gating, status and support power; no free relay/contact assumption. |
| Fast probe/PWM | Two input and two buffered output paths | Protection, sensor power, conditioning, timing and fault behavior need independent allocations. |
| Analog | Two complete AO paths and four AI paths | DAC/ADC, reference, amplifiers, filtering, protection, isolated control/power where needed, monitoring and calibration/test provisions. |
| Field buses | CAN controller as required, CAN and RS-485 transceivers, isolation and isolated supplies | Add termination/bias options, protection, defaults, connectors and software integration. Choose host/FPGA ownership before allocating pins. |
| FPGA/host/service support | Refit complete design; preserve independent watchdog and permission network | Recalculate clocks, rails, flash/debug, bus bandwidth, GPIO banks, routing and service isolation. ESP retains diagnostic UART/PGOOD/MOTION_DISARMED observation; no motion authority. |
| Power/terminals/manufacture | New rail and load budgets, connectors/mates, PCB area/layers, assembly, programming, test and enclosure | Include actual manufacturing process and good-unit yield; PCBWay quote remains pending complete files. Included display/host economics must be recomputed separately. |

AM26C31 is a four-channel 5 V driver with TTL-compatible logic inputs; AM26LV32E is a four-channel receiver with a 3.3 V supply range. These are different electrical roles, not permission to connect 5 V to FPGA pins. Recheck worst-case receiver output thresholds using actual loading; AM26LV32E's listed maximum low output at 5 mA is **0.5 V**. [TI AM26C31](https://www.ti.com/lit/ds/symlink/am26c31.pdf), [TI AM26LV32E](https://www.ti.com/lit/ds/symlink/am26lv32e.pdf)

Baseline follow-up: its `rx_fpga` link currently uses a 0.4 V low-output value. Correct that assumption against the exact loading/data-sheet condition on the next ledger regeneration and refresh derived validation/hashes. The 0.5 V maximum remains below the proposed FPGA 0.8 V input-low threshold, but reduces the stated margin; no updated baseline electrical evidence is claimed by this planning note.

The ISO1212 input design requires an application-specific resistor/protection network and board isolation layout. Its wider possible applications do not expand this candidate's nominal-24-V terminal rating. [TI ISO1212](https://www.ti.com/lit/ds/symlink/iso1212.pdf)

T20 remains a reference FPGA, not a fixed selection. Efinix lists 195 GPIO for F256, but usable bank/clock/configuration placement and fitted resource/timing results decide whether the complete design fits. Record each pin's voltage domain, direction, startup state, clock capability and reserved function before freezing a package. Review grade, availability, assembly and debug access as well as silicon price. [Efinix T20 data sheet v6.0](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf)

## Power, isolation and fault boundaries

Sixteen loads at the proposed 0.5 A/channel total **8 A**, or **192 W at 24 V**, before sensors and other field loads. That is external load power, not board heat. The baseline 6 A field-entry proposal cannot deliver this simultaneous load. Either design separate protected banks/entries or a suitably higher-current path, or publish a lower concurrent total explicitly. A configuration screen must not silently promise 16 simultaneous full-rated outputs on an undersized supply path.

Recalculate all rails from circuits and operating modes. Four encoder supplies, additional line drivers/receivers, analog references/amplifiers, isolated buses and expansion change both steady-state and startup loads. Eight floating enable switches do not automatically draw the baseline sourcing-enable current from field power. Estimate FPGA switching after synthesis; current reservations and thermal margins are not transferable. The display/core supply and external field load are distinct budgets.

Retain separately coordinated physical DC entry fuses and electronic branch protection, with existing protected output drivers supplying channel protection where appropriate. Select source, fuse interruption/time-current behavior, cables, connectors, eFuse/FET SOA, capacitance, inrush and inductive clamps together. Clearing a trip must not restart outputs. [Existing protection strategy](POWER_PROTECTION.md)

Draw a domain diagram covering LOGIC, FIELD, analog groups, each isolated bus, floating enable/process switches and chassis. State barrier working/transient requirements and prove the external harness does not bridge them unexpectedly. Differential STEP/encoder wiring remains referenced, not inherently isolated. Keep shield terminations distinct from logic return; an HDPE enclosure proposal needs reviewed bonding/metal mounting and EMC arrangements rather than an assumed shielding benefit.

Hardware permission must cover every machine-affecting output, including new PWM/process/analog commands and expansion. Design power-loss, partial-power, unconfigured-FPGA, clock-stall, stale-link, stuck-output and removed-module responses. The independent watchdog must observe useful control progress. Browser, Linux and ESP liveness cannot replace that signal. Machine E-stop/STO, braking and stored-energy handling require a separate machine-level design; general inputs labelled E-stop do not constitute a safety controller.

## Expansion families: explicit optional work

| Optional module | Candidate scope and dependency |
|---|---|
| Encoder expansion | Eight additional ABZ ports; twelve total only if this module and synchronized host integration are built and qualified |
| Required motion expansion (exception to this optional-work table) | Motors 9–12 on the adopted plug-in module, with individual enable/alarm, clock/skew, command deadline and global inhibit guarantees; factory-fitted twelve-motor version required, implementation unfinished |
| Analog servo | Bipolar ±10 V commands plus appropriate feedback and loop-performance qualification |
| Printer thermal/driver | Initial proposal: 2 hotends, 1 rated DC bed stage or external-stage interface, 4 fans, 4 typed temperature inputs and 2 filament inputs; optional local drivers; local timeout and independent thermal cutoff |
| Plasma isolation | Separately rated measurement/source/sensing interfaces; no raw arc connection to general analog/probe ports |
| Galvo/source | Scanner/source-specific protocol, electrical timing and interlock module; two generic PWM outputs are insufficient as its specification |
| Industrial I/O | More rated clamps, valves, toolchanger sensors or operator controls with published update deadlines |
| Specialty measurement | Load-cell, RTD, thermocouple or other dedicated conditioned inputs |

The backplane must define rails/current, returns, connectors, SPI ownership, chip select, synchronization, module ID/presence, fault and hardware inhibit. Publish clock skew/jitter, coherent snapshot rules, update deadlines, removal/fault behavior and recovery. Power-off insertion and replacement are the adopted first-release service mode; no hot-plug capability is assumed. Fast motion/feedback extensions need separate qualification from slow accessory I/O. Sensor types and CAN firmware protocols remain explicit compatibility requirements.

## Actionable gates

| Gate | Deliverable and acceptance evidence |
|---|---|
| E1 — Requirements detail | Approved machine/drive/sensor examples and electrical envelopes, simultaneous-load limits, fault defaults and timing matrix within the confirmed eight-standard/four-plug-in, full general-I/O and fixed-base/card scope; no reopening the adopted capacity or 20 ms limit |
| E2 — Architecture allocation | Expanded domain/clock/power diagrams; every function assigned to host, FPGA, circuit or module; versioned ABI/configuration proposal; 92 signals plus all support mapped without collisions |
| E3 — Circuit feasibility | Exact parts and support components; worst-case levels/current/thermal/propagation; connector and isolation plan; drive-enable loss-of-power behavior resolved for each profile |
| E4 — Digital feasibility | Expanded RTL and independent tests for all eight motors/four encoders plus events/I/O; faults, deadlines and configuration changes; target synthesis, placement, constraints and timing closure |
| E5 — Complete cost comparison | Separate fitted BOMs and actual source/quote evidence for the eight-motor assembly, plug-in expansion, factory-fitted twelve-motor version and replacement cards; connector mates, diagnostics, expanded power and PCBWay assembly/program/test included; screen and other complete packages costed separately against the preliminary US$400 assembly reference; historical six/two comparisons stay labelled and unknowns remain explicit |
| E6 — Design review | First complete the bounded physical LinuxCNC/FPGA link prototype required by BUILD_PLAN stage 5, incorporating its measured faults/timing before final production layout. Then full editable schematic/ERC, PCB/DRC, pin/bank audit, SI/thermal/EMC review and manufacturing/test documents; current partial circuit does not satisfy this gate |
| E7 — Later physical qualification | Measured timing under simultaneous traffic and UI/network/storage load; cable/drive/probe/encoder tests; power/reset/clock/short/open/fault injection; load/thermal/EMC and machine-profile acceptance |

Complete substantial source, circuit, costing and simulation work before ordering. The bounded physical link prototype precedes final production layout; E7 then qualifies the actual custom board/product. This is the same sequence as the [build plan](BUILD_PLAN.md), not permission to skip its earlier link test. The expanded candidate has **unproven performance and unproven complete cost**. CLI/UI/AI configuration must expose the selected board/firmware capabilities and validated ranges, preview changes, and invalidate affected commissioning checks; it cannot turn these proposed targets into achieved ratings.
