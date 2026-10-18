# Current CNC3 SIM2 host integration qualification

**PASS within the disconnected simulation scope.** The canonical
`receipt.json` binds the current71-source runtime closure to fresh twelve- and
eight-joint LinuxCNC2.9.4 executions. This is positive actual task/planner/HAL/C
driver/SPI/compiled-RTL/virtual-provider evidence, exceeding the earlier
incomplete-profile refusal run. It grants no physical authority or manufacturing
readiness. The external IS-1 archive and old receipts remain unchanged.

## Exact final evidence

| Current source run | Actual LinuxCNC NML observations | Actual C driver/SPI assertions | Compiled C manifest controls |
|---|---:|---:|---:|
| `nml-r07` —12 active/12 fitted |67 PASS |374 PASS |18 PASS |
| `nml-eight-r02` —8 active/12 fitted |64 PASS |374 PASS |18 PASS |

Both source snapshots and saved setup stores stayed byte-identical through each
run. All183 pre-existing installed rootfs modules match their before/after hashes;
the uniquely named temporary module was removed. Independent final review is
`../review/final-runtime-r01/receipt.json`, which also checked source closure,
copies, manifest bindings, log hashes, settings and the live installed modules.

The current complete standalone C driver/SPI/compiled-RTL/ProviderPlant chain
also passes374 assertions under combined AddressSanitizer and
UndefinedBehaviorSanitizer, with leak detection enabled (`sanitizer-r02`). The
same current sanitized C reader passes18 adversarial cases; an additional
strict-child control requires exact ACCEPTED/REFUSED stdout, exact exit0/1 and
empty stderr, so a sanitizer crash cannot count as a valid refusal
(`sanitizer-reader-strict-r01`). No address, undefined-behavior or leak diagnostic
was reported. This supplemental run did not install modules or repeat NML.
The first sanitized build succeeded but execution lacked a chroot proc mount;
LeakSanitizer could not enumerate its process tasks. That failed
`sanitizer-r01` execution stays recorded separately. Fresh namespace-correct
execution used the exact hash-verified sanitized binaries, a fresh reviewed
simulation context and unchanged current71-source closure.

The actual path is LinuxCNC task/NML → FREE joint planners → HAL motor command
pins → the new C CNC3 SIM2 driver → actual shifted SPI pins on the compiled
current `gateware/v3/runtime/cnc3_runtime_sim` → independent virtual mechanics
observing STEP/DIR/enable → actual ABZ inputs and serial feedback. No feedback
frames are fabricated or replaced by ideal host counters. Concurrent observations
contain positive actual joint velocities, command positions, independently
observed STEP rises and accepted model movement on every selected lane. Twelve
active lanes share one armed observation; the eight-joint run leaves lanes8–11
at zero STEP with twelve still fitted.

All four ABZ paths return serial counts and actual index capture records. Both
probe inputs produce capture events across the frozen event transport. Walking
each of24 virtual DI and16 virtual DO verifies serial input/application readback
and the independent output gate domain. An individual simulated drive alarm
during task motion cuts all motion and produces an actual endpoint fault; removing
the alarm does not restart motion. Explicit stopped reset creates a new motion
session, retains an inhibited/unhomed state and keeps provider sequence lineage
advancing. Probe/index historical capture counts remain available after reset.

## Concrete defects corrected

* READY originally sent NOP after IO_ENABLE and expired the independent5ms output
  watchdog while waiting for the deliberate reset press. It now sends actual
  acknowledged neutral IO_WRITE keepalives.
* Healthy alarm-current polarity now comes from the reviewed normally-current-high
  configuration; the independent provider emits configured sense XOR authored
  fault rather than tripping every selected lane at startup.
* Stopped SYNC originally retained old event ACK/deduplication sequence1, which
  could lose the first different event1 of the new session. Per-session fields
  reset after successful SYNC while historical records/counters are preserved.
  The independent compiled-C control is
  `../review/event-session-control-r02/receipt.json`.
* Maximum velocity is checked per saved channel, actual DDS rate words are bounded
  against high+low+carry timing, malformed/duplicate JSON is refused, invalid HAL
  command masks cannot consume a sequence/UPDATE, and invalid callback periods
  cannot advance unbounded virtual time. The first host fault remains latched.
* The LinuxCNC client now attaches a read-only HAL observer; uses an executable
  short DISPLAY entry with explicit environment paths; distinguishes continuous
  jog command receipt from completion; and waits for actual observed reset-button
  release before enabling. The eight-joint failed attempt demonstrated the last
  race: the endpoint refused ARM with0x08000000 and zero emitted motion. The
  corrected run waits for ProviderPlant's observed held=false, never a fabricated
  readiness flag.
* Temporary module publication uses reviewed complete-copy/fsync/atomic-link
  semantics and cleanup after an attempted partial install. No installed module
  is overwritten or removed on a mismatched digest.

Failures remain recorded in `driver-r01`, `driver-r02`, `driver-r03`,
`nml-r01` through `nml-r05` and `nml-eight-r01`. Earlier positive `driver-r04`
and `nml-r06` are retained as their own source-bound evidence. The DISPLAY
truncation failure's original `linuxcnc.j` content is preserved separately as
`retained-r04-linuxcnc-j.json`; old execution receipts are not rewritten.

## Reproduction and boundaries

The existing isolated WSL `GarciaMechBuilder` rootfs supplies LinuxCNC2.9.4,
gcc/g++14.2 and headers. Verilator is the WSL compiler. Exact literal commands,
package versions, source snapshots, reviewed manifest, binaries and logs are in
each final run directory. From the workspace in Windows PowerShell, use new
output paths:

```powershell
python cnc3_runtime/run.py --motors 12 --linuxcnc --out reports/deeper-runtime-20261004/host/new-12
python cnc3_runtime/run.py --motors 8 --linuxcnc --out reports/deeper-runtime-20261004/host/new-8
```

Only explicit disconnected simulation is supported. The environment-supplied
verifier is a trusted orchestration input; generic arbitrary process startup is
not an authenticated manifest boundary. Preparation and the qualified runner
require the complete current runtime source inventory and exact saved six-field
binding before fixture creation. Provider records additionally compare full
configuration/source SHA digests, context, CRC, sequence and age.

All joints in these profiles are authored LINEAR/mm FREE-mode coordinates. The
repeated trivkins letters load the actual motion/task stack without claiming
customer Cartesian kinematics. Encoder mapping is explicitly authored one edge
per STEP and3200 edges/revolution; the plant starts at3198 while emitted/encoder
RTL counters retain their own baseline, so qualification compares deltas.
Acceleration40mm/s² and geometry are lab assumptions, not physical commissioning.
I/O walking uses deliberate HAL virtual stimuli; it does not prove LinuxCNC M64
or G38 sensor integration, physical index homing or hardware limit wiring.

The run uses POSIX non-realtime callbacks and a compiled RTL model that can run
slower than wall time. The actual virtual core stays50MHz, the watchdog remains
5ms and timing/rate/electrical limits are unchanged. Loaded target deadlines,
physical measurements, electrical loads, physical IOL1 links, FPGA device fit,
ERC/DRC, manufacturing and physical commissioning are unqualified. The production
completion/physical-authority outputs remain false; the ordinary gateware wrapper
does not admit a simulation context. `full_requested_milestone_complete` therefore
remains false. Retained proprietary-source licensing is not a binary release or
redistribution qualification. No paid API or hardware device connection was used.
