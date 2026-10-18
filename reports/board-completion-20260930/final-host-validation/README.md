# Fresh host validation of the current r0.3 motion-card sources

30 September 2026, 14:16:46–14:17:31 UTC. Independent, disconnected host validation under **CPython 3.14.6**. Both requested commands completed with exit code zero. No engineering source was edited or rebuilt during either run.

| Command | Fresh result | Raw output |
| --- | --- | --- |
| `C:/Python314/python.exe -X utf8 -m unittest discover -s tests -p test_motion_card_integration.py -v` | **13 passed**, 0.460 s unittest time | `motion-card.log` |
| `C:/Python314/python.exe -X utf8 -m unittest discover -s tests -v` | **858 reported: 853 passed, 5 skipped**, 39.752 s unittest time | `full-suite.log` |

The five skips are LinuxCNC rootfs-layer symlink tests: symlink creation is unavailable on this Windows host. They remain unexecuted here. The focused 13 cases are also included in the full 858-case suite; these are not 871 distinct tests. Earlier 714-test evidence is untouched and is not reused as this run's count.

`receipt.json` records exact commands, interpreter, UTC timestamps, exit codes, log hashes, parsed summaries and skipped-test names. `source-before.json` and `source-after.json` cover **1,000 text/source files** across `tools`, `tests`, `controller_config`, `controller_backend`, `controller_lab`, `firmware`, `gateware`, `cnc1`, `config` and `hardware`: every before/after hash is identical, with no added or removed file in that scope. The hardware inventory includes the current motion-card design/netlist/schematic and retained native PCB revisions. Binary media/compiled outputs, gallery HTML/JS, build/cache directories, root documentation and report files are excluded; simultaneous root proposal/viewer and accounting-document edits are not hardware validation inputs.

Logs and receipts are written only in this directory. `TEMP` and `TMP` point to `test-artifacts/`, containing temporary disconnected fixtures; Python bytecode writes are disabled. The exact runner that executed is preserved as `run_validation-executed.py`. The initial receipt did not parse the Windows CRLF summary line; `receipt-before-summary-normalization.json` is retained, and only the parser's in-memory text was normalized to derive the final summaries from the unchanged raw logs. `run_validation.py` includes the corrected parser for a future **new** receipt directory and refuses to overwrite an existing run.

This proves the current scoped host tests pass against an unchanged source snapshot. It does not rerun native ERC/DRC, compile target firmware, simulate HDL, vendor-fit the FPGA, operate physical interfaces or measure electrical/timing/thermal/EMC behavior. The partial motion-card remains `manufacturing_ready: false`; full-controller and physical qualification gates remain separate.
