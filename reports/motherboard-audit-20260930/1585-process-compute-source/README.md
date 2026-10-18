# Actual motherboard population audit

**1585 physical footprints; 1557 purchased fitted parts; 26 bare PCB test pads.** Function rows are exclusive and already include their passives. Fitted geometry includes test pads; these have no purchased part or assembly placement. The material composition is separate; it is not added to the total.

| Function | Footprints | Fitted |
|---|---:|---:|
| 12 motor interfaces and source buffers | 350 | 350 |
| 24 digital inputs | 120 | 120 |
| 16 smart outputs | 110 | 110 |
| Four encoders / frequency / MPG receivers | 28 | 26 |
| FPGA rails and motor receiving-rail monitors | 111 | 111 |
| FPGA / configuration flash / clock / support | 70 | 70 |
| Watchdogs / permission / deliberate-control bridges | 91 | 91 |
| I/O acquisition and control | 100 | 100 |
| Probe / pendant / fast-port supplies | 194 | 194 |
| Protected power entry / distribution | 220 | 220 |
| PWM / process contacts and acquisition | 116 | 116 |
| Analog / communications | 0 | 0 |
| LED indicators | 0 | 0 |
| Compute / ESP / storage socket circuits | 75 | 75 |
| **Total** | **1585** | **1583** |

Resistors 767; capacitors 445; TVS diodes 58: **1270 footprints (80.126%)**. Remaining: 267 U-reference active devices (including photorelays and power MOSFETs), 5 inductors, 1 oscillator and 26 bare copper test pads.

No physical DIN/H15/har-bus card/backplane connector, rack identity EEPROM or duplicate Linux/ESP processor is in this BOM. Legacy MIA/MX4/card names remain on some internal nets; those names do not represent fabricated cards. Exact source buffers and permission gates still need their electrical review.

**Actual compute socket count: 2; ESP socket rows: 2; storage sockets: 0.** Socket circuitry is credited only where physically drawn. Purchased modules remain separate procurement items; interchangeable-module images, mechanical/thermal and powered qualification remain unfinished. Protected power entry, probe/pendant and process circuits are credited by their exclusive rows. Analog/comms, status LEDs and physical field terminals remain unfinished. Freezing this as a complete controller would preserve missing circuitry.

Two regulators supply distinct FPGA 1.2 V and logic 3.3 V rails. Seven LTC2962 devices monitor different rails, receiving banks or isolated post-limiter supplies. No rack-only regulator/supervisor has been proved removable. Current/load/startup budgets still need reconciliation.

U5004 uses one octal-buffer channel and is a possible single-channel Ioff substitution. It is not yet an electrically/mechanically/procurement-qualified saving. Four duplicate DO default resistors are removed in the reviewed I/O-control source; the consolidation is integrated here only if the function table includes that source block.

The audit found and corrected a real new watchdog-clear conflict: 33 Ω branches had targeted U4019 push-pull outputs. They now target U4018 WD_REARM_M/O inputs, active-high/default-low, retaining power-reset qualification. The erroneous source is archived separately. Native pin parity alone did not catch this topology defect.

Routing continues only after the missing existing-required circuits and these real electrical issues are reconciled. No new capability or rack architecture is authorized. Prototype measurements, vendor FPGA fit and manufacturing cost remain separate evidence gates.
