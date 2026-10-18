# Routed KiCad progress — 18 October 2026

[Download the complete editable KiCad project](../../archives/kicad-routing-progress-20261018-r1.zip), extract it into a separate folder, and open `native/board.kicad_pro`. It includes all 214 native PCB/project/rules/schematic/library files. The PCB exceeds GitHub's individual file limit and is supplied inside the ZIP. Exact file hashes are in [FILES.json](FILES.json).

**KiCad 10.0.7 measured improvement: 1,688 → 1,687 required joins; API items 1,713 → 1,712. Zero previous pad relationships were lost.** This update adds one join on FPGA_USER_RESET_N while retaining every copper record of the previous six-gain candidate. Total measured improvement from the a210 cached reference is seven joins (1,694 → 1,687). These counters are not directly comparable to the historical 1,172 full-fill result.

The new route adds 19 track segments and three vias. Composition checks cover its clearance from the previous route delta; native checks cover pad connectivity/poses, actual via masks and new via-drill/SMD intersections. The previously added inner annulus remains explicitly reviewed. See [measured progress](evidence/progress.json) and the accompanying source-bound receipts.

This is **unfinished, unadopted, and not manufacturing-ready**. This measurement used saved copper caches; full refill/DRC, power/current/return/thermal/assembly and physical qualification remain open. A separate full refill/DRC job on the previous a76e board does not qualify this newer source. All twelve motor interfaces remain fitted. IS-3 remains a proposal.

The [additive donor SES](additive-donor.ses) belongs to the original a210 routing input and carries this update's additive route. It is not a complete session for the combined seven-gain board; use the supplied complete PCB. [Original source and DSN inputs](../current-routing-setup-20261018/README.md) and the [previous six-gain board](../kicad-candidate-a76e13de-20261018/README.md) remain available separately. Bulk routing continues beyond this frozen checkpoint.
