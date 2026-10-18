# Actual motherboard source: partial exact-MPN component cost

30 September 2026; USD; `source-r25-2688-complete-cost-v10`. **2688 physical footprints / 2642 purchased fitted parts / 37 bare PCB test pads + 1 bare chassis pad + 6 bare NPTH mounts / 2 DNP footprints / 291 exact source MPN/geometry groups.**

These totals are a partial catalogue basket for this immutable schematic snapshot. Unpriced parts, unresolved exact module/package selections and all PCBWay manufacture costs remain unknown. They are not a complete board price, available procurement basket, turnkey quote or selling price.

| Boards | Qty-matching priced subtotal | Priced fitted inventory value | Catalogue purchase cash incl. excess | Unpriced MPNs / fitted pieces |
|---:|---:|---:|---:|---:|
| 1 | $948.90 | $1091.51 | $61020.80 | 184 / 720 |
| 10 | $7347.60 | $8773.68 | $67419.50 | 184 / 7200 |
| 100 | $76530.45 | $79651.22 | $131032.35 | 184 / 72000 |

Fitted inventory value allocates the price of consumed parts at the applicable purchase tier. Purchase cash includes unused MOQ inventory. Neither proves delivery or design qualification. The two inherited PLT 1k/10k T1 lots require **$11,200 minimum known cash**, with prices of $5.63/$5.57 per piece at 1,000 each. Every remaining unpriced PLT string retains its actual T1 packaging syntax; its unit price and order acceptance remain unknown.

R7015/R7016 MPG termination footprints are DNP in the initial source model and are excluded from purchasing even though the old CSV lacked a DNP column. Their physical footprints remain in counts. Subsequent receipts use their own frozen DNP states.

[All quantity rows](MOTHERBOARD_COST.csv), [complete calculation and exclusions](MOTHERBOARD_COST.json), [exact observed price evidence](CATALOGUE_OBSERVATIONS.json), [part sourcing/package screen](PARTS_SOURCING_REVIEW.json), [input hashes](snapshot.json) and [issued artifact hashes](receipt.json).

## Sourcing and package findings

The nominal footprint-family screen is distinct from full IC pin/land/orientation verification. It preserves exact source MPNs and never infers suitability merely from a quote.

- ****:  Nominal footprint family needs review.
- **10164227-1001A1RLF**:  Nominal footprint family needs review.
- **16SVPG330M**:  Nominal footprint family needs review.
- **1757242**:  Nominal footprint family needs review.
- **1844210**:  Nominal footprint family needs review.
- **1844223**:  Nominal footprint family needs review.
- **1844252**:  Nominal footprint family needs review.
- **1844294**:  Nominal footprint family needs review.
- **1844317**:  Nominal footprint family needs review.
- **1844333**:  Nominal footprint family needs review.
- **219-3MSTRF**:  Nominal footprint family needs review.
- **3568**:  Nominal footprint family needs review.
- **503398-1892**:  Nominal footprint family needs review.
- **61302211821**:  Nominal footprint family needs review.
- **614004134726**:  Nominal footprint family needs review.
- **690-019-298-412**:  Nominal footprint family needs review.
- **7499111446**:  Nominal footprint family needs review.
- **74LVC125APW,118**:  Nominal footprint family needs review.
- **74LVC1G17GW**: Manufacturer type number is valid SOT353-1, but exact orderable suffix is unresolved; official Nexperia lists 74LVC1G17GW,125. No unapproved suffix normalization.
- **74LVC2G04GW,125**:  Nominal footprint family needs review.
- **74LVC2G07GW,125**:  Nominal footprint family needs review.
- **AAA3528RGBS/K11/C8CC**:  Nominal footprint family needs review.
- **AD5683RBRMZ-3**:  Nominal footprint family needs review.
- **ADS1115IDGSR**:  Nominal footprint family needs review.
- **ADS8684AIDBTR**:  Nominal footprint family needs review.
- **APT1608SGC**:  Nominal footprint family needs review.
- **APT1608SURCK**:  Nominal footprint family needs review.
- **ASV-40.000MHZ-LC-T**:  Nominal footprint family needs review.
- **BAS16,215**:  Nominal footprint family needs review.
- **BAT54S,215**:  Nominal footprint family needs review.
- **BLM15EX331SN1D**:  Nominal footprint family needs review.
- **BSS138P,215**:  Nominal footprint family needs review.
- **C0805C223K1RACTU**:  Nominal footprint family needs review.
- **C1608X7R1H473K080AA**:  Nominal footprint family needs review.
- **C2012C0G2A103J125AA**: Exact 0805/100V/C0G/5% product confirmed; accessible detailed primary price is CAD. No inferred currency conversion or substitute tolerance price used.
- **CGA5L3X7S2A225K160AB**:  Nominal footprint family needs review.
- **CGA6M3X7S2A475K200AE**:  Nominal footprint family needs review.
- **CGA6P1X7S1A476M250AC**:  Nominal footprint family needs review.
- **CL10C332JB8NNNC**: Manufacturer validates exact Samsung part; no current purchasable primary USD offer verified. LCSC reference-only/out-of-stock excluded.
- **CRCW2512120RFKEG**:  Nominal footprint family needs review.
- **CSD19537Q3T**:  Nominal footprint family needs review.
- **CSD19538Q3AT**:  Nominal footprint family needs review.
- **EEEFK1A331P**:  Nominal footprint family needs review.
- **FSUSB42MUX**:  Nominal footprint family needs review.
- **GCM155R71C104KA55D**:  Nominal footprint family needs review.
- **GCM31CR71A226KE02L**:  Nominal footprint family needs review.
- **GRM155R71H103KA88D**:  Nominal footprint family needs review.
- **GRM188R71H105KA12D**: Exact name occurs in official TI TIDA-01464 BOM (1uF/50V/X7R/0603); present manufacturer/orderable catalogue and USD price not verified. Different KAALD suffix is not substituted.
- **GRM31CR72A105KA01L**:  Nominal footprint family needs review.
- **INA149AIDR**:  Nominal footprint family needs review.
- **INA219AIDR**:  Nominal footprint family needs review.
- **ISO1212DBQR**: Nominal DBQ family fits both source libraries. The initial 685 snapshot had six generic motor SSOP land patterns and twelve exact-TI DI patterns; later snapshots list their actual source footprints here. Full native land/pin verification is separate hardware evidence.
- **ISO1540DR**:  Nominal footprint family needs review.
- **ISO7720FDWR**:  Nominal footprint family needs review.
- **ISO7760FDWR**:  Nominal footprint family needs review.
- **ISO7761FDWR**:  Nominal footprint family needs review.
- **ISO7762FDBQR**:  Nominal footprint family needs review.
- **ISOW1044DFMR**:  Nominal footprint family needs review.
- **ISOW1432DFMR**:  Nominal footprint family needs review.
- **KRL2012E-C-R015-F-T5**:  Nominal footprint family needs review.
- **KRL3216D-C-R005-F-T1**:  Nominal footprint family needs review.
- **KRL3216D-C-R006-F-T1**:  Nominal footprint family needs review.
- **LM4040A25IDBZR**:  Nominal footprint family needs review.
- **LM66100DCKR**:  Nominal footprint family needs review.
- **LM70660RRXR**:  Nominal footprint family needs review.
- **LM706A0RRXR**:  Nominal footprint family needs review.
- **LMR36506R5RPER**:  Nominal footprint family needs review.
- **LPS6235-223MRC**:  Nominal footprint family needs review.
- **LT3092IST#PBF**:  Nominal footprint family needs review.
- **MAX17612AATB+T**:  Nominal footprint family needs review.
- **MAX17612CATB+T**:  Nominal footprint family needs review.
- **MCP2518FDT-E/SL**:  Nominal footprint family needs review.
- **OPA197IDBVR**:  Nominal footprint family needs review.
- **OPA4197IPWR**:  Nominal footprint family needs review.
- **PESD2CANFD24V-T**:  Nominal footprint family needs review.
- **PHP01206E1001BST5**:  Nominal footprint family needs review.
- **PLT0603Z1001LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z1002LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z1071LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z1151LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z2610LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z3160LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z3553LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z5803LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z8672LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z8792LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z9212LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PLT0603Z9312LST1**: Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.
- **PMV20XNEAR**:  Nominal footprint family needs review.
- **REF5025AIDR**:  Nominal footprint family needs review.
- **SMBJ12CA-E3/52**:  Nominal footprint family needs review.
- **SMCJ30CA**:  Nominal footprint family needs review.
- **SMF36CA**:  Nominal footprint family needs review.
- **SMM02040C1001FB300**: Exact MiniMELF is documented in TI ISO1212 EVM BOM. LCSC's accessible USD tiers are reference-only with zero stock; selected purchasable offer remains unknown.
- **SN74AHCT04PWR**:  Nominal footprint family needs review.
- **SN74AHCT08PWR**:  Nominal footprint family needs review.
- **SN74LV165APWR**:  Nominal footprint family needs review.
- **SN74LVC08APWR**:  Nominal footprint family needs review.
- **SN74LVC14APWR**:  Nominal footprint family needs review.
- **SN74LVC2G34DCKR**:  Nominal footprint family needs review.
- **SN74LVC2G74DCUR**: TI SCES203Q confirms SINGLE 8-pin DFF with CLK1,D2,/Q3,GND4,Q5,/CLR6,/PRE7,VCC8. SN74LVC1G74DCUR uses the same pin map. '2G' does not imply dual; no invalid-package assertion is supported here.
- **SN74LVC2T45DCTR**:  Nominal footprint family needs review.
- **STM32G031C8T6**:  Nominal footprint family needs review.
- **STM32G031K8T6**:  Nominal footprint family needs review.
- **TBU-CA025-050-WH**:  Nominal footprint family needs review.
- **TCA9517ADGKR**:  Nominal footprint family needs review.
- **TCA9517DGKR**:  Nominal footprint family needs review.
- **TCA9534PWR**:  Nominal footprint family needs review.
- **TLC59116FIPWR**:  Nominal footprint family needs review.
- **TLP3640A(TPL,E**: Exact spelling matches Toshiba representative order code and distributor MPN. Earlier source's closing-parenthesis alias is retained only in its historical receipt. Accepted factory packing suffix/PCBWay handling still require procurement confirmation.
- **TLP4176A(TP,F**: Exact spelling matches Toshiba representative order code and distributor MPN. Earlier source's closing-parenthesis alias is retained only in its historical receipt. Accepted factory packing suffix/PCBWay handling still require procurement confirmation.
- **TMR 4-2412WI**:  Nominal footprint family needs review.
- **TMR 4-2413WI**:  Nominal footprint family needs review.
- **TMR 4-2415WI**:  Nominal footprint family needs review.
- **TMUX1121DGKR**:  Nominal footprint family needs review.
- **TMUX1511PWR**:  Nominal footprint family needs review.
- **TNPW0603100KBEEA**:  Nominal footprint family needs review.
- **TNPW0603100RBEEA**:  Nominal footprint family needs review.
- **TNPW0603107KBEEA**:  Nominal footprint family needs review.
- **TNPW060310K0BEEA**:  Nominal footprint family needs review.
- **TNPW060311K5BYEA**:  Nominal footprint family needs review.
- **TNPW0603120KBEEA**:  Nominal footprint family needs review.
- **TNPW0603123KBEEA**:  Nominal footprint family needs review.
- **TNPW0603130KBEEA**:  Nominal footprint family needs review.
- **TNPW060313K3BEEA**:  Nominal footprint family needs review.
- **TNPW0603140KBEEA**:  Nominal footprint family needs review.
- **TNPW060317K8BEEA**:  Nominal footprint family needs review.
- **TNPW06031K37BEEA**:  Nominal footprint family needs review.
- **TNPW060320K0BEEA**:  Nominal footprint family needs review.
- **TNPW0603267KBEEA**:  Nominal footprint family needs review.
- **TNPW060326K7BEEA**:  Nominal footprint family needs review.
- **TNPW0603287KBEEA**:  Nominal footprint family needs review.
- **TNPW060329K4BEEA**:  Nominal footprint family needs review.
- **TNPW06032K49BEEA**:  Nominal footprint family needs review.
- **TNPW06032K55BYEA**:  Nominal footprint family needs review.
- **TNPW060330K0BEEA**:  Nominal footprint family needs review.
- **TNPW0603316KBEEA**:  Nominal footprint family needs review.
- **TNPW0603332KBEEA**:  Nominal footprint family needs review.
- **TNPW060333K2BEEA**:  Nominal footprint family needs review.
- **TNPW060334K0BEEA**:  Nominal footprint family needs review.
- **TNPW06033K00BEEA**:  Nominal footprint family needs review.
- **TNPW06033K24BEEA**:  Nominal footprint family needs review.
- **TNPW0603412KBEEA**:  Nominal footprint family needs review.
- **TNPW060344K2BEEA**:  Nominal footprint family needs review.
- **TNPW060348K7BEEA**:  Nominal footprint family needs review.
- **TNPW060349K9BEEA**:  Nominal footprint family needs review.
- **TNPW06034K02BEEA**:  Nominal footprint family needs review.
- **TNPW06034K75BEEA**:  Nominal footprint family needs review.
- **TNPW060353K6BEEA**:  Nominal footprint family needs review.
- **TNPW0603549KBEEA**:  Nominal footprint family needs review.
- **TNPW060357K6BEEA**:  Nominal footprint family needs review.
- **TNPW060360K4BEEA**:  Nominal footprint family needs review.
- **TNPW0603615KBEEA**:  Nominal footprint family needs review.
- **TNPW0603649KBEEA**:  Nominal footprint family needs review.
- **TNPW060368K1BEEA**:  Nominal footprint family needs review.
- **TNPW0603698RBEEA**:  Nominal footprint family needs review.
- **TNPW060378K7BEEA**:  Nominal footprint family needs review.
- **TNPW060393K1BEEA**:  Nominal footprint family needs review.
- **TNPW06039K53BEEA**:  Nominal footprint family needs review.
- **TNPW0805887KBEEA**:  Nominal footprint family needs review.
- **TPD12S016PWR**:  Nominal footprint family needs review.
- **TPD1E10B06DPYR**:  Nominal footprint family needs review.
- **TPD4E05U06DQAR**:  Nominal footprint family needs review.
- **TPD4EUSB30DQAR**:  Nominal footprint family needs review.
- **TPS1H000AQDGNRQ1**:  Nominal footprint family needs review.
- **TPS22990DMLR**:  Nominal footprint family needs review.
- **TPS26624DRCR**:  Nominal footprint family needs review.
- **TPS26630RGER**:  Nominal footprint family needs review.
- **TPS274C65ASRHAR**:  Nominal footprint family needs review.
- **TPS3700DDCR**:  Nominal footprint family needs review.
- **TPS3702CX50DDCR**:  Nominal footprint family needs review.
- **TPS3839K33DBZR**:  Nominal footprint family needs review.
- **TPS62902RPJR**:  Nominal footprint family needs review.
- **TPS7A1633DGNR**:  Nominal footprint family needs review.
- **TPS7A1650DGNR**:  Nominal footprint family needs review.
- **TPS7A2650DRVR**:  Nominal footprint family needs review.
- **TS3A27518EPWR**:  Nominal footprint family needs review.
- **USB4105-GF-A**:  Nominal footprint family needs review.
- **VY2472M49Y5US63V7**:  Nominal footprint family needs review.
- **WSL0805R1000FEA**:  Nominal footprint family needs review.
- **XAL1010-472MED**:  Nominal footprint family needs review.
- **XAL7070-472MEC**:  Nominal footprint family needs review.

The 2G74/1G74 package and pin-map finding is supported by [TI SCES203Q](https://www.ti.com/lit/ds/symlink/sn74lvc2g74.pdf) and [TI SCES794G](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf). The [Vishay PLT ordering specification](https://www.vishay.com/docs/60030/plt.pdf) permits nonstandard resistance values and specifies T1's 1,000-piece minimum/multiple. The [Nexperia ordering list](https://www.nexperia.com/chemical-content/74LVC1G17GW.html) separates type number from orderable suffix. [TI TIDA-01464 BOM](https://www.ti.com.cn/lit/pdf/TIDRTP7) records the otherwise unverified exact Murata 1uF name.

## Unpriced exact MPNs

- `1844210`: 2 fitted/board; cost unknown.
- `1844223`: 2 fitted/board; cost unknown.
- `1844252`: 4 fitted/board; cost unknown.
- `219-3MSTRF`: 2 fitted/board; cost unknown.
- `3568`: 3 fitted/board; cost unknown.
- `503398-1892`: 1 fitted/board; cost unknown.
- `61302211821`: 2 fitted/board; cost unknown.
- `614004134726`: 1 fitted/board; cost unknown.
- `690-019-298-412`: 1 fitted/board; cost unknown.
- `7499111446`: 1 fitted/board; cost unknown.
- `74LVC1G17GW`: 1 fitted/board; cost unknown.
- `74LVC2G04GW,125`: 2 fitted/board; cost unknown.
- `74LVC2G07GW,125`: 2 fitted/board; cost unknown.
- `AAA3528RGBS/K11/C8CC`: 7 fitted/board; cost unknown.
- `APT1608SURCK`: 13 fitted/board; cost unknown.
- `ASV-40.000MHZ-LC-T`: 1 fitted/board; cost unknown.
- `BAS16,215`: 23 fitted/board; cost unknown.
- `BAT54S,215`: 14 fitted/board; cost unknown.
- `BLM15EX331SN1D`: 4 fitted/board; cost unknown.
- `BSS138P,215`: 3 fitted/board; cost unknown.
- `C0603C102J5GACTU`: 2 fitted/board; cost unknown.
- `C0805C223K1RACTU`: 16 fitted/board; cost unknown.
- `C1608X7R1H473K080AA`: 2 fitted/board; cost unknown.
- `C2012C0G1H223J125AA`: 2 fitted/board; cost unknown.
- `C2012X7R1C475K125AB`: 3 fitted/board; cost unknown.
- `C3216C0G2A104J160AC`: 3 fitted/board; cost unknown.
- `C3216X7R1A106K160AB`: 1 fitted/board; cost unknown.
- `CGA5L3X7S2A225K160AB`: 25 fitted/board; cost unknown.
- `CGA6M3X7S2A475K200AE`: 8 fitted/board; cost unknown.
- `CGA6P1X7S1A476M250AC`: 6 fitted/board; cost unknown.
- `CL10C332JB8NNNC`: 2 fitted/board; cost unknown.
- `CRCW06030000Z0EA`: 5 fitted/board; cost unknown.
- `CRCW0603100RFKEA`: 1 fitted/board; cost unknown.
- `CRCW0603110KFKEA`: 6 fitted/board; cost unknown.
- `CRCW0603120RFKEA`: 4 fitted/board; cost unknown.
- `CRCW0603150KFKEA`: 7 fitted/board; cost unknown.
- `CRCW06031K80FKEA`: 1 fitted/board; cost unknown.
- `CRCW06031M00FKEA`: 2 fitted/board; cost unknown.
- `CRCW06031R20FKEA`: 1 fitted/board; cost unknown.
- `CRCW0603215RFKEA`: 2 fitted/board; cost unknown.
- `CRCW0603221KFKEA`: 1 fitted/board; cost unknown.
- `CRCW060322R0FKEA`: 21 fitted/board; cost unknown.
- `CRCW060324K9FKEA`: 2 fitted/board; cost unknown.
- `CRCW0603270RFKEA`: 1 fitted/board; cost unknown.
- `CRCW060329K4FKEA`: 2 fitted/board; cost unknown.
- `CRCW06032K20FKEA`: 2 fitted/board; cost unknown.
- `CRCW0603390RFKEA`: 8 fitted/board; cost unknown.
- `CRCW06033K32FKEA`: 2 fitted/board; cost unknown.
- `CRCW0603470RFKEA`: 2 fitted/board; cost unknown.
- `CRCW060347R0FKEA`: 4 fitted/board; cost unknown.
- `CRCW060349R9FKEA`: 6 fitted/board; cost unknown.
- `CRCW06034K42FKEA`: 4 fitted/board; cost unknown.
- `CRCW06034R70FKEA`: 4 fitted/board; cost unknown.
- `CRCW060356K0FKEA`: 1 fitted/board; cost unknown.
- `CRCW06035K10FKEA`: 2 fitted/board; cost unknown.
- `CRCW0603680RFKEA`: 28 fitted/board; cost unknown.
- `CRCW06039K53FKEA`: 2 fitted/board; cost unknown.
- `CRCW2512120RFKEG`: 2 fitted/board; cost unknown.
- `CSD19537Q3T`: 3 fitted/board; cost unknown.
- `EEEFK1A331P`: 1 fitted/board; cost unknown.
- `FSUSB42MUX`: 1 fitted/board; cost unknown.
- `GCM155R71C104KA55D`: 4 fitted/board; cost unknown.
- `GCM31CR71A226KE02L`: 19 fitted/board; cost unknown.
- `GRM155R71H103KA88D`: 4 fitted/board; cost unknown.
- `GRM1885C1H101JA01D`: 4 fitted/board; cost unknown.
- `GRM1885C1H102JA01D`: 1 fitted/board; cost unknown.
- `GRM1885C1H131JA01D`: 1 fitted/board; cost unknown.
- `GRM1885C1H222JA01D`: 4 fitted/board; cost unknown.
- `GRM1885C1H331JA01D`: 2 fitted/board; cost unknown.
- `GRM1885C2A103JA01D`: 26 fitted/board; cost unknown.
- `GRM188R71H105KA12D`: 50 fitted/board; cost unknown.
- `GRM188R72A103KA01D`: 4 fitted/board; cost unknown.
- `GRM21BR61E106KA73L`: 3 fitted/board; cost unknown.
- `GRM21BR71A106MA73L`: 2 fitted/board; cost unknown.
- `GRM21BR71A475KE51K`: 4 fitted/board; cost unknown.
- `GRM21BR71C225KA12L`: 4 fitted/board; cost unknown.
- `GRM31CR72A105KA01L`: 10 fitted/board; cost unknown.
- `INA219AIDR`: 1 fitted/board; cost unknown.
- `ISO7760FDWR`: 1 fitted/board; cost unknown.
- `KRL2012E-C-R015-F-T5`: 1 fitted/board; cost unknown.
- `KRL3216D-C-R005-F-T1`: 1 fitted/board; cost unknown.
- `KRL3216D-C-R006-F-T1`: 1 fitted/board; cost unknown.
- `LM4040A25IDBZR`: 1 fitted/board; cost unknown.
- `LM66100DCKR`: 2 fitted/board; cost unknown.
- `LMR36506R5RPER`: 2 fitted/board; cost unknown.
- `LPS6235-223MRC`: 2 fitted/board; cost unknown.
- `LT3092IST#PBF`: 1 fitted/board; cost unknown.
- `MAX17612CATB+T`: 1 fitted/board; cost unknown.
- `OPA197IDBVR`: 3 fitted/board; cost unknown.
- `PESD2CANFD24V-T`: 1 fitted/board; cost unknown.
- `PLT0603Z1071LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z1151LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z2610LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z3160LST1`: 1 fitted/board; cost unknown.
- `PLT0603Z3553LST1`: 2 fitted/board; cost unknown.
- `PLT0603Z5803LST1`: 2 fitted/board; cost unknown.
- `PLT0603Z8672LST1`: 2 fitted/board; cost unknown.
- `PLT0603Z8792LST1`: 3 fitted/board; cost unknown.
- `PLT0603Z9212LST1`: 3 fitted/board; cost unknown.
- `PLT0603Z9312LST1`: 2 fitted/board; cost unknown.
- `PMV20XNEAR`: 2 fitted/board; cost unknown.
- `REF5025AIDR`: 1 fitted/board; cost unknown.
- `SMBJ12CA-E3/52`: 2 fitted/board; cost unknown.
- `SMCJ30CA`: 3 fitted/board; cost unknown.
- `SMF36CA`: 7 fitted/board; cost unknown.
- `SMM02040C1001FB300`: 44 fitted/board; cost unknown.
- `SN74AHCT04PWR`: 6 fitted/board; cost unknown.
- `SN74AHCT08PWR`: 2 fitted/board; cost unknown.
- `SN74AHCT1G08DBVR`: 1 fitted/board; cost unknown.
- `SN74LV165APWR`: 3 fitted/board; cost unknown.
- `SN74LVC08APWR`: 4 fitted/board; cost unknown.
- `SN74LVC14APWR`: 4 fitted/board; cost unknown.
- `SN74LVC1G00DBVR`: 2 fitted/board; cost unknown.
- `SN74LVC1G04DBVR`: 3 fitted/board; cost unknown.
- `SN74LVC1G08DBVR`: 18 fitted/board; cost unknown.
- `SN74LVC1G10DBVR`: 2 fitted/board; cost unknown.
- `SN74LVC1G14DBVR`: 6 fitted/board; cost unknown.
- `SN74LVC1G32DBVR`: 1 fitted/board; cost unknown.
- `SN74LVC2G34DCKR`: 1 fitted/board; cost unknown.
- `SN74LVC2T45DCTR`: 1 fitted/board; cost unknown.
- `TCA9517DGKR`: 1 fitted/board; cost unknown.
- `TCA9534PWR`: 1 fitted/board; cost unknown.
- `TMUX1121DGKR`: 1 fitted/board; cost unknown.
- `TMUX1511PWR`: 1 fitted/board; cost unknown.
- `TNPW0603100KBEEA`: 10 fitted/board; cost unknown.
- `TNPW0603100RBEEA`: 1 fitted/board; cost unknown.
- `TNPW0603107KBEEA`: 2 fitted/board; cost unknown.
- `TNPW060311K5BYEA`: 1 fitted/board; cost unknown.
- `TNPW0603120KBEEA`: 1 fitted/board; cost unknown.
- `TNPW0603123KBEEA`: 2 fitted/board; cost unknown.
- `TNPW0603130KBEEA`: 4 fitted/board; cost unknown.
- `TNPW060313K3BEEA`: 2 fitted/board; cost unknown.
- `TNPW0603140KBEEA`: 3 fitted/board; cost unknown.
- `TNPW060317K8BEEA`: 2 fitted/board; cost unknown.
- `TNPW06031K37BEEA`: 3 fitted/board; cost unknown.
- `TNPW060320K0BEEA`: 2 fitted/board; cost unknown.
- `TNPW0603267KBEEA`: 2 fitted/board; cost unknown.
- `TNPW060326K7BEEA`: 1 fitted/board; cost unknown.
- `TNPW0603287KBEEA`: 1 fitted/board; cost unknown.
- `TNPW060329K4BEEA`: 3 fitted/board; cost unknown.
- `TNPW06032K49BEEA`: 2 fitted/board; cost unknown.
- `TNPW06032K55BYEA`: 1 fitted/board; cost unknown.
- `TNPW060330K0BEEA`: 3 fitted/board; cost unknown.
- `TNPW0603316KBEEA`: 2 fitted/board; cost unknown.
- `TNPW0603332KBEEA`: 1 fitted/board; cost unknown.
- `TNPW060333K2BEEA`: 8 fitted/board; cost unknown.
- `TNPW060334K0BEEA`: 3 fitted/board; cost unknown.
- `TNPW06033K00BEEA`: 2 fitted/board; cost unknown.
- `TNPW06033K24BEEA`: 1 fitted/board; cost unknown.
- `TNPW0603412KBEEA`: 1 fitted/board; cost unknown.
- `TNPW060344K2BEEA`: 1 fitted/board; cost unknown.
- `TNPW060348K7BEEA`: 1 fitted/board; cost unknown.
- `TNPW060349K9BEEA`: 2 fitted/board; cost unknown.
- `TNPW06034K02BEEA`: 1 fitted/board; cost unknown.
- `TNPW06034K75BEEA`: 1 fitted/board; cost unknown.
- `TNPW060353K6BEEA`: 3 fitted/board; cost unknown.
- `TNPW0603549KBEEA`: 1 fitted/board; cost unknown.
- `TNPW060357K6BEEA`: 3 fitted/board; cost unknown.
- `TNPW060360K4BEEA`: 1 fitted/board; cost unknown.
- `TNPW0603615KBEEA`: 1 fitted/board; cost unknown.
- `TNPW0603649KBEEA`: 1 fitted/board; cost unknown.
- `TNPW060368K1BEEA`: 1 fitted/board; cost unknown.
- `TNPW0603698RBEEA`: 3 fitted/board; cost unknown.
- `TNPW060378K7BEEA`: 1 fitted/board; cost unknown.
- `TNPW060393K1BEEA`: 1 fitted/board; cost unknown.
- `TNPW06039K53BEEA`: 2 fitted/board; cost unknown.
- `TNPW0805887KBEEA`: 3 fitted/board; cost unknown.
- `TPD12S016PWR`: 1 fitted/board; cost unknown.
- `TPD1E10B06DPYR`: 16 fitted/board; cost unknown.
- `TPD4E05U06DQAR`: 5 fitted/board; cost unknown.
- `TPD4EUSB30DQAR`: 2 fitted/board; cost unknown.
- `TPS1H000AQDGNRQ1`: 3 fitted/board; cost unknown.
- `TPS2553DBVR`: 2 fitted/board; cost unknown.
- `TPS26624DRCR`: 2 fitted/board; cost unknown.
- `TPS3808G30DBVR`: 1 fitted/board; cost unknown.
- `TPS3808G33DBVR`: 5 fitted/board; cost unknown.
- `TPS3839K33DBZR`: 1 fitted/board; cost unknown.
- `TPS62902RPJR`: 1 fitted/board; cost unknown.
- `TPS7A1633DGNR`: 2 fitted/board; cost unknown.
- `TPS7A1650DGNR`: 2 fitted/board; cost unknown.
- `TS3A27518EPWR`: 1 fitted/board; cost unknown.
- `USB4105-GF-A`: 1 fitted/board; cost unknown.
- `WSL0805R1000FEA`: 1 fitted/board; cost unknown.
- `XAL7070-472MEC`: 1 fitted/board; cost unknown.

## Stock is a separate constraint

All observed inventory is dated, unreserved catalogue evidence. A price can exist with zero or insufficient stock. Future expected receipts are not treated as available. Aggregate supervisor demand uses every actual fitted source reference in the quantity rows, rather than only the historical three retained MC devices. Unknown stock stays null.

| Boards | Priced MPNs short of purchase quantity | Priced MPNs with unknown stock | Stock-qualified complete basket |
|---:|---:|---:|---|
| 1 | 22 | 9 | Unknown |
| 10 | 25 | 9 | Unknown |
| 100 | 30 | 9 | Unknown |

## Separate modules and complete kit costs

The actual ESP32-S3-DevKitC-1-N8R8 v1.1 is a separate purchased service module, with the observed catalogue offer recorded separately; the exact required PCB revision and availability remain unqualified. The compute/RAM/storage/wireless SKU, removable storage and optional AI choices remain unselected and null. Complete touchscreen assemblies in the 7-, 10-, 12-, 14-, 18- and 21-inch classes remain six independent package rows, including touch controller, interface, cable, power and mounting. Screen size never changes the motherboard I/O scope.

PCBWay fabrication/stackup/finish/impedance/yield; accepted exact-part turnkey sourcing; assembly, stencil, setup, feeders, attrition, reeling/tube/tray/BGA inspection; programming; test/fixtures/calibration; cooling, PSU, enclosure/harness/mounting; shipping/tax/tariff; packaging/warranty/support all remain individually null at 1/10/100. No quote has been requested and no files uploaded. The original MC two-inductor $50 leader/trailer allowance is historical only. Current XAL1010-472MED also has a conditional $25 machine-ready charge below its 300-piece reel; all accepted reeling/feeder charges remain separate and unknown.

Only this exact drawn source population is included. The per-block inventory table identifies the physical and purchased counts from actual source blocks, including compute/ESP sockets, power, analog/comms, identity and indicators when present. Exact separately purchased terminal mates, three fitted fuse accessories, M4 bond hardware and full cable/enclosure retention remain distinct rows. Bare PCB geometry has no purchased-part or assembly-placement charge. Any future source correction has unknown counts/cost until frozen, and does not retroactively alter this receipt.

No source hardware was changed by this audit. No native ERC/DRC, target compilation, FPGA synthesis or physical test is claimed. Receipt verification checks immutable hashes, BOM/model identity, DNP exclusion, exact-MPN arithmetic, tier/MOQ, nulls, stock and adversarial negative controls.

## Actual separate accessories

| Exact accessory MPN | Quantity per controller | Catalogue cash at 1 / 10 / 100 controllers |
|---|---:|---:|
| M4 hardware SKU unselected | 1 | Unknown / Unknown / Unknown |
| 0997005.WXN | 1 | Unknown / Unknown / Unknown |
| 099707.5WXN | 2 | Unknown / Unknown / Unknown |
| 1757019 | 6 | $10.86 / $89.22 / $892.20 |
| 1840366 | 2 | Unknown / Unknown / Unknown |
| 1840379 | 2 | Unknown / Unknown / Unknown |
| 1840405 | 4 | Unknown / Unknown / Unknown |
| 1840447 | 6 | Unknown / Unknown / Unknown |
| 1840463 | 8 | Unknown / Unknown / Unknown |
| 1840489 | 12 | Unknown / Unknown / Unknown |

These plugs/fuses/bond accessories are not included in soldered-PCB component subtotal; there is no complete accessory/package total while any line is unknown.

| Source block | Physical / purchased per board | Known fitted inventory at1 /10 /100 boards | Unknown purchased per board |
|---|---:|---:|---:|
| fpga_core | 70 / 70 | $26.62 / $23.68 / $18.98 | 1 |
| mc_local_power | 48 / 48 | $71.86 / $61.93 / $56.50 | 11 |
| mc_motor_buffers | 124 / 124 | $7.89 / $4.91 / $4.04 | 0 |
| mc_permission | 56 / 56 | $9.63 / $6.28 / $5.02 | 0 |
| motherboard_acc_control | 51 / 45 | $3.74 / $2.72 / $2.29 | 8 |
| motherboard_analog_input | 165 / 165 | $176.86 / $144.74 / $133.07 | 58 |
| motherboard_analog_output | 143 / 143 | $108.12 / $86.34 / $77.23 | 56 |
| motherboard_comms | 95 / 95 | $33.06 / $25.27 / $21.45 | 43 |
| motherboard_compute | 191 / 183 | $8.87 / $6.73 / $5.96 | 49 |
| motherboard_control_bridges | 6 / 6 | $0.11 / $0.06 / $0.05 | 0 |
| motherboard_di | 120 / 120 | $18.90 / $13.82 / $11.78 | 24 |
| motherboard_diagnostics | 20 / 10 | $8.43 / $5.75 / $4.76 | 0 |
| motherboard_do | 110 / 110 | $56.08 / $39.27 / $35.95 | 34 |
| motherboard_esp_socket | 23 / 23 | $1.59 / $1.06 / $0.89 | 7 |
| motherboard_fast_inputs | 28 / 26 | $11.21 / $7.43 / $6.13 | 0 |
| motherboard_identity_io | 14 / 14 | $4.51 / $3.14 / $2.61 | 3 |
| motherboard_io3_reset_bypass | 1 / 1 | $0.05 / $0.04 / $0.04 | 0 |
| motherboard_io3_upgrade | 2 / 2 | $0.00 / $0.00 / $0.00 | 2 |
| motherboard_io3_window | 1 / 1 | $0.00 / $0.00 / $0.00 | 1 |
| motherboard_io_control | 103 / 85 | $10.59 / $7.73 / $6.46 | 22 |
| motherboard_motor_power | 65 / 65 | $131.48 / $119.56 / $111.65 | 18 |
| motherboard_motors | 226 / 226 | $95.74 / $72.67 / $63.84 | 14 |
| motherboard_operator | 198 / 198 | $23.66 / $16.15 / $13.77 | 80 |
| motherboard_power_entry | 221 / 221 | $74.24 / $57.11 / $52.20 | 117 |
| motherboard_process | 68 / 68 | $8.04 / $6.09 / $5.55 | 22 |
| motherboard_safety_sensor | 176 / 175 | $51.05 / $37.46 / $32.60 | 59 |
| motherboard_status | 290 / 290 | $16.54 / $11.45 / $9.20 | 81 |
| motherboard_terminals | 44 / 43 | $125.98 / $111.14 / $110.51 | 8 |
| watchdog_conditioning | 29 / 29 | $6.67 / $4.84 / $3.98 | 2 |

Known block values allocate board-wide exact-MPN purchase tiers. They do not add a separate MOQ charge for each circuit region.
