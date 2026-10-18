# Controller OS experience and image contract

4 October 2026. The user wants an appliance that feels like a polished modern operating system: a dark interface with red accents, smooth touch navigation, fast startup, guided setup and required software prepared beforehand. Linux remains the underlying platform, with LinuxCNC providing the motion engine. The product interface, startup, settings and recovery experience are ours to integrate. This explicitly authorizes the new OS shell alongside the Rev A integration work; Claude retains PCB routing.

The implemented `controller_shell` home page uses the existing configuration/readiness service. Machine setup, drive details, review, diagnostics and recovery retain the same validation, transactions, electrical limits and API allowance protections as the public CLI. Home reads configuration-bound evidence. It never enables motion or makes paid requests. The generic machine drawing is an illustration, not verified geometry or a collision model.

Navigation preserves real edits through the guarded save path, leaves an untouched provisional template unsaved, and keeps failed/stale saves on screen. The interface marks unavailable service data as unavailable rather than displaying cached checks as current evidence. It supports keyboard focus and reduced motion, uses local assets and modest opacity/transform transitions, and avoids continuous decorative animation. The development preview was exercised at 800×480, 390×844, 1280×800 and 1920×1080. These are browser viewport checks, not physical touchscreen compatibility or measured frame pacing.

Run a separate explicitly selected workspace without altering an existing preview:

```powershell
python -m controller_shell --directory reports/my-os-preview --port 8770
```

`controller_os` provides structured profile inspection, deterministic offline application-overlay staging, checksummed closure verification, read-only startup inspection and read-only recovery. It stages the application, web assets and separate service/kiosk definitions into a new directory. It does not install services, write a disk, include customer settings or credentials, download packages, flash firmware or claim a signed/bootable release. Current staging permits only the explicitly selected Linux x86_64 development profile. CM4, CM5, CB1 and CB2 image profiles remain blocked until their exact carrier/module/boot/kernel/transport combinations are qualified.

The development service plan binds only to loopback, separates the graphical session from the application and recovery checks, limits application privileges/devices, and keeps settings outside the replaceable image. Successful application startup does not restore position, homing, commissioning or output permission. Startup must inspect a previously saved configuration without creating lock/export artifacts in a read-only workspace. Package compression availability is checked explicitly; missing support is unavailable evidence.

The shipping image must bind exact purchased compute SKU/revision, carrier/selector, storage, bootloader, kernel/PREEMPT_RT configuration, device tree, graphics/touch drivers, physical CNC3 backend, gateware/service versions and application hashes to qualified results. A checksum alone is not release authentication. Signed staged updates, slot/rollback behavior, interrupted power and protected settings/entitlement recovery remain qualification work.

Performance acceptance must include cold boot to the usable interface, ordinary touch response, frame intervals, memory and storage consumption, thermal throttling and loaded motion latency under concurrent rendering, recording, transfers and permitted AI work. The existing 60 Hz / under-100 ms ordinary feedback targets remain unmeasured on the controller hardware. Start the memory study at the retained 2 GB eMMC compute configuration; increase it only with measured need. UI/conversion/AI work must not consume the motion engine’s scheduling budget. Screen size never changes fitted channels or licensing.

See [OS implementation and evidence](../reports/os-experience-20261004/README.md), [current runtime integration](../reports/deeper-runtime-20261004/README.md), [boot/storage requirements](BOOT_STORAGE_AND_PROVISIONING.md), [compute-carrier requirements](COMPUTE_CARRIER_STRATEGY.md) and [display tiers](DISPLAY_TIERS.md).
