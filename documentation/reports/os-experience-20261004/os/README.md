# Offline appliance overlay and startup evidence

The implemented `controller_os` subsystem creates a deterministic application
rootfs overlay for our desktop shell and existing configuration service. Its
structured CLI defines compute profiles, stages a fresh image directory,
inspects exact installed bytes and runs startup/recovery checks. It neither
installs an OS nor changes the current computer's desktop, default target,
network or services. [Canonical evidence](../../../WORKSPACE_REFERENCES.md#artifact-ce27d063f8e07dd1) binds the final
[run-r03 execution](../../../WORKSPACE_REFERENCES.md#artifact-e7b0dc541606cf89), source files, logs and both overlays.

The current permitted profile is explicitly disconnected Linux x86_64
development. The CM4/CM5 Lite/eMMC and CB1/CB2 profiles are recorded as blocked
compute candidates. No approved base image, bootloader, kernel/device tree or
physical target is substituted by an application test. No physical boot,
real-time latency, display frame pacing, signed release or manufacturing
qualification is claimed.

The overlay includes every Python/web asset in `controller_config`,
`controller_shell` and `controller_os`, plus the shared configuration-binding
helper and its package initializer. Optional laboratory scenario tools are
excluded. Existing settings, generations, AI allowance data, credentials,
diagnostic history, entitlements and calibration stay outside the image.
The source closure and generated services are verified again when loading the
manifest; resealing a checksum cannot omit a required installed source, replace
the service command or promote authority. The integrity digest is not publisher
authentication or release signing.

The service definition uses a dedicated unprivileged account, preflight before
shell startup, private devices and a loopback-only shell. Recovery is a separate
read-only target that conflicts with the shell. The optional user kiosk retains
the browser sandbox and is not enabled by staging. Its browser, graphical session
and physical screen remain unqualified. The staged shell uses the actual shared
service command: `python3 -m controller_shell --directory
/var/lib/controller/workspace --port 8769`.

The final run passed 18 adversarial Python tests and 15 actual isolated Linux
checks. A previously initialized SIM-only settings fixture was made mode 0444
inside a mode 0555 directory. Under euid 1000, the historical backup/export
write-lock path failed with `PermissionError`, while current preflight read its
full six-field binding and consistent readiness without creating a lock or
changing settings or directory contents. This confirms the startup correction
requested by independent root review: preflight derives its binding from the
already captured status snapshot instead of calling `backup_snapshot()`.

The same Linux process ran the staged shell and original workbench on an
ephemeral loopback port. It verified the inherited CSP, token and Host checks,
the same saved generation and disconnected authority, then stopped that server.
An actual FIFO was refused before opening could block. Five system-level unit
definitions passed `systemd-analyze verify`; no unit was installed, enabled or
booted, and the optional browser was not launched.

Two independent stages of the same 38 application files and eight generated
payload files produced identical 513,701-byte payloads and identical overlay
SHA-256 `cf1f1f06dd9d8eab26af102f224202cce09f8fa88d749305604d31f8351e2072`.
Run-r03 rechecked all 40 source/test/CLI inputs before and after execution.
The native test host was Python 3.14.6; the isolated Linux process was Python
3.13.5 on WSL2. Its real `compression.zstd` backend is unavailable and is
reported as disabled. The image definition explicitly records CPython 3.14+
with libzstd as the dependency for compressed packages; no unverified pinned
package version or complete backup feature availability is asserted.

The first attempt is retained as [run-r01](../../../WORKSPACE_REFERENCES.md#artifact-3844bc7e156305bf): its private
network namespace had loopback down, so the staged HTTP exercise failed with
`NetworkUnreachable`. The runner was corrected to use existing loopback without
altering interface or route configuration. [Run-r02](../../../WORKSPACE_REFERENCES.md#artifact-ab104733373dc03d)
passed the preceding 17-test/14-check source revision; it remains historical.
Only run-r03 binds the current special-file guard and 18-test/15-check suite.

Shipping still requires an exact compute/carrier choice, pinned offline base
image and package closure, boot/storage provisioning, approved kernel and
transport, signed update/recovery design, interrupted-update and power-loss
tests, preserved settings-media contracts and physical loaded motion/display
measurements. Application startup grants no motion or physical readiness.
