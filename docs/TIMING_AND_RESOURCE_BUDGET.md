# Timing study and current resource evidence

**Reviewed 18 October 2026.** [Documentation index](README.md) · [Current engineering status](../reports/ENGINEERING_STATUS.md). The equations and runnable examples below are the original illustrative study; their assumed network packets, limits and braking values are not the current CNC3 SPI ABI or machine ratings.

## Current device and runtime resource boundary

The adopted hardware direction is one active soldered-FPGA motherboard with all twelve motor interfaces, four ABZ, 24 general DI and 16 smart DO plus the retained required functions. [The current continuation record](../reports/board-finish-20261017/README.md) binds actual T20F256/I4 vendor mapping of canonical disconnected SIM2 at **15,805 LUT4 + 2,107 ADD = 17,912**, 10,441 FF, 63 RAM5K and one multiplier. This is 1,816 below the conservative 19,728 LUT4+ADD screen. Registered RAM/prefetch bypass, the seven-producer FIFO and command alignment retain the original 256-record capacity, seven simultaneous producers, all completed protocol buffers and channel/function limits.

Fresh eight-/twelve-joint LinuxCNC task/FREE-planner/HAL/C-driver/serial-SPI/selected-RTL/virtual-plant runs pass. Separate real vendor interface checks cover 135 assigned pins and seven source-defined 3.3 V banks. These results establish neither complete physical-wrapper fit nor placement/routing/static timing, actual transport latency, loaded RT schedulability, all-channel 2 MHz operation or physical stopping behavior. The frozen 96-byte command/176-byte feedback contract and actual rate/electrical limits remain unchanged. Failed earlier maps and simulation startup runs retain their dated evidence; their resource totals do not describe the corrected canonical core.

## Historical illustrative study

These are configurable engineering examples, not the user's machine specifications and not a selection of chips. The study makes it possible to reject an architecture on paper, identify the demands that matter, and keep hardware choices open while the software and interfaces develop.

All numeric inputs are explicit assumptions in [`../config/machine-study.json`](../config/machine-study.json). No component capabilities or compliance claims are asserted here, so the analysis does not rely on external product specifications. The equations are dimensional calculations. Actual device limits must later be entered from the exact drive, encoder, transceiver and processor documentation, followed by measurement.

## What is runnable now

The dependency-free analyzer is [`../tools/analyze_requirements.py`](../tools/analyze_requirements.py). It accepts JSON, calculates per-joint and aggregate demands, checks configured assumed limits, and outputs JSON. A deterministic generated report is saved as [`../reports/timing-budget.json`](../reports/timing-budget.json).

From the project root:

```powershell
python tools/analyze_requirements.py config/machine-study.json --output reports/timing-budget.json
python -m unittest discover -s tests -p test_requirements_analysis.py -v
```

The first command returns zero for a valid study even when a scenario exceeds an assumed limit. Add `--fail-on-limit` to return exit status 1 when any configured limit is exceeded. Input/IO errors return status 2. The supplied mill case deliberately exceeds assumed limits, so `--fail-on-limit` should return 1. JSON always goes to standard output; `--output` also saves it. The input file cannot be overwritten by using the same path for output.

The top-level `units` dictionary must match the supported unit system exactly. Numeric fields also include units in their names. The analyzer rejects unsupported units rather than silently converting them. It rejects unknown fields, duplicate JSON keys, empty or duplicated scenario/joint/stream names, ambiguous encoder definitions, nonfinite values, booleans where numbers are expected, invalid signs, and packets above the configured MTU. Fractional resolutions or byte counts are not accepted. Zero speed and zero reaction time are valid; zero screw lead, pulse duration, update period, link capacity or braking deceleration are invalid.

## The sample results

| Illustrative case | Physical joints | Largest single-joint demand | Aggregate step demand at simultaneous maxima | Two transitions per step, aggregate | Peak directional network utilization |
|---|---:|---:|---:|---:|---:|
| Router | X, Y-left, Y-right, Z | 120,000 pulses/s | 440,000 pulses/s | 880,000 transitions/s | 1.552% |
| Mill | X, Y, Z, rotary A | 400,000 pulses/s | 1,020,000 pulses/s | 2,040,000 transitions/s | 10.304% |
| Lathe | X, Z | 240,000 pulses/s | 400,000 pulses/s | 800,000 transitions/s | 4.128% |

The network column assumes a 100 Mbit/s full-duplex link with the overhead listed below. It is a capacity estimate, not a latency estimate. All maximum joint speeds are assumed simultaneous for this upper-demand comparison; the planner's coordinated path limits may result in lower simultaneous demands.

The router uses four independent pulse outputs even though it has three named linear axes: the two gantry motors are separate joints. The mill uses four outputs including a rotary joint. A logical step/direction design would therefore start with eight joint command signals for either example, before enable, faults, probes, encoders, spindle controls or any machine I/O. These are signal counts, not connector pins, and say nothing about whether a selected processor can route and time them.

The mill's X and Y each require 400 kHz, while the illustrative drive interface requires at least 2.5 microseconds high plus 2.5 microseconds low. That interface permits at most 200 kHz in the idealized width model. A separate assumed processor output limit of 500 kHz does not resolve the drive pulse-width conflict. The aggregate 1.02 million pulses/s also exceeds the separately assumed 1 million pulses/s budget. These are useful failed design cases, not claims that a real mill must use those settings.

Potential changes to study include speed, screw lead, gearing, drive electronic gearing, or the assumed interface. Reducing command pulses per revolution changes the command increment; it must not be silently presented as having unchanged positioning performance. A faster CPU does not change an external drive's minimum accepted pulse widths.

## Pulse demand equations

For a linear joint, define:

- `v`: maximum speed in mm/min.
- `L`: screw lead or belt travel in mm per output revolution.
- `G`: motor revolutions per output revolution; a 2:1 reduction is `G = 2`.
- `P`: accepted command pulses per motor revolution, including configured electronic gearing inside the drive.

Then:

```text
output revolutions/s = v / (60 × L)
motor revolutions/s  = v × G / (60 × L)
command pulses/mm    = P × G / L
step pulses/s        = v × P × G / (60 × L)
step period, us      = 1,000,000 / step pulses/s
```

For a rotary joint with output speed `R` in revolutions/min:

```text
step pulses/s = R × G × P / 60
```

There is no finite pulse period at zero speed; the JSON reports `null`. With assumed minimum pulse-high time `H` and minimum pulse-low time `T`, both in microseconds:

```text
ideal width-limited maximum pulses/s = 1,000,000 / (H + T)
```

The equality boundary passes the arithmetic check, but has no width margin. Pin rise/fall times, digital filter behavior, clock error, timer quantization, direction setup/hold, output skew and isolation delay are not included. They need their own budget before the interface is accepted.

Each pulse has a rising and falling transition in this model. An aggregate pulse rate cannot be compared directly with a quoted transition/event rate without checking the definition. Hardware channels may process edges concurrently; a software interrupt per edge may process them serially. This analyzer does not assume either implementation. It must not be used to infer CPU utilization from pulse rate alone.

## Encoder counts, lines and spindle pulses

The input definition is mandatory and accepts exactly one of these meanings:

| `signal_definition` | Meaning of `resolution_per_rev` | Rate calculation |
|---|---|---|
| `quadrature_lines_per_rev` | Full cycles/lines per channel per shaft revolution; four-count decoding assumed | lines × 4 × shaft revolutions/s |
| `decoded_counts_per_rev` | Already-decoded counts per shaft revolution | counts × shaft revolutions/s; no second factor of four |
| `single_channel_rising_pulses_per_rev` | Counted rising pulses per shaft revolution | pulses × shaft revolutions/s; no factor of four |

An encoder on a motor shaft and one on an output shaft see different rates when gearing is present. The joint's `encoder_shaft` explicitly selects `motor` or `output`. Index rising-pulse rate is calculated separately and is not added to quadrature counts.

At the illustrative lathe's 6,000 rev/min, a 2,048-line quadrature encoder produces 819,200 decoded counts/s, with 204,800 full cycles/s per quadrature channel. A one-pulse-per-revolution signal produces 100 rising pulses/s. The example reports both as a comparison, not a requirement to install both. Equal spindle speed does not make those feedback signals interchangeable for synchronization or position estimation.

These counts are input acquisition demands. They do not prove that a control loop, velocity estimator or threading implementation has sufficient precision. A future controller-level loop study must include timestamp resolution, filtering, sample period, noise, mechanical compliance, plant dynamics, output latency and phase delay.

## Communication budget

The example is a wired byte-slot model. The following are configurable assumptions, not a claim that every transport or packet uses this format:

| Element | Assumed bytes or equivalent byte times |
|---|---:|
| Ethernet header | 14 |
| Frame check sequence | 4 |
| Preamble and start delimiter | 8 |
| Interpacket gap | 12 |
| IP header | 20 |
| Transport header | 8 |
| Minimum Ethernet payload, including IP/transport content | 46 |
| Maximum IP packet bytes before unsupported fragmentation | 1,500 |

The interpacket gap is accounted for as occupied byte times rather than transmitted application bytes. With application payload `B` bytes per packet:

```text
modeled wire-slot bytes/packet = max(46, 20 + 8 + B) + 14 + 4 + 8 + 12
packets/s                      = packets/update × 1,000 / update period in ms
modeled bits/s                 = wire-slot bytes/packet × 8 × packets/s
serialization plus gap, us     = wire-slot bytes/packet × 8 / link bits/s × 1,000,000
```

Full duplex compares each direction independently with link capacity; its reported utilization is the larger directional load divided by that capacity. The report also shows the sum of both directions without incorrectly treating that sum as a full-duplex bottleneck. `capacity_mode: "shared"` instead compares the sum with the configured shared capacity. The shared mode is only a capacity accounting option; it is not a Wi-Fi or Bluetooth protocol simulator.

The router's assumed 128-byte packets at 1,000 updates/s use 194 byte slots per packet, 1.552 Mbit/s in each direction, and 15.52 microseconds per packet including the modeled gap at 100 Mbit/s. The mill's 256-byte packets at 4,000 updates/s use 10.304 Mbit/s in each direction. Neither calculation establishes that a host process will deliver one packet before each update deadline.

These packet contents are examples, not a chosen control protocol. They do not specify whether the packet carries an absolute position, velocity target, timestamped trajectory segment, feedback record or buffered job chunk. That protocol decision determines how delay, sequence gaps and stale data must be handled. A locally executing controller can use the external link for jobs and supervision; a cyclic external servo loop has different deadline obligations. This budget deliberately does not decide between those architectures.

Packet loss, reordering, duplicate packets, queueing, OS scheduling, switches, contention, retransmission, other traffic, clock drift, USB transport and wireless overhead are excluded. Payload serialization is only one part of the eventual latency budget. Higher bandwidth cannot be used as evidence of a bounded worst-case deadline.

## Idealized reaction and braking examples

Let `v` be initial speed in mm/s, `t` the assumed reaction interval in seconds, and `a` the assumed positive constant deceleration in mm/s²:

```text
reaction distance = v × t
braking distance  = v² / (2 × a)
total distance    = v × t + v² / (2 × a)
braking time      = v / a
```

| Illustrative condition | Reaction distance | Braking distance | Sum |
|---|---:|---:|---:|
| Router: 300 mm/s, 10 ms reaction, 1,500 mm/s² deceleration | 3 mm | 30 mm | 33 mm |
| Same router assumptions, 100 ms reaction | 30 mm | 30 mm | 60 mm |
| Mill: 200 mm/s, 10 ms reaction, 1,000 mm/s² deceleration | 2 mm | 20 mm | 22 mm |
| Lathe Z: 150 mm/s, 10 ms reaction, 1,000 mm/s² deceleration | 1.5 mm | 11.25 mm | 12.75 mm |

These values illustrate why reaction delay deserves a budget; they are not protective distances or a verified stopping envelope. The model excludes jerk limits, torque/current limits, drive response, load and gravity, loss of power, compliance, backlash, spindle coast, uncertain braking capability and failure modes. The reaction input must eventually be decomposed into detection, scheduling, communication, command acceptance and actuation contributions. A shutdown that removes power can behave differently from a controlled deceleration. The JSON therefore explicitly marks stopping results `safety_validated: false`.

## Original resource checklist and remaining qualification

The original calculations define the following checklist. Current architecture and protocol choices supersede the open choices in this study; apply the remaining measurement/budget obligations to the exact motherboard, compute, CNC3 and machine profiles rather than reopening settled requirements:

1. Replace illustrative motions with machine classes and ranges the design is intended to support. Keep simultaneous joint count, independent gantry joints, rotary joints and spindle feedback separate.
2. Decide whether the controller merely sends step/direction commands to drives with internal feedback or closes any position/velocity loops itself. Mark every feedback source and the actual loop boundary.
3. Define pulse-generation channels, timer tick and timestamp resolution, direction timing, minimum widths, output synchronization and the acceptable quantization error. Test the scheduler against generated trajectories and reversals before assigning a processor.
4. Allocate encoder capture resources by physical input type and required count rate. For a quadrature electrical input, include signal conditioning and the index path; an already-decoded count source may arrive through a different interface.
5. Specify network packet fields, update periods, buffering, sequence/session identity, permitted age, clock assumptions and behavior on loss/reordering. Stress these in simulation; a bandwidth margin does not answer them.
6. Make a worst-case execution budget for each real-time job: planner, interpolator, pulse preparation, feedback acquisition, control computation and supervision. Their measured execution times, interrupt interference and scheduling policy determine feasibility. CPU clock frequency alone does not.
7. Define what continues locally during communication loss and what causes controlled stop, output inhibition or operator recovery. A helper ESP's observations and requests must have explicit ownership and precedence in those states.
8. Track unallocated resources: boot/recovery paths, program/storage space, DMA channels, timer channels, pin routing, peripheral buses, power rails, isolation channels, thermal design and external I/O. Numerical budgets here do not yet allocate them to a particular device.

Simulation can expose protocol mistakes, infeasible assumptions and inconsistent state transitions. It cannot establish actual electrical pulse timing, worst-case kernel/interrupt latency, drive compatibility, noise immunity or physical stopping behavior. Those remain explicit later bench measurements rather than reasons to buy before the architecture and software contracts are ready.

## Verification coverage

The unit tests use independently calculated cases for gearing, linear/rotary demand, exact pulse-width boundaries, zero speed, motor/output encoder locations, line-versus-count definitions, index pulses, Ethernet padding, MTU boundaries, full-duplex versus shared capacity, and idealized braking. Integration tests check the deliberate mill-limit failures, strict units/fields, malformed input, CLI JSON output and exit codes. Passing tests establish consistency with these equations and validation rules; they do not validate any particular machine or processor.
