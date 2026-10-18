# Cartridge and module recovery through the common CLI

28 September 2026. The file-backed cartridge and replacement APIs now run through `python -m controller_config`. These commands use the existing `Cartridge`, `RecoveryService` and `ConfigurationService` implementations. They do not create another settings store or change the ordinary backup identity rule. No global command installation is required.

## Run the complete workflow

```powershell
python -m examples.configuration.recovery_cli_demo
python -m unittest discover -s tests -p test_recovery_cli.py -v
```

The executable demonstration starts public CLI subprocesses in a dedicated temporary directory. It exports the three-axis mill profile, saves both bounded cartridge records, inspects them without creating a compute store, explicitly initializes a new store and imports the configuration through a saved bootstrap preview. It then authors a compatible replacement observation, saves a replacement preview, refuses applying that preview against the unchanged original inventory, and applies it against the matching replacement inventory. Settings and the original exported source remain unchanged. Temporary files are removed when it returns.

The scoped acceptance suite passed **10 subprocess tests** (rerun after the 28 September 2026 audit fixes). It covers that successful workflow with a nondefault user scaling value, the replacement's own factory metadata and affected verification list, the replacement's own same-revision `replace_module` audit entry (not the earlier bootstrap entry), inspect-only behavior, compare-and-save generation checks, wrong machine and destination store, wrong voltage/ABI/channel count, forged inventory/capabilities, stale inventory/cartridge/store, altered permission flags in a plan, non-overwriting exports, JSON errors and ordinary cross-store backup refusal. The broader regression is recorded separately after integration with the other workstreams.

## Public commands

| Command | Explicit input | Behavior |
| --- | --- | --- |
| `cartridge inspect` | `--directory`, `--machine-id` | Read and validate the existing bounded records. Never initializes a cartridge, compute store or binding. |
| `cartridge save` | Same identity/path, `--configuration`, `--expected-generation` | Validate raw simulation configuration and call compare-and-save. Zero initializes an empty cartridge's first record; a second explicit save establishes the second valid record. |
| `recovery inventory` | `--input-bank`, `--output` | Export an authored fixture selection, such as `input-original` or `input-replacement`. No hardware discovery occurs. |
| `recovery bootstrap-preview` | Global `--store`; `--directory`, `--machine-id`, `--fixture-inventory`, `--output` | Preview importing a matching cartridge into a previously initialized empty compute store. Only the requested new plan export is written. |
| `recovery replace-preview` | Same inputs | Preview a compatible replacement input bank against an already bound store. |
| `recovery apply` | Plan filename; global `--store`; `--directory`, `--machine-id`, `--fixture-inventory` | Re-observe and revalidate all dependencies through `RecoveryService.apply`, then delegate settings changes to the shared service. |

The existing `profile`, `config`, `wiring`, `backup`, `audit`, `schema`, `capabilities` and `init` operations retain their successful response formats. All operational and argument errors return a JSON envelope with `ok: false`, a named error code and exit status 2. Successful operations return `ok: true` and exit status 0. `--help` remains ordinary human-readable usage text.

`--output` exports **raw JSON**, suitable for a later CLI input. Standard output is a response envelope and must not be redirected as though it were a raw plan. Existing export destinations are refused. A replacement apply leaves the configuration and revision unchanged and appends one `replace_module` entry to `audit`, naming machine, cartridge generation and the serial change. Every recovery apply still returns `outputs_inhibited: true`, `homed: false`, `run_permission: false` and `physical_commands: 0`. Plan flags are never accepted as machine permission; the entire plan must equal the freshly computed preview.

## Persistent walkthrough

Run from the repository root. These commands create only a uniquely named directory under the host's temporary directory. Nothing initializes or attaches a physical device.

```powershell
$recoveryDirectory = Join-Path $env:TEMP ('controller-recovery-' + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $recoveryDirectory | Out-Null
$recoveryMachine = [guid]::NewGuid().ToString()
$recoveryStore = Join-Path $recoveryDirectory 'compute.json'
$recoveryCartridge = Join-Path $recoveryDirectory 'cartridge'
$recoveryConfig = Join-Path $recoveryDirectory 'machine.json'
$recoveryInventory = Join-Path $recoveryDirectory 'input-original.json'
$replacementInventory = Join-Path $recoveryDirectory 'input-replacement.json'
$bootstrapPlan = Join-Path $recoveryDirectory 'bootstrap-plan.json'
$replacementPlan = Join-Path $recoveryDirectory 'replacement-plan.json'

python -m controller_config profile select sim-mill-3axis --output $recoveryConfig
python -m controller_config cartridge save --directory $recoveryCartridge --machine-id $recoveryMachine --configuration $recoveryConfig --expected-generation 0
python -m controller_config cartridge save --directory $recoveryCartridge --machine-id $recoveryMachine --configuration $recoveryConfig --expected-generation 1
python -m controller_config cartridge inspect --directory $recoveryCartridge --machine-id $recoveryMachine
python -m controller_config --store $recoveryStore init
python -m controller_config recovery inventory --input-bank input-original --output $recoveryInventory
python -m controller_config --store $recoveryStore recovery bootstrap-preview --directory $recoveryCartridge --machine-id $recoveryMachine --fixture-inventory $recoveryInventory --output $bootstrapPlan
python -m controller_config --store $recoveryStore recovery apply $bootstrapPlan --directory $recoveryCartridge --machine-id $recoveryMachine --fixture-inventory $recoveryInventory

python -m controller_config recovery inventory --input-bank input-replacement --output $replacementInventory
python -m controller_config --store $recoveryStore recovery replace-preview --directory $recoveryCartridge --machine-id $recoveryMachine --fixture-inventory $replacementInventory --output $replacementPlan
python -m controller_config --store $recoveryStore recovery apply $replacementPlan --directory $recoveryCartridge --machine-id $recoveryMachine --fixture-inventory $replacementInventory
python -m controller_config --store $recoveryStore config show
python -m controller_config --store $recoveryStore audit
```

The machine UUID identifies the modeled machine separately from the new compute-store UUID. A real product still requires an independently established machine identity. Inventing or copying a UUID does not authenticate physical equipment.

## Observation and authority boundaries

Inventory JSON has exactly these fields:

```json
{
  "schema_version": 1,
  "kind": "disconnected_fixture_inventory",
  "simulation_only": true,
  "provenance": "authored_builtin_module_fixtures_v1",
  "modules": {"SIM.INPUT_BANK0": "input-original"}
}
```

The CLI rereads that file every time recovery requests an inventory observation. Module limits, serial and factory metadata come from the built-in fixture registry; user-supplied capabilities, additional slots and claims of physical discovery are rejected. The selected fixture identity and full fixture record become part of the dependency-bound recovery plan. The filename itself is not a machine identity: another file selecting the same built-in observation is equivalent.

These are **disconnected host-file operations**. Fixture inventory and stopped-state assumptions are not authoritative machine observations. No force-approval, ready/homed, physical transport, firmware flash or motion switch exists in these recovery commands. The machine's own output inhibit has not been measured. The replacement currently covers one eight-input virtual bank, not arbitrary accessory modules or the expanded eight-motor controller.

The existing [cartridge/replacement report](MODULE_REPLACEMENT_DEMO.md) documents the bounded two-record format, corruption handling, binding reservation, interrupted bootstrap recovery, cooperative locks and non-atomic multi-file boundary. Checksums detect corruption rather than authenticate a user. The CLI does not add EEPROM durability, physical module presence, transactional mirror authority, reconciliation after ordinary settings edits, persistent commissioning or automatic field recovery. Those remain separate engineering work.

Source: [common CLI](../controller_config/__main__.py), [subprocess tests](../tests/test_recovery_cli.py), [one-command demonstration](../examples/configuration/recovery_cli_demo.py).
