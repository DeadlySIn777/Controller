# Routed KiCad progress — 18 October 2026

[Download the complete editable KiCad project](../../archives/kicad-routing-progress-20261018-r3.zip), extract it into a separate folder, and open `native/board.kicad_pro`. All 214 PCB/project/rules/schematic/library files are included. The PCB exceeds GitHub's individual file limit and is supplied inside the ZIP. [Exact file inventory](FILES.json).

**KiCad 10.0.7 measured 1,680 → 1,675 required joins; API items 1,707 → 1,703. Zero previous pad relationships were lost.** This is 5 additional joins and 19 total closed from the same a210 cached baseline of 1,694. These counters are not directly comparable to the historical 1,172 full-fill result.

Every copper record of the 1,680-join composition base is retained. Native connectivity, pad poses, retained via flags, actual annuli and new via-drill/SMD intersections were checked; the composition clearance check covers the new copper against the previous route delta. [Measured progress and scope](evidence/progress.json). This batch selects whole independent nets from a held native import; nets with an SES/native via-net mismatch, changed original source records, or earlier routed progress were omitted. No net was reassigned. The held full router session is a proposal, not a session for this combined PCB. See [subset provenance](evidence/subset-provenance.json).

The board is **unfinished, unadopted, and not manufacturing-ready**. This measurement uses saved copper caches. Full refill/DRC and power/current/return/thermal/assembly/physical qualification remain open. Checks running on older sources do not qualify this newer PCB. All twelve motor interfaces remain fitted; IS-3 remains a proposal. Bulk routing continues beyond this frozen checkpoint.
