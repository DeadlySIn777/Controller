# FPGA reference endpoint validation — 28 September 2026

**Later integration update:** the [compiled CNC1/actual-LinuxCNC connection](CNC1_INTEGRATION.md) now exercises an opt-in ABI v2 build through Verilator. This report's regression covers the default ABI v1 build plus a separate ABI v2 capability testbench. **Audit-fix rerun, 2026-09-28T19:42:45Z:** the RTL was changed (inhibit synchronization, MISO turnaround, capability-page consumption, Verilog-2001 forms, new `progress_wdi` output) and all figures below come from that rerun. The previous 180-check run (manifest recorded 2026-09-28T06:30:23Z) is historical and archived with its sources in `gateware/validation/before-audit-fixes-2026-09-28/`. Physical transport and vendor target synthesis remain open.

**A functioning RTL reference endpoint has been implemented and simulated. It is source-level engineering evidence, not a manufacturing release or machine-ready controller.** The selected custom CNC1 SPI ABI is distinct from Mesa HostMot2. LinuxCNC needs a new realtime transport component; none is included in this result.

## Implemented scope

| Area | Implemented behavior |
|---|---|
| Six STEP/DIR generators | Atomic signed DDS velocity updates, generated-pulse counters, direction reversal guards, bounded pulse timing |
| Two ABZ inputs | Synchronized x4 quadrature, signed counts, index latches, illegal-transition diagnostics |
| SPI endpoint | Mode 0, exactly 64 bytes, big endian, streaming CRC-16/CCITT-FALSE, coherent response snapshot |
| Command authority | Explicit disarmed fresh-session SYNC, zero-speed ARM, strict increasing sequence, validated UPDATE, DISARM |
| Fault behavior | Link/watchdog/inhibit/timing fault outputs, default-disabled boot, latched recovery, no UPDATE-based auto-resume |
| External inhibit | Asynchronous capture and immediate combinational gating of STEP/DIR/`motion_enable`; every clocked consumer sees it only through a two-flop synchronizer (two to three core clocks) |
| Useful-progress output | `progress_wdi` toggles once per accepted, sequence-valid UPDATE only; cleared by reset |
| ABI v2 discovery | Capability page served by the next transaction and consumed by it whether accepted or rejected |
| Host evidence | Offline Python pack/unpack codec, independent golden command vectors, Python decoding of an RTL-generated response |

The production-default core clock assumption is 50 MHz. The chosen rate cap is 195,312.5 pulses/s per axis; STEP high/low minimum and DIR setup/hold defaults are 2 microseconds. With those 100/100-tick defaults the minimum fault-free STEP period is 201 core ticks (248,756 steps/s), so any rate cap must satisfy `MAX_RATE <= floor(2^32/(PULSE_CYCLES+SPACE_CYCLES+1))` = `0x01460CBC`; the configured `0x01000000` does, and the cap was not changed. The SPI bound is core/8, 6.25 MHz, from input oversampling plus the nominal MISO turnaround (MISO changes three to four core ticks after the SCLK rise, leaving four to five ticks before the next rise at core/8, before pad, trace and master-setup delays). These are reference design choices and RTL arithmetic, not measured board limits. The default communication watchdog is 5 ms; the testbench uses 0.4 ms so fault cases complete quickly.

The core exports one global motion permission and one useful-progress watchdog output. It does **not** implement all 22 field/drive input channels, 14 field/enable output commands, spindle DAC/PWM/0–10 V, probe capture, tool changer, or target pin wrapper, and the board coupling of `progress_wdi` to an external supervisor is not drawn. The hardware predesign remains the separate owner of package/bank allocation, rail/reset gating, drive interface behavior, and the independent external watchdog.

## Actual verification

Executed in WSL distribution `GarciaMechBuilder`, Alpine Linux 3.24.2:

- **Icarus Verilog 13.0, default ABI v1 testbench (`-g2012`):** **252 counted checks passed**: 136 per-transfer status header/CRC checks (68 transfers) and 116 scenario checks across 74 distinct labels. Separately, uncounted continuous `$fatal` monitors on all six channels (STEP high = 100 ticks, STEP low >= 100, DIR setup >= 100, DIR hold >= 100, and no STEP while disabled) abort the simulation on any violation; they are not part of the 252. A MISO monitor measured the data setup before, and hold after, every one of 36,649 SCLK rises: minimum 83.0 ns setup and 63.0 ns hold (zero-delay simulation).
- **Icarus Verilog 13.0, ENABLE_DISCOVERY=1 ABI v2 testbench with production defaults:** **27 counted checks passed** (11 ordinary-status header/CRC checks, 16 scenario checks): capability-page contents, one-shot consumption by valid, bad-CRC and truncated transactions, no `progress_wdi` change across the three disarmed capability requests and their page/consuming transactions (an edge counter, so an even number of spurious toggles is also caught), v1-version rejection, and an armed capability request that disarms without serving a page or toggling `progress_wdi`.
- **Icarus elaboration:** production-default top with `-g2012`, and both the default and ENABLE_DISCOVERY=1 tops with plain Verilog-2005 `-g2005` (the `.v` files no longer use SystemVerilog size casts or loop-scoped declarations).
- **Python 3.14.7:** `binascii.crc_hqx` known-answer check (`123456789 -> 29b1`), three independent command vectors (frame bytes unchanged; files now written with LF), and decode/CRC/field-layout validation of a response captured from the RTL simulation; corrupted CRC and reserved status bits rejected.
- **Verilator 5.048:** `--lint-only -Wall --top-module cnc_endpoint` for the default build, with `-GENABLE_DISCOVERY=1`, and with `--default-language 1364-2005`; all three completed with exit code 0 and no lint suppressions.

The integrated runner completed with exit code 0. The v1 testbench simulated 9.93086 ms and the v2 testbench 1.72764 ms of hardware time. There are Icarus informational `@*` array-sensitivity warnings for the status assembly; these identify inclusion of every array element in the combinational sensitivity set. The strict Verilator lint runs are clean. The recorder also re-derives the fault-free rate bound from the RTL defaults and refuses to record if `MAX_RATE` exceeds it. This report covers RTL simulation, elaboration, codec and lint evidence only; this Alpine environment has no Yosys. The Yosys 0.52 Efinix-family technology mapping of the same RTL, including a structural inhibit clock-domain-crossing check, was rerun in the isolated Debian rootfs and is recorded in [FPGA_SYNTHESIS.md](FPGA_SYNTHESIS.md); vendor (Efinity) T20 synthesis, package fit, timing closure and bitstream remain unproven.

The 252 count includes repeated framing checks; it is not 252 independent operating scenarios and is not exhaustive/formal verification. A mutation run during this fix pass (scratch copies of the RTL, not part of the recorded evidence) confirmed the new checks are discriminating: restoring the falling-edge MISO update fails the core/8 MISO margin check, removing the rejected-frame capability consumption fails the v2 consumption check, toggling `progress_wdi` on ARM or on NOP fails the corresponding progress checks, and toggling it on a disarmed capability request (once, or also on the page-serving NOP) fails the v2 disarmed-capability progress check. Key exercised cases:

| Group | Exercised behavior |
|---|---|
| Boot and recovery | Disabled reset; ARM without SYNC fails; new SYNC clears faults; reset in middle of ARM cannot enable |
| SPI | Independent command vectors; valid response CRC; 5 MHz and 6.25 MHz transfers; core/8 at three SCLK-to-clock phases with MISO setup >= 3 and hold >= 2 core ticks; truncated ARM; truncated UPDATE during motion; overlong ARM; bad CRC; nonzero reserved payload; unknown opcode |
| Authority | Wrong session (ARM and UPDATE); bad-CRC UPDATE; duplicate/out-of-order sequence; changing axis mask; excessive velocity; nonzero ARM velocity; explicit disarm |
| Motion | All six outputs emit positive motion; negative direction reverses counts; continuous 2-microsecond high/low/setup/hold checks during enabled operation; generated-pulse counters equal the internal STEP rising edges across an inhibit and for the whole run |
| Rate bound | Instantiated `MAX_RATE <= floor(2^32/(PULSE+SPACE+1))`; a standalone generator at `0x01460CBC` runs fault-free at the 201-tick minimum period; the 250 ksteps/s increment `0x0147AE14` latches a timing fault |
| Watchdog | Timeout disables; later UPDATE cannot rearm; read-only NOP cannot feed watchdog; held-low CS cannot defeat timeout |
| Progress output | `progress_wdi` clear after reset and after an FPGA reset from high; toggles exactly once per accepted UPDATE; unchanged by a free-running clock, armed motion, SYNC, ARM, NOP, DISARM, truncated, wrong-session, bad-CRC, replayed, out-of-order, over-rate and mask-changing UPDATEs, watchdog expiry, UPDATE after timeout or inhibit, held CS and (v2) disarmed and armed capability requests |
| Inhibit | Asynchronous pad gate; stepgen enables, status permission/ready bits and `endpoint_ready` drop within three core clocks; a modeled sub-clock inhibit pulse latches; UPDATE after the pulse cannot resume; SYNC cannot clear an asserted inhibit |
| Discovery (v2) | Capability page contents; consumed by the next valid, bad-CRC or truncated transaction; armed request is a protocol fault |
| Feedback | Both encoders forward/backward; both index latches; illegal AB transitions; counts while disarmed; response field layout and frozen snapshot; accepted session/sequence |

An inhibit pulse shorter than a clock is a simulation stimulus, **not** proof of the minimum pulse width capturable on a T20 package. The RTL now keeps the asynchronously cleared inhibit flops away from every other flip-flop's D/EN input (a two-flop synchronizer feeds all clocked consumers; the Yosys flow checks this structurally). Because the pads are gated at once but the step generators stop two to three clocks later, an internal STEP edge generated in that window is counted but masked at the pad. Synchronizer metastability/MTBF, pin electrical behavior, jitter, minimum setup/hold at pads, and EMI are outside this functional simulation.

## Preserved evidence and reproduction

- Protocol and integration contract: [`../gateware/PROTOCOL.md`](../gateware/PROTOCOL.md).
- Raw successful output: [`../gateware/validation/simulation.log`](../gateware/validation/simulation.log).
- RTL-produced response used by Python: [`../gateware/validation/status_encoder.hex`](../gateware/validation/status_encoder.hex).
- **Exact SHA-256 hashes** of the validated RTL, both testbenches, protocol codec, runner, vectors, specification, and saved evidence: [`../gateware/validation/manifest.json`](../gateware/validation/manifest.json), recorded 2026-09-28T21:47:55Z (a rerun of the same regression after the recorder gained a read-only `--check`; `python gateware/tools/record_evidence.py --check` verifies the record without writing) with LF line endings (`gateware/.gitattributes` keeps gateware files LF on every checkout). The manifest records source identity, not a signed release or device qualification.
- Previous (historical) 180-check manifest, log and sources: [`../gateware/validation/before-audit-fixes-2026-09-28/`](../gateware/validation/before-audit-fixes-2026-09-28/ARCHIVE_NOTE.md).

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
