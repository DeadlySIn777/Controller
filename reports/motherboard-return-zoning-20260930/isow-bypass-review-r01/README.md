# ISOW HF capacitor placement: independent source review

The proposed local X = ±6.10 mm, Y = 5.080 mm vertical 0402 placement has a coherent manufacturer-dimension basis. This receipt does not adopt a native PCB or certify assembly/EMC performance.

[TI ISOW1432](https://www.ti.com/lit/ds/symlink/isow1432.pdf), page41 Figure9-7, illustrates a terminal-edge distance. Its wording does not formally define a PCB-land versus mechanical lead-tip datum. [TI ISOW1044](https://www.ti.com/lit/ds/symlink/isow1044.pdf), page37, gives matching layout guidance. Therefore measure the actual matching-land routed edge path and the physical lead-tip/body bounds independently; a capacitor-centre threshold is not established by those drawings.

[TI SLLU337 EVM guide](https://www.ti.com/lit/ug/sllu337/sllu337.pdf), page8 Figure4-2, visibly places C20's matching lands overlapping the extended IC lands. That observation refutes a universal clearance-derived1.48mm centre minimum: matching-net lands can overlap. It does not provide exact placement coordinates. The EVM uses a different10nF0402 capacitor from the motherboard's selected part.

TI's package drawing gives9.97–10.63mm overall lead-tip span. The selected [Murata GRM155R71H103KA88](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM155R71H103KA88-01A.pdf) body width is0.50±0.05mm. At X =6.10mm, physical tip/body gap is0.510–0.890mm nominal. An **aggregate relative** X assembly bound of±0.10mm produces0.410–0.990mm. This bound requires assembly-process evidence; ±0.10mm separately for each part would permit1.09mm.

The proposed IC-courtyard indentation to±5.55mm covers the maximum nominal lead tip with0.235mm margin. Native DRC and the full exact body/lead/assembly envelopes must verify that change while preserving every copper/paste/mask land. The earlier X =6.91mm recipe could have a short PCB-land edge gap, but its physical tip/body gap is1.320–1.700mm and cannot establish literal less-than1mm tip/body compliance.

Keep the symmetric HF loop, effective bulk capacitance, ferrite connections and manufacturer4mm raw-secondary EMI exclusion. Required local raw paths shown in TI's example are intentional; filtered return pours must not bypass the real return ferrite. Physical EMC/assembly qualification remains open.

`review.json` freezes the primary PDFs, SHA256 hashes, calculations, proposal and limitations. No schematic or PCB was changed.
