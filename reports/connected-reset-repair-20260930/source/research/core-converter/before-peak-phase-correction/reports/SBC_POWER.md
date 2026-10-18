# Hardware-supervised SBC supply

28 September 2026. This is an actual editable KiCad circuit that waits for CORE_5V, then starts the computer through a controlled-slew switch. It does not need running Linux, an FPGA image or ESP firmware to start power. **It is a candidate circuit, not a qualified power subsystem.**

Artifacts: [schematic](../hardware/sbc_power/sbc_power.kicad_sch), [PDF](../hardware/sbc_power/sbc_power.pdf), [netlist](../hardware/sbc_power/netlist.xml), [design envelope](../hardware/sbc_power/design-envelope.json), [BOM](../hardware/sbc_power/bom.csv), [ERC](../hardware/sbc_power/erc.json), [bounded calculations](../research/sbc-power/analysis.json), [validation and hashes](../hardware/sbc_power/validation.json).

## Circuit and boundaries

U1 is **TPS22990DMLR**, a 5.5 V, 10 A load switch used here for a 3 A computer branch. Its pad11 is the input-connected exposed thermal pad, **not ground**. U2 is **TPS389001DSET**, the adjustable supervisor. This six-terminal DSE package has no additional exposed pad. Both footprints remain unassigned pending independent land-pattern review. [TI switch datasheet](https://www.ti.com/lit/ds/symlink/tps22990.pdf), [TI supervisor datasheet](https://www.ti.com/lit/ds/symlink/tps3890.pdf)

| Device | Exact pin connections |
| --- | --- |
| U1 TPS22990DMLR | 1 slew capacitor;2 NC;3 VIN CORE_5V;4 VBIAS CORE_5V;5 ON SBC_ENABLE;6 LOGIC_GND;7 PG;8/9/10 SBC_5V;11 thermal pad CORE_5V |
| U2 TPS389001DSET | 1 SENSE divider;2 LOGIC_GND;3 MR;4 VDD CORE_5V;5 delay capacitor;6 open-drain RESET to SBC_ENABLE |
| JIN1 | 1 CORE_5V;2 LOGIC_GND |
| JOUT1 | 1 SBC_5V;2 LOGIC_GND |
| JSTATUS1 | 1 SBC_ENABLE;2 SBC_SWITCH_PG;3 LOGIC_GND; **5 V domain** |
| JMR1 | 1 SBC_RESET_N;2 LOGIC_GND; optional normally-open dry contact only |

RHI1/RLO1 are 31.6 kΩ/10 kΩ, 0.1%, 10 ppm/K. RESET/ON has 330 kΩ to CORE_5V and 330 kΩ to ground. MR has 100 kΩ to CORE_5V. The switch's PG has 100 kΩ to SBC_5V. Input bypass is 2.2 µF plus separate 100 nF local capacitors at switch bias and supervisor; the output has 1 µF. These values require effective-capacitance checks and exact passive MPN selection.

CTSW1 is 1 µF/50 V X7R, requiring **470 nF minimum effective capacitance**; the switch CT node can reach 15 V, so a low-voltage capacitor is unsuitable. CTSUP1 is 2.2 µF/16 V X7R, requiring **1.2-3.2 µF effective capacitance** at its operating voltage. All other circuitry, connectors and passive footprints are also unqualified rather than automatically assigned generic production lands.

## Hardware startup and brownout behavior

The supervisor holds the switch off while CORE_5V rises. At valid sense voltage it starts its independent delay. Only after that interval does RESET release, allowing the ON divider to rise. The switch then slews the separate SBC capacitors. This prevents the computer's 3 A reservation from coinciding with the main converter's bulk-capacitor charge.

With 0.2% total sense-resistor allowance, 1% supervisor threshold accuracy and ±100 nA conservative sense-leakage screening, falling threshold is **4.7186-4.8497 V**, rising threshold **4.7474-4.8792 V**. The top falling corner is only 0.283 mV below the stated 4.85 V lower rail envelope: noise and tolerances must be qualified, and this comparator does not certify the whole ±3% rail. The 4.95 V minimum DC converter setpoint is above the maximum rising threshold. Brownout detection cannot guarantee the computer remains above 4.75 V during an arbitrary fast collapse.

Using the supervisor's specified charge-current and threshold corners gives **1.040-4.587 s** delay for the stated effective CT limits. Minimum released ON is approximately 2.367 V after leakage screening, exceeding the switch's 1.2 V required high. Below the supervisor's normal 1.5 V operating range, its 0.8 V power-on-reset specification is conditional on a 15 µA sink load; the 330 kΩ pull-up draws only 2.42 µA at 0.8 V. The low-voltage divider and reset output do not establish blanket partial-power qualification.

On brownout or manual reset, RESET asserts low; after recovery it releases automatically following the delay. There is no restart latch or machine permission. Supervisor assertion and switch turnoff propagation require physical characterization; typical delays are not guaranteed hard maximums. PG on TPS22990 means the FET gate has reached its fully-on condition, **not that output voltage is independently within tolerance**. It also requires valid VBIAS. A missing or externally powered diagnostic rail must not be misread as machine readiness.

## Separate capacitance, current and voltage budgets

The SBC branch permits **1.0 mF maximum total charge capacitance**, including its local capacitor, computer, carrier and any connected peripherals. The switch's typical 10%-90% rise-time equation, evaluated with 470 nF CT and an additional factor of 0.5 for faster operation, gives about **13.799 ms**. That screens to **0.299 A capacitor current**, plus the full 3 A running reservation. This factor is a conservative engineering assumption, not a TI guaranteed minimum rise time. The equation was characterized near 5 V bias and smaller CT/load examples; the extrapolation, actual waveform slope and computer undervoltage load behavior must be measured.

With an 8 mΩ assumed switch resistance across the proposed operating range, 3 A gives **24 mV drop and 72 mW steady loss**. Add a maximum 15 mΩ trace/contact budget to obtain **4.781 V** at the computer from a 4.85 V main rail. TI specifies lower on-resistance at its listed bias conditions; the expanded 8 mΩ system bound still needs qualification. This allocation excludes an arbitrary external USB cable or unknown connector resistance.

The internal discharge resistance's 253 Ω maximum, 1 mF load and 1.040 s minimum delay predict approximately **84 mV** remaining from 5.15 V before re-enable. That calculation applies only while the discharge circuit is powered and no source backfeeds the output. It does not establish safe discharge after all supplies disappear.

**TPS22990 is not a current limiter, reverse blocker, electronic fuse or overvoltage cutoff.** A shorted computer can collapse the shared main rail and trigger upstream protection. Independent USB or other SBC power can bypass sequencing through reverse paths. Such alternate powering remains unsupported until an explicit reviewed isolation arrangement is added. Protection response, startup switch dissipation/SOA, faults, hot-plug and partial-power behavior remain physical test gates.

## Main converter correction

The main converter now uses three existing 47 µF ceramics plus **two Panasonic 16SVPG330M** polymer capacitors. The 330 µF/16 V parts have 6.5 mΩ catalog ESR at 100-300 kHz and 20°C. Two parts screen to 422.4 µF minimum and 950.4 µF maximum when ±20% initial capacitance and a separate ±20% lifetime allowance are combined. The assumed 2× ESR factor is **not** a manufacturer guarantee over temperature, aging and control-loop frequency. [Panasonic SVPG catalog](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C175.pdf)

The revised [core calculations](../research/core-converter/analysis.json) include the extra 3 mA branch/bulk allowance and the independent power-sequence block's 10 mA reservation. Normal demand is **5.403388 A**; simultaneous limited encoder faults reserve **5.570490 A**. Maximum main charge capacitance is **1.231256 mF**, including the existing logic/encoder/transmitter bypass tally, the new SBC input bypass and power-sequence bypass.

With the computer physically off, all other loads including encoder faults plus the fastest 1.9 ms converter capacitor ramp total **5.843039 A**. After the main rail is charged, computer running current plus controlled branch charging totals **5.869068 A**. Both fit 6 A under the stated assumptions. Starting everything together would require **8.843039 A** and fails: the sequencing is essential, not decorative.

The full 6 A unload screen now includes 5.05 V maximum DC setpoint, approximately 14.25 mV initial half-ripple, 483.9 µF assumed effective storage and 7 mΩ aggregate ESR/interconnect. It predicts **5.147506 V**, only **2.494 mV below** the 5.15 V target. This closes the earlier explicit arithmetic failure but is **not sufficient transient margin for production**: actual capacitor impedance, board inductance and control response remain unproven. The calculator rejects excessive ESR rather than producing a negative capacitor requirement. Compensation is revised to **9.53 kΩ/22 nF/330 pF** as a derived starting point; Bode, load-step and temperature tests remain required.

## Evidence and reproduction

**KiCad 10.0.4 ERC: zero violations. Fourteen SBC tests and thirteen core-calculation tests pass.** Independent mutations cover incorrectly grounded input pad, bypassed power path, circular supervisor supply/sense, permanent enable, missing or wrongly rated CT, missing default pull-down, wrong supervisor variant and misleading PG output type. Calculation tests preserve the old failures, reject invalid/nonfinite inputs, and expose increased capacitance, ESR and wiring drop. PDF overview and component-detail views were inspected.

```powershell
python tools/hardware_build_sbc_power.py
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist --format kicadxml --output hardware/sbc_power/netlist.xml hardware/sbc_power/sbc_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc --format json --severity-all --exit-code-violations --output hardware/sbc_power/erc.json hardware/sbc_power/sbc_power.kicad_sch
python -m unittest discover -s tests -p test_sbc_power.py -v
python -m unittest discover -s tests -p test_core_converter_analysis.py -v
python tools/hardware_validate_sbc_power.py
```

Regeneration replaces this generated block; preserve manual edits first and refresh PDF/netlist/ERC together. Historical core failure evidence remains at `research/core-converter/before-sbc-sequencing/`, with the original source/evidence hashes verified before copying. No physical device access, PCB layout, board DRC, SPICE model validation, production quote or manufacture release is claimed.
