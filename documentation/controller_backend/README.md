# LinuxCNC software simulation adapter

`LinuxCNCBackend()` starts disconnected and imports no LinuxCNC bindings until
an explicit `connect()`. It only accepts the checked-in simulation profile,
verified by path and manifest. It has no web listener, machine auto-connect,
or production hardware mode. Profile verification is an accidental-use guard,
not an authentication/security boundary against a malicious local user.

Controls are one-use, session-bound, sequenced, expiring requests. Every accepted
request is consumed before state checks; failed requests are never retried.
Reconnect drops requests and the loaded-program identity. Poll freshness is a
service-level check, **not a measured servo heartbeat**. A disconnect drops UI
authority and does not claim to stop an independently running controller.
Request expiry is checked after status refresh and before every command write,
including the motion command after a mode transition. Controller errors latch
until explicit reconnect. Abort and power-off remain available after a latched
controller error, subject to usable channels and a fresh request.

The adapter uses LinuxCNC's actual `command()`, `stat()`, and `error_channel()`.
It is the sole error-channel reader for the headless demo. The external operator
lease/supervisor and realtime HAL/SPI implementation remain separate components;
this Python adapter must never generate cyclic SPI motion traffic.
One service thread owns an adapter instance; it is not thread-safe. Motion,
homing, pause and resume dispatch asynchronously. Their returned status is a
sample, **not a completion acknowledgement**; observe the subsequent controller
state and errors. Mode changes, program-open, power changes and abort use bounded
completion waits. The runtime demo demonstrates why these distinctions matter.

Host-only contract tests (no LinuxCNC and no hardware):

```powershell
python -m unittest discover -s tests -p test_linuxcnc_backend.py -v
```

See `reports/LINUXCNC_INTEGRATION.md` for real-runtime evidence, scope, and exact
commands. The dedicated HAL profile loops ideal commanded position directly to
feedback; it loads no physical hardware driver and qualifies no real timing.

CLI demonstration on a Windows workspace with a WSL distro and the already
provisioned isolated Debian runtime. Run from the repository root; `wsl` starts
in the translated current directory and the launcher locates itself with
`dirname "$0"`, so no machine-specific path is needed (substitute your distro
name for `GarciaMechBuilder`, the one used on the recording workstation):

```powershell
wsl -d GarciaMechBuilder -- sh controller_backend/run_isolated_simulation.sh
```

The recorded runs used the equivalent absolute form
`wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/controller_backend/run_isolated_simulation.sh`.

The launcher copies this package into a private root filesystem and runs
LinuxCNC with private PID, IPC, mount and network namespaces. No existing UI or
machine configuration is launched. Each run first deletes the previous work
copy inside the rootfs and removes generated state from the fresh copy
(`evidence/`, `.runtime/`, LinuxCNC `*.var*` parameter files, `position.txt`,
`__pycache__`), so a run starts only from the checked-in package and profile.
It writes a fresh run ID, a checks report, and sampled trajectory JSON. A
subsequent run replaces those generated files.

All launchers and `fetch_debian_rootfs.py` locate the rootfs through
`$CONTROLLER_LAB_ROOTFS` (default `/root/.cache/controller-lab-linuxcnc/rootfs`);
the provenance record `debian-rootfs-source.json` lives in its parent directory.
The fetcher verifies the pinned manifest, image config and layer digests and
extracts layers through `rootfs_member_filter`, which keeps Debian modes,
ownership and absolute symlinks but refuses members that escape the
destination (including writes through an earlier symlink, and symlink members
whose last name component is `.` or `..`), escaping hard links and device
nodes/FIFOs. Extraction requires a Python whose `tarfile` re-filters its
link fallback (CVE-2025-4138 fix, detected by `tarfile.LinkFallbackError`:
CPython 3.12.11+, 3.13.4+ or 3.14+); on older builds the fetcher exits before
downloading. `verify_cached_layers.py` re-checks that filter against a cached
pinned layer archive without downloading anything.
