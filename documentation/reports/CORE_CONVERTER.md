# Core 5V converter circuit

28 September 2026. The actual KiCad circuit uses LM70660RRXR, a 4.7 µH inductor, a 6 mΩ current-sense resistor, three 47 µF ceramic output capacitors and three polarized 330 µF polymer capacitors. It connects the protected core entry to the logic, transmitter, encoder and delayed SBC supply blocks. This is an engineering candidate, not a production power supply.

Editable source: [schematic](../WORKSPACE_REFERENCES.md#artifact-1255086158f994f0), [exported netlist](../WORKSPACE_REFERENCES.md#artifact-f545a9ab2ab1476a), [part contract](../WORKSPACE_REFERENCES.md#artifact-2f9292320c358462), [BOM](../WORKSPACE_REFERENCES.md#artifact-ade619fae506a79a), [ERC](../WORKSPACE_REFERENCES.md#artifact-b1dd53bdf4b6d4e6), [validation identities](../WORKSPACE_REFERENCES.md#artifact-e073765c70bf6127). The [source review](../research/CORE_CONVERTER_REVIEW.md) and [numerical result](../WORKSPACE_REFERENCES.md#artifact-2fe142844e20d30d) retain manufacturer documents, equations, conditions and assumptions.

## Implemented design corrections

The entry PGOOD pin sinks the converter EN node while the entry rises. A protected-input-powered 100k/10k divider releases EN without an already-running computer or ESP. The old entry R9 pullup is absent so that divider cannot feed the unpowered IO3V3 supply. VIN supplies startup bias; output BIAS improves running operation.

Initial four-ceramic sizing failed the full-load unload screen and could not start all loads plus the total connected capacitance. The revised candidate adds three Panasonic16SVPG330M polymer capacitors, reduces the ceramic set to three, and uses the [power sequencer](POWER_SEQUENCE.md) to hold the logic regulators off during main charge and the [supervised SBC branch](SBC_POWER.md) to postpone its 3A load until main and logic supplies have charged. An intermediate two-polymer revision still failed when the inductor switching-phase peak was included; the third capacitor corrects that specific calculation failure. Compensation is now 9.53k / 22nF / 330pF. Those values are starting points for stability measurement, not a demonstrated phase margin. The original failed calculation and source identities are preserved under research/core-converter/before-sbc-sequencing.

## Current numerical screening

The following are computed scenarios, not measured ratings. Main-input calculations assume 19V at entry, a 0.20Ω path and 85% converter efficiency; selected-resistor eFuse accuracy and several component corners still require qualification. The earlier electrical ledger remains unchanged and is not silently promoted to these new limits.

| Scenario | Main5V current | Core entry current |
|---|---:|---:|
| Normal reservations | 5.403A | 1.787A |
| Both encoder branches at their assumed maximum limit | 5.570A | 1.841A |
| Main capacitor charge, SBC and logic physically off | 5.817A | 1.922A |
| Logic-rail charge, SBC off | 2.740A | 0.930A |
| SBC starts after main and logic charge | 5.869A | 1.938A |
| Simultaneous logic and SBC charge — fails6A | 6.039A | 1.994A |
| Every load active during main charge — fails6A | 10.106A | 3.340A |

The main charge-capacitance bound is 1706.5µF. The1.29A logic operating reservation is removed only during qualified cold main charge, when the independent sequencer holds the regulators off; their input capacitance and a1mA disabled-current allowance remain counted. A separate0.17A5V allowance covers logic output-capacitor charge. The SBC branch separately allows at most1mF and3A. Its slew bound is derived from a typical equation and the full delay requires initially discharged timing capacitance; short warm resets are not covered by this cold-start result.

The full6A unload screen now includes inductor peak switching phase, independently conservative inductance/ESR/ripple corners, and the48.4V reference input transient. It reaches **5.1453V**, only **4.68mV** below the5.15V study target. That is a tight, conditional screen using at least695.1µF effective output capacitance and at most5mΩ aggregate ESR. Controller response, actual capacitor impedance, additional energy delivered before turnoff and physical layout remain unproved. It must not be represented as a passed load-transient test. The input-surge current-limit screen also has very little margin. Compensation crossover is provisionally about6.98kHz under this model; phase margin remains unproved.

## Checks and unfinished physical work

The actual exported circuit passes16 independent connection/mutation tests and KiCad ERC has zero violations. Tests reject switched-node/current-sense errors, downstream-dependent startup bias, reversed or omitted bulk capacitors, old compensation, incorrect device variants and a generic1206 footprint on the long-side shunt. The schematic and IC detail were visually inspected. The combined scoped run is recorded separately in the connected-hardware evidence.

U1's RRX power lands, RS1's long-side0612 lands and bulk-capacitor footprints remain unassigned pending exact land review. Small-passive MPNs remain open. Output negative excursion, retained-output/reverse-feed behavior, fuse/source coordination, actual startup/boot, hot inductor saturation, control-loop stability, thermal layout and EMC are unfinished. This circuit does not grant machine permission or supply the display, motor drives or optional AI companion. The old18V input and2A core-source target are not met by this candidate.

Reproduce with tools/hardware_build_core_converter.py, native KiCad netlist/ERC export, tools/core_converter_analysis.py and tools/hardware_validate_core_converter.py. The connected assembly supplies the current full drawing for review.
