# Diagnostics, machine state and portable packages

**Reviewed 18 October 2026.** [Documentation index](README.md) · [Current engineering status](../reports/ENGINEERING_STATUS.md). The recorder/package implementation remains a disconnected host foundation. The later [Motion X12 appliance](CONTROLLER_OS.md) exposes the same diagnostics through the shared service; its Files destination validates/downloads approved-folder packages without extraction or apply.

4 October 2026. Implemented host software in the disconnected setup workspace. Claude owns routing; this work changes no PCB, firmware, gateware, real-time protocol or physical machine configuration.

The workbench keeps the operator flow simple: open **Diagnostics**, read the fault and next checks, inspect its retained history, and download a support report. **Try a fault example** creates a separate authored simulation. It neither discovers nor observes a machine. Deterministic explanations and compression make zero API calls.

## Shared service and evidence

`DiagnosticService` serves the same recorder, explanations, archives and setup transactions to the public CLI and local HTTP UI. Records have an exact versioned envelope: `schema_version`, `simulation_only`, `timestamp_ns`, `source`, `sequence`, `kind` and bounded JSON `data`. Time is explicitly caller-declared simulation monotonic time. It is not a hardware timestamp or a physical stop measurement. Each source's sequence advances; duplicate acknowledgement replay is exact-content-bound. Invalid records do not initialize storage.

The read-only machine-state projection is bound to the current active setup's store, epoch, revision, generation and configuration digest. Motion, spindle, I/O, safety, modules, temperatures, network and controller observations distinguish measured, commanded and reported values. Missing, invalid, stale, incompatible or differently bound facts remain unavailable. A new configuration revision cannot reuse an old observation as current evidence. The installed IS-2 target inventory is separate from observed/qualified capability; there are no invented presence signals, readiness percentages or motion permission.

Fault explanations keep the raw observations and provenance. A drive alarm alone establishes neither its cause nor a successful stop. Commanded velocity is a request; stop state, spindle behavior, homing and position need their own fresh observations and qualification. Unknown fault formats remain in the downloadable report even when the explanation catalog cannot interpret them. Logical M0–M11 map to display M1–M12. Soldered FPGA/I/O regions use whole-motherboard service; actual commodity compute/ESP/storage units are separate replaceable items.

## Bounded recorder

The current implementation is a synchronous **non-real-time host ingestion API**. Call it only from a service process outside the servo, STEP/DIR, encoder, watchdog and CNC1/CNC3 paths. No physical transport is connected to this recorder. The separate [current SIM2 runtime](../reports/board-finish-20261017/README.md) passes eight-/twelve-joint LinuxCNC/SPI/RTL virtual-feedback runs; that does not establish a live acquisition path into this recorder. A qualified production path still needs a bounded producer queue, declared sampling/freshness rules and loaded target tests; this API is not a real-time callback.

Defaults are a five-minute pre-fault target, 30-second post-fault target, at most 128 records/64 KiB raw per chunk, 96 chunks and 8 MiB of compressed storage plus reserved manifest space within the quota. Records are limited to 16 KiB. Immutable checksummed Zstd chunks are published before an atomic sealed manifest. Stable OS locks coordinate processes on one host; a synchronized cloud folder is not a distributed recorder. Host `fsync`/atomic-save tests do not establish media power-loss behavior.

Coverage comes from actual retained records, declared timestamps, sequence continuity and explicit gaps. Post-fault capture stays incomplete until later observations exist. Up to eight incident windows are pinned. Quota pressure reports dropped records and gaps instead of silently claiming complete capture. Normal rolling expiry and incident expiry are counted. One additional bounded chunk may exist during an atomic update; recognized abandoned chunks are detected/recovered. Corrupt files fail closed and are preserved. A missing Zstd runtime is an availability error, not a corruption verdict.

The example has 331 one-second observations, an authored Y/logical M2/display M3 alarm at 300 seconds and 30 seconds afterwards. Its only velocity fact is **commanded** 82 mm/s. It supplies no measured machine response. Interrupted generation resumes only an exact verified fixture prefix; conflicting data is preserved and rejected.

The example carries its own validated dual-X, four-motor gantry definition, including Y on logical M2. Its report and support package use that same definition and exclude unrelated workspace settings. Version 2 uses a separate example directory and preserves any earlier example recordings. Workspace records and actual saved setup snapshots remain separate. Fault/event content without the typed configuration binding is retained as source evidence and is not promoted into current machine-state facts.

Acknowledged appends currently publish a host-durable chunk/manifest update; a partially filled chunk is rewritten. Compressed byte size alone therefore does not establish reduced write traffic or flash wear. Production ingestion needs measured batching, queue/drop behavior and write amplification at its declared rates.

## Portable packages and recovery

All packages are one checksummed Zstandard frame containing strict USTAR regular files and a versioned SHA-256 inventory. Limits include 128 members, 8 MiB per member, 32 MiB payload, bounded metadata and an 8 MiB decompression window. Unsafe/ambiguous paths, links, devices, special/PAX/sparse members, duplicates, unexpected payloads, corrupt hashes, oversized frames and trailing/concatenated frames are rejected. Reads return bytes only: no extraction, interpreter, firmware installation or machine execution.

Exports create a new file atomically and never overwrite an existing source. A configuration snapshot includes the current draft, active saved configuration, retained profile drafts and saved generations from one locked state. AI prompts, credentials, provider caches and the private allowance ledger are excluded. Support exports add the diagnostic report; review local setup facts and records before sharing. Downloading never uploads to a support service.

Restore reads a **config** package, selects its active configuration (or explicitly its unsaved draft), then generates the ordinary revision-bound setup preview. Review/diff and the existing commit checks still apply. Imported package metadata cannot raise electrical/model limits or authorize motion. Restore creates a new inhibited, unhomed generation. This is disconnected configuration recovery, not the protected physical settings-cartridge/replacement qualification contract.

`.cncjob` is currently an inert package of explicitly selected program/assets. A GLB, photograph or G-code member remains ordinary data. There is no adopted native execution format, CAD importer, verified collision model, executable AI macro or automatic installation. Firmware/update packages are deliberately unsupported by this archive contract. SHA-256 and Zstd checksums detect corruption; they are not a signature, encryption or sender authentication.

## CLI

Use an explicit separate simulation directory; these commands never connect to a controller:

```powershell
python -m controller_config setup --directory .controller-setup-demo diagnostics status
python -m controller_config setup --directory .controller-setup-demo diagnostics state
python -m controller_config setup --directory .controller-setup-demo diagnostics state-schema
python -m controller_config setup --directory .controller-setup-demo diagnostics observation-example --output observation.json
python -m controller_config setup --directory .controller-setup-demo diagnostics example
python -m controller_config setup --directory .controller-setup-demo diagnostics report --example
python -m controller_config setup --directory .controller-setup-demo diagnostics append record.json
python -m controller_config setup --directory .controller-setup-demo diagnostics export support.tar.zst --example
python -m controller_config setup --directory .controller-setup-demo package backup setup.tar.zst
python -m controller_config setup --directory .controller-setup-demo package inspect setup.tar.zst
python -m controller_config setup --directory .controller-setup-demo package restore-preview setup.tar.zst --output reviewed-plan.json
python -m controller_config setup --directory .controller-setup-demo commit reviewed-plan.json --request-id restore-reviewed-1
python -m controller_config setup --directory .controller-setup-demo package job example.cncjob --entry program/main.ngc=example.ngc
```

Compression uses [Python's optional standard-library Zstandard backend](https://docs.python.org/3/library/compression.zstd.html), introduced in Python 3.14. Without it, ordinary setup remains available and compressed operations return `ARCHIVE_UNAVAILABLE`. No package is installed automatically. Dictionaries are not trained or loaded; their exact version/distribution and measurable benefit need separate qualification. No controller CPU-load, retention-duration, eMMC wear or cloud-cost savings are claimed from desktop compression results.

Verification and the current screenshots are in [the dated software report](../reports/diagnostics-zstd-20261004/README.md). Host/service/browser checks are separate from target compilation, real-time loaded operation, HDL simulation, FPGA fit/timing, ERC/DRC and physical measurements.
