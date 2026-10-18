# Disconnected module replacement and machine cartridge demonstration

28 September 2026. **Host software demonstration only.** A virtual grouped input bank can be replaced while the machine configuration stays byte-for-byte equivalent, and a fresh compute store can import that configuration through the existing shared service. Neither operation restores homing, permission to run or completed physical commissioning. No module was physically replaced, connected or programmed.

## What runs

The implementation is [controller_config/recovery.py](../WORKSPACE_REFERENCES.md#artifact-0d0d3286a284d740), with an executable [replacement demo](../WORKSPACE_REFERENCES.md#artifact-49162e4d8bfcc754) and [34 scoped tests](../WORKSPACE_REFERENCES.md#artifact-9c480a06aefaf3e3). The configuration model is unchanged; the shared service later gained one configuration-neutral audit event (below), and the public CLI was later extended, as recorded in the [recovery CLI report](RECOVERY_CLI.md).

```powershell
python -m examples.configuration.replacement_demo
python -m unittest discover -s tests -p test_configuration_recovery.py -v
```

The scoped run after the 28 September 2026 audit fixes passed all 34 tests (the original run passed 32; the two added tests cover the replacement audit entry). The demo returned success with zero physical commands and reports the shared audit actions `initialize`, `apply`, `replace_module` at store revision 1. It creates a temporary directory and removes its generated stores and cartridge files before returning.

The public Python API consists of `Cartridge.save/load`, `module_fixture` for explicitly selected virtual observations, and `RecoveryService.preview/apply`. Recovery always delegates configuration preview/application to `ConfigurationService`; it does not write an alternative configuration store or loosen the ordinary backup's same-store identity rule. The public CLI now exposes this API as `cartridge inspect/save` and `recovery inventory/bootstrap-preview/replace-preview/apply` through `python -m controller_config`; see the [recovery CLI report](RECOVERY_CLI.md) and [subprocess tests](../WORKSPACE_REFERENCES.md#artifact-8598a2cbf3ff67d2). A guided UI does not exist, and this report does not claim automatic hardware discovery.

## Observed demonstration

1. The three-axis mill fixture is stored in two validated cartridge records and imported into an initially empty compute store. This is simulated setup, not physical commissioning.
2. The virtual `SIM.INPUT_BANK0` identity changes from `SIM-IN-001` to compatible `SIM-IN-002`. The bank covers `SIM.DI0` through `SIM.DI7`; the current mill assigns its three home sensors to the first three inputs.
3. All machine settings and assignments remain equal. The replacement's own illustrative factory metadata changes from an input-filter clock correction of `15` to `-22` ppm. This metadata is authored fixture data, not a calibration measurement or an applied filter calculation. The demonstration proves separation of records, not calibration performance.
4. The returned verification list names only `x-home`, `y-home` and `z-home`, with wiring and polarity checks pending. Existing axis scaling values remain. All original commissioning records remain unverified; the demo cannot prove that unaffected axes were previously commissioned.
5. A 3.3 V fixture cannot replace the configured 24 V input bank. Separate tests also refuse an incompatible interface ABI and insufficient channel capacity.
6. A deliberately truncated generation-three write and a subsequent corrupted generation-three record each leave generation two readable.
7. A new empty compute store gets a different store UUID, binds to the same explicit machine UUID and imports the same machine configuration through shared-service preview/apply. Ordinary cross-store backup restore still returns `BACKUP_IDENTITY`.

Every receipt reports `outputs_inhibited: true`, `homed: false`, `run_permission: false` and `physical_commands: 0`. These are constraints of the disconnected model; they are not observations of physical inhibit wiring. No coolant-output bank or accessory execution has been added to the current drive/home-input schema.

## Cartridge format and recovery rules

Each slot is capped at **16,384 encoded bytes**, including its envelope, digest and required final framing newline. Two slots model **32,768 bytes** of payload storage. The unchanged default mill example measures **6,906 bytes per record**, or **13,812 bytes for its two copies**. Those figures do not include host filesystem allocation, sidecar files, EEPROM page overhead, proposed macros or recovery images. No memory chip is selected by this result.

A record contains format version, generation, machine UUID and the entire validated virtual machine configuration. Its SHA-256 digest covers those fields. It contains no compute-store UUID, module serial, factory calibration, firmware image, output permission or saved position. The machine UUID is independent of mutable machine name. Configuration dependency and electrical constraints remain the shared schema's validated virtual definitions.

Normal saves alternate to the older or invalid slot and compare the caller's expected generation. The valid peer stays untouched. Fault injection deliberately writes only a prefix of the target record. Exact canonical framing is required, so even interruption at the last byte cannot be accepted as a completed record. Initializing an empty cartridge produces one valid record; the demo explicitly saves a second copy to establish redundancy.

Load selects the highest valid generation, reports invalid slots and refuses two conflicting valid records at the same generation. Fully valid records from different machines are refused. Valid but unsupported cartridge or embedded configuration versions fail closed, including a future format with extra fields. Missing, malformed, oversized, duplicate-key, semantically invalid or digest-damaged records can fall back to their valid peer. No valid record means no import and no automatic overwrite. Generations are positive unsigned 32-bit values; wrap is refused.

Checksums detect corruption, not maliciously rewritten settings. A fresh compute store has no independent anti-rollback authority: a valid older fallback can be recovered with verification pending. An applied existing store, however, refuses module replacement if the selected cartridge generation/hash or store revision/configuration differs from its binding. It asks for explicit reconciliation, which is not implemented here. This prevents a torn newer record from silently rolling an already-bound machine back.

## Binding, preview and interrupted imports

`RecoveryService` receives the expected machine UUID and an inventory provider from the simulation caller. Its module compatibility comes from the built-in fixture registry; imported claims cannot raise electrical or interface capabilities. Inventory snapshots are copies, so clients cannot mutate that registry through a returned object.

Preview is read-only. Its plan binds the cartridge generation and full-record hash, observed fixture inventory, existing binding hash, shared-service destination identity/revision/configuration, and simulated runtime epoch. Apply reacquires the cartridge/recovery locks and recomputes the plan. A changed dependency or edited plan is refused.

For compute bootstrap, a sidecar reserves the machine/store binding before shared-service application and then marks it applied. An interrupted import can resume only with the same cartridge and inventory and either the original empty revision-zero store or its exact intended revision-one configuration. An unrelated existing configuration, later revision or foreign/corrupt binding cannot use this path to overwrite a store. The shared audit uses action `apply` and an actor label containing cartridge machine identity and generation; it does not claim an ordinary backup restore. An input-bank replacement changes no configuration, so the shared apply creates no revision; recovery instead appends a same-revision `replace_module` audit entry whose before and after digests are equal and whose actor names the machine, cartridge generation, slot and serial change (for example `...:g2:SIM.INPUT_BANK0:SIM-IN-001->SIM-IN-002`). This keeps a durable who/when record after the binding sidecar replaces the previous inventory.

After the shared service commits, recovery reacquires its store lock, verifies the committed identity/revision/configuration and rechecks runtime/inventory before finalizing the sidecar. Tests inject an ordinary intervening edit and require failure with the reservation left unresolved. For a replacement, the audit entry is written under that lock before the sidecar; if the sidecar write then fails, the audit records the attempt, the sidecar still names the old module and a retry records a second entry. This is a fail-closed coordinated workflow, not an atomic two-file transaction. File-only readers/writers must honor the cooperative locks; production state, hot-removal and bus ownership need a different authoritative implementation.

## Test coverage and remaining work

The 34 tests cover same-machine new-compute import, the replacement audit entry and its ordering before the sidecar, ordinary foreign-backup refusal, own-module metadata, retained settings, affected checks, wrong voltage/ABI/channel count, unknown inventory, forged readiness/capabilities, topology bounds, store and runtime changes, stale plans, mixed identities, ambiguous generations, future schemas, record limits, torn/corrupt fallback, final-byte interruption, interrupted reservation/application/finalization and conflicting retry states.

Still required:

- A machine-cartridge/host-mirror authority and predecessor-chain protocol, version migration and explicit reconciliation. Ordinary current `ConfigurationService` edits do not yet update the cartridge or binding; subsequent replacement therefore refuses until reconciliation is designed.
- A real module identity bus, firmware compatibility/update/recovery rules, factory-calibration verification, physical presence/ownership fencing and a machine-state authority. The current fixture registry does not discover or authenticate equipment.
- An actual memory driver, page layout, commit protocol, hardware write-protect, corruption/endurance strategy, supply hold-up and measured interrupted-power behavior. File truncation/atomic replacement is not EEPROM qualification; host filesystem durability and stale lock recovery remain limited.
- Persistent physical verification evidence, a guided UI for recovery (the CLI commands exist), permission wiring, output defaults, replaceable connectors, circuit and PCB work, and physical electrical/EMC/mechanical tests.

The [repairability architecture](../docs/MODULAR_REPAIR_AND_MEMORY.md) defines the wider product requirement. This demo advances its configuration and identity behavior without making the six-joint baseline, expanded hardware candidate or physical manufacture more complete than the existing evidence establishes.
