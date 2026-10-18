# Actual motherboard population audit

**880 physical footprints; 878 fitted parts.** Function rows are exclusive and already include their passives. The material composition is separate; it is not added to the total.

| Function | Footprints | Fitted |
|---|---:|---:|
| 12 motor interfaces and source buffers | 350 | 350 |
| 24 digital inputs | 120 | 120 |
| 16 smart outputs | 110 | 110 |
| Four encoders / frequency / MPG receivers | 28 | 26 |
| FPGA rails and motor receiving-rail monitors | 111 | 111 |
| FPGA / configuration flash / clock / support | 70 | 70 |
| Watchdogs / permission / deliberate-control bridges | 91 | 91 |
| Analog / communications | 0 | 0 |
| LED indicators | 0 | 0 |
| Compute / ESP / storage sockets | 0 | 0 |
| **Total** | **880** | **878** |

Resistors 464; capacitors 227; TVS diodes 36: **727 footprints (82.614%)**. Remaining: 150 U-reference active devices (including photorelays and power MOSFETs), 2 inductors and 1 oscillator.

No physical DIN/H15/har-bus card/backplane connector, rack identity EEPROM or duplicate Linux/ESP processor is in this BOM. Legacy MIA/MX4/card names remain on some internal nets; those names do not represent fabricated cards. Exact source buffers and permission gates still need their electrical review.

**Compute, ESP and storage socket count is zero.** Replaceable modules are the adopted architecture but are not implemented by this 880-part schematic/PCB. Analog/comms, status LEDs, complete protected power entry, I/O control and physical field terminals also remain unfinished. Freezing this as a complete controller would preserve missing circuitry.

Two regulators supply distinct FPGA 1.2 V and logic 3.3 V rails. Seven LTC2962 devices monitor different rails, receiving banks or isolated post-limiter supplies. No rack-only regulator/supervisor has been proved removable. Current/load/startup budgets still need reconciliation.

U5004 uses one octal-buffer channel and is a possible single-channel Ioff substitution. It is not yet an electrically/mechanically/procurement-qualified saving. The separate future I/O-control candidate has four duplicate default resistors that should be removed during reviewed integration; it is not in this count.

The audit found and corrected a real new watchdog-clear conflict: 33 Ω branches had targeted U4019 push-pull outputs. They now target U4018 WD_REARM_M/O inputs, active-high/default-low, retaining power-reset qualification. The erroneous source is archived separately. Native pin parity alone did not catch this topology defect.

Routing continues only after the missing existing-required circuits and these real electrical issues are reconciled. No new capability or rack architecture is authorized. Prototype measurements, vendor FPGA fit and manufacturing cost remain separate evidence gates.
