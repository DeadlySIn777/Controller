# Bounded signal-via endpoint return gate

The separate `tools/hardware_check_return_corridors.py` accepts actual endpoint antipads while preserving the geometric return requirement. The frozen additive router is unchanged. Import `return_corridor_check(board, added_UUIDs, exact_net_rows)` after native refill/DRC and complete source validation.

Only actual same-net signal through-via endpoints can create an exception. Exact reviewed diameter/drill must match. Each intended reference side needs continuous filled own-return copper around the bounded antipad, plus a through return stitch within1mm that connects to actual numbered source pads and the same filled connected polygon. The full0.20mm annulus and full ground-stitch copper projection are conservative acceptance requirements. Partial plane contact near a keepout does not pass this router.

Outside those exact endpoint voids, every projected route corridor must remain covered. PTH contacts, arbitrary voids, slots, wrong reference domains and disconnected same-named plane fragments receive no blanket exemption. Power, precision and high-speed routing selection remains outside this module.

Nine actual KiCad-runtime/native-fill regression cases passed. Eight native board/DRC fixtures are retained here; the ninth changes the exact manifest via geometry. The valid fixture has zero regular DRC violations and no ignored checks. The old gate rejects its real endpoint antipad, while the new gate passes. Negative fixtures deliberately alter return-domain identity, source connectivity, distance, reference layers or copper coverage and are rejected; their native DRC results are recorded independently, not relabeled passes.

This verifies native geometry and physical connectivity checks on a fixture. It does not establish full-board connectivity, impedance, EMC, target firmware, motion behavior or manufactured reliability. Full integrated native DRC, source/pad preservation and uncapped connectivity remain required after adoption.
