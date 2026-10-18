# Actual FPGA synthesis: six STEP/DIR, two ABZ, CNC1 ABI2

28 September 2026. **The current RTL completes actual Yosys synthesis into Efinix-family primitives.** Hierarchy/driver checks, strict mapped-circuit checks, latch exclusions and a structural inhibit clock-domain-crossing check pass. This advances the evidence from RTL simulation to technology mapping; T20 package fit, routed timing and a working bitstream remain unproved.

**Audit-fix rerun.** The figures below are from the rerun recorded at 2026-09-28T19:22:22Z (synthesis manifest) and 2026-09-28T19:24:08Z (post-map manifest), after the RTL gained two-flop inhibit synchronizers, the MISO update one tick after the detected SCLK rise, rejected-frame capability consumption, Verilog-2001 forms and the `progress_wdi` output. The previous run (synthesis manifest 2026-09-28T08:18:18Z: 3,215 `EFX_FF`, 9,420 mapped cells, 19 ports / 32 bits; post-map manifest 08:23:40Z) is historical; its manifests and small hashed files are archived in `gateware/synthesis/before-audit-fixes-2026-09-28/` and `gateware/synthesis/postmap/before-audit-fixes-2026-09-28/`.

## Result

The input is the current `cnc_endpoint`, `cnc_spi_frame`, `cnc_stepgen` and `cnc_encoder` source (the same files the RTL regression hashes). Synthesis explicitly sets `ENABLE_DISCOVERY=1`, matching the compiled driver's ABI2. All other values remain the baseline: six STEP/DIR channels, two ABZ encoders, assumed 50 MHz core, 100-cycle pulse/space/direction intervals, 250,000-cycle watchdog and maximum DDS rate `0x01000000`. No full field-I/O implementation or eight/four expansion is included.

| Mapped primitive | Actual instances |
|---|---:|
| `EFX_LUT4` | 4,072 |
| `EFX_ADD` | 2,132 |
| `EFX_FF` | 3,221 |
| `EFX_GBUFCE` | 1 |
| `EFX_RAM_5K` | 0 |
| Total circuit cells | 9,426 |

The six additional flip-flops relative to the historical 9,420-cell run are the two two-flop inhibit synchronizers (four), the registered SCLK-rise strobe for MISO and `progress_wdi`; the LUT and adder counts are unchanged. The final top has 20 logical ports containing 33 bits (the new one-bit `progress_wdi` output). Those are core interface signals, **not** an assigned physical pinout or the complete controller GPIO budget. MISO output and output-enable are separate signals awaiting the real device pad/interface implementation.

The T20 v6.0 datasheet lists 19,728 equivalent logic elements, 204 memory blocks and 36 multipliers; F256 advertises 195 GPIO under its documented conditions. Its logic cell contains a four-input LUT or adder plus a register. These advertised capacities and Yosys primitive counts are different quantities. We do not sum primitive counts into occupied LEs or claim a utilization/fit percentage: device packing, routing, control distribution and vendor mapping have not been established. [Efinix T20 datasheet, pages 4–7](https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf)

## What actually ran

- **Verilator 5.048**: `--lint-only -Wall -GENABLE_DISCOVERY=1`, with no warning suppression; zero warnings/errors.
- **Yosys 0.52**, Debian package `0.52-2`, git identity `fee39a3284c90249e1d9684cf6944ffbbcbb8f90`, and matching `yosys-abc`: SystemVerilog elaboration, explicit parameter selection, checked hierarchy and process conversion, then `synth_efinix` technology mapping.
- Structural `check -assert` and final `check -assert -mapped`: zero reported problems, including the checks for conflicting drivers, undriven wires and combinational loops covered by that pass. Latch-selection assertions pass. This is not a formal proof of functional equivalence or exhaustive correctness.
- `cdc_check.ys` re-reads the four RTL files as plain Verilog-2005 (no `-sv`), flattens the unmapped design and asserts that every sequential element is an asynchronously reset `$adff` and that the combinational cone of `inhibit_n`, `inhibit_sync` and `inhibit_authorized` reaches a flip-flop D/EN input only in those two capture registers and the first stage of the two synchronizers. Yosys keeps each register as one multi-bit `$adff` cell, so exactly four cells are permitted: the 3-bit `inhibit_sync`, the 1-bit `inhibit_authorized` and the two 2-bit synchronizers `inhibit_ok_ff`/`authorized_ff` (whose second stage is fed only by their first). The pre-fix RTL does not parse as Verilog-2005; read with `-sv` in a scratch run, the committed script fails earlier, at the permitted-cell count (`select -assert-count 4 @allowed` finds only 2 cells, because the synchronizer registers do not exist), and never reaches the cone assertion. The cone assertion itself was shown to discriminate on two scratch mutants of the fixed RTL: routing the step-generator enable back to `motion_enable`, or qualifying SYNC with the raw `inhibit_sync[2]` instead of the synchronized `inhibit_ok_s`, each fails `select -assert-none @captured @allowed %d` (both scratch runs, not recorded evidence). It is a structural netlist check, not a metastability or MTBF analysis.
- The recorder independently checks final JSON cell types, ABI parameter, six-step/two-encoder/`progress_wdi` port widths, equality with final statistics and the CDC check marker, then hashes sources, tool identity files, scripts, lint output and generated evidence. It writes the manifest with LF line endings; the previous manifest had been written with CRLF on Windows, so the hash chained into the post-map manifest only verified on that checkout. The runner now clears earlier task-work results before copying them back.

Yosys's supplied Efinix flow maps arithmetic and registers to EFX primitives and uses ABC four-input LUT mapping. It has no T20F256C4 selection argument or placement/routing stage. The installed backend's help is saved with the results. [Official Yosys Efinix synthesis command](https://yosyshq.readthedocs.io/projects/yosys/en/v0.53/cmd/synth_efinix.html)

The run uses only the existing isolated Debian 13 rootfs under WSL `GarciaMechBuilder`; no tool was installed globally into Windows or the Alpine host. The dpkg `Installed-Size` metadata recorded by the run in `results/package-sizes.tsv` is 25,753 KiB for `yosys`, 12,925 KiB for `yosys-abc` and 390 KiB for `python3-click` (39,068 KiB, about 40 MB; package metadata, not a measured disk delta). The download size of that installation was not logged; the earlier "11.3 MB downloaded" figure has no saved evidence and is withdrawn. A private namespace provides `/proc` for Yosys. No hardware devices were opened.

Expected diagnostics remain visible: the six-word `rates` array is lowered into registers, and ABC notes that its extracted LUT network is combinational. Neither is a width/driver error. The FPGA has genuine sequential cells outside that ABC combinational mapping stage. Two earlier runner failures are preserved in `gateware/synthesis/attempts/`: parameterized-top naming and nine non-circuit `$scopeinfo` entries. The final script normalizes the top name and removes only that metadata before the strict check and **before exporting both final netlists**. Those tooling fixes did not edit RTL.

## Evidence and reproduction

- [Synthesis script](../WORKSPACE_REFERENCES.md#artifact-e8f4b97debde51ed) and [isolated runner](../WORKSPACE_REFERENCES.md#artifact-f5a98ed567c4d238).
- [Raw successful synthesis log](../WORKSPACE_REFERENCES.md#artifact-f8757faf033a6c06) and [final resource statistics](../WORKSPACE_REFERENCES.md#artifact-3a8cee9717dc69e8).
- [Mapped JSON netlist](../WORKSPACE_REFERENCES.md#artifact-14e0b621ed3d5057) and [EDIF netlist](../WORKSPACE_REFERENCES.md#artifact-62ea20a314edd026).
- [Structural inhibit CDC check](../WORKSPACE_REFERENCES.md#artifact-3837eeb035ece1aa) and its [log](../WORKSPACE_REFERENCES.md#artifact-fc8e8d138328c2ff).
- [Source/tool/evidence manifest](../WORKSPACE_REFERENCES.md#artifact-6579ca541a3d89cd), with copies of the exact input RTL and hashes of the Yosys/ABC executables and Efinix mapping libraries.

From the Windows workspace root:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware/synthesis/run.sh
python gateware/synthesis/record_results.py --check
```

The second command re-derives the summary from the recorded evidence and checks it and the current source identity; it does not rerun synthesis. The earlier [RTL simulation evidence](GATEWARE_VALIDATION.md) and [actual LinuxCNC/RTL integration](CNC1_INTEGRATION.md) remain separate. No board bitstream has been generated.

## Functional verification of the mapped circuit

After mapping, the final JSON netlist was exported to Verilog and compiled with the exact installed Yosys Efinix primitive simulation models in Verilator. **All 179 assertions in the frozen CNC1 compiled-driver harness passed with this mapped circuit** (the same 179 labels as the historical run). The original CNC RTL was not used as the DUT in this run. The driver, header, bit-level SPI simulator and test source were copied from the complete `before-persistent-runtime` archive to avoid mixing this check with concurrent host/runtime changes; they were left frozen because they remain compatible with the changed RTL (the simulator samples MISO at the SCLK rise, the driver reads the capability page with the transaction immediately after its request, and it does not reference the new port).

What the harness does and does not exercise on the mapped netlist:

- It covers discovery, signed commands on all six channels, emitted-count feedback, varying ABZ/index inputs, CRC/replay/session/sequence/truncation rejection, link loss and the watchdog drop of the `motion_enable` pin, and recovery without automatic arm.
- About 30 of the 179 assertions evaluate host common code only and never involve the netlist in their own condition: 7 decode rejections of host-mutated copies of the capability frame, 5 CRC/counter/index/rate unit checks, 3 host timing/sequence guards, 12 `cnc1_configure` API checks and 3 fixture/simulation-guard checks (source-inspection count of the frozen `test_driver.c`). The count also includes repeated setup assertions.
- "Configuration inhibit" in the harness means the host driver's stopped-configuration lock (`cnc1_configure`), not the FPGA `inhibit_n` input. The simulator holds `inhibit_n` deasserted for the whole run, so the mapped hardware-inhibit path, including the new synchronizers, is **not** exercised post-mapping.
- The only output pins read are `motion_enable` and `spi_miso`. The four fault outputs, `endpoint_ready` and `progress_wdi` are not observed; fault and ready state is observed only through the SPI status bytes.

This is a compiled-driver functional run, not an actual LinuxCNC session against the mapped circuit, exhaustive equivalence proof or device timing simulation.

Mapped-netlist lint is separate from clean source-RTL lint. It reports 465 unused-signal, 78 missing-pin, 11 selection-range, four unnamed-generate, two filename and two undriven-debug-wire diagnostics (historical run: 471 unused-signal, others identical). The run retains them using `-Wall -Wno-fatal`. The missing pins are unused primitive outputs; an independent netlist audit checks all primitive inputs are present and driven. Yosys emits 385 two-bit, 1,250 four-bit, 1,240 eight-bit and 1,197 sixteen-bit LUT masks (historical: 384/1,302/1,200/1,186). The upstream untyped model selects from a nominal 16-bit mask, causing range diagnostics for shortened parameters; every input above the populated mask's address range is proven tied to zero. Unused/undriven debug aliases do not feed primitive inputs. No RTL or primitive-model patch was used to hide these diagnostics.

Reproduce the separate check with:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware/synthesis/postmap/run.sh
python gateware/synthesis/postmap/record_results.py --check
```

The [post-mapping manifest](../WORKSPACE_REFERENCES.md#artifact-6ec08d523c343618) hashes the frozen C/C++ inputs, primitive models, generated Verilog, originating mapped JSON/synthesis manifest, commands and results. Its `--check` now re-derives the assertion count, absence of FAIL lines, exit status, warning counts, primitive-input and LUT-mask audits from those hashed files and requires them to equal the recorded summary (previously it only compared hashes and printed the stored count). The runner now deletes stale Verilator output from earlier runs; the first rebuild in this pass failed because a leftover split `.cpp` file from the historical run was compiled, and no evidence was recorded from that attempt. [Raw assertion output](../WORKSPACE_REFERENCES.md#artifact-1fd20af347571e1f) and [full Verilator diagnostics](../WORKSPACE_REFERENCES.md#artifact-70bf25781d2cdc29) are preserved. This simulation uses zero-delay functional primitive models: routing delay, clock skew, setup/hold, metastability, physical inhibit-pulse capture and the selected package remain unqualified.

## What this resolves and what remains

The specific concern that the existing ABI2 RTL might be unsynthesizable or contain inferred latches is now checked in a real synthesis flow. The primitive inventory gives a concrete starting point for the next device implementation review. It does not prove the 50 MHz assumption: `CORE_HZ` is a design/protocol parameter, not an applied static-timing constraint or a clock measurement.

Next, create the grounded Efinity project for the selected part/package/grade, with actual oscillator/reset/clock and pad interfaces; exact pin/bank/rail allocation; justified timing/CDC constraints and synchronizer placement; the board coupling of `progress_wdi` to the external watchdog and the inhibit connection; and the remaining field I/O. Confirm vendor acceptance or run vendor synthesis directly, then place/route and inspect complete timing and resource reports. Prove reset/reconfiguration/power-loss output states and boot storage before generating a release candidate bitstream. Physical SPI, encoder, pulse, fault and loaded host measurements remain required. The separate expanded eight-motor/four-encoder proposal needs its own synthesis and board allocation.
