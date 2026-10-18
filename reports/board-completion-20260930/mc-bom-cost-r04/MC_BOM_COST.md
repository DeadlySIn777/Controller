# MC r0.4 exact-MPN component pricing

30 September 2026; USD. Current MC: **327 physical components / 52 exact MPNs**. All 52 lines are included at 1, 10 and 100 board builds. These partial catalogue totals exclude ten unpriced MPNs and all manufacture extras; no complete controller, stock-covered purchase basket, PCBWay quotation or manufacture approval exists.

| Boards | Qty-matching catalogue subtotal | Fitted inventory value, priced parts | Catalogue purchase cash, including excess | Unpriced MPNs |
|---:|---:|---:|---:|---:|
| 1 | $94.31 | $127.85 | $11294.31 | 10 |
| 10 | $702.90 | $1038.30 | $11902.90 | 10 |
| 100 | $5811.68 | $9165.68 | $17011.68 | 10 |

**42 MPNs are priced: 40 match fitted demand and two require MOQ excess.** Quantity matching describes the purchase arithmetic, not availability. Some priced catalogue parts show zero stock and others have unknown stock. Stock-qualified purchase totals remain null at every quantity.

[Exact BOM snapshot](MC_BOM_INPUT.csv), [source catalogue](MC_BOM_PRICE_SOURCES.json), [complete JSON](MC_BOM_COST.json), and [all 156 quantity lines in CSV](MC_BOM_COST.csv) retain piece-tier and null data. Historical r03 artifacts were preserved unchanged; only the parent packaging substitution changes this current costing.

## Current supervisor packaging and stock

Parent MC-PACK-001 changes **U2003/U2004/U2005** to **LTC2962HUD#PBF**, H-grade UD 3 × 3 mm QFN-16 plus exposed ground pad 17, in tube packaging. The inherited schematic Value stays LTC2962HUD#TRPBF; electrical circuitry and the original child blocks remain unchanged. [ADI ordering specification](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf), [exact DigiKey offer](https://www.digikey.com/en/products/detail/analog-devices-inc/LTC2962HUD-PBF/9555593), [engineering receipt](../SOURCING_OPTIMIZATION_PROPOSAL.md).

Published tube tiers (component pieces): 1 $9.56000; 10 $7.43600; 25 $6.90640; 121 $6.26033; 363 $5.95245; 605 $5.83864; 1,089 $5.72638. Supplier MOQ/multiple are 1/1; the manufacturer standard package of 121 is not an order minimum. Packaging below the standard package may change through distributor services.

| Boards | Supervisor demand | Selected piece tier | Catalogue subtotal | Observed stock | Required stock shortfall |
|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 1 | $28.68 | 71 | 0 |
| 10 | 30 | 25 | $207.19 | 71 | 0 |
| 100 | 300 | 121 | $1878.10 | 71 | 229 |

The 71 observed supervisors are unreserved and cover only the 3- and 30-piece demand for this one line. **300 pieces exceed observed stock by 229; $1,878.10 is a published-price calculation, not an available 100-board supply.** No full-build availability is inferred from this line. Delivery, tube handling, assembly fees, shipping, tariffs and tax remain unknown.

## Remaining MOQ excess

| Exact MPN | Per board | MOQ/multiple | USD/unit at MOQ | Minimum cash | Excess at 1 / 10 / 100 boards |
|---|---:|---:|---:|---:|---:|
| [PLT0603Z1001LST1](https://www.mouser.com/en/ProductDetail/Vishay/PLT0603Z1001LST1?qs=fJ6SLga%2FIXDJ8RDAhm6Tzw%3D%3D) | 2 | 1000/1000 | $5.63 | $5630.00 | 998 / 980 / 800 |
| [PLT0603Z1002LST1](https://www.mouser.com/en/ProductDetail/Vishay/PLT0603Z1002LST1?qs=sGAEpiMZZMtlubZbdhIBIEUeBStaGZjYTAgvS68eoNs%3D) | 4 | 1000/1000 | $5.57 | $5570.00 | 996 / 960 / 600 |

The original PLT precision-resistor requirements are retained. No conditional lower-cost resistor proposal is applied. Eight other PLT values remain unpriced; generic cut-tape selectors do not waive the two listed 1,000-piece lot constraints.

## Ten unpriced exact MPNs

- **74LVC1G17GW**, 1/board: BOM gives Nexperia base type; catalogue orderable suffix,125/115 is not specified. Cannot assign another exactMPN price.
- **CL10C332JB8NNNC**, 2/board: Manufacturer validates exact Samsung part; no current purchasable primary USD offer verified. LCSC reference-only/out-of-stock excluded.
- **PLT0603Z1071LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z1151LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z2610LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z3160LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z5452LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z5752LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z8792LST1**, 1/board: No exact primary public USD offer verified; cost remains null.
- **PLT0603Z9212LST1**, 1/board: No exact primary public USD offer verified; cost remains null.

## Separate modules and manufacture extras

Linux compute, ESP32 service/recovery, optional AI and complete touchscreen packages for 7-, 10-, 12-, 14-, 18- and 21-inch classes and further qualified sizes are absent from this MC. Their exact parts, quantity and cost remain separate null lines; display size does not change motion-channel scope. Required omitted interfaces, connectors and final architecture also remain unfinished.

PCBWay sourcing, bare PCB/stackup, assembly/stencil/setup/attrition, feeders/reeling/tube handling, programming/test fixtures, calibration, cooling, protection/PSU, enclosure, harnesses, shipping/tariffs/tax, packaging and warranty remain unknown. The optional Coilcraft leader/trailer charge is $25 per MPN ($50 for two); accepted assembly format is unquoted and no packaging fee is assumed zero.

The active Murata GRM188R72A104KA35D replacement remains 41 pieces per board. All other offers are retained from the dated r03 source catalogue. Full-reel prices are not credited to cut-tape quantities, discounts are not interpolated, and fitted inventory value is not substituted for purchasing cash.

Frozen current BOM SHA256: `af349fe5aa00e3cf0363d4a95070c405dde18e691efc77130431aaadcc6077e1`. Decimal arithmetic confirms purchasing cash equals fitted inventory value plus excess inventory value before display rounding at all quantities. This task did not change source, rerun native ERC/DRC, compile targets or make physical measurements.
