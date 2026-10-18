# Twelve fitted motor interfaces on one motherboard

30 September 2026. This new circuit block follows the user's latest one-custom-motherboard decision. It is a schematic partition of the same motherboard, not a removable custom card or a separately manufactured daughterboard. Historical MC and transmitter sources were not changed.

The new [native source](../../hardware/motherboard_motors/motherboard_motors.kicad_sch) contains 210 physical candidate parts: six AM26C31 differential transmitters, twelve TLP3640A normally-open contacts, twelve TLP4176A normally-closed contacts, two hex open-drain enable drivers, two hardware-gated enable-supply switches, six dual ISO1212 alarm receivers and receiver qualification/OPI logic. All twelve motors retain individual enable and alarm. The twelve alarm inputs consume none of the 24 general DI; enable contacts consume none of the 16 general DO. No FPGA-pin/resource, speed or runtime-channel qualification follows from this circuit export.

Fresh KiCad 10.0.4 standalone ERC reports zero violations with `ignored_checks: []`. Native XML checks all 926 source pin assignments, including 40 declared NC pins, against their exact standalone-root names. Source/contract tests include reversed differential polarity, swapped switch pins, lost power inhibits, wrong enable default rail, shorted per-channel enables, grounded ISO substrates and incorrect OPI clear wiring. Host tests, native ERC, source inspection and physical validation remain distinct.

The native part references occupy the 6000 range and must not be offset a second time. The parent may remove logical boundary symbols and conditional PWR_FLAG declarations during integration. Their absence must be replaced with actual parent circuitry and connections, not assumed power-good constants.

## Parent connections

The [design.json](../../hardware/motherboard_motors/design.json) contains exhaustive `boundary_inputs`, `boundary_outputs`, `boundary_power`, component pin maps and the motor field signal map. Preserve current MC private output names when promoting interfaces; this block's source logical names have no leading slash and its standalone XML names have one root slash. A controlled parent mapping is necessary.

- STEP/DIR/EN_N: `STEP0_TO_MIA` through `STEP7_TO_MIA`, corresponding DIR/EN_N, and `STEP8_TO_MX4` through `STEP11_TO_MX4`, corresponding DIR/EN_N. The suffixes retain old MC source names for copper compatibility and do not imply custom cards in this revision.
- Permission inputs: `TX_PERMIT_A_TO_MIA`, `TX_PERMIT_B_TO_MX4`, `MOTOR_POWER_OK_A_QUALIFIED`, `MOTOR_POWER_OK_B_QUALIFIED`.
- OPI interface: `OPI_REARM_A/B` inputs, `OPI_OK_A/B` outputs. Both latches are asynchronously cleared by the exact `MOTOR_TX_GATE_A/B` physical nodes controlling the transmitters and enable-supply switches.
- Alarm outputs: `ALM0_FPGA` through `ALM11_FPGA`. Polarity, qualified sampling and validity masking remain FPGA/host work.
- Logic power/return: `MOTOR_IO_3V3`, `MOTOR_5V_A/B`, `LOGIC_GND`. Receiving enable pull-ups belong to `MOTOR_IO_3V3`; they never pull up to a potentially dead upstream MC source rail.
- Field power/return: `AUX_5V_A/B`, `AUX_24V_A/B`, `FIELD_GND`. FIELD_GND remains separate from LOGIC_GND. CHASSIS is a separate shield/connector boundary, with bonding to be designed in the complete assembly.

Each motor's logical 14-position field boundary retains four differential contacts, signal reference, shield/separation, three floating enable contacts, two protected auxiliary supplies, field return and alarm. The connector/mate/pitch/clearance selection is deliberately unresolved; these logical symbols have no footprint or fitted BOM line. The source does not misrepresent them as manufactured connectors.

## Manufacturer inspection and defaults

Toshiba's 7 April 2026 PDFs were obtained through their official `docget.jsp` endpoints after the named-PDF endpoints refused direct retrieval. Both photorelays are pin 1 anode, 2 cathode, 3/4 floating MOSFET drains. TLP3640A's reference lands are 1.2 × 0.8 mm, centred at ±3.15/±0.635 mm after rotation into pin-1-upper-left orientation. The new local footprint follows that figure. TLP4176A supplies a package drawing rather than a reference land pattern; its new footprint uses explicitly inferred 1.8 × 0.9 mm lands at ±3.15/±1.27 mm and a courtyard containing the maximum package envelope. That land/stencil candidate still needs assembly review. Neither relay has an invented 3D body.

TPS22918's manufacturer top view and table agree: VIN1/GND2/ON3/CT4/QOD5/VOUT6. CT is open as permitted; QOD is tied directly to VOUT. A separate 1 kΩ passive bleeder and 100 nF output capacitor provide a discharge path independent of QOD. The datasheet-screen LED current, including maximum switch resistance and the bank bleeder, is approximately 5.364–12.167 mA at the specified 25°C diode-voltage conditions. It does not qualify diode Vf/trigger/leakage over temperature, ageing or partial-power transitions. Powered-high LVC07 output leakage versus the 0.1 mA form-B return threshold is not closed by its Ioff-at-VCC=0 specification.

Every receiving STEP/DIR input has a 10 kΩ pull-down. Each receiving EN_N input has its own 10 kΩ pull-up. A dark LED pair makes NO open and NC closed; independent bank permission cuts their supply. Disable-on-current drives still require a loop source powered whenever the drive is powered, and an independent STO/drive-power stop path. A lost loop supply or open conductor can enable such a drive; software cannot remove that electrical limitation.

ISO1212's field returns are FIELD_GND and logic returns LOGIC_GND. SUB12/SUB13 remain separate unconnected pads with isolated substrate copper to be laid out; they must never connect to any ground or each other. NC6/7 are also unconnected. A weak logic-output pull-down does not prove brownout validity.

Vishay's bidirectional SMBJ33CA is used across each floating contact and each alarm field input: 33 V stand-off and 53.3 V clamp at its specified 25°C pulse condition. That is below the 60 V device limit for screening. It is not a whole-board surge/EMC or energy rating. Contact limits are 30 V absolute peak, 50 mA continuous; 30 Vrms operation is not established by a 33 V TVS choice.

## Remaining engineering and physical gates

The complete parent still must generate and supervise actual motor 5 V, receiver 3.3 V, field/AUX supplies; allocate FPGA pins and power/thermal budgets; connect hardware-qualified power health; select/connect field terminals; route and preserve isolation/shield/transient return paths. No fitted power or connector is created by the source boundaries.

The 820 Ω/1.5 nF receiver RC is a source candidate, not a proved 0.5 µs-reject/2 µs-accept filter. Manufacturer Schmitt limits at a stated supply point cannot be silently interpolated across all real supply/drive corners. Repeated glitches, minimum qualified output pulse, OPI capture, QOD/bleed delay, both relay transitions and the complete 20 ms watchdog-to-field-inhibit budget remain unproved. Alarm analog-filter plus FPGA-sampler latency also needs qualification. These open gates remain in the machine-readable model and validation report. Routing, DRC, vendor FPGA fit, target compilation, manufactured BOM, fabrication files and hardware operation were not performed by this standalone block.
