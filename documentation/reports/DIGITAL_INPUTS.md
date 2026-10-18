# Baseline 22-channel digital-input circuit — review r0.1

The full baseline input bank is now drawn: **11 ISO1212DBQR devices / 22 sinking inputs**, preserving every frozen ledger ID, logic net and JDI terminal. Six home inputs plus the existing 16 auxiliary assignments remain separate from the expanded eight-motor candidate. No shared ledger, earlier power circuit or FPGA implementation was modified.

The circuit targets the ledger's **0-30 V DC PNP-source or dry-contact-to-positive interface**, with low at or below 5 V and high at or above 15 V. It supplies neither NPN mode nor AC/universal-voltage acceptance. The [TI input topology](https://www.ti.com/lit/ds/symlink/iso1212.pdf) needs no field-side supply: the external sensor/contact source supplies input current, while IO_3V3 powers the isolated logic outputs. FIELD_GND is common to all inputs and stays distinct from LOGIC_GND.

## Actual artifacts and checks

- [Editable KiCad schematic](../WORKSPACE_REFERENCES.md#artifact-eb16fcc8e3fdcf6d), [project](../WORKSPACE_REFERENCES.md#artifact-6ff145d17b3a29b2), [PDF](../WORKSPACE_REFERENCES.md#artifact-1d46fbe99387e2b8) and local symbol library.
- [Exported netlist](../WORKSPACE_REFERENCES.md#artifact-fcc243af237e4902), [BOM](../WORKSPACE_REFERENCES.md#artifact-f6e524f7a9568d18), [ERC](../WORKSPACE_REFERENCES.md#artifact-2cdaf1513b6a726b), [expected warnings](../WORKSPACE_REFERENCES.md#artifact-e703754673df3c39).
- [Circuit/channel model](../WORKSPACE_REFERENCES.md#artifact-2451160b7f18ddb2), frozen ledger, [analytical checks](../WORKSPACE_REFERENCES.md#artifact-823d903d7066cc6c), [source notes/hashes](../research/digital-inputs/SOURCE_NOTES.md) and [artifact manifest](../WORKSPACE_REFERENCES.md#artifact-3a9be2f97cdb0da4).

**KiCad 10.0.4: zero errors, 22 retained warnings.** Each warning is a named one-pin substrate net. TI requires each SUB pin to remain on a separate floating copper island; joining or grounding them to silence ERC would change the circuit incorrectly. The validator allows only the exact 22 warning IDs, labels and severities. It rejects extra warnings, omitted expected warnings, errors and broad suppression. The ordinary `--exit-code-violations` ERC command therefore returns a violation status; this is not an ERC-zero design.

**26 Python tests pass.** They check the actual exported netlist and inject terminal changes, wrong input/ground/NC/SUB pins, role swaps, resistor bypasses, changed probe capacitance, inadequate ratings, malformed values, source tampering and ERC alterations. The rendered whole sheet, a detailed channel pair and terminal area were visually inspected. These are host tests and circuit-source/ERC evidence, not SPICE, DRC, physical signals or isolation/EMC qualification.

## Preserved channel map

| IDs | Existing function / logic net | Field terminals |
|---|---|---|
| DI00-DI05 | HOME0_FPGA through HOME5_FPGA | JDI0.1-.6 |
| DI06 / DI07 | PROBE_FPGA / TOOLSETTER_FPGA | JDI0.7 / .8 |
| DI08 / DI09 | DOOR_STATUS_FPGA / PROTECTIVE_STATUS_FPGA | JDI1.1 / .2 |
| DI10 / DI11 | SPINDLE_FAULT_FPGA / SPINDLE_READY_FPGA | JDI1.3 / .4 |
| DI12 / DI13 | FEED_HOLD_FPGA / CYCLE_START_FPGA | JDI1.5 / .6 |
| DI14 / DI15 | LUBE_STATUS_FPGA / SPARE_FPGA | JDI1.7 / .8 |
| DI16-DI21 | ALM0_FPGA through ALM5_FPGA | JDI2.1-.6 |
| Shared return | FIELD_GND | JDI2.7 / .8 |

JDI0 and JDI1 have no return pin of their own in the frozen ledger; the return allocation remains JDI2.7/.8. No sensor-positive distribution is supplied by this sheet. JLOG1/JLOG2 are internal logic boundaries, not new user terminal assignments. None of these boundary symbols specifies an approved physical connector, wire or mating plug.

## Circuit and electrical screens

Every field path is terminal → **1 kohm threshold/pulse resistor** → SENSE node. A **562 ohm sense resistor** connects that node to IN, and **10 nF / 100 V C0G** returns SENSE to FIELD_GND. Each device has 100 nF / 25 V logic bypass. EN ties directly to IO_3V3. Each logic output has 100 kohm pull-down bias.

The threshold and sense resistors use exact parts from the [TI EVM BOM](https://www.ti.com/lit/ug/sllu254/sllu254.pdf): SMM02040C1001FB300 and CRCW0603562RFKEA. The [TDK filter](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012C0G2A103J125AA) is C2012C0G2A103J125AA. The bias part is CRCW0603100KFKEA; logic bypass is 06033C104JAT2A. All are provisional fitted candidates, with lifecycle, sourcing and final footprint review still required.

| Quantity | Source limit or calculated screen | Meaning |
|---|---:|---|
| Published falling threshold at nominal 1kohm/562ohm | 8.7 V minimum, 9.2 V typical | Not a complete external-resistor lifetime tolerance result |
| Published rising threshold at those values | 10.4 V typical, 10.95 V maximum | Distinct from the product's wider 15 V high target |
| Active current, stated source conditions | 2.05-2.75 mA | The smaller headline typical range is not used as a guaranteed bound |
| Added external-resistor TCR current screen | 2.030-2.778 mA | Engineering extension over +/-100 K, not a new manufacturer guarantee |
| Conservative rising / intrinsic falling screen | 11.370 V maximum / 6.5 V minimum | Shows margin to the 15 V / 5 V targets under the stated comparator assumptions |
| Threshold / sense resistor DC dissipation | 7.84 / 4.43 mW maximum | Pulse requirements remain separate from steady dissipation |
| 30 V filter-step resistor/energy screen | 0.914 W initial / 4.74 uJ | Requires pulse-curve and actual-waveform review; not an IEC surge rating |
| RTHR × CIN corner range | 9.33-10.69 us | Filter time constant only, not total input latency |
| All inputs high at 30 V | Up to 61.2 mA / 1.834 W field-input screen | From the external sources; thermal and upstream sensor-power budgeting required |
| IO_3V3 static load screen | Up to 21.7 mA | Eleven IC quiescent maxima plus output-bias current; dynamic load omitted |
| Logic output levels at the rail envelope | High at least 2.8 V / low at most 0.4 V under source test assumptions | Exact FPGA I/O bank/threshold, loading and sequencing still require review |

The calculations deliberately separate data-sheet conditions, added assumptions and measured qualification. They do not establish a newly guaranteed input range. Full probe/home delay includes source impedance, cable capacitance, nonlinear input current, isolator propagation, FPGA synchronization/filtering and latch behavior. The IC's nanosecond propagation figures cannot be advertised as the filtered channel delay.

The BOM has **110 proposed fitted parts** plus five boundary symbols: 11 ICs, 22 threshold resistors, 22 sense resistors, 22 filter capacitors, 11 bypass capacitors and 22 output-bias resistors. The bias resistors are additions to the earlier support allowance and need pricing. There is no added per-input digital isolator and no FIELD_5V load from ISO1212. If controller field power supplies the external contacts/sensors, its budget must include these input currents and sensor quiescent loads; do not silently place them inside the existing 60 mA field-control reservation or count them twice.

## Defaults, faults and isolation

With valid IO_3V3 and EN high, an open input reads low. **During unpowered or brownout conditions the device's output is undetermined.** The 100 kohm pull-down is a weak bias and does not override that specification. All inputs must remain invalid until independent rail/reset readiness is established; machine-required status loss must trigger the profile's reviewed hold/inhibit response. That masking and the 22-channel FPGA path are not implemented by this schematic.

| Fault or boundary | Consequence / required qualification |
|---|---|
| Wire open, source lost or short to FIELD_GND | Typically looks like an inactive low; this bank has no wire-break diagnostic or test pulse. A profile's NC/NO polarity cannot turn this into a certified safety input. |
| Short to field positive or output stuck high | Can appear continuously active. Required plausibility, reset checks or independent protection remain outside this circuit. |
| Shared field return opens | Multiple inputs may float or cross-couple through external equipment; do not assume all become low. |
| RTHR shorts, CIN opens or sensor leakage rises | Threshold/filter/EMC assumptions change. Confirm contact wetting, PNP off-leakage, two-wire sensor compatibility and cable impedance for each profile. |
| Logic rail ramps or fails | Outputs and FPGA sampling can be invalid. Do not infer healthy door, probe, protective or service status from a forced software default. |
| Cycle-start asserted at startup/reconnect | Raw level is insufficient command authority. Require deliberate fresh intent through the existing stopped/armed policy. |
| Negative input / overvoltage | The component's reverse tolerance is not a system port rating. This design's proposed operating range remains 0-30 V DC; reverse/surge qualification is open. |

All 22 field returns are common, so the product cannot claim channel-to-channel isolation. Keep **each SUB1/SUB2 as its own approximately 2x2 mm floating copper island**: 22 separate nets, no connection to another substrate, signal, FIELD_GND, LOGIC_GND or PE. These are layout copper features rather than fitted BOM items. Device/package isolation ratings do not establish PCB creepage, connector spacing, environmental category or finished-product safety certification.

No PE capacitor or TVS is silently added. TI's reference surge topology depends on tightly bounded total field-ground coupling to other potentials, including PE. The complete controller's other isolators, supplies, shielding, machine grounding and external cables have not been assessed against that condition. The resistor/filter choice therefore does **not** inherit the manufacturer's demonstrated reference-board EMC levels. Required changes must be qualified and costed at system level.

## Before integration and board release

1. Retain the exact JDI map; review common-return access, connector ratings/keying and sensor-positive distribution in the combined design.
2. Review package land patterns and 22 independent SUB islands, isolation keep-outs, mixed-domain routing and input resistor/cap placement. The selected standard footprints are candidates, not approved finished layout.
3. Complete rail-valid input masking, the FPGA sampling/latching path and HAL/configuration capability binding. Current motion RTL cannot gain 22 working inputs from a schematic change.
4. Measure static thresholds/current and leakage compatibility across voltage/temperature; account for resistor life drift and all sources/cables. Qualify probe/toolsetter/home latency and repeatability at actual machine approach speeds.
5. Verify all-high thermal behavior, reverse/overvoltage/ESD/EFT/surge and grounding faults on the assembled system. Determine whether further clamping or filtering is needed without making fast-input claims prematurely.
6. Add the new fitted support costs and actual external-sensor power budget. No procurement or PCBWay quote is claimed.

Reproduce with `python tools/hardware_build_digital_inputs.py`, KiCad netlist/ERC/PDF export, `python tools/hardware_validate_digital_inputs.py --write`, and `python -m unittest discover -s tests -p test_digital_inputs.py -v`. Preserve the 22 expected ERC warnings. Exports and hashes must be refreshed after edits. No PCB, DRC, fabrication data or physical qualification is produced by these checks.
