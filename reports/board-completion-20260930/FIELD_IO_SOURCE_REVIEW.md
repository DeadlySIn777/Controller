# Field I/O primary-source review

30 September 2026. Source inspection, visual PDF-table inspection and explicitly labelled arithmetic only. No circuit, profile, CLI, firmware or frozen IS-1 modification. No target compilation, ERC/DRC rerun, purchased hardware or physical measurement. FIO-P1 is a proposed IS-2 option study; frozen DO remains 0.5 A/channel and 2 A/four-output group. The full DO bank is still unfinished.

Primary reference: **TI TPS274C65, SLVSFZ2C, Rev C, February 2024**, exact selected **TPS274C65ASRHAR**. The retained PDF is `field-io-source-review/sources/tps274c65-SLVSFZ2C.pdf`, SHA-256 **44b8df8d0cdc7f8497690bb97e652697251f5e7c2802a9551602e31c29bb0ac8**. Package: RHA VQFN-40, 6×6 mm. The [exact TI part page](https://www.ti.com/product/TPS274C65/part-details/TPS274C65ASRHAR) identifies ACTIVE lifecycle but returned no usable quantity price; its stock/login display is not a supplier commitment. No $4 quotation was verified.

## Source findings and consequences

| Checked source fact | Project consequence |
| --- | --- |
| High-side quad switch; AS has ADC/current diagnostics; BS does not. Table 4-1 marks AS unsuitable for 2 A current-limit operation and ASH suitable. | AS is sourcing-only. A sinking/NPN-compatible DO needs another real topology. BS is not a diagnostic-equivalent cheaper substitute. ASH is a candidate, not an approved substitution. |
| Recommended VS: 12–36 V; VDD: 3.0–5.5 V. Absolute VS: 40 V continuous, 60 V for <1 ms **while ON**. Sections 6.1/6.3. | Neither the part name nor software permits arbitrary voltage. Qualify nominal-12 V supply tolerance and all rail/transient states; the ON-state exception does not qualify OFF-state 60 V or continuous 48 V. |
| VS undervoltage protection falling 8.6–9.3 V, recovery 9.5–10.3 V; fixed warning falling 12–13.5 V, recovery 11.2–15.8 V. Section 6.5. | Normal nominal-12 V can assert the warning. Preserve raw warning and a separate qualified rail assessment, rather than masking all undervoltage behavior. Below the qualified operating minimum, diagnose the value as out of range. |
| ILIM is a 4-bit code, shared CH1/2 and CH3/4; ILIM_SET selects one shared setting or the two pair settings. Registers 0x21–0x23, tables 8-46–8-48. | No arbitrary per-channel limit assignment. The frozen eight-code IOL1 blob requires a versioned pair constraint or a different chip. |
| Four channels enabled: ILNOM 1.6 A/channel at 85°C ambient; two enabled: 2.5 A/channel at 85°C. Section 6.5. | These specified operating cases are not permission to run all four at 2 A under any enclosure/temperature. The board needs its own simultaneous-load and thermal rating. |
| RON maximum 72 mΩ at 25°C and 110 mΩ at 125°C under the table's conditions. RθJA 25.4°C/W uses a JEDEC four-layer board. Sections 6.4/6.5. | Use hot resistance for loss screening. Package thermal metrics do not certify our motherboard copper or cooling. |
| Internal current ADC: 10 bits; current and VS use additional LSB registers; conversion timing 128 µs typical per measurement. Sections 6.5/8.3.6.6 and register tables. | Resolution is not accuracy or a guaranteed whole-chip scan period. Read/assemble coherent values and report range, age and invalid conditions. |
| RCB requires an external blocking MOSFET; reverse-blocking condition makes ISNS/ADC report zero with sensing unavailable. Section 8.3.5.9. | An integrated gate controller is not a fitted reverse-blocking path. Report zero as invalid during blocking, rather than healthy no-load. Include external MOSFET resistance/cost. |
| DO_EN LOW disables all four outputs. ADC and device watchdog reset disabled; ILIM pair code resets 0xA. Auto-retry defaults enabled. Tables 5-1, 8-46–8-50. | Hold hardware inhibition until protected configuration/readback succeeds. Do not rely on reset values for the frozen 0.5 A tier or fault-latched behavior. |

All above checked against [TI's exact datasheet](https://www.ti.com/lit/ds/symlink/tps274c65.pdf). Relevant page images were inspected alongside the extracted text; the retained source is authoritative for table conditions.

## Actual limit-code screen

AS/BS nominal code ladder, 0x0 through 0xF in amperes: **0.25, 0.33, 0.40, 0.48, 0.56, 0.67, 0.72, 0.85, 1.00, 1.10, 1.25, 1.50, 1.60, 1.75, 1.90, 2.20**. This is not continuous software-adjustable precision. The following are selected guaranteed min/typ/max table values during the specified regulated short-circuit test (RL<200 mΩ, VDD=3.3 V, section 6.5 conditions), not guaranteed instantaneous peak currents. [TI tables 8-4 and 6.5](https://www.ti.com/lit/ds/symlink/tps274c65.pdf)

| Variant / code | Nominal setting A | Table min/typ/max A | Interpretation |
| --- | ---: | --- | --- |
| AS 0x3 | 0.48 | 0.40 / 0.48 / 0.55 | Cannot both guarantee a 0.5 A load and guarantee a 0.5 A hard ceiling |
| AS 0x5 | 0.67 | 0.53 / 0.67 / 0.78 | Finite tolerance and little load margin; not automatically a selected default |
| AS 0x6 | 0.72 | 0.62 / 0.72 / 0.82 | Frozen default candidate for the 0.5 A continuous-load tier |
| AS 0x7 | 0.85 | 0.72 / 0.85 / 1.00 | Highest frozen permitted code under its 1 A maximum regulated-fault limit |
| AS 0x8 | 1.00 | 0.85 / 1.00 / 1.15 | A setting labelled 1 A does not guarantee a 1 A load |
| AS 0xA | 1.25 | 1.00 / 1.25 / 1.50 | Reset default; higher than the accepted frozen limit profile |
| AS 0xB | 1.50 | 1.19 / 1.50 / 1.75 | Possible 1 A tier headroom only after whole-bank re-rating |
| AS 0xF | 2.20 | 1.85 / 2.20 / 2.55 | Cannot guarantee 2 A operation |
| ASH 0xE | 2.26 | 2.01 / 2.26 / 2.88 | Candidate 2 A tier; larger protected fault current must be designed |
| ASH 0xF | 2.45 | 2.06 / 2.45 / 2.84 | Candidate 2 A tier; not a drop-in electrical/protocol approval |

Inrush duration is another discrete setting, 0–64 ms. Options include unchanged limit, half-limit, twice-limit and a fixed higher threshold; they do not preserve the frozen ceiling interchangeably. Frozen configuration rejects the twice-limit and fixed-high options. At the AS 2.2 A setting, the specified short transient peaks reach 10 A when enabling into a short and 9.4 A for a short while enabled, with the table's 24 V / 2.2 µH minimum-inductance conditions. A programmed regulated limit is not an instantaneous peak clamp. [TI sections 6.5/8.3.3 and tables 8-5–8-7](https://www.ti.com/lit/ds/symlink/tps274c65.pdf)

## Diagnostic accuracy screen

Section 6.5 specifies current-sense output ranges. The arithmetic below applies the table's nominal KSNS=1160 at its 2.4 A range to those min/max sense currents. It excludes ADC/reference error, resistor tolerance, quantization, ground drop, saturation, filtering, calibration and low-range changes; it is **not** a complete current-measurement accuracy claim. [TI section 6.5, page 10](https://www.ti.com/lit/ds/symlink/tps274c65.pdf)

| True load | Source min/typ/max sense current | Apparent current from nominal ratio only | Error from nominal ratio only |
| --- | --- | --- | --- |
| 1 A | 0.834 / 0.862 / 0.890 mA | 0.96744–1.03240 A | −3.256% to +3.240% |
| 0.5 A | 0.410 / 0.424 / 0.450 mA | 0.47560–0.52200 A | −4.880% to +4.400% |
| 0.2 A | 0.151 / 0.168 / 0.184 mA | 0.17516–0.21344 A | −12.420% to +6.720% |
| 0.05 A | 0.020 / 0.037 / 0.054 mA | 0.02320–0.06264 A | −53.600% to +25.280% |

The reference range is 2.72–2.85 V, typical 2.8 V. With an **assumed** 1% sense resistor and nominal software conversion, the 0.5 A sense/reference/resistor-only screen becomes approximately **0.462585–0.542724 A** (−7.483% to +8.545%). Formula: `ISNS × 1160 × Ractual/Rnominal × 2.8/Vreference_actual`. Unknown ADC errors are still excluded. This is why “10-bit ADC” cannot become a blanket ±1% or low-current zero-detection promise. Calibrate and test each claimed measurement range; publish unavailable/stale/off-state semantics and test open-load detection with the actual attached load.

## Heat, banks, inductive loads and protection

Own hot-conduction arithmetic using 0.110 Ω: per quad IC at 0.5/1/2 A on all four channels is **0.11/0.44/1.76 W**; four ICs give **0.44/1.76/7.04 W**. This excludes quiescent current, optional RCB FETs, inductive release, switching/short-circuit power and neighbouring compute heat. External 16-channel 24 V load power is **192/384/768 W**, rather than heat dissipated entirely in the controller. Increasing load tier requires re-rating each four-output group, both field entries, fuses, connectors, copper and enclosure cooling; a switch IC's limit does not set the motherboard aggregate rating.

During a short, switch dissipation can approach supply voltage times regulated current while the output is near zero. Heat and fault-time behavior must be bounded with the entry and channel protection rather than left to continuous thermal cycling. Thermal shutdown's 160–210°C threshold is above the 150°C absolute junction maximum; the controller cannot use that protective shutdown threshold as its acceptable operating temperature. Characteristic guarantees here stop at 125°C junction. [TI sections 6.1/6.5](https://www.ti.com/lit/ds/symlink/tps274c65.pdf)

The output's inductive clamp is between VS and OUT, not a generic external 24 V flyback diode. The 24 V clamp table gives 40–50 V across the FET at its specified current; turn-off drives OUT negative. Use actual load L/I/R, release time, cable inductance, hot starting temperature and simultaneous channels. TI's single-pulse graph applies to one channel starting at 125°C; its repetitive statement allows 40% of that energy for one million pulses at 2 Hz. Do not extrapolate this into an arbitrary repetitive-duty guarantee. Add external suppression where the load profile exceeds the bounded energy case, ensuring required actuator release time. [TI section 8.3.5.3–8.3.5.4 and figure 8-27](https://www.ti.com/lit/ds/symlink/tps274c65.pdf)

Physical fuse plus channel current/thermal protection is an appropriate architecture to investigate. Fuse selection still needs voltage/interrupt rating, wire/terminal ampacity, time-current coordination, enclosure derating, inrush and short overshoot. Preserve hardware DO_EN, OUT_EN rearm, local/link watchdogs and latched fault history. Configuration may qualify a diagnostic threshold; it may not indiscriminately suppress a safety-relevant fault or remove the independent machine stopping chain.

## Source contradictions requiring conservative treatment

The application narrative and table 9-2 describe broader 6–36 V/36–48 V operation and a 48 V/36 V-TVS example, conflicting with the 12–36 V recommended and 40 V continuous absolute rating tables. Do not adopt the broader claims or that TVS blindly. Some auto-retry prose/figure descriptions and SW_FS_CFG descriptive text also disagree with their register value descriptions. Use the explicit register tables plus physical tests and obtain manufacturer clarification for ambiguous behavior; external inhibition must remain effective regardless. No relaxation or hidden waiver is made here.

## DI compatibility and cost boundary

Primary input reference: [TI ISO1212, SLLSEY7G](https://www.ti.com/lit/ds/symlink/iso1212.pdf), retained SHA-256 **41e0bc7308dd4e0cc8c7f30efb6a2cd87bcc865d9195095ff849be6036cb2328**. Sections 8.2.1–8.2.3 show physical sinking, sourcing and bidirectional arrangements. PNP/NPN changes require actual current-path wiring, not input inversion. Its two-receiver bidirectional example consumes both channels per field point, affecting DI24 counts. Threshold, leakage and cable-drop qualification is required for 12 V: the historical 562 Ω / 1 kΩ threshold arrangement can require 10.95 V to assert, so an **assumed** 12 V ±10% sensor supply at 10.8 V has no assertion margin even before sensor/cable drop.

At the user's **unverified** $4 each at 100 ICs, four quad output ICs cost $16 per DO16 bank. Buying 100 ICs supplies only 25 such banks. At 1/10/100 controllers the DO IC quantities are 4/40/400; unidirectional DI24 alone needs 12/120/1,200 ISO1212 packages. Motor alarms, safety inputs and extra bidirectional hardware are additional. The illustrative $40–80 complete-bank allowance has no complete fitted BOM, procurement, PCBWay assembly or test quote here. No motherboard or option price is approved.

See [the versioned configuration proposal](../../docs/FIELD_IO_CONFIGURATION_PROPOSAL.md) for preserved scope and the required implementation sequence. Exact source identities, arithmetic and unchanged frozen inputs are recorded in `field-io-source-review/receipt.json`.
