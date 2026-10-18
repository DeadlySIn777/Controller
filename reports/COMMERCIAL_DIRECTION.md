# Commercial direction and licensing status

29 September 2026. This report records the user's commercial clarification and its engineering implications. It is a requirements/status record, not a product release approval or legal opinion.

## Decided offer structure

- Sell the controller as a defined hardware/software configuration.
- Sell paid licences for the original commercial application and product integration. The application is not described as freeware, and the project makes no promise of an open-source release.
- Sell expansion modules that add named, qualified capability such as additional motion/I/O or process interfaces.
- Sell complete tested kits that bundle a defined screen, compute, power, enclosure, harnesses and selected peripherals. The kit price pays for integration, provisioning, test, documentation and support.
- Allow customers to source ordinary supported peripherals from other retailers. A kit's preferred adapter, display, drive, VFD, relay, power supply or cable does not become a proprietary purchase requirement.

The [commercial model and licensing policy](../docs/COMMERCIAL_MODEL_AND_LICENSING.md) is the detailed contract. Screen classes, machine I/O and expansion capability remain separately costed; a complete kit must identify its exact tested population.

## Compatibility publication requirement

For each supported peripheral or kit substitution, publish the exact manufacturer/model/revision, firmware/manual revision, electrical and wiring limits, grounding/isolation and cable requirements, controller/software/profile versions, tested operations, fault/reconnect behavior, evidence identifier and support status. Mark generic or customer-authored profiles as unqualified. A detected connector, USB identity, protocol name or successful read does not establish compatibility.

This requirement applies to ordinary USB-to-RS-485 adapters, Modbus RTU/TCP devices, serial VFDs, displays, drives, relays and other peripherals. Customers who buy a listed part elsewhere follow the same profile and commissioning path as a kit customer. Unlisted parts remain outside the published compatibility claim until separately qualified.

## Offline licence and module replacement requirement

The commercial application licence must be locally verifiable after legitimate installation and continue to work without an internet connection. Its entitlement must be associated with the licensed controller/machine and edition, rather than only with a replaceable compute, motion or I/O module serial number. A supported same-capability replacement must preserve the existing entitlement without repurchase. A new expansion capability may carry a separate stated entitlement; exchanging a failed module for an approved spare is not a new purchase.

Licensing must never block machine inhibition/stopping, fault reporting, read-only diagnostics, configuration backup/restore, safe rollback or recovery to a disarmed state. The touchscreen, CLI and assistant must use the same entitlement/capability result, including offline service.

## Third-party boundary

The release needs a versioned dependency inventory and software bill of materials covering the Linux image, LinuxCNC integration, kernel/userspace packages, ESP-IDF components, FPGA/runtime tools, UI/CAD libraries, fonts/assets, codecs and optional AI software/models. Preserve each applicable notice, attribution, source or corresponding-offer obligation and modification record. LinuxCNC's applicable GPL-2.0 obligations are an explicit example requiring release review.

The boundary between copyleft components and the commercial application must be reviewed against the actual build and distribution arrangement. This report does not make a legal determination. A commercial licence cannot override a third-party licence, and the product's documented configuration/CLI and editable engineering inputs do not imply that the commercial application source is being released.

## Status and release gates

The requirement is now carried into the project memory, build plan, roadmap, CLI contract, modular-repair plan, Modbus plan and industrial-qualification plan. The current disconnected configuration/replacement demonstrations show useful validation and recovery contracts, but they do not implement or qualify offline commercial licensing, physical module discovery, customer-supplied peripheral operation or complete tested kits.

Before a paid release, demonstrate and record:

1. offline licence installation, restart, update, recovery and deliberate network loss;
2. supported module exchange with retained machine wiring/configuration and licence continuity;
3. rejection of incompatible module identities before output permission;
4. an ordinary listed peripheral purchased outside our sales channel following the same validated profile and commissioning flow as the kit item;
5. compatibility records linked to exact tests and clearly marked untested variants;
6. separate controller, expansion, kit, replacement and software-support costs; and
7. licence/notice/source-offer review for the actual shipped artifacts.

Until those gates pass, the project remains an engineering prototype and partial design. No current document should describe the commercial offer as manufactured, fully qualified or ready for PCBWay release.

