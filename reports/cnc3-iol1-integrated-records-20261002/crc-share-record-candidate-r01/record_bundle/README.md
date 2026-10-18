# Staged one-motherboard record and DIC configuration

This is a proposed IS2 supplement and actual report-local C implementation. Four fitted STM32G031 controllers belong to one motherboard. They share its board serial, with each region record bound to its real MCU UID. No EEPROM, removable card or custom daughterboard was added.

The target executes a flash-record integrity reader and read-only IDENT telemetry chunking. A separate host verifier checks actual Ed25519 signatures under explicitly supplied keys. CRC is not authentication; a UID check in ordinary firmware is not secure attestation. No manufacturer trust root is provisioned, and developer-key metadata can never produce production trust. The signature does not prove fitted parts, factory measurements, calibration accuracy or wiring.

The frozen DIC CONFIG_WRITE payload is validated before sequence, accepted time and configuration change. The three group values drive elapsed-time debounce at 100us units. Configuration invalidation/replacement restarts the candidate stability timer. Rejected frames retain the prior configuration and never reload accepted progress. A new accepted epoch clears configuration qualification; nothing becomes ACTIVE. Runtime flash erase/program and an update bootloader remain absent.

The linker reserves independent final2KiB pages, leaving60KiB for application. No WRP/RDP/BOR/IWDG option bytes have been provisioned or measured. The two-page prefix/commit tests are software fault models. Actual flash ECC/torn-write behavior, factory programming/write protection and power loss require hardware qualification.

The IDENT chunk supplement is explicit and unadopted:40B IOL1 and96/176B CNC3 lengths stay unchanged,16B realtime stays intact, and8B record chunks use selected telemetry. Existing diagnostic acquisition still expects major0; coordinated host/master firmware work is required for provisioned revisions. Calibration and factory-test hashes bind separately retained records; missing records remain unqualified. Offline machine entitlement stays separate from board identity.

Evidence categories: Python cryptographic/record execution; the same C validators/filter with sanitizers; actual simulated SPI into that C; four ARM target compilations. These are not execution of DMA/IRQ/MMIO or physical flash/IO measurements.

Successor r02 adds strict host slot/UID argument rejection, a real linker overflow
negative, software IWDG start before factory-page reads and actual C two-generation
selection/torn-successor retention controls. A flash ECC NMI may cause a reset loop;
recovery from physical corrupted flash is not implemented or qualified. The default
DIC diagnostic filter is100us while configuration is unqualified. Source population
ends in the four-lane mask0x0F, not an extra card count.

Run `replay_record_config.py --out <fresh-directory> [--wsl-distro GarciaMechBuilder]`
for all three fresh evidence stages, or `--inventory` for a nonexecuting inventory.
The exact bundle is checked before execution and after it. The source inspection
category is distinct from compiled tests, ARM compilation and SPI simulation.

Peer review found a retained DIC sample-age wrap in r02. Successor r03 uses one
actual shared C age helper in the real DIC/DO target paths: FFFF is unavailable,
65534 remains representable, and both65535/65536 saturate. Cold DIC data is
unavailable until an actual sampled tuple commits. Once stale, the validity
latch remains invalid until a fresh sample, so a full32-bit timestamp wrap cannot
revive old data. Same-C boundary/rollover tests and a compiled truncation mutation
cover it. The SPI fixture also services1050 real accepted polls with sampling
explicitly disabled, retains old samples withFFFF age, then requires a resample.
This is not execution of the target GPIO/DMA/IRQ or proof of hardware poll jitter.

The final actual C interrupted-page control uses generation2 successor prefixes,
and conflicting same-generation/foreign-source diagnostic records fail closed.
Those C records are integrity-valid only; target signature authentication remains
absent and the separately supplied host trust registry cannot grant production.
