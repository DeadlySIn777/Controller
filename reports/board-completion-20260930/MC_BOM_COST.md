# Current MC exact-MPN sourcing cost

30 September2026; USD. The parent MC r0.3 candidate contains **327 physical components /52 exact MPNs**. This is a bounded source-backed component cost sheet, with all52 lines included at1,10 and100 board builds. It is not a PCBWay quotation, complete controller cost or manufacture approval. The architecture clarification remains pending.

The active100nF Murata replacement now used41 times is included. The obsolete25V part remains historical evidence only. [Source ledger](MC_BOM_PRICE_SOURCES.json), [exact current BOM snapshot](MC_BOM_INPUT.csv), [complete data](MC_BOM_COST.json), and [CSV](MC_BOM_COST.csv) preserve the source links, piece-level tiers, actual purchase quantities and null unknowns.

| Board build quantity | Qty-matching known subtotal | Fitted inventory value of all priced parts | Actual known purchase cash, including excess | Unpriced exact MPNs |
|---:|---:|---:|---:|---:|
| 1 | $65.63 | $115.96 | $25256.08 | 10 |
| 10 | $495.71 | $998.99 | $25686.16 | 10 |
| 100 | $3933.58 | $8966.44 | $29124.03 | 10 |

**42 of52 exact MPNs have a published price**;39 can be costed at the requested piece count and3 require excess purchases. Stock or delivery availability remains unqualified even for priced lines. Fitted inventory value is an accounting allocation; use the purchase-cash column when assessing prototype cash needs. None of these partial subtotals includes the10 unpriced lines or manufacture extras.

| MOQ-constrained exact part | Used per board | Minimum purchase | Published USD/unit at MOQ | Minimum cash | Excess at1 /10 /100 boards |
|---|---:|---:|---:|---:|---:|
| [LTC2962HUD#TRPBF](https://www.digikey.com/en/products/detail/analog-devices-inc/LTC2962HUD-TRPBF/9555679) | 3 | 2500 | $5.59618 | $13990.45 | 2497 / 2470 / 2200 |
| [PLT0603Z1001LST1](https://www.mouser.com/en/ProductDetail/Vishay/PLT0603Z1001LST1?qs=fJ6SLga%2FIXDJ8RDAhm6Tzw%3D%3D) | 2 | 1000 | $5.63 | $5630.00 | 998 / 980 / 800 |
| [PLT0603Z1002LST1](https://www.mouser.com/en/ProductDetail/Vishay/PLT0603Z1002LST1?qs=sGAEpiMZZMtlubZbdhIBIEUeBStaGZjYTAgvS68eoNs%3D) | 4 | 1000 | $5.57 | $5570.00 | 996 / 960 / 600 |

LCSC lists exact LTC2962 cut quantities but stock is zero and prices are explicitly reference-only; they are retained as excluded research, not usable procurement cost. Mouser generic cut-tape controls do not override the precision-resistor minimum1000/multiple1000. Eight other PLT values have no exact primary public offer found. A different resistor tolerance or temperature coefficient requires engineering reanalysis before substitution.

All quantity tiers mean **component pieces**. For example4 TI244A devices per MC means4,40 and400 pieces: published CT tiers1,25 and250 apply, yielding$2.08,$12.96 and$104.592 respectively. The exact FPGA is **T20F256I4**; the cheaper C4 price is excluded. Cut-tape prices are used even when a cheaper reel price exists; no reel discount is applied to a small cut-tape order. No discount is inferred at an unpublished board-build quantity.

## Remaining unpriced lines

- 74LVC1G17GW: 1/board. BOM gives Nexperia base type; catalogue orderable suffix,125/115 is not specified. Cannot assign another exactMPN price.
- CL10C332JB8NNNC: 2/board. Manufacturer validates exact Samsung part; no current purchasable primary USD offer verified. LCSC reference-only/out-of-stock excluded.
- PLT0603Z1071LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z1151LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z2610LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z3160LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z5452LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z5752LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z8792LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.
- PLT0603Z9212LST1: 1/board. No exact primary USD purchase offer found. Supplier quote needed.

## Active bypass-capacitor sourcing closure

The parent recorded [MC-CAP-001](../../hardware/motion_card/component-substitutions.json): Murata **GRM188R72A104KA35D**,100nF±10%,X7R,100V,0603,1.6±0.1×0.8±0.1×0.8±0.1mm. Murata lists the nominal package, temperature range−55…125°C and terminal dimensions; DigiKey identifies it as active and offers CT. This preserves the selected nominal capacitance, dielectric, tolerance and0603 geometry while increasing the voltage rating from25V to100V. It does not establish biased capacitance, impedance, mounting/process or physical performance equivalence. [Manufacturer](https://www.murata.com/products/productdetail?partno=GRM188R72A104KA35%23), [exact active distributor offer](https://www.digikey.com/en/products/detail/murata-electronics/GRM188R72A104KA35D/702549).

The published CT tiers are1:$0.16,10:$0.087,50:$0.06120,100:$0.05320,500:$0.03980. The41/410/4100 required pieces therefore cost$3.567/$21.812/$163.18 using CT tiers10/100/500. The cheaper4000-reel price$0.02739 is not assigned to4100CT pieces; a separately quoted4000reel+100CT order could differ.

## Off-board items and manufacture extras

Linux compute, ESP32 service/recovery and optional AI modules are absent from this MC. No exact off-the-shelf module is fixed in this sourcing sheet; their separately costed lines remain null. Displays and complete screen packages across7/10/12/14/18/21-inch classes remain separate. The final board architecture, I/O/interface parts and connectors must be reconciled before this becomes a controller BOM.

PCBWay procurement, PCB fabrication, SMT/BGA assembly, stencil/setup, attrition, programming/test fixtures, cooling, input protection/PSU, enclosure, cables, shipping/tariffs/tax and warranty costs remain unknown. Coilcraft publishes$25 per MPN for leader/trailer on below-reel tape ($50 for the two inductors if selected); ordinary tape is not machine-ready, so PCBWay must specify its accepted format. No reeling or optional packaging fee is silently treated as zero.

Frozen input BOM SHA256: `e4a07baaf0eaa55697f978e361a996c37ad55e2a35802736672ddeb3b1c82d97`. Decimal arithmetic verified that purchased cash equals fitted inventory value plus excess inventory value before display rounding at all three quantities.
