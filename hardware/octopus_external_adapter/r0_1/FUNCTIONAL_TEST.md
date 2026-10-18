# Adapter verification and factory-test draft

**Procedure, not executed evidence.** Use an isolated bench fixture first. No machine configuration changes, connected machine axes or automatic motion are authorized by this procedure. Record exact PCB/source revision, instruments, loads, supply limits, waveforms and results. Agree numeric acceptance and factory scope before build release.

The proposed circuit is `SN74LVC3G06DCUR`, three 1 kΩ input series resistors, 47 kΩ STEP/DIR pulldowns, 47 kΩ EN pullup and 100 nF plus 4.7 µF supply bypass. Outputs are current sinks; the driver's input circuitry completes each path from the +5 V common. A HIGH gate input sinks its output and a LOW releases it. Do not treat a floating output measured without a load as a driven HIGH. [TI datasheet](https://www.ti.com/lit/gpn/SN74LVC3G06)

| Stage | Verification and acceptance purpose |
| --- | --- |
| Source | Reconcile host socket map, all connector cavity numbers, U1 package pin map, passive values, unused pins and fitted BOM. Record native schematic ERC separately from independent netlist checks. |
| Board | Run native DRC including unconnected items; compare actual PCB nets with schematic; inspect routing/returns, pad geometry, drill sizes, copper-to-edge and pin-1 marks. Record exact file hashes. |
| Mechanics | Fit a non-powered first article to the identified host. Verify left J1 has eight pins and right J2 has seven pins starting one position lower; the upper-right VM position has no contact or plated pad. Check header lengths and seating, under-board clearance, adjacent occupied sockets, top cable insertion/removal and strain relief. |
| Harness | Test every pin-map path, all three positive branches, no unintended connections, contact retention, splice insulation and labels. |
| Unpowered PCBA | Inspect solder joints/orientation. Check no 5 V-to-GND short and confirm the VM contact and plated pad are absent. Verify J2 pins 1/7 are GND, pin 6 is +5 V and pins 2–5 are unconnected motor positions; other unused contacts remain unused as specified. |
| Static sink test | Power from a current-limited bench 5 V source; drive inputs with valid 5 V logic. Apply controlled sourcing loads of 7, 10 and 16 mA to each output individually and all three together. Measure VOL, rail drop and input levels. Establish margin against TI and driver limits. |
| Loaded input test | Use the identified CL57T V4.1 in 5 V input mode or a documented optocoupler-equivalent load. Verify each input current remains 7–16 mA and asserted/deasserted differential levels satisfy its manual. Measure at the driver terminals through the final cable. |
| Pulses | Measure at the remote driver input, including rise/fall, ringing, pulse count, width and direction setup. Start at low rate; qualify the configured upper rate with margin and simultaneous switching. |
| Defaults and sequences | Test input high impedance, host reset, input disconnect, adapter power before/after drive power, power loss and recovery. Record actual STEP and ENA behaviour; resolve enable polarity on the actual drive. |
| Four adapters | Repeat signal checks with four loaded adapters on the actual host. Three 16 mA loads per adapter represent 48 mA; four represent 192 mA before circuit/host consumption. Verify rail regulation, ground movement, thermal behaviour and timing. |

The provisional named host supplies 5 V socket logic. At U1 VCC = 5 V, a generic 3.3 V input does not meet the specified HIGH threshold. Verify the actual host before energizing; do not silently widen compatibility.

The CL57T V4.1 manual specifies at least **1 µs pulse HIGH**, **1 µs pulse LOW**, **2 µs DIR setup**, and **200 ms ENA lead before DIR**. Configure margin beyond these minima and measure after the cable. Its downloadable manual and current product page disagree about the maximum pulse rate; this adapter has no qualified maximum-rate claim. [Driver manual](https://www.omc-stepperonline.com/download/CL57T-V41_user_manual.pdf), [product page](https://www.omc-stepperonline.com/closed-loop-stepper-driver-v4-1-0-8-0a-24-48vdc-for-nema-17-23-24-stepper-motor-cl57t-v41)

EN HIGH provisionally sinks the enable optocoupler to request drive disable; this is an **unverified drive-polarity assumption**, not an acceptance result. EN pullup only defines an input while the adapter rail exists. Loss of adapter power releases the sink and removes the harness common supply. Neither state establishes an inhibited drive. Deliberate restart and machine safety require a separately qualified system.

For a first prototype, retain failed measurements and revise the candidate before repeated assembly. Bench qualification of the first article precedes an agreed reduced per-unit factory test. Do not represent source review, ERC, DRC, fixture measurements or powered-driver behaviour as interchangeable evidence. Target compilation, HDL simulation and FPGA synthesis are not applicable to this standalone logic adapter.
