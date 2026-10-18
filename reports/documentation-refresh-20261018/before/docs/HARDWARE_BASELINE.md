# Recommended hardware baseline

Recommendation, 28 September 2026 UTC. No order or final production component selection. This narrows the engineering architecture following the advanced machining and model-based setup requirements.

**Supersession note (28 September 2026):** the compute selection recorded here is historical. The current direction is the open [CM4/CM5-style carrier study](COMPUTE_CARRIER_STRATEGY.md) (CM4, CM5 and BTT CB2 shortlisted, none selected) and the [cost-first build plan](BUILD_PLAN.md), whose memory study starts at **2 GB RAM with eMMC** and justifies any increase by measurement. Where this file and those documents differ, they win.

**Cost update:** the user subsequently made sale price a deciding requirement. The x86/Mesa stack below remains a development reference. CM5 became one measured-cost feasibility candidate with a custom FPGA/I/O circuit and ESP helper; the bundled-display constraint later reopened the compute selection. Previous 8/16 GB provisions are not production requirements.

## Recommended engineering stack

| Layer | Use for the engineering baseline | Why |
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

## Compact production candidate

**Compute Module 5 with eMMC** is one shortlisted compact alternative to the x86 compute module for a custom carrier (the earlier 8 GB RAM / 32/64 GB eMMC provision is superseded; the current memory study starts at 2 GB, see [BUILD_PLAN.md](BUILD_PLAN.md)). It has a quad-core Cortex-A76, onboard Ethernet PHY and one PCIe Gen 2 lane; wireless variants are available. This offers a documented carrier-design route without designing a CPU/DDR motherboard. [CM5 specifications](https://www.raspberrypi.com/products/compute-module-5/), [datasheet](https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf)

A supported Pi 5 image does not qualify a particular CM5 carrier or its loaded latency. Compare the exact CM5 and x86 options using the same model-import corpus, LinuxCNC profiles, storage activity and fault tests. If CM5 meets the requirements it can become the production compute choice; if it does not, retain the x86 module. Do not introduce a new STM32MP2/Linux platform merely for a newer chip before establishing a software benefit.

## Connections inside and outside the enclosure

- The local computer has a dedicated direct wired connection to the Mesa reference endpoint. Ordinary browser/file traffic uses the other interface or a separately supported wireless interface.
- LinuxCNC's Mesa Ethernet driver excludes wireless and USB NICs for its real-time link. Those exclusions do not apply to a laptop's browser connection. [hm2_eth](https://linuxcnc.org/docs/2.9/html/man/man9/hm2_eth.9.html)
- USB-C is a connector requirement to engineer, not a protocol. A laptop-to-controller USB networking function needs actual device-mode hardware/software. An ordinary x86 USB host port does not provide it. A laptop USB-C Ethernet adapter is a simpler service-network option.
- For CM5, explicitly allocate the Ethernet PHY, PCIe lane and USB resources. Reserve native Ethernet for the timing link; choose the additional service-network implementation deliberately. Do not allocate the sole PCIe lane independently to multiple devices without a switch/resource design.
- Supply the main interface directly from the Linux computer. ESP diagnostics can remain a small independent interface when the main application fails; retaining power through a total supply failure needs an additional power design.

## Route to our own hardware

The supported FPGA board is the reference implementation for proving software and machine behavior. A custom carrier, modular I/O and product enclosure can then be developed around the chosen compute module. Replacing the FPGA endpoint is a subsequent engineering decision with its own gateware, host driver, feedback, watchdog and timing evidence.

No bare FPGA is selected yet. Efinix/Lattice/AMD options must be compared by required I/O banks, resources, toolchain, licensing, availability, routing, power and timing closure. A modern FPGA does not automatically implement Mesa/HostMot2 semantics. LinuxCNC also documents litehm2 support, but the current project describes limited configured modules and an older toolchain; that is an investigation route, not established feature parity. [Current hm2_eth](https://linuxcnc.org/docs/html/man/man9/hm2_eth.9.html), [litehm2](https://github.com/sensille/litehm2)

Before ordering: complete the offline UI/backend boundary, representative model-load measurements, hardest machining acceptance programs, interface/resource budget and concrete prototype measurement plan. Software simulation can narrow choices; physical real-time and electrical behavior will still require later tests.

## What the earlier Octopus project actually built

The local project `Z:/Programming Projects/GrblHalStm32f4` contains a `btt_octopus_pro_f429` PlatformIO target and saved `.pio/build/btt_octopus_pro_f429/firmware.bin` (255,428 bytes when inspected). This establishes a local **grblHAL / STM32F429 Octopus Pro build**, not which binary is currently flashed on a physical machine. Adjacent documentation is inconsistent about some board/crystal variants, so hardware configuration must be rechecked before any future flash.

The candidate browser app is named **FluidCNC**. That name is separate from **FluidNC**, another CNC firmware project. Our current investigation compiled the upstream grblHAL host simulator and validator; it has not built or flashed new custom-board firmware. Preserving the browser experience with a LinuxCNC backend requires an adapter and feature mapping, not flashing LinuxCNC into an Octopus MCU.
