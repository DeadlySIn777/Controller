# Core and field power-entry circuits

Revision r0.2, 28 September 2026. Two editable KiCad input circuits now implement the proposed physical-fuse/eFuse arrangement, with separate logic and field returns. They contain actual component connections, reverse-blocking FETs, voltage/current setting networks and local diagnostic boundaries. **This is a partial circuit, not a complete or qualified power system.** Physical fuse and output-clamp selections remain open.

Artifacts: [editable schematic](../hardware/power_entry/power_entry.kicad_sch), [project](../hardware/power_entry/power_entry.kicad_pro), [PDF](../hardware/power_entry/power_entry.pdf), [rendered sheet](../hardware/power_entry/preview.png), [IC detail](../hardware/power_entry/detail.png), [netlist](../hardware/power_entry/netlist.xml), [BOM](../hardware/power_entry/bom.csv), [requirements](../hardware/power_entry/requirements.json), [ERC](../hardware/power_entry/erc.json), [validation and source hashes](../hardware/power_entry/validation.json).

## Implemented connections

Each entry passes through a physical-fuse position to a local RAW net. A bidirectional SMCJ30CA candidate and ceramic bypass connect RAW to that domain's return. A CSD19537Q3 blocking FET then feeds TPS26630RGER, whose output supplies the downstream converter/load boundary. BSS138P,215 provides the RAW-referenced gate pulldown. The two columns use LOGIC_GND and FIELD_GND respectively; neither diagnostic pullups nor reset contacts bridge those domains.

The circuit uses the manufacturer's RGE24 pin map and a matching KiCad RGE0024H footprint. All IN, OUT and exposed-ground-pad contacts are connected. The NexFET footprint combines physical drain contacts 5–8 and the drain land into KiCad pad 5; this is deliberate, not missing copper connections. The symbol gives one shared OUT contact the power-output type and the other the passive type because they are one internal node. The first ERC export that treated both contacts as separate power sources is preserved under `hardware/power_entry/attempts`.

MODE stays open. SHDN uses its internal pullup and a normally open, local dry-contact boundary for shutdown/reset, avoiding an assumption that an unpowered host GPIO can start its own supply. Opening the contact can restore power. Voltage recovery and power cycling can also restore the supply; **this contact and MODE choice do not implement machine restart permission or an E-stop circuit**.

FLT retains a local 10 kΩ pullup; IMON has 10 kΩ to local ground and no bypass capacitor. Core fault diagnostics use IO_3V3 and field diagnostics FIELD_5V. **PGOOD pullups R9/R29 were removed.** The connected core and field buck circuits now use protected-input-powered 100 kΩ / 10 kΩ enable dividers. Their PGOOD/EN nodes are analog controls, not direct GPIO inputs. This removes the circular startup dependency and the divider path that would backfeed an unpowered downstream rail. Partial-power behavior still needs qualification. Field diagnostic isolation remains unfinished.

## Calculated operating constraints

The [independent calculator](../tools/power_entry_analysis.py) reads the current requirements and electrical ledger. It recomputes voltage corners rather than trusting stored results, and distinguishes a valid calculation from a qualified circuit. The [source review](../research/POWER_ENTRY_REVIEW.md) records primary data sheets, equations and assumption limits; the [machine-readable result](../research/power-entry/analysis.json) records exact inputs by SHA-256.

| Item | Core | Field |
|---|---:|---:|
| Existing normal input-current reservation | 1.81 A | 4.36 A |
| Proposed source/path capacity target | 3 A | 6 A |
| ILIM resistor | 7.50 kΩ | 3.65 kΩ |
| Assumed current-limit range | 2.149–2.653 A | 4.416–5.452 A |
| Margin above original ledger load at assumed low limit | 0.339 A | 0.056 A |
| Protected output at 19 V entry and assumed 0.20 Ω total path | 18.638 V | 18.128 V |

The input study is explicitly **19–30 V**, narrower than the unchanged ledger's 18–30 V. Any positive path loss makes an 18 V entry insufficient for an 18 V-minimum converter. The proposed 3 A core source also differs from the old 2 A allowance. Neither change is silently adopted as a completed controller rating. Retaining the original range requires different downstream converter/analog-supply limits and a reconciled budget.

Voltage corner analysis includes comparator extrema, both leakage polarities and a 0.5% total resistor error allowance. UV turn-on spans 17.262–18.726 V; OV trip spans 32.288–34.818 V. The lowest OV recovery threshold is about 29.907 V, so returning to exactly 30 V after a fault may leave the input off. Falling thresholds do not guarantee acceptable downstream converter voltage through a brownout.

The current ranges use an explicit ±10% screening assumption at these selected resistor values. The family ±7% headline is not a guarantee at every setting. The field margin is especially small and must be reconciled with load tolerances and startup before selection is frozen.

The 100 nF dVdT network with at most 1,000 µF effective downstream capacitance gives a model ramp of 397–609 V/s, about 49–76 ms to 30 V, and up to 0.609 A charging current. Adding already-active normal loads can exceed either assumed low current limit. The connected converter blocks now delay their enables using entry PGOOD. The older 1,000 µF entry-capacitance scenario remains a screening bound; it is not the same as the downstream 5V converter capacitance. **Field load permission and complete startup/thermal qualification remain open.** These capacitive calculations do not establish thermal safe operating area or a measured startup waveform.

## Checks completed

- KiCad 10.0.4 export: **zero ERC violations** with the standard project check configuration. The four default ignored check categories are listed in the validation JSON; no per-violation waiver was added.
- **19 connectivity/mutation tests** check the real exported circuit against an independently written contract. They cover reverse FET orientation, fuse bypass, ground/pullup crossing, reset wiring, exposed pad, MODE, clamp polarity, thresholds, wrong device variant, assembly omission, duplicate identities, lost open-drain ERC semantics and reintroduction of downstream PGOOD pullups.
- **16 calculator tests** exercise ideal analytical cases, tolerance widening, malformed/nonfinite inputs, source undersizing, ledger changes and refusal to turn assumptions into qualification.
- The r0.2 circuit contains **44 components and 48 exported nets**, of which 14 are explicit single-pin MODE/NC no-connect nets. An independent reviewer checked its integrated PGOOD/EN connections and separated returns. The earlier 46-component review belongs to the preserved r0.1 evidence archive.

The separate [encoder-power circuit](ENCODER_POWER.md) supplies two current-limited 5 V branches. Its simultaneous limit model requires a provisional 0.568 A upstream reservation rather than treating the 0.4 A normal encoder budget as a fault maximum. The current core-converter calculator includes both encoder-limit currents; it still does not establish a qualified source or measured regulator response.

## Unresolved parts and integration

Fuse symbols are intentional unselected positions, not approved ratings. Source foldback/prospective fault current, fuse/holder interruption and clearing energy, wire withstand, TVS energy and failed-short semiconductor behavior must be coordinated. No candidate fuse receives an approved BOM status from this report.

Output negative clamps, exact passives/connectors, independent machine inhibit and complete board integration remain unfinished. Core/field converters, logic supplies and encoder power are now electrically connected in the [assembly review](CONNECTED_CONTROLLER.md). Candidate capacitor package/voltage values still need effective capacitance at bias and temperature. SMCJ30CA's specified pulse clamp does not establish immunity to arbitrary surge waveforms, sustained overvoltage or negative-input/retained-output combinations. The field diagnostic boundary still requires an isolation design. The existing TPS4H160 field-output candidate has a 48V transient absolute limit; the entry TVS's 48.4V reference clamp cannot establish its protection. That interface requires a separate clamp/driver decision before release.

No PCB layout, DRC, manufacturing package or physical fault/thermal/EMC evidence is produced by these checks. Screens, motor-drive power and optional AI remain outside these core/field input budgets.

## Reproduce

```powershell
python tools/hardware_build_power_entry.py
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist --format kicadxml -o hardware/power_entry/netlist.xml hardware/power_entry/power_entry.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc --format json -o hardware/power_entry/erc.json hardware/power_entry/power_entry.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export pdf -o hardware/power_entry/power_entry.pdf hardware/power_entry/power_entry.kicad_sch
python tools/power_entry_analysis.py --report research/power-entry/analysis.json
python -m unittest discover -s tests -p 'test_power_entry*.py' -v
python tools/hardware_validate_power_entry.py
```

Rebuilding replaces this generated block; preserve manual edits first. Regenerate and visually inspect the PDF images after a drawing change, then refresh the validation manifest. Changes to the source review or ledger also invalidate the recorded identities.
