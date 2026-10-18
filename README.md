# Visual CNC controller — engineering workspace

Documentation reconciled **18 October 2026** against recorded decisions and evidence. The controller has working disconnected software, LinuxCNC/RTL integration and substantial native electrical/PCB work. Routing, complete electrical qualification, FPGA physical implementation and physical machine qualification remain unfinished. **There is no manufacturing release.**

## Start here

| Document | Purpose |
| --- | --- |
| [Complete documentation index](docs/README.md) | All topic guides, component documentation and historical evidence |
| [Project briefing](PROJECT_BRIEFING.md) | Product, architecture, implemented work and remaining work |
| [Project memory](PROJECT_MEMORY.md) | User decisions and constraints to preserve |
| [Engineering status](reports/ENGINEERING_STATUS.md) | Latest recorded results, exact sources and limitations |
| [Current acceptance gates](docs/CURRENT_ACCEPTANCE_GATES.md) | Requirements still needed for release |
| [Build plan](docs/BUILD_PLAN.md) and [platform roadmap](docs/PLATFORM_ROADMAP.md) | Execution order and proposed capabilities |

## Current product contract

[IS-2](docs/MOTHERBOARD_IS2.md) requires **one active custom motherboard with a soldered FPGA and all twelve motor interfaces fitted**, individual enable/alarm on all twelve, at least eight usable motors, four base ABZ encoders, 24 general DI and 16 smart general DO, plus the specified fast inputs, process/analog interfaces, communications, protection and watchdog/permission circuitry. Purchased compute, ESP and storage/settings modules remain replaceable. The older passive base, removable custom motion/I/O cards and motors-9–12 expansion card are superseded.

Local LinuxCNC owns motion planning; the FPGA supplies deterministic timing/capture and the ESP has a bounded diagnostic/service role. Accessory automation is a separately qualified extension. The touchscreen, CLI and optional AI proposals share validation and reversible configuration transactions. Normal operation and recovery remain available offline without AI credits. See [setup](docs/SETUP_WORKBENCH.md), [configuration](docs/CONFIGURATION_AND_CLI.md), [diagnostics](docs/DIAGNOSTICS_AND_PACKAGES.md) and [OS experience](docs/CONTROLLER_OS.md).

Screen options cover the **7-, 10-, 12-, 14-, 18- and 21-inch classes and further qualified sizes**. Screen size and software licensing do not remove fitted motor channels or required I/O. Every package must include and cost its stated display, compute, supplies, enclosure, harnesses and setup scope. See [display tiers](docs/DISPLAY_TIERS.md) and [commercial policy](docs/COMMERCIAL_MODEL_AND_LICENSING.md).

Power-off service exchanges an approved commodity module or the whole motherboard using keyed pluggable terminal/harness groups. Preserve protected machine settings, mirror/export recovery, offline entitlement and deliberate inhibited restart. Whole-board service has its own verification and cost requirements; no five-minute replacement guarantee is established. See [repair and machine memory](docs/MODULAR_REPAIR_AND_MEMORY.md).

## Evidence to read in context

| Scope | Recorded result | Boundary |
| --- | --- | --- |
| Adopted Source26/ROOT104, published CAD30 | 3,508 required joins remain; native ordinary DRC 0 errors/0 warnings; Source26 ERC 0 errors/70 warnings | Dated adopted source, distinct from later isolated finishing work |
| [17 October finishing continuation](reports/board-finish-20261017/README.md) | Recovered R299 full native result: 1,172 required joins / 1,183 API items, 0 ordinary errors/333 warnings/0 parity issues | Unfinished continuation; no adoption or manufacturing promotion |
| Isolated corrected baseline in that continuation | Same 1,172 joins; cached-fill DRC 0 ordinary errors/332 warnings/0 parity issues | Duplicate-via/BOM correction; no fresh refill in that check |
| Composed routing stages 1–4 | Native input/source/geometry checks recorded; full refill/AFTER qualification remains open in the cited report | Stale cached fills cannot establish new connectivity or ratings |
| Canonical disconnected SIM2 correction | Actual full-core mapping: 15,805 LUT4 + 2,107 ADD = 17,912; 63 RAM5K; fresh eight-/twelve-joint LinuxCNC/C/SPI/RTL/virtual-feedback checks | Functional mapping and simulation; physical wrapper, vendor place/route and timing remain open |
| Historical CNC1 baseline | [Six-joint/two-encoder integration](reports/CNC1_INTEGRATION.md), [synthesis](reports/FPGA_SYNTHESIS.md) and [recovery](reports/PERSISTENT_RUNTIME.md) | Preserve the original tested source, date, limits and profile |

Use the source-bound [engineering status](reports/ENGINEERING_STATUS.md) and continuation receipts before quoting a count. Source inspection, host tests, target compilation, HDL simulation, FPGA mapping, circuit ERC, board DRC and physical measurements establish different things. No physical commissioning or complete machine rating follows from the table.

The immutable [Source26 cost audit v11](reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11/README.md) is a dated partial basket: 105 exact MPNs priced, 185 MPNs/720 fitted pieces unpriced. Known-priced consumed parts at 1/10/100 controllers are US$1,091.51/$877.37/$796.51 per board. Modules, displays, fabrication, assembly, programming/test and packaging remain additional unknowns. US$400 is a preliminary assembly reference; a complete product cost or PCBWay quote is not established.

## Use the disconnected workbench

From this directory, with the required Python dependencies available:

```powershell
python -B -m controller_config setup --directory .controller-setup-demo serve --port 8766
```

Open `http://127.0.0.1:8766/`. This starts the local simulation setup UI and shared service. It does not commission or authorize a physical machine. The [workbench guide](docs/SETUP_WORKBENCH.md) describes intake, readiness, reviewed saves, backup recovery and optional AI budgets. Use a separate demonstration directory to preserve existing machine configurations.

To inspect the engineering bench before choosing checks:

```powershell
python -X utf8 tools/validate_controller.py --inventory
```

The documented full disconnected bench is `./validate_controller.ps1 --full` or `python -X utf8 tools/validate_controller.py --full`. It creates a new evidence directory. Missing tools and unfinished stages remain explicitly blocked; physical tests remain unrun. See [Rev A qualification](docs/REV_A_QUALIFICATION.md) and the [PCBWay submission checklist](manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md).

The [200-feature catalogue](docs/FEATURE_CATALOG.md) preserves proposals and stable IDs. Dated research, component READMEs and report snapshots keep their original evidence scope; use the [documentation index](docs/README.md) to find current guidance before interpreting them as product capabilities.

## Published native board snapshot

The existing [board-review package](BOARD_REVIEW.md), its native baseline/staged files and original provenance remain available alongside the complete engineering source. See [GitHub publication scope](GITHUB_PUBLICATION.md) for the source/evidence inventory.
