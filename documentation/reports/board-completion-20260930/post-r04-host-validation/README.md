# Fresh post-r0.4 host validation

30 September 2026, **15:13:05–15:13:41 UTC**. Executed after the parent confirmed **MC-r04-rev14** source/research freeze. All three commands exited zero under CPython 3.14.6. Existing `final-host-validation/` evidence remains immutable.

| Command scope | Fresh result | Unittest elapsed time | Raw output |
| --- | --- | --- | --- |
| Footprint envelopes | 8 passed | 0.007 s | [footprint-envelopes.log](../../../WORKSPACE_REFERENCES.md#artifact-498dc68e3dbf732c) |
| MC integration | 16 passed | 0.580 s | [motion-card.log](../../../WORKSPACE_REFERENCES.md#artifact-ae1b63946420449c) |
| Full suite | **869 reported: 864 passed, 5 skipped** | 32.438 s | [full-suite.log](../../../WORKSPACE_REFERENCES.md#artifact-5cac5bf31b1aabb1) |

The five skips are LinuxCNC rootfs symlink cases unavailable on this Windows host; their exact names and reasons appear in [receipt.json](../../../WORKSPACE_REFERENCES.md#artifact-422ccef198d50af6). Focused cases are included in the full 869-case suite, not additional distinct tests. `TEMP`/`TMP` point inside `test-artifacts/` and Python bytecode writes are disabled.

All **1,272 source/research file hashes** are identical in [source-before.json](../../../WORKSPACE_REFERENCES.md#artifact-08fbcfed9c8314c8) and [source-after.json](../../../WORKSPACE_REFERENCES.md#artifact-5272772bc4fa37f9), with no added or removed file in scope. The hash scope covers source/text files in `tools`, `tests`, `controller_config`, `controller_backend`, `controller_lab`, `firmware`, `gateware`, `cnc1`, `config`, `hardware` and `research`, plus retained primary research PDFs. Compiled outputs, binary media, caches, downloaded `vendor-src`, root documentation and report directories are excluded. This extends the earlier ten-directory scope to include primary research inputs; its count is distinct from the earlier 1,000-file r0.3 snapshot.

No engineering source was edited or rebuilt by [the runner](../../../WORKSPACE_REFERENCES.md#artifact-c09cd51fadba5040). Its exact commands, times, source scope, raw log hashes, coherent summary parsing and runner hash are recorded in the receipt. No target compilation, HDL simulation, FPGA vendor fit, native ERC/DRC rerun, physical-interface operation or measurement was part of this run. Manufacturing readiness remains false. Later documentation changes after `source-after.json` do not alter this frozen test snapshot.
