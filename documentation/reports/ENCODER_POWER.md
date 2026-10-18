# Two independent encoder power branches

28 September 2026. An actual editable KiCad block now supplies the two baseline encoder interfaces through separate **TPS2553DBVR-1** current-limited switches. It preserves the existing names `ENC0_5V_LIMITED` and `ENC1_5V_LIMITED`. It does not implement the controller's complete supply, fault-inhibit policy, PCB or a qualified protected encoder port.

Artifacts: [project](../WORKSPACE_REFERENCES.md#artifact-b8ad4b8d9f29a90b), [schematic](../WORKSPACE_REFERENCES.md#artifact-11f867d5272b6cdb), [PDF](../WORKSPACE_REFERENCES.md#artifact-7344eef7002dd93e), [rendered sheet](../WORKSPACE_REFERENCES.md#artifact-1414ada8d2d12cdc), [netlist](../WORKSPACE_REFERENCES.md#artifact-7df1120d930407e4), [BOM](../WORKSPACE_REFERENCES.md#artifact-b04a6fb6015e4836), [design envelope](../WORKSPACE_REFERENCES.md#artifact-fce9e5a6cb1e3186), [ERC](../WORKSPACE_REFERENCES.md#artifact-74dd5038d91847b5), [validation and hashes](../WORKSPACE_REFERENCES.md#artifact-462fa4b3ccac0c71).

The input is a [frozen exact ledger copy](../WORKSPACE_REFERENCES.md#artifact-bb77ecd1dbfc58ac), not the concurrently evolving main ledger. The generator never refreshes this snapshot automatically. This work does not modify the earlier transmitter, receiver or ledger files. This block feeds the receiver block's `JPWR1` boundary; it has not been merged into a complete controller schematic.

## Circuit and exact mapping

U1 supplies encoder 0 and U2 supplies encoder 1. The selected IC ordering code is **TPS2553DBVR-1**, active-high enable, DBV six-pin SOT-23. The similarly named DRV package uses different pins. [TI exact ordering page](https://www.ti.com/product/TPS2553-1/part-details/TPS2553DBVR-1)

| DBV pin | Function | U1 net | U2 net |
| --- | --- | --- | --- |
| 1 | IN | CORE_5V | CORE_5V |
| 2 | GND | LOGIC_GND | LOGIC_GND |
| 3 | EN | ENC0_POWER_EN | ENC1_POWER_EN |
| 4 | Open-drain /FAULT | ENC0_POWER_FAULT_N | ENC1_POWER_FAULT_N |
| 5 | ILIM | ENC0_ILIM | ENC1_ILIM |
| 6 | OUT | ENC0_5V_LIMITED | ENC1_5V_LIMITED |

The map follows [TI Rev. F, page 5](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf). Each ILIM has 110 kΩ, 1%, 100 ppm/K to ground. Each EN has a 10 kΩ pull-down; each /FAULT has a 10 kΩ pull-up to IO_3V3. The output has a passive 100 kΩ, 1%, 100 ppm/K bleed. Per branch, the drawing includes 100 nF plus provisional 10 µF input capacitance and 100 nF plus 1 µF output capacitance.

| Boundary | Pins in order |
| --- | --- |
| JIN1 | 1 CORE_5V; 2 LOGIC_GND; 3 IO_3V3 |
| JOUT1 | 1 ENC0_5V_LIMITED; 2 LOGIC_GND; 3 ENC1_5V_LIMITED; 4 LOGIC_GND |
| JCTRL1 | 1 ENC0_POWER_EN; 2 ENC0_POWER_FAULT_N; 3 LOGIC_GND; 4 ENC1_POWER_EN; 5 ENC1_POWER_FAULT_N; 6 LOGIC_GND |

JOUT1 maps directly to receiver `JPWR1.1–4`; downstream `JENC0/1.7` is the respective supply and `.8` its return. These are review boundary connectors, with no selected connector MPN or current rating. They are not instructions to fabricate a harness yet.

The ILIM resistor reference `CRCW0603110KFKEA` follows [Vishay document 20035](https://www.vishay.com/docs/20035/dcrcwe3.pdf). The remaining resistor and capacitor MPNs are **unselected**. Effective input capacitance must satisfy TI's 0.1 µF minimum after bias/tolerance/temperature, with close placement. The nominal capacitor values alone do not qualify that requirement. The IC footprint is nominally assigned; final land pattern, copper and assembly qualification remain open.

## Current and voltage envelope

The frozen ledger reserves **0.4 A for normal encoder loads**, split here into 200 mA per port. The current-limit calculation uses TI's equations with resistor tolerance and an additional conservative 150 K × 100 ppm/K allowance:

```text
Rmin = 110 × 0.99 × 0.985 = 107.2665 kΩ
Rmax = 110 × 1.01 × 1.015 = 112.7665 kΩ
Imin = 25230 / Rmax^1.016 = 207.444664 mA
Inom = 23950 / 110^0.977 = 242.585515 mA
Imax = 22980 / Rmin^0.94 = 283.604920 mA
```

Equations are from [TI Rev. F, Section 9.5.1](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf); results and extra resistor allowance are this design's calculations, not measurements. The 150 K allowance is a conservative calculation bound, not permission to operate beyond component ratings.

Two branches can draw **0.567210 A** at their simultaneous limited fault currents before latch action. With a provisional 140 µA switch-current reservation per branch, reserve **0.568 A rounded upward**, versus 0.4 A normal encoder load. That is neither an instantaneous peak bound nor complete upstream converter approval. The 140 µA value is conservatively borrowed from TI's 20 kΩ test condition; it is not an explicit guaranteed 110 kΩ supply-current characterization. Normal encoder load plus bleed and this reservation totals approximately **0.400388 A**. Logic pull-down/pull-up currents also require their own 3.3 V budget.

The switch does not regulate voltage. This block accepts a proposed **4.75–5.25 V CORE_5V** envelope. Using 135 mΩ gives approximately **27.01 mV switch drop and 5.403 mW loss** at 200 mA plus bleed. Therefore 4.75 V upstream does **not** guarantee 4.75 V at an encoder; cable/contact loss further reduces it. Encoders requiring 5 V ±5% need tighter upstream regulation or a different reviewed envelope. The proposal's 70°C local ambient ceiling has no physical qualification.

Near a short, the arithmetic approaches **1.489 W per switch** until protection acts. This is a transient demand, not an allowed continuous dissipation or a thermal simulation. Supply droop, cable energy, output overshoot and hot-plug/startup into encoder capacitance must be measured. The ~7.4 mA minimum-limit headroom above the 200 mA load is small; accepted encoder models must pass startup testing.

## Default, recovery and partial-power limits

The -1 device latches after overcurrent/reverse faults; EN cycling or input power cycling clears that state. **Thermal shutdown can auto-retry even on the -1 device.** Reverse current can flow before turn-off. EN operates at 0–6.5 V, with VIH 1.1 V minimum and VIL 0.66 V maximum. Pin absolute limits are −0.3 to 7 V, not operating guarantees. [TI Rev. F, Sections 7 and 9.3](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf)

This drawing uses only 0–3.6 V shared-ground control. A 10 kΩ pull-down defaults EN off **if its external driver is high impedance**; a retained high EN can energize the port on power return. There is no independent restart latch. Datasheet EN leakage suggests only millivolts across that pull-down under its specified test conditions, but does not prove an unpowered host's leakage or injection behavior. /FAULT is never a machine-permission or power-good signal. An unpowered switch, disabled output or fault pull-up that is itself absent can be misinterpreted without additional system logic.

Host/FPGA unpowered EN injection, powered FAULT pull-up into an unpowered switch, an externally powered encoder feeding OUT, IO_3V3 loss, and ground sequencing remain explicit qualification cases. Absolute maximum compliance alone does not establish functional partial-power tolerance. No blanket reverse-polarity, 24 V miswire, surge, system ESD or shorted-cable protection claim is made. A 100 kΩ passive bleed does not establish a safe discharge time for unknown external capacitance or backfeed. Fault logging, output inhibition, explicit reset policy and encoder validity checks are still required outside this block.

## Evidence and reproduction

**KiCad 10.0.4 ERC: zero violations. Twelve scoped host tests: passed.** The actual exported netlist contains 21 populated components and 11 nets. An independent validator checks every connected pin against the DBV map, the frozen ledger and the declared budget. Mutations cover bypass/merged supplies, input/output swaps, wrong IC variants, ILIM errors, floating/default-on EN, wrong FAULT voltage/port, missing ground/bypass or DNP, incorrect open-drain semantics, misleading current arithmetic, and hidden thermal/reverse/partial-power limitations.

The exported PDF was rendered and visually inspected at overview and circuit-detail scale. Notes, labels, component pins and connector mapping are clear of overlaps. This is circuit ERC/connectivity plus bounded arithmetic; there is no PCB DRC, SPICE validation, thermal measurement, physical switching test or production release. The saved ERC records KiCad's default ignored checks; no bespoke suppression was added.

```powershell
python tools/hardware_build_encoder_power.py
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist --format kicadxml --output hardware/encoder_power/netlist.xml hardware/encoder_power/encoder_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc --format json --severity-all --exit-code-violations --output hardware/encoder_power/erc.json hardware/encoder_power/encoder_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export pdf --output hardware/encoder_power/encoder_power.pdf hardware/encoder_power/encoder_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export bom --fields Reference,Value,Footprint,MPN,QUANTITY,DNP --labels Refs,Value,Footprint,MPN,Qty,DNP --output hardware/encoder_power/bom.csv hardware/encoder_power/encoder_power.kicad_sch
python -c "import fitz; d=fitz.open('hardware/encoder_power/encoder_power.pdf'); d[0].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save('hardware/encoder_power/preview.png')"
python -m unittest discover -s tests -p test_encoder_power.py -v
python tools/hardware_validate_encoder_power.py
```

Regeneration overwrites this generated block only; preserve manual edits before rebuilding and refresh dependent exports together. The validator hashes the frozen input, primary TI PDF, source, report, tests and artifact files. The whole-controller power budget and machine fault policy remain unapproved engineering work.
