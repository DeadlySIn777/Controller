from pathlib import Path
root=Path(__file__).resolve().parents[2]
(root/'hardware/motherboard_analog_input/README.md').write_text('''# Actual isolated differential analog inputs, source r0.2

165 fitted parts / 554 electrical pads. Four protected differential 0–10 V inputs with actual switched 250 ohm current burdens, INA149, buffered ADC inputs, ADS8684AIDBTR acquisition, isolated diagnostics, a protected 87 mA usable sensor branch, and a regulated 10 V reference with a static current ceiling below 10 mA. This is one motherboard region, using purchased DC/DC components.

All three actual primary converter inputs use CORE_24V_PROTECTED / LOGIC_GND. Exact Traco TMR 4-2412WI, TMR 4-2413WI and TMR 4-2415WI have a 9–36 V input, seven actual pins, open remote default ON, and no minimum load. The obsolete R14701 minimum-load bleed is retired. The 12 V converter feeds real TPS7A2650DRVR, whose actual 4.7 kohm load maintains the >=1 mA accuracy test condition; AI5 is no longer directly the loose 5 V converter output.

Actual TPS3702CX50DDCR, SET HIGH, observes AI5 directly with factory UV4.80 / OV5.20 thresholds. Full-temperature ±0.9% gives UV falling >=4.7568 V and OV rising <=5.2468 V, against ADC4.75–5.25 V. Its hysteresis admits the conservative LDO static4.92–5.08 V screen. SENSE and return must be Kelvin-connected at ADC AVDD/AGND: the remaining static margins are only6.8 mV and3.2 mV. These are static source checks; propagation, noise, transients and acquisition freshness are not instantaneous validity proof.

The two TPS3700 coarse15/24 V monitors are actually powered by AI5, with local AI5 bypass. They are not supplied by24 V or by the rail being monitored. Their divided sense networks admit the wide converter static corners; coarse health does not certify INA headroom or calibrated accuracy.

Native XML/model validation and native ERC pass. Exact IC/pad maps, default/fault paths and source limits have focused mutation checks. Target acquisition firmware, real loaded timing/freshness, full-temperature protection, INA output headroom, reference/ADC calibration and effective capacitance remain open. TPS7A26 actual mixed load and PCB thermal must be proved:500 mA is its IC rating, not the usable board allocation. At12.496 V input/4.92 V output, JEDEC73.3 C/W,55 C ambient/125 C junction yields only about126 mA before thermal margin; final copper, thermal vias, coupled module heating and actual maximum load must close.

Primary source and immutable transition receipts are under reports/motherboard-analog-wide-input-20260930. Parent routing, manufacturing DRC, stackup, assembly acceptance and physical qualification are separate gates. No fabrication release is implied.
''',encoding='utf-8')
(root/'hardware/motherboard_analog_output/README.md').write_text('''# Actual two isolated analog outputs, source r0.2

143 fitted parts / 474 electrical pads. Two independently isolated 0–10 V outputs use exact AD5683RBRMZ-3 real SPI register readback, a precision amplifier, normally closed input clamp, normally open terminal disconnect, hardware permission/reset, and actual ADS1115 terminal/rail/reference diagnostics. Receiver minimum remains2 kohm.

Each island uses actual purchased Traco TMR 4-2412WI,9–36 V input, seven pins1/2/3/5/6/7/8 and no minimum load. This corrects the previous18 V minimum after the protected entry. Existing fixed5 V LDOs and all external limits remain. TPS3700 coarse UV upper267 kohm/OV316 kohm with10 kohm lower legs admits the conservative wide-converter static11.504–12.496 V band including threshold, resistor tolerance/TCR, leakage and hysteresis. It does not prove AO precision or amplifier headroom.

Native XML/pin/default validation passes. ERC has zero errors and the eight explicitly justified isolated-return naming warnings, with no ignored checks. The updated96-cap AI/COMMS owner manifest is separate, exact-source placement guidance.

Target firmware/loaded latency, assembled20 ms total inhibit, actual precision/calibration under2 kohm load, effective capacitors, new converter/copper thermal and complete native parent routing/mechanics remain gates. Traco full-load202 mA input and30 ms startup are typical, not maxima. Through-hole drill/land dimensions are assembly candidates; manufacturer module copper/trace exclusion and creepage require PCB reconciliation. No manufacturing release is implied.
''',encoding='utf-8')
