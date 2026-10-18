# Measured routing-model failures — 18 October 2026

The first actual Rust bulk-routing result is rejected. No board is adopted, no new routing gain is accepted, and no further production run is started while these model defects are being diagnosed. The physical source remains [the exact a693 native project](../../archives/joint-global-R3-exact-native-project.zip); [its current DSN and rules](../../current-global-R3/README.md) and [native-drill metadata derivative](../../current-global-R3/rust-native-hole-model/README.md) remain separate inputs.

## Actual native result

[Exact cached native diagnostic](rejected-native-cached-diagnostic.json), with unchanged source zones/cache scope and matched pad/net inventory:

| Measurement | Source a693 | Rejected routed result |
| --- | ---: | ---: |
| Required native pad-island joins | 1,693 | 2,192 |
| Native API unconnected items | 1,719 | 2,208 |

The result adds **499 required joins**. It splits 502 previously connected native pad groups, losing 971 old pad-pair relationships, while three mergers gain six pairs. All 233 protected discrete nets and their actual masks are retained. Ordinary annulus changes remain held. No Fill, DRC, full AFTER, or manufacturing acceptance follows. These counts use a different input/cache scope from the historical 1,172-join baseline.

The engine's six routed attempts and 27 ripped objects did not describe the full change scope: native copper objects fell from 94,300 to 68,423, with 2,414 ordinary source-via UUIDs retired and 873 new ordinary-via UUIDs. Source-forward validation preserves retained native records and distinguishes new/retired objects. This candidate is retained strictly for diagnosis.

## The working contact model already differs before routing

[Original-engine no-routing source/cleanup experiment](original-source-and-cleanup-graph.json) binds all 2,155 ordinary nets and 5,122 native ref/pin/net contexts, including the previously omitted 644 single-pad nets. Native source ordinary joins are **839**; an optimistic undirected union of the original engine's normal-contact observations has **1,470**, missing 1,432 native pad-pair relationships across 631 splits on 474 nets before any routing or cleanup. It has no mergers against native. The union is optimistic if original contacts are nonreciprocal; it is not a claim that the original directed connected-set implementation is equivalent.

Original tail removal alone then changes engine joins **1,470 → 1,473**, losing another eight engine pad-pair relationships on three nets; vias fall 8,015 → 6,683. Its subsequent optimizer yields 1,468 engine joins and 6,657 vias. No scheduler or routing was run in this experiment. This identifies a source/contact-model and cleanup problem that must be resolved before trusting more bulk routing.

Exact-center contact semantics, native off-center/mid-trace contacts, DSN precision, and native per-layer via eligibility are under investigation. The [complete native literal coordinate census](source-native-coordinate-grid.json) finds 12,511 segment endpoint scalar coordinates and 1,866 via-center scalar coordinates off the engine's current 100 nm grid. This alone does not attribute the missing relationships or authorize geometric tolerances. Native source copper and electrical limits remain the authority.

## Independently confirmed inactive-layer violation

The [original terminal](rejected-engine-terminal.json) is HELD with exit code 2: `New trace on inactive layer`. [Exact rational native-body witnesses](inactive-layer-native-body-proof.json) prove five added In2 intervals on OBS26_INVERTED/OBS29_INVERTED lie outside every old same-net trace capsule and even full nominal via-disc supersets. These are actual new copper, rather than only new identifiers after re-segmentation. A bounded search on another interval is not treated as an equivalence waiver.

Post-route tightening and via movement can affect layers that the maze has disabled. An isolated allowed-layer correction is being qualified, together with all-changed-item DRC and cleanup checks. A layer-only correction does not resolve the independent pre-route contact mismatch. No blanket clearance reduction, synthetic connection, lost-connection waiver or channel removal is accepted.

The board remains unfinished. Current/return, source contact, complete native refill/DRC, assembly, FPGA physical implementation/timing and physical qualification remain open.

## Java result and corrected source-model qualification

The original Java R11 run also used exact-center contact semantics. It was stopped through original public cancellation, preserving its diagnostic session. [Same-cache native measurement](cancelled-Java-native-cached-diagnostic.json) changes 1,693 → **2,254 required joins**, with 614 old groups split/1,234 old pad-pair relationships lost, versus 53 mergers/99 pairs gained. Source copper falls from 94,300 to 56,972. There is no accepted final original CRC record, so the frozen eligible/full-AFTER gate remains closed. The separate diagnostic performs no Fill, native Save or DRC and never adopts the cancelled result. This is further evidence of the old model/cleanup defect, not routing progress.

The two remaining original-overlap gaps are real source-zone paths carrying inductor-to-shunt current: CORE_CORE_ISNS and MOTION_CORE_ISNS. A [membership-only correction](power-role-membership-independent-review.json) protects both (235 protected/2,153 ordinary), retaining every other AST token, complete class profile and effective pair clearance. [Root's original-overlap recomputation](corrected-ordinary-overlap-partitions.json) now matches every ordinary native source partition.

The [actual opt-in corrected-engine qualification](corrected-source-cleanup-qualification.json) and [independent review](corrected-source-cleanup-independent-review.json) reproduce **all 5,116 pads/837 ordinary joins** before cleanup, after tail cleanup and after optimizer. All 84,582 working traces/8,015 vias remain exact. Electrical overlap queries are distinct from editable center contacts; generic defaults retain their oracle behavior. This proves source relationship retention, not successful simplification: guarded cleanup may skip or roll back. Complete changed-copper DRC, affected-net connection retention, fresh physical-source export and actual routed native feedback remain required before a new production run. The separate three-clamp source candidate has its own native project and evidence.
