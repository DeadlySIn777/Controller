# Frozen r0.3 motion-card evidence

Recorded 30 September 2026. This snapshot preserves the actual 327-part r0.3 source and published PCB revision `20260930-12`, with 673 track/via items. It is not the complete controller or a manufacturing package. The 65 captured input hashes in `review.json` were unchanged during the native checks.

Fresh native KiCad 10.0.4 ERC reports zero violations. The fresh XML export has the same 1,473 connected source pin entries as the parent XML (including logical boundaries); the source-contract validator checks all 1,229 fitted pins and passes. The separate physical routing inventory checks the real native copper: 106 of 203 multiple-pad nets fully joined, 97 incomplete, 711 uncapped missing joins, 106 source-declared native-NC pads and no orphan copper. Missing controller circuits/connectors are outside this inventory and cannot be relabeled NC.

Native DRC reports zero regular violations under its original defaults and 499 capped unconnected items; its nonzero exit code is preserved. **This is not a DRC pass.** The additional `strict-rules-review/` copy enables every originally ignored ERC/DRC check: strict ERC remains clean, while strict DRC reveals **nine missing courtyards** on U2001–U2005, L2001/L2002 and U3001/U3002. The missing courtyards are real source/assembly-rule work and must be fixed in a later revision; they are not suppressed or hidden by this snapshot. Neither review modified source pads, copper or original project files.

The parallel [frozen host validation](../final-host-validation/README.md) reports 13 focused passes and 858 total tests (853 passes plus five Windows-symlink skips), with 1,000 source files unchanged during that run. Those results are host/source checks; no target compile, vendor FPGA placement/timing or physical measurements occurred here. Native circuit/board checks and physical copper inspection are separate evidence classes.

No Gerber, drill, CPL or release assembly package is generated from this incomplete PCB. Source/native exports are retained for engineering review only. The live viewer may now show a later revision; this archive remains the recorded r0.3 evidence.
