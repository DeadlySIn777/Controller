# Expanded motor-capacity power review

29 September 2026. This is a read-only arithmetic screening of the existing power-tree candidates after the product requirement changed to eight motors minimum and twelve-channel expansion. It does not modify any implemented regulator, transmitter, connector or PCB design. The machine remains a pre-manufacture engineering prototype.

The twelve-channel transmitter reserves 1.2 A at its 5 V driver rail. The FPGA support additions reserve 60 mA on IO_3V3 and the machine-permission block reserves 10 mA. The ESP service local-capacitor charge and the FPGA/permission capacitance raise the rounded logic charge allowance to 0.4 A from the earlier 0.17 A screening value. These are design reservations and arithmetic assumptions, not measured loads or guaranteed fault currents.

| Candidate scope | Existing CORE_5V arithmetic result | Interpretation |
|---|---:|---|
| Six-channel historical source, normal | 5.46 A | Fits the old 6 A screen with little margin |
| Eight motors, normal | 5.66 A | Fits the old 6 A screen only for steady state |
| Eight motors, cold main-charge case | 6.02 A | Exceeds the old 6 A screen |
| Twelve motors, normal | 6.06 A | Exceeds the old 6 A screen |
| Twelve motors, host-charge case | 6.53 A | Exceeds the old 6 A screen |
| Twelve motors, unqualified simultaneous charge | 10.76 A | Exceeds both the old 6 A and the screened 10 A candidate |

The existing LM70660 six-amp path therefore cannot be carried forward as the twelve-channel product power decision. A dedicated 24 V-to-5 V transmitter rail can remove the transmitter reservation from CORE_5V, but its converter rating, input-current impact, startup behavior and protection still require a complete design and test. A dedicated 3.3 V transmitter rail also needs a new regulator and updated IO_3V3 budget; the existing one-amp branch is insufficient for the screened 1.2 A twelve-channel reservation.

The current main-rail unload arithmetic is conditional. It uses assumed effective capacitance, ESR, switching frequency, inductor corners and 85% efficiency. Several twelve-channel and high-load cases exceed the 5.25 V arithmetic target, and none of these screens proves loop stability, thermal behavior, current-limit behavior, short-circuit peak, load-step regulation or brownout recovery. The existing core overvoltage monitor also does not accept the full 5.25 V CM4 input range without revisiting its threshold contract. The CM4 branch needs at least about 4.819 V at the main rail under the stated 3 A path-drop assumption to guarantee 4.75 V at the module; that is a screening calculation, not a supply qualification.

The next power decision is to compare a redesigned higher-current main rail against a separately protected transmitter rail, with the eight-motor standard and twelve-motor expansion costed independently. Do not remove I/O or protection to preserve a six-amp target. Re-run the calculation whenever the FPGA, permission, compute module, display tier or transmitter driver is changed; the present `research/expanded-power/analysis.json` records its source hashes and remains a non-manufacturing study.

Not established here: a complete 8/12-channel motion runtime, individual enable/alarm output stages, a qualified converter, PCB thermal/current density, EMI, physical measurements, or a PCBWay turnkey quote. Ordinary compute, display, drives, relays, adapters and other peripherals remain replaceable third-party compatibility items; their power must be included in the selected kit BOM rather than silently assumed.
