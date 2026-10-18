# Disconnected configuration examples

Run from the repository root with Python 3.10 or newer; no third-party packages are needed:

```powershell
python -m examples.configuration.demo
python -m controller_config capabilities
python -m controller_config schema
python -m controller_config profile list
```

The API demonstration calls the same `ConfigurationService` methods as the CLI, creates a temporary store, selects/validates a virtual mill, generates illustrative wiring, applies a preview, backs up, changes scaling and restores the backup as a new revision. It also demonstrates conflict, stale-plan and armed-state refusals. Temporary files are removed when the demonstration exits.

`sim-mill-3axis.json`, `sim-lathe-2axis.json` and `configuration.schema.json` are readable snapshots of the built-in fixtures/schema. They describe no actual board terminal or physically commissioned machine. All terminal names start with `SIM.`. The fixture uses a bounded six-motor reference; it does not implement the expanded eight-motor design or discover CNC1 runtime capabilities.

For a persistent CLI demonstration, use a fresh dedicated directory:

```powershell
$demoDirectory = Join-Path $env:TEMP ("controller-config-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $demoDirectory | Out-Null
$demoStore = Join-Path $demoDirectory 'state.json'
$demoConfig = Join-Path $demoDirectory 'mill.json'
$demoPlan = Join-Path $demoDirectory 'apply-plan.json'
$demoBackup = Join-Path $demoDirectory 'backup.json'
$demoRestore = Join-Path $demoDirectory 'restore-plan.json'
python -m controller_config --store $demoStore init
python -m controller_config profile select sim-mill-3axis --output $demoConfig
python -m controller_config config validate $demoConfig
python -m controller_config wiring plan $demoConfig
python -m controller_config --store $demoStore config diff $demoConfig --output $demoPlan
python -m controller_config --store $demoStore config apply $demoPlan --actor cli-demo
python -m controller_config --store $demoStore backup create $demoBackup
python -m controller_config --store $demoStore backup restore-plan $demoBackup --output $demoRestore
python -m controller_config --store $demoStore config apply $demoRestore --actor cli-demo-restore
python -m controller_config --store $demoStore config show
python -m controller_config --store $demoStore audit
```

An unchanged restore is a no-op. The API demonstration changes scaling first, so it exercises an actual restoration. Plans are raw JSON files written by `--output`; ordinary stdout is a response envelope. Exports refuse existing files. Re-preview to a new plan filename after any configuration revision changes.

**The runtime flags are a local simulation fixture. Editing them does not prove a real machine is disarmed or stopped.** There is no physical state observer, driver connection, output command, commissioning action or motion permission in this package. The separate LinuxCNC/CNC1 workstream is not joined to this configuration demo. Future UI clients can call the shared service, but no UI integration or production server is claimed.

See [implementation and persistence boundaries](../../reports/CONFIGURATION_DEMO.md).

## Cartridge and replacement CLI

The cartridge/replacement APIs are also exposed through the common CLI:

```powershell
python -m examples.configuration.recovery_cli_demo
python -m controller_config cartridge --help
python -m controller_config recovery --help
```

The one-command demonstration runs public CLI subprocesses to save and inspect two file-backed cartridge records, explicitly initialize a fresh compute store, export/apply a bootstrap preview, and export/apply a compatible input-bank replacement preview. It also rejects a replacement against mismatched inventory. The original settings and source file stay unchanged; no homing or run permission is restored. Generated files live in a dedicated temporary directory and are removed on exit.

`cartridge inspect/save` require the cartridge directory and machine UUID. Recovery preview/apply additionally require a deliberately authored `--fixture-inventory` file. Generate that simulation selection with `recovery inventory`; it is not hardware discovery. Every plan exports to a new filename, and apply rereads the current dependencies through the existing shared service. Ordinary store-bound backup rules remain unchanged.

See [exact commands, persistent walkthrough and evidence](../../reports/RECOVERY_CLI.md). This recovery CLI remains disconnected even when other runtime workstreams are present; it does not expose a physical cartridge or module bus.
