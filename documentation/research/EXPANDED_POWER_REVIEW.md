# Expanded motor power review — proposal only

28 September 2026. **No existing converter, entry, transmitter, sequencer or ledger is changed by this review.** The current product requirement is at least eight motors with expansion to twelve. The six-joint/two-encoder circuit is historical evidence, not the new product limit. The calculations below retain two encoder power branches, the existing 3 A host reservation and no display/AI power allowance. Further encoder or accessory expansion needs a new budget.

The existing 6 A main converter is insufficient for the expanded circuit as currently connected. My recommended next prototype for an explicitly RS-422 motor interface is **a dedicated protected-24 V to 3.3 V transmitter supply with AM26LV31E drivers**. It removes transmitter load from the main converter and provides documented input leakage at zero transmitter supply. If a supported drive profile requires the existing 5 V output implementation, the alternate is an **LM706A0 main converter revision with protected driver inputs**. Neither choice is implemented, priced or physically qualified here. The dedicated 5 V transmitter supply is a third, less comprehensive fix: it removes the current overload but leaves the input-protection problem.

## Current and startup calculations

Reproduce using `python research/expanded-power/analyze.py`. Inputs, source hashes and full results are in [analysis.json](../WORKSPACE_REFERENCES.md#artifact-7e70c080781b90d5); [six numerical boundary checks](../WORKSPACE_REFERENCES.md#artifact-f18e1f1e1bf4e3ea) passed. These are arithmetic tests, not SPICE, loop-stability, thermal or board measurements.

New support loads are 60 mA on IO_3V3 for FPGA support plus 10 mA for machine permission. At 3.34125 V, 4.85 V input and an assumed 85% local efficiency this adds **56.734 mA at CORE_5V**. New maximum local bypass capacitance is 28.658 µF ESP, 10.879 µF FPGA core, 44.920 µF FPGA I/O and 0.9662 µF permission. Their local ramp charge plus the previous regulator output capacitors calculates to **338.876 mA at CORE_5V**; reserve **400 mA**, replacing the historical 170 mA startup allowance. These are supplied design allowances, not measured peak currents.

| Case | Eight motors | Twelve motors | Existing 6 A main |
|---|---:|---:|---|
| Normal operation | 5.6601 A | 6.0601 A | Twelve fails |
| Simultaneous limited encoder faults | 5.8272 A | 6.2272 A | Twelve fails |
| Cold main charge, host and logic held off | 6.0171 A | 6.4171 A | Both fail |
| Logic charge with host held off | 3.2272 A | 3.6272 A | Both screen below 6 A |
| Host starts after main and logic charge | 6.1260 A | 6.5260 A | Both fail |
| Unqualified overlapping logic/host charge | 6.5260 A | 6.9260 A | Both fail |
| Unqualified all operating loads during main charge | 10.3628 A | 10.7628 A | Also exceeds 10 A |

The main capacitor charge remains 1.706456 mF maximum at 5.05 V in 1.9 ms. Host charge uses the existing 1 mF maximum, 470 nF minimum slew capacitor and explicitly assumed 0.5× fastest switch slew; the calculation is updated to the proposed 5.25 V upper interface bound. Downstream regulator operation is excluded only for the qualified cold-start sequence. Arbitrary retained-charge resets remain unqualified. **A larger converter does not remove the need for sequencing.**

The 0.2 A reservation per quad transmitter is not a proven maximum for all terminations, cable capacitance, switching patterns or multiple output faults. In particular, AM26C31's 200 mA package current is an absolute rating, not a current regulator or a guaranteed operating allowance. The new budget is a conditional design screen until transmitter profiles and fault behavior are bounded.

## Entry supply and protection

For conservative input-power screening use 5.25 V times reserved output current, 85% conversion efficiency, 65 mA auxiliary input load and 0.2 Ω total input path. Solve

`Iin = Pout / [eta × (19 V − Iin × 0.2 Ω)] + 0.065 A`.

The twelve-motor host-start case needs **2.2376 A** at the proposed 19 V connector minimum; protected input is **18.5525 V**. The present 7.50 kΩ ILIM screen has only 2.1493 A minimum and fails this case. A **5.10 kΩ, 0.1% initial resistor with 0.5% total allowance** and a **4 A qualified source/wiring target** is a concrete alternative: 3.1607–3.9019 A using the same explicitly assumed ±10% transfer screen. TI does not guarantee that interpolated accuracy at this resistor. Source foldback, wiring temperature, fuse clearing and prospective fault current remain unresolved. The historical 3 A fuse candidate is not carried forward as approved for this revision. [TPS2663 datasheet](https://www.ti.com/lit/ds/symlink/tps2663.pdf)

This proposed entry still does **not** promise a continuous 10 A user output. A full 10 A at the 5.25 V screening voltage needs 3.4378 A, above the proposed minimum current-limit screen. The 10 A converter alternative provides regulator headroom for a defined controller load. It is not an additional 10 A accessory port.

## Main rail voltage: preserve the lower bound

The original CORE_5V interface remains 4.85–5.15 V. A separate revision could use **4.85–5.25 V** after the following changes and tests. Simply changing it to 4.75–5.25 V is unsuitable for the current SBC path.

| Consumer | Primary device limit or current design constraint | Effect on proposed revision |
|---|---|---|
| Raspberry Pi CM4 candidate | Official module input 4.75–5.25 V | A 3 A load through assumed 8 mΩ switch plus 15 mΩ wiring loses 69 mV. Main 4.75 V would yield 4.681 V; at least 4.819 V is required before dynamic margin. Host selection and actual drop remain unqualified. |
| TPS22990 SBC switch | Up to 5.5 V input/bias | 5.25 V fits device operation; recheck slew, PG, supervisor delay and output-node overshoot. |
| TPS3890 SBC supervisor | Supply 1.5–6.5 V | Voltage range allows 5.25 V; its divider and startup behavior still matter. |
| TPS62901 local regulators | Input 3–17 V | The device is not limited to 5.5 V input. Their existing 4.85–5.15 V design contract nevertheless needs explicit revision. |
| AM26C31 driver | Supply 4.5–5.5 V | Fits 5.25 V supply; does not resolve its input restriction during supply collapse. |
| TPS2553 encoder switches | Input 2.5–6.5 V; existing block envelope 4.75–5.25 V | These are switches, not regulators. About 27 mV switch drop at 0.2 A plus cable drop prevents equating main-rail minimum with encoder-terminal minimum. |
| LTC2962 sequencers | Supply 2.25–5.5 V | Supply range fits, but the existing CORE_5V OV threshold is 5.0726–5.1375 V and can reset the system below the proposed upper bound. |

Sources: [CM4 datasheet](https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf), [TPS22990](https://www.ti.com/lit/ds/symlink/tps22990.pdf), [TPS3890](https://www.ti.com/lit/ds/symlink/tps3890.pdf), [TPS62901](https://www.ti.com/lit/ds/symlink/tps62901.pdf), [AM26C31](https://www.ti.com/lit/ds/symlink/am26c31.pdf), [TPS2553](https://www.ti.com/lit/ds/symlink/tps2553.pdf), [LTC2962](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc2962-2963-2964.pdf). CM4 full PDF retrieval was blocked/oversized; its official indexed input specification was checked, not its entire carrier contract.

The sequencer intentionally accepts the regulation-only 4.95–5.05 V range rather than every point of the broader interface envelope. Even the historical 5.1453 V unload screen may cross its static OV threshold; whether the short pulse causes reset has not been demonstrated. Revising the monitor must retain tolerance and response-time margin below consumer limits. A separate regulated encoder rail is needed only if selected encoders require a tighter terminal envelope; adding it without a qualified encoder profile does not yet establish a benefit. Passive ratings, all backfeed paths and connector/host USB loads still need integration review.

## Option A: same-family 10 A main converter

**LM706A0RRXR** shares the documented RRX pin definition with LM70660RRXR. Its supported shunt is **4 mΩ**, versus the existing 6 mΩ. TI's 10 A example uses **KRL2012E-M-R004-F-T5**; this is a reference candidate, not a drop-in footprint assertion. [TI family datasheet, sections 4, 5.3 and 7.2.2](https://www.ti.com/lit/ds/symlink/lm70660.pdf)

With assumed ±2% total shunt variation, the 50–62 mV threshold gives 12.2549–15.8163 A. Adding the **typical-only** 75 ns delay at 48.4 V and assumed 2.632 µH gives **17.1955 A**, not a guaranteed short-current maximum. The old XAL7070-472MEC's 15.2 A typical saturation point cannot qualify that case. A concrete larger candidate is **XAL1010-472MED**, 4.7 µH, 5.7 mΩ maximum 25°C DCR, 25.4 A typical 30% inductance-drop point at 25°C. Hot saturation, fault pulse energy and inductor tolerance still need qualification. [Coilcraft primary part page](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal1010/xal1010-472/)

Keep the same assumed effective inductance limits only as a comparison hypothesis. Changing the shunt also changes loop gain. For the existing three-bulk minimum 695.1 µF, **6.34 kΩ / 33 nF / 560 pF** is a calculable compensation starting point: approximately 6.968 kHz crossover, 761 Hz zero and 41.98 kHz high-frequency pole including the internal 38 pF. Retaining 9.53 kΩ would instead imply about 10.474 kHz crossover. Neither is a stability result; verify the full capacitance, ESR, temperature, load and operating-mode range before selecting passives.

| Removed load, at 48.4 V reference input | Two existing 330 µF polymers | Three polymers | Relevant result |
|---|---:|---:|---|
| 6 A | 5.18000 V | 5.14532 V | Three only barely screens under old 5.15 V |
| Revised 12-motor 6.526 A case | 5.19246 V | 5.15402 V | Both fit proposed 5.25 V arithmetic; old 5.15 V fails |
| Full 10 A | 5.29001 V | 5.22227 V | Only three fit proposed 5.25 V arithmetic |

These combine worst switching-phase inductor energy, independent maximum ESR step, fixed-output tolerance and half the ripple. They exclude controller response delay, layout impedance, temperature-qualified capacitor ESR and energy from external loads. The 48.4 V TVS number is a reference test clamp, not a guaranteed system surge bound. **Do not add more bulk reflexively:** the existing three capacitors are a useful prototype starting point under an explicitly changed upper rail limit. Keeping only two would require restricting and verifying the real maximum load and faults; a regulator labeled 10 A would not make that two-capacitor configuration pass a full 10 A unload.

This option also needs stronger input/source qualification, changed shunt/inductor/compensation, updated monitoring and a separate remedy for the AM26C31 input issue. It is not an IC-only swap.

## Option B: dedicated transmitter converter

**LMR36520FADDAR** is a 65 V, 2 A, 400 kHz FPWM, DDA-8 candidate. The `F` denotes FPWM, not a fixed 5 V output. TI's adjustable reference circuits use 100 kΩ/24.9 kΩ, 10 µH and two 22 µF output capacitors for nominal 5 V; for nominal 3.3 V they use **100 kΩ/43.2 kΩ, 6.8 µH and three 22 µF**. Both include two 4.7 µF plus 220 nF input capacitors, 100 nF bootstrap and 1 µF VCC bypass. Internal soft start is 3–6 ms. Exact MPNs, effective capacitance, inductor saturation, EN/PG wiring and board compensation/layout qualification remain to be designed. [TI LMR36520 Rev C, tables 6.6 and 8-1, figure 8-1](https://www.ti.com/lit/ds/symlink/lmr36520.pdf)

Moving all TX power off CORE_5V, including the old 0.6 A baseline, reduces its twelve-motor fault load to **5.0272 A**, host start to **5.3260 A** and cold main charge to **5.2171 A**. A separate 5 V buck leaves the shared input power essentially unchanged: 2.2376 A for that host-start case using equal assumed efficiency, before the extra converter's startup and quiescent current. Splitting rails cannot create upstream power.

For a 3.3 V transmitter rail, AM26LV31E is a concrete alternative with a corresponding 16-pin SOIC/TSSOP signal map. It specifies operation at 3.0–3.6 V, inputs up to 5.5 V, input leakage ±10 µA at VCC=0, and differential output at least 2 V into 100 Ω. It improves the documented zero-supply input behavior. It does **not** prove every intermediate-power state, cable/EMC condition or unlimited shorts; the datasheet limits short-circuit testing to one output and one second. [AM26LV31E Rev C](https://www.ti.com/lit/ds/symlink/am26lv31e.pdf)

Do not advertise the 3.3 V option as a universal replacement for a 5 V optocoupler drive input. Specify compatible RS-422 receivers, common-mode range, termination and cable limits, and qualify them. Also do not simply attach 1.2 A of drivers to the current 1 A IO regulator: logic plus new support plus TX would reserve **1.67 A**. A 3.3 V TX buck fed from CORE_5V still produces **6.2986 A** main host-start demand under the unchanged TX reservation, so it fails the original 6 A supply. Feed the independent TX converter from protected 24 V if retaining the 6 A main is the objective. The direct 24 V→3.3 V case has lower shared input power, but extra converter startup/thermal demand and driver faults are not yet included.

The current AM26C31 circuit's input absolute limit is VCC+0.5 V. Its 33 Ω series input resistor is not a clamp and cannot establish compliance while CORE_5V collapses but FPGA I/O remains energized. A larger main converter does not fix this. A 5 V implementation needs a specifically qualified powered-off interface or a rigorously proven sequencing/clamping design. [AM26C31 ratings](https://www.ti.com/lit/ds/symlink/am26c31.pdf)

## Cost and next concrete decision

No supplier quotes or component prices were fabricated. The new power hardware is not covered by the old controller cost matrix.

| Option | Material change to cost | Work still needed |
|---|---|---|
| 10 A main, retain 5 V TX | IC premium; larger inductor; shunt; revised protection/monitoring; powered-off TX interface | Quote delta; review exact packages, thermal layout, loop stability and drive profiles |
| Separate 5 V TX buck | Additional IC, inductor, about eight capacitors, feedback/enable/status passives and PCB area; powered-off TX interface still needed | Design full converter and both-rail startup/fault behavior |
| Separate 3.3 V TX buck and LV drivers | Additional converter with one more output capacitor than 5 V reference; six driver substitutions at twelve motors | Design rail/permission interaction and qualify explicit receiver profiles; avoid unproven 5 V compatibility |

The next useful implementation is one selected power/driver combination with a revised current contract and fault tests. The RS-422 option is my recommendation for that prototype because it addresses both current capacity and documented zero-supply input behavior. Retain the present six-axis evidence unchanged and rerun electrical connectivity and startup calculations for the selected eight/twelve-motor implementation. Neither this review nor the completed ESP service circuit makes the product ready for manufacture.
