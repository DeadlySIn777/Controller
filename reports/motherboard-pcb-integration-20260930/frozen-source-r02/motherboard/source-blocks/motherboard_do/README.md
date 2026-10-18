# Sixteen motherboard smart sourcing outputs

Source candidate r0.1, 30 September 2026. **110 fitted parts / 552 fitted pads**, four exact TI TPS274C65ASRHAR drivers, two ISO7762FDBQR isolation barriers, sixteen CSD19538Q3AT reverse-blocking FETs and two independent permission/rearm logic domains. This is a soldered region of the one custom motherboard. It is not a custom daughtercard, a PCB or a fabrication release.

The [editable schematic](motherboard_do.kicad_sch), [native netlist](netlist.xml), [BOM](bom.csv), [exact pin model](design.json), [boundary map](boundary-map.json), [footprint provenance](footprint-review.json) and [independent validation](validation.json) preserve all sixteen DO0–DO15 channels. Native ERC has zero errors and two documented ground-name warnings. They identify the ISO7762 pin9 connections to **FIELD_A_0V / FIELD_B_0V**, which are required isolated field returns rather than LOGIC_GND. The checker requires precisely those two warnings and independently checks the actual pin/net mapping. `ignored_checks` is empty.

Each eight-output bank has two addressed SPI devices, strapped with 13.3k / 17.8k, 0.1% resistors for addresses 0 / 1. Four forward isolator channels carry SCLK, SDI, CS_N and DO_EN; two return SDO and wired-OR active-low FLT. The **F** isolator defaults low when its input domain is absent. Therefore an absent host can hold field CS low, but DO_EN remains low; this is documented rather than represented as a correctly deselected SPI bus. Firmware must restore a valid idle phase, clear SW_STATE and verify configuration before enabling.

The TPS current-sense output has a physical 1k/100pF RC to field ground. Its **internal 10-bit ADC**, current, output-voltage, supply and temperature registers reach the local-controller boundary over isolated SDO. This closes the former test-point-only acquisition path at the frontend. The local IOL1 controller, CRC register driver, calibration, timestamps and host/UI readout are still unimplemented. READY has its manufacturer-required resistor to device ground; it is not a universal power-good or permission signal.

Each bank gates DO_EN with `OUT_PERMIT_k AND OUT_EN_LATCH_Q AND CARD_EN`. Its latch clears when permission or the local-controller reset falls. A fresh IO_ENABLE edge is required after an accepted drop/reset; a returning permission level alone cannot rearm it. Controller-enable, reset, strobe and permission inputs have real pull-downs. The independent permission path bypasses SPI/application commands. Whole-path startup sequencing, local watchdogs and loaded shutdown timing still require integration and measurements.

The inherited ratings remain **0.5 A continuous per channel / 2 A continuous per four-channel group**. The chosen commissioning current limit is **code6, 0.72 A nominal, 0.62–0.82 A datasheet range**. It is paired for channels1/2 and3/4. The driver **POR limit is codeA, 1.25 A**, not0.72 A: outputs must stay disabled until firmware writes and reads back both paired limits, zero SW_STATE/failsafe state, no inrush boost/paralleling, CRC/ADC/watchdog configuration and latch-off behavior. These are explicit unimplemented firmware requirements; the circuit does not physically lock programmable ILIM to0.72 A. Nominal1 A code8 permits1.15 A max and is rejected by the validation screen; code7 permits1.0 A max.

Reverse blocking uses each TPS RCB gate and an external **100 V CSD19538Q3AT**, with source toward the switch and drain toward the terminal. Its manufacturer top view was visually checked: **pins1–3 source,4 gate,5–8 and exposed pad9 drain**. Extracted PDF text rearranged the labels and was not used as a substitute for the drawing. The selected FET specifies RDS(on) at6 V, matching the TPS6–7 V gate drive; its4.3 nC typical Qg is below TI's20 nC typical application value. This is a component screen, not reverse-miswiring/transient/thermal qualification. Each terminal has a100 V22nF filter after its blocking FET. Unused LEDOUT pins remain native NC; no actual-output indication is claimed.

Six logical boundary symbols have no MPN/footprint and are excluded from PCB and BOM:

| References | Boundary | Remaining parent circuit |
| --- | --- | --- |
| J10001 / J10002 | XDO0 / XDO1, eight outputs and four matching field returns each | Exact pluggable terminal selection and contact geometry |
| J10003 / J10004 | FIELD_A/B_24V, separate return and DOA/DOB_FIELD_3V3 | Protected entries, bank bulk, surge strategy and **same-VS-derived** logic supplies / rail health |
| J10005 / J10006 | IO_3V3/LOGIC_GND, OUT_PERMIT_A/B, controller reset, enable strobe/CARD_EN, SPI and FLT | Two local IOL1 controllers and their1 ms accepted-frame timeout / independent<=2 ms IWDG, new-epoch enable and diagnostics |

Both TPS internal regulators are disabled with REG_EN grounded. Their VDD pins are never paralleled while the internal regulators are active. No field-3V3 converter, fake regulator, always-true presence/permission, or fabricated connector is introduced. The conditional ERC supply flags are boundary declarations, not power sources.

The TI RHA40 lands include41 numbered electrical pads and nine separate paste apertures. DNH8 includes9 numbered electrical pads and its offset drain EP. ISO7762 reuses the same TI DBQ0016A land drawing as the separately reviewed ISO1212; the shared pin count does not reuse that IC's electrical pin map. Actual filled/capped thermal vias, return planes, high-current copper, creepage, stencil and solder coverage belong to the final PCB. Three-dimensional module/mechanical qualification is not established by these source footprints.

Build and check:

```powershell
C:/Python314/python.exe -X utf8 tools/hardware_build_motherboard_do.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml --output hardware/motherboard_do/netlist.xml hardware/motherboard_do/motherboard_do.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --output hardware/motherboard_do/erc.json hardware/motherboard_do/motherboard_do.kicad_sch
C:/Python314/python.exe -X utf8 tools/hardware_validate_motherboard_do.py --write
C:/Python314/python.exe -X utf8 -m unittest discover -s tests -p test_motherboard_do.py -v
```

The [dated source receipt](../../reports/motherboard-do-20260930/README.md) distinguishes primary-source inspection, host tests and native ERC from target firmware, PCB DRC, fabrication or physical validation. Earlier cost receipts stay immutable; these110 parts are not silently inserted into the701-part cost basket.
