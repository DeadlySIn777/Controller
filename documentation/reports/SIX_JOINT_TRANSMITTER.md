# Six-joint differential transmitter schematic block

28 September 2026. The complete baseline transmitter allocation is now drawn as an editable KiCad circuit: three AM26C31IPWR devices, twelve differential STEP/DIR channels, their input defaults and supply bypass, and all 24 proposed JTX0/JTX1/JTX2 positions. This completes the transmitter **block**, not the controller schematic, physical permission system or board.

Open the [schematic](../WORKSPACE_REFERENCES.md#artifact-6d14e83e89cbf495), [project](../WORKSPACE_REFERENCES.md#artifact-d81e759d7ed8a1da), [PDF](../WORKSPACE_REFERENCES.md#artifact-7c49c8c359ed449c) or [rendered overview](../WORKSPACE_REFERENCES.md#artifact-8c79c386507e64f9). The [netlist](../WORKSPACE_REFERENCES.md#artifact-b3b70f98f61d2ae2), [circuit BOM](../WORKSPACE_REFERENCES.md#artifact-737ede931573ebe1), [channel/pin map](../WORKSPACE_REFERENCES.md#artifact-3030faeb26bca2c0), [ERC](../WORKSPACE_REFERENCES.md#artifact-97378bae077b90ce) and [source/evidence hashes](../WORKSPACE_REFERENCES.md#artifact-b9cae69e444b6380) accompany it.

The earlier two-joint `hardware/tx_bank` project, all its exported evidence and its generator are retained unchanged. Their ten source/artifact hashes were checked against the previous hardware review manifest and match. This new project does not overwrite or relabel that evidence.

## Implementation and exact mapping

U1/U2/U3 correspond to ledger TX0/TX1/TX2. Each device's channels 1/2/3/4 carry STEP/DIR for its first joint followed by STEP/DIR for its second joint. The PW16 input pins are 1/7/9/15; corresponding positive output pins are 2/6/10/14 and negative pins are 3/5/11/13. Pin 4 is active-high G, pin 12 active-low /G, pin 16 VCC and pin 8 ground. The selected driver ordering code is **AM26C31IPWR**, PW16 TSSOP; the nominal library footprint is `Package_SO:TSSOP-16_4.4x5mm_P0.65mm`. Package land pattern/manufacturing review still precedes board release. [TI AM26C31 Rev. P, Figure 4-1 and ordering/package information](https://www.ti.com/lit/ds/symlink/am26c31.pdf)

Each JTX connector follows the existing ledger exactly: positions 1/2 first STEP +/−, 3/4 first DIR +/−, 5/6 second STEP +/−, and 7/8 second DIR +/−. JTX0 serves joints 0/1, JTX1 joints 2/3, JTX2 joints 4/5. Their exact connector MPNs and footprints remain unselected.

`JLOGIC1` is a 16-position **review boundary**, not an assigned physical FPGA connector: 1 SIGNAL_5V, 2 LOGIC_GND, 3 TX_PERMIT, 4–15 the twelve STEP/DIR logic nets, and 16 LOGIC_GND. `JREF1.1/.2/.3` are review boundaries mapping to the existing ledger JPOWER.5/.6/.7 (`TX0_REFERENCE`, `TX1_REFERENCE`, `TX2_REFERENCE`), each bonded to LOGIC_GND. They are not three newly selected final connectors. The diagram does not silently use a differential conductor as the reference return.

## Defaults and support components

All three /G pins connect to SIGNAL_5V; all G pins connect to TX_PERMIT. Three 10 kΩ pulldowns—one per bank—hold that shared request low if its upstream source is high impedance. Twelve 10 kΩ data pulldowns and twelve provisional 33 Ω input-series resistors preserve the original design pattern. The shared permission source sees the three enable pulldowns in parallel (nominally 3.33 kΩ, approximately 0.99 mA at 3.3 V), before other loads; its actual drive capability remains to be reviewed.

The device needs a 4.5–5.5 V supply and accepts high logic at ≥2 V and low at ≤0.8 V, permitting a suitably specified 3.3 V logic source. Each bank has 100 nF bypass plus a provisional 1 µF local bulk capacitor. TI requires the 100 nF bypass close to the supply pins. With G low and /G high, outputs are high impedance. [TI AM26C31 Rev. P, Sections 5.3, 7.4 and 8.3](https://www.ti.com/lit/ds/symlink/am26c31.pdf)

High impedance does not establish STEP-low at an arbitrary receiver. The separate machine drive inhibit, remote fail-safe/bias, common-mode limits and partial-power behavior remain required. There are no 5 V pull-ups on FPGA-connected nets; the drawing explicitly forbids driving an unpowered transmitter. The actual sequencer, backfeed prevention, source driver and hardware permission latch are absent. Resistor/capacitor MPNs and approved substitutions remain open; 33 Ω is a damping provision awaiting layout/SI review, not a measured optimum.

## Actual checks

- **KiCad 10.0.4 ERC:** zero violations, including warning/exclusion severities; default ignored checks are retained in the JSON report, without custom project suppressions. The external supply flags declare supplied boundary nets; they do not implement a power supply.
- **Exported netlist validation:** exact node sets for 51 nets, 12 independent signal paths, three driver PW16 maps, all 24 output positions, supply/default networks and reference returns match the separate electrical ledger. Extra shorts or duplicate pin membership fail review.
- **Eight host fault-injection tests:** passed. Mutations cover polarity reversal, final-bank enable bypass, missing data/default/bypass components, wrong package/default value, added short, lost reference and a changed/expanded ledger allocation.
- **Visual inspection:** the actual exported PDF was rendered and inspected. All three banks, boundary labels and notes fit the A2 sheet; a floating-point placement issue producing diagonal supply stubs was corrected before the final export. This is readability/connectivity evidence, not layout review.

Reproduce the source, netlist review and tests:

```powershell
python tools/hardware_build_tx_six.py
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist --format kicadxml --output hardware/tx_six/netlist.xml hardware/tx_six/tx_six.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc --format json --severity-all --exit-code-violations --output hardware/tx_six/erc.json hardware/tx_six/tx_six.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export pdf --output hardware/tx_six/tx_six.pdf hardware/tx_six/tx_six.kicad_sch
python tools/hardware_validate_tx_six.py
python -m unittest discover -s tests -p test_tx_six.py -v
```

Regeneration replaces only the new generated block's source files; preserve manual edits before running it. After source changes, regenerate all derivative exports and the evidence manifest together. No PCB, Gerbers, centroid data, target timing/power simulation, measured loaded-cable performance or electrical/EMC qualification is supplied. The expanded eight-motor candidate does not inherit this six-joint result.
