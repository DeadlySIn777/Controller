# Actual twelve-channel HAL refusal qualification

The report-local adapter compiled, loaded and ran in LinuxCNC 2.9.4's actual HAL
scheduler. Six disconnected cases passed 124 executed assertions. All 38 input
source hashes remained unchanged, and all 183 existing installed rootfs modules
were preserved byte for byte. The seven original CNC3 C/H files match the
untouched external IS-1 archive. [Canonical receipt](receipt.json) and
[exact fresh runtime receipt](run-r06/receipt.json) record the commands and hashes.

The adapter exports twelve command pins, twelve feedback pins, twelve independent
STEP-rise monitors and four encoder count pins. Its unchanged copy of the report-local IS-2-compatible C driver
exchanges real 176-byte CS_FB and 96-byte CS_CMD frames through actual Verilated
SPI pins. No capability or feedback byte is synthesized by the host transport.
All twelve HAL command values are present during the refusal test. Feedback is
explicitly invalid, and the independent RTL output-pin monitors observe zero STEP
edges on every channel.

| Executed control | Actual result |
|---|---|
| Incomplete IS-2 profile, enable/reset asserted | QUALIFICATION fault after 128 serial exchanges and 64 CRC-valid CAP3 responses; 12 supported motors/4 supported encoders, zero qualified installed inventory |
| Held reset while enabled | No rediscovery or ARM; authority stays inhibited |
| Stopped reset, then later enable | Fresh discovery reaches the same bounded refusal; totals 256 exchanges/128 CAP3 responses; enable cannot restore authority |
| Returned serial response CRC corrupted by host fixture | BAD_FRAME after one actual SPI exchange; no authority |
| Unavailable encoder or MPG configuration | CONFIG fault before any wire byte |
| Unchanged original IS-1 driver | BAD_CAPS after two actual exchanges; it does not silently accept an IS-2 profile |
| No explicit simulation opt-in | Module fails to load and exports no pins |

The normal test observes zero CONFIGURE, ARM and UPDATE frames, zero endpoint
session, zero enable/armed masks and zero motion/general-output authority in all
four captured snapshots. These are executed refusal controls, beyond module-load
evidence. The CRC control alters a real response after shifting it; it is an
explicit host-link fault fixture, not an RTL-CRC mutation.

The exact endpoint is the unadopted
`reports/cnc3-is2-profile-20261002/profile-candidate-r02/rtl` candidate. Its
constant-false `IS2_PROFILE_COMPLETE` guard is unchanged. The fixture requests
ideal external qualification and all twelve integrated interfaces/class0, so the
test also proves that those ideal inputs cannot override the incomplete-profile
guard. It invents no removable-card presence. The production
`gateware/v3/rtl/cnc3_frame_endpoint.v` is structural; it is not this stateful
candidate or a completed motion controller.

The older stateful motion endpoint lacks CAP3 discovery. The separate
[twelve/four motion candidate evidence](../rtl/README.md) uses explicit bench
qualification and proves generator/encoder/fault behavior. Adding that result to
this inhibited HAL result does not establish one continuous qualified machine.

This run has no LinuxCNC motion-controller trajectory, successful discovery,
ACTIVE HAL-to-STEP motion, working HAL encoder feedback, integrated limits/probe,
complete IOL1 authority, device fit, target timing or physical qualification.
HAL command values are test stimuli, not a commanded coordinated machine path.
The timestamps are actual simulated RTL ticks, and POSIX non-realtime execution
is functional evidence only. Frozen rate and drive-timing limits are unchanged.
`full_requested_milestone_complete` remains **false**.

Run a fresh qualification from the project directory in PowerShell:

```powershell
python reports/rev-a-integration-20261004/host/run_hal.py --out reports/rev-a-integration-20261004/host/run-r07
```

The output directory must not exist. The runner uses the existing
`GarciaMechBuilder` WSL distro and
`/root/.cache/controller-lab-linuxcnc/rootfs`, creates a UUID-keyed work directory,
and uses separate PID/IPC/mount/network namespaces. Literal compiler and runtime
commands are in the receipt's `executions` array. Exact HAL commands and returned
values are retained in `run-r06/HAL-commands-*.log`; package versions and generated
model/binary hashes are retained alongside them. The runner has no device or
network transport and makes no paid-provider call.

Existing rootfs modules are hashed before installation. Only new UUID-named test
modules are temporarily installed. Completed copies are published atomically
without replacement, pending files are cleaned on error, and cleanup runs after
partial installation as well as success. Removal verifies the exact own name,
directory and content hash. Original module inventories are compared after the
run. Each case has its own work-local RTAPI socket, so it does not reuse a user's
existing LinuxCNC socket.

Four independent [inert Linux cleanup controls](../review/module-install-corrected-controls.json)
also passed: second-copy failure, torn pending copy, lost acknowledgment after
successful publication, and fsync failure. No torn module or pending copy remained,
and each restore returned the exact original fixture inventory. These controls
accessed no actual installed rootfs modules.

`run-r01` retains the initial vendor-header warning failure; `run-r02` retains
the inherited daemon-output pipe hang; `run-r03`/`run-r04` retain the HAL component
name/readiness mismatch. `run-r05` passed the runtime before the reviewed cleanup
correction. They are historical attempt receipts, not the canonical current
qualification. Final `run-r06` includes the corrected harness and source binding.

The linked CNC3 sources retain `LicenseRef-Proprietary` notices, and the combined
module descriptor identifies that boundary. This is a local qualification build;
no binary redistribution, licensing resolution or product release is claimed.
