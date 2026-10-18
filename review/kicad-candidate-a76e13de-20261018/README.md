# KiCad routing candidate — 18 October 2026

Download the [complete KiCad ZIP](../../archives/kicad-candidate-a76e13de-20261018.zip), extract it into a separate folder, and open `native/board.kicad_pro`. The ZIP contains the actual PCB, project settings, custom rules, schematics, symbol libraries, footprint libraries and original source BOM evidence. The 127 MB PCB is inside the ZIP because it exceeds GitHub's individual file limit. The supporting [native files](native/) are also browsable here; download the ZIP to open the complete project.

This isolated candidate is **unfinished and not adopted or manufacturing-ready**. Exact PCB SHA-256: `a76e13deac7bb766419e63bb76c12ce0cde746eda10a66fcef47da36e2fece2b`.

Cached native measurement closes **6 required joins: 1,694 → 1,688**, with **zero old pad pairs lost**. Of the remaining total, 831 are ordinary joins. The historical 1,172 result uses a different source/fill state and is not directly comparable. Full fresh copper refill/DRC, power/current/return/thermal/assembly and physical qualification remain open. All twelve fitted motor interfaces remain required. Isolated power-placement proposals are not incorporated in this board.

See [measured status](candidate-status.json), [file hashes](FILES.json), and the exact [final router session](final.ses). Do not import that SES into an unrelated board. The [starting source, design rules and DSN inputs](../current-routing-setup-20261018/README.md) remain separately available. This publication packages existing measured evidence; it does not run new KiCad validation or produce fabrication outputs.

The preserved evidence/portable-files.json describes the a210 starting source. Use FILES.json and candidate-status.json for this candidate; historical source hashes have not been rewritten.
