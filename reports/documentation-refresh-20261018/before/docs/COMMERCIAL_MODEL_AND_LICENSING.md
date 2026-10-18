# Commercial model, licensing and compatibility

29 September 2026. **Commercial direction:** sell the controller, paid software licences, expansion modules and complete tested kits. Kits sell convenience, integration and support. Expansion modules sell additional capability. Ordinary peripherals remain replaceable, sourceable products; a customer must not have to buy a routine drive, display, relay, RS-485 adapter, VFD, cable or power accessory from us merely to use a supported interface.

This is a product and release requirement, not evidence that the current prototype is ready for sale. The [engineering status](../reports/ENGINEERING_STATUS.md), component reports and release checklist remain the authorities for implemented behaviour and manufacturing readiness.

## Product forms

| Offer | What the customer receives | Commercial boundary |
|---|---|---|
| Controller | Controller electronics, the selected compute/motion/I/O population, required base firmware and the paid local application licence where that configuration includes it | Exact I/O, power, screen, compute and software scope is named for the purchased revision. A controller is not advertised as an arbitrary-voltage or universal machine interface. |
| Software licence | A paid licence for the commercial application, service and included product features defined by the selected edition | Works offline after a legitimate activation or licence transfer. Licensing cannot block stopping, hardware inhibition, diagnostics, configuration recovery or safe rollback. |
| Expansion module | A qualified hardware module, its compatible firmware/configuration, capability record and installation/retest instructions | Adds a named capability, channel group or process interface. It has its own electrical, timing, power, calibration and compatibility limits. An expansion is not silently included in the base controller. |
| Complete tested kit | Controller plus a defined screen/compute/power/enclosure/harness/peripheral combination that has passed the published kit tests | The price covers integration, tested wiring, provisioning, documentation and support. The kit is a convenience choice; supported ordinary components may be sourced separately. |
| Service and support | Installation help, updates, replacement guidance, compatibility records and paid support options | Support scope and duration are stated for each offer. Support does not turn an untested substitute into a qualified component. |

The screen catalogue remains tiered independently of machine I/O: 7-, 10-, 12-, 14-, 18- and 21-inch classes and further qualified sizes use the same service contract but have separate display, compute, power, mounting, enclosure, testing and pricing records. A complete kit can include one of those displays while the controller and expansion capability remain a separate choice. See [display tiers](DISPLAY_TIERS.md) and the [compute carrier strategy](COMPUTE_CARRIER_STRATEGY.md).

## Peripheral freedom and published compatibility

Use proven off-the-shelf peripheral components where they meet the interface contract. A kit may include a preferred display, adapter, drive, VFD, relay, power supply, cable or enclosure because it has been tested and is easier to install. That inclusion does not make the item proprietary or require the customer to purchase it from us.

Publish a compatibility record for every supported substitution. Each record should identify:

- exact manufacturer, model, hardware revision and relevant firmware/manual revision;
- electrical domain, voltage/current/frequency limits, connector and pinout, grounding/isolation, cable and termination requirements;
- controller, compute, firmware, gateware, application and profile versions used for the test;
- permitted operations, measured limits, startup/default state, communication loss and replacement behaviour;
- test date, test method, evidence identifier, known restrictions and whether the result is qualified, compatible-by-review or untested.

The service and CLI show the same compatibility records as the touchscreen. They distinguish an exact tested item from a generic profile or a detected USB/Bluetooth/Wi-Fi identity. A connector shape, marketplace title, protocol name or successful read does not establish compatibility. Customers may purchase a listed peripheral elsewhere and use the published wiring/profile data, subject to the same commissioning and support boundaries. A customer-selected item outside the list enters a clearly marked user-qualified path; it does not inherit our tested claim.

This policy applies to the ordinary third-party devices already planned for the controller, including USB-to-RS-485 adapters, Modbus RTU/TCP equipment and compatible serial VFDs. Modbus remains outside precision motion timing. See [third-party Modbus](THIRD_PARTY_MODBUS.md).

## Commercial software and offline operation

Our original application, UI, common configuration service and product integration are commercial software. Project documents must describe them as paid software or as an included licensed component of a purchased controller/kit; they must not describe them as freeware or promise an open-source release.

The product still exposes the documented interfaces needed for the promised experience: versioned configuration schemas, structured CLI/service calls, validation, preview/diff, reversible apply/rollback, capability records, wiring guidance and supported extension points. Editable configuration, hardware design files and published interface specifications make supported customization possible. They do not, by themselves, grant rights to redistribute the commercial application or imply that all of its source is open.

The licence design must support the following before a paid release:

1. Normal operation, setup, diagnostics, updates and recovery work without an internet connection or cloud account after the entitlement is legitimately installed.
2. A licence is associated with the licensed controller/machine entitlement and product edition, with a local signed record or equivalent offline-verifiable record. It must not be tied only to a replaceable compute, FPGA or I/O module serial number.
3. Replacing a designated failed module under the supported service procedure preserves the valid licence. The customer does not buy the same software again because a compute, motion, I/O or service module was replaced. The replacement still must pass identity, firmware, calibration, configuration and affected-function checks.
4. A new capability supplied by an expansion module may have its own separately purchased entitlement when the offer says so. That is an upgrade decision, not a replacement fee for an already licensed capability. A licensed module can be replaced by an approved same-capability spare without repurchase.
5. Licence expiry, corruption, clock errors, network loss or an unresponsive optional AI computer cannot suppress hardware fault handling, stopping/inhibit behavior, read-only diagnostics, offline configuration recovery or the safe return to a known disarmed state.
6. The UI, CLI and assistant receive the same entitlement and capability result. A hidden GUI-only check must not make offline service or automation impossible.

The exact activation, transfer, grace, support and edition rules remain implementation work. They must be specified, tested and documented before advertising offline replacement. Do not use a cloud callback as the only source of entitlement or as the only recovery path.

## Third-party software and licence boundary

Before distribution, maintain a versioned dependency inventory and software bill of materials for the Linux image, LinuxCNC integration, kernel/userspace packages, FPGA tools/runtime pieces, ESP-IDF components, drivers, fonts, UI libraries, CAD/import libraries, codecs, model files and optional AI software. Record the exact version, origin, licence, notices, source-offer obligations, modification status and distribution location for each item.

LinuxCNC and other copyleft components remain governed by their applicable licences. In particular, a release using LinuxCNC must preserve the applicable GPL-2.0 notices and source or corresponding-offer obligations. The commercial application boundary, linking/IPC arrangement, bundled scripts, modified components and distribution package require a deliberate licence review; this document does not make a legal conclusion about any particular boundary. Do not remove notices, relabel third-party code as our proprietary software or use a commercial licence to override a third-party obligation.

The release package should include a local licence/notice view and an offline export of the dependency record. Where a third-party licence requires source, offer text, attribution or installation information, provide it in the required form for the distributed version. Optional AI models and accelerator runtimes need their own model/data/software licence review; an AI add-on cannot silently change the licence of the base controller application.

## Replacement, expansion and kit acceptance gates

The commercial promise is only ready when the following are demonstrated on the defined release configuration:

- a customer can run the licensed application offline through a power cycle and controlled network loss;
- a supported module can be exchanged power-off while the machine wiring and protected machine configuration remain intact, and the licence survives without repurchase;
- an incompatible or counterfeit-identity module is rejected before output permission, and a compatible spare restores only the affected capability after the required checks;
- an ordinary supported peripheral bought outside our sales channel produces the same validated profile, wiring guidance and fault behaviour as the corresponding kit item;
- the compatibility table links each claim to an exact test record, with untested substitutions clearly labelled;
- the controller, expansion module and complete kit each have a separate fitted cost, replacement price, software entitlement and support scope;
- the dependency inventory, notices, source/offers and commercial application boundary have been reviewed for the actual release artifacts.

The current disconnected configuration and replacement demonstrations are useful contract evidence, but they do not yet prove a physical cartridge, offline licensing system, live module discovery, ordinary peripheral qualification or a sale-ready kit. Keep those claims separate in [engineering status](../reports/ENGINEERING_STATUS.md) and the [PCBWay release checklist](../manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md).

