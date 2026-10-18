# Autonomous rail qualification and reset candidate

Engineering evidence, 28 September 2026. This block supplies an actual hardware startup chain for the three existing logic regulators. It is a **cost-risk circuit candidate**, not a selected production BOM or a finished controller. Four precision supervisors are unlikely to be the final answer for the user's low-price target. Core threshold margins are too small to close the lifetime and transient requirements.

## Delivered circuit and evidence

- Editable `hardware/power_sequence/power_sequence.kicad_sch`, project, symbols and UD16 footprint; actual KiCad XML netlist and PDF.
- KiCad 10.0.4 ERC: **0 errors, 0 warnings**. The ERC JSON records the tool's ignored checks. ERC establishes schematic consistency, not operational safety.
- Independent validator checks every exported node, selected value/MPN/package, physical pin function, boundary and footprint pad coordinate; it also calculates threshold and loaded enable corners.
- **20 focused Python tests pass**, including deliberate wiring, population, pin-function and model mutations. The tests use the actual exported netlist; no connected hardware or simulation of transistor behavior is involved.
- PDF overview and regulator/reset detail PNGs were visually inspected. The buffer NC pin was moved away from its supply wire, and bypass capacitors were moved away from adjacent labels. The final exporter retains separate NC singleton nets.
- `validation.json` includes the calculation results and SHA-256 hashes of this block's source, frozen ledger, tools, tests, research and rendered evidence. The historical ledger, logic regulators and other circuit blocks were not changed.

No PCB, DRC, Gerbers, manufacturing placement files, hardware measurements or physical startup certification are supplied.

## What the hardware does

The four `LTC2962HUD#TRPBF` devices use separate adjustable undervoltage/overvoltage channels. Each monitors its named rail with two independent precision dividers. The inactive channels are deliberately configured and tied high; there are no floating monitor inputs. All four run from `CORE_5V`, with individual 100 nF bypass capacitors and common `LOGIC_GND`.

| Stage | Qualifies | Prior condition | Released output |
| --- | --- | --- | --- |
| U1 | CORE_5V | Its own powered input | SEQ_5V_OK, which enables CORE_1V2 and ESP_3V3 through bounded resistor networks |
| U2 | CORE_1V2 | SEQ_5V_OK | IO_3V3_EN |
| U3 | IO_3V3 | IO_3V3_EN | FPGA reset qualifier |
| U4 | ESP_3V3 | SEQ_5V_OK | ESP reset qualifier |

Each stage uses the specified fixed **160–240 ms release delay**. FPGA core therefore starts before FPGA I/O; the reset output remains asserted through the I/O qualification delay. No Linux or ESP application needs to execute for this cold-start sequence. ESP qualification does not feed the FPGA reset chain. The rails still share an upstream power source: this is not fault-isolated redundant computing.

Two `SN74LVC1G17DBVR` Schmitt buffers translate the qualified reset signals into their respective destination supply domains. U5 runs from `IO_3V3` and drives `FPGA_CRESET_N`. U6 runs from `ESP_3V3` and drives `ESP_CHIP_PU`. Their outputs are push-pull. **Do not wire a programmer, reset button or second driver directly against these outputs.** Such reset requests must be combined upstream in a separately designed interface.

`SEQ_5V_OK` is a loaded internal analog/logic node, not a general-purpose 3.3 V GPIO, safety signal or permission to move. Additional loads on this node invalidate the present resistor calculation. Existing raw regulator PG outputs are not used because they do not establish the narrow rail windows.

## Exact interfaces and selected populations

`JRAIL1` is a schematic integration boundary: pin 1 CORE_5V; 2 CORE_1V2; 3 IO_3V3; 4 ESP_3V3; 5 LOGIC_GND.

`JCTRL1`: pin 1 CORE_1V2_EN; 2 IO_3V3_EN; 3 ESP_3V3_EN; 4 FPGA_CRESET_N; 5 ESP_CHIP_PU; 6 SEQ_5V_OK; 7 LOGIC_GND. These are not selected physical connectors. Every enable retains this block's 10 kΩ pull-down **and** the existing regulator's 10 kΩ pull-down. There must be no active-high external enable driver.

Independent ADI UD16 pin review: 1 RDIS, 2 MR, 3 DVCC, 4 VCC, 5 REF, 6 PG1, 7 PG2, 8 PG3, 9 PG4, 10 RT, 11 GND, 12 RST, 13 V4, 14 V3, 15 V2, 16 V1; exposed pad 17 is connected to ground. RDIS and RT go to CORE_5V, DVCC goes to ground. PG1/3/4 connect to REF; PG2 connects to ground. The H grade covers −40 to 125 °C; this is not an enclosure-temperature rating for the whole product.

TI DBV5 buffer mapping: 1 NC, 2 input, 3 ground, 4 output, 5 supply. The custom supervisor footprint implements the manufacturer's nominal UD16 land pattern. Mask, paste, assembly process and board placement still need manufacturing review.

Precision divider parts use the Vishay PLT0603Z catalog format with 0.01% initial tolerance and 5 ppm/K temperature coefficient. Examples are `PLT0603Z8792LST1` (87.9 kΩ), `PLT0603Z1002LST1` (10 kΩ) and `PLT0603Z2550LST1` (255 Ω). The 1 Ω trim is `CRCW06031R00FKEA`, 1%/100 ppm. Exact populations are recorded in `design-envelope.json`; catalog-format validity does not establish stocked availability or price. The six bypass-capacitor MPNs and boundary connectors are deliberately unselected.

## Threshold calculations and the narrow core limitation

For each independent divider:

`Vtrip = Vreference × (1 + Rtop/Rbottom) + Ibias × Rtop`

The bounded fresh-part calculation enumerates reference 0.4975–0.5025 V, sense bias ±15 nA, initial resistor tolerance and 100 K excursion from the 25 °C reference. Precision resistor error is ±0.06%; the 1 Ω trim uses ±2%. Series resistor extrema are summed individually. No statistical cancellation is assumed.

| Rail | Nominal top UV / OV; bottom | Calculated UV extrema | Calculated OV extrema |
| --- | --- | --- | --- |
| CORE_5V | 87.9 kΩ / 92.1 kΩ; 10 kΩ | 4.863963–4.926098 V | 5.072599–5.137464 V |
| CORE_1V2 | 1.355 kΩ / 1.445 kΩ; 1 kΩ | 1.170784–1.184225 V | 1.215494–1.229516 V |
| IO_3V3 | 54.5 kΩ / 57.5 kΩ; 10 kΩ | 3.204806–3.245231 V | 3.353832–3.396207 V |
| ESP_3V3 | Same as I/O | 3.204806–3.245231 V | 3.353832–3.396207 V |

These fresh static corners fit the declared strict rail envelopes and accept the regulation-only ranges: CORE_5V 4.95–5.05 V, CORE_1V2 1.185–1.215 V, and the 3.3 V rails 3.25875–3.34125 V. The CORE_5V acceptance calculation does **not** promise continuous operation at every point of its broader 4.85–5.15 V interface envelope; some allowed input extremes intentionally produce reset.

The smallest core margin is only **0.484 mV**. Adding a ±0.04% precision-resistor aging sensitivity causes the core acceptance/detection envelope to fail. The Vishay source describes aging under its stated test conditions; the sensitivity calculation is not a universal lifetime bound. Supervisor assembly stress, resistor assembly shift, ripple and real load transients are also not closed. Production release is blocked even though the fresh-part arithmetic passes.

The supervisor's maximum fault propagation figure is conditioned on **10% overdrive**. It is not a guaranteed delay for an arbitrarily shallow threshold crossing. Without a bounded power-collapse slew, this circuit cannot promise reset will precede a rail crossing its absolute operating boundary. Filtering also means short excursions can be ignored. These limitations require physical qualification and likely a better threshold/reference architecture before final component selection.

## Loaded enables and resets

The validator solves the coupled R101/R102/R104 network rather than treating its outputs as independent dividers. It enumerates ordinary resistor ±2% envelopes, source voltage, internal supervisor pull-up currents, a conservative ±1 µA regulator-input allowance, both installed carrier pull-downs and every connected/disconnected combination. The ±1 µA allowance is a verification contract; the TPS62901's listed 300 nA leakage is tested at EN=12 V, not a newly inferred guaranteed specification at every input voltage.

| Powered, released condition | Calculated range |
| --- | --- |
| Both carrier pull-downs installed, SEQ_5V_OK | 2.6736–2.9987 V |
| Both installed, CORE_1V2_EN and ESP_3V3_EN | 1.5886–1.8308 V |
| IO_3V3_EN with its carrier pull-down | 2.0280–2.3107 V |
| CORE/ESP enable maximum across disconnect cases | 2.7184 V |
| IO enable with carrier disconnected | 2.8684–3.2238 V |

The correct comparison is regulator enable ≥1.03 V, supervisor MR ≥1.6 V on SEQ_5V_OK and IO_3V3_EN, and the existing enable boundary ≤3.6 V. CORE/ESP enable voltages below 1.6 V are acceptable because those nodes do not drive MR. Powered asserted supervisor outputs fit their specified sink-current bounds and pull the enables below the regulator's low threshold. Below the monitor's valid operating conditions, this is not a general partial-power guarantee.

The reset qualifiers have 47 kΩ pull-ups and 470 kΩ pull-downs. Their high level clears the buffer's published Schmitt thresholds; slow release edges are acceptable for this Schmitt input. An ordinary non-Schmitt replacement is not equivalent.

FPGA reset has a 4.7 kΩ pull-down: its high load is below 0.74 mA, so the buffer's conservative 2.4 V high-level bound clears the FPGA's 2.0 V requirement. The FPGA's internal 27–65 kΩ reset pull-up is accounted for when considering the low-state load.

ESP reset uses **47 kΩ**, not 4.7 kΩ. With a powered external-input-load allowance of 20 µA, total high load remains below 94 µA. The buffer's ≤100 µA specification then guarantees at least VCC−0.1 V, clearing ESP reset VIH=0.75×VDD. The Espressif 50 nA input-current table is specified at 3.3 V/25 °C; full-temperature leakage remains an interface qualification requirement. The 160 ms minimum release hold exceeds its 50 µs startup/reset timing requirement in normal powered operation.

At exactly zero buffer supply, its maximum 10 µA Ioff produces at most 48 mV across the FPGA pull-down and 480 mV across the ESP pull-down, assuming no other energized injection. At CORE_5V=0 with destination rails retained, the bounded qualifier leakage model gives ≤0.223 V. These isolated endpoint calculations do **not** prove every intermediate-supply state, external-I/O backfeed condition or rapid power transition. The Schmitt buffer's normal operating minimum is 1.65 V.

## Power, startup and shutdown boundary

Reserve **10 mA additional CORE_5V current** for this block. A conservative allocation is 5 mA direct CORE_5V, 2 mA CORE_1V2, 2 mA IO_3V3 and 2 mA ESP_3V3. Referring the last three back through an assumed 85% conversion efficiency at 4.85 V gives about 8.90 mA total, leaving allocation margin. Direct current includes the four 210 µA maximum supervisor currents, pull-ups, sense dividers and control-pin allowances. Reset-buffer loads and transient input-region current remain part of measurement qualification.

The four direct CORE_5V bypass capacitors add **0.552 µF** maximum under the stated 20% tolerance and 15% X7R temperature envelopes. The two destination-rail bypass capacitors are behind their regulators. Upstream startup calculations must also retain all existing logic-regulator input capacitance and disabled-input-current allowances.

On a normal cold ramp with no alternate enable drive, U1 keeps the regulators disabled until CORE_5V qualifies and its release delay expires. The supervisor's low-output guarantee extends to VCC=1 V, while the TPS62901's own rising UVLO is 2.85–3.0 V. This supports separating initial main-rail capacitor charging from downstream operating loads in a conditional startup calculation. It does not prove arbitrary retained-charge restarts. TPS62901's maximum shutdown input current is 3.5 µA at EN=0 V; the circuit's nonzero low-level bound requires an allowance or measurement rather than silently treating that test condition as identical.

Efinix T20 guidance requires core/analog core power before I/O and reset held through valid startup. Its 3.3 V rail-ramp requirement remains the regulator/load designer's responsibility: the supervisor's 160–240 ms qualification delay is not the I/O ramp time. No explicit general reverse power-down ordering was found in the cited T20 source. This design therefore makes no reverse-order shutdown claim. Powered-off discharge, retained rails and backfeed remain open. Regulator thermal recovery and supervisor recovery can restart the power sequence; there is no latch requiring operator acknowledgement here.

FPGA package power-pin mapping, PLL filtering, flash/configuration pins, CDONE/user-mode qualification and the independently inhibited motion-output permission circuit remain separate unfinished work. A reset release must never be treated as machine permission.

## Reproduction

Run from the repository root, using the installed KiCad CLI:

```powershell
python tools/hardware_build_power_sequence.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o hardware/power_sequence/netlist.xml hardware/power_sequence/power_sequence.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json -o hardware/power_sequence/erc.json hardware/power_sequence/power_sequence.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export pdf -o hardware/power_sequence/power_sequence.pdf hardware/power_sequence/power_sequence.kicad_sch
python -m unittest discover -s tests -p test_power_sequence.py -v
python tools/hardware_validate_power_sequence.py
```

The initial `python -m unittest tests.test_power_sequence` invocation failed because this repository's tests directory is not importable as that package; the discovery command above ran all 20 tests successfully. Export/render evidence was refreshed after the actual R113 change.

Primary source URLs, editions and page references are in `research/power-sequence/SOURCES.md`. The ADI PDF was read through the web tool; direct transfer timed out, so no local ADI PDF hash is claimed. TI, Efinix, Vishay and Espressif PDFs are preserved locally. Manufacturer-source pin interpretation was independently reviewed by other project agents; no hardware measurements were substituted by that review.
