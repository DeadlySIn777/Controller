# Preserved engineering milestone

This directory preserves tested work while the main workspace is receiving concurrent changes. It is an engineering evidence package, not firmware to flash or a manufacturing release.

- `source-snapshot.json` identifies the exact host-test source and fixture files. **290 Python tests pass**; see `python-tests.txt`. Backend profile assets were missing from the first copied fixture; that failed output is retained, and the completed fixture passed a full rerun.
- `proven-runtime/` preserves the exact earlier recorded LinuxCNC milestone: **192 compiled checks, 26 runtime checks and 59 persistence checks across nine launches**. All62 source/evidence entries and the compiled module match their recorded hashes. The initial CLI schema predates subsequent envelope changes. No physical transport is implied.
- `proven-spi/` preserves the checked Linux SPI backend, exact header and recorded binaries: **892 normal and892 sanitizer assertions**, C++ linkage, zero physical device opens. Its original header was recovered from the verified runtime archive after the shared header changed.
- `source/gateware/synthesis/` preserves actual Efinix-family mapping and the **179-check mapped-netlist simulation**. This uses frozen pre-persistence driver sources. Device fit, routed timing and bitstream generation remain open.
- `hardware-check.json` records fresh ledger/netlist checks: zero errors,54 open design items, and both six-joint TX/two-ABZ RX blocks consistent with the copied ledger. Existing KiCad ERC exports contain zero violations. Full board design and qualification remain unfinished.

The `source` directory is a host-test fixture and evidence copy, not a deployable Linux image or a combined production source release. `component-verification.json` records where the shared runtime/SPI sources changed after recorded evidence. Do not treat those partial current-component copies as freshly tested motion firmware; use the separate `proven-runtime` and `proven-spi` snapshots for the exact historical checks.

Run the frozen Python checks from `source` with `python -m unittest discover -s tests`. Do not run generators in the snapshot if you need to retain its recorded hashes. The main review is [durable-hardware-review.json](../durable-hardware-review.json).
