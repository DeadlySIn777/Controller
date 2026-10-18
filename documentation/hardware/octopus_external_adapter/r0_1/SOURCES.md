# Primary-source register

Final candidate BOM adopts Samsung `CL10B104KB8NNNC` for C1 and Yageo `CC0805KKX7R6BB475` for C2. Earlier Murata entries below are retained as research history, not fitted purchase instructions. The source-controlled BOM and native component fields identify the actual selected parts.

Reviewed for this adapter candidate on 5 October 2026. Public specifications establish design inputs; they do not establish the user's exact equipment, stock, final cost or measured performance.

| Source | Use |
| --- | --- |
| [BTT Octopus Pro V1.0 schematic](https://raw.githubusercontent.com/bigtreetech/BIGTREETECH-OCTOPUS-Pro/master/Hardware/BIGTREETECH%20Octopus%20Pro_SCH.pdf) | Provisional F429/F446 socket and 5 V buffered-logic baseline; exact user board unconfirmed |
| [TI SN74LVC3G06 datasheet](https://www.ti.com/lit/gpn/SN74LVC3G06) | DCU package pin map, open-drain function, logic thresholds and electrical limits |
| [JST XH connector drawing](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf) | Exact 2.50 mm header/housing/contact family, PCB geometry and contact wire range |
| [CL57T V4.1 manual](https://www.omc-stepperonline.com/download/CL57T-V41_user_manual.pdf) | Provisional driver input current, 5 V selector, common-anode connection and timing |
| [CL57T V4.1 product page](https://www.omc-stepperonline.com/closed-loop-stepper-driver-v4-1-0-8-0a-24-48vdc-for-nema-17-23-24-stepper-motor-cl57t-v41) | Cross-check; maximum pulse-rate statement differs from downloaded manual and needs resolution |
| [PCBWay assembly file requirements](https://www.pcbway.com/assembly-file-requirements.html) | BOM, SMD centroid, Gerbers and supporting assembly information |
| [PCBWay panel requirements](https://www.pcbway.com/pcb_prototype/Panel_Requirements_for_Assembly.html) | Factory panel/rail review for a small adapter |
| [PCBWay board-type options](https://www.pcbway.com/helpcenter/ordering_parameter_instruction/Board_type.html) | Panel by PCBWay option |
| [PCBWay assembly quotation](https://www.pcbway.com/quotesmt.aspx) | Turnkey, depanelled delivery, functional test and cable harness options |

The attached pictures and pasted earlier advice are reference material. They do not identify a connector pitch, qualify a passive extractor, establish current stock, or authorize manufacture. The current request authorizes this adapter design and matching cable preparation. Existing project motherboard engineering and its physical architecture remain unchanged.

## Passive-part check

Manufacturer specifications match the proposed nominal values and footprints:

| MPN | Verified specification | Primary source |
| --- | --- | --- |
| Murata GRM188R71C104KA01D | 100 nF, ±10%, 16 V, X7R, 0603/1608 | [Murata part-number model catalogue](https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-s-mlcc-2506.ashx?cvid=20250805040438000000&la=ko-kr), base number GRM188R71C104KA01 |
| Murata GRM21BR71A475KA73L | 4.7 µF, ±10%, 10 V, X7R, 0805/2012; L packaging code | [Murata reference sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR71A475KA73-01.pdf) |
| Yageo RC0603FR-071KL | 1 kΩ, ±1%, 0603/1608, 0.1 W at 70°C | [Manufacturer exact-part sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-071KL) |
| Yageo RC0603FR-0747KL | 47 kΩ, ±1%, 0603/1608, 0.1 W at 70°C | [Manufacturer exact-part sheet](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-0747KL) |

**Lifecycle remains open for both Murata selections.** Their available reference/model documents verify specifications, not current production status; the manufacturer's exact product-detail pages returned HTTP 403 during this check. Do not release these capacitor MPNs for procurement without manufacturer lifecycle confirmation or a reviewed current-production replacement. No lifecycle notice was present on the reviewed Yageo exact-part sheets, which is not a stock or price guarantee. No prices or availability are asserted here.

Replacement review: [Samsung CL10B104KB8NNNC](https://product.samsungsem.com/cn/mlcc/CL10B104KB8NNN.do) is explicitly listed as **Mass Production**, 100 nF ±10%, 50 V, X7R, 0603. [Yageo CC0603KRX7R9BB104](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB104) is also manufacturer-documented as 100 nF ±10%, 50 V, X7R, 0603. [Yageo CC0805KKX7R6BB475](https://yageogroup.com/download/specsheet/CC0805KKX7R6BB475) matches 4.7 µF ±10%, 10 V, X7R, 0805. Neither Yageo sheet displays an NRND/EOL notice; factory procurement confirmation remains necessary. The alternative [Samsung CL21B475KPFNNNE](https://product.samsungsem.com/mlcc/CL21B475KPFNNN.do) is explicitly **NRND** and should not be selected for this new design. Final adopted MPNs must agree across native source, PCB properties and BOM.
