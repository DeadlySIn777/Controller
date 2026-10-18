# Motherboard ordinary status source r0.1

30 September 2026. New 17xxx source only; previous motor, power, sensor and probe sources were not changed. The superseded unfrozen 289-part status draft is archived with its hashes in `prior-289-disarmed-semantics/`: ordinary disabled permission is not a system fault.

The source contains **290 purchased physical parts / 861 numbered footprint pads**, seven ordinary common-anode RGB packages, 24 green actual DI receive-level emitters, twelve red actual motor-alarm receive-level emitters, sixteen green actual DO terminal-voltage emitters and one independent red WDT emitter. There are 74 emitter paths. No WS2812 chain, new controller GPIOs, custom module or motion authority is added.

## Actual fault and disarmed behavior

Global `STATUS_HW_GOOD = MC_RAILS_OK_5V AND WD_M_TRIP_N AND WD_O_TRIP_N`. `WD_M_TRIP_N` and `WD_O_TRIP_N` are the retained permission circuit U4014/U4015 pin3 /Q outputs, not the timer's raw WD_OK. Their async rail reset clears the trip record (Q=0,/Q=1). A falling WD_OK samples actual SET1 and its feedback holds a trip until the existing explicit clear. A disabled watchdog does not by itself mean a captured trip. The inherited loaded clock/clear timing and record-before-clear firmware requirements remain unqualified; this indicator does not repair or replace them.

Two SN74AHCT08 hardware gates qualify rail/trip records. Global LOW holds both TLC59116F reset pins LOW, suppressing software R/G/B channels, and two 74LVC07 open-drain sinks independently illuminate four/three parallel red paths. Each path has its own resistor/diode; all seven do not share a single 32mA sink. A separate sink uses the two sticky trip records for WDT indication.

Ordinary TX/OUT/PROC permission LOW is **not global red**. A separate hardware tree `TX_PERMIT AND FPGA_USER_RESET_N AND MOTOR_TX_GATE_A AND MOTOR_TX_GATE_B` controls a normally-open TMUX1121 that physically opens the MOTION green and blue paths when motion is disarmed/unqualified. MOTION red remains controllable; the other six RGBs remain usable for qualified boot/provisioning/setup. A white or yellow MOTION pattern cannot be displayed while those paths are inhibited; the UI must state that limitation rather than pretend a requested color was emitted. LED indications confer no authorization.

| Actual electrical state | Fallback indication |
|---|---|
| CORE5 absent | Dark/unavailable; no healthy claim |
| CORE5 present, MC rails not qualified or logic unavailable | Hardware red, software RGB reset; WDT red means unavailable, not a measured timed-out event |
| Rails qualified, both trip records clear, normal disarm or FPGA user reset | Other RGBs available after explicit fresh software initialization; MOTION G/B physically open; no false watchdog fault from disabled timers |
| Qualified rails and either sticky trip asserted | Hardware red on all seven plus WDT red; software colors reset |
| Unconfigured FPGA with no software status | POR/register defaults remain OFF apart from actual hardware fault paths; no invented module identity/healthy state |

## Exact components, pins and lands

TLC59116FIPWR is the resistor-limited **F** variant. Pin1 is NC, address2/3/4/5, grounds10/19/24, reset25, SCL26,SDA27,VCC28. Its sixteen outputs are pins6/7/8/9/11/12/13/14/15/16/17/18/20/21/22/23. Twenty-one outputs drive RGB; eleven are explicit NC. Individual addresses0x60/0x61; POR all-call0x68 is enabled and must be disabled by the eventual owner. The reserved software-reset0x6B may not be allocated to another device; sub-call0x69/0x6A/0x6C remain default-disabled. No address collides with fitted0x20/0x48/0x49/0x4A. TCA9517DGKR levels the actual ACC `AO_I2C_SCL/SDA` bus into5V; the complete shared bus must remain at≤400kHz.

Six SN74AHCT04PWR TTL receivers accept the actual3.3V protected receive outputs and restore5V logic before six 74LVC07APW,118 open-drain sinks. The latter has an explicitly specified powered-HIGH IOZ row (10µA at−40..85°C, VI=VIH,VO5.5/GND,VCC1.65..5.5) and Ioff10µA atVCC0, unlike merely citing Ioff as powered-off proof. A10k resistor across each receive LED shunts the conditional leakage. No LED directly loads a DI/ALM receive output; added AHCT input leakage/capacitance still belongs in its fanout and edge budget.

Kingbright AAA3528RGBS/K11/C8CC pins1red,2green,3blue,4common-anode; recommended four1.2×.9mm lands atx±1.4/y±.725. APT1608SGC/SURCK pins1cathode/2anode, recommended.8mm square lands with.85mm gap. BAS16,215 has pin1anode,pin2NC,pin3cathode; stock SOT23 contact geometry was independently loaded and reviewed against the manufacturer's2.9×1.3mm body/pin drawing. The field diode is an LED antiparallel clamp, not a replacement for channel surge protection.

TI PW14 and DGK8 lands follow their retained official examples. PW28 uses retained TI4040064-7/G package outline (official DIR9001 p37, package only) and extends the matching PW14 land dimensions/pitch to28 pins. Nexperia SOT402 uses its own exact package outline and the reviewed matching PW14 land dimensions. These two are **derived lands**, not falsely labelled published manufacturer solderland examples: toe/heel coverage and pad clearance are audited, while assembly process approval remains required. There is no invented production/3D/fabrication result.

## Current, loading and qualified limits

All arithmetic below screens 1% resistor tolerance and100ppm/K×150K drift conservatively; scope remains0–55°C internal ambient. CORE5 uses4.95–5.05V, field observation≤30V.

- Each receive/WDT current resistor limits total branch current to5.178690mA even with a shorted LED. The10k bleed is included within this branch current, not an additional supply path. A conditional25°C LED VFmax2.5V and OD VOLmax.55V screen gives about1.6mA optical current; full temperature/brightness is not guaranteed by a25°C VF test.
- Each680Ω RGB/software or parallel-red path limits current to7.615721mA independent of VF/PWM registers. Four hardware red paths total30.462885mA<32mA sink test current; three total22.847164mA. Simultaneous software+hardware red has a15.231443mA resistor ceiling. Native waveform/optical derating remains a measurement gate.
- CORE5 emitter total ceiling351.541693mA normal /404.851742mA simultaneous reset transition (all37receive/WDT plus21softwareRGB plus7parallel red). This is a conservative current-resistor ceiling, not a guaranteed complete IC/current budget. Two I2C5V pullups and logic loads are additional. The two TLC59116F supplies have13mA **typical**, no maximum in the cited table. AHCT ΔICC1.5mA/input is specified atVI3.4V/VCC5.5; no interpolation is called a guaranteed3.14–3.465V loaded aggregate. A.55A CORE5 status reservation is only a planning screen, not a completed supply qualification.
- IO3 adds.1µF nominal bypass and the TCA9517 A-side supply (1mA maximum at both channels LOW) plus two10k bus pullups (≤.744mA at3.6V with the conservative resistor screen). Existing shared pullups must be reconciled, not duplicated in the system budget. CORE5 adds1.9µF nominal bypass including the MOTION switch.
- AHCT loaded VOHmin3.8V at8mA/4.5V versus downstream LVC/TLC VIHmax3.535V is a source-supported test-row screen; total load/fanout, supply ramps and transient margins remain explicit. TMUX1121 activeHIGH has VIH1.49/VIL.87 across rated temperatures, full5V±10% RONmax4.5Ω at10mA/−40..85. Its leakage table usesVDD5V and specified1.5/4.5V terminal test points; arbitrary rail/terminal/brownout cases are not silently guaranteed. No switch I/O gets a separate powered source: all LED/driver/switch signal supplies areCORE5.
- Sixteen field indicators each use two6.8k resistors. Total current≤2.262095mA at30V; worst conservative dissipation per resistor≈35.9mW<100mW rating. These observe **terminal voltage only**, including any external pull-up/backfeed; they do not confirm command acceptance, current flow or load health. Eight return toFIELD_A_0V and eight toFIELD_B_0V, with no isolation barrier bridge.

## Evidence and remaining engineering gates

Native KiCad ERC:0errors/0warnings/noignored. Independent exported-netlist comparison verifies all290parts, exact MPN/footprint/pins and boundary nodes. The actual gate graph is tested for all128 combinations, including disarmed/no-trip versus actual fault. Meaningful negative tests reject raw WD_OK substitutions, cached DI/DO commands, wrong RGB color/common anode, F/non-F driver confusion, activeLOW motion switch, bypassed physical G/B inhibit, unsafe resistor values, field-return bridges, forbidden I2C and hidden NCs.

Native KiCad loads290footprints/861numbered pads and the isolated six-layer geometry fixture has0regular DRC violations/noignored. It deliberately contains unrouted nets and KiCad displays499capped unconnected items; this fixture is not routed PCB evidence, production dimensions or connectivity completion. No Gerber/CPL/drill has been produced for this block. Parent owns actual placement/returns/creepage/routing.

Loaded I2C ACK and bus noise remain engineering issues: TCA B-side contention threshold.4V and TLC SDA.4V test row provide no quoted voltage margin, and mixed exact supply/test loading needs resolution before production; typical lower VOL is not a guarantee. Whole-bus pullup/rise/loading and≤400k operation must close. Driver full maximum ICC/off leakage, complete CORE/IO budget, source fanout, all partial-power/ramp paths and optical/thermal/light-pipe/label/current tests remain unqualified. The LED owner, freshness timeout, reset-aware initialization/readback and stale-state handling are target firmware work, not implemented by these source/host tests. A fault LED is diagnostic; it neither changes nor proves the20ms motion inhibit path.
