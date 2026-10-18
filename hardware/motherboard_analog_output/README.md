# Actual two isolated analog outputs, source r0.2

143 fitted parts / 474 electrical pads. Two independently isolated 0–10 V outputs use exact AD5683RBRMZ-3 real SPI register readback, a precision amplifier, normally closed input clamp, normally open terminal disconnect, hardware permission/reset, and actual ADS1115 terminal/rail/reference diagnostics. Receiver minimum remains2 kohm.

Each island uses actual purchased Traco TMR 4-2412WI,9–36 V input, seven pins1/2/3/5/6/7/8 and no minimum load. This corrects the previous18 V minimum after the protected entry. Existing fixed5 V LDOs and all external limits remain. TPS3700 coarse UV upper267 kohm/OV316 kohm with10 kohm lower legs admits the conservative wide-converter static11.504–12.496 V band including threshold, resistor tolerance/TCR, leakage and hysteresis. It does not prove AO precision or amplifier headroom.

Native XML/pin/default validation passes. ERC has zero errors and the eight explicitly justified isolated-return naming warnings, with no ignored checks. The updated96-cap AI/COMMS owner manifest is separate, exact-source placement guidance.

Target firmware/loaded latency, assembled20 ms total inhibit, actual precision/calibration under2 kohm load, effective capacitors, new converter/copper thermal and complete native parent routing/mechanics remain gates. Traco full-load202 mA input and30 ms startup are typical, not maxima. Through-hole drill/land dimensions are assembly candidates; manufacturer module copper/trace exclusion and creepage require PCB reconciliation. No manufacturing release is implied.
