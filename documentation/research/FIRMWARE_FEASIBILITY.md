# Firmware feasibility before buying hardware

**Later implementation evidence:** actual [LinuxCNC simulation/integration](../reports/LINUXCNC_INTEGRATION.md), [FPGA RTL](../reports/GATEWARE_VALIDATION.md) and [ESP32-S3 builds](../reports/ESP_SERVICE_BUILD.md) have now been completed within their documented scopes. The source audit and not-run entries below describe the earlier investigation; consult [current engineering status](../reports/ENGINEERING_STATUS.md) for remaining work.

Audit: 27 September 2026 Halifax / 28 September UTC. This is a source-pinned development audit, not a claim that a production controller or a hardware prototype has been validated.

**Audit-fix rerun (28 September 2026, build recorded 2026-09-28T19:06:41Z):** both host targets were rebuilt and the bounded tests rerun after the record script was changed to derive build status, compiler and distribution from the build logs and `build-record.json` instead of literals. The rerun reproduced every earlier outcome below (same pinned commits; 17 test records with the same pass/timeout pattern; the validator executable is byte-identical, the simulator differs only in its embedded build-info strings). Evidence class: host compilation and host simulation only. The pre-fix record is archived in [before-audit-fixes-2026-09-28](before-audit-fixes-2026-09-28/ARCHIVE_NOTE.md).

**We can run real motion software before ordering anything.** The actual upstream grblHAL host simulator was built here and executed a coordinated line followed by a semicircle. It generated the expected final position: X = 400, Y = 100, Z = -20 steps with 200 steps/mm. That is useful evidence about the interpreter/planner/stepper software. It provides no measurement of a future board's jitter, input latency, electrical noise tolerance, or machine accuracy.

For an ambitious mill/lathe/plasma platform, **LinuxCNC is the strongest feature-ceiling reference in this audit; grblHAL is the easiest actual upstream motion engine to exercise on the existing computer today.** These are separate decisions. Do not choose the final processor simply because one simulator was easy to build.

## What was actually done

| Work | Result | What it establishes |
|---|---|---|
| Pin FluidNC, grblHAL Simulator/core/RP2040/H7, LinuxCNC | Done; exact commits below and in `firmware-sources.json` | Reproducible source references rather than changing branch URLs |
| Compile upstream `grblHAL_sim` | Passed on existing WSL Alpine Linux v3.24, `gcc (Alpine 15.2.0) 15.2.0` (queried at build time; log ends `EXIT: 0`) | Host motion engine can execute locally without a board |
| Compile upstream `grblHAL_validator` | Passed (log ends `EXIT: 0`) | Compilation only; execution problems remain |
| Run actual line + arc through `grblHAL_sim` | Passed: 132 sampled motion records, final steps `[400,100,-20]`, normal exit | Basic planner/step-generation path executes |
| Run parser cases through full simulator check mode | Three valid geometric programs and five expected-rejection cases; detailed records in JSON | Baseline dialect/configuration acceptance and rejection |
| Run standalone validator | Eight bounded cases timed out, including invalid G-code | This target is not an accepted validator for our pipeline yet |
| FluidNC native/WASM build | Not run | Targets and dependencies inspected only |
| RP2350 or H7 firmware cross-build | Not run | Board definitions inspected, not compiled or exercised |
| LinuxCNC build/run | Not run | Source and build/simulation path audited; a fuller Linux dependency environment is still needed |

No toolchain, package, driver, or hardware was purchased or installed. Existing WSL2 distribution `GarciaMechBuilder` contains Alpine 3.24.2 (`/etc/os-release`: "Alpine Linux v3.24") and GCC 15.2.0; the record now takes both from the build run. It lacks CMake/make in its current PATH. Windows has Visual Studio Build Tools, but the grblHAL upstream Windows CI uses MinGW GCC; this audit therefore used existing Linux GCC directly.

The only upstream code patch adds musl's `__DEFINED_time_t` guard to `core/vfs.h`. Without it, the embedded fallback redefines host `time_t` and `struct tm`. The one-line patch is [saved here](../WORKSPACE_REFERENCES.md#artifact-ca7b1213d47d3419). No planner, parser, or step-generation algorithm was changed. GCC also emitted a pointer-size warning at `modbus.c:266`; Modbus was not exercised.

An initial larger simulation with `-t 0`, EOF termination, and M2 did not finish within 30 seconds and stopped recording near its endpoint. This is retained as a limitation rather than treated as passed. The accepted smaller test uses `-t 10`, explicit Ctrl-F graceful shutdown, and no M2. Likewise, the standalone validator's hangs remain unresolved. These observations are about this exact host snapshot/configuration; they do not establish a hardware firmware defect.

## Exact upstream snapshots

| Repository | Commit | Commit timestamp |
|---|---|---|
| [FluidNC](https://github.com/bdring/FluidNC/commit/07bdfcb9eb9d914a2854fbbaca9285b7c45358fa) | `07bdfcb9eb9d914a2854fbbaca9285b7c45358fa` | 2026-09-26 18:13:51 -07:00 |
| [grblHAL Simulator](https://github.com/grblHAL/Simulator/commit/226e2e8c43e9d2d1a34897850246ea53a5b00f79) | `226e2e8c43e9d2d1a34897850246ea53a5b00f79` | 2026-09-25 09:27:25 +02:00 |
| [Simulator and RP2040 pinned core](https://github.com/grblHAL/core/commit/d7aaee3d84b1e7010f075d395206afff038d7379) | `d7aaee3d84b1e7010f075d395206afff038d7379` | 2026-09-23 20:03:29 +02:00 |
| [grblHAL RP2040/RP2350 driver](https://github.com/grblHAL/RP2040/commit/12327965f03c0218afd51d248ee166cfbe902f1e) | `12327965f03c0218afd51d248ee166cfbe902f1e` | 2026-09-23 20:09:15 +02:00 |
| [dresco STM32H7 driver](https://github.com/dresco/STM32H7xx/commit/bfe5d4f6ec271cc9929336244c3b1c8e55d1d040) | `bfe5d4f6ec271cc9929336244c3b1c8e55d1d040` | 2026-06-30 16:35:01 +01:00 |
| H7 pinned core | `26d44fe733292b0c1f453237f3c9c2bdbac2ac67` | Gitlink inspected; this core was not checked out/built |
| [LinuxCNC](https://github.com/LinuxCNC/linuxcnc/commit/086258b4f7beacb84b5deb7416b6d2a9b50f6cc9) | `086258b4f7beacb84b5deb7416b6d2a9b50f6cc9` | 2026-09-28 00:57:55 +02:00 |

The H7 driver is maintained in **dresco/STM32H7xx**, linked by grblHAL's third-party driver index, not `grblHAL/STM32H7xx`. A similarly named fork should not silently replace its upstream. H7 and RP2350 do not currently pin the same core, so a result against the RP2350/Simulator core must not be generalized to the H7 build.

## Supported targets and board-free paths

### FluidNC

The inspected [PlatformIO configuration](https://github.com/bdring/FluidNC/blob/07bdfcb9eb9d914a2854fbbaca9285b7c45358fa/platformio.ini) declares ESP32 and ESP32-S3 targets; it also now declares RP2040, RP2350, native Windows/Linux/macOS, and a WASM browser target. This corrects any earlier assumption that the present tree only targets ESP32/S3. A declared target is not the same as a stable release or proven board configuration. No S31, P4, or C5 target was established here.

The Linux capture target runs substantial real source with host shims and includes parts of the WebUI. The WASM target builds real interpreter/planner source with a browser bridge, but excludes real Wi-Fi/Bluetooth, Trinamic/servo drivers, and most WebUI/VFD integration. Its usefulness is genuine software execution, not emulation of an ESP's exact timers and radio contention. Windows capture also excludes hardware-specific modules.

The project has a [Linux native build workflow](https://github.com/bdring/FluidNC/blob/07bdfcb9eb9d914a2854fbbaca9285b7c45358fa/.github/workflows/linux_x86_64.yml) and a native GoogleTest configuration. The native tests select parser, expression, string, HTTP-command, and configuration helpers rather than proving every motion/hardware path. Next step: create an isolated development environment with PlatformIO/C++ dependencies and build `linux_x86_64`; keep WASM as an additional UI/integration test surface after native execution works. That work has **not** been done in this audit.

### grblHAL with RP2350 or STM32H7

The [RP driver README](https://github.com/grblHAL/RP2040/blob/12327965f03c0218afd51d248ee166cfbe902f1e/README.md) explicitly names `pico2`, `pico2_w`, and the RP2350B board route. Its firmware build uses Pico SDK 2.1.1 and a target compiler. The [H7 README](https://github.com/dresco/STM32H7xx/blob/bfe5d4f6ec271cc9929336244c3b1c8e55d1d040/README.md) identifies H743/H723 development boards, SKR 3 EZ, Octopus Max EZ, and Scylla, with STM32CubeIDE/PlatformIO build routes. This does not establish generic support for every Octopus Pro variant or every H7 chip.

The [Simulator](https://github.com/grblHAL/Simulator/blob/226e2e8c43e9d2d1a34897850246ea53a5b00f79/README.md) wraps the same grblHAL core in host driver implementations. Its fake hardware can log steps and accept synthetic probe, limit, hold, start, and stop inputs. It runs approximately in real time; its timers and concurrency model are not an RP2350 PIO or STM32 timer simulator.

Reuse the core/HAL boundary for machine services and simulation. Preserve driver capabilities as explicit runtime/build configuration: a parser accepting a word does not mean the driver can execute the physical operation.

### Embedded LinuxCNC

LinuxCNC can live **inside the controller enclosure**; the operator's workstation can remain Windows/macOS. The browser/service frontend and ESP companion can run outside the motion deadline. Kernel-level capability concerns the controller's Linux realtime environment and scheduling, not what OS the operator's laptop uses.

The upstream [build guide](https://github.com/LinuxCNC/linuxcnc/blob/086258b4f7beacb84b5deb7416b6d2a9b50f6cc9/docs/src/code/building-linuxcnc.adoc) supports a non-realtime simulation build and `runtests`. The configuration is `./configure --with-realtime=uspace`; `--enable-simulator` is deprecated. Non-realtime simulation is useful for software testing and is not accepted for driving a real machine. Target realtime execution is a separate qualification step.

Before hardware, prepare a Debian-based VM/container or isolated environment, build a pinned release/development snapshot, run the test suite, and instantiate three simulation profiles: mill, lathe, plasma. Simulate feedback plants, spindle index/encoder signals, homing, machine I/O, and ATC sequencing. A VM/WSL test cannot certify the future embedded machine's realtime latency. No LinuxCNC install/build/test was attempted here because its dependency set is substantially beyond the existing Alpine tools.

## Capability ceiling for the proposed controller

“Source present” below means audited code/docs provide a path. It does not mean these features were enabled together, tested here, or qualified on hardware.

| Requirement | FluidNC snapshot | grblHAL snapshot | LinuxCNC snapshot |
|---|---|---|---|
| Coordinated step/dir motion | Interpreter/planner and platform stepping engines | Core plus platform HAL; host line/arc path executed here | Motion controller plus HAL step generators/drivers |
| True controller-side axis feedback loop | No generic industrial axis PID/scale loop established; external servo/closed-loop drive commands are different | No generic per-axis scale/servo loop established in inspected core/drivers; spindle PID does not prove axis feedback control | Explicit position/speed PID components and feedback wiring; qualify chosen drive interface and servo loop |
| G33/G76 lathe threading | Not found in inspected G-code switch | Core spindle-sync option documented experimental; encoder/index driver support and configuration required | Documented G33/G76 and spindle feedback requirements |
| G33.1 rigid tapping | Not found in inspected G-code switch | **Not established.** Core has future hooks and a weak unsupported stub; Simulator/validator explicitly return unsupported | Documented synchronized feed, reversal, and return sequence |
| Probing | G38 paths and machine probe configuration | G38 paths require HAL probe capability; default host input is synthetic | G38 plus HAL input/position capture; physical timing remains a later test |
| Dual-motor gantry squaring | Cartesian code handles motors with individual limits | X/Y/Z auto-square compile options and driver support | Multiple joints, synchronized homing, and joint/axis distinction |
| Nontrivial kinematics | Extensible classes including Cartesian/CoreXY/delta/wall plotter | Kinematics interface and bundled implementations including RTCP AC; individual maturity varies | Broad kinematics/HAL integration path; machine geometry and supported combinations still require validation |
| PLC/ATC/machine sequencing | Macros and tool-changer classes; not an established general PLC | Tool change/ATC hooks, plugins, auxiliary I/O; integration required | HAL/ClassicLadder/remap/tool-change handshakes; machine sequence still must be implemented |
| Plasma | No complete equivalent of QtPlasmaC established in this audit | Plasma plugin exists; driver/THC path must be audited separately | QtPlasmaC is an explicit integrated subsystem; simulate its I/O and process states |
| Feed hold/fault recovery | Protocol and machine states; exact recovery rules need test cases | Protocol/state machine including hold/alarms; no automatic restoration of physically lost position | Feed hold/abort and following-error paths; machine-specific recovery still required |

Evidence for important distinctions:

- [FluidNC G-code dispatch](https://github.com/bdring/FluidNC/blob/07bdfcb9eb9d914a2854fbbaca9285b7c45358fa/FluidNC/src/GCode.cpp) and [Cartesian motor/limit handling](https://github.com/bdring/FluidNC/blob/07bdfcb9eb9d914a2854fbbaca9285b7c45358fa/FluidNC/src/Kinematics/Cartesian.cpp).
- [grblHAL spindle-sync configuration](https://github.com/grblHAL/core/blob/d7aaee3d84b1e7010f075d395206afff038d7379/config.h), [rigid-tapping stub](https://github.com/grblHAL/core/blob/d7aaee3d84b1e7010f075d395206afff038d7379/motion_control.c#L815), and [August 11 future-hooks changelog](https://github.com/grblHAL/core/blob/d7aaee3d84b1e7010f075d395206afff038d7379/changelog.md#L283).
- [grblHAL HAL interfaces](https://github.com/grblHAL/core/blob/d7aaee3d84b1e7010f075d395206afff038d7379/hal.h), [RP driver options](https://github.com/grblHAL/RP2040/blob/12327965f03c0218afd51d248ee166cfbe902f1e/my_machine.h), and [H7 options](https://github.com/dresco/STM32H7xx/blob/bfe5d4f6ec271cc9929336244c3b1c8e55d1d040/Inc/my_machine.h).
- [LinuxCNC PID](https://github.com/LinuxCNC/linuxcnc/blob/086258b4f7beacb84b5deb7416b6d2a9b50f6cc9/docs/src/man/man9/pid.9.adoc), [G-code including G33/G33.1/G76](https://github.com/LinuxCNC/linuxcnc/blob/086258b4f7beacb84b5deb7416b6d2a9b50f6cc9/docs/src/gcode/g-code.adoc), [homing](https://github.com/LinuxCNC/linuxcnc/blob/086258b4f7beacb84b5deb7416b6d2a9b50f6cc9/docs/src/config/ini-homing.adoc), and [QtPlasmaC](https://github.com/LinuxCNC/linuxcnc/blob/086258b4f7beacb84b5deb7416b6d2a9b50f6cc9/docs/src/plasma/qtplasmac.adoc).

## Useful boundary for an ESP companion

Treat communications, job staging, diagnostics, display/pendant services, provisioning, and recovery/update control as candidates for ESP work. Treat its capabilities as separate from authority to generate machine motion. Running FluidNC on the ESP would make it a second CNC interpreter/planner, not automatically a synchronized backup for LinuxCNC or another engine.

A takeover would have to establish position validity, active modal state, tool/work offsets, queued motion, spindle phase, outputs, and exclusive ownership. That is an additional controller design problem. For the early design, a helper may request a stop and report health; it must not silently take over moving axes after a main-controller crash. Simulate these authority rules independently of the choice of MCU.

Use high-level job/control requests across ordinary Wi-Fi/USB/Ethernet. If a separate timing processor is eventually used, define a distinct bounded-latency motion/feedback interface and watchdog contract. Do not equate an ESP HTTP connection or Grbl serial stream with a LinuxCNC cyclic servo link.

## Reproduce the work

The downloaded repositories and binaries are under ignored `research/vendor-src/`. The checked-in record is `firmware-sources.json`, the build/run scripts, and the narrow patch. That record includes exact upstream gitlinks and SHA-256 hashes of evidence files; the patched `vfs.h` hash is explicitly a local modified file. Build status is derived, not asserted: `build_grblhal_wsl.py` queries `gcc --version` and `/etc/os-release`, ends each target log with `EXIT: <code>` and writes `build-record.json` with log and executable SHA-256; `run_grblhal_audit.py` records the SHA-256 of the executables it tested; `record_firmware_sources.py` reports `success` only when the log exit line, recorded exit code and executable hash agree, refuses to pair audit results with different executables, and exits non-zero on any mismatch. Copies of the build record, both build logs and the audit results are kept in [research/evidence/grblhal](../WORKSPACE_REFERENCES.md#artifact-cdb11787b397816e).

From a fresh checkout, clone the repositories, check out the pinned commits, and update Simulator submodules. Apply `patches/grblhal-musl-time-types.patch` **inside the Simulator's `src/grbl` checkout** for musl. The patch is unnecessary on platforms where upstream already recognizes the libc time type.

On this Windows machine:

```powershell
wsl -d GarciaMechBuilder -- python3 /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/research/patches/build_grblhal_wsl.py
wsl -d GarciaMechBuilder -- python3 /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/research/patches/run_grblhal_audit.py
python research/patches/record_firmware_sources.py
```

The build helper follows the `.c` file lists in upstream CMake, uses Linux host definitions and `-fno-strict-aliasing`, and generates only build metadata. The audit script returns failure while any standalone-validator case remains unresolved; this intentionally prevents an all-green result from concealing that problem. Full simulator results and validator results are recorded separately.

## Next work that should happen before selecting boards

1. Make the LinuxCNC simulation environment reproducible and run upstream tests. Separate stable-release qualification from experiments against development HEAD.
2. Turn mill, lathe, and plasma needs into executable acceptance programs and simulated machine profiles. Include spindle reversals, G33/G76/G33.1, probe misses/stuck inputs, gantry skew, ATC interlocks, and plasma voltage/arc faults.
3. Exercise actual upstream feed hold, abort, reconnect, soft limits, overrides, and buffer starvation. Compare traces to explicit expected state transitions. Extend the already-running grblHAL simulator instead of substituting a hand-written motion planner.
4. Build FluidNC native as a second software reference; compare dialect and configuration behavior using the same applicable corpus. Unsupported commands must be visible, not silently translated.
5. Resolve or replace the standalone grblHAL validator path; preserve its upstream issue evidence. Add expression-enabled and axis-count variants deliberately instead of assuming default options cover advanced features.
6. Specify the motion/feedback contract, worst-case rates, trace format, watchdog behavior, startup/output states, and firmware update/recovery protocol. Map those requirements to candidate peripheral resources only afterward.
7. Cross-build proposed MCU firmware with exact SDKs, full plugin/core gitlinks, resource reports, and static analysis. Host simulation and successful cross-compilation are separate gates.

Hardware remains necessary later for actual deadline measurements, electrical interfaces, encoders, drive response, EMC, and machine behavior. There is substantial useful software, interface, and failure-model work to complete before that gate.
