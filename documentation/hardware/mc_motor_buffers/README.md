# Motion-card motor and TX isolation circuitry

30 September 2026, `mc-motor-buffers-r0.1`. This is a native KiCad source block for **eight standard motor channels plus four expansion channels**, each with STEP, DIR and individual active-low enable. It also buffers the two motor-bank TX permits. It contains 38 outgoing paths and 124 physical component candidates. It is ready for source integration and review; it is not a complete motion card or a manufacturing release.

The source is [mc_motor_buffers.kicad_sch](../../WORKSPACE_REFERENCES.md#artifact-00df98cb162b521c), with its [native PDF](../../WORKSPACE_REFERENCES.md#artifact-a9f06cc73cd7fa5e), [exported physical netlist](../../WORKSPACE_REFERENCES.md#artifact-f7abfdd74f91b53d), [BOM](../../WORKSPACE_REFERENCES.md#artifact-a01f7fa03723d627), [design ledger](../../WORKSPACE_REFERENCES.md#artifact-8fd76039a7fe4bb3) and [independent validation](../../WORKSPACE_REFERENCES.md#artifact-af9d9d0bc50ad595). B1–B4 are internal logical boundary symbols excluded from BOM and board; they are **not** selected backplane connectors or assigned HB160 contacts. No PCB, routing, fabrication outputs or device bitstream is supplied here.

## Integration ports and physical ownership

| Direction at this block | Exact names | Purpose |
|---|---|---|
| Power/reference input | `IO_3V3`, `LOGIC_GND` | Shared MC local 3.3 V rail, required 3.14–3.465 V operating range |
| FPGA input to buffer | `STEPi_FPGA`, `DIRi_FPGA`, `ENi_N_FPGA`, i = 0…11 | Distinct physical motor inputs; map existing reserved drive-enable GPIO aliases in the parent |
| Permission input | `TX_PERMIT` | Common physical input to the two independently buffered TX paths |
| Positive output-enable input | `BANK_B_BUFFER_ENABLE_QUALIFIED` | Actual shared copper to all 13 used bank-B OE pins and, in the parent, OPI_BOE clear/observation |
| Bank-A output to MIA | `STEPi_TO_MIA`, `DIRi_TO_MIA`, `ENi_N_TO_MIA`, i = 0…7 | Eight standard motors |
| Bank-B output to MX4 | `STEPi_TO_MX4`, `DIRi_TO_MX4`, `ENi_N_TO_MX4`, i = 8…11 | Four expansion motors |
| TX output to receiving card | `TX_PERMIT_A_TO_MIA`, `TX_PERMIT_B_TO_MX4` | Bank A always active while MC rail is live; bank B physically qualified by its positive OE |

The parent must use `BANK_B_BUFFER_ENABLE_QUALIFIED` itself for the OPI_BOE clear function. An additional software-request alias or replica of this signal does not prove observation of the actual gate. Upstream qualification, latches, inhibit generation, watchdogs and receiver circuits are outside this block.

## Selected circuit candidates

U1–U4 are **SN74LVC244APWR**, TSSOP-20, with both active-low OE pins connected to ground. They serve the 24 standard motor paths and TX_PERMIT_A, with all unused inputs grounded and unused outputs explicitly unconnected. U5–U11 are **SN74LVC2G126DCUR**, VSSOP-8, with the 13 used positive-OE pins connected to the shared qualified bank-B copper; the last unused channel has its input and OE grounded and its output unconnected. Both parts specify partial-power-down Ioff behavior. The selected dual part has positive OE; SN74LVC126A must not be substituted without an independently qualified Ioff solution. Physical package functions are extracted independently from retained TI pin tables and compared with the native export. [TI SN74LVC244A](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf), [TI SN74LVC2G126](https://www.ti.com/lit/ds/symlink/sn74lvc2g126.pdf).

Every buffer output has a **33 Ω, 1% source-series candidate**; its final value requires routed interconnect/load and edge qualification. Every motor input has a **4.7 kΩ, 1%** default: STEP/DIR to ground, EN_N to local 3.3 V. TX_PERMIT and the qualified BOE have their own 4.7 kΩ pulldowns. These are intentionally stronger than the frozen 100 kΩ input-pull study because the T20 reset/configuration GPIO weak pull-up is as low as 27 kΩ. They are a versioned implementation proposal, without editing frozen IS-1. Twenty-four outgoing STEP/DIR and both outgoing TX nets have local **10 kΩ, 1% pulldowns**. Eleven **100 nF X7R** capacitors provide one explicit local bypass candidate per buffer IC; close placement remains a layout requirement. [Efinix T20 datasheet, Tables 75 and 129](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf).

**There is no outgoing EN_N pull-up to the motion card's rail.** Each receiving MIA/MX4 enable input requires its own 10 kΩ, 1% pull-up to its independently powered 3.3 V rail. Biasing this outgoing signal from a dead MC rail could pull the receiver toward LOW and defeat the intended disabled state. MC power loss only establishes the required high impedance when the buffer rail is held at the Ioff specified 0 V; receiver HIGH/disabled also depends on the receiving-card bias, rail and leakage contract. None of those receiving circuits is drawn or declared qualified here. The static screen uses SN74LVC07A receiving-input leakage for EN_N and AM26C31I receiving-input leakage for STEP/DIR. Opposite partial-power states, rail ramps and shared-ground disturbances remain open. [TI SN74LVC07A](https://www.ti.com/lit/ds/symlink/sn74lvc07a.pdf), [TI AM26C31](https://www.ti.com/lit/ds/symlink/am26c31.pdf).

## Checked evidence and limits

The [receipt](../../WORKSPACE_REFERENCES.md#artifact-21137226444b6139) records hashes of the checked source, primary evidence and native exports. The scoped suite passes **34 tests**. Native KiCad 10.0.4 ERC reports **zero violations** with errors and warnings included. The independent validator passes **1,840 checks**, including **342 ideal digital checks** traced through actual physical A/Y/OE, package-power and series-resistor nets. It imports no generator and does not trust declared path metadata. Mutations cover OE bypass/polarity, channel swaps, series bypass, wrong rails, incompatible parts/packages, dangerous enable bias, missing decoupling, DNP, altered manufacturer/native pin functions, electrical types, stale native conductors and ERC suppression. The exported PDF was rendered and representative bank-A, bank-B and passive sections visually inspected; label/property overlaps were repaired before this receipt.

The static DC screening uses the explicitly declared rail/pull/leakage assumptions in [validation.json](../../WORKSPACE_REFERENCES.md#artifact-af9d9d0bc50ad595):

| Inactive condition | Screened voltage | Required logic threshold used |
|---|---:|---:|
| T20 tri-state plus worst weak pull-up, STEP/DIR | ≤0.6393 V | LOW ≤0.8 V |
| T20 tri-state plus worst weak pulldown, EN_N | ≥2.5880 V | HIGH ≥2.0 V |
| Qualified BOE floating with declared 13-OE/OPI/FPGA fanout | ≤0.3798 V | LOW ≤0.8 V |
| MC off, powered receiver EN_N, bank A / bank B | ≥2.8875 / 2.9885 V | HIGH ≥2.0 V |
| MC off, STEP/DIR bank A / bank B receiver | ≤0.2121 / 0.1111 V | LOW ≤0.8 V |

These are static divider/leakage calculations, not measured voltage, propagation time or power-sequence qualification. TI244A full 125°C limits use 20 µA leakage, rather than its lower 85°C limits. The declared powered receiver rail and 10 kΩ ±1% pull are assumptions to close on those cards.

The conservative single motor GPIO pull/weak-pull/input-leak screen is **0.8931 mA**; common TX fanout is **0.8981 mA** and the qualified BOE driver's declared load is **0.8247 mA**. Summing the 36 individual motor input screens gives **32.149 mA**, not a total MC rail budget. Each fitted outgoing pulldown loads a HIGH by up to 0.350 mA; with the required receiving STEP/DIR pulldown the screen is 0.701 mA including AM26C31I leakage. EN_N actively LOW must sink the receiving pull-up, up to 0.355 mA including receiving-input leakage. These currents must be retained in the integrated power and GPIO review.

The eleven ICs' rail-input-condition quiescent current sums to **0.230 mA**, excluding resistor loads, dynamic switching and additional CMOS input current. This is **not** a complete buffer power bound: TI244A specifies up to 5 mA additional current for one input at VCC−0.6 V at 125°C. Intermediate valid logic voltage and startup transitions require further power/thermal qualification. Efinix's cited GPIO drive table is at nominal voltage and 25°C; loaded drive over the supported thermal range is still unqualified. TI244A's 125°C loaded VOL guarantee plus series drop also does not establish complete receiver LOW margin. Loaded waveform, receiver fanout, rise/fall rates, thermal and partial-power measurements remain necessary.

## Reproduce the bounded checks

Run from the repository root, with KiCad 10 available:

```powershell
python tools/hardware_build_mc_motor_buffers.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml --output hardware/mc_motor_buffers/netlist.xml hardware/mc_motor_buffers/mc_motor_buffers.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --output hardware/mc_motor_buffers/erc.json hardware/mc_motor_buffers/mc_motor_buffers.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export pdf --output hardware/mc_motor_buffers/mc_motor_buffers.pdf hardware/mc_motor_buffers/mc_motor_buffers.kicad_sch
python tools/hardware_validate_mc_motor_buffers.py --output hardware/mc_motor_buffers/validation.json
python -m unittest discover -s tests -p test_mc_motor_buffers.py -v
```

A changed source needs fresh native exports and a new immutable integration receipt. Passing these checks does not close PCB DRC, FPGA bank/device fit, loaded target timing, full motion-card Ioff, motor alarms, receivers, contact mapping, hardware fault response or manufacture readiness.
