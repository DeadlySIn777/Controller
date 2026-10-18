# CNC1 six/two Efinix-family synthesis

`run.sh` performs actual Yosys technology mapping of the current reference RTL,
with `ENABLE_DISCOVERY=1` for the compiled HAL driver's ABI2. It runs strict
Verilator lint, structural checks, latch exclusions and a final fully mapped
circuit check. It writes Efinix-primitive JSON/EDIF and a hash manifest.
`cdc_check.ys` then re-reads the RTL as plain Verilog-2005 (no `-sv`) and
asserts structurally that the raw `inhibit_n` pin and the flip-flops it clears
asynchronously reach a flip-flop D/EN input only in the inhibit capture flops and
the first stage of the two-flop synchronizers. That is a netlist-structure check,
not a metastability/MTBF analysis.

It does **not** choose package pins, apply device timing constraints, run vendor
placement/routing, generate a bitstream or establish T20 fit. Read the
[result and limitations](../../reports/FPGA_SYNTHESIS.md).

The existing isolated Debian rootfs inside WSL `GarciaMechBuilder` now contains
Debian `yosys` and `yosys-abc` version `0.52-2`; the runner does not install tools.
It uses a private mount/PID namespace with a temporary `/proc` mount so Yosys can
find its technology data without modifying the host mount namespace. No physical
devices or machine connections are opened.

From the Windows workspace root:

```powershell
wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware/synthesis/run.sh
python gateware/synthesis/record_results.py --check
```

`CONTROLLER_SYNTH_ROOTFS` may name another prepared isolated Debian rootfs.
The copied `input/` RTL identifies the exact synthesis input. The manifest also
hashes current `gateware/rtl/` and rejects differences. `results/` contains the
successful final run; the runner clears earlier task-work results first, so no
stale file from a previous run is copied back. `attempts/` preserves two
development-script failures: the parameterized top initially needed an explicit
normalized name, then strict mapping rejected harmless `$scopeinfo` hierarchy
metadata. The final script fixes those tooling issues without changing RTL; only
the final cleaned netlist is exported. `--check` re-derives the summary from the
saved output and verifies hashes; it does not rerun synthesis. The recorder writes
the manifest with LF line endings on every host so the hash chained into the
post-map manifest does not depend on the recording platform.
`before-audit-fixes-2026-09-28/` preserves the previous manifest and its small
hashed files.
