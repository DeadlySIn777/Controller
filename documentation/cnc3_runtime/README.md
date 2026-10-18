# Disconnected CNC3 SIM2 runtime

This directory implements a current executable integration candidate: LinuxCNC
task/NML and FREE joint planners → twelve HAL command/feedback interfaces → C
CNC3 driver → actual shifted 96-byte command / 176-byte feedback SPI pins →
compiled `gateware/v3/runtime/cnc3_runtime_sim` → independently observed virtual
STEP/DIR mechanics, four ABZ sources and virtual digital/probe inputs/outputs.
The eight-joint profile keeps all twelve interfaces fitted and leaves four unused
lanes inhibited. The historical six-joint/two-encoder and incomplete-profile
refusal results remain separate evidence.

Only the explicit Verilator/virtual-provider backend is implemented here. The
physical IS-1 archive is untouched; the retained physical drivers do not accept
this separate SIM2 identity. `physical_authority` and
`production_profile_complete` remain false, and the ordinary gateware wrapper
does not admit the simulation context. No device, network or motion-hardware
backend is selected by these runners.

Preparation consumes an exact reviewed six-field saved SetupService binding,
recomputes mechanics and saved maximum velocity, checks 50MHz timing and DDS
carry bounds, and binds the complete current runtime source inventory and an
explicit lab encoder mapping into full SHA-256 digests. All configured encoders
in the authored qualification fixtures map one edge per electrical motor STEP,
3200 edges per revolution. Source geometry deliberately starts at electrical
step3198 so actual movement crosses index3200; RTL emitted/encoder counters start
at their own zero baseline, so tests compare deltas. Lab acceleration40mm/s²,
plant geometry and repeated trivkins coordinate letters are authored test
conditions, never inferred physical machine commissioning or homing.

The LinuxCNC HAL adapter requires explicit environment opt-in and successful
shared Python verification before creating the fixture. Its C reader separately
refuses malformed/duplicate JSON, invalid guards, unsupported channels/encoders,
unsafe rates and inconsistent selected encoder periods. The environment-provided
verifier is a trusted lab orchestration input; this is not an authentication
boundary against arbitrary software that controls the process environment.
The provider ledger independently binds full configuration/source digests and
strict monotonically advancing context records, with freshness and CRC checks.
Provider lineage stays continuous when the motion session restarts.

Commissioning requires real capability discovery/configuration, both timed
watchdog selftests, continuity acknowledgment, independent output-gate/OPI
handshake and neutral readback. READY sends actual neutral IO_WRITE watchdog
feeds while waiting for the deliberate reset action. ARM requires a later enable
edge and a fresh timed reset press/release. Faults preserve the first cause;
stopped reset starts a new session without motion or homing. New-session event
acknowledgment/deduplication resets while historical captures stay recorded.

From Windows in this repository, with the existing disconnected LinuxCNC2.9.4
rootfs in WSL `GarciaMechBuilder`, reproduce into a **new** evidence directory:

```powershell
python cnc3_runtime/run.py --motors 12 --linuxcnc --out reports/deeper-runtime-20261004/host/new-12-run
python cnc3_runtime/run.py --motors 8 --linuxcnc --out reports/deeper-runtime-20261004/host/new-8-run
```

The runner preserves source snapshots, manifests, literal build/run commands and
results. It compiles against the rootfs ABI, atomically installs one uniquely
named temporary module, runs in isolated mount/PID/IPC/network namespaces, and
restores the complete prior installed module inventory even after partial install
failure. Original saved setup bytes are checked before/after. Qualification
fixtures under the host report are explicitly authored separate stores; the
runner does not commit or change customer configuration.

Receipts distinguish actual task/planner execution and serial/RTL simulation
from physical target compilation, loaded realtime deadlines, electrical behavior,
IOL1 hardware links, Cartesian kinematics, physical homing, FPGA device fit,
manufacture and physical commissioning. Retained C sources identify
`LicenseRef-Proprietary`; the local combined module descriptor retains that
boundary. These runs do not qualify binary redistribution or release.
