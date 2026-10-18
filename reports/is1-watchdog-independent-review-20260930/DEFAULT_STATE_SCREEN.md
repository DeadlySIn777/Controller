# Independent watchdog default-state screen

30 September 2026. Read-only review; no changes to frozen IS-1, watchdog circuitry, GPIO assignments or electrical budgets. This is arithmetic/source inspection, not a target measurement or a guaranteed complete interface bound.

The T20 primary datasheet, `research/fpga-core/trion20-ds-v6.0.txt` Table 129 (page 86, text lines 7139–7170), states that ordinary GPIO are inputs with weak pull-ups during reset and configuration. Table 75 (page 58, text lines 4631–4651) specifies a 27–65 kΩ internal pull-up for 3.3 V LVTTL/LVCMOS. The new candidate's R3/R4/R5/R7 are 100 kΩ pulls on request/progress inputs (`tools/hardware_build_is1_watchdogs.py`, rows around lines 120–125). Therefore a pull-down symbol alone is not evidence that these attached T20 signals default LOW.

The TPS3851 primary revision SBVS300B, page 5, requires **SET1 LOW ≤ 0.25 V**, HIGH ≥ 0.8 V (`research/is1-watchdogs/tps3851-revb.txt`, lines 297–302). WDI has different thresholds: LOW ≤ 0.3 × VDD and HIGH ≥ 0.8 × VDD. Conflating those thresholds would give the request/default analysis a false margin.

The arithmetic uses IO_3V3 = 3.465 V, internal pull-up = 27 kΩ, and +1% external pull-down for the largest default voltage:

`Vdefault = (VDD / Rpullup + Isource) / (1 / Rpullup + 1 / Rpulldown_max)`

| External pull-down candidate | Default with no added leakage | With assumed +10 µA source leakage | With assumed +12 µA source leakage | Max run-HIGH resistor current | Max resistor dissipation |
|---|---:|---:|---:|---:|---:|
| 100 kΩ, 1% | 2.73410 V | 2.94715 V | 2.98976 V | 0.0350 mA | 0.1213 mW |
| 1.8 kΩ, 1% | 0.21859 V | 0.23562 V | 0.23903 V | 1.9444 mA | 6.7375 mW |
| 1.0 kΩ, 1% | 0.12494 V | 0.13468 V | 0.13663 V | 3.5000 mA | 12.1275 mW |

The +10 µA screen comes from the T20's input/tri-state leakage specification, Table 73, page 57, text lines 4561–4591. The extra +2 µA case is an explicit engineering allowance illustrated against the retained SN74LVC1G34 input-current specification, page 6 (VI = 5.5 V or GND); it is **not** a manufacturer-specified SET1 leakage bound. TPS3851 SET1 input leakage, board contamination/temperature, noise, partial power and rail mismatch remain unbounded here. Thus the 1.8 kΩ option's roughly 14 mV remaining LOW margin in the +10 µA screen is especially small. No option is adopted by this report.

Current/dissipation screens use the opposite resistor tolerance: `Imax = 3.465 / (Rnominal × 0.99)` and `Pmax = 3.465² / (Rnominal × 0.99)`. Four strong pull-downs draw up to **7.78 mA with 1.8 kΩ** or **14.00 mA with 1 kΩ** when all four signals are HIGH, before existing parallel pulls and receiver loads. These are extra GPIO and rail loads that must appear in the interface/power budget.

Even the existing 10 kΩ pull in parallel with a new 100 kΩ pull does not close the request default: at both +1%, the combined resistance is 9.1818 kΩ, giving **0.87931 V without added leakage** or **0.94783 V with assumed +10 µA**. Both exceed the SET1 HIGH threshold. A parallel pull may have to be replaced or accounted for explicitly rather than counted twice as an independent protection.

For actively driven signals, T20 Table 72 (page 57, text lines 4522–4546) specifies 3.3 V **LVCMOS** VOL(max) = 0.2 V and VOH(min) = VCCIO − 0.2 V. That gives only 50 mV of SET1 LOW margin and VOH(min) = 2.94 V at 3.14 V IO_3V3, subject to the actual loaded interface and chosen configuration. The **LVTTL** row allows VOL(max) = 0.4 V, which cannot guarantee SET1 LOW. Table 74's drive-strength-1 IOH = 14.4 mA/IOL = 8 mA is characterized at nominal voltage and 25 °C; it does not independently prove a 3.5 mA added load over the product's full rail/temperature envelope. The 120 mA per-bank limit elsewhere is for clamp-diode input injection and must not be repurposed as a normal output-source budget.

A qualified CDONE/rail/arm-latch final permission gate can keep field outputs inhibited while these raw inputs are HIGH. It does **not** make the raw request LOW, disable SET1 while unconfigured, guarantee progress idle LOW or establish that startup trip records are genuine runtime faults. A future revision must explicitly choose and verify either the complete loaded default-conditioning interface, or a separate hardware SET1 qualification combined with the raw request. It must also define how startup self-test and trip recording distinguish unconfigured states. A software setting that only applies after FPGA configuration cannot solve the pre-configuration weak pull-up state.

The new candidate remains standalone, unintegrated and startup-unqualified. This finding is an interface/integration blocker, not a claim of observed machine motion or a reason to relax the 20 ms requirement. Root retains the existing frozen specification and records the forthcoming revision instead of silently changing it.
