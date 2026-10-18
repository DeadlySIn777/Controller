# Boot storage and offline provisioning

30 September 2026. User-requested SD/NVMe option and Optane listing review. This is a carrier/provisioning requirement and component investigation, not an added M.2 socket, an implemented image creator or a validated boot image. No storage was purchased or installed.

Provide supported removable boot/recovery media and an optional NVMe path where the **exact compute module** exposes and boots the necessary PCIe interface. Keep the base controller usable without buying an SSD. Consider SD for the low-cost/Lite route and recovery media, module eMMC where supplied, and ordinary replaceable NVMe for larger jobs/models/history on qualified hosts. Keep screen size independent of storage or motor/I/O capacity. A microSD slot and M.2 connector do not make every inserted compute variant support both.

Raspberry Pi documents SD boot for Lite variants and onboard eMMC for eMMC variants. CM4/CM5 carrier families expose PCIe storage options; NVMe boot needs the appropriate carrier, bootloader configuration and supported drive. The eMMC variant's primary SD interface is already used on the module; do not promise a shared carrier microSD boot slot on those variants. [Compute-module boot/provisioning](https://www.raspberrypi.com/documentation/computers/compute-module.html), [Raspberry Pi NVMe boot](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#nvme-ssd-boot).

CB1/CB2 require their own exact revision/interface/image checks. Do not advertise native PCIe NVMe for CB1 merely because the CM bay can physically carry a PCIe pair. USB storage through a qualified bridge is a distinct route, with different costs/boot support and throughput. The [compute-bay audit](../reports/board-completion-20260930/COMPUTE_BAY_PIN_AUDIT.md) owns the per-contact compatibility matrix.

| Compute family | SD/eMMC candidate | NVMe candidate | Present evidence boundary |
|---|---|---|---|
| CM4 / CM5 Lite | Carrier SD | PCIe x1 and configured NVMe boot | Manufacturer route; custom carrier/drive/loaded timing untested |
| CM4 / CM5 with eMMC | Module eMMC; primary SD pins occupied | PCIe x1 and configured NVMe boot | Own matching prepared image and bootloader required |
| CB1 SD | Carrier SD | No exposed native PCIe on audited revision | SD boot is distinct from the conflicting USB FEL recovery contacts |
| CB1 eMMC | Exact eMMC/SD boot revision to qualify | No established native PCIe | Complete contact/recovery audit still open |
| CB2 standard | eMMC and documented SD route | Published PCIe x1, NVMe Linux startup via U-Boot on SD/eMMC | RK3566 does not initially boot from NVMe alone; custom power/reset/link untested |

The CB2 route is documented in [BTT's V3.0.2 release](https://github.com/bigtreetech/CB2/releases/tag/V3.0.2). Never inherit this table for a new CB2 Lite or revised module solely from its product-family name. PCIe AC coupling, clock/reset and socket power differ across the eligible modules and require one reviewed carrier design; a module selector cannot replace that work.

## User's Optane candidate

The supplied title advertises a 16 GB Intel Optane Memory M.2 2280 device and mentions 16/32 GB. It does not establish an exact orderable MPN, seller authenticity, new condition, warranty, firmware or stock. Preserve it as a sourcing lead, not the selected storage BOM. The separate user estimate of approximately $35 for 128 GB-and-under NVMe remains unquoted; currency, exact SKU, quantity and delivered cost are not established.

Intel's original Optane Memory/M10 families are small **nonvolatile NVMe storage**, not extra system RAM. The M10 brief specifies PCIe 3.0 x2, M.2 2280 B+M form and 16/32/64 GB variants. The listing cannot establish that it is specifically M10. Its old PC cache-acceleration feature is different from using a drive as a standalone storage device, and must not be promised on our ARM hosts. An exact 16 GB drive can only supply that storage capacity; it is not a 128 GB SSD and cannot increase compute RAM or AI model memory. [Intel M10 product brief](https://www.intel.com/content/dam/www/public/us/en/documents/product-briefs/m10-accelerates-mobile-desktop-speed-product-brief.pdf).

Intel states the original Optane Memory and M10 families have reached end of life and ended interactive support in 2024. Therefore they are a surplus/experimental comparison rather than the standard production storage recommendation. A claimed new unit can be old stock. Qualified PCIe link-width negotiation, NVMe enumeration/boot, power/thermal, update space and supplier continuity remain necessary even if it physically fits. [Intel support notice](https://www.intel.com/content/www/us/en/support/articles/000098370/memory-and-storage/intel-optane-memory.html).

Intel's original [16 GB product specification](https://www.intel.com/content/www/us/en/products/sku/97544/intel-optane-memory-series-16gb-m-2-80mm-pcie-3-0-20nm-3d-xpoint/specifications.html) lists 3.5 W active power: approximately 1.06 A at 3.3 V, not a guaranteed peak-current requirement. That already exceeds the audited modules' auxiliary-3.3-V allowance. A storage socket needs its own adequately rated, protected and sequenced 3.3 V supply; do not power this drive from the module's auxiliary output. The specification does not claim enhanced power-loss data protection.

Prefer costing a current ordinary NVMe with adequate usable capacity alongside SD/eMMC, rather than choosing discontinued 16 GB Optane from its impressive marketing description. Do not claim today's NVMe market is universally expensive or infer an economical complete option from a drive price alone. Include socket, permitted 2230/2242/2280 mounting lengths, 3.3 V power/inrush protection, PCIe routing and clocks/reset, screws/standoffs, clearance/cooling, assembly/test and any host limitations. An M.2 SATA drive is not a PCIe NVMe substitute for this proposed socket.

## Prepared images, recovery and image creation

Each supported replacement compute module or SD/NVMe must contain its own approved matching host image. The FPGA-facing protocol and service API stay stable for qualified module exchanges; neither SD nor NVMe automatically reflashes the FPGA or ESP. A release manifest must bind exact module/profile/carrier, bootloader/kernel/device tree/real-time driver, application and compatible gateware/service versions, hashes and verification results. Storage itself does not compile firmware: reproducible build tools produce the approved artifacts before packaging them.

Plan a common-service CLI/UI workflow for inspecting the exact media, previewing the target/profile and destructive write, exporting a backup, writing an approved image to explicitly selected removable media and verifying it. Do not overwrite user source files, machine settings or an ambiguous system disk. Keep settings, offline licence entitlement, factory calibration and fault history separate from replaceable OS images. Preserve the protected configuration-cartridge/interrupted-save requirement until its physical contract is reconciled; an ordinary SD/NVMe is not automatically that cartridge.

Power-off service and offline recovery remain the first-release rule. Installations and image changes occur only in a stopped service state with independent machining inhibition, never during a cut. A failed or interrupted image update must reach a defined recovery state and never restore motion permission or homing. Validate image footprint including recovery/update headroom, write workload, read-only/overlay choices where appropriate, media wear, abrupt-power-loss behavior and the loaded UI/LinuxCNC timing before selecting a minimum capacity or calling storage industrial-qualified.
