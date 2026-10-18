# Verified disconnected SIM2 resource corrections

The three verified implementation fixes are applied to the canonical disconnected runtime. This does not adopt a production profile, qualify physical I/O/timing or finish the motherboard.

The full native T20F256/I4 area2 core map measures **15,805 LUT4 + 2,107 ADD = 17,912**, leaving **1,816** against the conservative 19,728 screen; 10,441 FF, 63 RAM5K and one multiplier are used. All twelve motion generators, four encoders, 256 event records, seven simultaneous event producers and complete protocol buffers remain.

Evidence is separated by scope:

- [Strict original/new queue differential](behavior-receipt.json): 110,592 boundary cases and 28,164,819 logical record comparisons.
- [Independent functional review and mutation controls](../release-review/producer-fifo-independent-supplement-r1/independent-reviewed-overlay-packet.json).
- [Unchanged complete SIM2 runtime suite](full-runtime-independent-r1/receipt.json).
- [Actual native full-core map](native-full-map/receipt.json) and [independent resource/source review](../release-review/producer-full-native-map-independent-r1/receipt.json).
- [Actual mapped event-engine vendor-primitive simulation](postmap-behavior-r3/receipt.json): 23,596 output checks, every producer filled/drained, resets and binary stress. Failed SystemVerilog-mode startup runs r1/r2 and independent model-language reproductions remain separate. Verilog-2005 mode resolves the reproduced Icarus/vendor-model initialization ordering without model edits, internal forcing or skipped clocks.
- [Fresh actual eight-/twelve-joint LinuxCNC integration](linuxcnc-pair-r1/receipt.json), explicit disconnected profiles and virtual STEP/DIR plant. Original settings, fixtures and installed modules are preserved/restored.
- [Canonical adoption and exact backups](canonical-adoption-r1/receipt.json); [guarded rollback](canonical-adoption-r1/rollback.py) restores only if the adopted files still have their expected hashes.

The actual 135-pin physical boundary is independently classified in [the physical wrapper scope](../release-review/physical-wrapper-scope-r1/scope.md). Real record acquisition is reusable, but authenticated physical provenance, complete I/O/handshake integration, physical implementation and timing remain open. A diagnostic-only image must retain inhibited authority and a distinct identity.
