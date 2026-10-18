# Connected controller circuit review

28 September 2026. Ten actual KiCad circuit blocks are now connected in one editable hierarchical project. This replaces isolated power/interface drawings with an exported electrical netlist, explicit cross-sheet connections and a combined review BOM. It is still a partial controller circuit, not a PCBWay manufacturing package.

Open [controller_assembly.kicad_pro](../hardware/controller_assembly/controller_assembly.kicad_pro) in KiCad. The [root schematic](../hardware/controller_assembly/controller_assembly.kicad_sch) contains the hierarchy; the [combined drawing](../hardware/controller_assembly/controller_assembly.pdf), [netlist](../hardware/controller_assembly/netlist.xml), [reference/source map](../hardware/controller_assembly/assembly-map.json), [review BOM](../hardware/controller_assembly/review-bom.csv) and [validation identities](../hardware/controller_assembly/validation.json) describe the same exported circuit. The BOM still contains unselected parts and review-boundary connectors; it is not suitable for turnkey ordering.

## Actual circuit scope

| Sheet | Implemented connections | Main limits |
|---|---|---|
| Power entry | Independent core/field physical-fuse positions, TPS26630 paths, reverse-blocking FETs, thresholds and diagnostics | Fuse/output-clamp selection and source/surge coordination open |
| Core converter | LM70660 5V candidate, current sensing, bootstrap, local bypass, ceramic/polymer storage and compensation | Load-step, stability, thermal and reverse-feed qualification open |
| Logic power | Separate TPS62901 core1.2V, IO3.3V and ESP3.3V branches | Exact ramp/transient limits still need physical verification |
| Field power | LMR36506 fixed5V field-side buck | Field domain only; field loads still require independent permission |
| Encoder power | Two separately limited5V branches | External encoder compatibility and actual fault response unqualified |
| Six-joint transmitters | Twelve differential STEP/DIR signals using three AM26C31 banks | Drive inhibit/defaults and physical motion timing unqualified |
| Two encoder receivers | Six used differential A/B/Z receivers | Line protection, timing and target package mapping unfinished |
| SBC power | Voltage supervisor plus controlled-slew TPS22990 switch |3A/1mF bounded computer branch; no branch reverse blocking or current limiting |
| Power sequence | Independent voltage windows, core-before-IO order, separate FPGA/ESP reset paths | Four precision monitors are a cost-risk candidate; tight core-voltage margins remain |
| Digital inputs |22 ISO1212 inputs, filter/current-setting networks, logic bias and terminal mapping |0-30V study, common field return; no universal-voltage or channel-to-channel-isolation claim |

The assembler exports only explicitly allowed interface nets and gives every physical component a unique reference. LOGIC_GND and FIELD_GND remain separate. The transmitter's former SIGNAL_5V boundary is explicitly mapped to CORE_5V. Core1.2V, IO3.3V and ESP3.3V enable lines now connect the independent sequencer to the regulator branches, including their existing pulldowns. SBC_5V remains a separate switched rail at a compute-module boundary; it is not shorted back to CORE_5V.

The original six-joint/two-encoder electrical ledger is preserved. This circuit does not quietly become the proposed eight/four controller. Compute, FPGA and ESP chip/package connections remain undrawn; interface boundary labels do not stand in for those devices. The original18-30V/2A core-source study is not fulfilled by the revised19-30V/3A source proposal. Display and optional AI power are outside these budgets. A3A computer branch does not establish that every CM4/CM5/CB2 variant and peripheral set can run from it.

## Problems corrected and remaining numerical limits

- Removed entry R9/R29: converter EN dividers now derive their startup bias from the protected input, without backfeeding unpowered logic rails.
- Changed core current-limit resistor from8.20k to7.50k for the revised load reservation; its stated transfer corners remain screening assumptions.
- Replaced the earlier TPS62160 logic-regulator proposal after its accuracy/ramp limits failed the FPGA requirements review.
- Separated main-rail charge, logic-rail startup and computer startup. Actual hardware timing now supports the staged budget; arbitrary warm-reset/partial-power behavior is not inferred from cold-start arithmetic.
- Increased main output storage and revised compensation. Independent review caught use of average load current in an unload-energy screen; the current calculation includes the inductor's peak switching phase. The calculator still cannot establish control-loop stability or measured load regulation.
- Preserved ISO1212 floating substrate islands as22 distinct one-pin nets. KiCad reports22 expected warnings; no dummy connections, grounding or broad warning suppression hide them.
- Found that the proposed TPS4H160 output driver's48V transient absolute limit is below the entry TVS's48.4V reference clamp. See [the protection finding](../research/FIELD_OUTPUT_PROTECTION_GAP.md). The output-stage protection decision remains open.

The current detailed calculations and conditions are in [core converter](CORE_CONVERTER.md), [SBC power](SBC_POWER.md), [logic supplies](LOGIC_POWER.md), [sequencing](POWER_SEQUENCE.md), [field supply](FIELD_POWER.md) and [inputs](DIGITAL_INPUTS.md). None of the independent regulators or reset signals grant machine run permission.

## Verification and reproducibility

Native KiCad export supplies the actual connected netlist and ERC result. The independent assembly validator reconstructs the complete expected union of each source netlist, checks every pin/reference/value/MPN/footprint and rejects unknown aliases, joined returns, changed sources, omitted parts and duplicate pin identities. Each source block also has its own connection and fault-mutation checks. Numerical tests exercise limits and deliberately invalid assumptions separately from the circuit connectivity.

The combined result has zero ERC errors and exactly22 expected isolated-substrate warnings identified by their original label UUID, type, severity and text. Standard ignored categories are retained in the raw ERC record. This is not 'zero ERC violations' and it does not replace PCB DRC or an isolation layout review.

The [scoped test log](connected-hardware-20260928/tests.txt), [review](connected-hardware-20260928/review.json) and [before/copy/after identities](connected-hardware-20260928/source-inventory.json) preserve the exact checked source snapshot. The older46-test power-protection and290-test implementation archives remain separate historical milestones. No old runtime/synthesis evidence is relabeled as a new test of these circuits.

Rebuild source blocks with their tools/hardware_build_* scripts, export their XML netlists and ERC using KiCad10, then run:

```powershell
python tools/hardware_build_assembly.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o hardware/controller_assembly/netlist.xml hardware/controller_assembly/controller_assembly.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json -o hardware/controller_assembly/erc.json hardware/controller_assembly/controller_assembly.kicad_sch
python tools/hardware_validate_assembly.py
python tools/hardware_check_connected.py --evidence-dir reports/connected-hardware-NEW-REVISION
```

The final command refuses to overwrite an existing evidence directory and rejects changed inputs, empty test modules or skipped tests. It copies the exact circuit/code inputs, independently re-exports all eleven schematics with native KiCad to bind the tested XML/ERC to the drawings, and runs the scoped Python tests from that copied snapshot in a separate process. Rebuilding generated drawings can replace manual edits: preserve them first. Re-export and visually inspect the PDF after any drawing change.

## Work still required for an actual controller

1. Exact compute/FPGA/ESP package and supply connections, oscillator/configuration/debug, bank/pin mapping and physical link. The current software/RTL checks do not establish device routing, bitstream or real-time operation on the chosen host.
2. Independent machine permission/watchdog/restart latch, complete protected field outputs, analog spindle/process interfaces, and power-off/partial-power line behavior. Raw reset/PGOOD signals are not an E-stop or a machine safety claim.
3. Remaining special footprints, physical fuse/clamp and connector selection, full PCB layout, thermal/current/creepage constraints, DRC and reviewed assembly/test files.
4. Full fitted-parts sourcing and PCBWay turnkey quotations, including test, yield, enclosure, compute, display, power and packaging for each screen tier. The7/10/12/14/18/21-inch family remains the product requirement; no single large screen is forced into every price.
5. Engineering-prototype measurements: actual power/transient/short/brownout, Linux/graphics latency and motion link, machine I/O, thermal/EMC and deliberate recovery. These require hardware after the pre-order design gates; source tests cannot supply their evidence.
6. Complete product UI/CAD import, guided wiring/commissioning, production configuration/cartridge drivers and optional accessory/AI behavior against the actual hardware. Existing diagnostic firmware and disconnected service demos retain their documented scope.

No purchase, supplier submission, board layout or fabrication release was made by this milestone.
