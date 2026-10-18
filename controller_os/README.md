# Motion X12 appliance image system

This subsystem stages our application and desktop shell as a reproducible offline
rootfs overlay. It provides an image manifest, startup checks, a local service
plan, optional kiosk launch and a separate read-only recovery target. It never
installs an OS, writes a disk, enables services, launches the user's desktop,
changes network configuration, connects hardware or flashes FPGA/ESP firmware.

The current approved scope is `dev-x86_64-posix-v1`, an explicitly disconnected
Linux development host. CM4/CM5 Lite/eMMC and exact CB1/CB2 variants remain blocked
compute candidates. No matching approved base image, bootloader, kernel/device
tree, transport or loaded target timing exists in this subsystem. The overlay is
an implemented artifact; it is not a qualified bootable, signed or shipping OS.

```powershell
python tools/controller_os.py profiles
python tools/controller_os.py definition --allow-development
python tools/controller_os.py boot-plan --allow-development
python tools/controller_os.py kiosk-recovery --allow-development
python tools/controller_os.py stage --source-root . --output reports/my-os-candidate --release-id development-r1 --allow-development
python tools/controller_os.py inspect --root reports/my-os-candidate/rootfs --allow-development
```

Stage requires a new directory. Repeating the same release and exact source
bytes produces an identical regular-file-only tar and manifest. Manifest and
source inventories bind all shell/configuration/OS code and web assets, plus the
shared configuration-binding helper and the three-file appliance service package.
Other laboratory scenario tools, preferences and appliance package directories are omitted.
Machine settings, saved generations, allowance ledgers, credentials, diagnostic
history, licences and calibration are kept outside the replaceable image.
Checksums detect corruption; they do not authenticate a publisher or replace
release signing. Recomputing a checksum cannot omit an installed dependency,
alter a generated service command or promote the disconnected guards.

On a staged Linux development filesystem, preflight verifies its image and
observed host, then reads the existing setup integrity, full six-field binding
and matching readiness. It never initializes a store, acquires the export write
lock, restores settings, claims homing or enables motion. Corrupt/stale settings
stay intact and direct the service into recovery. Missing settings remain an
ordinary first-use setup choice. Special files, links and oversized inputs are
refused before reading; a FIFO cannot block startup indefinitely.

The service plan runs `python3 -m controller_shell --directory
/var/lib/controller/workspace --port 8769` as a dedicated unprivileged account.
Preflight precedes every shell launch through `ExecStartPre`, including a later
restart after the separate initial oneshot check has completed. Private devices
hide hardware, and shell network
access is restricted to loopback. Recovery conflicts with the shell and performs
read-only inspection. The optional graphical user kiosk keeps the browser's
sandbox; it requires a separately qualified browser/display session and is never
enabled by staging. Application and browser each have a total three-start budget,
three-second retry delay and deliberate manual retry after exhaustion. The
browser's failure target is user-only and has no application or runtime control.
The kiosk opens `/launch` to honor the guarded startup-page preference; ordinary
Home navigation still opens `/`.
It reports unknown application/runtime/output state without reading or modifying
settings. The existing system recovery target is read-only; application restart
requires fresh evidence and cannot restore homing or machine permission.
No motion-runtime unit exists in this overlay. Runtime lifecycle qualification
remains separate; process independence must not be represented as measured motion
continuity. No default OS target or existing desktop configuration is
modified.

GarciaMech's Motion X12 SVG mark and inert desktop recovery page are local,
checksummed payloads. The staged boot plan proposes quiet/splash service display
while retaining error/recovery diagnostics, but changes no bootloader file.
It records the exact-base initramfs/Plymouth renderer as pending, rather than
claiming that the SVG alone is an installed boot theme. Update/recovery partition
identity, slot count and boot time remain unknown; no fabricated partitions,
bitstream, signed updater or five-to-ten-second startup result is produced.
The recipe follows the [kernel parameter documentation](https://docs.kernel.org/admin-guide/kernel-parameters.html)
and [systemd service](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd.service.xml)
and [unit](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd.unit.xml)
contracts; the exact target still needs its own measurements.

The shell core supports Python3.11+. Compressed backups and diagnostics require
the real `compression.zstd` backend (CPython3.14+ built with libzstd); startup
reports its actual availability. The present isolated Linux Python3.13 test host
correctly reports that feature unavailable. An actual base image must pin and
verify its dependencies before claiming the full appliance experience.

The release still needs exact module/carrier identity, pinned base OS and package
closure, approved boot/storage layout, kernel/device-tree/transport integration,
signed offline updates, interrupted-update/power-loss recovery, preserved media
contracts and physical display/loaded motion tests. Successful application
startup cannot close those gates or grant machine authority.
