# FPGA reference endpoint validation — 28 September 2026

**A functioning RTL reference endpoint has been implemented and simulated. It is source-level engineering evidence, not a manufacturing release or machine-ready controller.** The selected custom CNC1 SPI ABI is distinct from Mesa HostMot2. LinuxCNC needs a new realtime transport component; none is included in this result.

## Implemented scope

| Area | Implemented behavior |
|---|---|
| Six STEP/DIR generators | Atomic signed DDS velocity updates, generated-pulse counters, direction reversal guards, bounded pulse timing |
| Two ABZ inputs | Synchronized x4 quadrature, signed counts, index latches, illegal-transition diagnostics |
| SPI endpoint | Mode 0, exactly 64 bytes, big endian, streaming CRC-16/CCITT-FALSE, coherent response snapshot |
| Command authority | Explicit disarmed fresh-session SYNC, zero-speed ARM, strict increasing sequence, validated UPDATE, DISARM |
| Fault behavior | Link/watchdog/inhibit/timing fault outputs, default-disabled boot, latched recovery, no UPDATE-based auto-resume |
| Host evidence | Offline Python pack/unpack codec, independent golden command vectors, Python decoding of an RTL-generated response |

The production-default core clock assumption is 50 MHz. The chosen rate cap is 195,312.5 pulses/s per axis; STEP high/low minimum and DIR setup/hold defaults are 2 microseconds. The SPI bound is core/8, 6.25 MHz under the documented oversampling/guard assumptions. These are reference design choices, not measured board limits. The default communication watchdog is 5 ms; the testbench uses 0.4 ms so fault cases complete quickly.

The core exports one global motion permission. It does **not** implement all 22 field/drive input channels, 14 field/enable output commands, spindle DAC/PWM/0–10 V, probe capture, external watchdog progress output, tool changer, or target pin wrapper. The hardware predesign remains the separate owner of package/bank allocation, rail/reset gating, drive interface behavior, and the independent external watchdog.

## Actual verification

Executed in WSL distribution `GarciaMechBuilder`, Alpine Linux 3.24.2:

- **Icarus Verilog 13.0:** RTL plus testbench compiled; simulation completed with **180 explicit checks passed**, including repeated response header/CRC checks and continuous pulse timing monitors on all six channels.
- **Icarus default-top elaboration:** production parameter values elaborated separately from the shortened-watchdog testbench.
- **Python 3.14.7:** `binascii.crc_hqx` known-answer check (`123456789 -> 29b1`), three independent command vectors, and decode/CRC/field-layout validation of a response captured from the RTL simulation; corrupted CRC and reserved status bits rejected.
- **Verilator 5.048:** `--lint-only -Wall --top-module cnc_endpoint` completed with exit code 0, no lint suppressions.

The integrated runner completed with exit code 0. It simulated 6.81132 ms of hardware time. There are Icarus informational `@*` array-sensitivity warnings for the status assembly; these identify inclusion of every array element in the combinational sensitivity set. The strict Verilator lint run is clean. No Yosys/Efinix synthesis was run; Yosys was unavailable in the selected Alpine package repository.

The 180 count includes repeated framing checks; it is not 180 independent operating scenarios and is not exhaustive/formal verification. Key exercised cases:

| Group | Exercised behavior |
|---|---|
| Boot and recovery | Disabled reset; ARM without SYNC fails; new SYNC clears faults; reset in middle of ARM cannot enable |
| SPI | Independent command vectors; valid response CRC; 5 MHz and 6.25 MHz transfers; truncated ARM; truncated UPDATE during motion; overlong ARM; bad CRC; nonzero reserved payload; unknown opcode |
| Authority | Wrong session; duplicate/out-of-order sequence; changing axis mask; excessive velocity; nonzero ARM velocity; explicit disarm |
| Motion | All six outputs emit positive motion; negative direction reverses counts; continuous 2-microsecond high/low/setup/hold checks during enabled operation |
| Watchdog | Timeout disables; later UPDATE cannot rearm; read-only NOP cannot feed watchdog; held-low CS cannot defeat timeout |
| Inhibit | Asynchronous gate behavior in RTL; a modeled sub-clock inhibit pulse latches; SYNC cannot clear an asserted inhibit |
| Feedback | Both encoders forward/backward; both index latches; illegal AB transitions; counts while disarmed; response field layout and frozen snapshot; accepted session/sequence |

An inhibit pulse shorter than a clock is a simulation stimulus, **not** proof of the minimum pulse width capturable on a T20 package. Clock-domain synchronization, metastability, pin electrical behavior, jitter, minimum setup/hold at pads, and EMI are outside this functional simulation.

## Preserved evidence and reproduction

- Protocol and integration contract: [`../gateware/PROTOCOL.md`](../gateware/PROTOCOL.md).
- Raw successful output: [`../gateware/validation/simulation.log`](../gateware/validation/simulation.log).
- RTL-produced response used by Python: [`../gateware/validation/status_encoder.hex`](../gateware/validation/status_encoder.hex).
- **Exact SHA-256 hashes** of the validated RTL, testbench, protocol codec, runner, vectors, specification, and saved evidence: [`../gateware/validation/manifest.json`](../gateware/validation/manifest.json). The manifest records source identity, not a signed release or device qualification.

From the workspace root on Windows:

```powershell
python gateware/tools/protocol.py --write-vectors
wsl -d GarciaMechBuilder -- sh -lc 'cd /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/gateware && sh tools/run_tests.sh > build/simulation.log 2>&1'
python gateware/tools/record_evidence.py
```

For a clean checkout, run `sh gateware/tools/run_tests.sh` once without redirection or create `gateware/build` before shell redirection. Redirection happens before the runner can create its build directory. Linux requires Python 3 and Icarus Verilog; install Verilator and its development include files for the second check. Scripts do not open hardware devices. Source changes require rerunning validation and regenerating the manifest; the recorder preserves the supplied successful log and source hashes but does not itself rerun a simulation.

## Remaining release gates

1. **Realtime host driver:** exclusive SPI ownership, deterministic transfers, velocity scaling, response pipeline/acknowledgments, fresh-session handshake, timestamp/epoch handling, error latching, LinuxCNC HAL integration, and real servo timing on the chosen ROCK 3C RT image. The Python command/stat/error frontend is not that driver.
2. **Target implementation:** Efinix device/package choice, clock/reset primitives, MISO tri-state pad, bank voltages, exact pin allocation, timing constraints, synthesis resource fit, place/route, timing closure, boot/configuration, and power-sequencing review. No T20 bitstream is produced.
3. **Complete machine I/O:** the field input/output/enable/drive-alarm/analog paths above need separate RTL, ABI extensions, and tests. Existing reserved bytes confer no actuator functionality.
4. **Physical fault and motion validation:** output disable during power loss/reset/FPGA reconfiguration; independent watchdog during FPGA clock halt; drive-side interpretation of disabled/high-impedance outputs; probing/limits and actual feedback; noise and thermal behavior; controlled recovery on a guarded test rig before an installed machine.

Faults, reset, DISARM, and external inhibit can truncate a STEP pulse. This is **not controlled deceleration**; emitted-pulse counters do not prove drive acceptance or physical position after interruption. Position recovery and the mechanical consequences of abrupt loss of drive permission require machine-specific design. The clocked FPGA watchdog cannot detect loss of its own clock, so the separate external watchdog/driver gate is essential. The ESP service node has no motion authority in this architecture.
