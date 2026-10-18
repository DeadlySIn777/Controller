# Diagnostics and machine-intelligence implementation

4 October 2026. Applied to the local software workbench. Claude retains routing; this pass adds no hardware, firmware, gateware or real-time changes. The [previous readiness work](../readiness-fixes-20261004/README.md) remains separate evidence.

## Delivered

- One validated active simulation definition supplies machine-state identity, configured resources, calculations and illustrative wiring. Typed observations bind to its store, epoch, revision, generation and digest. Measured, commanded, reported, stale and unavailable facts remain distinct; no invented health percentage or motion permission.
- A bounded non-real-time recorder stores checksummed Zstd chunks, pins fault windows, reports gaps/drops and supports host process interruption recovery. Default capture targets are five minutes before and 30 seconds after a fault.
- Offline fault explanations retain provenance, show next checks and readable wiring, and do not infer a successful stop, retained position or cause. Unknown formats remain in the raw report. These operations spend no API credits.
- The same CLI/service/HTTP contract exports strict support, configuration and inert job packages. Configuration recovery uses the existing review/diff/commit flow. Packages exclude the private API allowance and provider data, reject unsafe or oversized members, and never extract or execute contents.
- The UI has a responsive Diagnostics workspace. Its separate version-2 gantry example uses Y on logical M2/display M3 consistently across fault, definition, wiring and export. Earlier example records and customer settings are preserved.

[Usage and limits](../../docs/DIAGNOSTICS_AND_PACKAGES.md) · [One supported machine acceptance path](../../docs/FLAGSHIP_WORKFLOW.md).

## Verified evidence

| Check | Result | Scope |
| --- | --- | --- |
| [Final host tests](host-tests.json), [log](host-tests.log) | 408 reported: 407 passed, 1 skipped; zero failures/errors; source unchanged throughout | Setup, allowance, optional fake-provider AI, configuration/runtime/release regressions and new state/recorder/archive/CLI/HTTP contracts |
| [Source preservation](protected-source-verification.json) | 6,826 original files unchanged | Hardware, firmware, gateware and CNC1 bytes; no new routing qualification |
| Independent service review | 9 final consistency/privacy probes passed; all 7 contract tests pass in the final host run | Temporary disconnected fixtures and actual Zstd export |
| [Browser verification](browser-verification.json) | Desktop/mobile layout, fault semantics, readable wiring and no final console errors | Authored simulation in the in-app browser |
| [Compression measurements](compression-measurements.json) | Exact byte round trips at levels 1, 3 and 6 | Python 3.14.6 on Windows; five wall-time trials per level on repetitive synthetic data |

The skipped test requires Windows file-symlink creation privileges. Archive link-member rejection is separately exercised by passing negative tests. The in-app browser's final saved download file remains unverified because its automation download event timed out; actual CLI files and authenticated HTTP binary round trips passed.

The 331-record example stores **78,595 raw chunk bytes in 2,131 compressed bytes**. Its [actual support archive](example-support-v2.tar.zst) is **6,150 bytes**, with a verified 104,264-byte payload containing the matching authored configuration and report. The highly repetitive 2,000-record synthetic benchmark compresses 2,639,774 bytes to 9,702 bytes at level 3; median host encode/decode times were 0.7454/1.5256 ms. These numbers establish no target CPU budget, realistic retention duration, network benefit or flash-wear savings. Per-record durable publication currently rewrites partially filled chunks; production batching/write amplification needs measurement.

Older `example-support.tar.zst`, `example-setup.tar.zst` and the earlier pre-freeze receipt are retained development artifacts, superseded by the explicitly named v2 support example and final `host-tests.json`.

## Remaining acceptance work

Live transport/discovery, physical commissioning and self-test, measured baselines, calibrated geometry/collision protection, approved whole-motherboard recovery, signed staged updates, paid-model CNC-expert evaluation and loaded target timing remain open. No test here establishes physical stop timing, real-time behavior, target compilation, HDL simulation, FPGA synthesis/fit/timing, circuit ERC, board DRC, actual media power-loss durability or manufacture readiness. Compression needs the optional Python 3.14 standard-library backend; ordinary setup remains usable without it.

Run the disconnected preview with:

```powershell
C:\Python314\python.exe -B -m controller_config setup --directory reports/diagnostics-zstd-20261004/ui-preview serve --port 8769
```

The verification scripts are local, reproducible and do not connect to a controller or paid provider.
