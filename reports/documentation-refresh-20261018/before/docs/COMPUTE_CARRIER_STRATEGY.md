# Compute carrier: CM4/CM5-style footprint

28 September 2026; user direction updated 30 September 2026. **Use the Raspberry Pi CM4/CM5 dual-100-pin physical ecosystem for the compute bay**, with separately verified CM4, CM5, BTT CB2 and CB1 profiles. This is now the user's mechanical/platform direction, rather than merely a preferred study. Exact supported SKUs/revisions, electrical paths, host images and production BOM remain qualification decisions; no interchangeable-module claim is established by the connector shape.

The user also requested physical selection instead of a full firmware update. The [cold-start compute selector proposal](COMPUTE_MODULE_SELECTOR.md) records a three-bit DIP or coded rotary selector, preinstalled per-module profiles, fail-closed startup and shared CLI/UI diagnostics. It is a design contract, not fitted hardware or a working profile-selection feature. Linux images/device trees still need to match each SoC. A future purchased interposer may translate a separately qualified module interface; the user's illustrative $15–30 adapter price is not a quote, and an interposer cannot rescue incompatible software or turn into another custom CNC controller.

## Recommended evaluation order

| Candidate | Proposed role | What still decides selection |
|---|---|---|
| Raspberry Pi CM4 with at least 2 GB RAM and eMMC | Software/reference route for a CM-family carrier | Current exact-SKU price/availability, local UI memory use, custom SPI driver, loaded latency and thermal qualification |
| Raspberry Pi CM5 with eMMC | Higher-compute option and possible main module if complete economics fit | Added power/cooling and carrier differences, independent SPI/real-time validation, actual workload benefit and fitted cost |
| BTT CB2 | Budget competitor on a closely related footprint | Verified price, every used pin and power/reset function, target PREEMPT_RT build, LinuxCNC/SPI/GPU integration and support burden |
| BTT CB1 | Lower-memory cost experiment | Its priced 1 GB configuration is below the initial 2 GB study target; it must demonstrate the complete graphics/control workload rather than rely on Klipper suitability |

The first three are an evaluation shortlist, not certified-compatible modules. Other dual-connector modules can be added when their exact revision passes the same checks. The separate ROCK 3C and CM3S cost studies remain useful comparators; a preferred footprint alone does not prove better finished economics. [BTT source and price review](../research/BTT_COMPUTE_REVIEW.md)

LinuxCNC publishes a Raspberry Pi 4/5 image and ARM64 packages. This gives the Pi family a documented starting route; it does not qualify our CM carrier, display workload or custom FPGA protocol. LinuxCNC distinguishes real-time machine control from simulation on a normal kernel. [LinuxCNC downloads](https://linuxcnc.org/downloads/)

## Physical fit is only the first check

Raspberry Pi documents cross-use of CM4/CM5 IO boards with reduced functionality. Its transition guide identifies changed USB/MIPI assignments and reset semantics: pin 92 changes from RUN_PG to a power-button input. It also specifies a CM5 module power budget up to 5 V at 2.5 A; peripheral loads are additional. Therefore, even the two official Pi modules need deliberate carrier review. [Compatibility overview](https://www.raspberrypi.com/documentation/computers/compute-module.html), [CM4-to-CM5 transition guide](https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP/Transitioning-from-Compute-Module-4-to-Compute-Module-5)

Treat the user's three connector categories as a visual classification. Connector count, edge-contact count or a shared word such as “CM5” is not an electrical standard. The broad Jetson/SO-DIMM and Radxa/ArmSoM compatibility claims in the supplied table have not been audited here; no carrier decision relies on them.

One specific correction is verified: PINE64's SOEdge uses a **204-pin SO-DIMM** connector, not the 260-pin category in the supplied table. The manufacturer's announcement identifies that connector explicitly. This correction does not make SOEdge a supported carrier option or provide a current price. [PINE64 SOEdge announcement](https://pine64.org/2020/02/03/fosdem-2020-and-hardware-announcements/)

The compute-module connector's pin count does not determine the number of machine terminals. In this architecture the dedicated link carries commands and feedback; FPGA resources, field-interface circuits, power and actual connectors determine machine I/O capacity.

The next design uses an exact module/revision matrix. Each row must resolve:

1. Connector part, position, stack height, mounting and cooling keep-outs.
2. Every power, ground, signal and reserved pin, including power direction, voltage and startup behavior. Unsupported inserted modules cannot be made electrically compatible by a later software check.
3. Module-specific boot, reset, recovery, storage programming and shutdown arrangements. Keep recovery manual/host-owned and the ESP diagnostic-only under the current implementation. Any future ESP-assisted reset requires a separate reviewed authority/circuit change, tied to the correct module and a verified stopped state.
4. Display and touch, Ethernet, USB host/service, and the dedicated FPGA transport with pinmux and kernel-driver ownership.
5. Reproducible OS/kernel/device tree and per-module transport implementation. GPIO numbering or an SPI overlay from a different SoC is not a portable real-time driver.
6. Rated power, inrush, thermal load and independent output inhibition through boot, faults and recovery.

Do not label the socket “any CM4/CM5.” Publish the supported part/revision list and distinguish a factory hardware population from a customer-replaceable upgrade. Use appropriate identification/labels and configuration controls, but establish electrical compatibility before power is applied.

## Proposed common subset for the first carrier

Start by mapping one HDMI display path, USB for touch and supported adapters, Ethernet, storage/programming, a dedicated Linux-to-FPGA SPI path and module-specific service/reset. Retain USB capacity for the user's third-party Modbus-adapter requirement. Study HDMI plus USB touch across the [7/10/12/14/18/21-inch screen tiers](DISPLAY_TIERS.md). Compact DSI assemblies are optional configurations needing exact host/carrier/panel qualification; DSI is not a dependency for every screen. An SPI display must not be assumed to share the dedicated motion transport.

Audit this subset separately for CM4, CM5, CB2 and each supported CB1 revision. Leave repurposed high-speed pins unused unless a deliberately reviewed, default-off routing/protection design handles them. The latest requirement is one motherboard with the supported compute modules replaceable; a separate incompatible carrier revision does not satisfy that promise. If a module cannot use a safe common subset, disclose the limit and resolve the supported list before layout freeze. Software or a DIP setting must never be the sole protection against incompatible pre-boot electrical connections.

The field-I/O FPGA and ESP remain independent of the compute-module brand. Their host protocol is shared, while the target SPI implementation, image, recovery wiring and qualification evidence are specific to each supported module. A compute upgrade preserves compatible saved configuration, but it invalidates system timing qualification and requires a controlled requalification procedure.

**RAM upgrade scope (user, 30 September):** support replacing a qualified compute module with a higher-RAM qualified variant while preserving compatible machine configuration and offline entitlement. The selected CM4/CM5/BTT families have onboard memory; their dual-100-pin interface does not expose the processor memory bus for a motherboard DIMM/SO-DIMM RAM slot. Do not promise socketed RAM expansion on this bay or call NVMe/SD/swap storage extra physical RAM. Optional AI keeps its own separately costed compute/RAM/power. A different memory-socketed computer would be a different compute architecture, not a small connector addition to this frozen design.

Record [SD/eMMC/NVMe boot and offline provisioning](BOOT_STORAGE_AND_PROVISIONING.md) separately from module selection and RAM capacity. Supported storage is module/revision-specific; the supplied 16 GB Optane title is an unqualified discontinued-storage lead, not a selected new-generation memory upgrade.

## Cost gate

Compare **module + mating connectors + carrier circuitry + storage + cooling + power + assembly/test**, at identical quantities and display/I/O scope within each screen tier. Cost each complete display package separately, including its power and mechanical integration. Screen diagonal does not dictate compute: measure actual resolution, graphics/model workload, memory and enclosure thermals before pairing modules with tiers. Cost power and cooling for the actual supported upgrade envelope. Record the user's estimated prices as leads separately from dated, exact-variant offers and supplier quotations. No current evidence establishes a profitable complete $249 bundle; that illustrative price is not fixed for every tier.

The next selection requires a complete pin/power compatibility matrix, a reproducible software build route and a like-for-like fitted cost comparison. Loaded physical timing follows on the bounded engineering prototype before final production layout.

The [new sourced comparison](../research/COMPUTE_DISPLAY_MATRIX.md) holds exact screen candidates constant across CM4/CM5/CB2, preserves six/two versus eight/four separately, and includes 1/10/100/1,000-unit cases. Reference carrier merchandise is separate from our unpriced custom carrier; unavailable modules and unqualified combinations remain identified. This study does not close the complete-cost gate.
