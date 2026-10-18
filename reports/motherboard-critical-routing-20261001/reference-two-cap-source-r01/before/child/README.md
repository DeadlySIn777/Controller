# Actual isolated differential analog inputs, source r0.2

165 fitted parts / 554 electrical pads. Four protected differential 0–10 V inputs with actual switched 250 ohm current burdens, INA149, buffered ADC inputs, ADS8684AIDBTR acquisition, isolated diagnostics, a protected 87 mA usable sensor branch, and a regulated 10 V reference with a static current ceiling below 10 mA. This is one motherboard region, using purchased DC/DC components.

All three actual primary converter inputs use CORE_24V_PROTECTED / LOGIC_GND. Exact Traco TMR 4-2412WI, TMR 4-2413WI and TMR 4-2415WI have a 9–36 V input, seven actual pins, open remote default ON, and no minimum load. The obsolete R14701 minimum-load bleed is retired. The 12 V converter feeds real TPS7A2650DRVR, whose actual 4.7 kohm load maintains the >=1 mA accuracy test condition; AI5 is no longer directly the loose 5 V converter output.

Actual TPS3702CX50DDCR, SET HIGH, observes AI5 directly with factory UV4.80 / OV5.20 thresholds. Full-temperature ±0.9% gives UV falling >=4.7568 V and OV rising <=5.2468 V, against ADC4.75–5.25 V. Its hysteresis admits the conservative LDO static4.92–5.08 V screen. SENSE and return must be Kelvin-connected at ADC AVDD/AGND: the remaining static margins are only6.8 mV and3.2 mV. These are static source checks; propagation, noise, transients and acquisition freshness are not instantaneous validity proof.

The two TPS3700 coarse15/24 V monitors are actually powered by AI5, with local AI5 bypass. They are not supplied by24 V or by the rail being monitored. Their divided sense networks admit the wide converter static corners; coarse health does not certify INA headroom or calibrated accuracy.

Native XML/model validation and native ERC pass. Exact IC/pad maps, default/fault paths and source limits have focused mutation checks. Target acquisition firmware, real loaded timing/freshness, full-temperature protection, INA output headroom, reference/ADC calibration and effective capacitance remain open. TPS7A26 actual mixed load and PCB thermal must be proved:500 mA is its IC rating, not the usable board allocation. At12.496 V input/4.92 V output, JEDEC73.3 C/W,55 C ambient/125 C junction yields only about126 mA before thermal margin; final copper, thermal vias, coupled module heating and actual maximum load must close.

Primary source and immutable transition receipts are under reports/motherboard-analog-wide-input-20260930. Parent routing, manufacturing DRC, stackup, assembly acceptance and physical qualification are separate gates. No fabrication release is implied.
