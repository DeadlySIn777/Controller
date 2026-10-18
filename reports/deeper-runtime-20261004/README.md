# Deeper runtime upgrade and qualification

4 October 2026. The new disconnected CNC3 SIM2 integration passes actual LinuxCNC task/planner/HAL execution with twelve active joints and with eight active joints, while keeping all twelve interfaces fitted. This is a substantial improvement over the earlier refusal-only and ideal-provider checks. It is laboratory software/simulation evidence. Physical authority, commissioning and manufacturing readiness remain false.

The user's subsequent OS request also produced an implemented dark red shell and reproducible application overlay. See the [OS experience report](../os-experience-20261004/README.md). Claude's PCB routing, the adopted motherboard sources, existing customer settings and external IS-1 archive were not changed by this work.

## Current evidence and gaps

| Category | Result | Evidence and practical limit |
|---|---|---|
| SOFTWARE PASS within scope | Reviewed setup binding, host admission, independent provider freshness, event lineage, guarded UI and offline staging | [Setup controls](setup/run-r06/receipt.json), [host report](host/README.md), [provider receipt](providers/receipt-r03.json), [OS report](../os-experience-20261004/README.md) |
| SIMULATION PASS within FREE joint scope | Actual twelve- and eight-joint task motion through C driver, shifted SPI, compiled current RTL and an independent STEP/DIR plant | [Twelve: 67 observations](host/nml-r07/linuxcnc.json); [eight: 64 observations](host/nml-eight-r02/linuxcnc.json). Cartesian machining, index homing, machine kinematics and loaded real-time deadlines are unqualified. |
| FPGA PASS not achieved | Generic family mapping completed; the functional SIM top fails the coarse T20 resource screen | [RTL receipt](rtl/receipt.json): 34,493 LUT4, 7,776 ADD, 9,900 FF, 64 RAM5K. No vendor device placement, routing, timing or qualified bitstream. |
| PHYSICAL VALIDATION REQUIRED | Zero physical measurements | Actual transport/acquisition, firmware execution, interlocks, electrical loads, analog accuracy, thermal/power-fail behavior, homing and target OS performance remain open. |

[Machine-readable gaps and current-source recheck](gaps.json) verify 94 current source files with zero mismatch or conflicting hashes and retain `full_requested_milestone_complete=false`. These labels do not promote production readiness from a passing simulation.

## Implemented path

The reviewed configuration service supplies one exact store/epoch/revision/generation/configuration-digest/draft-digest binding. The new adapter verifies the complete trusted runtime source inventory and explicit encoder mapping before preparing an exclusive simulation manifest. Its timing, velocity, motor/encoder/I/O masks and STEP/DIR polarity checks retain the existing electrical and motion bounds. Configuration review does not restore output permission or homing.

The actual execution path is LinuxCNC NML/task → FREE joint planners → HAL motor command pins → C CNC3 SIM2 driver → actual SPI signal shifts → current compiled `cnc3_runtime_sim` RTL → an independent mechanical model that observes STEP/DIR/enable → ABZ and serial feedback. Host position counters do not substitute for emitted pulses. Every selected lane has observed positive joint velocity, emitted STEP and accepted plant movement; the eight-joint profile emits no STEP on lanes 8–11.

The runs exercise four ABZ paths with index captures, both probe inputs, 24 virtual DI, 16 virtual DO, drive alarm inhibition during task motion, sticky faults and a deliberate stopped reset into an unarmed/unhomed session. All I/O and encoder ratios are authored laboratory stimuli. The HAL snapshot sequence guards adapter-owned outputs; it does not make NML status and external HAL input commands one atomic snapshot.

Concrete corrections include READY output-watchdog keepalives, reviewed alarm polarity, per-session event acknowledgement/deduplication reset, full provider identity and CRC/sequence/age checks, a watchdog recovery delay after clearing a forced fault, invalid HAL mask/period refusal and bounded DDS admission. The LinuxCNC client uses a real HAL observer, a short executable DISPLAY entry, bounded jog receipt checks and actual observed reset-button release. Temporary HAL modules use exclusive atomic publication and digest-checked cleanup.

## Verification

| Execution | Current result | Counting rule |
|---|---:|---|
| Setup adapter | 15 Python test methods; 38 observations | [Exact run](setup/run-r06/receipt.json) |
| Twelve-joint LinuxCNC | 67 observations; 374 C/SPI assertions; 18 compiled C manifest controls | [Source-bound receipt](host/nml-r07/receipt.json) |
| Eight-joint LinuxCNC | 64 observations; the same 374 C/SPI assertions and 18 manifest controls | [Source-bound receipt](host/nml-eight-r02/receipt.json); repeated controls are not new unique tests |
| Standalone current host sanitizer | 374 C/SPI assertions and 18 strict compiled C manifest controls passed with ASan, UBSan and leak detection | [Source-bound execution](host/sanitizer-r02/receipt.json); no address, undefined-behavior or leak diagnostics |
| Independent provider | 504 checks in normal and ASan/UBSan execution; 12 deliberate mutations detected | [Exact receipt](providers/receipt-r03.json); do not add the normal and sanitizer counts |
| Current RTL | 1,190 wire assertions, 11 event-storage assertions, 7 provider-boundary assertions, 10,000 default-deny cycles; three mutations detected | [Exact receipt](rtl/receipt.json); the event-storage total includes the preceding nine-assertion suite |
| Independent review | Both 71-file runtime closures, copies, bindings, logs, saved settings and all 183 pre-existing lab modules checked | [Runtime review](review/final-runtime-r01/receipt.json), [host boundary review](review/host-boundary-review-r01.json) |

The standalone host sanitizer run executes the current C driver, actual SPI, compiled RTL and independent virtual plant; it is separate from the ordinary NML process and provider-only sanitizer run. The first attempt retained a LeakSanitizer infrastructure failure because the chroot lacked `/proc`. The same exact compiled binaries then passed in an isolated namespace with `/proc`, a fresh context and strict reader controls that require the correct exit/text and empty stderr. A sanitizer crash cannot count as a successful refusal. No full LinuxCNC process sanitizer qualification is implied.

The report-local serialized event-RAM experiment passed its wire/differential controls and reduced RAM5K from 64 to eight. It increased LUT4 to 35,757, so it was **not adopted**. [Resource analysis](rtl/resource-experiment.md) and [independent experiment review](review/serialized-storage-review-r01.json) preserve this result. Reusing that prototype would not solve device fit or timing.

Failures and earlier source revisions remain in their own run directories. The initial final-report source recheck deliberately failed because it selected OS run-r02 after the FIFO guard correction; [that failed recheck](gaps-recheck-r01.json) is retained. The canonical gap report selects current OS run-r03. It does not rewrite the earlier receipt or call the old execution current evidence.

[Preservation check](preservation-r03.json) compares the original 24 feature files, 3,308 protected source files, 20 external archive files, 21 existing settings files and 20 regression files to the earlier baseline. New SIM2, shell and OS additions are recorded separately. The earlier [508 passing host tests plus one privilege skip, 5,441 diagnostic C checks and four ARM builds](../deep-upgrade-20261004/README.md) remain historical source-bound evidence; those totals were not rerun or added to this report's counts.

## Reproduce within the disconnected lab

Use new exclusive output paths. Exact commands, versions, snapshots and logs are retained alongside each run:

```powershell
python cnc3_runtime/run.py --motors 12 --linuxcnc --out reports/my-new-runtime-12
python cnc3_runtime/run.py --motors 8 --linuxcnc --out reports/my-new-runtime-8
```

This requires the existing isolated LinuxCNC lab environment. It uses POSIX callbacks and a compiled RTL model that may advance slower than wall time. The virtual core remains 50 MHz and the watchdog remains 5 ms. It is not the physical CNC3 backend. No device connection, paid API request, FPGA flash, service installation, existing module replacement or routing edit was performed.
