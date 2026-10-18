# Controller OS experience upgrade

4 October 2026. The dark red appliance interface is implemented and available in the [local preview](http://127.0.0.1:8770/). It gives the controller its own home, consistent navigation, guided next action, readiness and recovery entry points while retaining the existing setup service and CLI contract. Linux and LinuxCNC remain the underlying operating and motion components.

[Actual controller home at normal browser size](../../WORKSPACE_REFERENCES.md#artifact-c5491eafce8fa84d)

This capture uses an explicitly authored report-local setup fixture. The machine drawing is an illustration. The interface identifies the disconnected development state and requires physical commissioning.

## What changed

The new `controller_shell` serves local assets, a compact home and the existing workbench through the same guarded server. Dark surfaces, restrained red accents, clear hierarchy and primary touch controls replace the utility-style entry experience. Keyboard focus and reduced-motion preferences are supported. Ordinary transitions use modest opacity/transform changes; there is no continuous decorative animation, blur dependency or external font/CDN request.

Home reads the actual configuration/readiness context, checks the full six-field binding before displaying it and routes the next step to the existing panel. It makes no paid AI request or motion request. Visible-page polling is bounded, fetches time out after eight seconds and a failing request aborts its sibling. Unavailable or inconsistent data is labelled accordingly instead of remaining a current readiness claim.

Navigation preserves real edits using the existing guarded save path. An untouched provisional template does not create saved settings or initialize an AI allowance merely because someone visits readiness and returns home. Failed or stale saves retain the answers on screen. Requested panels wait for the workbench to become ready, rather than silently opening the wrong step. The inherited Host, Origin, token, session and CSP controls still protect the shared API.

The new `controller_os` CLI stages a deterministic offline application overlay with exact source checksums, privilege-limited service definitions, startup preflight, separate read-only recovery and an optional graphical-session kiosk. Existing machine settings, entitlements, diagnostic history, credentials and AI allowance data stay outside the image. Staging does not install or enable these services. [Detailed overlay execution](os/README.md) explains its scope and reproduction.

## Current checks

| Evidence | Result | Scope |
|---|---|---|
| [Shell HTTP tests](../../WORKSPACE_REFERENCES.md#artifact-b853929d3c63d8d4) | Five passed | Actual service/API/session policy and preservation of settings/allowance semantics |
| [JS controls](../../WORKSPACE_REFERENCES.md#artifact-e6c6d66ea3c434c6) | Six passed | Guarded navigation, pending route and fetch-failure behavior in inert Node controls |
| [Browser layout](../../WORKSPACE_REFERENCES.md#artifact-6c41f63dc5168dd5) | Four viewports passed | 800×480, 390×844, 1280×800, 1920×1080; no horizontal overflow and 48-pixel primary actions; 40 source files and fixture bytes unchanged during capture |
| [Earlier actual browser workflows](../../WORKSPACE_REFERENCES.md#artifact-0bf49fca2d778369) | Captured | Exact next-step panel, untouched navigation, edit preservation, service loss and new-session reload; these earlier captures have no independent source ledger |
| [OS execution](../../WORKSPACE_REFERENCES.md#artifact-e7b0dc541606cf89) | 18 adversarial tests, 15 actual Linux checks, five systemd syntax checks passed | Non-root process, existing saved settings in a read-only directory, real loopback HTTP and actual FIFO refusal |
| [Deterministic overlay](../../WORKSPACE_REFERENCES.md#artifact-ce27d063f8e07dd1) | Two independently staged payloads identical | SHA-256 `cf1f1f06dd9d8eab26af102f224202cce09f8fa88d749305604d31f8351e2072`; 46 payload files, 513,701 bytes |
| [Independent shell review](../../WORKSPACE_REFERENCES.md#artifact-86ad340cdbbcc680) | No remaining actionable finding in inspected scope | Review and retained root-executed HTTP/JS/browser evidence are attributed separately |

The Linux checks exposed a real preflight bug: the earlier backup snapshot call tried to create a write lock in read-only saved settings. Preflight now uses one captured service status and verifies its exact binding against readiness without creating that lock. A Linux process with euid 1000, a 0444 settings file and 0555 directory demonstrated the old negative control failing and the corrected startup passing unchanged. Non-regular image inputs, including a real FIFO, are refused without blocking.

## What the OS image still needs

The deliverable is an application overlay, **not a bootable or signed controller image**. Only the explicit x86_64 POSIX development profile is permitted. CM4/CM5 Lite/eMMC and CB1/CB2 candidates remain blocked until their exact compute, carrier, storage, kernel, bootloader, device tree, graphics/touch and physical CNC3 backend are approved and qualified.

The retained isolated Linux host runs Python 3.13 and lacks the required `compression.zstd` backend. Its package capability is honestly reported unavailable. The base definition requires CPython 3.14+ with libzstd, but a pinned offline package/base-image closure has not been built or qualified. Therefore this report does not claim that all dependencies or compressed backup/support paths already work on the target image.

Cold boot, ordinary touch latency, frame pacing, memory, storage use, thermals and loaded real-time motion have not been measured on the controller. The retained 60 Hz / under-100 ms ordinary-response targets are acceptance goals, not results. Signed staged updates, rollback, interrupted power and settings-media recovery also remain open. Successful application startup never restores position, homing or output permission.

## Use the implementation

Create an explicitly selected development workspace and exclusive staging output:

```powershell
python -m controller_shell --directory reports/my-os-preview --port 8770
python -m controller_os profiles
python -m controller_os stage --source-root . --output reports/my-os-candidate --release-id development-r1 --allow-development
python -m controller_os inspect --root reports/my-os-candidate/rootfs --allow-development
python -m controller_os preflight --help
```

[Implementation/image contract](../../docs/CONTROLLER_OS.md), [subsystem CLI documentation](../../controller_os/README.md), [current runtime gap report](../deeper-runtime-20261004/README.md), [boot/storage requirements](../../docs/BOOT_STORAGE_AND_PROVISIONING.md) and [display tiers](../../docs/DISPLAY_TIERS.md) retain the shipping gates. Screen size and licensing do not change the twelve fitted motor interfaces or required I/O. No paid calls, routing changes, device writes, OS installation or network-setting changes were used for this upgrade.
