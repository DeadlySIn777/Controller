# Incomplete motherboard source: exact-MPN component cost

30 September 2026; USD; `initial-685`. **685 physical footprints / 683 fitted parts / 2 DNP footprints / 69 exact BOM MPNs.**

These totals are a partial catalogue basket for this immutable schematic snapshot. Omitted circuitry, unpriced parts, commodity modules and all PCBWay manufacture costs remain unknown. They are not a complete board price, available procurement basket, turnkey quote or selling price.

| Boards | Qty-matching priced subtotal | Priced fitted inventory value | Catalogue purchase cash incl. excess | Unpriced MPNs / fitted pieces |
|---:|---:|---:|---:|---:|
| 1 | $151.34 | $184.88 | $11351.34 | 15 / 109 |
| 10 | $1097.86 | $1433.26 | $12297.86 | 15 / 1090 |
| 100 | $9303.06 | $12657.06 | $20503.06 | 15 / 10900 |

Fitted inventory value allocates the price of consumed parts at the applicable purchase tier. Purchase cash includes unused MOQ inventory. Neither proves delivery or design qualification. The two inherited PLT 1k/10k T1 lots require **$11,200 minimum known cash**, with prices of $5.63/$5.57 per piece at 1,000 each. The eight unpriced PLT strings also use the manufacturer's T1 packaging syntax; their unit prices and order acceptance are unknown.

R7015/R7016 MPG termination footprints are DNP in the initial source model and are excluded from purchasing even though the old CSV lacked a DNP column. Their physical footprints remain in counts. Subsequent receipts use their own frozen DNP states.

[All quantity rows](MOTHERBOARD_COST.csv), [complete calculation and exclusions](MOTHERBOARD_COST.json), [exact observed price evidence](CATALOGUE_OBSERVATIONS.json), [part sourcing/package screen](PARTS_SOURCING_REVIEW.json), [input hashes](snapshot.json) and [issued artifact hashes](receipt.json).

## Sourcing and package findings

The nominal footprint-family screen is distinct from full IC pin/land/orientation verification. It preserves exact source MPNs and never infers suitability merely from a quote.

- **74LVC1G17GW**: Manufacturer type number is valid SOT353-1, but exact orderable suffix is unresolved; official Nexperia lists 74LVC1G17GW,125. No unapproved suffix normalization.
- **C2012C0G2A103J125AA**: Exact 0805/100V/C0G/5% product confirmed; accessible detailed primary price is CAD. No inferred currency conversion or substitute tolerance price used.
- **CL10C332JB8NNNC**: Manufacturer validates exact Samsung part; no current purchasable primary USD offer verified. LCSC reference-only/out-of-stock excluded.
- **GRM188R71H105KA12D**: Exact name occurs in official TI TIDA-01464 BOM (1uF/50V/X7R/0603); present manufacturer/orderable catalogue and USD price not verified. Different KAALD suffix is not substituted.
- **ISO1212DBQR**: Nominal DBQ family fits both source libraries. Initial six motor parts still use generic SSOP land pattern; twelve DI parts use reviewed exact TI DBQ0016A geometry. Full native land/pin verification is separate hardware evidence.
- **PLT0603Z1001LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z1002LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z1071LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z1151LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z2610LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z3160LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z5452LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z5752LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z8792LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z9212LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **SMM02040C1001FB300**: Exact MiniMELF is documented in TI ISO1212 EVM BOM. LCSC's accessible USD tiers are reference-only with zero stock; selected purchasable offer remains unknown.
- **SN74LVC2G74DCUR**: TI SCES203Q confirms SINGLE 8-pin DFF with CLK1,D2,/Q3,GND4,Q5,/CLR6,/PRE7,VCC8. SN74LVC1G74DCUR uses the same pin map. '2G' does not imply dual; no invalid-package assertion is supported here.
- **TLP3640A(TPL,E)**: Inherited source adds a final ')' while distributor manufacturer-product-number strings omit it. Exact procurable ordering-code equivalence requires explicit manufacturer evidence; alternate punctuation offer is not applied automatically.
- **TLP4176A(TP,F)**: Inherited source adds a final ')' while distributor manufacturer-product-number strings omit it. Exact procurable ordering-code equivalence requires explicit manufacturer evidence; alternate punctuation offer is not applied automatically.

The 2G74/1G74 package and pin-map finding is supported by [TI SCES203Q](https://www.ti.com/lit/ds/symlink/sn74lvc2g74.pdf) and [TI SCES794G](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf). The [Vishay PLT ordering specification](https://www.vishay.com/docs/60030/plt.pdf) permits nonstandard resistance values and specifies T1's 1,000-piece minimum/multiple. The [Nexperia ordering list](https://www.nexperia.com/chemical-content/74LVC1G17GW.html) separates type number from orderable suffix. [TI TIDA-01464 BOM](https://www.ti.com.cn/lit/pdf/TIDRTP7) records the otherwise unverified exact Murata 1uF name.

## Unpriced exact MPNs

- `74LVC1G17GW`: 1 fitted/board; cost unknown.
- `C2012C0G2A103J125AA`: 36 fitted/board; cost unknown.
- `CL10C332JB8NNNC`: 2 fitted/board; cost unknown.
- `GRM188R71H105KA12D`: 2 fitted/board; cost unknown.
- `PLT0603Z1071LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z1151LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z2610LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z3160LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z5452LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z5752LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z8792LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z9212LST1`: 1 fitted/board; cost unknown.
- `SMM02040C1001FB300`: 36 fitted/board; cost unknown.
- `TLP3640A(TPL,E)`: 12 fitted/board; cost unknown.
- `TLP4176A(TP,F)`: 12 fitted/board; cost unknown.

## Stock is a separate constraint

All observed inventory is dated, unreserved catalogue evidence. A price can exist with zero or insufficient stock. Future expected receipts are not treated as available. The original three LTC2962HUD#PBF demand is 3/30/300; its recorded 71 pieces leave a 229-piece shortage at 100 boards. Unknown stock stays null.

| Boards | Priced MPNs short of purchase quantity | Priced MPNs with unknown stock | Stock-qualified complete basket |
|---:|---:|---:|---|
| 1 | 6 | 7 | Unknown |
| 10 | 6 | 7 | Unknown |
| 100 | 8 | 7 | Unknown |

## Separate modules and complete kit costs

No exact compute, ESP32, storage/settings or optional AI module SKU is selected here. Their price and purchasing quantity remain unknown. Complete touchscreen assemblies in the 7-, 10-, 12-, 14-, 18- and 21-inch classes remain six explicit independent package rows, including touch controller, interface, cable, power and mounting costs. Screen size never changes the motherboard I/O/channel scope.

PCBWay fabrication/stackup/finish/impedance/yield; accepted exact-part turnkey sourcing; assembly, stencil, setup, feeders, attrition, reeling/tube/tray/BGA inspection; programming; test/fixtures/calibration; cooling, PSU, enclosure/harness/mounting; shipping/tax/tariff; packaging/warranty/support all remain individually null at 1/10/100. No quote has been requested and no files uploaded. The optional Coilcraft $25 leader/trailer fee per inductor MPN ($50 for two) remains a conditional extra, not assumed free or included.

The source also omits selected compute/ESP/storage sockets, actual field terminal mates, parent field-power/protection, DI acquisition/validity, sixteen smart DO and further analog/comms/process/expansion/status circuitry. Missing part counts and costs remain unknown, not zero. A component count or a clean schematic cannot close them.

No source hardware was changed by this audit. No native ERC/DRC, target compilation, FPGA synthesis or physical test is claimed. Receipt verification checks immutable hashes, BOM/model identity, DNP exclusion, exact-MPN arithmetic, tier/MOQ, nulls, stock and adversarial negative controls.
