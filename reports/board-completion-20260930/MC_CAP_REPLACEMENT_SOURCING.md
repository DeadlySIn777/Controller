# MC-CAP-001 sourcing receipt

30 September2026. Root has promoted **GRM188R72A104KA35D** into parent MC r0.3 for all41 formerly obsolete bypass positions. This receipt supplies primary manufacturer parameters and exact distributor pricing; it does not edit a circuit or approve manufacture.

| Parameter | Original GRM188R71E104KA01D | Current candidate GRM188R72A104KA35D |
|---|---:|---:|
| Nominal capacitance |100nF|100nF|
| Tolerance |±10%|±10%|
| Dielectric |X7R|X7R|
| Rated voltage |25V|100V|
| Package |0603 /1608|0603 /1608|
| Body L×W×T |1.6±0.1×0.8±0.1×0.8±0.1mm|1.6±0.1×0.8±0.1×0.8±0.1mm|
| Terminal width e |0.2…0.5mm|0.2…0.5mm|
| Terminal gap g |≥0.5mm|≥0.5mm|
| Operating range |−55…125°C|−55…125°C|
| Distributor lifecycle |Obsolete|Active|

The exact part family and these new-candidate dimensions appear in the [current Murata product catalogue](https://www.murata.com/products/productdetail?partno=GRM188R72A104KA35%23), and the distributor identifies the [exact D packaging SKU as active](https://www.digikey.com/en/products/detail/murata-electronics/GRM188R72A104KA35D/702549). The original [D SKU](https://www.digikey.com/en/products/detail/murata-electronics/GRM188R71E104KA01D/587154) and its [J reel-size variant](https://www.digikey.in/en/products/detail/murata-electronics/GRM188R71E104KA01J/2612494) are both obsolete. Changing only the old suffix to J would not close availability.

The manufacturer-authored [reference sheet](sourcing-evidence/murata-grm188r72a104ka35.pdf) is retained from [DigiKey's document host](https://media.digikey.com/pdf/Data%20Sheets/Murata%20PDFs/GRM188R72A104KA35.pdf):89,534bytes; SHA256`76518e2eb0b870cd5344b9897bda297aa42f5572d5fde8a0e9c911a0ef1b0654`. Its own update date is2013-12-24. The current manufacturer catalogue separately corroborates the listed nominal parameters, and the current distributor listing supports lifecycle/stock. The PDF alone does not establish current lifecycle. A direct proposed Murata PDF API returnedHTML and was not retained as a PDF.

The D packaging code specifies4000pieces per full reel. **Distributor cut tape allows smaller quantities**; it does not require buying a manufacturer full reel.

| Published quantity minimum (pieces) | CT USD/unit |
|---:|---:|
|1|0.16000|
|10|0.08700|
|50|0.06120|
|100|0.05320|
|500|0.03980|

| MC builds | Required pieces | Applied CT tier | Fitted part subtotalUSD |
|---:|---:|---:|---:|
|1|41|10|3.56700|
|10|410|100|21.81200|
|100|4100|500|163.18000|

The4000-piece full-reel offer is$0.02739/piece,$109.56/reel. A separate4000reel+100CT scenario for4100 required pieces is$114.88, rather than$163.18 for the selected CT-only model. It mixes packaging, so it is **not substituted silently into the current cost model**. PCBWay must quote its accepted format, attrition and any reeling/setup charge before selection.

The source-backed change preserves nominal capacitance, dielectric, tolerance and body/terminal geometry; the parent uses its existing0603 footprint. It increases voltage rating. This receipt makes no equivalence claim for biased capacitance, impedance, solder/process performance or physical measurements. WatchdogCWD capacitors are separate parts and were not changed.

[Exact source ledger](MC_BOM_PRICE_SOURCES.json) and [current component cost](MC_BOM_COST.md) preserve the frozen327-part parent BOM with this substitution.
