# Baseline low-voltage regulator implementation

28 September 2026. Three independently controlled regulators now have actual editable KiCad circuits for **CORE_1V2, IO_3V3 and ESP_3V3**, using a frozen baseline ledger. The circuit advances the physical controller design; it does not complete the FPGA power sequence, board layout or machine permission chain.

Artifacts: [project](../WORKSPACE_REFERENCES.md#artifact-db330903bc0f9335), [schematic](../WORKSPACE_REFERENCES.md#artifact-c9da8eecebf22664), [PDF](../WORKSPACE_REFERENCES.md#artifact-475d1a7e7f478186), [overview](../WORKSPACE_REFERENCES.md#artifact-fe2a2b34fc510d38), [detail](../WORKSPACE_REFERENCES.md#artifact-40a539eac0503f88), [netlist](../WORKSPACE_REFERENCES.md#artifact-df941de97f49002d), [BOM](../WORKSPACE_REFERENCES.md#artifact-dd48e4b17c527637), [calculated envelope](../WORKSPACE_REFERENCES.md#artifact-2cc33e144d234a84), [ERC](../WORKSPACE_REFERENCES.md#artifact-a31d685a718f4ae6), [validation and hashes](../WORKSPACE_REFERENCES.md#artifact-861e4c5f036feeae), [primary source index](../research/logic-power/SOURCES.md).

## Why the regulator changed

The ledger's TPS62160DSGR remains a historical candidate. Its ±3% PWM and −3.5/+4% PSM accuracy, before external divider effects, cannot substantiate the ledger's 1.17–1.23 V core window. Its typical 25 mV/µs startup also exceeds the T20's 10 V/ms limit, while PG becomes high impedance in disabled/UVLO/thermal states. [TI TPS62160 Rev. E, Sections 7.5, 8.3.3 and 8.4.1](https://www.ti.com/lit/ds/symlink/tps62160.pdf)

This block selects **TPS62901RPJR**, an active 1 A, RPJ9 converter with configurable soft start and discharge. Its fixed-voltage VSET regulation specification is ±1.25% over the full stated temperature range. A regulator substitution requires a new package, support circuit, evidence and costing; it is not a drop-in BOM edit. [TI exact ordering page](https://www.ti.com/product/TPS62901/part-details/TPS62901RPJR), [TI Rev. A, Section 5.5](https://www.ti.com/lit/ds/symlink/tps62901.pdf)

The original ledger and other circuit blocks are unchanged. The [frozen snapshot](../WORKSPACE_REFERENCES.md#artifact-454d11ee4c1794c1) remains the input; its SHA-256 must match the generated envelope. TI's ordering page showed no available inventory during this review. Exact candidate does not mean supply, price or production approval is secured.

## Circuit implemented

U1 generates CORE_1V2; U2 IO_3V3; U3 ESP_3V3. All draw from CORE_5V, specified here as 4.85–5.15 V. Each has its own inductor, capacitors, EN pull-down and raw PG output. Their returns share LOGIC_GND. ESP power is separately regulated; this block does **not** provide independent input fault isolation from CORE_5V.

| RPJ pin | Function | Connection per regulator |
| --- | --- | --- |
| 1 | PG | `<rail>_PG_OD`, externally pulled up |
| 2 | SW | `<rail>_SW` to its inductor |
| 3 | VOS | Output rail at output capacitor |
| 4 | GND | LOGIC_GND |
| 5 | EN | `<rail>_EN`, 10 kΩ to ground |
| 6 | VIN | CORE_5V |
| 7 | MODE/S-CONF | 76.8 kΩ to ground |
| 8 | SS/TR | 6.8 nF to ground |
| 9 | FB/VSET | Ground for 1.2 V; 301 kΩ to ground for 3.3 V |

The chosen configuration is mode 14: **VSET, 1 MHz forced PWM, active discharge**. Pin 9 is a signal pad, not an exposed ground paddle. [TI Rev. A, pin table and Tables 6-1/6-2](https://www.ti.com/lit/ds/symlink/tps62901.pdf)

| Fitted support candidate | Count | Purpose |
| --- | --- | --- |
| XGL4020-222MEC | 3 | 2.2 µH output inductors |
| C3216X7R1E106K160AB | 3 | 10 µF / 25 V X7R inputs, **1206** |
| C2012X7S1A226M125AC | 3 | 22 µF / 10 V X7S outputs, 0805 |
| GRM1885C1H682JA01D | 3 | 6.8 nF / 50 V C0G soft start, 0603 |
| CRCW060376K8FKEA | 3 | Mode selection, 76.8 kΩ / 1% / 100 ppm/K |
| CRCW060310K0FKEA | 3 | 10 kΩ EN pull-downs |
| CRCW0603100KFKEA | 3 | Passive 100 kΩ output bleeds |
| CRCW0603301KFKEA | 2 | 301 kΩ VSET selection for 3.3 V |

Manufacturer sources are individually linked in the source index. The TDK input package and output rating were independently checked: TI's example table has inconsistent size/voltage descriptions, so those descriptions were not copied. Candidate support MPNs are concrete; DC-bias, aging, temperature, ripple-current and procurement qualification remain open. A 76.8 kΩ 1%/100 ppm resistor with a conservative 150 K allowance stays within the converter's ±4% configuration-resistor decoding allowance. The 301 kΩ selector similarly remains above 249 kΩ.

Two editable local footprint candidates transcribe actual manufacturer copper patterns: TI RPJ0009A drawing 4224505/A and Coilcraft 1529-3. The inductor pads are 0.98 × 3.4 mm at **2.37 mm center spacing**, not a 2.37 mm gap. KiCad parsed both footprint sources and exported SVG previews successfully. These are real copper-pattern sources, not a routed PCB or validated stencil/assembly specification. Connector MPNs are unselected; JIN/JOUT/JCTRL are review boundaries.

## Voltage, load and startup calculations

| Rail | Reserved load | Regulation-only range | Ledger range | New modeled 5 V input reservation |
| --- | ---: | ---: | ---: | ---: |
| CORE_1V2 | 0.8 A | 1.185–1.215 V | 1.17–1.23 V | 0.285779 A → 0.29 A |
| IO_3V3 | 0.4 A | 3.25875–3.34125 V | 3.2–3.4 V | 0.374196 A → 0.38 A |
| ESP_3V3 | 0.7 A | 3.25875–3.34125 V | 3.2–3.4 V | 0.617344 A → 0.62 A |

Input calculations use `Iload × Vout_max / (4.85 × 0.85) + 0.05 A`, rounded upward to 10 mA. The assumed 85% efficiency and 50 mA allowance are engineering reservations, not measured guarantees. The combined rounded reservation is **1.29 A**, 40 mA above the old ledger's 1.25 A. Small passive loads and forced-PWM losses must be covered by the allowance and verified. FPGA consumption and ESP radio peaks remain measured-load requirements. No whole-board power approval follows from this table.

Static regulation leaves just **15 mV per side** for core ripple, layout drop and dynamic behavior. It leaves 58.75 mV per side for the 3.3 V rails. Those remaining margins must be tested at load and temperature; this is not a full output-voltage guarantee.

The selected soft-start capacitor gives the nominal model:

```text
Tss = Css(pF) / Iss(µA) × 0.8 V + 55 µs
    = 6800 / 2.5 × 0.8 + 55 = 2231 µs

Cmin = 6800 × 0.95 × 0.9955 = 6430.93 pF
Cmax = 6800 × 1.05 × 1.0045 = 7172.13 pF
Conservative Vref_min = (0.6 × 0.9875 − 0.008) / 0.75 = 0.779333 V
Conservative Vref_max = (0.6 × 1.0125 + 0.008) / 0.75 = 0.820667 V
Tss_min = Cmin / 2.7 × Vref_min − 700 = 1156.236 µs
Tss_max = Cmax / 2.3 × Vref_max + 160 = 2719.099 µs
```

The bounded model uses TI's additional min/max equations with conservative reference/tracking allowances. Its 700 µs K term exceeds the entire Figure 7-4 curve, avoiding optimistic interpolation at 6.8 nF. These are calculations from application guidance, **not a bound on EN-to-switching delay, prebias or the fully loaded ramp shape**. [TI Rev. A, Section 7.2.2.5.3, equations 14–16](https://www.ti.com/lit/ds/symlink/tps62901.pdf)

The modeled slopes are approximately 0.436–1.051 V/ms for core and 1.198–2.890 V/ms for 3.3 V, fitting the T20 all-supply target of 0.33–10 V/ms for this 3.3 V bank plan. At the local output capacitor's +20% tolerance/+22% temperature bound, 32.208 µF adds modeled startup currents of about 34 mA core and 94 mA each 3.3 V branch. Load decoupling and external capacitance are not included. No startup acceptance claim follows until the fully loaded rails are measured.

At 1 MHz nominal and an assumed effective-inductance floor of 1.408 µH, the ripple models are 0.659 A core and 0.833 A on each 3.3 V rail. Adding half-ripple to the loads yields approximately 1.130/0.817/1.117 A peaks. The Coilcraft data gives 4.4 A at 20% inductance drop and 21.5 mΩ maximum DCR **at 25°C**. Frequency/temperature and dynamic current-limit bounds remain unqualified. [Coilcraft XGL4020, document 1529](https://www.coilcraft.com/getmedia/76c9c081-4945-4c85-9129-9356e1ad6734/xgl4020.pdf)

Capacitor acceptance must establish at least 3 µF effective input and **6–50 µF effective output** at 1 MHz, counting load-side capacitance. The selected local output's upper tolerance/temperature figure already consumes 32.208 µF of that allowance. Nominal markings do not establish minimum capacitance at DC bias or aged temperature. Local input/output loops and the VOS sense connection need careful layout; no PCB layout is supplied here.

## Explicit sequencing and fault boundary

`JCTRL1` exposes EN, PG_OD, GND in three consecutive groups: pins 1–3 CORE_1V2; 4–6 IO_3V3; 7–9 ESP_3V3. JOUT1 exposes each corresponding rail and ground on 1/2, 3/4, 5/6. JIN1 is CORE_5V/GND on 1/2. EN uses external 0–3.6 V shared-ground control; 10 kΩ defaults off only when its driver is high impedance. PG has **no fitted pull-up here**; the external supervisor must provide a suitable pull-up and validity qualification.

PG is undefined below 1.8 V input and may assert at only 93.5% target. Discharge requires an earlier enable and retained input near 2 V; thermal shutdown can restart. [TI Rev. A, Sections 6.3.6, 6.3.9 and 6.4.5](https://www.ti.com/lit/ds/symlink/tps62901.pdf)

Consequently PG is insufficient to establish the narrow ledger voltage windows. There is no direct PG→EN cascade, independent voltage supervisor, restart latch or machine permission signal in this block. Raw PG alone cannot distinguish every brownout, broken feedback path, lost pull-up or unpowered device. Active discharge is not a guaranteed power-off bleed; the 100 kΩ fallback has no guaranteed system discharge time with unknown backfeed/capacitance. Reverse-current blocking is not implemented.

Efinix requires core/PLL before VCCIO and specified ramps, followed by reset qualification; unused PLL/MIPI/DDR resources have package-specific connections. F256 configuration reset has a 320 ns minimum pulse, but that alone does not implement a complete boot sequence. [T20 v6.0, Figure 28 and Tables 66, 71, 115](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf)

Actual FPGA supply pins, PLL filtering, downstream decoupling, reset hold/release, brownout recovery and ordered shutdown remain outside this block. The separately designed core 24 V→5 V stage and supervisor must be integrated and tested before this assembly can run the FPGA. Independent machine safety and output inhibition do not derive from these PG outputs.

## Evidence

**KiCad 10.0.4 ERC: zero violations. Sixteen scoped host tests: passed.** The netlist has 29 fitted components and 22 nets. Tests mutate pin/rail connections, regulator choice, VSET/mode/soft-start values, startup control, capacitor package, missing ground, PG semantics, model claims and custom land-pattern coordinates. All are disconnected source checks; they do not simulate or measure analog operation. The final PDF and detailed renders were visually inspected; labels and pins are readable without overlap. Manufacturer package and inductor land-pattern diagrams were also inspected directly.

```powershell
python tools/hardware_build_logic_power.py
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist --format kicadxml --output hardware/logic_power/netlist.xml hardware/logic_power/logic_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc --format json --severity-all --exit-code-violations --output hardware/logic_power/erc.json hardware/logic_power/logic_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export pdf --output hardware/logic_power/logic_power.pdf hardware/logic_power/logic_power.kicad_sch
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export bom --fields Reference,Value,Footprint,MPN,QUANTITY,DNP --labels Refs,Value,Footprint,MPN,Qty,DNP --output hardware/logic_power/bom.csv hardware/logic_power/logic_power.kicad_sch
python -m unittest discover -s tests -p test_logic_power.py -v
python tools/hardware_validate_logic_power.py
```

Regenerate dependent exports together after any source edit. Preserve manual changes before running the generator. The final validation manifest hashes the frozen ledger, sources, tests, report, manufacturer files and generated evidence. No fabrication files, routed PCB, board DRC, analog transient results, thermal/EMC qualification or production claim have been created.
