# Current motherboard routing review — 18 October 2026

Start with the [complete editable KiCad project ZIP](../../archives/three-clamp-native-source-a21004a7.zip), extract into a separate directory, and open `native/board.kicad_pro`. This is the actual a210 source, not the older loose-board snapshots. Board SHA-256: `a21004a7dbd8e53340bd6882c758185f72e90166d9403dd982d2b8d305bdc9c5`.

The ZIP includes the PCB with its saved copper caches, project, custom design rules, schematics and local libraries. For direct inspection, the exact [project/settings](board.kicad_pro) and [custom rules](board.kicad_dru) are also here. Read these before judging placement, net classes, clearance, layer assignment or routing feasibility. The source is a 450 × 235 mm, six-copper-layer board with 2,726 footprints, 9,977 pads, 86,317 track segments and 8,017 vias. All twelve motor interfaces remain fitted.

## Routing inputs

- [Physical-source DSN](physical-source.dsn): source-exact copper interchange, including the short-edge preservation corrections. This preserves the physical source; exporting a DSN does not encode every KiCad custom rule or electrical/current requirement.
- [Current signal-route-first experiment DSN](signal-route-first.dsn): defers 238 power-zone planning envelopes that have no saved filled copper, while retaining two actual cached current-sense copper areas as net-aware fixed obstacles. The 238 envelopes are not being deleted from the KiCad design. Their electrical/current/reference paths must still be completed and verified. Treat this as an experimental routing model, not a fabrication source or permission to route through required final planes.

Ordinary signal routing currently uses F.Cu, In3.Cu and B.Cu. The remaining inner layers largely contain split power/reference zones. The experiment retains protected power/critical conductors, converter and domain restrictions, native drill constraints and typed clearance floors. Do not infer blanket clearance reductions, merged galvanic domains or removed fitted loads from the experimental DSN.

## Counts and limitations

The historical corrected R299 result is **1,172 required joins / 1,183 API unconnected items / 499 CLI unconnected diagnostic rows**. Those are three different counters. The a210 cached no-route reference is **1,694 required joins / 1,720 API items**; its source/cache differs, so those figures are not directly comparable with the older full result. Router counters alone are not native PCB connectivity measurements.

The board is substantially incomplete. Global routing experiments and isolated power-placement work are continuing; this bundle makes their actual starting geometry and constraints available for independent review. It does not assert that the placement is routable as-is. Full native refill/DRC, complete power and return paths, current/thermal/signal integrity, FPGA physical implementation and manufacturing qualification remain open. No finished-board or manufacturing release is claimed.

## Later measured routing candidate

[Complete newer KiCad candidate and editable support files](../kicad-candidate-a76e13de-20261018/README.md): six cached native joins closed, zero old pad pairs lost, 1,688 remain. This is a separate unadopted candidate; the a210 starting source above is preserved.

## Later routed KiCad progress

[New complete project and native measurements](../routing-progress-20261018-r1/README.md): 1,688 → 1,687 cached joins, zero prior pad pairs lost. Full refill/DRC and manufacture remain open.
