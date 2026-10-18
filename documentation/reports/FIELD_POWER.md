# Field-side 5 V power block — review r0.1

An editable standalone buck circuit now connects `FIELD_24V_PROTECTED` to the existing **5 V / 100 mA FIELD_5V target**. The frozen ledger still reserves 50 mA for the initial field-side isolation/logic load. This is a new design study; the shared electrical ledger and earlier entry circuit are not modified by this block. It does not qualify the whole machine's 18 V entry requirement or expand the six-joint baseline's capacity.

The selected [TI LMR36506R5RPER](https://www.ti.com/lit/ds/symlink/lmr36506.pdf) uses fixed 5 V sensing, RT tied to its internal VCC for 1 MHz, a 22 uH inductor and two 22 uF output capacitors. Its pin 9 is the ground pad; BOOT's 100 nF capacitor returns to SW. All returns stay on FIELD_GND. This converter provides no galvanic isolation itself; the complete product must preserve the FIELD/LOGIC barrier elsewhere.

## Review artifacts

- [Editable schematic](../WORKSPACE_REFERENCES.md#artifact-777745d0bb744b07), [project](../WORKSPACE_REFERENCES.md#artifact-8223a325664cd27b), local symbol library and [PDF](../WORKSPACE_REFERENCES.md#artifact-0bde6228815d2574).
- [Actual KiCad XML netlist](../WORKSPACE_REFERENCES.md#artifact-e82836a26d16b576), [ERC report](../WORKSPACE_REFERENCES.md#artifact-25d9e06313ca6eda), [BOM exported from that netlist](../WORKSPACE_REFERENCES.md#artifact-6d305e1efeb81e8c).
- [Machine-readable circuit](../WORKSPACE_REFERENCES.md#artifact-843889fa2ac42516), frozen ledger/entry snapshots and [bounded calculations](../WORKSPACE_REFERENCES.md#artifact-2eeaf9c637eb8d0c).
- [Primary source notes](../research/field-power/SOURCE_NOTES.md), [source hashes](../WORKSPACE_REFERENCES.md#artifact-ee746a72aa777dfb), [artifact hashes](../WORKSPACE_REFERENCES.md#artifact-e08597438355a47c).

KiCad 10.0.4 exported the schematic and reported **zero ERC violations**. The PDF was rendered and visually checked for pin/label placement, bootstrap return and separation of field nets. Twenty Python tests exercise the exported circuit and inject wrong pins, crossed grounds, self-powered enable, an extra pull-up, insufficient capacitor ratings, undersized inductor current margin, altered variants, invalid numbers, evidence corruption and ERC suppression. These are source/circuit checks, not SPICE, board DRC, assembly or physical measurements.

## Startup interface

| Boundary | Pin | Net / meaning |
|---|---:|---|
| J1, entry | 1 | FIELD_24V_PROTECTED; local 18-30 V study |
| J1 | 2, 4 | FIELD_GND |
| J1 | 3 | F_PGOOD: analog power-control node shared with entry TPS26630 PGOOD pin 16 |
| J2, load | 1 | FIELD_5V; 100 mA external load target |
| J2 | 2, 4 | FIELD_GND |
| J2 | 3 | FIELD_5V_PGOOD: buck's separate diagnostic output |

J1/J2 are logical circuit boundaries, **not approved connector selections or customer wiring assignments**. There is no direct host/ESP GPIO connection.

R1=100 kohm biases F_PGOOD from protected 24 V and R2=10 kohm returns it to FIELD_GND. The [entry eFuse PGOOD](https://www.ti.com/lit/ds/symlink/tps2663.pdf) sinks the node during its powered ramp; after entry power is ready, the divided input enables the buck. This breaks the former circular dependency on an already-existing 5 V rail.

**Remove the entry's former R29 pull-up to FIELD_5V completely.** A parallel path or fitted/DNP option is not part of this proposal. Root owns the coordinated entry revision; the frozen snapshot intentionally retains the older circuit. Keep the separate F_FAULT_N pull-up separate. Once integrated, re-export and review the whole entry/buck netlist: this standalone checker cannot attest that another sheet removed R29.

The enable divider gives a calculated 1.576-2.830 V across local 18-30 V inputs, compared with the buck's 1.36 V maximum turn-on threshold. The calculation includes multiplicative resistor tolerance and TCR corners over +/-100 K and a stated leakage assumption. At an illustrative 60 V stress screen, the asserted entry sink keeps enable below 0.079 V; its current stays below 0.604 mA and R1 below 36.7 mW. These screens do not qualify surge energy or establish a 60 V product rating.

## Power and passive budget

| Item | Provisional selection / scope |
|---|---|
| U1 | LMR36506R5RPER, RPE0009A 2x2 mm; exact land pattern still required |
| L1 | [LPS6235-223MRC](https://www.coilcraft.com/en-us/products/power/shielded-inductors/ferrite-drum/lps/lps6235/lps6235-223/), 22 uH +/-20%, 1.6 A at 10% L reduction under the manufacturer's 25 C test; temperature/fault review open |
| C1-C4 | 4 x 2.2 uF / 100 V X7S, CGA5L3X7S2A225K160AB; effective-capacitance floor not yet demonstrated |
| C5 | 100 nF / 100 V input bypass, GRM188R72A104KA35D |
| C6 / C10 | 100 nF / 16 V, GCM155R71C104KA55D; bootstrap / output bypass respectively |
| C7 | 1 uF / 16 V VCC bypass, 885012206052; no external VCC load |
| C8-C9 | 2 x 22 uF / 10 V, GCM31CR71A226KE02L; output-bias/aging verification remains open |
| R1/R4, R2/R3 | 100 kohm and 10 kohm CRCW0603, respectively; +/-1%, 100 ppm/K; R4 is a weak bleed, R3 pulls up buck diagnostic only |

There are 16 proposed physical components plus two boundary symbols. All have exact provisional MPNs except the boundaries; none is qualified. U1 and L1 deliberately have no assigned footprint until their custom land patterns are checked. No price or procurement availability is asserted.

The 100 mA external load plus worst static PG pull-up/bleed loading screens at 0.518 W output. At an explicitly assumed 70% efficiency it requires about 0.740 W input, or 41.2 mA at 18 V, plus up to 0.279 mA in the enable divider. This is a budgeting assumption, not an efficiency specification. The IC's 0.6 A rating does not authorize a higher product rail budget.

Maximum local input capacitance under positive initial/temperature tolerances is about 11.94 uF, adding about 7.27 mA at the frozen entry's maximum ramp. Maximum local output capacitance is about 55.79 uF; a linear equivalent soft-start estimate gives 132.6 mA capacitor charging current. Neither is a switch-current peak proof. Downstream capacitors/load startup remain to be added to the entry and rail budgets.

The ideal CCM ripple screen is 0.128-0.261 A peak-to-peak. At the intended small load this variant can operate in PFM/DCM, so this is an inductor sizing check, not a predicted measured waveform or ripple specification.

## Fault boundaries and release gates

| Condition | Circuit behavior / unresolved requirement |
|---|---|
| Normal cold startup | Powered entry PGOOD holds buck off until entry is ready. The approximately 4.3 A field output loads must remain held off through entry ramp and buck startup; their actual driver/inhibit circuit remains required. |
| Entry PGOOD wire open or stuck released | Divider can enable the buck before entry ramp completion. This is not a fail-off interlock; place this interface internally, and diagnose/test the fault. The supply cannot grant machine permission. |
| Entry loses supply while protected OUT remains charged | Unpowered PGOOD state is not guaranteed; a retained rail can allow restart. No claim of latched shutdown, monotonic collapse or autonomous safe rearm is made. |
| Buck PGOOD at very low VIN | Treat as unknown below its specified valid-input range. Output pull-up collapse is not an isolated health indication. A host-facing status interface still needs its own qualification. |
| Input reversed or driven negative | Buck's negative limit is -0.3 V; the entry clamp/reverse-protection system still needs waveform and retained-energy validation. This block adds no reverse-input protection. |
| FIELD_5V externally powered / retained while VIN falls | Reverse-current paths and output prebias are not qualified. No external source connection is authorized. |
| Output short, thermal event or rail restoration | IC internal protection does not constitute a machine stop or certified safety function. Any automatic recovery must leave output drivers inhibited and motion permission invalid until the separate permission system explicitly rearms. |
| Switch fault raising output | This block lacks a separate output overvoltage cutoff; evaluate hazard allocation and protection for downstream field logic. |

Before PCB release: close EN leakage over the actual divider range and resistor long-term drift; resolve the entry's 18 V versus proposed 19 V startup envelope; prove input/output effective capacitance at bias/temperature/age; confirm fixed-5 V light-load accuracy and ripple satisfy 4.85-5.15 V; complete exact footprints, layout/return loops, thermal and EMC design; total all downstream capacitance/startup loads; verify independent driver holdoff and isolated status; test shorts, brownouts, repeated ramp, power sequencing and retained-energy faults. R4's ideal discharge estimate is roughly 9.3 seconds to 1 V with no external source; **there is no guaranteed safe-off time**.

The input-cap application paragraph in TI Rev C contains a different device name and a 4.7 uF statement while its table lists 2.2 uF. This study conservatively requires at least 4.7 uF effective input capacitance, explicitly unverified. It also avoids claiming the fixed-5 V PFM accuracy from a table entry labelled FPWM. Source ambiguities are qualification gates.

Reproduce the checked circuit with `python tools/hardware_build_field_power.py`, export KiCad XML/ERC/PDF using KiCad 10.0.4, then run `python tools/hardware_validate_field_power.py --write` and `python -m unittest discover -s tests -p test_field_power.py -v`. Regeneration invalidates artifact hashes until exports and manifest are refreshed. No full-board schematic, layout, DRC, Gerbers, CPL or manufacturing release is produced here.
