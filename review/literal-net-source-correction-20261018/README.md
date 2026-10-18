# Literal LED net correction — 18 October 2026

[Complete corrected editable KiCad project](../../archives/three-clamp-native-source-a21004a7.zip). Extract separately and open `native/board.kicad_pro`. Board SHA-256: `a21004a7dbd8e53340bd6882c758185f72e90166d9403dd982d2b8d305bdc9c5`.

The earlier d798 source contains 17 LED segments with literal blank net names. KiCad inferred their intended nets on load, hiding the source emitter defect. This successor corrects those 17 fields: twelve CORE shutdown-LED segments and five FIELD_B shutdown-LED segments. Reversing the substitutions recovers the entire old board byte for byte. Geometry, UUIDs, widths, layers, locks, pads, vias, zones and project support files are unchanged. The older archive is retained as historical evidence.

[Independent source bridge](cached-parent-source-authority-bridge.json) binds each corrected field to the parent's actual native copper net and geometry. [Finite source-to-DSN check](source-forward-finite-check.json) passes all 94,334 copper records and 8,017 vias, including 61 exact short-edge overrides; seven negative controls reject invalid bindings. This is a source/interchange check, not a new native connectivity measurement or routed result. [Emitter controls](emitter-controls.json) exercise explicit rejection of missing/blank/mismatched nets before adding copper and verify saved literals before native reload.

The [parent's measured cached native evidence and physical limitations](../three-clamp-source-20261018/README.md) retain their scope. The corrected source has no new full refill or full-board DRC. Return-plane work, bulk routing, current/thermal/signal qualification, FPGA fit/timing and physical/manufacturing qualification remain open. No board adoption or readiness is claimed.
