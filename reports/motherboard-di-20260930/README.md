# Twenty-four general DI: source and native review

30 September 2026. [New editable source](../../hardware/motherboard_di/motherboard_di.kicad_sch) implements the **24 dedicated general input frontends**, with twelve ISO1212DBQR devices and 120 fitted source components. Native footprint inspection counts 408 physical pads, including 24 declared device NC pads (pins 6/7). DI0–DI23 remain distinct from all twelve motor alarm inputs and the two required fast probes. The historical 22 mixed HOME/probe/alarm input study is unchanged and remains separate evidence.

[Frozen review](review.json) contains 58 unchanged input hashes and byte-identical copies in `inputs/`. [Native XML](../../hardware/motherboard_di/netlist.xml) matches every fitted and logical-boundary pin/value/MPN/footprint. The [native PDF](../../hardware/motherboard_di/motherboard_di.pdf) is visually inspected in [overview](native-overview.png) and [pair detail](native-pair-detail.png). This is new standalone schematic work for integration into the one motherboard, not a routed circuit or another custom service card.

| Check | Result and scope |
| --- | --- |
| New host tests | 28 passed; physical pin/domain, NC/SUB, channel allocation, defaults, shared sensor supply, footprint and native evidence mutation cases |
| Preserved old input tests | All 26 passed against the unchanged historical 22-input source/evidence |
| Native KiCad schematic export | XML and one-page PDF generated with KiCad 10 |
| Native ERC | Zero errors; exactly 24 `isolated_pin_label` warnings, retained and independently identified; `ignored_checks: []` |
| Native footprint review | 120 loaded fitted footprints, 408 pads; ISO1212 pads match the TI DBQ0016A example |
| Source/native validator | Passes; no connector boundary is fitted or included in the 120-line BOM |
| Physical/PCB/firmware/RTL | Not performed or implemented by this scope; no manufacturing release |

The 24 ERC warnings identify the separate single-pin floating SUB nets. TI Figure 4-2 explicitly forbids their connection to either field ground, logic ground, another SUB or any signal. The final PCB must give each its own approximately 2 × 2 mm floating copper island while preserving full isolation clearance. Those islands remain layout work; adding a ground to silence ERC would violate the device contract. [Exact warning identities](../../hardware/motherboard_di/expected-erc-warnings.json) and mutation tests reject additional/deleted/changed warnings or suppression.

The frontends are fixed sinking inputs for PNP sources or dry contacts to a qualified field positive supply. They retain the 0–30 V study envelope and LOW ≤ 5 V / HIGH ≥ 15 V targets. NPN, 12 V, automatic source/sink selection, AC and per-channel sensor-mode switching are not implemented or qualified. EN is tied to IO_3V3; an open input reads LOW only while powered and valid. Unpowered/brownout output is undetermined: 100 kΩ output bias does not prove fail-safe validity. The local acquisition controller, independent rail/reset readiness, IOL1 validation/sequence/freshness and protocol/service validity remain unimplemented parent circuits.

Four no-footprint/on-board-false schematic boundary symbols preserve three XDI0–XDI2 logical groups and the future acquisition interface. Each field group maps eight general DI plus supply contacts 9/10 and return contacts 11/12. Supply contacts 9 and 10 share **one 0.20 A group reservation**, not 0.20 A each. All three groups reserve 0.60 A under frozen IS-1 section 03 XDI and section 04 §10.2. The earlier delegated 0.5 A recollection was corrected against those exact sources; no new electrical limit was authorized. **No sensor-power source, current limiter, voltage/fault telemetry or selected connector is fitted here.** [Boundary map](../../hardware/motherboard_di/boundary-map.json) explicitly excludes those symbols from PCB and BOM. FIELD_B_0V remains separate from LOGIC_GND.

The output nets are DI0_LOGIC–DI23_LOGIC for the future local acquisition controller, not 24 allocated FPGA ball assignments. Physical GPIO allocation and versioned integrated-region identity/validity need the parent IS-2 circuit and logic contract. Source references reserve index 8: U8001–U8012, R8001–R8024 / R8101–R8124 / R8201–R8224, C8001–C8024 / C8101–C8112. Do not merge the historical 22-input sheet as an additional promised general bank.

[Calculation screens](../../hardware/motherboard_di/validation.json) retain TI's guaranteed-table 2.05–2.75 mA active-input range at stated Rs conditions, with separately labelled external TCR extension. The 100 K extension screens all 24 active inputs at about 66.67 mA / 2.00 W field power at 30 V and about 23.63 mA static logic load. RTHR/C time-constant screens are approximately 9.33–10.69 µs, **not complete propagation delay**. Current-limit accuracy, cable/sensor leakage, input filtering/acquisition latency, pulse/surge/EFT, assembled thermal/EMC and complete-board isolation remain qualification work. Required sensor supply/current limiters and telemetry are parent engineering work, not closed by these numbers.

Remaining engineering includes the local acquisition/protected sensor supply circuits, line/transient qualification, selected terminals and mating/clearance, actual board routing/SUB islands/return paths, complete power/thermal/EMC review, FPGA/controller resource binding and physical validity/timing tests. Existing MC r0.4/revision-14 routing statistics remain unchanged by this work; no Gerbers, drill/CPL or fabricated prototype is claimed.

Reproduce the source, then native exports and scoped validation:

```powershell
python tools/hardware_build_motherboard_di.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml --output hardware/motherboard_di/netlist.xml hardware/motherboard_di/motherboard_di.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json --severity-all --output hardware/motherboard_di/erc.json hardware/motherboard_di/motherboard_di.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export pdf --output hardware/motherboard_di/motherboard_di.pdf hardware/motherboard_di/motherboard_di.kicad_sch
python tools/hardware_validate_motherboard_di.py --write
python -m unittest discover -s tests -p test_motherboard_di.py -v
python -m unittest discover -s tests -p test_digital_inputs.py -v
& 'C:/Program Files/KiCad/10.0/bin/python.exe' reports/motherboard-di-20260930/native_footprint_review.py
```

The frozen `record_review.py` run refuses to overwrite `inputs/`; preserve this review and use a new dated review before recording a material revision. Host/source, native ERC and loaded footprint geometry are separate evidence classes; no target firmware build, HDL simulation, vendor fit, board DRC or physical measurements occurred here.
