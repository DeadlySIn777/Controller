# Physical fuses and electronic protection

Reviewed 18 October 2026. [Documentation index](README.md) · [current engineering evidence](../reports/ENGINEERING_STATUS.md). Protection is integrated on the [IS-2 motherboard](MOTHERBOARD_IS2.md); purchased modules and the whole board have separate powered-off service procedures.

28 September 2026. Engineering recommendation answering the user's fuse question: **use both, with coordinated roles**. This is a circuit requirement, not a qualified protection design or a final fuse rating.

Historical partial work: [two core/field entry circuits](../reports/POWER_ENTRY.md) and [two encoder-power branches](../reports/ENCODER_POWER.md) have editable KiCad source, real netlist/ERC exports and scoped checks. Their TPS26630RGER/blocking-FET and 19–30 V / 3 A proposals retain those exact study scopes; they are not complete motherboard ratings. IS-2 requires protected CORE, FIELD_A and FIELD_B entries plus all retained branch protection. The [17 October continuation](../reports/board-finish-20261017/README.md) has native geometry/source checks but unresolved full simultaneous current, IR drop, returns, assembly and physical qualification. Neither clean ordinary DRC nor a connected net approves fuse coordination or a current rating.

| Location | Proposed protection | Purpose and fault behavior |
|---|---|---|
| Controller low-voltage power entry | Serviceable, labeled, DC-rated physical fuse; reverse-polarity/transient protection; electronic input limiting as needed | Protect the entry wiring and provide a backup interruption path. A blown fuse requires fault diagnosis and replacement with the specified type. |
| Compute and display branches | eFuse or suitable protected converter/load switch | Limit inrush and isolate branch overloads; report fault and power-good where justified. Recovery boots the controller disarmed. |
| ESP and accessory supervision branch | Separately regulated/protected ESP supply with reviewed reset/brownout, decoupling and direct supervisor inputs | Budget radio transients and sensor/interface load; independent watchdog/default circuitry must handle ESP freeze/power loss; shared upstream failure remains possible |
| Separate machine field-power entry | Its own coordinated physical fuse/protection sized for its wiring and source | Field current must not pass through the compute power budget or defeat isolation domains. |
| Field output banks/channels | Existing protected high-side drivers, with bank protection as required | Use their built-in current/thermal protection before adding redundant per-channel devices. Machine-affecting faults require deliberate recovery; no repeated automatic re-energizing. |
| Optional AI accessory | Accessory-specific protected supply or separate power adapter | Avoid adding an unselected AI module's peak load to every base unit. |

Physical fuses and eFuses do different jobs. A fuse must be selected against DC voltage, prospective fault current/interrupting capacity, time-current behavior, inrush and ambient temperature. [Littelfuse's selection guide](https://www.littelfuse.com/assetdocs/fuseology-selection-guide?assetguid=d812dff2-1c47-4dc3-bce7-07a4001ddc32) describes those factors. The upstream supply's current limiting matters: a supply that folds back below the physical fuse's opening current may leave that fuse intact. Validate the whole source/wire/fuse/electronic-protection combination.

The [TI TPS2663 family](https://www.ti.com/product/TPS2663) is one candidate for a nominal-24-V branch: its operating range is 4.5–60 V, with adjustable 0.6–6 A current limit, inrush control, current/fault reporting and selectable latch-off/auto-retry behavior. Reverse-polarity protection requires the datasheet's external FET arrangement. The exact variant, supporting parts, thresholds, dissipation and total cost remain open; a chip family headline is not a completed branch circuit.

## Control and diagnostics

- Set electrical maximums in hardware and the board capability record. A CLI or AI may select only validated settings within those limits; it cannot raise a trace, connector or semiconductor rating.
- Protection acts autonomously; a hung ESP or Linux service must not prevent a short-circuit trip.
- Where supported, report the named branch, trip reason, measured current/voltage and timestamp through the same UI/CLI schema. Distinguish an inferred cause from a measured event.
- Carry fault status across an isolation boundary using an appropriate isolated interface. Reading an analog current-monitor pin directly from a different ground domain can defeat the intended isolation.
- Acknowledge a trip separately from restarting the machine. Clearing a power fault does not establish valid position or resume permission.
- Overcurrent protection is separate from machine E-stop/STO and brake sequencing. Removing electrical power is not always a controlled mechanical stop.

## Calculations and tests before selection

The [machine-memory and repair system](MODULAR_REPAIR_AND_MEMORY.md) retains a protected replaceable settings provision with committed generations, mirror/export and interrupted-write recovery. Define write protection, ESD, reversed/wrong insertion prevention, brownout write behavior and fault isolation so a damaged accessory or settings bus cannot hold the whole controller indefinitely. A shared low-voltage rail alone does not establish independence from field faults. Replacement is powered off until separately qualified; software recognition does not make a connector hot-pluggable. A failed soldered power region requires motherboard repair/replacement, followed by board-wide supply, inhibit, output-default and affected calibration checks. It is not a power-card swap. Exact complete protection qualification and cost remain open.

Define continuous/peak load and duration for every branch; input-voltage range; cable and connector ratings; converter efficiency/inrush; output capacitance; inductive energy/clamp path; device SOA and thermal limits; fuse time-current and I²t coordination; current-limit tolerance; and permitted voltage during transients. Confirm normal startup survives while fault cases trip predictably. Include shorted load, reversed input, supply foldback, shorted protection switch and supply restore cases in the later bench plan.

Fuse holders, eFuse ICs, external FETs, TVS devices, sense/filter parts and fault telemetry belong in the BOM. Their unresolved cost is already part of the power/protection gaps in the cost model; they are not assumed free.

The [accessory-automation requirement](ESP_ACCESSORY_AUTOMATION.md) adds possible ESP-owned drivers and sensor circuits. Allocate their load to an identified supply; they are not powered by an assumed spare GPIO budget. Define which cooling or other equipment must continue after each fault, and provide a qualified hardware path where a frozen or unpowered processor cannot guarantee it. [Whole-unit qualification](INDUSTRIAL_QUALIFICATION.md) includes the finished enclosure, display, power supply and connected cables.
