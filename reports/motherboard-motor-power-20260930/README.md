# Actual motor receiving and field power health — source r0.1

This new 9xxx circuit partition belongs to the single custom motherboard. It does not alter the frozen 226-part motor r0.2 block or create a custom daughterboard. [Native schematic](../../hardware/motherboard_motor_power/motherboard_motor_power.kicad_sch), [source model](../../hardware/motherboard_motor_power/design.json), [native PDF](../../hardware/motherboard_motor_power/motherboard_motor_power.pdf) and [independent validation](../../hardware/motherboard_motor_power/validation.json) contain the actual circuit.

**63 physical parts are implemented:** four LTC2962HUD#PBF window supervisors, two SN74LVC1G17DBVR translations, one ISO7720FDWR isolator, one SN74LVC2G08DCUR hardware AND, 46 resistors and nine bypass capacitors. References are U9001–U9008, R9001–R9046 and C9001–C9009. B9001/B9002 are logical review boundaries with no footprint/BOM line. Standalone power flags declare parent-fed actual rails; they neither generate supplies nor turn absent supplies into qualified health.

Native KiCad 10.0.4 ERC has **zero errors and zero warnings, `ignored_checks: []`**. Independent native XML checks **229 pin assignments including eight NC**, and exact package/pin/net/polarity inventory passes. **21 host tests pass**, including 256 valid-supply truth combinations and negative tests for a default-high isolator, domain bridging, incorrect comparator mode, reset bypass, fabricated high health, unmonitored post-limiter rails, weak precision substitutions, footprint and physical pin-map errors. All six distinct footprints load and number correctly in native KiCad. The native PDF is one page and has been visually inspected. None of these checks is a PCB DRC, hardware measurement or manufacturing release.

## Actual topology and integration ports

U9001 and U9002 each monitor two windows: their own receiving `MOTOR_5V_A/B` and actual retained `IO_3V3`. They are independently powered from retained `CORE_5V`, so a dead receiving motor rail cannot power a fake healthy output. U9003/U9004 separately monitor post-limiter `AUX_5V_A/B` and `AUX_24V_A/B`, powered from independent field-domain `FIELD_5V`. No monitoring occurs on an upstream fictitious substitute for the post-limiter node.

Each LTC2962 has PG1/PG3 tied REF (+ADJ undervoltage), PG2/PG4 tied local GND (−ADJ overvoltage), grounded DVCC (open-drain), local MR/RDIS high, RT tied source VCC (160–240 ms release). Four real comparator inputs must be healthy before RST releases. Released RST pull-ups belong to the supervisor's actual source rail, with independent 100 kΩ pull-downs. Schmitt buffers translate slow logic-domain RST to actual receiving 3.3 V. The ISO7720 **F suffix is mandatory** for default-low input power/signal loss at its specified supply states. The final hardware AND requires both local logic and isolated field health; Linux/ESP/FPGA cannot drive a software health bypass.

Exact exported outputs:

- `MOTOR_POWER_OK_A_QUALIFIED`, `MOTOR_POWER_OK_B_QUALIFIED`: connect to the frozen motor source's same logical inputs.
- `MOTOR_LOGIC_HEALTH_A`, `MOTOR_LOGIC_HEALTH_B`: receiving logic diagnostics.
- `MOTOR_FIELD_HEALTH_A_ISOLATED`, `MOTOR_FIELD_HEALTH_B_ISOLATED`: isolated field diagnostics and hardware inhibit terms.

Exact power inputs are `CORE_5V`, `IO_3V3`, `LOGIC_GND`, `MOTOR_5V_A`, `MOTOR_5V_B`, `FIELD_5V`, `FIELD_GND`, `AUX_5V_A`, `AUX_5V_B`, `AUX_24V_A`, `AUX_24V_B`. There are no software control inputs. Parent integration must map the frozen motor source's `MOTOR_IO_3V3` to actual `IO_3V3` explicitly, and promote the named bank rails and health outputs so both circuit partitions share them. No wildcard retained-copper rename is authorized. `FIELD_GND` and DI `FIELD_B_0V` remain unjoined until the actual power-entry/domain assignment is reviewed.

## Static voltage corners

Bounds include H-grade ADI ±0.5% comparator threshold, ±15 nA input bias at the threshold, resistor ±0.01% initial, 5 ppm/°C over a conservative ±100 K excursion and an additional 400 ppm drift sensitivity. This is a component-corner screen; soldering stress, arbitrary lifetime and board noise are not guaranteed by the extra allowance.

| Window | Guaranteed component-corner UV threshold | OV threshold | Acceptance interval screened |
| --- | --- | --- | --- |
| Motor 5 V, each bank | 4.8605–4.9296 V | 5.0689–5.1412 V | 4.95–5.05 V within required 4.85–5.15 V |
| Receiving 3.3 V, each bank monitor | 3.2026–3.2474 V | 3.3515–3.3985 V | 3.25875–3.34125 V within required 3.20–3.40 V |
| AUX5, each bank | 4.8009–4.8692 V | 5.1186–5.1915 V | 4.875–5.075 V |
| AUX24, each bank | 18.1181–18.3823 V | 29.2862–29.7146 V | 19–29 V only |

The inherited **18–30 V AUX24 requirement remains unchanged**. These divider corners accept 19–29 V reliably and reject below/above the required outer window, but do not guarantee arming throughout 18–30 V. That reduced guaranteed acceptance is an explicit integration limitation, not a renamed equivalent requirement. The actual threshold extrema, rather than an assumed one-volt margin, appear in the model.

AUX5's frozen falling-trip minimum of 4.80 V and monitor-node normal minimum 4.875 V have only **0.908 mV trip margin and 5.801 mV normal acceptance margin** in this conservative screen. This is narrow and needs either a better-qualified rail/error allocation or a refined monitor selection if physical noise/drop/stress cannot fit. Do not call these positive arithmetic margins robust physical qualification.

The qualified AND outputs include their own 1 kΩ pull-down plus frozen motor 10 kΩ pull-down and receiver leakage. Calculated high load is 3.822 mA, inside the 8 mA data-sheet condition supporting 2.4 V minimum high at the stated 3 V supply point; receiving HIGH is 2.0 V. Raw logic/field health released minima are approximately 4.384/4.405 V. Schmitt screening uses the largest **published** VT+ maximum (3.33 V across listed supply test points), without interpolating a 3.3 V threshold or timing bound. Table-conditioned leakage and exact-zero supply checks remain distinct from arbitrary intermediate supplies.

## Source-backed land patterns

The LTC2962 footprint is copied byte-for-byte from the retained reviewed MC parent. Numbered pads, SMD thermal pad17 and parent courtyard stay unchanged. The TI ISO7720 footprint follows the **DW0016B 4221009/B HV/isolation example**, with 16 lands 1.65 × 0.60 mm, x centres ±4.875 mm and 1.27 mm pitch. Its 8.1 mm nominal pad-to-pad copper gap is the drawing's HV option. No fake 3D body, board-level isolation certification or stencil approval is added. Primary PDF, rendered pin/outline/land pages and native pad inspection are archived here.

## Exact remaining gates

1. **Supply circuitry remains absent:** receiving motor 5 V generation/protection and current budgets; field 5 V and independent AUX5/AUX24 bank limiters/drop/current/short-survival. Retained CORE5's 4.85 V minimum leaves no guaranteed series-drop headroom to a receiving rail also requiring 4.85 V. This block does not silently loosen either limit.
2. **Independent latched inhibition remains circuit/integration work:** ISO7720F output is explicitly undetermined when a supply is 1.7–2.25 V, and when receiving power is absent. A field ramp/recovery must not resume physical permission because a transient health output rises. An independently latched upstream inhibit and deliberate rearm, or a separately qualified power-blanking path, must close this gate. It is not merely a physical-validation-only blocker.
3. **Brownout/fault timing remains conditional:** LTC2962's 40 µs maximum applies at 10% overdrive. There is no guaranteed bound for arbitrary shallow droop/slew; RST power-down low is specified only down to VCC=1 V. Intermediate 3.3 V logic, LED rail charging/discharge and direct physical gate response require an actual circuit/slew contract and subsequent measurement. Whole 20 ms withdrawal is not proved here.
4. **AUX24 full-range acceptance and AUX5 narrow margins remain unresolved**, as quantified above. Monitoring is delayed fault signalling and cannot replace a surge clamp.
5. **Exact precision resistor procurement and costs remain unknown**, along with stress/lifetime, actual rail noise, Kelvin layout, loaded temperature and manufacturing stencil/assembly qualification. Whole-board connectors, routing/planes/isolation, FPGA/firmware, DRC and fabrication remain parent work.

No purchasing, fabrication export or physical hardware test was performed by this source partition. [Frozen motor r0.2](../motherboard-motors-20260930/receipt-r02.json) hashes remain unchanged.
