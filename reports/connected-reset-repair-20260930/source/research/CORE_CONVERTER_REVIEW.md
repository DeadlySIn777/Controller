# Core 24 V to 5 V converter: bounded feasibility review

28 September 2026. **Select LM70660RRXR for the next schematic, not for production release.** It is a concrete 6 A candidate with integrated switching MOSFETs. The existing 3 A converter suggestions cannot satisfy this controller's load. The selected 65 V input operating range also leaves useful voltage margin above the entry TVS's 48.4 V reference clamp; that reference is not a guaranteed system surge ceiling. The 10 A LM706A0 shares this datasheet but is a different part. [TI LM70660/LM706A0 datasheet, SNVSCD4](https://www.ti.com/lit/ds/symlink/lm70660.pdf)

This review covers the six-joint/two-encoder core. It does not budget the display, motor power, field branch, optional AI or eight/four expansion. It supplies an exact [pin/net/passive contract](../hardware/core_converter/requirements.json), [independent calculator](../tools/core_converter_analysis.py), [tests](../tests/test_core_converter_analysis.py) and [computed results](core-converter/analysis.json). No physical converter or PCB has been tested.

## Implementable circuit

The complete pin map is in requirements.json, transcribed from TI Table 4-1. All six VIN pins join `CORE_24V_PROTECTED`; SW1-3 feed L1, then a Kelvin-sensed shunt, then `CORE_5V`. ISNS+ senses the inductor side and VOUT senses the load side of the shunt. SW4 is the local bootstrap return and is already connected to SW1-3 inside the package. AGND, power ground and controller pad30 belong to LOGIC_GND; their copper routing has different noise and thermal duties.

| Item | Candidate and connection |
| --- | --- |
| Converter | LM70660RRXR, RRX package; VIN operating 4.5-65 V, absolute 70 V |
| Inductor | Coilcraft XAL7070-472MEC, 4.7 µH, ±20%, between SW and ISNS |
| Shunt | Susumu KRL3216D-C-R006-F-T1, 6 mΩ, 1%, 1.5 W, **0612 long-side terminals** |
| Input capacitance | 4 × TDK CGA6M3X7S2A475K200AE, 4.7 µF/100 V, plus two local 10 nF/100 V capacitors |
| Output capacitance | 3 × TDK CGA6P1X7S1A476M250AC, 47 µF/10 V, plus CBULK1-CBULK3: 3 × Panasonic 16SVPG330M, 330 µF/16 V, positive pin1 to CORE_5V |
| VCC / VDDA bypass | 4.7 µF/16 V and 100 nF/16 V respectively; effective values require selection review |
| Bootstrap | 47 nF/25 V between CBOOT and SW4; fixed 5 V mode does not need the 8 V-mode series resistor |
| Fixed output selection | 24.9 kΩ from FB to VDDA: selects 5 V output and 5 V VCC |
| Frequency / configuration | 49.9 kΩ RT to ground; 29.4 kΩ CONFIG to ground; standalone, DRSS initially off |
| Operating mode | PFM/SYNCIN to VDDA: diode emulation at light load |
| Compensation | EXTCOMP → 9.53 kΩ/1% → 22 nF/5% C0G → AGND; separate 330 pF/5% C0G EXTCOMP to AGND |
| Bias | BIAS to CORE_5V, using VIN-powered internal bias during startup |
| Enable | 100 kΩ protected input to C_PGOOD; 10 kΩ C_PGOOD to ground; C_PGOOD to buck EN |
| Status | Buck PG open drain, 100 kΩ to IO_3V3; status only, not a safety permission |

The selected inductor's 15.2 A saturation specification means a **typical 30% inductance reduction at 25°C**. Its thermal-current figures are reference values, not hot-board ratings. [Coilcraft XAL7070 datasheet](https://www.coilcraft.com/getmedia/1ba55433-bcc8-4838-9b21-382f497e12e0/xal7070.pdf) The exact shunt has ±50 ppm/K TCR; 2% total resistance allowance is an engineering screening bound that still needs lifecycle/temperature qualification. A normal 1206 footprint is wrong for its long-side terminals. [Susumu exact part](https://www.susumu.co.jp/en/product_detail/?pdid=560)

The two TDK ordering codes are confirmed in the manufacturer's catalog. Their bias curves were not successfully downloaded: HTTP 403 responses are recorded as a limitation. Nominal capacitance cannot stand in for effective capacitance. [TDK input capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA6M3X7S2A475K200AE), [TDK output capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA6P1X7S1A476M250AC)

Small passive MPNs, a final land pattern, supply lifetime and quantity pricing remain open. This is one integrated converter and one inductor, not an extra compute module or a complete purchased power board. It is cost-conscious in architecture but has **no validated manufactured-cost claim**. PCBWay must eventually quote these exact qualified parts and permitted substitutions.

## Startup without a computer dependency

The entry TPS26630 pulls C_PGOOD low while its output capacitor charges. It releases only after its FET is enhanced and its PGTH voltage is valid. The protected-24 V divider then enables LM70660. Neither the computer nor 3.3 V needs to exist first. TI explicitly supports using entry PGOOD to enable a downstream converter. [TPS2663 Rev. G, Sections 8.3.2 and 9.2.2.5.1](https://www.ti.com/lit/ds/symlink/tps2663.pdf)

The core entry 10 kΩ PGOOD pull-up to IO_3V3 has been removed in the current circuit. Leaving it fitted would connect the divider to an unpowered 3.3 V rail. This boundary is an analog enable/control node; future digital diagnostics need appropriate buffering. No second active-high driver is allowed on that node.

At 19/30/48.4 V the released divider is nominally 1.727/2.727/4.400 V. Even with the entry's 130 Ω maximum specified pull-down, the 48.4 V reference case is approximately 62 mV while asserted. The buck's precision rising threshold is 0.95-1.05 V. These relationships are comfortably separated under the stated normal electrical conditions. The converter starts well after the entry output ramps, avoiding simultaneous bulk-input charge and full buck load.

This does not prove all abnormal states. TPS26630's normal PGOOD electrical guarantees assume IN_SYS above 4.5 V. Below that, with negative raw input, or with output energy feeding backward, PGOOD function is not established here. The divider limits a retained positive protected voltage, but it cannot guarantee shutdown without an operating sink. The LM70660 BIAS recommendation also requires BIAS not to exceed VIN; an externally powered 5 V rail is therefore an unresolved case. Protected-input negative overshoot must remain above the buck's −0.3 V pin limit, and the entry's negative clamp remains unqualified. Machine output inhibition must be independent; supply restoration and buck hiccup recovery cannot authorize motion.

## Load, input current and startup limits

The earlier ledger's 5.35 A core budget now includes encoder switch overhead/fault behavior, the logic-power block's revised 0.29/0.38/0.62 A reservations (+0.04 A), a 3 mA SBC-switch/bulk-leakage allowance and the separate power-sequencing block's 10 mA reservation. The resulting **normal load is 5.403388 A**, and simultaneous limited encoder faults reserve **5.570490 A**. Only **0.429510 A** remains before the converter's 6 A rating. Unknown SBC boot/peripheral peaks cannot be declared covered by that margin.

Use the proposed **19-30 V connector envelope**, 0.20 Ω total input-path resistance, 85% converter efficiency as a screening assumption, 60 mA analog input reservation and 5 mA entry/auxiliary allowance. Solve the input current self-consistently:

```text
Iin = Vout_max × Iout / [efficiency × (Vconnector − Rpath × Iin)] + Iaux
```

At 19 V, approximately 1.787 A normal, 1.841 A encoder-fault and **1.981 A at 6 A output** are required. The calculator carries exact results. The earlier 8.20 kΩ entry limit's 1.966 A conservative screening minimum was too marginal for a full 6 A claim. The revised circuit uses **7.50 kΩ**: nominal 2.4 A, screened 2.149-2.653 A, within the proposed 3 A source/wiring target. The ±10% transfer assumption at this exact ILIM resistor is not a TI guaranteed bound; preserve that open qualification gate. A foldback supply also needs its own startup review.

The original 18 V whole-controller minimum remains unresolved because the separate analog converter requires 18 V after path drop. The buck itself is not the reason for the 19 V draft. The old 2 A source rating has not become a qualified 3 A source merely by changing the limiter.

The original 350 µF charge-capacitance budget was inadequate for direct SBC integration. That failed design and its hashed inputs are preserved in [before-sbc-sequencing](core-converter/before-sbc-sequencing/). The revised hardware uses an independent [SBC supervisor and controlled-slew switch](../reports/SBC_POWER.md), keeping the 3 A host reservation physically disconnected while the main rail charges. Its enable comes from the unswitched rail's supervisor; it does not depend on host software.

Three polymer capacitors provide 633.6 µF assumed minimum and 1,425.6 µF maximum after separate ±20% initial and ±20% lifetime capacitance allowances. Three ceramics add 61.5 µF assumed effective minimum and 206.424 µF maximum after +20% initial/+22% X7S temperature allowances. Existing logic/encoder/TX/power-sequence input bypass contributes 70.932 µF maximum and new SBC input bypass another 3.5 µF. Thus main-rail charge capacitance is **1.706456 mF maximum**, independently of the **1 mF maximum switched host capacitance**. These are engineering bounds requiring exact-part qualification, not measured capacitance.

At the buck's fastest 1.9 ms soft-start, main capacitor charge reserves **4.535580 A**. For qualified cold start, the separate LTC2962 sequencer holds all three logic regulators disabled until CORE_5V is valid plus at least 160 ms. Remove their 1.29 A operating load during main charging, retain all input capacitance and add an assumed 1 mA disabled-current allowance. TPS62901 specifies 3.5 µA maximum shutdown at EN=0; that does not directly guarantee its current at the sequencer's nonzero asserted voltage. The supervisor's low-state validity begins below the TPS62901 input UVLO, establishing a noncircular normal-start argument; arbitrary partial power remains unqualified.

All other loads, including simultaneous encoder faults, give **5.817070 A total during main charge**, approximately 1.922 A from 19 V. Logic output charging after that, with host off, screens at **2.740490 A**, including a 170 mA allowance derived from three maximum 32.208 µF output caps, their 1.156 ms analytical minimum startup, maximum output voltages and 85% efficiency. The full host plus bounded branch capacitor charge then gives **5.869068 A**, approximately 1.938 A input. Overlapping logic and host charging would require **6.039068 A** and fails; starting everything with main charging would require **10.106070 A** and fails. Normal sequence separation therefore matters. The host's minimum 1.040 s delay assumes initially discharged TPS3890 CT; arbitrary short warm resets can invalidate it. Switch slew, external FPGA/host capacitance, undervoltage load behavior, actual peaks and loop response require measurements, not just arithmetic.

## Magnetics, regulation and thermal limits

The calculation deliberately uses Lmin = 4.7 µH × 0.8 × 0.7 = **2.632 µH**, an assumed bias/tolerance bound, and Lmax = 5.64 µH. The 49.9 kΩ frequency row is 400-480 kHz; an additional 0.5% screening allowance gives 398-482.4 kHz. At 30 V and 6 A this produces approximately **4.009 A peak-to-peak ripple, 8.005 A peak and 6.111 A RMS**. The minimum calculated current threshold is 8.170 A, so there is little spare corner margin. The reference-clamp case leaves only approximately 11 mA margin. Hot inductance needs direct confirmation.

The shunt/current-sense threshold gives 8.170-10.544 A before propagation delay. Using TI's **typical** 75 ns delay at the reference clamp gives approximately **11.923 A short-circuit peak**. This is not a guaranteed maximum: the table does not provide a worst-case delay, and hot saturation and PCB inductance are not characterized. Require a measured fault envelope and adequate hot magnetics margin.

At the stated corner, shunt loss screens at 0.229 W. An assumed linear copper TCR at 125°C gives approximately 0.742 W inductor copper loss, excluding core loss. The 85% efficiency assumption would imply 5.347 W total conversion loss at 6 A; that loss is distributed across the IC, magnetics and other parts. It cannot be converted directly into IC junction temperature. Vendor EVM thermal figures depend on its copper layout; they do not qualify this board's 70°C ambient goal.

The revised output ripple screen uses only the three ceramics' assumed 61.5 µF and 2 mΩ high-frequency ESR, predicting **28.494 mV peak-to-peak**. Input capacitor RMS screening uses 3 A at 50% duty; the independent 0.5 V input-ripple screen with 2 mΩ input ESR needs approximately 7.72 µF effective capacitance. The proposed input requirement is at least 10 µF after bias and temperature.

The earlier 82 µF full-unload estimate failed. Independent review found that the subsequent two-bulk calculation incorrectly used average 6 A instead of phase-peak inductor current; that superseded source/result snapshot is preserved in [before-peak-phase-correction](core-converter/before-peak-phase-correction/). The corrected calculation uses **695.1 µF effective minimum assumed** and **5 mΩ aggregate ESR/interconnect**. For each normal/reference input, it evaluates stored energy at both inductance endpoints with their own ripple peaks; the energy is convex over that range. It then conservatively adds the largest independent-corner ESR current step and worst half-ripple to the 5.05 V initial DC maximum.

At 30 V input the bound is **5.142659 V**. At 48.4 V reference input, energy uses Lmax5.64 µH/7.0075 A and ESR uses Lmin2.632 µH/8.1589 A, yielding **5.145316 V**, only **4.684 mV below 5.15 V**. This is a conditional arithmetic correction, with insufficient production margin: frequency-dependent impedance, control delay and board inductance remain unproven. Excessive ESR is rejected rather than producing negative capacitance. The Panasonic 6.5 mΩ catalog figure is specified at 100-300 kHz and 20°C; doubling each part's ESR, dividing by three parallel parts and adding 0.666667 mΩ interconnect is an assumption, not a guaranteed temperature/lifetime bound. Endurance tanδ is not an ESR guarantee. [Panasonic SVPG catalog](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C175.pdf)

The revised external compensation derives from TI's current-mode procedure: **9.53 kΩ/22 nF/330 pF**, typical crossover approximately **6.983 kHz** at minimum capacitance, zero **759 Hz**, high-frequency pole **45.38 kHz** including the example's 38 pF internal capacitance. These are starting values. Bode, load-step and temperature testing must cover actual output capacitors, downstream converters, maximum and minimum capacitance and diode-emulation transitions. Buck PG's broad windows do not certify a ±3% rail.

## Package and independent circuit review

The actual RRX0029B drawing, revision 4228757/D April 2024, was visually inspected on PDF pages53-55. It contains an irregular VIN copper area joined to pins1/2/27-29, a separate switch copper area joined to20-22, and controller ground pad30. The large VIN/SW regions use defined mask apertures; the stencil has segmented openings. **No custom footprint is emitted or qualified by this review.** Exact copper-versus-mask contours, paste and pin mapping need a separate checked implementation; a generic QFN or three-rectangle substitute would be misleading. The source drawings and rendered evidence are retained locally.

The initial independent netlist review found 29 components and 18 nets. Its converter connections matched the contract; the selected long-side 0612 shunt incorrectly had a generic 1206 footprint. The root removed that assignment and the nonexistent temporary converter footprint. That historical finding concerns layout mapping, not schematic connectivity. The revised bulk circuit and final ERC/connectivity evidence belong to the root's block report; bulk footprints also remain unqualified.

## Reproduction and remaining release gates

```powershell
python -m unittest discover -s tests -p test_core_converter_analysis.py -v
python tools/core_converter_analysis.py --output research/core-converter/analysis.json
```

Fifteen scoped arithmetic tests passed, including impossible operating points, lowered efficiency, changed load/capacitance, incorrect part substitutions, nonfinite/boolean/huge inputs, falsely injected stored results, excessive ESR, missing logic sequencing and the preserved phase-peak failure. The calculator recalculates from inputs and reports failed cases. Fifteen separate SBC tests cover its circuit and bounds, including retained CT charge. This is not SPICE, PCB DRC, power-integrity analysis, thermal measurement or target-device testing.

The concrete remaining blockers are adequate transient margin and physical regulation, guaranteed slew/capacitance and actual compute peaks, hot magnetics/efficiency/temperature, loop stability, partial-power/backfeed/negative-input behavior, fuse/source coordination, exact footprints, PCB layout and complete costing. The selected part, corrected conditional arithmetic and editable circuits do not close these gates.
