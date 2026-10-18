# Controller comparison grounded in implementation evidence

30 September 2026. This is an engineering judgment, not a measured product ranking. The 880-part population audit is frozen separately; subsequent required I/O-control integration has 980 footprints, including 18 bare copper factory test pads. No assembled motherboard exists.

**Architecture direction: 80/100. Current manufacturable-prototype readiness: 30/100.** A 93/100 rating would overstate the evidence. Twelve motor interfaces, replaceable commodity compute, protected I/O and guided offline setup are useful product goals, but unfinished circuits and unmeasured operation cannot earn the same credit as delivered hardware. Firmware, UI and compatibility proposals do not become working board features because they appear in a specification.

| Exact comparison | Motor/axis interfaces | Base digital I/O | Host arrangement and material distinction |
|---|---|---|---|
| Our adopted target | Twelve STEP/DIR motor interfaces with individual enable/alarm; four ABZ | 24 DI; 16 sourcing smart DO, 0.5 A/channel and 2 A/four-channel group | Local LinuxCNC compute plus FPGA and purchased ESP service module. Sockets, complete power, further required circuits, full routing and complete runtime are unfinished. Twelve motor interfaces are not a claim of twelve coordinated axes. |
| Mesa 7I96S | Five STEP/DIR; one encoder | Eleven isolated inputs; six isolated outputs | Ethernet motion/I/O interface for a separate host. Vendor specifies up to 10 MHz step rates. Four DC output channels and two lower-current AC SSR channels have different ratings. [Mesa's exact board specifications](https://www.mesanet.com/fpgacardinfo.html). |
| Centroid AcornSix | Six axes; three encoder ports | Sixteen inputs; sixteen logic-level outputs intended for external relay interfaces | CNC12 host-based system; logic outputs are not equivalent to our proposed protected load switches. [Official AcornSix manual](https://centroidcnc.com/centroid_diy/downloads/acorn_documentation/acornsix_spec_manual.pdf). |
| MASSO G3 | Five axes | Twenty-four isolated inputs; eighteen 5 V TTL outputs | Standalone controller; output rating and needed external load interfaces matter more than counting output pins. [MASSO's official FAQ](https://docs.masso.com.au/MASSO_FAQ/about_masso). |
| Buildbotics controller | Four axes with four built-in stepper power drivers | Ten inputs; five outputs | Integrated standalone unit, published US$499 price; screen and power-supply options are separate. Its built-in motor drivers are a capability our interface-only motherboard does not provide. [Official product listing](https://store.buildbotics.com/buildbotics-cnc-controller/). |

This is a comparison against these particular base products, not every controller sold by each manufacturer. Mesa also documents multi-board ten-axis step/dir and twelve-axis analog-servo combinations, together with encoder, serial and other expansion options. Its ecosystem is not restricted to the five channels of one 7I96S. [Mesa FPGA product documentation](https://www.mesanet.com/fpgacardinfo.html).

Our potential advantages are all twelve motor interfaces on one custom board, a shared guided UI/CLI contract, offline replacement/configuration retention, and measured hardware diagnostics. These require full integration and testing. We have not demonstrated that our controller is faster, more reliable, easier to commission, cheaper as a complete package, or a better closed-loop servo controller than the products above. Optional AI is not a substitute for any of those measurements.

The 80-point architecture assessment credits the adopted one-board structure, sensible separation of Linux/FPGA/service responsibilities, useful I/O scope, service/configuration design and independent inhibit intent. It subtracts for unclosed power/partial-power behavior, missing peripheral and module circuits, FPGA implementation risk, a large provisional PCB and unproven economics. It is a subjective assessment of direction, not a sales claim.

The current 30-point prototype-readiness assessment uses these explicit weights:

| Area | Earned | Available | Evidence limit |
|---|---:|---:|---|
| Complete required schematic | 9 | 25 | Real motor/DI/DO/fast-input/watchdog sources; required carrier, connectors, power and further functions unfinished |
| Pin, footprint and source reconciliation | 8 | 15 | Independent native checks and bounded FPGA allocation; full final BOM/connector/mechanical closure absent |
| Routing, planes and distribution | 5 | 25 | Preserved real copper and five local planes; full integrated routing remains open |
| Default-state and verification evidence | 6 | 15 | Host mutation tests and native review; no full vendor fit, loaded target timing or physical measurements |
| Final mechanics | 1 | 10 | Provisional regions and reservations only |
| Manufacturing and complete cost | 1 | 10 | Partial sourced BOM studies; no release Gerbers/drills/CPL/assembly or accepted turnkey quote |
| **Total** | **30** | **100** | **Not manufacture-ready** |

These scores should rise through closed engineering gates, not through adding features. Preserve the adopted scope, finish the actual circuit, route it, pass native and independent checks, export the real production artifacts, then qualify the prototype against declared limits. Physical reliability and competitive machine performance remain unscored until measured.
