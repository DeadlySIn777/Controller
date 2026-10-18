# Independent watchdog and permission sources

Read 28 September 2026. Primary PDFs are retained locally; the validator hashes these copies. Exact order codes are engineering candidates. No inventory, price, supplier submission or manufacture claim is made.

| Source | Pages and use | Local file |
| --- | --- | --- |
| [TI TPS3431 Rev A](https://www.ti.com/lit/ds/symlink/tps3431.pdf) | pp3–6 pin/functions and electrical/timing conditions; pp10–14 falling-edge WDI, ENOUT/WDO, auto-release, timer equation and tested capacitor range; p29 DRB0008A land pattern; order appendix TPS3431SDRBR | `tps3431.pdf` |
| [TI SN74LVC2G74 Rev Q](https://www.ti.com/lit/ds/symlink/sn74lvc2g74.pdf) | pp3/5–7 DCU8 physical pins, Q pin5 versus inverted Q pin3, asynchronous clear/preset, recovery and pulse constraints, Ioff and drive limits | `sn74lvc2g74.pdf` |
| [TI SN74LVC2G08 Rev N](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf) | p3 DCU8 mapping, recommended logic levels, Ioff and switching conditions; used as two separate AND gates | `sn74lvc2g08.pdf` |
| [TI SN74LVC1G11 Rev I](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf) | pp3–5 DBV6 physical map, 3-input AND, VOH/VOL and Ioff; two fitted parts | `sn74lvc1g11.pdf` |
| [TI SN74LVC1G34 Rev O](https://www.ti.com/lit/ds/symlink/sn74lvc1g34.pdf) | pp3/5–6 DBV5 pin map and <=100uA VCC−0.1V output-high guarantee, used before the watchdog's 0.8×VDD WDI input | `sn74lvc1g34.pdf` |
| [TI SN74LVC2G17 Rev N](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf) | pp3/5–6 DBV6 pin map, Schmitt input tables, Ioff, output current and timing; consumes the two open-drain signals | `sn74lvc2g17.pdf` |
| [Murata GRM1885C1H121JA01](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM1885C1H121JA01-01A-EN_PDF_CERAMICCAPACITORSMD) | p2 120pF/50V/C0G/5%/0603 and D packaging; p6 low-temperature change limits; solder, humidity and endurance tests have distinct conditions | `watchdog-cap.pdf` |

The waveform/page interpretation also used the existing Efinix and power-sequence sources, without changing them. Frozen copies of the actual endpoint RTL and its protocol are included in `hardware/machine_permission`; their six-channel implementation remains historical baseline evidence, while the new product requirement is eight motors with expansion to twelve.

Rejected or comparison-only local TI PDFs: SN74LVC08A (no suitable Ioff statement in the inspected part's limit table), SN74HCS08 (supply-relative clamps and different drive/threshold evidence), SN74LVC1G97 (did not simplify the selected circuit). They are not fitted parts.

[TPS3435 Rev A](https://www.ti.com/lit/ds/symlink/tps3435.pdf) was inspected through the web tool only: its nominal20ms example in Table4-1 is labelled product preview and uses a latched output released by a WDI falling edge. That behavior does not directly replace the selected auto-release recovery path. No local TPS3435 PDF hash is claimed.

Important source qualifications: TPS3431's table and prose conflict below its normal operating minimum regarding WDO; ENOUT is therefore included, and arbitrary low-supply behavior remains unqualified. Its VOL condition is VDD=5V/3mA, not a new guaranteed 3.3V measurement. Schmitt thresholds are tabulated at discrete supply points, so use at3.2–3.4V retains an explicit characterization gate rather than inventing a continuous guaranteed threshold curve. The 100pF tested capacitor minimum motivated120pF nominal after tolerance. The headline typical timing accuracy is not used as the worst-case limit.
