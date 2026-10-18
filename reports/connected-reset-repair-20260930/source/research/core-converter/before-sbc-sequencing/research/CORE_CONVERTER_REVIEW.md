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
| Output capacitance | 4 × TDK CGA6P1X7S1A476M250AC, 47 µF/10 V |
| VCC / VDDA bypass | 4.7 µF/16 V and 100 nF/16 V respectively; effective values require selection review |
| Bootstrap | 47 nF/25 V between CBOOT and SW4; fixed 5 V mode does not need the 8 V-mode series resistor |
| Fixed output selection | 24.9 kΩ from FB to VDDA: selects 5 V output and 5 V VCC |
| Frequency / configuration | 49.9 kΩ RT to ground; 29.4 kΩ CONFIG to ground; standalone, DRSS initially off |
| Operating mode | PFM/SYNCIN to VDDA: diode emulation at light load |
| Compensation | EXTCOMP → 4.99 kΩ → 10 nF → AGND; separate 47 pF EXTCOMP to AGND |
| Bias | BIAS to CORE_5V, using VIN-powered internal bias during startup |
| Enable | 100 kΩ protected input to C_PGOOD; 10 kΩ C_PGOOD to ground; C_PGOOD to buck EN |
| Status | Buck PG open drain, 100 kΩ to IO_3V3; status only, not a safety permission |

The selected inductor's 15.2 A saturation specification means a **typical 30% inductance reduction at 25°C**. Its thermal-current figures are reference values, not hot-board ratings. [Coilcraft XAL7070 datasheet](https://www.coilcraft.com/getmedia/1ba55433-bcc8-4838-9b21-382f497e12e0/xal7070.pdf) The exact shunt has ±50 ppm/K TCR; 2% total resistance allowance is an engineering screening bound that still needs lifecycle/temperature qualification. A normal 1206 footprint is wrong for its long-side terminals. [Susumu exact part](https://www.susumu.co.jp/en/product_detail/?pdid=560)

The two TDK ordering codes are confirmed in the manufacturer's catalog. Their bias curves were not successfully downloaded: HTTP 403 responses are recorded as a limitation. Nominal capacitance cannot stand in for effective capacitance. [TDK input capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA6M3X7S2A475K200AE), [TDK output capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA6P1X7S1A476M250AC)

Small passive MPNs, a final land pattern, supply lifetime and quantity pricing remain open. This is one integrated converter and one inductor, not an extra compute module or a complete purchased power board. It is cost-conscious in architecture but has **no validated manufactured-cost claim**. PCBWay must eventually quote these exact qualified parts and permitted substitutions.

## Startup without a computer dependency

The entry TPS26630 pulls C_PGOOD low while its output capacitor charges. It releases only after its FET is enhanced and its PGTH voltage is valid. The protected-24 V divider then enables LM70660. Neither the computer nor 3.3 V needs to exist first. TI explicitly supports using entry PGOOD to enable a downstream converter. [TPS2663 Rev. G, Sections 8.3.2 and 9.2.2.5.1](https://www.ti.com/lit/ds/symlink/tps2663.pdf)

**Remove the existing core entry 10 kΩ PGOOD pull-up to IO_3V3.** Leaving it fitted would connect the divider to an unpowered 3.3 V rail. Expose this boundary as an analog enable/control node; future digital diagnostics need appropriate buffering. No second active-high driver is allowed on that node.

At 19/30/48.4 V the released divider is nominally 1.727/2.727/4.400 V. Even with the entry's 130 Ω maximum specified pull-down, the 48.4 V reference case is approximately 62 mV while asserted. The buck's precision rising threshold is 0.95-1.05 V. These relationships are comfortably separated under the stated normal electrical conditions. The converter starts well after the entry output ramps, avoiding simultaneous bulk-input charge and full buck load.

This does not prove all abnormal states. TPS26630's normal PGOOD electrical guarantees assume IN_SYS above 4.5 V. Below that, with negative raw input, or with output energy feeding backward, PGOOD function is not established here. The divider limits a retained positive protected voltage, but it cannot guarantee shutdown without an operating sink. The LM70660 BIAS recommendation also requires BIAS not to exceed VIN; an externally powered 5 V rail is therefore an unresolved case. Protected-input negative overshoot must remain above the buck's −0.3 V pin limit, and the entry's negative clamp remains unqualified. Machine output inhibition must be independent; supply restoration and buck hiccup recovery cannot authorize motion.

## Load, input current and startup limits

The earlier ledger's 5.35 A core budget has two additions: encoder switch overhead/fault behavior, and the logic-power block's revised 0.29/0.38/0.62 A reservations (+0.04 A). The resulting **normal load is 5.390388 A**, and simultaneous limited encoder faults reserve **5.557490 A**. Only **0.442510 A** remains before the converter's 6 A rating. Unknown SBC boot/peripheral peaks cannot be declared covered by that margin.

Use the proposed **19-30 V connector envelope**, 0.20 Ω total input-path resistance, 85% converter efficiency as a screening assumption, 60 mA analog input reservation and 5 mA entry/auxiliary allowance. Solve the input current self-consistently:

```text
Iin = Vout_max × Iout / [efficiency × (Vconnector − Rpath × Iin)] + Iaux
```

At 19 V, approximately 1.783 A normal, 1.837 A encoder-fault and **1.981 A at 6 A output** are required. The calculator carries exact results. The existing 8.20 kΩ entry limit's 1.966 A conservative screening minimum is therefore too marginal for a full 6 A claim. Recommend **7.50 kΩ**: nominal 2.4 A, screened 2.149-2.653 A, within the proposed 3 A source/wiring target. The ±10% transfer assumption at this exact ILIM resistor is not a TI guaranteed bound; preserve that open qualification gate. A foldback supply also needs its own startup review.

The original 18 V whole-controller minimum remains unresolved because the separate analog converter requires 18 V after path drop. The buck itself is not the reason for the 19 V draft. The old 2 A source rating has not become a qualified 3 A source merely by changing the limiter.

The buck's fastest specified soft-start is 1.9 ms. With a **350 µF maximum total charge-capacitance budget**, 5.05 V rise requires about **0.930 A** beyond the running load. Encoders held off leave a 4.99 A startup reservation, giving **5.920 A** total. Four local 47 µF capacitors alone can screen at 275.232 µF when +20% initial and +22% X7S temperature allowances are combined, leaving only 74.768 µF for all connected downstream capacitance. That downstream limit is not yet proven for the actual computer/carrier.

**Fastest startup with both encoder fault currents fails the 6 A screen**, requiring about **6.488 A**. Do not claim guaranteed boot under that combination. Existing encoder EN pull-downs only guarantee off when their drivers are high impedance; retained-high and partial-power behavior must be tested or hardware gated. Output-capacitor charge current, downstream undervoltage constant-power behavior, switch self-consumption and SBC peaks require a measured startup envelope. The current arithmetic is not a time-domain model.

## Magnetics, regulation and thermal limits

The calculation deliberately uses Lmin = 4.7 µH × 0.8 × 0.7 = **2.632 µH**, an assumed bias/tolerance bound, and Lmax = 5.64 µH. The 49.9 kΩ frequency row is 400-480 kHz; an additional 0.5% screening allowance gives 398-482.4 kHz. At 30 V and 6 A this produces approximately **4.009 A peak-to-peak ripple, 8.005 A peak and 6.111 A RMS**. The minimum calculated current threshold is 8.170 A, so there is little spare corner margin. The reference-clamp case leaves only approximately 11 mA margin. Hot inductance needs direct confirmation.

The shunt/current-sense threshold gives 8.170-10.544 A before propagation delay. Using TI's **typical** 75 ns delay at the reference clamp gives approximately **11.923 A short-circuit peak**. This is not a guaranteed maximum: the table does not provide a worst-case delay, and hot saturation and PCB inductance are not characterized. Require a measured fault envelope and adequate hot magnetics margin.

At the stated corner, shunt loss screens at 0.229 W. An assumed linear copper TCR at 125°C gives approximately 0.742 W inductor copper loss, excluding core loss. The 85% efficiency assumption would imply 5.347 W total conversion loss at 6 A; that loss is distributed across the IC, magnetics and other parts. It cannot be converted directly into IC junction temperature. Vendor EVM thermal figures depend on its copper layout; they do not qualify this board's 70°C ambient goal.

The proposed 82 µF effective output value is the TI application example's starting point, not a measured minimum for these four capacitors. With assumed 2 mΩ aggregate ESR, estimated output ripple is about 23 mV peak-to-peak. Input capacitor RMS screening uses 3 A at 50% duty; the 0.5 V input-ripple screen needs approximately 7.72 µF effective capacitance. The proposed input requirement is at least 10 µF after bias and temperature.

**Full 6 A load removal fails the 4.85-5.15 V rail target.** An energy-only screen using the 5.05 V initial maximum and 5.64 µH inductance predicts about **5.289 V**, before control-delay/ESR uncertainty. At least 199 µF effective capacitance would be needed for that idealized event. The 82 µF candidate supports only a roughly 3.85 A unload in that simplified screen. Therefore either bound the real simultaneous load step or increase storage and redesign startup/compensation; do not silently loosen the rail specification.

The external compensation starting values derive from TI's current-mode procedure: typical crossover approximately 30.99 kHz, zero 3.19 kHz and high-frequency pole approximately 375 kHz including the example's 38 pF internal capacitance. Compensation is unproven until Bode and transient checks include actual output capacitors, downstream converters and diode-emulation transitions. Buck PG's broad undervoltage/overvoltage windows do not certify a ±3% rail.

## Package and independent circuit review

The actual RRX0029B drawing, revision 4228757/D April 2024, was visually inspected on PDF pages53-55. It contains an irregular VIN copper area joined to pins1/2/27-29, a separate switch copper area joined to20-22, and controller ground pad30. The large VIN/SW regions use defined mask apertures; the stencil has segmented openings. **No custom footprint is emitted or qualified by this review.** Exact copper-versus-mask contours, paste and pin mapping need a separate checked implementation; a generic QFN or three-rectangle substitute would be misleading. The source drawings and rendered evidence are retained locally.

Independent review of the actual netlist found 29 components and 18 nets. All converter pin connections and passive topology matched the contract. One concrete issue was reported to the root author: the selected long-side 0612 shunt had a generic 1206 footprint. The root removed that unqualified assignment along with the nonexistent temporary converter footprint; a subsequent read confirmed both fields are blank. This finding is about layout mapping, not schematic electrical connectivity. The final circuit/ERC evidence belongs to the root's block report.

## Reproduction and remaining release gates

```powershell
python -m unittest discover -s tests -p test_core_converter_analysis.py -v
python tools/core_converter_analysis.py --output research/core-converter/analysis.json
```

Ten scoped arithmetic tests passed, including impossible operating points, lowered efficiency, changed load/capacitance, incorrect part substitutions, nonfinite/boolean/huge inputs and falsely injected stored results. The calculator recalculates from inputs and reports failed cases. It does not perform SPICE, PCB DRC, power-integrity analysis, thermal measurement or target-device testing.

The concrete blockers are full-load transient regulation, startup capacitance and encoder-off guarantee, actual compute peaks, hot magnetics/efficiency/temperature, loop stability, partial-power/backfeed/negative-input behavior, fuse/source coordination, exact footprints, PCB layout and complete costing. The selected part and editable schematic are useful progress; they do not close these gates.
