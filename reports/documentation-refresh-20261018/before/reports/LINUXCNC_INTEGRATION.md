# LinuxCNC integration: actual software execution

28 September 2026 UTC. **The real LinuxCNC motion stack executed successfully in an isolated software-only profile.** This is separate from the adapter's fake-API contract tests and the earlier grblHAL simulator tests.

## Implemented

`controller_backend/linuxcnc_backend.py` calls upstream `linuxcnc.command()`, `stat()` and `error_channel()` through an explicit-connect adapter. Construction neither imports LinuxCNC nor connects. Hardware mode is rejected. Before opening a command channel it verifies the exact package simulation INI path, the initialized XYZ status, and hashes of the INI, HAL and display launcher. This is an accidental-use guard, not a security boundary against a local user who can rewrite files.

Controls have session IDs, strictly advancing sequences, single-use tokens and expiry. Rejected requests are consumed. The adapter checks request expiry after status refresh and before **each** command write, including after changing mode. Stale samples, wrong profiles, modified/reordered/replayed requests, nonfinite status and channel loss cannot silently issue fresh motion. Error-channel failures latch; normal motion then requires explicit reconnect. Reconnect discards all pending controls and the loaded-program identity and sends no control command. It does not stop or rewind an independent controller.

Program loading is confined to named `.ngc` files under the simulation profile and requires a matching SHA-256; run/resume recheck the file. MDI accepts one bounded line. This is not a production interpreter sandbox. The adapter is intended for one service owner; network authentication, an HMI lease, supervisor-to-controller stop acknowledgement and any production API server are not implemented here.

## Actual runtime and isolation

The existing `GarciaMechBuilder` WSL distro hosts a task-local Debian root filesystem at `/root/.cache/controller-lab-linuxcnc/rootfs`. No host package installation, Docker daemon, physical machine profile or existing auto-connecting UI was used. Debian packages were installed **inside that root filesystem**. Rootfs + packages require roughly 2.2 GB; the package download was 453 MB. Nothing was ordered.

- Real runtime: Debian `linuxcnc-uspace 1:2.9.4-2+deb13u1`, Python `3.13.5-1`; kernel `6.18.33.2-microsoft-standard-WSL2`.
- Pinned Debian OCI manifest: `sha256:7792b1f7702a86946cd518db72b6a407302c3e9bc1635634368b878189e8221c`, recorded as `trixie-slim` linux/amd64. The current fetch script resolves the `trixie-slim` index, requires this digest to be listed for linux/amd64, and checks the image config's `os`/`architecture` before writing the tag. **The provisioned rootfs and its provenance record `controller_backend/evidence/debian-rootfs-source.json` predate that change**: the record has only `image`, `manifest_digest` and `layers`, so in that record the tag and architecture are labels, not properties the script verified. The manifest and layer digests were verified at fetch time. The fetch has not been re-run, so no new download was made.
- Verified rootfs layer: `sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8`. The cached layer archive was re-hashed locally on 2026-09-28 and matches (`controller_backend/evidence/rootfs-layer-filter-check.json`).
- `fetch_debian_rootfs.py` now resolves the `trixie-slim` index (requiring the pinned digest under linux/amd64), fetches that exact manifest and verifies manifest, image-config (`os`/`architecture`) and layer hashes. Layer members are extracted through `rootfs_member_filter` (not `fully_trusted`, which the audited revision used). It refuses absolute or escaping paths, writes through an earlier or pre-existing symlink that resolve outside the destination, symlink members whose last name component is empty, `.` or `..` (for example `p -> .` followed by a `p/..` symlink, which would otherwise name the directory above the rootfs), escaping hardlinks, lexically escaping relative symlink targets, and device nodes/FIFOs. Extraction refuses to start (and the fetcher exits before downloading) on a Python whose `tarfile` lacks the CVE-2025-4138 link-fallback re-filter (feature test `tarfile.LinkFallbackError`; CPython 3.12.11+, 3.13.4+, 3.14+), because older builds extract a link's fallback target without passing it through the filter. It keeps modes, ownership (setuid/setgid) and Debian's absolute symlinks. The pinned digest remains the trust anchor. Evidence class: **host tests**. There are synthetic-archive cases in `tests/test_linuxcnc_backend.py`: 49 tests pass as root under WSL Python 3.14.7, and on Windows Python 3.14.6 44 pass and the 5 symlink cases are skipped (`controller_backend/evidence/backend-contract-tests*.txt`). The `.`/`..` symlink-name case calls the filter directly, so it does not rely on this Python's own link-fallback re-filter. There is also `controller_backend/verify_cached_layers.py`, which extracted the cached pinned layer into a scratch directory as root (rerun after the `.`/`..` change at 2026-09-28T19:19:03Z): 3,269 members, including 32 absolute symlinks, 1 hardlink and 11 setuid/setgid files. No member was refused and all 11 kept their mode and owner. The scratch directory was then removed. The provisioned rootfs was extracted earlier by the pre-filter fetcher and was not re-extracted. The provisioner pins the LinuxCNC package version; dependency versions are recorded in `controller_backend/evidence/debian-packages.tsv`. Repository availability and all dependency archives are not vendored, so this is source/version evidence rather than a fully offline reproducible image.
- Each launch deletes the previous work copy inside the rootfs before copying the package. It also removes generated state from the new copy: `evidence/`, `.runtime/`, LinuxCNC `*.var*` parameter files, `position.txt` and `__pycache__`. The run therefore starts only from the checked-in profile. LinuxCNC's `link (updating variable file): No such file or directory` log line comes from starting without a parameter file. Run `0544b28f` (below) evidently used this launcher too: the launcher was changed at 08:48Z and that run's log shows the same line.
- The actual run has private PID, IPC, mount and **network** namespaces, uses unprivileged `cnclab`, mounts a private `/proc` and `/dev/shm`, and exposes no host device tree. Rootfs `/dev` contains only null, zero, random and urandom nodes. Launch is bounded to 120 seconds.
- LinuxCNC reported **POSIX non-realtime**. The 1 ms configured servo period is a simulation setting, not a measured deadline guarantee.

This package version differs from the v2.9.10 source revision audited in `research/SPI_FEASIBILITY.md`. The runtime result does not prove that CM5 SPI code or any custom HAL driver works.

## Executed acceptance

`controller_backend/evidence/linuxcnc-simulation.json` is the machine-readable real-runtime result; `linuxcnc-trace.json` contains actual LinuxCNC status samples. The launcher requires a matching new run ID and `success: true` before reporting success, preventing a stale passing file from masking a failed launch.

| Real LinuxCNC check | Observed result |
|---|---|
| Dedicated profile attach and XYZ homing | Passed; the attach check compares the controller-reported `ini_filename` (`/work/controller_backend/profiles/sim/controller.ini`) with the checked-in profile and records both |
| MDI move | Reached `(1, 2, -1)` mm |
| Line, G2 semicircle and return | Sampled X approximately 20 mm and Y approximately 10 mm; returned to origin |
| Feed hold | Actual motion stopped and position stayed fixed through a 0.2 s observation |
| Explicit resume | Resumed and completed the loaded program |
| Abort during motion | Stopped near X=1 mm, before the X=20 mm destination |
| Reconnect replay rejection | Old MDI request rejected; no resulting position change |
| Reconnect program authority | Run rejected until an explicit program reopen |
| Controlled end | Software machine powered off; status sampler had no error |

The current evidence is run ID `bac564b6-1f50-4593-86bc-b3d496f33e75` at `2026-09-28T19:03:22Z` (`linuxcnc-simulation.json`: `success: true`, **12 passing checks**, **3,118 status samples**, profile SHA-256 `16edf263…`). Historical runs, each also 12/12: `0544b28f-9abf-4984-8ff9-d1f61672d925` at 08:49:34Z had 3,167 samples; its files are archived in `controller_backend/evidence/before-audit-fixes-2026-09-28/`. `da9f1f4c-a338-494a-9e69-67787eb6c9af` at 05:01:13Z had 3,166 samples; its files are no longer on disk. In both historical runs the attach check was a tautology: the sample carried the adapter's expected path, not the controller-reported one. Profile identity was still enforced inside `connect()`/`poll()`. The adapter contract suite has **49 tests**, including a read-only check that this report cites the run in `linuxcnc-simulation.json`. On Windows Python 3.14.6, 44 pass and the 5 symlink cases are skipped. Under WSL Python 3.14.7 as root, all 49 pass. Earlier revisions had 30 tests. Those tests use a fake API and do not simulate a planner; the acceptance above uses the actual LinuxCNC interpreter, task process, trajectory planner, kinematics and HAL motion component.

Two real integration bugs were found and fixed: LinuxCNC inserts `-ini` before display arguments, requiring an executable wrapper; and `wait_complete()` can block through a whole run or remain pending during a pause. Motion/home/pause/resume therefore dispatch asynchronously and the client observes completion independently. The demo also waits for the ideal feedback loop to settle rather than treating interpreter-idle as proof of final position.

## Commands

Already-provisioned runtime, from the workspace root. `wsl` starts in the translated current directory, so the repository-relative form works on any checkout. Substitute your distro name for `GarciaMechBuilder`:

```powershell
python -m unittest discover -s tests -p test_linuxcnc_backend.py -v
wsl -d GarciaMechBuilder -- sh controller_backend/run_isolated_simulation.sh
wsl -d GarciaMechBuilder -- python3 controller_backend/verify_cached_layers.py --output controller_backend/evidence/rootfs-layer-filter-check.json
```

Run `bac564b6` was recorded with the absolute form on this workstation: `wsl -d GarciaMechBuilder -- sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/controller_backend/run_isolated_simulation.sh`.

Fresh runtime creation, only into the designated **empty** task rootfs. `$CONTROLLER_LAB_ROOTFS` defaults to `/root/.cache/controller-lab-linuxcnc/rootfs`, and every launcher reads it:

```powershell
wsl -d GarciaMechBuilder -- python3 controller_backend/fetch_debian_rootfs.py
wsl -d GarciaMechBuilder -- sh controller_backend/provision_isolated_runtime.sh
```

The fetcher refuses an existing populated destination. Provisioning requires network access; the subsequent simulation itself has no network. The launch command is CLI-first and runs no graphical application.

## Remaining boundaries

The HAL file loads `trivkins` and `motmod` and loops joint position commands directly to ideal feedback. It has no motors, plant dynamics, drives, physical encoders, spindle or field I/O. Tool and ESTOP signals are simulation handshakes. In run `bac564b6`, LinuxCNC's **task main loop** logged 10 excursions above 10 times its configured 1 ms period. The maximum was 0.126868 s over 30,698 cycles (average 0.001091 s); see `controller_backend/evidence/linuxcnc-raw.log`. Historical maxima: 0.127382 s in `0544b28f` and 0.123849 s in `da9f1f4c`, each with 10 excursions. These are task-loop diagnostics, not a measured servo jitter distribution. The captured trace must not be presented as hardware timing or a safety validation.

`controller_lab.Supervisor` remains a separate authority/fault reference model. This adapter does not falsely translate an API poll into its motion-heartbeat or stopped-ack event. The custom FPGA protocol described in `gateware/PROTOCOL.md` still needs a real-time LinuxCNC HAL transport and physical validation; the Python adapter is not that cyclic transport and does not use unmodified Mesa/HostMot2 drivers.

Not executed here: closed-loop servo tuning, physical probing, spindle-synchronized threading/rigid tapping, gantry homing, nontrivial kinematics, ATC/PLC sequences, plasma THC, production fault recovery, local 3D-display scheduling load, synthesis or any electrical validation. LinuxCNC capability in source is not proof of a finished custom machine integration.

Upstream references: [LinuxCNC Python API](https://linuxcnc.org/docs/2.9/html/config/python-interface.html), [Debian LinuxCNC package](https://packages.debian.org/trixie/linuxcnc-uspace). Exact runtime artifacts and package versions are recorded locally rather than inferred from current documentation.
