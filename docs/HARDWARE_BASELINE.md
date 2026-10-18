# Historical hardware baseline and current implementation direction

Reviewed 18 October 2026. [Documentation index](README.md) · [current engineering evidence](../reports/ENGINEERING_STATUS.md).

The current implementation direction is [one active IS-2 motherboard](MOTHERBOARD_IS2.md), with a soldered FPGA, all twelve differential STEP/DIR interfaces and individual enables/alarms, four ABZ, 24 general DI, 16 smart general DO and the other retained process/analog/comms/protection interfaces. Purchased compute, ESP and storage/settings modules remain replaceable. The [CM4/CM5-style compute bay](COMPUTE_CARRIER_STRATEGY.md) includes separately qualified CM4/CM5/CB1/CB2 profiles; exact production variants and target qualification remain open. The memory study begins at **2 GB RAM with eMMC** and justifies increases by measurement. Screen size and licensing do not remove fitted motor channels or required I/O.

**Cost update:** the user subsequently made sale price a deciding requirement. The x86/Mesa stack below remains a development reference. CM5 became one measured-cost feasibility candidate with a custom FPGA/I/O circuit and ESP helper; the bundled-display constraint later reopened the compute selection. Previous 8/16 GB provisions are not production requirements.

## Historical 28 September engineering reference stack

| Layer | Historical study choice | Why it was considered |
|---|---|---|
| Embedded computer | x86-64 industrial SBC/compute module; provisionally 16 GB RAM, SSD, two independent native/PCIe wired Ethernet interfaces | Run PREEMPT_RT LinuxCNC, local jobs and machine services; host the existing browser UI and model-processing services |
| Motion endpoint | Supported Mesa Ethernet FPGA reference; 7I95T is the six-step/dir, six-encoder reference to evaluate | Known LinuxCNC interface while proving the product workflow and machine features |
| Helper | ESP32-S3-WROOM module; external-antenna variant considered for metal enclosure | Independent provisioning, diagnostics, panel functions and stopped recovery |
| Electrical interfaces | Replaceable isolated modules with stated ratings, plus appropriate external drives/relays/contactors | Accommodate different machine voltages and signal types without exposing logic pins to them |
| Power/control integrity | Designed low-voltage rails, reset/output-inhibit sequencing, independent machine stop circuit and machine-specific brakes/STO | Defined startup and failure behavior; an ESP watchdog alone is not a complete machine protection design |

16 GB and SSD capacity are provisional development provisions, not measured minimums. Exact x86 board, BIOS, NIC and kernel must be qualified together. An Intel/AMD product name alone cannot establish acceptable real-time latency. CAD conversion, networking, storage and thermal load belong in that qualification.

LinuxCNC supplies current x86-64 and ARM64 packages and Raspberry Pi 4/5 images. Its PREEMPT_RT/uspace architecture is the proposed route; a kernel-space RTAI installation is not the route for Mesa Ethernet. [Official downloads](https://linuxcnc.org/downloads/), [latency guidance](https://linuxcnc.org/docs/html/install/latency-test.html)

Mesa documents six step/direction channels, six high-speed encoder channels, 24 isolated inputs, six isolated outputs and expansion on the 7I95T. These are finite resources: six axis-feedback encoders plus a spindle encoder would require another encoder resource. Analog servo commands or EtherCAT drives need their corresponding interface architecture; six pulse channels are not universal drive compatibility. [7I95T manual](https://www.mesanet.com/pdf/parallel/7i95tman.pdf)

The ESP32-S3 module supplies Wi-Fi and Bluetooth LE. In this design it runs service firmware; putting FluidNC on it would create a separate CNC engine requiring an explicit stopped-mode ownership design. It is not the main CAD-file gateway and does not take over moving axes. [Espressif module documentation](https://www.espressif.com/en/module/esp32-s3-wroom-1-en)

## Compact compute candidate retained for qualification

**Compute Module 5 with eMMC** is one shortlisted compact alternative to the x86 compute module for a custom carrier (the earlier 8 GB RAM / 32/64 GB eMMC provision is superseded; the current memory study starts at 2 GB, see [BUILD_PLAN.md](BUILD_PLAN.md)). It has a quad-core Cortex-A76, onboard Ethernet PHY and one PCIe Gen 2 lane; wireless variants are available. This offers a documented carrier-design route without designing a CPU/DDR motherboard. [CM5 specifications](https://www.raspberrypi.com/products/compute-module-5/), [datasheet](https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf)

A supported Pi 5 image does not qualify a particular CM5 carrier or its loaded latency. Compare qualified compute-bay candidates using the same model-import corpus, LinuxCNC profiles, storage activity and fault tests. The x86/Mesa study remains a development comparator; it does not override the adopted CM-family motherboard bay or authorize a different production architecture. A failed candidate requires an explicit qualification finding and supported-module decision.

## Historical x86/Mesa connection study

- The local computer has a dedicated direct wired connection to the Mesa reference endpoint. Ordinary browser/file traffic uses the other interface or a separately supported wireless interface.
- LinuxCNC's Mesa Ethernet driver excludes wireless and USB NICs for its real-time link. Those exclusions do not apply to a laptop's browser connection. [hm2_eth](https://linuxcnc.org/docs/2.9/html/man/man9/hm2_eth.9.html)
- USB-C is a connector requirement to engineer, not a protocol. A laptop-to-controller USB networking function needs actual device-mode hardware/software. An ordinary x86 USB host port does not provide it. A laptop USB-C Ethernet adapter is a simpler service-network option.
- For CM5, explicitly allocate the Ethernet PHY, PCIe lane and USB resources. Reserve native Ethernet for the timing link; choose the additional service-network implementation deliberately. Do not allocate the sole PCIe lane independently to multiple devices without a switch/resource design.
- Supply the main interface directly from the Linux computer. ESP diagnostics can remain a small independent interface when the main application fails; retaining power through a total supply failure needs an additional power design.

## Current custom-hardware evidence and remaining gates

The custom motherboard and CNC3 source/driver/RTL work already exist as incomplete engineering inputs. The older Mesa endpoint remains a comparison reference. It is no longer necessary to reopen the custom-FPGA architecture decision; complete its integrated circuits, routing, physical wrapper, target transport and qualification while preserving current source, machine configuration and electrical limits.

The present engineering target is Efinix T20F256/I4. The [17 October continuation](../reports/board-finish-20261017/README.md) records real vendor checks of 135 assigned pins/seven source-defined 3.3 V banks and corrected canonical disconnected SIM2 mapping at 15,805 LUT4 + 2,107 ADD (17,912 total). That core screen retains twelve generators, four encoders and the original event capacity; it does not establish complete physical-wrapper fit, routed timing or hardware qualification. CNC3 is a custom contract; HostMot2/litehm2 references do not establish compatibility. [HostMot2 Ethernet reference](https://linuxcnc.org/docs/html/man/man9/hm2_eth.9.html), [historical litehm2 investigation](https://github.com/sensille/litehm2)

Before ordering: close remaining native connectivity, complete power/current/return and assembly checks, physical-wrapper FPGA implementation/timing, source-bound release files and the concrete prototype measurement plan. The recovered R299 board has 1,172 required joins remaining. The isolated corrected cached DRC has zero ordinary errors/332 warnings/zero parity; it is not adopted hardware or a finished board. Software simulation and native CAD checks retain separate scopes from physical timing, electrical and manufacturing qualification.

## What the earlier Octopus project actually built

The local project `Z:/Programming Projects/GrblHalStm32f4` contains a `btt_octopus_pro_f429` PlatformIO target and saved `.pio/build/btt_octopus_pro_f429/firmware.bin` (255,428 bytes when inspected). This establishes a local **grblHAL / STM32F429 Octopus Pro build**, not which binary is currently flashed on a physical machine. Adjacent documentation is inconsistent about some board/crystal variants, so hardware configuration must be rechecked before any future flash.

The candidate browser app is named **FluidCNC**. That name is separate from **FluidNC**, another CNC firmware project. Our current investigation compiled the upstream grblHAL host simulator and validator; it has not built or flashed new custom-board firmware. Preserving the browser experience with a LinuxCNC backend requires an adapter and feature mapping, not flashing LinuxCNC into an Octopus MCU.
