# ACC2 bounded AO interface correction

The 48-part ACC source is archived under `prior48-inputs/` and remains historical evidence. The r0.2 source has 50 physical footprints: 44 purchased fitted components plus six PCB test pads, and 159 electrical pads.

The only added hardware is two 10 kΩ pullups for real AO chip selects. PB3, package pin 42, drives `AO0_CS_N_HOST`; PB4, package pin 43, drives `AO1_CS_N_HOST`. Both reset to deselected. SPI2 PB13/PB14/PB15 shares actual clock, response and command with the future AI ADC. Existing I2C1 PB8/PB9 and its pullups are preserved.

The source and exact GPIO allowlist now specify the readback-capable AD5683RBRMZ-3 frontend. Actual terminal voltage readback comes from isolated ADS1115 devices, distinct from DAC input-register readback. No target firmware or valid measurements are claimed by native source inspection.

ERC is zero errors/zero warnings with no ignored checks. The receipt records all 50 footprints loaded by native pcbnew, exact native XML pin checks and the fresh 280-test source regression. The fourth IOL1 lane, slot, frame timing, fail-off defaults, actual supervisor, hardware watchdog option requirements and deliberate rearm semantics are unchanged.
