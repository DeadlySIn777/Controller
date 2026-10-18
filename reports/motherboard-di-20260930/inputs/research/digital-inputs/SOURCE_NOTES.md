# Baseline digital-input sources — 2026-09-28

Downloaded official PDFs are archived with hashes in `sources.json`; text extracts and images are reading aids. Online-only sources explicitly have no archived source-byte hash. No purchase, supplier inquiry or stock commitment was made.

| Primary source | Use and qualification boundary |
|---|---|
| [TI ISO1211/ISO1212 datasheet](https://www.ti.com/lit/ds/symlink/iso1212.pdf), Fig4-2, §5.9/5.10, Table7-2, §8.2.1/8.4 | Exact 16-pin ISO1212 map, powered/open-input behavior, undetermined unpowered output, thresholds/current ranges, filter/resistor topology and separate floating SUB islands. Pin page, threshold table and application drawing were visually inspected. Header says RevG February2025 while revision history says January2026; archived bytes identify the actual source. |
| [TI ISO1212EVM guide SLLU254A](https://www.ti.com/lit/ug/sllu254/sllu254.pdf), BOM | Exact ISO1212DBQR, SMM02040C1001FB300 threshold resistor, CRCW0603562RFKEA sense resistor and 06033C104JAT2A logic bypass. The EVM uses different input capacitors/configurations; its measurements are not transferred to this board. |
| [TI TIDA-01508 guide TIDUDI8](https://www.ti.com/lit/ug/tidudi8/tidudi8.pdf) | Reference implementation/context only. Its 16-channel scope and EMC tests are not claims for this 22-channel design. |
| [Vishay SMM0204](https://www.vishay.com/docs/20004/smm0204.pdf) | Selected C-code 50ppm/K, F-code 1% and 1kohm value; 200V working-voltage family, 0.25W standard-operation screen. Its pulse curves still need evaluation against actual assembled surge/EFT waveforms and repetition; wattage alone is insufficient. |
| [Vishay CRCW](https://www.vishay.com/docs/20035/dcrcwe3.pdf) | Sense/bias resistor family, 1% and 100ppm/K; conservatively use 0.1W for 0603 with 75V rating. Temperature and lifetime drift remain in the qualification plan. |
| [TDK C2012C0G2A103J125AA](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012C0G2A103J125AA), [characterization sheet](https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/charasheet/c2012c0g2a103j125aa.pdf) | Exact 10nF +/-5%, 100V, C0G +/-30ppm/C, 0805 filter candidate. C0G reduces the DC-bias/temperature uncertainty of a Class-II input filter; full tolerance and assembled timing remain to measure. Characterization plots are typical data, not guaranteed timing evidence. |

TI's published table lists a 2.05-2.75mA active-input current range under its stated 562ohm +/-1% conditions below 30V at SENSE; the smaller 2.2-2.47mA headline range is labelled typical across temperature. The design does not substitute that headline for the maximum.

TI specifies about 2x2mm floating copper for each SUB pin and forbids connection to other substrate/ground/signal nets. These are layout requirements, not extra fitted BOM parts. The 22 single-pin net warnings are retained and enumerated independently by reference/pin/net/UUID.

The reference surge arrangement limits total field-ground coupling to other potentials, including PE. This controller's complete supplies, other isolation paths, shielding and external wiring have not been measured. No PE capacitor is added here and no reference EMC level is claimed for the product.
