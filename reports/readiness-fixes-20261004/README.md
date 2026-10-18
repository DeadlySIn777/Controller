# Applied readiness and setup fixes — 4 October 2026

The requested readiness work now includes executable software changes, not only an audit. The [setup workbench](../../docs/SETUP_WORKBENCH.md) provides a responsive local UI, public CLI and common service for explicitly disconnected IS-2 simulation. Claude's routing work was left alone. No real machine, paid provider request, firmware flash, board export or fabrication job was used.

## Applied changes

| Area | Result | Evidence / boundary |
| --- | --- | --- |
| Setup frontend | Machine/profile intake, remembered answers, drive mechanics and units, optional I/O, calculated review, exact diff, save, reopen and reviewed restore | Actual browser work on the real loopback server; simulation only |
| Shared service | 3-axis, dual-motor gantry, 8- and 12-motor profiles; all 12 enable/alarm resources, 4 ABZ, 24 DI and 16 DO; checked scale/rate/timing/voltage/current/resource assignments | [Service report](setup-service.md), 29 service tests; SIM terminal labels and 100 kHz ceiling are authored fixtures |
| Persistence | Atomic saved intake, four retained profile drafts, versioned configurations, stale-plan rejection, idempotent commit results and audit trail | Profile switching/restart/restore exercised; Windows killed-writer lock recovery and concurrent edits tested |
| CLI | Public `setup` commands use the same service, including schema, capabilities, examples, preview/commit, request results, restore, export, guidance and budget inspection | 12 CLI tests; Windows JSON output now preserves Unicode independently of the console codepage |
| AI allowance | Immutable local session cap up to US$15; durable reservations before dispatch; exact duplicate suppression, conservative arithmetic, uncertain-charge holds and overrun freeze | [Budget report](budget.md), 26 budget tests; one-host/session control, not a verified global account limit |
| Optional AI | Explicitly configured OpenAI adapter with strict missing-mechanical-field proposals, exact source quotations, bounded input/output, caching and zero automatic retries | 21 fake-provider adapter tests; actual provider/model quality, pricing and final billing remain unevaluated |
| Assistant authority | Removed raw actuation/callback paths from the unadopted external FluidCNC assistant | [Source fix](hardware-release-fixes.md): 170 inert cases, zero actuation; original reproduced eight unsafe calls |
| Product release | Production checker requires all G01–G26 and package/revision/evidence bindings | 50 tests; all 26 gates remain open; prototype has 17 blockers and production has 49 |
| Historical RTL verification | Explicit unchanged historical runner/dependency scope; exact archived old recorder plus new verifier transition | 12 tests; 12 old source hashes and two evidence hashes verified; no HDL rerun or re-stamped baseline |

The existing historical six-motor/two-encoder configuration examples and XYZ runtime authority retain their original scope. New simulation inventory is not physical discovery or a twelve-channel LinuxCNC integration claim. Other required IS-2 interfaces are enumerated as requirements but are not yet configurable through this workbench. No fake removable-card identities were added.

## Defects found and fixed during integration

- A browser parses `640.0` as a JavaScript number and serializes it as `640`, changing a Python-canonical plan digest. The backend correctly rejected the first browser commit. HTTP preview/restore now include an opaque `commit_payload`; the UI sends its exact string for strict parsing and independent validation. The ordinary result object and service hashing remain unchanged. A real Node round-trip is retained as a negative test.
- A save originally returned a fresh status after releasing its lock. Another writer could advance the store between those operations, giving the first client someone else's revision. Save, initialize and epoch restart now return their exact locked snapshot. The UI also retains the initialization snapshot and refuses to overwrite an independently started draft.
- Legacy sentinel locking survives a killed writer. The new setup service uses its own stable OS advisory lock, released by process death. It refuses an old sentinel rather than silently bypassing it. Legacy service locking is unchanged.
- Switching from twelve motors to a smaller profile originally discarded unused motor answers. The service now archives each outgoing supported profile draft atomically; returning after a process restart restores the twelfth motor's distinct value.
- Reopening an edited draft originally showed the completed screen whenever an older active configuration existed. Pending edits now reopen in Drive details; the saved screen takes its identity from the committed generation.
- Changing distance units originally relabelled numbers. It now converts travel and velocity, invalidates the plan, and revalidates the calculation. The display conversion uses twelve significant digits, not a promise of exact reversible decimal conversion.
- Local guidance originally ignored complete-but-invalid drafts. It now reports blockers, including excessive pulse rate and electrical limits.
- A damaged allowance record originally prevented the entire setup UI from loading. It now disables paid advice, preserves the ledger and permits a valid offline setup to save and restore.
- HTTP handling now rejects duplicate/ambiguous authorization and framing headers, oversized or malformed JSON, duplicate keys, nonfinite numbers and unknown routes. It binds only to loopback, checks exact Host/Origin/session token and sends a restrictive content policy.
- Optional AI handling now caches structured rejection for huge integers/exponents, freezes on contradictory model or excessive usage evidence, rechecks price expiry before generation, and retains liability if counting completed before a later failure. Failed paid UI requests show the retained reservation rather than remaining labelled in progress.

## Verification

**325 scoped host tests passed**: 105 setup tests, 125 existing configuration/recovery/runtime tests, 33 existing persistent-runtime host tests, 50 release tests and 12 historical-recorder scope tests. These are host tests with temporary stores and disconnected/fake adapters. No target compilation, HDL simulation, FPGA synthesis, vendor fit/timing, circuit ERC, board DRC or physical measurement was rerun by this fix pass.

- [Final setup run and source hashes](setup-host-tests-final.json), [105-test log](setup-host-tests-final.log).
- [125 legacy tests](legacy-configuration-tests.log), [33 persistence tests](legacy-persistence-tests.log).
- [Release verification](product-acceptance-verification.json), [recorder tests](rtl-scope-tests.log), [opaque HTTP plan tests](setup-web-verification-r03.json).
- [Budget, failure and fake-provider verification](budget-test-receipt.json).

An initial aggregate test command ran from Python stdin, which Windows multiprocessing cannot re-import. That harness failure is preserved in `setup-host-tests-stdin-harness-failure.log`; the checked-in `verify_setup_host.py` runner then passed all 105 cases. The final compact/mobile CSS adjustment was tested in the browser after that host snapshot; [browser verification](browser-verification.json) and the final source inventory record the resulting CSS separately.

The actual browser walkthrough verified:

1. Missing facts remain empty; an authored example is selected explicitly.
2. Eight-motor calculation rejects a requested 640,000,000 pulses/s against its 100,000 Hz simulation ceiling; corrected facts review and commit.
3. Eight → twelve → three → reopen → twelve preserves the twelfth motor's entered 7 mm travel.
4. 5 mm converts to approximately 0.196850393701 in; twelve motors review and commit. Restoring the prior eight-motor setup creates generation 3 with inhibited/unhomed state.
5. A fresh three-axis setup rejects 0.6 A against the 0.5 A/channel limit; 0.25 A output and 4,000 decoded encoder counts review and save as generation 1.
6. With a deliberately obsolete test-only ledger, offline review/save/reopen still works, the allowance says unavailable, and the ledger is preserved.
7. On a separately labelled fake-provider server, the UI shows the proposed 200 full steps/revolution with its exact quote. Repeating the same request reuses the result: the fake log has exactly two HTTP-provider operations total (one count and one generation). Clicking Add reviewed facts saves only the draft; generation remains zero and seventeen missing facts remain. No live model was contacted and the displayed US$0.012 reservation is fixture arithmetic, not real spending.
8. Compact 800×480, desktop 1280×800, large 1920×1080 and narrow 390×844 layouts were inspected. The 800, 390 and 1920 checks had no document-level horizontal overflow; scrolling within content remains necessary. These viewport checks are not novice-user trials or qualification of physical displays.

The browser download-event observation timed out, so the UI's final file-download receipt is not claimed verified. The export endpoint and public CLI export passed host tests. The browser page remained functional with no captured console errors. The fake-provider server was stopped; the normal offline preview was left open at `http://127.0.0.1:8766/`, using only the report-local `ui-preview` simulation store. Its restart command is:

```powershell
python -B -m controller_config setup --directory reports/readiness-fixes-20261004/ui-preview serve --port 8766
```

![Saved local simulation setup](screenshots/saved-1280x800.png)

## Preserved evidence and boundaries

[Preservation comparison](preservation-check.json) checks 643 prior hardware/evidence hash references: **all unchanged**. Of 619 previously inventoried software/source files, only the four explicitly intended existing files changed: CLI entry point, release checker, release tests and historical recorder. New setup modules/tests/assets are additional files. The external assistant has its own exact before/after receipt and archived original; its normal application controls remained unchanged. Existing user configurations and the external IS-1 archive were preserved.

This is not yet a qualified CNC setup expert or complete firmware. G26 remains open. The missing physical equipment catalog, approved real terminal maps and machine-specific commissioning procedure require exact reference sources and machine evidence. Full IS-2 runtime/telemetry integration, protected cartridge/mirror recovery and offline entitlement integration are not established by this file-backed setup fixture. Live-model reference-answer evaluation, cost distributions, authoritative billing integration and novice-user trials remain required.

FPGA capacity/vendor timing, complete IOL1 authority and remaining hardware/electrical/physical/product release requirements are still open. No tests or status files were fabricated to close them. The [3 October audit](../readiness-reaudit-20261003/README.md) remains the dated original finding; this record identifies the fixes actually applied afterward.
