# Motion X12 OS appliance pass

**PASS within offline development-overlay scope.** The
[canonical receipt](receipt.json) binds the current Motion X12/GarciaMech
application image, [run-r01 execution](run-r01/receipt.json) and additive
[user recovery-unit parser control](user-unit-probe-r01/receipt.json).
This is a real deterministic application/rootfs overlay and working Linux
startup/HTTP evidence. It is not a bootable physical-controller image, installed
kiosk, signed release, measured five-to-ten-second startup or motion continuity.

## Applied implementation and defects

The staged image now carries local source-native Motion X12/GarciaMech SVG and
inert desktop recovery HTML. It also carries exact boot and lifecycle JSON
recipes. The quiet/splash proposal changes no bootloader file, installs no
Plymouth theme and leaves its renderer/base-image integration pending. Signed
updates are unavailable; update/recovery partitions, slot count and usable-UI
boot time are unknown. No fabricated partition, bitstream or physical image is
included.

The prior application unit relied on an active oneshot preflight. A later restart
could therefore skip fresh image/settings validation. Every application launch
now has the same non-ignored read-only `ExecStartPre` check. A corrupt or changed
image/settings snapshot is refused even after an earlier successful check.
Startup never repairs, restores or initializes the machine store.

The prior optional kiosk had no explicit retry budget. Both kiosk and application
now have a total three-start budget, three-second retry delay and deliberate
retry after exhaustion. Browser failure reaches only a user recovery target and
read-only report; its dependency/command graph has no application or runtime
control. The kiosk opens `/launch`, honoring the shared guarded startup-page
preference while ordinary Home remains `/`. Browser sandbox bypass is forbidden.
System application recovery remains separate and read-only.

The kiosk report takes no runtime observation. It reports output state as
unknown, never announces measured inhibition, and grants no authority. Inhibited,
unhomed application restart is a required policy. There is no motion-runtime
unit in this overlay, and process separation cannot establish a working or
qualified independent runtime supervisor.

## Exact verification

The fresh run passed 25 adversarial Python tests. Added controls exercise
cross-unit failure dependencies, bounded retry policy, exact per-launch preflight,
corrupt settings and stale image after earlier success, resealed sandbox/retry
bypasses, inert bound branding assets, explicit unavailable boot/update state and
public CLI opt-in/unknown-output behavior.

Seventeen actual Linux checks ran under euid 1000 on an initialized SIM-only
store in a mode 0555 directory with mode 0444 settings. Historical export/write
locking failed as expected; current startup read the exact saved generation and
readiness without writes. The staged shell/original workbench retained Host,
token and CSP contracts and preserved settings bytes/directory contents. Actual
FIFO refusal, non-actuating kiosk recovery and unapplied/unmeasured boot recipe
were checked in that same process.

Five system-level units passed `systemd-analyze verify`. The first offline user
parser probe found its inherited WSLg runtime-directory path absent inside the
chroot; its failure log remains intact. The additive probe supplied a new owned
runtime directory and the two exact user recovery units passed with no
diagnostics. No systemd manager or unit was activated. Chromium is absent in the
isolated base, so browser/kiosk/display qualification remains open.

Two independent stages of the same 48 application files and 14 generated
payload files yielded identical 594,324-byte payloads and identical tar SHA-256
`b8e73b5b37585f0fde04015280f49ce222e7639837be7a3e243a46cc29de5938`.
The manifest digest is
`96c1566a7ebd255075724882b2bc7321cce6801b244188f889010807be3b93f8`.
All 50 source/test/CLI inputs and all 71 frozen motion-runtime inputs matched
before and after execution. The exact three-module `controller_appliance`
service ships; preferences, package directories, settings, allowances,
credentials and laboratory fixtures do not.

The isolated Linux Python 3.13.5 process correctly reports compressed packages
unavailable. The definition records the required actual CPython 3.14+/libzstd
backend without asserting that this base supplies it. Native Python tests used
3.14.6. These package/kernel observations are not a pinned complete base image.

The independent hardware reviewer executed
[27 process/lifecycle controls](../review/lifecycle-r01/receipt.json) against this
exact staged image. An explicitly non-motion PID/counter sentinel survived
SIGKILL and restart of a GET-only client and real shell HTTP process. Fresh
preflight, token rotation/refusal, stale-image/corrupt-settings refusal,
read-only recovery and cloned settings preservation passed. This is process
separation evidence; no actual browser, systemd service, LinuxCNC or RT-motion
continuity ran in that control.

## Reproduction and qualification limits

Use a fresh output directory; existing reports/images are never overwritten:

```powershell
python tools/controller_os.py boot-plan --allow-development
python tools/controller_os.py kiosk-recovery --allow-development
python reports/appliance-os-20261004/os/run_checks.py --out reports/appliance-os-20261004/os/new-run
```

Only explicit disconnected Linux x86_64 development is staged. CM4/CM5/CB1/CB2
compute/carrier/base/kernel/device-tree/boot/graphics remain unqualified.
Actual service boot, independent motion supervision, loaded RT/graphics/touch
and cold-boot measurements, signed updates, measured slot/recovery headroom,
interrupted-power recovery and physical commissioning are still required.
No current desktop/network configuration, service enablement, disk/partition,
original configuration/runtime source, hardware, paid API or routing was changed.
