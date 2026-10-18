# Baseline two-ABZ receiver schematic block

28 September 2026. Six differential receiver channels are now implemented in an editable KiCad schematic using two AM26LV32EIPWR devices. The exported circuit follows the existing baseline encoder allocation and both eight-position JENC connectors. This is a receiver **block**, not a finished protected encoder port or complete controller.

Artifacts: [schematic](../WORKSPACE_REFERENCES.md#artifact-07f777feb9780818), [project](../WORKSPACE_REFERENCES.md#artifact-b4faa56fc7cf9d83), [PDF](../WORKSPACE_REFERENCES.md#artifact-6b0fab20b5e88744), [visually inspected overview](../WORKSPACE_REFERENCES.md#artifact-b2596d9975c52580), [netlist](../WORKSPACE_REFERENCES.md#artifact-b57d4e464cd23aef), [BOM](../WORKSPACE_REFERENCES.md#artifact-2f95f3424ee99ea9), [pin mapping and termination calculation](../WORKSPACE_REFERENCES.md#artifact-8f96b72f938c03d3), [ERC](../WORKSPACE_REFERENCES.md#artifact-eac74a3509fa164c), [validation and source hashes](../WORKSPACE_REFERENCES.md#artifact-64cc8412f8e27df9). The original ledger and earlier transmitter sources/evidence are unchanged.

## Exact mapping and defaults

U1 corresponds to RX0; U2 to RX1. The ledger deliberately splits encoder 1 across the two chips:

| Signal | Receiver/channel | Positive A pin | Negative B pin | Output Y pin | JENC +/− positions |
| --- | --- | --- | --- | --- | --- |
| ENC0_A | U1 / 1 | 2 | 1 | 3 | JENC0.1 / .2 |
| ENC0_B | U1 / 2 | 6 | 7 | 5 | JENC0.3 / .4 |
| ENC0_Z | U1 / 3 | 10 | 9 | 11 | JENC0.5 / .6 |
| ENC1_A | U1 / 4 | 14 | 15 | 13 | JENC1.1 / .2 |
| ENC1_B | U2 / 1 | 2 | 1 | 3 | JENC1.3 / .4 |
| ENC1_Z | U2 / 2 | 6 | 7 | 5 | JENC1.5 / .6 |

The exact receiver ordering code is **AM26LV32EIPWR**, PW16 TSSOP. Pins 4/12 are G and /G; pin 16 is supply and pin 8 ground. Its operating supply is 3.0–3.6 V. Both enable pins connect to IO_3V3, keeping receivers enabled while the motion system is inhibited. U2's unused channels 3/4 have A tied to IO_3V3 and B to LOGIC_GND, with outputs 11/13 explicitly marked no-connect. [TI AM26LV32E Rev. E, Figure 5-1, Table 8-1 and ordering table](https://www.ti.com/lit/ds/symlink/am26lv32e.pdf)

Each receiver has 100 nF bypass plus a provisional 1 µF local capacitor. The 100 nF capacitor must be placed close to supply/ground pins in layout. TI specifies open-circuit fail-safe, and explicitly removed shorted/terminated fail-safe claims in the 2020 revision. A disconnected cable with the 120 Ω termination still fitted must therefore **not** be treated as a proven stable encoder input. [TI Rev. E, revision history, Sections 8.3/8.4 and 10](https://www.ti.com/lit/ds/symlink/am26lv32e.pdf)

That behavior matters: the present gateware counts ABZ transitions; this schematic adds no independent wire-break detector or reliable validity signal. Noise on a disconnected terminated pair could produce transitions. Software filtering and a CRC on the FPGA link do not prove the encoder cable is intact. Encoder-validity/fault handling remains a separate design requirement before machine use.

## Termination actually drawn

R1–R6 are fitted **120 Ω, 1%, 0.5 W, 1210** terminations across the six pairs at the receiver end. The reference MPN is `CRCW1210120RFKEA`, constructed from Vishay's published ordering convention. Supplier availability, assembly alternates and final land-pattern qualification are not established. The manufacturer's CRCW1210 rating is 0.5 W at 70°C, subject to the resistor/PCB thermal system and permissible film temperature. [Vishay D/CRCW e3, document 20035, technical specifications and ordering information](https://www.vishay.com/docs/20035/dcrcwe3.pdf)

Selection is an **assembly population choice**: fit the 120 Ω resistor for the reviewed terminated version, or omit it for a separately reviewed open-termination configuration. There is no bypass jumper, 0 Ω substitution or software switch. The exported schematic/BOM is the fitted version; its validator rejects silently marking the resistors DNP. The alternate open population requires regenerated evidence and cable/encoder qualification.

The new calculation replaces the earlier unselected `>=0.125 W` support allowance for this block without silently editing the historical ledger. Declared applied differential is bounded to **5.5 V** for this study. With 1% tolerance and a conservative 150 K × 100 ppm/K resistance allowance:

```text
Rmin = 120 × 0.99 × 0.985 = 117.018 Ω
Pmax = 5.5² / 117.018 = 0.258507 W per channel
Six simultaneous channels = 1.551043 W
```

The provisional local ambient limit is **70°C maximum**, with actual board/film temperatures, thermal coupling, aging and fault energy still unmeasured. That arithmetic is not a product rating. The receiver's common-mode specification cannot be interpreted as permitting 14 V continuously across these terminations; that would exceed their selected dissipation. Remote encoder drive strength and power consumption must also support the fitted load. No existing 200 mA encoder-supply reservation is certified by this calculation.

## Supply and interface boundaries

Each JENC position 7 carries its separately named `ENC0_5V_LIMITED` or `ENC1_5V_LIMITED` rail; position 8 is LOGIC_GND. `JPWR1.1/.3` supply those rails independently and `.2/.4` are returns. **The current-limiting/protection circuits are not present**: the names describe the required upstream interface, and the diagram is a pass-through boundary requiring an already protected source.

`JLOGIC1.1/.2` supply IO_3V3 and ground; positions 3–8 carry ENC0 A/B/Z then ENC1 A/B/Z to the future FPGA inputs. These review boundary connectors have no selected physical MPN. The receiver TSSOP footprint is nominally assigned; actual FPGA pins, rail sequencing and partial-power behavior remain open. The encoder interface is not galvanically isolated. The receiver's component ESD ratings do not constitute complete-port or controller EMC qualification. No speculative TVS or surge network is represented as completed protection.

## Evidence and reproduction

**KiCad 10.0.4 ERC reports zero violations**, with all severity classes requested and default ignored-check settings recorded. Exact exported node sets are checked against the independent ledger and PW16 map, including all six polarity paths, cross-chip allocation, separate supplied encoder rails, reference returns, always-enabled inputs, unused-channel ties and explicit output no-connects. The actual PDF was rendered and inspected; the unused-channel annotation was moved clear of ENC1_Z's output label before the final export.

**Ten scoped host tests passed.** Fault mutations cover input polarity, cross-chip output swaps, enable/unused-input loss, missing explicit no-connects, shorted or underpowered termination, silent DNP, merged encoder supplies, missing bypass, a false 14 V differential interpretation and overstated thermal claims/arithmetic.

```powershell
python tools/hardware_build_rx_abz.py
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist --format kicadxml --output hardware/rx_abz/netlist.xml hardware/rx_abz/rx_abz.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc --format json --severity-all --exit-code-violations --output hardware/rx_abz/erc.json hardware/rx_abz/rx_abz.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export pdf --output hardware/rx_abz/rx_abz.pdf hardware/rx_abz/rx_abz.kicad_sch
python tools/hardware_validate_rx_abz.py
python -m unittest discover -s tests -p test_rx_abz.py -v
```

Regeneration replaces only this generated block's source; preserve manual edits first and refresh all derivative exports together. No PCB/DRC, fabrication artifacts, physical measurements, target timing, encoder power limiter or port protection is complete here. The expanded four-encoder proposal remains separate.
