# Drop-in modules: current design boundaries

30 September 2026. Read-only reconciliation for the user's question about CM4/CM5, ESP32 and other drop-in modules. This clarifies the existing adopted service architecture; it does not revise frozen IS-1 or change electrical component selections.

| Function | Planned physical construction | Normal customer service unit |
|---|---|---|
| Linux compute | Qualified CM4/CM5-family module on two 100-pin carrier connectors, mated at the factory | Complete compute carrier/card (CMC), so field service does not handle the fine-pitch module connectors |
| ESP helper | ESP32-S3 WROOM component soldered onto the service card | Complete removable ESP service card (ESC) |
| FPGA motion | FPGA, clock, configuration flash and supervisory circuitry soldered onto the motion card | Complete removable motion card (MC) |
| Machine interfaces | Grouped motor, input, output and process-interface cards behind the fixed wiring base | Qualified whole cards; expansion slots accept their defined motor/encoder modules |

The adopted acceptance target is power-off replacement without soldering, disturbing individual machine wires, losing configuration, repurchasing an existing software entitlement or manually flashing a supplied replacement. These remain requirements to implement and qualify. Exact compute variants are approved independently; matching connector shape does not establish electrical, boot/software or real-time compatibility.

Source authority: `PROJECT_MEMORY.md`, `docs/MODULAR_REPAIR_AND_MEMORY.md`, `docs/COMPUTE_CARRIER_STRATEGY.md`, and frozen IS-1 section 02 in the separate `controller-interface-spec` checkout (CMC contents, ESC contents and removal/replacement sections). The current live CAD covers partial MC placement and a separate watchdog study, not an implemented CMC/ESC/backplane.

**Current ESP source gap:** `hardware/esp_service/bom.csv` still identifies ESP32-S3-WROOM-1-N8, with no assigned footprint. Frozen IS-1 specifies ESP32-S3-WROOM-1U-N8 on ESC with the external antenna connection. That circuit/antenna/card migration remains engineering work; this answer does not silently claim it has been performed. There is no finished drop-in ESC PCB yet. Bare-FPGA/oscillator source footprint assignments also remain open; CAD uses explicitly identified placement-only candidates.

Manufacturer physical references checked for this answer: [Raspberry Pi compute-module documentation](https://www.raspberrypi.com/documentation/computers/compute-module.html) and [Espressif WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf). These describe the respective component/package interfaces; our card topology and qualification status come from the project sources above.
