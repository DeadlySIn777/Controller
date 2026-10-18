# Native MC r0.4 review: published PCB revision 20260930-14

30 September 2026. This is a **partial motion card**, not a complete controller or a manufacturing package. The [immutable validation receipt](review.json) records fresh KiCad10.0.4 checks, independent source-contract validation and uncapped physical connectivity. All105 scoped inputs stayed unchanged during that run; copied inputs are under `source/`.

- 327 physical source parts,1,229 fitted pads and382 represented native nets. All327 footprints now have source assignments; none is placement-only.317 package models are available; ten bodies remain omitted explicitly.
- The parent-only changes close nine missing courtyards, promote the previously inspected Y1001 oscillator footprint, and change three exact H-grade supervisors from reel to tube ordering. The original child circuits and earlier published PCBs are preserved. Rounded oscillator lands remain an explicitly unqualified assembly/process difference.
- The [retained-copper receipt](../routing-integrated-v5/motion-card-retained.receipt.json) proves1,229 pad geometries/net assignments and all673 existing track/via items unchanged, with no net renames. This increment did not reduce the711 required missing joins.
- [Strict native ERC](native-erc.json): zero violations and `ignored_checks: []`. The fresh XML export agrees with the independent fitted-source contract across1,229 fitted pins.
- [Strict native DRC](native-drc.json): zero regular violations, `ignored_checks: []`,499 capped unconnected items and the expected violation exit code5. **DRC does not pass.** No missing courtyard exclusion was added.
- [Independent physical inventory](fresh-native-routing-inventory/review.json):106 of203 multi-pad nets fully joined,97 incomplete,711 missing physical cluster joins; the uncapped KiCad connectivity count independently agrees.106 source-declared NC pads are retained, with no orphan copper or fitted pad/net mismatch. Missing circuits and connectors are not counted as NC.

Native schematic source/PDF are under `hardware/motion_card/`; the [published native routed candidate](../../../hardware/board_review/revisions/20260930-14/motion-card-route-candidate.kicad_pcb) is editable in KiCad. Its220×100mm outline, six copper layers and1.6mm thickness are layout assumptions. No final stackup, planes, complete BGA escape, mechanical/connector approval or physical measurements are established by this review.

The subsequent [post-r04 host regression](../post-r04-host-validation/receipt.json) reports869 cases:864 passed and five existing Windows symlink cases skipped, with1,272 scoped hashes unchanged during the disconnected run. Eight envelope cases and16 MC integration cases are included in those869. No target compilation, HDL simulation or vendor device fit was rerun by this hardware-source increment.

The [current readiness report](../READINESS.md) records the actual missing controller functions, physical-contract conflict, incomplete manufacturing files and separate current sourcing evidence. `manufacturing_ready` remains false.
