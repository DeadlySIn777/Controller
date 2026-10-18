# Reliability, qualification and first commercial release

28 September 2026, updated 29 September 2026. **Industrial reliability is the product target, not a current certification or tested whole-unit rating.** The user's [latest note](../research/user-notes/2026-09-28-esp-industrial-direction.txt) prioritizes dependable control, verified supporting equipment, understandable faults and serviceability. The commercial direction is to sell the controller, paid offline software licences, capability-expanding modules and complete tested kits, while allowing customers to source ordinary peripherals elsewhere from the published compatibility list. Software prototypes and partial circuits do not establish sale readiness or market demand. See the [commercial model and licensing policy](COMMERCIAL_MODEL_AND_LICENSING.md).

## Specify the complete installed product

Define the intended machine class, supply/field wiring, accessories, enclosure location, contamination, ambient temperature/humidity, cable lengths/shields, mounting/vibration, operator environment and target markets. Publish only the limits qualified for the complete offered configuration. Each screen tier, compute/cooling option and interface module has a controlled configuration record; assess changes for renewed testing.

Espressif specifies the ESP32-S3-WROOM-1-N8 at −40 to +85 °C ambient immediately around that module. That is not the assembled controller's temperature range; display, storage, power parts, thermal rise and enclosure conditions remain limiting factors. Other module suffixes can have different ranges. [Module datasheet, variant table and ambient note](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)

## Qualification record required before claims

| Area | Design inputs and later evidence |
|---|---|
| Power | Operating range, continuous/peak/inrush loads, reverse-polarity, transient, short/overload, brownout and restore behavior; coordinate physical fuses and electronic protection with actual supplies/cables |
| Field interfaces | Published voltage/current/frequency ranges, isolation/grounding boundaries, protection energy and faults; outputs inactive or in their explicitly reviewed state through boot/reset/reconfiguration |
| EMC | Finished-assembly ESD, fast-transient, applicable surge, conducted/radiated immunity and emissions plan; include representative cables, active radios, display, power supply and worst-case machine activity |
| Thermal/environment | Actual internal hot spots and component derating; ambient operating/storage conditions, condensation/contamination limits, ingress and cooling maintenance; representative screen/compute/enclosure variants |
| Mechanics | Connector retention, replaceable terminals, mounting strain, shielding/bonding, vibration/shock requirements and cable termination |
| Software/control | Bounded queues/resources, rejected stale/configuration commands, explicit fault deadlines, deliberate restart, rollback/recovery, logged version/configuration identity and loaded operation |
| Manufacturing | Exact approved BOM/alternates, traceable board/firmware revisions and serials, programming verification, calibrated test equipment, per-unit functional results and rework control |
| Service | Replaceable modules/terminals, compatible recovery images, exportable event history, spare-part and support policy, documented repair/retest requirements |

A qualification laboratory and the engineering compliance review must identify the applicable standards, editions, ports, test levels and acceptance criteria for the declared product/markets. No standard or test level is selected solely because another industrial controller publishes it. A successful development test beside one VFD remains useful development evidence rather than full EMC qualification.

The [power-protection design](POWER_PROTECTION.md) and [ESP accessory contract](ESP_ACCESSORY_AUTOMATION.md) feed this matrix. Protecting, testing and supporting the product are complete-package cost requirements, not optional omissions to meet a headline price.

## Enclosure direction

Carry the machined HDPE enclosure described in the supplied note as a candidate to engineer and cost. Specify the actual material/grade, wall/mount geometry, temperature and fire behavior, coolant/cleaner compatibility, strain relief, shielding strategy and accessible metal bonding. A metal backplate alone does not establish EMC performance. Keep RF antenna placement separate from shield termination and test the final installed arrangement. Different screen tiers may need different bezels or enclosure sizes even with one controller core.

Retain accessible physical emergency-stop/interlock connections appropriate to the machine. Industrial durability/reliability and safety-rated control are distinct claims. ISO 13849-1 addresses design of safety-related control-system parts; citing it does not qualify our board or turn an ESP32 into a safety PLC. The machine's required safety functions, architecture and validation need their own engineering assessment. [ISO 13849-1:2023 scope](https://www.iso.org/standard/73481.html)

Define a fault-response matrix per machine. A loss of drive permission may leave a vertical axis unsupported; cutting all power may stop required cooling or release workholding. Establish controlled-stop feasibility, braking/support, pressure retention and safe isolation from the actual mechanisms and power paths. Do not claim a software request guarantees the physical result.

## Factory package and pilot

The [modular repair/memory requirement](MODULAR_REPAIR_AND_MEMORY.md) adds factory-programmed replacement images, module identity and calibration records, connector/keying inspection and recovery-package compatibility to the test package. Before advertising replacement without manual programming, demonstrate removal/reinstallation with individual conductors retained, offline settings recovery and licence continuity after compute loss, wrong-module rejection and affected verification. Test both interrupted record writes and cartridge/main-storage disagreement; require explicit stale-copy/conflict diagnostics. Measure connector life and retention against the intended service cycle, and test cartridge short/power/bus faults on the finished assembly. Software file tests do not establish EEPROM brownout, physical write protection or connector behavior.

PCBWay turnkey remains the board-manufacturing route after the design is complete. The release package needs exact source/fabrication/BOM/placement files, programming images, fixtures and numeric pass/fail procedures. Specify who performs final screen/enclosure assembly, calibration, full functional testing and recording. A board assembly quotation alone does not cover the finished appliance.

Before a paid production release, qualify one defined machine class and a short explicit list of drives, VFDs and accessories. The proposed five-to-ten-unit pilot is a later planning quantity, not an order authorization. Pilot units need controlled revisions, installation/support instructions, incident tracking and known boundaries.

Record installation time, wiring/setup errors, failed or interrupted jobs with operating-hour denominators, unexplained faults, recovery time, support hours and replacement causes. Collect willingness-to-pay and usability feedback for demonstrated behavior, with consent for any telemetry or machine/job data. Set success thresholds before the pilot; the user's shop experience is an input, not proof of wider demand.

Compare selling economics against clearly defined complete installations. Affordability remains a goal; the historical Mesa-price included-screen ceiling is superseded by the preliminary US$400 controller-assembly reference, with complete screen/PSU/enclosure/harness/help kits separately priced. Cost every offered screen/compute/I/O package, paid software edition, expansion module, replacement licence policy, warranty/support, yield/rework, fixtures, qualification and spares transparently. Publish tested compatibility so customers can source ordinary peripherals independently; kit pricing covers integration and support rather than a proprietary lock-in. Do not use assumed competitors' current prices as evidence without a dated exact-kit source. The exact latest numeric acceptance targets are registered in [current acceptance gates](CURRENT_ACCEPTANCE_GATES.md).

## Next concrete work

Continue the LinuxCNC–CNC1–RTL connection, disconnected common configuration service and compute/display cost matrix. Then add qualified ESP service state machines and sensor/driver hardware, close power/protection and full board design, and execute bounded bench/machine tests. Each result advances a named requirement; none alone declares the controller industrial-grade or ready for sale.
