# Motherboard parts/cost audit — 30 September 2026

The latest audited schematic source has **701 physical footprints, 699 fitted parts, two DNP MPG termination footprints and 74 exact BOM MPNs**. It remains an incomplete one-motherboard source, with missing circuits/connectors and no complete routed PCB or PCBWay quotation. **A complete manufactured board or controller-kit cost is unknown.**

| Build quantity | Priced fitted inventory value, batch | Per board, priced parts only | Catalogue purchase cash incl. MOQ excess, batch | Unpriced MPNs / fitted pieces |
|---:|---:|---:|---:|---:|
| 1 | $246.87 | $246.87 | $11,413.33 | 13 / 85 |
| 10 | $1,938.67 | $193.87 | $12,803.27 | 13 / 850 |
| 100 | $16,999.02 | $169.99 | $24,845.02 | 13 / 8,500 |

These are partial **USD catalogue calculations**, with 61 priced exact MPNs. Fitted inventory value and purchase cash are deliberately separate. The original 1k/10k PLT precision resistor lots require 1,000 each and **$11,200 minimum known purchase cash**; eight other PLT values still have unknown prices/order acceptance. Catalogue stock is unreserved, sometimes zero/insufficient, or unknown. No complete available basket is inferred.

The final source is frozen in [final-701](final-701/README.md): [222 quantity rows](final-701/MOTHERBOARD_COST.csv), [full costing/null exclusions](final-701/MOTHERBOARD_COST.json), [parts/package review](final-701/PARTS_SOURCING_REVIEW.json), [42 frozen input hashes](final-701/snapshot.json), [issued artifact hashes](final-701/receipt.json) and [independent verification](final-701/verification.json). Final here means the latest cost receipt in this task; it does not mean a finished board.

The initial 685-physical/683-fitted source is separately retained in [initial-685-review-v2](initial-685-review-v2/README.md), with 54 priced / 15 unpriced MPNs and 207 quantity rows. Its priced fitted inventory totals were $184.88 / $1,433.26 / $12,657.06 at 1/10/100. [Exact snapshot comparison](SNAPSHOT_COMPARISON.json) records the source changes. Price coverage also changed, including 24 already present photorelay parts now using Toshiba's verified orderable spelling, so the cost difference does not equal the cost of the sixteen added physical parts.

The original `initial-685` input archive and first issued audit are preserved. Its nominal FPGA envelope description was incorrect; `initial-685-review-v2` corrects the review description to the source's **13 × 13 mm, 0.8 mm pitch**. Frozen input bytes and all cost arithmetic are identical between those initial versions. The current tool and final receipt use the corrected description.

The scoped source investigation did not support calling SN74LVC2G74 a dual/14-pin device or an invalid 8-pin footprint. Official TI data shows it is a **single DFF**, with the same DCU pin map as the separately sourced SN74LVC1G74. Nonstandard PLT resistance values are explicitly supported by Vishay; exact unquoted strings are sourcing unknowns, not proven nonexistent parts. Nexperia's inherited `74LVC1G17GW` remains a type number with an unresolved orderable suffix. The exact Murata `GRM188R71H105KA12D` appears in an official TI reference BOM; its current exact source and USD price remain unknown.

The thirteen unpriced exact MPNs are eight PLT precision values, Nexperia `74LVC1G17GW`, Samsung `CL10C332JB8NNNC`, TDK `C2012C0G2A103J125AA`, Murata `GRM188R71H105KA12D` and Vishay `SMM02040C1001FB300`. TDK's accessible CAD-only tier table and LCSC's zero-stock/reference-only MELF pricing remain separate excluded references. No currency conversion or substitute part was inserted.

Compute, ESP32, storage/settings and optional AI module SKUs are unselected and separately null. Six complete touchscreen package rows cover 7-, 10-, 12-, 14-, 18- and 21-inch classes; screen size is independent of machine I/O. PCBWay fabrication, turnkey sourcing, assembly/stencil/attrition/handling, programming, testing/fixtures/calibration, cooling/PSU/enclosure/harnesses, freight/tax/tariff and packaging/warranty/support are individually unknown at all three quantities. Omitted source circuits have unknown part counts and costs; they are not treated as free.

Verification passed **207 initial + 222 latest quantity rows**, with **11 initial + 9 latest negative controls** covering DNP purchase mistakes, missing MOQ cash, borrowed/zero unknown prices, unsupported volume discounts, inventory shortfalls, invented module costs, false complete totals and FPGA package metadata. All frozen input/issued output hashes pass. Nominal package-family coverage is 74/74 for the latest receipt; this is distinct from full pad/pin/orientation/mechanical verification.

Reproduce read-only checks:

```powershell
C:/Python314/python.exe -X utf8 reports/motherboard-cost-20260930/verify_cost_receipt.py initial-685-review-v2
C:/Python314/python.exe -X utf8 reports/motherboard-cost-20260930/verify_cost_receipt.py final-701
```

For a newly stable parent source, use `tools/motherboard_cost_audit.py freeze <new-id>`, then `audit <new-id> --observations <versioned-ledger>`. Both commands refuse to replace issued evidence. This audit changed no hardware/CAD, made no supplier contact or order, and claims no native ERC/DRC, target compilation, synthesis or physical measurement.
