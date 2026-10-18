# Independent analog outputs, source candidate

This source adds the frozen two independently isolated 0–10 V analog outputs to the one motherboard. It has 143 fitted parts and 468 electrical pads. It creates no custom daughterboard. Each purchased TRACO power converter is a component soldered to the motherboard.

Each island includes its actual 12 V converter, 5 V regulator, 12 V undervoltage/overvoltage monitor, AD5683RBRMZ-3 DAC, OPA197 amplifier, normally closed input clamp and normally open output disconnect. The receiver requirement is at least 2 kΩ. Precision is a target requiring calibration and temperature/load measurements; 16-bit silicon does not prove 16-bit board accuracy.

AD5683RBRMZ-3 is the exact SDO variant. AD5683RBRMZ without `-3` is electrically different. SPI readback returns the input register; tying LDAC LOW transfers it into the DAC. That observation does not independently read the internal DAC latch and does not measure terminal voltage. A separate ADS1115 on each island reads the actual terminal, 12 V rail, 5 V rail and reference. Its readings need real firmware, validity and freshness checks.

The original DAC80501 choice has no SPI SDO, and a single I2C write at 1 MHz exceeds the frozen 20 µs apply allocation. The approved replacement uses shared ACC SPI2 with separately biased PB3/PB4 chip selects. At the conservative 4 MHz candidate rate, the two DAC writes take 12 µs of wire time. Two input-register readbacks take a further 24 µs. These are arithmetic screens, not a firmware scheduling or complete commit-latency result. I2C1 remains available to qualified status drivers; the two analog monitor ADCs reserve addresses 0x48 and 0x49.

Native KiCad ERC reports zero errors and eight ground-name warnings. Those warnings identify real isolated `AO0_COM`/`AO1_COM` returns, which KiCad's naming heuristic does not classify as ground. No check is ignored. The independent validator accepts only those exact eight warnings and rejects other warnings/errors. Joining these returns to LOGIC_GND would break the required isolation.

The exact TI ADS1115 DGS and TPS7A16 DGN lands are included. The regulator DNC pin has no electrical net, and its exposed pad is the local isolated return. The two relay package geometries are deliberately different. The TRACO single-output converter has physical pins 1, 2, 4 and 6, and no pin 5. Native pcbnew loads every actual pad and checks the vendor geometry.

The source receipt is `reports/motherboard-analog-20260930/receipt.json`. It records 280 fresh source regression tests and 71 unchanged inputs. This is circuit source evidence. Target firmware, board integration/routing, power and thermal margins, loaded signal timing, contact release, whole 20 ms inhibition, precision, EMC and physical connectors remain separate acceptance gates. No manufacturing files are issued by this block.
