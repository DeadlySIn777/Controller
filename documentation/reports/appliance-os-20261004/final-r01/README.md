# Motion X12 / GarciaMech appliance pass

4 October 2026. The appliance software pass is implemented and verified in its declared development scope. A dark/red Motion X12 shell now gives Machine, Setup, Diagnostics, Files and Settings the same persistent navigation. Offline setup, readiness and recovery retain the original common service. All 71 protected motion inputs and all 24 original configuration files remain unchanged; Claude retains ROOT105/routing. This pass made zero paid requests and connected to no hardware.

The [final delivery ledger](../../../WORKSPACE_REFERENCES.md#artifact-96cfee29137f3548) binds current sources, execution receipts, retained logs, browser screenshots and documentation. It reports software/overlay results separately from target boot, runtime continuity, physical validation and manufacture. Prior runtime and OS reports retain their original source snapshots.

## What changed

The shell has local assets, consistent touch navigation, responsive layouts and no continuous decorative animation. Files exposes native setup/configuration/support downloads and a bounded, read-only inventory of verified local configuration/support archives. It cannot browse arbitrary machine paths, execute jobs or apply a package. Compression availability and unsaved machine setup are explicit download gates.

Settings offers three text sizes, reduced motion and a starting screen through the same public `controller_appliance` CLI/service contract used by the UI. Every preference change has a reviewed diff, workspace/revision/integrity binding, expiration and idempotent confirmation. Interface reset is reversible until a later preference edit supersedes it. Machine setup, backups, calibration, licences, jobs and allowance data are outside this reset. Full machine factory reset is blocked pending protected storage and signed image recovery qualification.

Service details require a deliberate acknowledgement and expose capability/recovery limits. They are session presentation, not authentication, a terminal or machine authority. The kiosk entry `/launch` honors the selected starting screen; ordinary Machine `/` remains a direct home destination. A bounded loading fallback keeps the home usable when preference retrieval fails.

The deterministic development overlay carries 48 application files and 14 generated payload files, including source-native Motion X12 SVG branding, inert recovery HTML, quiet/splash recipes and update/recovery requirements. These recipes are unapplied. Every application launch receives a fresh, read-only preflight; the former active oneshot could skip validation on restart. Application and kiosk plans now have three total starts, a three-second retry delay and deliberate retry after exhaustion. Graphical recovery has no application/runtime control dependency. Recovery observes no outputs and reports their state as unknown.

## Defects corrected during review

- Refresh after a stale preference revision kept forcing users to re-enter choices. It now preserves edited fields, incorporates other saved fields and requires a fresh review. Cancel and duplicate/pending confirmation controls were executed against the actual JavaScript.
- First-use preference plans could cross between two empty workspaces. An opaque normalized workspace identity now binds plans before a store exists; equivalent aliases of the same workspace remain valid.
- Default numeric representation could differ across browser JSON and Python. Accepted scales are normalized and the exact reviewed plan returns as an opaque payload.
- Startup validation could be skipped after an earlier successful oneshot. Each launch now validates its exact image and settings again.
- Kiosk retries had no explicit budget. Retry/failure graphs are bounded and separately validated; no runtime unit is invented.
- Leaving an untouched provisional setup risked creating a store merely through navigation. The untouched draft leaves without initialization; real edits still use the original guarded save.

## Exact verification

Counts below retain their own scopes; they are not summed into a new total of unique tests.

| Evidence | Current result | Scope |
| --- | --- | --- |
| [Original shell HTTP contract](../../../WORKSPACE_REFERENCES.md#artifact-b58e1aaae33d93fd) | 5 tests pass | Current Host/token/CSP and setup wrapper contract |
| [Appliance service](../../../WORKSPACE_REFERENCES.md#artifact-9e1a0a2e96ec5b69) | 29 methods; Windows 25 pass/4 skip, Linux 24 pass/5 skip | Preferences, binding, reset/undo, archive/path boundaries; platform and codec skips explicit |
| [Appliance HTTP controls](../../../WORKSPACE_REFERENCES.md#artifact-a934618b49b7fa01) | 23 checks pass | Real HTTP envelopes, authority refusal, idempotency, native exact package downloads and protected data |
| [OS overlay](../../../WORKSPACE_REFERENCES.md#artifact-1c872302e95ae7aa) | 25 tests, 17 non-root Linux checks | Fresh preflight, read-only settings, image closure, exact staged assets, lifecycle policy |
| [Unit parser control](../../../WORKSPACE_REFERENCES.md#artifact-3f3e7c16783dea9f) | 5 system units and 2 user recovery units pass | Syntax only; no systemd unit activated |
| [Independent lifecycle control](../../../WORKSPACE_REFERENCES.md#artifact-568d1950236a6759) | 27 assertions pass | A non-motion PID/counter survives client/shell kill and restart; fresh preflight/token/recovery controls |
| [Independent preservation/source review](../../../WORKSPACE_REFERENCES.md#artifact-7882831ed8484324) | Scoped pass | 71 motion files, 24 config files, current/copied 48-file application closure and bound evidence |
| [Actual browser pass](../../../WORKSPACE_REFERENCES.md#artifact-f98981383625485f) | 20 observations pass | 390×844, 800×480, 1280×800, 1920×1080; largest text, navigation, preferences, reset/undo, service entry, native download |
| [Browser artifact controls](../../../WORKSPACE_REFERENCES.md#artifact-c6cc66c01429607f) | Pass | Actual downloaded Zstd configuration archive validated; all four saved setup/allowance fixture files unchanged by interface reset |
| [Documentation audit](../../../WORKSPACE_REFERENCES.md#artifact-1953107fb3b8a88c) | Pass | Five current documents updated; earlier document bytes preserved exactly |

Two independent stages produce the same 594,324-byte tar with SHA-256 `b8e73b5b37585f0fde04015280f49ce222e7639837be7a3e243a46cc29de5938`. The exact [image manifest](../../../WORKSPACE_REFERENCES.md#artifact-3cdb8da4abc196a2) lists its application and generated payloads. The image excludes customer settings, allowance data, credentials and lab fixtures. Current files match both copies.

The browser used only the separate report-local `preview-r01` fixture at [port 8771](http://127.0.0.1:8771/). The pre-existing port 8770 preview and its machine store were not edited. Leaving untouched setup produced only appliance preferences/lock files; an explicit name edit later created the report fixture's draft and zero-request allowance ledger. The downloaded configuration archive was validated with the unchanged public archive reader and saved as [actual browser bytes](../../../WORKSPACE_REFERENCES.md#artifact-6c945c28791300ce). Largest-text phone navigation fits all five destinations with 73-pixel-high targets. Layout checks do not establish physical touch latency or frame pacing.

Retained failures remain visible. The first shell HTTP run failed an obsolete branding assertion before its correction. The initial offline user-unit parser probe inherited a WSLg runtime path absent from the chroot; a separate owned-runtime-directory probe passed. Browser instrumentation initially read a dynamic input's HTML `value` attribute instead of its live property; [the failed measurement](../../../WORKSPACE_REFERENCES.md#artifact-322409462cd60f49) is retained, and the corrected current-value observation passed without an application edit. Earlier service runs and the reproduced stale-preferences control keep their original bytes.

## Qualification still required

This is a working shell and deterministic application/rootfs overlay, not a bootable release with all base software installed. The isolated Linux base lacks Chromium and uses Python 3.13 without the required Zstd package backend. Windows Python 3.14 compression works; the image records the required backend rather than pretending the Linux base supplies it. Only the explicit x86_64 development profile stages; exact CM4/CM5/CB1/CB2 target profiles remain blocked.

There is no motion-runtime unit in this overlay. The independent lifecycle test used a counter sentinel and GET-only client, not a real browser, active systemd manager or LinuxCNC motion process. Controller survival through actual GUI failure remains a target qualification gate. No bootloader, partition table, service installation, desktop, network, firmware or paid provider was changed.

The five-to-ten-second usable startup goal, hidden boot output, branded splash, fullscreen kiosk execution, physical touchscreen response, frame intervals, RAM/storage use, thermals and loaded motion/transport latency all require exact supported compute/display measurements. Quiet/splash and protected update/recovery partition recipes are staged requirements; signed release verification, slot rollback and interrupted-power behavior are unimplemented/unqualified. Full machine reset stays blocked.

The [earlier SIM2 chain](../../../WORKSPACE_REFERENCES.md#artifact-bb8d5c16c4b999c3) retains its actual LinuxCNC FREE-joint, C/SPI/current RTL and independent virtual feedback scope. It was not rerun or promoted by this UI pass. Efinity fit/place/route/static timing, ROOT105, physical board bring-up, real watchdog-to-inhibit, output current, analog accuracy, brownout and thermals remain open. Simulation cannot close those gates or permit manufacturing.

## Preview and reproduction

Open the separate local [Motion X12 preview](http://127.0.0.1:8771/). Its saved machine name explicitly identifies the browser test fixture. To create another isolated preview:

```powershell
python -m controller_shell --directory reports/my-motion-x12-preview --port 8772
```

Use the exact reproduction commands in the [OS report](../../../WORKSPACE_REFERENCES.md#artifact-2935e1ab4945330b), [service report](../../../WORKSPACE_REFERENCES.md#artifact-a59752e2cf9d9b37) and [independent review](../../../WORKSPACE_REFERENCES.md#artifact-e1372baa4850d7ca); always choose fresh output directories. Existing receipts and stages are not overwritten. Shipping stage construction does not install or flash it.

[Actual Motion X12 browser home](../../../WORKSPACE_REFERENCES.md#artifact-84c27e0c8a553192)
