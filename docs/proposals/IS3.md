# IS-3 proposal intake — 18 October 2026

**Draft; no adoption.** These are the owner's decided targets within the proposed revision. The active contract remains [IS-2](../MOTHERBOARD_IS2.md), including twelve fitted motor interfaces. This intake authorizes no schematic, board, gateware, live-machine, purchase or revision-ledger change. Existing qualification evidence retains its exact original scope.

## Proposed revision

| Group | IS-2 contract | IS-3 proposed targets |
| --- | --- | --- |
| Motor channels | 12 fitted | 8 fitted (XM0–XM7) + 4 through a qualified expansion interface (supplied labels XM9–XM12; namespace unresolved) |
| ABZ encoders | 4 fitted, 8 reserved | 6 fitted (XE0–XE5), 6 logical reserved, 4 spare receiver channels |
| General DI / smart DO | 24 / 16 | 24 / 24; six quad smart-driver ICs |
| Analog | 2 AO, 4 AI | 2 AO, 8 switchable-range AI: 0–10 V / 4–20 mA / 0.5–4.5 V; fused excitation per bank |
| RS-485 | 1 isolated | 2 fitted, one in service and one spare; CAN unchanged |
| Field voltage | Existing fixed arrangements | Per-bank selectable, fused 5/12/24 V; circuit compatibility unresolved |
| Machines served | One | MR1 and EMCO 120P through machine-identity-bound profiles |

The expansion is required for MR1's twelve-channel use. It is not a return to the superseded custom-card rack. Identity-bound profiles must not share live state. Preserve the inherited permission/watchdog/freshness/CRC/identity contract, 20 ms inhibit bound, settings/recovery/mirror/export, offline entitlements, deliberate inhibited restart and approved service boundaries. Screen size and licensing must not remove required machine resources. No new electrical rating follows from this proposal.

## Accounting and unresolved design details

Against the preserved IS-2 requirements, the supplied arithmetic is reproducible: fitted `371 − 4×14 + 2×10 + 12 + 12 = 359`; reserved `80 − 2×10 = 60`; total `359 + 60 = 419`, 32 below 451. The proposed expansion's 56 positions are excluded. These are conditional counts, not a regenerated terminal map or validated connector selection.

The supplied summary says 47 connector entries (45 IS-2 + XM9 + XDO2). Existing IS-2 already has XM9, so this does not establish 47 unique connector IDs. The XM9–XM12 expansion labels also require reconciliation with retained XM8–XM11 records. Preserve source labels until a separately authorized map resolves them.

Other source conflicts remain visible:

- The draft's ten-contact motor/eight-contact encoder prose conflicts with the baseline and delta arithmetic using fourteen/ten positions. Existing AI groups also do not establish a uniform three-position-per-channel implementation.
- The draft's two AM26C31 packages for eight motors is insufficient for STEP/DIR differential pairs. Each package has four transmitters: eight motors require sixteen transmitters, hence four packages; twelve require six. The current motor design records six. See [TI AM26C31](https://www.ti.com/product/AM26C31).
- A 5 V smart-output bank is not established by the selected TPS274C65, whose specified minimum operating supply is 6 V. A qualified circuit choice or explicit scope restriction is needed; retain actual limits. See [TI TPS274C65](https://www.ti.com/product/TPS274C65).
- Twelve synchronized channels remain required for MR1. Expansion generation, timing, transport and fault behavior need definition before assuming only eight FPGA generators. The existing 17,912 LUT4+ADD / 63 RAM result belongs to its exact disconnected IS-2 SIM2 source, not IS-3. Connector positions alone do not establish FPGA pin demand.
- Existing dated costs remain historical scenarios; no IS-3 saving or complete-package price is established.

## Open gates

| Gate | Evidence required before its associated claim |
| --- | --- |
| ND-1 | Recalculate XP1 power-entry currents, simultaneous loads, fuse and branch requirements for actual IS-3 loads |
| ND-5 | E3 envelope/contact review of the proposed eight-by-three AI pattern and range circuitry |
| ND-6 | Vendor pin/bank/resource review for DO24, encoder/AI changes and the complete physical wrapper |
| ND-7 | Resolve added DO/AI supplies, shields (the supplied proposal claims fifteen) and per-bank AUX loop supplies; feed actual loads into ND-1 |

No board layout, schematic, gateware implementation, native ERC/DRC, vendor fit/timing, physical measurement or manufacturing qualification was performed for this intake.

## Preserved source and provenance

The [local source archive](../../research/user-notes/2026-10-18-is3-proposal/README.md) preserves eight raw pasted pages and five unique extracted documents from the private Hugging Face workspace. It includes the motor architecture draft, EMCO console fix spec, delta JSON and supplied audit totals/classification. Source wording is retained even where it conflicts with the boundary above. A byte-exact copy of the current IS-2 requirements is retained separately; the active file is unchanged.

The EMCO spec remains a separate proposed software/workflow change: one canonical wiring packet, visible-surface refresh, shared calibration data, actual-window/portrait verification, reviewed reversible AI changes and no machine-command or interlock bypass. No console code was changed.

The linked builder, full regenerated requirements/terminal map and audit scripts were not supplied as file contents. They were not reconstructed or executed. The independent audit describes the earlier Git commit `945fb717`; its 126,703-entry run was not repeated. Follow-up interpretation and restored source files are documented in the [publication audit follow-up](../../reports/documentation-refresh-20261018/independent-audit-followup/README.md).

The original intake stayed local. The owner subsequently requested publication of the proposal, research notes and verification handoff on 18 October 2026. The [original intake receipt](../../reports/documentation-refresh-20261018/is3-proposal-intake/intake.json) retains its historical local-only scope; later publication does not adopt IS-3.

## Follow-up transcript review — 18 October 2026

The additional supplied conversation is preserved in the local source archive as `raw/followup-routing-conversation-20261018.txt` (SHA-256 `bbbbe35f567d506188e3130fb81984f9ba7218ede1b3a5f1a0466080fc10b76b`). It repeats the proposed counts and dual-machine profile requirement already captured above; it supplies no new implementation or adoption evidence. Its claims that every decision is closed conflict with the unresolved gates in this draft.

The routing conclusions in that conversation require correction:

- A six-minute quiet parsing attempt that was terminated is an incomplete attempt, not proof that a router cannot load the board or that routing is impossible. The current local exact-source Java load test completes in about 17 seconds. Its qualified electrical-contact query matches all 5,116 ordinary pin queries and 837 native ordinary joins, with no missing or extra pad pairs. This is a load/query result, not a completed routing pass. See [actual Java qualification](../../reports/board-finish-20261017/release-review/java-electrical-contacts-source-r1/actual-c7d8-native-ordinary-query-r1/qualification.json).
- Local routing has produced a measured candidate: cached native required joins fall from 1,694 to 1,688, with six joins closed and zero old pad pairs lost. The 831 remaining ordinary joins are a subset of that total. [Native preservation receipt](../../reports/board-finish-20261017/release-review/stopped-transaction-cached-source-preservation-root-r4.json) explicitly leaves full filled AFTER/DRC, current/reference, thermal and assembly qualification open and records no adoption. The historical 1,172 count belongs to a different source/fill state; these figures cannot be combined as one progress series.
- KiCad zone refill recomputes copper pours; it does not route arbitrary missing signal traces. Refill and DRC measure a candidate and may restore plane connectivity, but they do not automatically close the remaining joins. Local board editing, autorouting, FPGA compilation and native validation are executable engineering work; physical wiring and measurement are separate tasks.
- The supplied claim of 81 missing `F.Cu` files is not established. The existing [audit follow-up](../../reports/documentation-refresh-20261018/independent-audit-followup/README.md) traces a representative `F.Cu` entry to an in-memory geometry hash, not a missing CAD file. Each remaining entry needs its actual schema and source revision before any missing-file conclusion.
- The asserted eleven-file publication and full regenerated requirements remain unverified by this transcript. Its named GitHub repository returned HTTP 404 during this review; that does not distinguish a private, unavailable or nonexistent repository. The already preserved proposal sources came from a private Hugging Face workspace. No full requirements artifact or audit execution is inferred from conversational claims alone.

These findings update the draft's evidence and execution assumptions. They do not select the expansion connector, close FPGA or analog contact budgets, reduce the twelve fitted interfaces of active IS-2, or establish that the board is finished. Bulk routing and coordinated power/placement work remain required alongside the open IS-3 gates.
