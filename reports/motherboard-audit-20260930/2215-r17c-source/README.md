# Actual motherboard population audit

**2215 physical footprints; 2179 purchased fitted parts; 33 bare PCB test pads; 1 bare chassis pad.** Function rows are exclusive and already include their passives. Fitted geometry includes bare pads; these have no purchased part or assembly placement. The material composition is separate; it is not added to the total.

| Function | Footprints | Fitted |
|---|---:|---:|
| 12 motor interfaces and source buffers | 350 | 350 |
| 24 digital inputs | 120 | 120 |
| 16 smart outputs | 110 | 110 |
| Four encoders / frequency / MPG receivers | 28 | 26 |
| FPGA rails and motor receiving-rail monitors | 116 | 116 |
| FPGA / configuration flash / clock / support | 70 | 70 |
| Watchdogs / permission / deliberate-control bridges | 91 | 91 |
| I/O acquisition and control | 100 | 100 |
| Probe / pendant / fast-port supplies | 198 | 198 |
| Protected power entry / distribution | 220 | 220 |
| PWM / process contacts and acquisition | 118 | 118 |
| Analog / communications | 309 | 309 |
| LED indicators | 0 | 0 |
| Sensor power / XS1 field and acquisition | 176 | 176 |
| Field headers / chassis coupling | 44 | 44 |
| Compute / ESP / storage socket circuits | 165 | 165 |
| **Total** | **2215** | **2213** |

Resistors 1020; capacitors 642; diodes including TVS 67: **1729 footprints (78.059%)**. Remaining reference classes: F: 3, H: 1, J: 48, L: 6, Q: 3, TP: 33, U: 391, Y: 1.

No physical DIN/H15/har-bus card/backplane connector, rack identity EEPROM or duplicate Linux/ESP processor is in this BOM. Legacy MIA/MX4/card names remain on some internal nets; those names do not represent fabricated cards. Exact source buffers and permission gates still need their electrical review.

**Actual compute socket count: 2; ESP socket rows: 2; storage sockets: 1.** Socket circuitry is credited only where physically drawn. Purchased modules remain separate procurement items; interchangeable-module images, mechanical/thermal and powered qualification remain unfinished. Every implemented source is credited only by its exclusive row; zero-count rows remain absent. Actual terminal source does not prove edge access, mating clearance or copper connectivity. Freezing this as a complete controller would preserve missing circuitry and routing.

10 actual converter/LDO devices and 8 LTC2962 devices serve distinct rails, receiving banks or isolated post-limiter supplies. Repeated active MPNs, their exact references, domains and roles are included in review.json. Equal MPNs are not proof of removable duplication. No rack-only regulator/supervisor has been proved removable. Current/load/startup and temperature budgets still need reconciliation.

U5004 uses one octal-buffer channel and is a possible single-channel Ioff substitution. It is not yet an electrically/mechanically/procurement-qualified saving. Four duplicate DO default resistors are removed in the reviewed I/O-control source; the consolidation is integrated here only if the function table includes that source block.

The audit found and corrected a real new watchdog-clear conflict: 33 Ω branches had targeted U4019 push-pull outputs. They now target U4018 WD_REARM_M/O inputs, active-high/default-low, retaining power-reset qualification. The erroneous source is archived separately. Native pin parity alone did not catch this topology defect.

Routing continues only after the missing existing-required circuits and these real electrical issues are reconciled. No new capability or rack architecture is authorized. Prototype measurements, vendor FPGA fit and manufacturing cost remain separate evidence gates.
