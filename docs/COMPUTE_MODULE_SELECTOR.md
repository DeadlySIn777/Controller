# Compute-module selector: cold-start profile selection

Reviewed 18 October 2026. [Documentation index](README.md) · [current engineering evidence](../reports/ENGINEERING_STATUS.md). This contract applies to the purchased replaceable compute module on the [IS-2 motherboard](MOTHERBOARD_IS2.md), with all twelve motor interfaces and required I/O retained across qualified swaps.

30 September 2026 design contract, reviewed against later motherboard source work. Circuit/source representation is separate from fitted hardware, implemented cold-start selection and qualified module compatibility; those latter gates remain open. Frozen external IS-1 is unchanged.

The controller should accept qualified Raspberry Pi CM4/CM5 and BTT CB2/CB1 variants in one dual-100-pin mechanical compute bay. Swapping a qualified module should select an already installed host profile rather than require reflashing the FPGA or ESP. Each replacement module still needs its own compatible, prepared bootloader, Linux kernel/device tree, controller application and real-time transport. Changing a profile may require a controlled reboot. Installing support for a previously unsupported module is a separate software release and electrical qualification.

## Physical selector proposal

Use a three-pole DIP selector, or an eight-position coded rotary switch if the service/usability comparison favors it. The table follows the user's requested code assignments, not a selected connector/IC or GPIO allocation. Code bits are listed **S3 S2 S1**; ON means logical 1 after input conditioning. Default all-OFF selects AUTO; until a safe qualified identification/bootstrap path succeeds, it stays inhibited/service-only.

| Code | Selection | Release state |
|---|---|---|
| 000 | AUTO | Requested automatic selection; no universal pre-power hardware ID is established, so unqualified detection remains inhibited/service-only |
| 001 | Raspberry Pi CM4 | Candidate; exact SKU/revision and carrier still to qualify |
| 010 | Raspberry Pi CM5 | Candidate; exact SKU/revision and carrier still to qualify |
| 011 | BTT CB1 | Exact SD/eMMC revision must match its profile; eMMC recovery/pin audit remains open |
| 100 | BTT CB2 | Candidate; exact SKU/revision and carrier still to qualify |
| 101 | Future | Reserved; disabled until independently qualified |
| 110 | Reserved | Disabled |
| 111 | Reserved | Disabled |

Locate and label the selector in the service region, away from field-voltage conductors. Its inputs belong to the separately powered service domain; do not strap repurposed compute-module connector contacts or let the Linux module sample its own potentially incompatible pins to decide wiring. Specify actual pull networks, input protection, debounce, power sequencing, readback and switch footprint during carrier integration. A coded rotary alternative must have a defined valid-code/stability check too.

For replacement, power off the machine/controller, install the labeled supported module, set the labeled selector and power on. The startup controller reads a stable code before enabling the compute branch or optional module-specific paths. Changes while operating must never switch USB/reset/SPI routing live; latch a service fault, revoke normal machining authority through the existing fault policy, and require a deliberate stopped power-cycle/service sequence. The machine's defined fault response still governs gravity, workholding and cooling.

The ESP/service implementation may report selection and request a qualified compute startup sequence; it cannot grant FPGA or field-output permission. Existing independent rail/reset/watchdog/permission hardware must remain fail-closed during a missing service module, invalid code, startup or recovery. The current ESP firmware is diagnostic-only and does not implement this sequencing.

The latest user explicitly requests automatic hardware identification with a manual override. AUTO must therefore be designed around a proven independent ID path or a **universally safe common bootstrap** with conflicting paths still off until identification. No such path is implemented. If a given module cannot be identified safely, AUTO must say that manual selection is required and keep unqualified interfaces disabled; do not guess from floating GPIOs, blindly probe incompatible contacts, fabricate an ID resistor or force a routing profile. Manual override chooses among qualified compatible profiles; it never overrides an identity/electrical mismatch or machine limits.

## Carrier rules the switch cannot replace

One switch does not make different pinouts interchangeable. Keep the common electrical subset safe for **every advertised inserted module before Linux runs**. Leave conflicting functions disconnected or use a specifically reviewed, default-off routing/protection circuit. A wrong selector setting must not create a damaging signal connection. If a path cannot meet that requirement, exclude it from the common bay or restrict the supported list; do not depend on a late software check.

Raspberry Pi documents CM4/CM5 cross-use with reduced functionality and module-specific boot/device-tree arrangements. BTT publishes different SoC pin maps and its own host images. [Raspberry Pi compute documentation](https://www.raspberrypi.com/documentation/computers/compute-module.html), [BTT CB1 documentation](https://github.com/bigtreetech/CB1), [BTT CB2 documentation](https://github.com/bigtreetech/docs/blob/master/docs/CB2.md).

The current primary-source pin audit identifies these concrete review points:

- Pins 38/40/44 are candidate common SPI clock/MISO/MOSI. Pins 54/47 are candidate common **GPIO** chip selects, requiring the correct per-SoC driver and device tree. Native Pi CE0 at pin 39 is unconnected on audited CB1 SD. The stock CB2 overlay's 1 MHz setting does not qualify the required 5 MHz CNC3 exchange.
- Audited CB1 SD uses pins 140/142 for USB recovery; CM5 assigns those positions to USB3 TX. Pins 103/105 are USB host on that CB1 SD revision but USB OTG on Pi/CB2. USB and reset/boot routing must be reconciled electrically, not just assigned a profile name.
- No universal, documented pre-power module-ID mechanism was established on the common connector. The selector is the operator's declaration, not proof of what was inserted. Linux model/revision readback is a later cross-check; it cannot undo unsafe pre-boot wiring.
- CB1 SD and eMMC hardware revisions must not inherit each other's qualified profile. Published power, thermal, storage and real-time behavior also need separate qualification.

The exact pinned sources and complete contact tables are recorded in the dated [compute-bay pin audit](../reports/board-completion-20260930/COMPUTE_BAY_PIN_AUDIT.md). Later [motherboard finishing evidence](../reports/board-finish-20261017/README.md) includes source/native board checks, while actual startup, wrong-selection behavior and target transport qualification remain open. Neither a pin audit nor native board geometry is a booted target or physical transport measurement.

## Preinstalled profile and service flow

1. Hardware starts with machining permission inhibited and conflicting optional paths disconnected.
2. Service startup samples and validates the selector, exact supported carrier population and allowed module envelope. Invalid/reserved/unqualified combinations stay in service state.
3. Power/reset and optional routing use the reviewed cold-start sequence for that profile. Startup timeout or rail faults remain faults.
4. The prepared Linux image loads its matching device tree and real-time CNC transport. The controller compares detected SoC/model/revision with the selector and records the exact image/profile/driver revisions. Missing or contradictory identity blocks commissioning.
5. Host/FPGA/service protocol and capability checks, self-test and deliberate recovery are required before normal machine commissioning. A successful boot alone never enables motion or restores verified position.
6. Compatible saved machine configuration and offline software entitlement survive legitimate module replacement. Target timing, graphics/power/thermal checks and affected machine verification must pass again; a faster processor does not inherit another module's qualification.

Expose selector code, selected profile, detected module, image/driver revisions, qualification state and any mismatch through the existing common configuration/diagnostic service. CLI and UI consume that same structured contract. The physical selection is read-only to software; preview/diff may describe a proposed module change, but an apply command cannot pretend to move a switch or override a mismatch. No separate hidden setup API or invented successful-boot display is introduced by this document.

## Closure required before layout freeze

Select the exact switch and service input circuitry; allocate actual service pins; complete the shared module contact/power/boot matrix; qualify default-off optional paths and wrong-selection behavior; build the exact per-module host images/transports; implement same-contract readback; and test startup, mid-run selection changes, service-controller failure, missing/wrong module, recovery and replacement on physical prototypes. Add their actual fitted costs to the complete controller BOM. None of these gates is closed by a DIP switch alone.
