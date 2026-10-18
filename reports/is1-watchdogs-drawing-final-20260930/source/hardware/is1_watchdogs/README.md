# IS-1 timer frontends — standalone review candidate

Dual TPS3851G18SDRBT supervisors with independent 3.3 nF C0G timing capacitors, separate WDI rail buffers and wired-AND RESET/WDO health through two Schmitt channels. This block is **not connected to the controller assembly**, not a complete permission circuit and not ready for manufacture.

Both MR pins are explicitly unconnected per frozen IS-1. The INTERNAL REVIEW BOUNDARY symbol is excluded from BOM/board; it is not a fitted connector. The custom DRB0008A copper candidate does not qualify stencil, thermal, guarding or PCB layout.

**Unresolved startup interface:** 100 kΩ request/progress pulls do not override the T20's configuration pull-ups. Raw FPGA SET1/progress defaults, driven-low voltage margin, low-supply/partial-power behavior and complete permission latches require further review. No physical 20 ms claim is made.

See [block report](../../reports/next-implementation-20260930/IS1_WATCHDOG_BLOCK.md), [design](design.json), [native ERC](erc.json), [validation](validation.json) and [BOM](bom.csv). Rebuild with `tools/hardware_build_is1_watchdogs.py`, export only this schematic's netlist/ERC, then validate with `tools/hardware_validate_is1_watchdogs.py --check`. Timing analysis is separate in `tools/is1_watchdog_analysis.py`.
