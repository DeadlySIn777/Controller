# Bounded motherboard IO3 supply correction

Source candidate MB-IO3-001 continues the existing motherboard. It does not modify the retained motion-card source files, frozen motor/health/power-entry blocks, parent PCB or copper. This is not a fabrication release.

## Integration

Import `apply_io3_upgrade` from `tools/hardware_apply_motherboard_io3_upgrade.py` and call it on the retained `mc_local_power` schematic tree plus its full component model **before** the parent flattens/promotes that child. It returns deep copies `(tree, model, receipt)`. Unexpected MPNs, endpoints, manufacturer pin functions or repeated application raise errors.

Copy/register `CNC_MB_IO3.kicad_sym` as `CNC_MB_IO3`. Copy/register `CNC_MB_IO3.pretty` as the same footprint-library name. Keep the existing `CNC_MC_Power:TPS62901_RPJ9` footprint unchanged. The helper relocates the existing `IO_3V3` hierarchy-port UUID to R18001 pin 2, so the existing parent port remains valid. The new regulator-side node is private to the child: `/mc_local_power/IO_3V3_REG_LOCAL`. All other distributed consumers remain on the original IO3 net.

The exact ledger is in the accompanying receipt. Changes are U2002 TPS62901RPJR -> TPS62902RPJR; four endpoints (U2002.3, L2002.2, C2005.1, C2010.1) move to the local node; R2005 becomes CRCW06030000Z0EA and its pin 2 moves from LOGIC_GND to CORE_5V; R2008 becomes TNPW06032K55BYEA, with unchanged pins. Add R18001 KRL2012E-C-R015-F-T5 from local to distributed IO3 and R18002 TNPW060311K5BYEA from local to IO_3V3_VSET. No other retained endpoints or component records may change.

## Manufacturer evidence and conditional bounds

TI TPS62901 SLVSFS7A and TPS62902 SLVSFM1A specify the identical RPJ0009A pin map and package drawing 4224505/A (10/2018). The new regulator is rated 2 A; the retained regulator footprint and inductor remain unchanged. TI documents the distributed ceramic-load application with at least 10 mΩ distribution resistance. The explicit 15 mΩ resistor is a controlled design inference from that application, subject to real impedance/stability qualification. Its conservative minimum is 14.738625 mΩ after 1% tolerance and 50 ppm/K over a 150 K screen.

MODE is directly HIGH through a fitted 0 Ω link to VIN. This uses TI's external-FB, 2.5 MHz forced-PWM, output-discharge selection. It avoids assuming an unpublished MODE leakage for a pull-up resistor. MODE and VIN rise together; existing enable sequencing is retained. Power-off ramp behavior, alternate supply paths and startup under load still require validation.

Nominal feedback is 0.6 × (1 + 11.5k/2.55k) = 3.305882 V. The lower-impedance divider is deliberate: the guaranteed 70 nA FB current contributes up to 0.806691 mV, whereas 115k/25.5k would contribute about ten times as much. The corner screen uses TI's ±0.9% full-temperature reference bound, 0.1% initial resistor tolerance, 10 ppm/K over resistor temperature 0–85°C (maximum 60 K from reference), and the published Vishay 500 ppm / 1000 h general-operation drift limit with film temperature ≤125°C. This is a conditional life-test screen; it does not guarantee arbitrary aging or environmental exposures.

At the current 0.908707745 A design allocation and maximum damper resistance, the downstream minimum before additional copper/noise is 3.250213725 V. The receiver's guaranteed UV arming corner is 3.247426050 V, leaving **2.787675 mV** for additional DC drop and noise. Local maximum 3.347933104 V leaves **3.614724 mV** before the guaranteed OV corner. These margins are not closed until actual routed loss/noise and a complete load profile fit them. The 2 A rating does not mean the receiver can arm at any 2 A load.

The local nominal reservoir remains 22.1 µF. It must remain ≥10 µF effective after bias, tolerance, temperature and aging. The 1394-part source snapshot had another 66.11 µF nominal distributed capacitance; later source additions must be counted separately. No plane, track or other supply may bypass R18001. VOS and feedback must sense the local side with a quiet Kelvin return. The retained 1 µH inductor, regulator thermal behavior, startup, load-transient stability and FPGA dynamic demand remain qualification gates.

Susumu's exact MPN page specifies 15 mΩ, 1%, 50 ppm/K, 1 W and −55–175°C. Its catalogue's KRL2012 ≥2 mΩ recommended lands are two 0.70 × 2.20 mm pads at x = ±0.65 mm (0.60 mm inner gap, 2.00 mm span). The custom footprint uses those lands, not an ordinary 0805 pattern. Assembly solder-mask/paste and thermal assumptions require manufacturing review.

Primary sources: [TI TPS62901](https://www.ti.com/lit/ds/symlink/tps62901.pdf), [TI TPS62902](https://www.ti.com/lit/ds/symlink/tps62902.pdf), [Susumu exact resistor](https://www.susumu.co.jp/en/product_detail/?pdid=505), [Vishay TNPW e3](https://www.vishay.com/docs/28758/tnpw_e3.pdf). PDFs, rendered land pages and hashes are retained in the reports/research directories identified by the freeze receipt.

## Verification

The isolated native schematic has 50 fitted footprints, 162 numbered physical pads, 51 XML components including a nonphysical boundary and 171 connected XML nodes. KiCad 10.0.4 loaded all 50 footprints and the independent native/model connectivity validator passes. Native ERC reports zero errors, zero warnings and no ignored checks. The isolated source plus frozen motor/health/power-entry regression suite passed 92 tests, including negative tests for a bypassed damper, incorrect manufacturer pin map, wrong mode/feedback parts, native mismatch and unrelated retained mutations.

These checks are source inspection, native schematic ERC, native footprint loading and host tests. They are not PCB DRC, routed connectivity, FPGA target analysis, physical measurements or manufacturing approval.
