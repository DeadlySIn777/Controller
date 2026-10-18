# Disconnected configuration service demonstration

28 September 2026. **Implemented file-only prototype:** `python -m controller_config` is the first executable `cncctl` demonstration, not an installed global command or production CNC control API. The service has no physical device/network/GPIO transports and sends no LinuxCNC motion commands.

## Implemented slice

| Function | Concrete behavior |
|---|---|
| Common service | `ConfigurationService` exposes capabilities/schema, profile selection, validation, wiring, preview/apply, show/audit and backup/restore preview. CLI and executable API example use these same methods. |
| Typed versioned devices | Identity/revision, declared electrical capabilities, functions, required connections, calibration, compatible profiles, permitted commands, output owner, requested/observed readiness, startup/loss behavior and commissioning records. Unknown fields, wrong types and unsupported versions fail validation. |
| Explicit virtual identities | `virtual-baseline-6j-2enc`, two simulated mill/lathe profiles and authored virtual drive/switch models. No claim of observed physical identity or imported roadmap capabilities. |
| Validation | Rejects duplicate devices/connections, resource collisions, unavailable resources, role/signal mismatch, incompatible voltage/current/rate, negative/nonfinite/boolean quantities, altered device limits, incompatible profile topology and claimed completed commissioning. |
| Illustrative wiring | Uses only `SIM.*` terminal groups with function, voltage, current/rate and false physical-verification status. These are not the hardware ledger's physical terminal assignments. |
| Preview and transaction | Explicit JSON diff; candidate checksum; store ID, base revision/digest and simulated runtime epoch binding; apply revalidates and rejects stale/edited plans. Unsafe simulated state is checked before preparing and again before persisting a change. |
| Reversible persistence | Same-directory temporary file, flushed/fsynced before atomic replacement. Configuration, revision, prior configurations and audit commit in one document. An exclusive lock rejects competing writers. |
| Backup/restore | Checksummed, schema-validated same-store backup; restore requires a fresh preview and creates a new monotonically increasing revision. It never restores runtime flags, permission, verified position or physical commissioning. |

The virtual board exposes six grouped motion resources and sixteen home-input resources for configuration; two reference encoder ports are explicitly unallocated in this slice. It has no motion command API. The simulated profile is deliberately smaller than either complete hardware candidate: external-drive enable/alarm, spindle, complete general I/O, encoder configuration, plasma, Modbus, ESP accessory policies and expansion adapters remain future work.

Device output ownership is currently `none_simulation_only`; requested readiness is false and observed readiness unverified. Startup/loss policy fields describe the fixture and do not switch anything. Future accessory profiles may have different qualified ownership/default requirements; the schema does not establish live ESP automation. All calibration values remain unverified and commissioning checks pending. An imported file cannot assert measured evidence.

## Executable demonstration and checks

```powershell
python -m unittest discover -s tests -p test_configuration_service.py -v
python -m examples.configuration.demo
python -m controller_config capabilities
python -m controller_config schema
```

**40 scoped tests passed** after the 28 September 2026 audit fixes and their review (the first recorded run passed 32; the audit-fix run before review passed 39). They include API and subprocess CLI paths, identical result keys for a no-op apply, reporting of numeric representation changes such as `5` to `5.0`, the configuration-neutral `replace_module` audit event, its forgery checks and the absence of any public event-writing method or CLI command, bounded retry of a Windows sharing refusal while a reader holds the store open, electrical/resource rejection, huge integers and malformed API inputs, simulated armed/running/connected refusal, epoch and revision staleness, invalid restore data, forged readiness despite a recomputed checksum, foreign-store backup rejection, atomic-replace failure retaining the old file, busy/corrupt stores and preservation of existing exports. These are host software tests; they do not add physical or real-time qualification.

The executable API demonstration applies a virtual mill at revision 1, changes an unverified scale from 200 to 250 steps/mm at revision 2, and restores the original configuration at revision 3. Its audit contains initialize/apply/apply/restore. Conflict, stale replay and armed-state attempts are refused. It writes only a temporary directory and verifies restored configuration equality before removing that directory. [Demo source](../examples/configuration/demo.py), [CLI walkthrough and fixtures](../examples/configuration/README.md), [tests](../tests/test_configuration_service.py).

## API/CLI contract

`capabilities` and `schema` work without a store. `init` alone creates one, refusing any existing state. `profile list/select` gives supported virtual configurations. `config validate` and `wiring plan` do not persist changes. `config diff --output` generates the raw plan consumed by `config apply`; `backup restore-plan --output` uses the same apply path. `config show` and `audit` report the resulting state. `backup create` exports the current configuration without runtime flags.

CLI responses contain `schema_version`, `ok`, `simulation_only` and either `result` or an error with stable `code`, `message` and `path`. Successful service operations return exit 0; configuration/I/O refusal returns exit 2. Only `--help` uses normal argparse usage output; argument-syntax errors return the same JSON envelope with code `ARGUMENT_ERROR` and exit status 2. Named raw exports refuse overwriting files. Profile, schema and capability values are copies; mutating a returned catalog cannot increase service limits.

Apply plans are bound to a specific store/configuration revision and simulated epoch. A successful changing apply consumes that revision; replay fails. A no-op produces no revision and returns the same result keys as a changing apply, with `changed: false`, `simulation_only: true` and `commissioning: "unchanged; no revision created"`. Diffs compare the stored canonical JSON representation rather than Python equality, so a `5` to `5.0` edit is reported as a change and matches the differing candidate digest. Device availability and electrical limits come from the authored fixture registry, not the supplied profile. All persisted configurations and restored candidates pass validation again.

## Persistence and authority limits

- Audit actions `initialize`, `apply` and `restore` accompany configuration revisions. `replace_module` is a configuration-neutral event written by module-replacement recovery at the current revision with equal before/after digests. It is written only by `RecoveryService.apply` through an internal lock-held helper after its binding, inventory, cartridge-generation and stale checks; the service, CLI and UI expose no free-standing event command, so a service caller cannot record a module swap that recovery did not perform; a store containing any other action, or an event that claims a configuration change, is refused as `STORE_CORRUPT`. Stores containing `replace_module` cannot be read by code older than this change.
- Store retains the latest 20 prior configurations and 100 audit entries; explicit backup files retain their own snapshot. Restore preserves the current store's revision/history rather than importing old audit or rewinding revision numbers.
- SHA-256 detects accidental changes; it is not a signature, authorization token or tamper-proof audit. Actor names are descriptive labels. This local prototype has no authenticated server or multi-user authorization policy.
- Cooperative writers share an exclusive `.lock` file. A crashed writer can leave that lock and a temporary file; there is deliberately no automatic stale-lock stealing. Inspect the process and intact store before manual recovery. Atomic replacement avoids partial live JSON; complete power-loss durability on every filesystem/storage/cloud-sync stack is not established. Windows directory metadata is not fsynced by this prototype. On Windows the final replace is refused while any other process holds the store open without delete sharing, including a concurrent `config show`/`audit` reader (readers take no lock), OneDrive synchronization or an antivirus scan. The writer retries that refusal five times over about 0.4 s while still holding its lock; a longer hold fails closed with `IO_ERROR`, the temporary file removed and the previous store intact. A host test holds a reader open during apply and passes; a one-off run of that test with the retry disabled reproduced the refusal (`PermissionError`) on this Windows 11 host.
- The simulated runtime provider is checked twice, but it is not a physical controller-state oracle or a cross-process production motion lease. Editable local flags cannot establish that equipment is stopped. A production implementation needs authoritative ownership, state freshness and atomic configuration/motion exclusion.
- The separate LinuxCNC/CNC1 runtime demonstration is not yet connected to this service. No frontend integration, HAL/firmware generation, actual discovery, voltage measurement, wiring verification or calibration procedure is claimed.

Next integration work is to bind the common configuration record to discovered, versioned runtime capabilities and authoritative stopped/maintenance state; expand typed device/harness records; define selective commissioning invalidation; and connect the existing UI through the same service. Keep preview, validation and recovery behavior when adding those adapters. The current prototype remains explicitly disconnected.
