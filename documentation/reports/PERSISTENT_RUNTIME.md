# Durable calibration across actual LinuxCNC restarts

28 September 2026. **XYZ step calibration now survives independent LinuxCNC launches, with a compiled startup inhibit until the saved authority is explicitly validated and activated.** The implementation runs against actual LinuxCNC, the compiled CNC1 HAL module and the existing Verilator FPGA endpoint. It does not restore enable, homing, verified position or an interrupted job.

## Completed operation

The first launch explicitly initializes X=250 steps/mm, clears LinuxCNC homing, then requires separate operator-style enable/homing commands before a 1 mm move produces 250 returned STEP counts. A second independent launch starts inhibited at its internal defaults, discovers saved 250, and only activates it after `reconcile`. It again demonstrates a deliberately homed 1 mm / 250-pulse move.

That second launch requests X=300. A separate configuration client calls `os._exit(73)` immediately after runtime activation, before publishing the committed record. The client process dies, its process lock is released by the OS, and the compiled inhibit remains held. The journal retains committed generation 1 / 250 and pending generation 2 / 300. A third independent LinuxCNC launch executes `recover`, finishes generation 2 while disabled/unhomed, and a separately enabled/homed 1 mm move produces 300 returned pulses.

Six further independent launches reject missing, syntactically corrupt, foreign-machine, changed-profile, changed-capability and valid-but-older authority records. Each deliberately attempts machine enable; the actual LinuxCNC driver faults without granting FPGA permission. An explicit driver reset preserves the persistent inhibit. The ordinary volatile `recover-inhibit` service and compiled ordinary release operation cannot bypass pending persistent authority. In every launch, a HAL persistent acknowledgement (`config-op` 5) sent before any stopped scale commit is refused with result 5. The gate, the 200-step defaults and generation 0 are left unchanged.

## Evidence and scope

| Evidence | Result | Boundary |
|---|---|---|
| Default persistent configuration suite | **68 checks across nine independent LinuxCNC launches** (final sync rerun) | Actual LinuxCNC + compiled HAL + actual simulated RTL; repeated startup/refusal checks are counted, including one acknowledgement-without-commit refusal per launch |
| Previous runtime integration regression | **27 checks passed**, in explicitly opted-in volatile laboratory mode: the original 26 plus an actual-RTL pulse-rate margin boundary check added in the final sync | Preserves the original motion/fault/runtime-scale behaviors without pretending they use durable authority |
| Compiled C/RTL harness | **220 assertions passed** (log carried forward from the repair-round build; C sources, RTL and module unchanged since) | Includes repeated setup, common-code boundary fixtures and persistent gate/reset/generation behaviour, including the stage-then-commit precondition, op 4/5/3 without op 2, the documented limit that explicitly committed 200-step values are acknowledged with any hash, and the watchdog-derived period/age limits |
| Persistent host policy suite | **33 tests passed** (29 in the repair round, historical) | Explicit host adapter double, filesystem fault cases and mocked directory-fsync ordering; separate from actual-runtime evidence. The double now models the compiled scale-commit precondition: op 5 is refused with code 5 unless an op 2 followed the latest stage. A test checks that every op 5 the service attempts follows such an op 2 |
| Runtime host policy suite | **41 tests passed** (32 in the repair round, historical) | Includes slow HAL staging, versioned CLI success/configuration/I/O error envelopes, the servo-period pulse-rate margin and the driver's half-watchdog servo-period bound (`SERVO_PERIOD_LIMIT`) |
| Physical memory/power interruption and target deadline measurements | **Not performed** | Files are task-local Linux filesystem records, not a selected EEPROM/flash cartridge |

The current persistent run is `5cd2bcb5-d4e4-4592-9f53-6c6ab62b9f85`, from the final sync rerun of 28 September 2026. It was rerun because the configuration owner changed `controller_config/runtime.py`, which the launches copy, to apply the driver's half-watchdog servo-period bound. Its launch-bound INI/HAL SHA-256 is `fefe247b45c5c4a6ade69970a64b765fd89e7d0146a3f73607cf690b70d5f626`, unchanged. The nine per-launch JSON traces, logs, summary and final record/witness are under [cnc1/evidence/persistent](../WORKSPACE_REFERENCES.md#artifact-b391bb4b23cef302). The separate volatile regression run is `551cc0bd-9363-42b6-8a66-fa6adc27d7ab`: 27 checks, 1,124 samples, 14.8190 seconds wall time and 3.1621 seconds simulated RTL time. The repair-round runs are historical and archived under `cnc1/evidence/before-final-sync-2026-09-28/`: persistent `f25540e6-c2c3-42e7-960e-9696d652bba1` (68 checks) and volatile `c4357707-45e3-439a-8c38-7145cef75b3a` (26 checks, 1,122 samples, 14.8122 s wall / 3.1701 s simulated). The first audit-fix runs (persistent `bc27e94a-4630-4b5f-bf98-1c863ca849c3`, 68 checks; volatile `3ed8e8db-743d-4917-83db-db5ea47bcb34`, 1,116 samples, 14.8190 s wall / 3.1791 s simulated; 219 compiled assertions) are historical and archived under `cnc1/evidence/before-audit-repair-2026-09-28/`. They were superseded only because the persistence-precondition comments were corrected and a compiled limit case was added. The earlier final runs are historical and archived under `cnc1/evidence/before-audit-fixes-2026-09-28/`:

- persistent run `04c7b257-91e2-4802-ab5a-bdea697fa393`: 59 checks, 192 compiled assertions;
- volatile run `89f626bb-63e0-4136-8067-cb0cd585243e`: 1,233 samples, 16.1227 s wall / 3.1141 s simulated.

None of these runs establishes a physical 1 kHz deadline.

The current [CNC1 manifest](../WORKSPACE_REFERENCES.md#artifact-8474095096839423) was regenerated by `cnc1/tools/record_evidence.py` after the final sync rerun. It covers the sources, module and evidence of that rerun. The repair-round manifest and every log/JSON it hashed are archived byte-for-byte under [before-final-sync-2026-09-28](../cnc1/evidence/before-final-sync-2026-09-28/ARCHIVE_NOTE.md). `python cnc1/tools/record_evidence.py --check` reports any later drift. The pre-fix manifest and every log/JSON it hashed are archived byte-for-byte under [before-audit-fixes-2026-09-28](../cnc1/evidence/before-audit-fixes-2026-09-28/ARCHIVE_NOTE.md), and the first audit-fix record under [before-audit-repair-2026-09-28](../cnc1/evidence/before-audit-repair-2026-09-28/ARCHIVE_NOTE.md). Before changes, the previous manifest-covered files **and compiled module** were copied and hash-verified under [before-persistent-runtime](../WORKSPACE_REFERENCES.md#artifact-ac407032c9414679). An earlier successful 58-check persistent run, before the later deadline/directory review fixes, is preserved under `cnc1/evidence/persistent/pre-deadline-run/`; it is not the final evidence for those fixes.

Historical (before the audit-fix rerun): a later independent hash audit found edits to the CLI envelopes/I/O error handling and configurable rootfs launchers after the first 59-case manifest. Those edits were preserved and the affected build, 26-case regression, nine-launch suite and host checks were rerun. The previous exact tested service files were recovered from the task rootfs; all previous source/evidence bytes and module are retained under [post-manifest-review/prior-recorded-milestone](../WORKSPACE_REFERENCES.md#artifact-837ccf3a7cf618df), with per-file provenance and an exact change patch. The launcher/report reconstructions were accepted only after matching their previously recorded SHA-256 values. The final rerun explicitly set `CONTROLLER_LAB_ROOTFS=/root/.cache/controller-lab-linuxcnc/rootfs`; alternative filesystem images remain unqualified.

## Durable authority and reconciliation

`controller_config/persistent_runtime.py` implements one service used by the CLI and acceptance clients. Its schema intentionally contains only the implemented step-scale subset. It is separate from the larger disconnected machine-profile/cartridge schema and does not claim to persist wiring, tool tables, work offsets, full INI configuration, module factory calibration or firmware.

The store contains two checksummed files:

- `authority.json`: the last committed configuration and, while changing, one pending next generation. Each configuration binds a canonical machine UUID, exact launch profile fingerprint, discovered capabilities, bounded scales and generation.
- `generation-witness.json`: the published target generation and configuration SHA-256, bound to the same machine/profile. This separate file detects restoring only an older valid authority, or selecting a different record with the same generation. It is a logical witness on the same filesystem, not independent tamper-resistant storage.

Every change acquires the compiled pending inhibit **before** publishing the pending journal. The journal is atomically replaced and file/directory-fsynced; the witness is then published the same way. The existing shared stopped activation core unhomes actual joints, verifies their flags, revalidates runtime identity and applies all supported scales atomically. Only then does the service publish the committed journal, reread both files, compare their machine/profile/capability identity and exact target, and compare actual active scales.

The compiled persistent acknowledgement records the accepted generation/hash and clears the pending flag, but retains the configuration lock. The service rereads and checks storage and runtime again before requesting release. A client failure before release leaves the lock acquired. `reconcile`/`recover` begins by reacquiring/marking the persistent gate, so it can safely finish a valid interrupted journal even after the earlier client reached acknowledgement. These commands never choose between conflicting or corrupt records silently. `init` refuses to overwrite any existing authority/witness or an already accepted live generation.

The recoverable publication window is deliberately narrow: a pending record advances the committed generation exactly once and the witness matches either the old committed record or that pending target. A missing witness is recoverable only for an interrupted first initialization whose journal has no committed record and pending generation 1. A committed journal without its witness, an older authority against a newer witness, equal-generation hash disagreement, or wrong identity remains blocked.

Windows host tests inject interruption at journal publication, witness publication, runtime activation, committed publication, compiled acknowledgement and completed release. They reconcile in a new adapter instance. Tests also cover same-instance recovery, caller mutation, identity/capability changes, older backup conflicts, missing witness, corrupted JSON including numeric exponent overflow, and changes/expiry during disk operations. Since the final sync, they also cover these cases. A refused or unobserved op 2 stops before op 5, with the inhibit and pending state left set. On reconcile, a servo period above the half-watchdog bound (`SERVO_PERIOD_LIMIT`) or a missing watchdog (`CAPABILITIES_UNAVAILABLE`) refuses a saved authority before any transaction. These policy tests do not simulate storage electronics or actual power loss.

## Compiled gate and expiry

Default `cnc1_sim` initialization sets both persistence-pending and configuration-lock and records the current revision as the stage base. The compiled driver refuses to acknowledge (result 5) or release the gate until a stopped operation-2 scale commit has followed that stage. So uncommitted startup or staged values cannot be acknowledged or released, and the driver cannot ARM on them. This is not a value check. Any in-range scales, including the 200-step defaults, can still be committed by operation 2 and then acknowledged with an arbitrary hash, because the hash is opaque to the driver; the compiled harness asserts this limit explicitly. Equality between the committed scales and the durable record is enforced only by the persistent service, which is not an authentication boundary against a privileged HAL writer. `CNC1_ALLOW_VOLATILE_CONFIG=1` is an explicit opt-out used only by the previous laboratory acceptance launcher; it is not the default persistent workflow. Driver resets and communication recovery do not clear the pending gate.

New operation 4 acquires/marks pending persistent authority and records the current revision as the stage base. Operation 5 requires a later operation-2 commit (otherwise result 5) and then records the generation/hash while remaining locked. Operation 3 releases only after pending authority is cleared. Ordinary runtime apply/recover calls reject persistence-managed mode. The guard verifies session/revision/epoch and stopped driver/endpoint state; generation rollback and equal-generation hash replacement are rejected. Checksums and HAL pins are not authentication against a privileged local writer.

Configuration requests carry an absolute `CLOCK_MONOTONIC` deadline in two HAL words. The service retains the original deadline through journal writes, activation, acknowledgement and release. The adapter checks before staging and again immediately before publishing the request. The compiled cyclic handler checks the deadline **when it processes the request**, returning result 6 for a missing/expired deadline before any mutation or release. An actual HAL request with an already expired deadline was refused while the gate stayed held. The acknowledgement may be observed later; the deadline applies to accepting/executing the request, not to Python receiving its result.

Disk readback is followed by a fresh stopped runtime snapshot and a renewed deadline/binding check. This closes both filesystem-delay and HAL-handoff gaps found during review. The publication sequence remains tested on x86 LinuxCNC simulation; target ARM shared-memory ordering and real-time scheduling require separate qualification.

## CLI and reproduction

In the dedicated, running persistent RTL environment, all operations produce structured JSON:

```sh
python3 -m controller_config.persistent_runtime --directory /chosen/task-local/store status
python3 -m controller_config.persistent_runtime --directory /chosen/task-local/store init --scales 250 200 200 200 200 200
python3 -m controller_config.persistent_runtime --directory /chosen/task-local/store preview --scales 300 200 200 200 200 200 --output /tmp/change.json
python3 -m controller_config.persistent_runtime --directory /chosen/task-local/store apply /tmp/change.json
python3 -m controller_config.persistent_runtime --directory /chosen/task-local/store reconcile
python3 -m controller_config.persistent_runtime --directory /chosen/task-local/store recover
```

`init` is the explicit new-machine commissioning path. `reconcile` activates valid saved settings at startup while disabled; `recover` explicitly finishes a valid interrupted journal using that same path. Neither is a corrupt-record overwrite or arbitrary backup-selection command. The controller remains unhomed after activation.

From this Windows workspace, the task-local Debian rootfs is prepared and all nine launch scenarios are reproduced by:

```powershell
wsl -d GarciaMechBuilder -- sh -c 'sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/build.sh > /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/evidence/compiled-rtl-tests.log 2>&1 && sh /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/cnc1/tools/run_persistent.sh'
python -m unittest discover -s tests -p '*runtime*.py' -v
```

`run_persistent.sh` checks that the compiled module is installed. Before the nine launches, it starts from a clean profile/evidence/orchestrator/`controller_config` work copy and keeps `build/` and the run-id-keyed stores. It cleans only once, so the launches within one run still share their intended store.

The launcher uses fresh private IPC/mount/network/PID namespaces for each launch, unique task-local stores, an exact profile fingerprint and fresh run ID. It does not mount or open physical controller/machine devices. It preserves the user's source/configuration files. No board, FPGA, ESP or memory device was flashed.

## Remaining limits

Linux writes fsync the temporary file before atomic replacement and then the containing directory. Newly created directory names and their parents are also synced in order. Windows host tests cannot qualify Linux or device power-failure behavior. A selected storage medium, filesystem/mount options, power-loss behavior and physical fault injection still need measurement.

Rolling back **both** persistent files together after a complete reboot cannot be detected without an external monotonic anchor. Checksums detect accidental changes, not a malicious owner rewriting records. Corrupt/conflicting authority is held for explicit engineering repair; no automatic fallback to an older backup is implemented. Ongoing media corruption during an already operating session is not continuously monitored by this prototype.

This durable subset is a concrete bridge from saved calibration to actual running LinuxCNC. It is not yet complete machine-memory cartridge integration, physical homing/commissioning, public network authorization, production storage certification or hardware manufacturing readiness.
