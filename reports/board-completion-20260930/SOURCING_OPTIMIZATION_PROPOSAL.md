# Power sourcing optimization proposal — SOURCING-OPT-r0.1

Date: 2026-09-30. This is a read-only engineering and procurement proposal against the 327-component MC r0.3 BOM. No component, circuit, schema, frozen interface, supplier cart, or order was changed. The original r0.3 cost files remain intact. Numerical arithmetic, manufacturer source review, stock observations, target validation, and physical qualification are distinct evidence classes.

The strongest immediate substitution is **MC-PACK-001: `LTC2962HUD#TRPBF` → `LTC2962HUD#PBF` at U2003/U2004/U2005**. It changes the shipping package, preserves the electrical component and H temperature grade, and removes the 2500-piece pilot purchase requirement. Every resistor substitution remains a proposal; the parent explicitly deferred applying them because drift qualification is incomplete.

## 1. Exact LTC packaging equivalence and purchase quantities

The manufacturer's order table places both exact order codes on the same H-grade row: part marking LGZZ, UD 16-lead 3 × 3 mm QFN, operating range −40 to +125°C. The common pin diagram has the same 16 numbered leads and exposed pad17. Neither supply configuration, threshold mode, timing, schematic pin function, footprint, nor reset output type changes. The existing source grounds DVCC, uses the open-drain reset mode, and ties RT to CORE_5V; those conditions are unaffected. Both order codes use the same electrical-characteristics and package sections. The grade is identified on the shipping-container label; LGZZ alone cannot distinguish H from other grades. This review does not infer a new IC lifetime/endurance guarantee from a packaging suffix. [ADI datasheet, pp.2–4 and18](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf).

Authorized distributor DigiKey lists the exact #PBF item as Tube with a one-piece published tier and **71 pieces in stock at observation**. Demand is three devices per board. The published minimums are1/10/25/121/363/605/1089; prices are respectively $9.56/$7.436/$6.90640/$6.26033/$5.95245/$5.83864/$5.72638. Quantity below the standard package may be repackaged by DigiKey. Any PCBWay tube/tray handling or feeder preparation charge remains unquoted. [Exact DigiKey #PBF offer](https://www.digikey.com/en/products/detail/analog-devices-inc/LTC2962HUD-PBF/9555593).

| Board build | Exact supervisor demand | Selected published tier | Unit USD | Extended published USD | Observed stock covers demand? |
|---|---:|---:|---:|---:|---|
| 1 | 3 | 1 | 9.56000 | 28.68 | Yes, for this changed line only |
| 10 | 30 | 25 | 6.90640 | 207.19 | Yes, for this changed line only |
| 100 | 300 | 121 | 6.26033 | 1,878.10 | **No:229-piece shortfall** |

The100-board price is a published price reference, **not an available purchase total**. No replenishment, allocation, incoming stock, delivery date, quantity discount beyond the table, quotation, contact, or order was assumed. Remaining BOM-line availability is not established by these three offers.

## 2. Divider model and independently rerun bounds

`sourcing-optimization-proposal/analyze.py` derives the circuit equation from node current balance and independently enumerates each resistor, comparator threshold, and input-current corner. It imports no project validator and reads no generated expected analytical result. It checks fifteen authored nominal resistor values against both the source manifest and native XML netlist. Fourteen are precision resistors; the4.02Ω series correction stays an ordinary1%/100ppm component.

For the positive rail divider, the UV +ADJ and polarity-reversed OV −ADJ inputs use:

`Vrail_trip = Vthr × (1 + sum(Rtop)/Rbottom) + Imon × sum(Rtop)`.

Each input has a separate divider; an extra REF tolerance is not added to this equation. PG1 is tied to REF to select +ADJ; PG2 is grounded to select the opposite comparator polarity. The calculation uses the existing `Vthr=0.4975…0.5025V` and `Imon=−15…+15nA` assumptions. Those are full-temperature rows in the ADI table, whose stated default supply condition is **VCC=3.3V**. The actual board uses CORE_5V for the monitor supply. These calculations therefore reproduce and tighten the existing static model; **they do not establish an all-supply guarantee absent further evidence for the threshold/bias bounds at the actual supply**. Typical curves are not used as guaranteed replacement limits. [ADI datasheet, pp.3–4 and14–17](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf).

Each resistor's initial tolerance, TCR excursion, and additional drift are combined with a conservative symmetric envelope of compounded fractional errors. Series resistors receive independent corners; no matching or tracking credit and no RSS are used. The existing PLT reference is25°C with a100K maximum excursion to125°C; new Vishay TNPW/TNPU candidates use their20°C TCR test reference with105K to125°C. The original0.01%/5ppm parts have a fresh envelope of600.05ppm, rather than truncating the multiplication to600ppm. The400ppm case remains an additional sensitivity allowance, not a lifetime promise. [PLT source](https://www.vishay.com/docs/60030/plt.pdf), [TNPW source, pp.2–4 and12–15](https://www.vishay.com/docs/28758/tnpw_e3.pdf), [TNPU source](https://www.vishay.com/docs/28779/tnpue3.pdf).

The unchanged nominal divider chains are:

| Rail | UV top Ω | OV top Ω | Bottom Ω | Allowed rail V | Regulation-only interval V |
|---|---|---|---:|---|---|
| CORE_5V | 87,900 | 92,100 | 10,000 | 4.85–5.15 | 4.95–5.05 |
| CORE_1V2 | 1,070+261 | 1,150+316+4.02 | 1,000 | **1.15–1.25** | 1.185–1.215 |
| IO_3V3 | 54,500 | 57,500 | 10,000 | 3.20–3.40 | 3.25875–3.34125 |

The1.2V limits remain the actual T20 operating limits. The historical1.17–1.23V ledger is not substituted for them. Regulation-only intervals do not cover ripple, load transients, ground drop, or incomplete startup.

Acceptance requires four strictly positive margins, in order: UV_min−rail_min; regulation_min−UV_max; OV_min−regulation_max; rail_max−OV_max. The detailed JSON records every bound, all four margins, and all2,560 evaluated arithmetic corners with a second monotonic closed-form check.

## 3. Decisions from the calculations

**Blanket0.1%/10ppm is rejected.** Fresh CORE_5V OV can reach5.150932973V, beyond5.15V. Fresh IO_3V3 UV can be as low as3.196959611V and OV as high as3.404616134V, outside3.2–3.4V. Keeping nominal values does not preserve qualification when resistor uncertainty increases.

**Blanket0.05%/10ppm is also rejected.** Fresh IO_3V3 UV can fall to3.199663675V and OV rise to3.401712848V. Replacing only all six bottom resistors with this class passes fresh arithmetic, but fails the400ppm case: IO_3V3 OV reaches3.401282837V. Four top nominal values—54.5k,57.5k,87.9k,92.1k—are outside E96; no exact in-stock cheaper E96 offer is invented for them.

**The two core1k bottom resistors are the strongest selective tolerance candidate.** `TNPW06031K00BYEA` is1k,0603,0.1%,10ppm, lead-free, cut-tape MOQ1. The observed offer has1,026 pieces, $0.60 at qty1 and $0.497 at qty10. R2047/R2055 could retain their1k nominal values and existing footprint in a separately authorized source revision. Fresh and400ppm arithmetic pass; the core400ppm UV interval is1.157372220–1.173662060V and OV1.226256307–1.243802128V, with minimum core margin6.197872mV. A conservative sensitivity combining the candidate's solder-heat and1000-hour general-mode test allowances with the400ppm allowance also passes static arithmetic. This does not qualify assembly, environment, or product lifetime. **No resistor was changed.** [Exact 1k offer](https://www.digikey.com/en/products/detail/vishay-dale/TNPW06031K00BYEA/18891209).

**An alternate10k precision part addresses the MOQ without degrading fresh tolerance.** `RNCF0603TKY10K0` is10k,0603,0.01%,5ppm,0.1W, lead-free. The offer lists71,206 pieces, cut tape MOQ1 and $1.61 at qty1/$1.334 at qty10. Its dimensions fall in the1608 package class of the existing resistor lands, but actual solder-land/assembly acceptance remains a PCB qualification item. It is a potential replacement for R2027/R2035/R2067/R2075; it is **not applied or lifetime-qualified**. [Exact offer](https://www.digikey.com/en/products/detail/stackpole-electronics-inc/RNCF0603TKY10K0/2269698), [manufacturer RNCF table](https://www.seielect.com/catalog/sei-rncf.pdf), [manufacturer datasheet mirrored by Mouser](https://www.mouser.com/datasheet/2/385/SEI_RNCF-3077647.pdf).

RNCF's fresh and400ppm arithmetic match the original bottom-resistor class. However, the manufacturer's ≤0.05%-tolerance endurance and solder-heat test allowances are each500ppm. Conservatively combining both with400ppm makes IO_3V3 UV3.199935488V and OV3.401429172V; both safety margins fail. Temperature cycling permits a still wider change. Calling it a drop-in lifetime-qualified substitute solely because its initial tolerance matches would be incorrect. Post-assembly and environmental evidence or a revised independently qualified divider design is required before freezing that substitution.

## 4. Startup and metrology limits

ADI deliberately uses glitch filtering rather than intentional comparator hysteresis. The same static UV/OV bounds therefore define where all devices can accept the rail; reset release occurs only after the rail remains valid and manual-reset conditions are released. With RT tied to VCC, the table specifies160–240ms per stage; three sequential stages account for480–720ms of timer delays. Configuration begins when VCC reaches its configuration level (2.2V maximum); approximately500µs is typical, not a guaranteed maximum. Converter ramp, input charging, transient overshoot, partial power, and actual rail loading remain separate qualifications. The40µs comparator propagation maximum is specified at10% overdrive; it cannot establish the20ms machine-fault bound for arbitrary tiny threshold crossings. None of these packaging/resistor cost calculations changes or proves that full-system timing bound. [ADI timing/configuration details](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf).

The400ppm original static IO_3V3 OV safety margin is only1.475423mV at the rail. Layout drop, leakage, regulator transients, test loading and measurement uncertainty require their own budgets; they are not included in this number. A10MΩ voltmeter/probe connected to a10k sense-node bottom adds a shunt and moves nominal IO_3V3 UV/OV thresholds upward by2.725/2.875mV, respectively. The exact nominal shift is `0.5 × Rtop/Rprobe`. This is already larger than the remaining OV margin. Test the rail trip externally with sense nodes unloaded, or explicitly account for probe impedance, leakage, capacitance, ground reference, and instrument uncertainty. A practical calibrated fixture must guard-band threshold measurements by its stated voltage accuracy and by the unresolved temperature/supply/ground contributions; no assumed meter accuracy is invented here.

## 5. Cost consequences, without changing current costing

| Case, known component cash only | 1-board build USD | 10-board build USD | 100-board build |
|---|---:|---:|---|
| Current r0.3, three MOQ purchases | 25,256.08 | 25,686.16 | 29,124.03USD published original case |
| **#PBF packaging only** | **11,294.31** | **11,902.90** | Available total unknown; price reference17,011.68USD |
| Packaging plus two candidate1k TNPW | 5,665.51 | 6,282.84 | Not applied; available total unknown |
| Conditional packaging+1k TNPW+10k RNCF pilot basket | **101.95** | **766.20** | Not applied; available total unknown; price reference6,338.18USD |

The current-board figures will change only if the parent records MC-PACK-001 and regenerates a new revision. The101.95USD basket is **a conditional engineering proposal**, not the current BOM, complete manufactured-board cost, or controller selling price. All cases retain **10 unpriced exact MPNs**, including the nonstandard top precision values; they exclude PCB, turnkey assembly, feeders, programming, testing, cooling, connectors beyond this source, power supply, enclosure, display, purchased modules, packaging, shipping, taxes/tariffs, scrap, support and margin. Other supplier availability is still unqualified. Original records and six-joint historical evidence were not rewritten.

## Receipt

The JSON and calculator are saved alongside input snapshots and their hashes under `sourcing-optimization-proposal/`. Ten numerical checks passed, including negative controls that reject the blanket downgrades and a stock check that leaves the100-board available total null. Manufacturer PDFs available locally are hashed; failed raw PDF/page downloads are recorded. The source browser observations preserve current authorized offer values and manufacturer excerpts. No native ERC/DRC, target compilation, HDL run, synthesis, circuit source change, physical measurement or supplier upload was performed by this audit.
