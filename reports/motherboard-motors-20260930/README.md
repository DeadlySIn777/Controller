# Twelve fitted motor interfaces on one motherboard — source r0.2

30 September 2026. This schematic partition implements twelve fitted interfaces on the same custom motherboard. Historical MC/transmitter sources were preserved. It is neither a separate custom daughterboard nor a fabrication release.

The [native source](../../hardware/motherboard_motors/motherboard_motors.kicad_sch) contains **226 physical candidate parts**: 52 ICs, 96 resistors, 42 capacitors and 36 TVSs. All twelve motors have differential STEP/DIR, independent floating normally-open/normally-closed enable contacts and independent isolated alarms. These alarms and contacts consume none of the 24 general DI or 16 general DO. References are already in the 6000 range; integration must not offset them again.

The [r0.2 receipt](receipt-r02.json) freezes source, tool and test hashes. The earlier [r0.1 archive](archive-r0.1/archive.json) and [earlier report](README-r01.md) remain historical evidence. [Source changes](source-changes-r02.json), [IC pin inspection](ic-pin-review-r02.json) and [native footprint inspection](native-footprint-inspection.json) describe the current candidate.

## Verified source evidence

| Evidence | Result | Scope |
| --- | --- | --- |
| KiCad 10.0.4 native ERC | 0 errors; 12 warnings; no ignored checks | Exactly one isolated-pin-label warning for each independently floating ISO1212 substrate island |
| Independent native XML connectivity | 1,028 pin assignments; 30 declared NC pins; pass | Exact component, package, pin, net, polarity and boundary inventory |
| Focused host/mutation tests | 24 tests pass | Reversed differential polarity, wrong package/pins, lost gate/default, enable shorting, grounded substrate, incorrect OPI clear, timing/default calculation mutations |
| Native footprint loading | 14 distinct footprints pass | Includes both Toshiba manufacturer reference lands and TI ISO1212 reference lands |
| Native PDF export and visual review | One page, reviewed | Source presentation; no routing or mechanical qualification |

The native ERC warnings are justified individually by the TI requirement for separate floating approximately 2 × 2 mm substrate islands. SUB12 and SUB13 are real pads, each assigned a distinct single-pad net. They must not be grounded, tied together or discarded as NC. NC6/7 are separately declared NC. Parent routing must create the independent substrate islands.

## Parent connections

[design.json](../../hardware/motherboard_motors/design.json) contains exhaustive boundary and physical pin maps. Source logical names have no leading slash; standalone native XML names have the root slash. Parent integration requires a bounded mapping to preserve retained MC copper names.

- `STEP0_TO_MIA` through `STEP7_TO_MIA`, corresponding DIR/EN_N, and `STEP8_TO_MX4` through `STEP11_TO_MX4`, corresponding DIR/EN_N. The historical suffixes identify retained nets, not removable custom cards.
- `TX_PERMIT_A_TO_MIA`, `TX_PERMIT_B_TO_MX4`, `MOTOR_POWER_OK_A_QUALIFIED`, `MOTOR_POWER_OK_B_QUALIFIED` inputs.
- `OPI_REARM_A/B` inputs; `OPI_OK_A/B` and `MOTOR_TX_GATE_A/B` outputs. Both OPI latches clear from the exact physical gate controlling the transmitter and enable circuit.
- `ALM0_FPGA` through `ALM11_FPGA` outputs. FPGA sampling, polarity and validity masking remain integration/gateware work.
- `MOTOR_IO_3V3`, `MOTOR_5V_A/B`, `LOGIC_GND`, `AUX_5V_A/B`, `AUX_24V_A/B`, `FIELD_GND`, `CHASSIS` power/return boundaries. These require actual supply and protection circuits. Boundary flags do not generate power or qualify health.

Each motor has a logical fourteen-position field boundary. Connector/mate/pitch/clearance selection belongs to parent integration; the review symbols have no footprint or fitted BOM entry. There is no invented connector or 3D body.

## Defaults and timing closure

| Function | Current source | Conditional bounds / remaining qualification |
| --- | --- | --- |
| Receiving EN_N default | Own 10 kΩ pull-up to receiving 3.3 V | Receiver must actually be powered; arbitrary intermediate-voltage operation remains unproved |
| Per-motor enable gating | Schmitt EN inverter, NAND with hardware bank gate, non-inverting open-drain sink | Exhaustive truth table: EN_N/GATE 00, 10, 11 are off; only 01 is on. Gate withdrawal directly makes sink high impedance |
| Powered-high and VCC=0 leakage | Nexperia 74LVC07APW,118 | Distinct ±10 µA powered-high IOZ and ±10 µA Ioff limits, compared with 0.1 mA photorelay return threshold at 25°C |
| Enable LED supply | TPS22918 plus 330 Ω passive bleed and 100 nF | QOD and turn-off data are typical. Ideal capacitor-only bleed contribution about 200.4 µs excludes turn-off delay, leakage and extra copper/load capacitance |
| Series NO/NC LED current | 220 Ω, bank switch and bleed included | Approx. 5.360–12.167 mA at specified 25°C diode-Vf conditions; full temperature, ageing and current-dependent Vf/trigger behaviour require measurement |
| Permission level restoration | 74AHCT1G17GVH on actual receiving 5 V | TTL-input high margin ≥0.38 V for the inherited loaded MC source envelope; avoids the former approximately 4 mV direct LTC input margin |
| Permission qualification | LTC6994-2; 60.4 kΩ ±1%, 100 ppm/°C, DIV=0 | Programmed delay 1.118–1.300 µs over the stated 0–55°C ambient and full IC error bounds; conditional 0.5 µs rejection / 2 µs acceptance and ≥100 ns output pulse. Input/output loading and startup protocol must meet datasheet conditions |
| NC withdrawal | TLP4176A LED falls → contact closes | tON ≤1 ms at 25°C. The ≤3 ms tOFF refers to NC opening when the LED rises, not closure |
| NO withdrawal | TLP3640A LED falls → contact opens | ≤0.2 ms at 25°C; no full-temperature maximum from reference-only curves |
| Whole 20 ms inhibit budget | Inherited conditional MC max 13.1315 ms plus conservative field allocation 4.31 ms | 17.4415 ms conditional calculation, 2.5585 ms margin. Actual monitor response, loading, LTC propagation/startup, relay temperature/ageing and physical wiring are not guaranteed by this export |

LTC6994 output is held low during POR, but startup completion copies the input without programmed delay. Raw permission must remain low until real supplies are qualified and deliberate boot/self-test/arming has completed. Startup timing and propagation include typical-only data; no fixed guaranteed startup deadline is claimed.

SN74LVC1G74DCUR replaces SN74LVC2G74DCUR as a sourcing choice. TI specifies **both as a single eight-pin D flip-flop with the same DCU pin map**. The earlier suggestion that the 2G74 name implied a dual-part pin error was incorrect; this revision does not claim a pin repair.

## Manufacturer lands and ratings

TLP3640A uses manufacturer 1.2 × 0.8 mm lands at x = ±3.15 mm, y = ±0.635 mm. TLP4176A now also uses the Toshiba reference 1.2 × 0.8 mm lands, at x = ±3.15 mm, y = ±1.27 mm, rotated into pin-1-upper-left orientation. The old inferred 1.8 × 0.9 mm TLP4176A lands were replaced. The official reference GIF and hash are retained in `sources/`. Assembly/stencil and enclosure clearance qualification remain necessary.

TI ISO1212 DBQ0016A lands are 1.60 × 0.41 mm at x = ±2.70 mm and 0.635 mm pitch. The copied footprint matches the DI source exactly and was independently loaded by native KiCad. Substrate copper is a separate layout obligation.

Photorelay contacts are limited to **30 V absolute peak and 50 mA continuous**. SMBJ33CA devices provide the specified 33 V standoff / 53.3 V clamp at their stated 25°C test pulse, below the photorelay 60 V device limit for a component screen. This is neither a 30 Vrms rating nor whole-board surge/EMC qualification.

Dark LED pairs produce NO open and NC closed. Disable-on-current drives still require an enable-loop source alive whenever the drive is powered and an independent STO/drive-power stop path. An open conductor or lost loop source can enable such a drive; the contact scheme cannot remove that electrical limitation.

## Remaining engineering and physical gates

Actual bank 5 V, receiver 3.3 V and field/AUX sources, rail protection/current budgets and independent power-health generation remain parent circuit work. The next separately owned motor-power source adds monitoring without modifying this frozen block. No input named QUALIFIED may be tied high as a substitute for its circuitry.

Parent integration still owns FPGA allocation, real connectors, routing, independent substrate islands, isolation/shield/transient returns, thermal/load budgets, power sequencing and mechanical interferences. Physical validation includes arbitrary partial power/brownout slew, transient timing, LED/contact behaviour over temperature and ageing, alarm latency, cable faults, surge and EMC. Standalone source inspection, host tests and ERC do not establish PCB DRC, synthesis, target operation, a costed manufactured assembly or manufacturing readiness.
