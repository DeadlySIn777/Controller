# Historical r0.1 power-entry source review

This source study is retained for provenance. The implemented r0.2 circuit uses core R4=7.50k and removes R9/R29 for the protected-input-powered converter EN dividers. Current values/results are in reports/POWER_ENTRY.md, hardware/power_entry/requirements.json and research/power-entry/analysis.json. The original r0.1 files remain in reports/power-protection-evidence-20260928. Lower r0.1 numbers are not current selection data.

# Nominal 24 V power-entry feasibility

28 September 2026. **Proceed with two separate, editable entry circuits using TPS26630RGER, but keep manufacture blocked.** The supporting values and pin/net dictionary are in [requirements.json](../WORKSPACE_REFERENCES.md#artifact-528acbae9751ba7a). This review performs source inspection and numerical corner screening. It provides no SPICE, ERC, layout, EMC, thermal measurement or fault-interruption evidence. It does not alter the electrical ledger or approve a power supply.

## Scope and voltage decision

The six-step/two-encoder ledger reserves 1.81 A on CORE_24V and 4.36 A on FIELD_24V. The core estimate includes the 5.35 A load on CORE_5V, conversion loss and the analog converter. Screens, motor-drive power and optional AI power are excluded. CORE and FIELD retain separate grounds, fuses and protection; a common diagnostic wire must not bridge them.

The existing ledger calls for 18–30 V and a 2 A core source. A converter requiring 18 V cannot receive that voltage from an 18 V connector after any positive series loss. For this draft, use **19–30 V at each entry**, with a proposed 3 A qualified core source/path and the existing 6 A field source target. This is an explicit narrower study envelope, not fulfillment of the unchanged 18–30 V requirement. To retain 18 V operation, qualify a converter/analog supply and current budget below 18 V at their pins.

A provisional complete series-path resistance ceiling of 0.20 Ω gives at least 18.638 V core and 18.128 V field at the ledger loads and a 19 V connector input. This allowance includes the physical fuse, holder, FET, eFuse, copper and contacts between the defined entry and output. Cable drop before the entry must already be included in the specified 19 V minimum. It is a design limit to verify, not a measured resistance. Temperature and ageing belong in that verification.

## Circuit to draw

Each positive input passes through its physical fuse, then reaches RAW_FUSED. A bidirectional TVS and nonpolar ceramic input bypass connect RAW_FUSED to that branch's ground. Q1 connects RAW_FUSED to the eFuse IN; the protected OUT feeds downstream loads. The complete electrical mapping is machine-readable in the JSON.

Select **TPS26630RGER**, with MODE open. This avoids the sustained 2× pulse-current feature of the 31 variant; brief fast-trip overshoot still exists. SHDN can remain open at startup using its internal pullup. A normally open dry contact to the local ground can shut down/reset it without depending on an unpowered Linux or ESP GPIO. Clearing this contact may restore rail power. It is not machine restart permission. Voltage-fault recovery and UVLO/power cycling can also restore operation; MODE open is not a latch for every fault. [TI TPS2663 Rev. G, Tables 5-1/6.5/8-1 and §8.3](https://www.ti.com/lit/ds/symlink/tps2663.pdf).

Q1 is **CSD19537Q3**: source pins 1–3 to RAW_FUSED, gate 4 to B_GATE, drain 5–8 and the exposed drain to IN. Its 100 V drain rating and ±20 V gate rating are stress limits. Use the manufacturer's footprint and short power connections. [TI CSD19537Q3, Figure 3-1 and electrical characteristics](https://www.ti.com/lit/ds/symlink/csd19537q3.pdf).

Q2 is **Nexperia BSS138P,215**: gate 1 to DRV, source 2 to RAW_FUSED, drain 3 to B_GATE. It offers specified 50 pF maximum input capacitance at the stated 10 V test condition, 60 V drain and ±20 V gate ratings. This is a candidate substitution for the generic BSS138 in TI's example, not a proven drop-in qualification. The capacitance depends on operating point and the layout adds capacitance. [Nexperia BSS138P, Tables 2/5/7](https://assets.nexperia.com/documents/data-sheet/BSS138P.pdf). The reviewed [onsemi BSS138](https://www.onsemi.com/pdf/datasheet/bss138-d.pdf) lists 27 pF typical rather than a guaranteed maximum, so that figure cannot close the driver-load check.

Use a short Q1-gate/Q2 loop. All IN/OUT pins must connect; the eFuse exposed pad connects to domain ground along with its ground pin. Every signal marked NC stays unconnected. No shared grounds, global diagnostic pullups or boot GPIO assumptions are implied.

## Thresholds and support values

Proposed initial resistor tolerance is 0.1%; the calculation reserves **0.5% total resistance error** for initial tolerance, temperature and ageing. Exact resistor MPNs must meet that combined allowance. No temperature coefficient or lifetime qualification is inferred from the printed tolerance alone.

| Function | Proposed values | Calculated range including comparator, leakage and total resistor error |
|---|---|---|
| UV/OV ladder | RAW→UVLO 887 kΩ; UVLO→OVP 29.4 kΩ; OVP→GND 34 kΩ | UV rising 17.262–18.726 V; falling 15.985–17.606 V |
| Same ladder | Same values | OV trip rising 32.288–34.818 V; release falling 29.907–32.729 V |
| Output PGTH | OUT→PGTH 140 kΩ; PGTH→GND 10 kΩ | Rising 17.455–18.553 V; falling 16.177–17.433 V |
| Current setting | CORE 8.2 kΩ; FIELD 3.65 kΩ | Screening only: CORE 1.966–2.427 A; FIELD 4.416–5.452 A |
| Current monitor | IMON→GND 10 kΩ; no bypass capacitor | Screening maximum 0.736 V core / 1.652 V field at the assumed limit corners |
| Diagnostic outputs | FLT and PGOOD each 10 kΩ to their local diagnostic rail | Core IO_3V3, field FIELD_5V; receivers/isolation remain to be designed |
| Slew control | dVdT→GND 100 nF, effective ±5% | Capacitive ramp screening below |

The 887 kΩ upper ladder resistor also respects TI's reverse-input guidance requiring at least 300 kΩ in the UVLO-to-input path. The maximum UV rise remains below the proposed 19 V entry minimum. **These values do not enforce an 18 V minimum at a downstream converter**: the falling thresholds are lower, and PGOOD alone cannot establish valid logic rails or position. Converter UVLO, power sequencing and independent output inhibit must handle brownouts.

At the worst low OV release corner, a source restored only to 30 V after an overvoltage event can remain off. Guaranteed release requires a lower voltage, below approximately 29.9 V. This behavior must be reflected in diagnostics; do not call it an unexplained failure or force a software override.

Corner calculations enumerate both leakage polarities, resistor endpoints and reference endpoints. For ladder resistors A/B/C from top to bottom, leakage currents U/O taken positive into the pins:

```
Vin(UV) = Vref*(A+B+C)/(B+C) + U*A + O*A*C/(B+C)
Vin(OV) = Vref*(A+B+C)/C     + U*A + O*(A+B)
Vin(PG) = Vref*(1+Rtop/Rbot) + I*Rtop
```

The JSON retains the numerical inputs and full-precision outputs. No interpolation is needed for the voltage-comparator extrema.

For ILIM, however, a ±7% headline is insufficient: the data table specifies 1.84/2/2.16 A at 9 kΩ, 0.54/0.6/0.66 A at 30 kΩ, and ±7% at its 4.02 kΩ and 3 kΩ points. The selected 8.2 kΩ and 3.65 kΩ are not those guaranteed test points. The reported current range uses `18,000/R` with an explicitly assumed ±10% transfer allowance and ±0.5% resistance. That is a screening model, **not a manufacturer guarantee over all resistor settings**.

FIELD has only about 56 mA between the 4.36 A budget and this model's minimum limit. Reconcile input-protection quiescent current, load tolerances and startup overlap before freezing the 3.65 kΩ value. Increasing it makes nuisance limiting worse; lowering it raises maximum fault current. CORE's proposed limit exceeds the old 2 A source capacity, which is why the 3 A source/path proposal is explicit. A source folding back first may prevent a clean electronic trip or boot.

## Startup, load and heat

For a prototype total output capacitance bounded at **1,000 µF including tolerances and all downstream inputs**, the gain/charging-current corner model with the 100 nF capacitor gives 397–609 V/s. Charging alone takes approximately 49–76 ms to reach 30 V, peaks at 0.609 A, and stores 0.45 J. Its fastest-ramp average eFuse charging loss is about 9.13 W. This is a capacitive calculation; it is not a guaranteed startup waveform or an SOA pass. Thermal regulation may change the ramp, especially in a hot enclosure. The data sheet's Figure 6-18 is typical EVM evidence, not our board qualification.

If the 1.81 A core load is already active, adding the modeled capacitor current produces 2.419 A; field produces 4.969 A. Both exceed their lowest assumed electronic current limits. Therefore **hold converters and field loads off through startup using a hardware sequence** or reduce and requalify the capacitance/startup load. Downstream-rail pullups on diagnostic PGOOD do not solve this: using that signal to bootstrap its own unpowered rail is circular. The actual converter EN interface remains open. A diagnostic-only entry drawing must say so.

At the present normal loads, using the eFuse's full-temperature maximum 53 mΩ and a 30 V/1.7 mA bias allowance gives approximately 0.225 W CORE and 1.059 W FIELD. Multiplying by the published 31.4 °C/W package reference metric yields rises of 7.1 °C and 33.2 °C. At a **proposed 70 °C local ambient**, those estimates stay below the 125 °C recommended junction ceiling. The actual PCB's heat spreading and neighboring heat sources may invalidate that estimate.

The external FET has no guaranteed hot-resistance maximum in the reviewed table. Screening with twice its 25 °C, 6 V-gate maximum of 16.6 mΩ gives 0.109 W CORE / 0.631 W FIELD. The lower-gate-voltage test point avoids relying on a 10 V RDS value when the eFuse gate drive may be lower. The 2× temperature factor remains an engineering assumption. At 55 °C/W the field estimate rises about 35 °C; a minimum-pad 160 °C/W example would rise about 101 °C and fail the proposed 70 °C ambient budget. Layout area is consequential; do not treat the small package as permission for a tiny copper island.

## TVS, fuse and fault coordination

The provisional input TVS is **Littelfuse SMCJ30CA**, bidirectional, after the physical fuse. Its catalog standoff is 30 V; breakdown is 33.3–36.8 V; the stated clamp is 48.4 V at 31 A for the specified 10/1000 µs test. These are waveform-dependent values, not a 48.4 V ceiling for every source. [Littelfuse SMCJ data sheet](https://www.littelfuse.com/assetdocs/littelfuse_tvs_diode_smcj_datasheet?assetguid=37388813-0d6d-4329-969b-1aa8b7614ac1).

At those reference conditions, 48.4 V is below the eFuse's 60 V operating upper input bound; 67 V is an absolute stress limit, not an operating target. Negative input and retained positive output must also meet their **combined** reverse differential limit: −48.4 V input against +35 V output is −83.4 V, only 1.6 V from the −85 V/10 ms absolute condition. Temperature-dependent clamp changes and trace/cable ringing can consume that margin. Q1's 100 V rating alone does not protect the eFuse from this differential stress. No ±500 V surge or IEC immunity level is claimed.

Provide effective 1 µF nonpolar input bypass and at least 0.1 µF at IN and OUT; 100 V capacitor ratings are draft targets, with bias/temperature derating checked at the final MPNs. The downstream circuitry should be selected for at least a 36 V operating upper input range, but this alone does **not** prove surge survival: overvoltage cutoff has finite delay, and abrupt input steps may reach OUT before shutdown. Verify permitted voltage versus duration at every downstream input. Negative OUT excursions, inductive energy and reverse-fed output energy remain unresolved. An arbitrary Schottky diode cannot be credited with guaranteeing the −0.3 V OUT minimum.

Serviceable fuse candidates for further coordination are **0997003.WXN (3 A)** and **099707.5WXN (7.5 A)** from Littelfuse's 58 V MINI 997 series. The primary series listing gives 1,000 A interruption at 58 VDC, with typical melting I²t of 9.4 and 68 A²s respectively. These are catalog candidates, not approved BOM selections; full source retrieval timed out and the primary indexed tables were used. The holder and rejection feature must also be qualified. [Littelfuse MINI 58 V data sheet](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-997-mini58v?assetguid=f4bf5724-5a40-4a44-8f08-c52ae959a5ef).

Using a 75% room-temperature screening factor gives minimum nominal ratings of 2.41 A core and 5.81 A field before additional ambient/holder derating. This makes 3 A and 7.5 A worth evaluating. It does not prove a 7.5 A fuse protects a path described merely as “6 A.” Fuse selection also needs DC interruption, temperature, opening curves, pulse duty and wire withstand. Typical melting I²t is neither maximum total clearing I²t nor proof that a TVS or transistor survives until clearing. [Littelfuse Fuseology](https://www.littelfuse.com/assetdocs/fuseology-selection-guide?assetguid=d812dff2-1c47-4dc3-bce7-07a4001ddc32).

The decisive unprovided inputs are the supply's minimum/maximum prospective fault current and its foldback/hiccup behavior. An eFuse-failed-short case or a shorted TVS may never open a physical fuse if the source folds back below its opening region. Conversely, a low-impedance source can exceed the fuse's interruption rating or semiconductor energy limit. Document the source, cable, connector and fault voltage; calculate both extremes; then test the assembled path. A TVS is a pulse absorber, not a sustained overvoltage regulator.

## Next engineering work

Draw both entry branches with the stated values and explicit unresolved interfaces. Then select the actual converters and enable sequence, update the voltage/current ledger only after that decision, and measure all startup loads. Resolve fuse/holder/source coordination, output clamps and the 19 V minimum case before PCB layout. Review thermal copper, short gate/clamp loops, return routing and separation before ERC/DRC. Later fault tests must cover reverse wiring, hot plug, sustained overload, each shorted protector, supply foldback, retained output voltage, inductive returns and power restoration. Every recovery begins with machine permission removed independently of Linux/ESP.

No parts were ordered, supplier contacted, device opened or PCBWay package produced. Downloaded TI originals and their SHA-256 hashes are under [research/power-entry](../WORKSPACE_REFERENCES.md#artifact-013818e25e329fc9); other sources were read through primary web documents/indexes, with retrieval limitations recorded in the JSON.

## Reproduction and independent drawing review

The implemented [calculation CLI](../WORKSPACE_REFERENCES.md#artifact-c272b8400200ffc9) reads current requirements and the electrical ledger, recalculates the corners, and records both input hashes. It ignores the requirements file's embedded previous results. Run:

```
python tools/power_entry_analysis.py --report research/power-entry/analysis.json
python -m unittest discover -s tests -p test_power_entry_analysis.py -v
```

All **16 tests passed**. They cover an analytical ideal-divider case, monotonic tolerance widening, malformed/nonfinite input, wrong FET orientation/current variant, joined grounds, source undersizing, changed load budgets and unsupported current-limit certainty. The [actual report](../WORKSPACE_REFERENCES.md#artifact-3b679fa7c47319d9) contains four current issues: OV recovery at the maximum input voltage, unsequenced startup on each branch, and the old core source capacity. A valid calculation never sets manufacturing readiness true.

An independent read of the newly drawn netlist found no topology/value error within this partial scope: 46 components and 48 nets, including 14 single-node MODE/NC nets. Q1 source/gate/drain orientation, the common KiCad drain pad, Q2 RAW-referenced pulldown, thresholds, local diagnostic pullups and separated grounds agree with this review. The drawing now uses candidate 2.2 µF/100 V RAW bypass and 1 µF/100 V IN/OUT bypass; their effective-capacitance requirements still need exact parts. Placeholder output-clamp and physical-fuse positions remain explicitly unselected.

Reviewed netlist SHA-256: `03387c36953aa155ed51795b2461e2d98fca511298e7b5001faa3d7134ced670`. This read-only review did not rerun KiCad or establish a complete protection circuit. The separate power-entry report owns the drawing's ERC and connectivity-test evidence.
