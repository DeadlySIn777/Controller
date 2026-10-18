# Functional verification after Efinix mapping

The DUT is `../results/cnc_endpoint_efinix.json`, exported as Verilog and linked to
the exact installed Yosys Efinix primitive simulation models. Source CNC RTL is
not passed to Verilator. Four C/C++ harness inputs are frozen from
`cnc1/evidence/before-persistent-runtime/cnc1`, insulating this check from concurrent
runtime development. The archived driver's 179 assertions include repeated setup
and synthetic protocol-boundary fixtures, and about 30 of them evaluate host
common code only; this is not 179 independent machining operations or formal
equivalence proof. The harness holds `inhibit_n` deasserted throughout and reads
only the `motion_enable` and `spi_miso` pins; fault and ready state are observed
through the SPI status bytes, not the dedicated output pins, and `progress_wdi`
is not observed.

Run from the Windows workspace root:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware/synthesis/postmap/run.sh
python gateware/synthesis/postmap/record_results.py --check
```

The runner uses the same isolated Debian rootfs as synthesis, clears earlier
generated task-work files (stale Verilator split sources would otherwise be
compiled), copies stable inputs, exports the mapped circuit, generates/compiles
Verilator C++, and runs the existing C driver's bit-level SPI and fault harness.
It neither installs a HAL module nor launches LinuxCNC or physical hardware. Tests
have a 180-second execution timeout after compilation. Generated compiler files
stay in the task rootfs; the saved evidence includes exact inputs, generated
Verilog, diagnostics, the assertion log, package versions and executable hash.

`--check` verifies every recorded hash and re-derives the summary from the hashed
files (PASS count and marker, no FAIL line, exit status 0, Verilator warning
counts, primitive-input and LUT-mask audits, unconnected-output count), then
requires it to equal the recorded summary. It is read-only and does not rerun the
simulation. The manifest is written with LF line endings on every host.

The source-RTL lint result is clean. The mapped netlist's separate Verilator run
uses `-Wall -Wno-fatal` to retain all upstream-model and generated-netlist
diagnostics. The manifest lists them rather than claiming lint-clean output.
Audits prove the narrow LUT masks cannot be indexed beyond their populated bits,
every primitive input is connected/driven, and missing primitive ports are unused
outputs. Remaining unused/undriven warnings concern retained debug aliases, not
undriven circuit inputs. Read the [synthesis report](../../../reports/FPGA_SYNTHESIS.md)
for counts and limitations. No device propagation delays, static timing,
metastability or actual FPGA configuration are modeled.
`before-audit-fixes-2026-09-28/` preserves the previous manifest and its small
hashed files.
