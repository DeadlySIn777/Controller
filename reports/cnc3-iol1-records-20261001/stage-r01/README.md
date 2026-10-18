# Staged one-motherboard record and DIC configuration

This is a proposed IS2 supplement and actual report-local C implementation. Four fitted STM32G031 controllers belong to one motherboard. They share its board serial, with each region record bound to its real MCU UID. No EEPROM, removable card or custom daughterboard was added.

The target executes a flash-record integrity reader and read-only IDENT telemetry chunking. A separate host verifier checks actual Ed25519 signatures under explicitly supplied keys. CRC is not authentication; a UID check in ordinary firmware is not secure attestation. No manufacturer trust root is provisioned, and developer-key metadata can never produce production trust. The signature does not prove fitted parts, factory measurements, calibration accuracy or wiring.

The frozen DIC CONFIG_WRITE payload is validated before sequence, accepted time and configuration change. The three group values drive elapsed-time debounce at 100us units. Configuration invalidation/replacement restarts the candidate stability timer. Rejected frames retain the prior configuration and never reload accepted progress. A new accepted epoch clears configuration qualification; nothing becomes ACTIVE. Runtime flash erase/program and an update bootloader remain absent.

The linker reserves independent final2KiB pages, leaving60KiB for application. No WRP/RDP/BOR/IWDG option bytes have been provisioned or measured. The two-page prefix/commit tests are software fault models. Actual flash ECC/torn-write behavior, factory programming/write protection and power loss require hardware qualification.

The IDENT chunk supplement is explicit and unadopted:40B IOL1 and96/176B CNC3 lengths stay unchanged,16B realtime stays intact, and8B record chunks use selected telemetry. Existing diagnostic acquisition still expects major0; coordinated host/master firmware work is required for provisioned revisions. Calibration and factory-test hashes bind separately retained records; missing records remain unqualified. Offline machine entitlement stays separate from board identity.

Evidence categories: Python cryptographic/record execution; the same C validators/filter with sanitizers; actual simulated SPI into that C; four ARM target compilations. These are not execution of DMA/IRQ/MMIO or physical flash/IO measurements.
