# Native hole model for the Rust routing experiment

This is a derived routing input for the pinned FastRoute engine at `parisxmas/fastroute` commit `19c3b75322da6a0dc2f87a616fc0afe34a98f07e`. It is not a new PCB or routed result. The [complete native project](../../archives/joint-global-R3-exact-native-project.zip) remains the physical authority.

- Native PCB SHA-256: `a693477c5a71e26db86345ea2a356ad20519d301989d2f0e3506a8142f23c595`.
- Original adjacent DSN SHA-256: `62ec8575ada2eea4df0adadbcb8852b647e395f8b239dd86e6c62eb48275c683`.
- [Derived board.dsn](board.dsn) SHA-256: `a77c79df61e9ae8d363046477bfe7982ca32ef34b6e66a5176ef7853794de687`.

The engine otherwise invents a drill radius from pad size when its padstack name has no encoded drill. That creates fictitious holes in SMD pads and understates some actual through-hole drills. This input adds 146 engine-readable padstack aliases and changes 2,735 image-pin references: 9,112 native copper-bearing SMD pads and 10 connectors have zero drill, 504 round PTH pads use their actual native drill, and eight slots use conservative enclosing circles based on maximum drill dimension. All 8,015 existing vias and 17 explicit NPTH keepouts remain unchanged. The 320 native SMD pads omitted by the original DSN export are paste/mask-only, with no copper layers.

[Native pad/hole targets](native-pad-and-hole-targets.json) bind the 9,634 exported contexts to actual source references, pads and nets. The [independent delta review](hole-alias-delta-review.json) verifies that reversing only the added definitions and alias references recovers the entire original DSN syntax tree, including copper, placement, layers, clearance rules and all 238 power reservations with 19 owned windows. This corrects the router model without reducing electrical constraints.

The loader resolves four pad contexts to equivalent alternative aliases and 352 contexts to a 180-degree pin rotation. The former require explicit equal-copper/pose/drill checks in the guarded wrapper. The latter use one exactly centrally symmetric integer polygon; [the exact finite-copper proof](rotation-Cu-equivalence-review.json) closes every affected context. These exceptions do not permit arbitrary missing pad mappings.

Actual startup still must pass all per-pin identity/net, drill-model, original fixed-session and protected-copper gates before routing. The original native no-route preservation result is not a routed AFTER result. Genuine native refill, saved/reloaded connectivity, DRC, retained reference/current paths, assembly and physical qualification remain required. Manufacturing readiness is false.
