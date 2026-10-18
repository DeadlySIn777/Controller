# Independent watchdog and edge-armed output permission

Engineering candidate, 28 September 2026. A real, editable seven-IC circuit now provides independent progress monitoring and a global permission latch. It is sized electrically to drive the new twelve-motor transmitter proposal's six AM26C31 enable inputs. The user requirement remains **at least eight motor channels, expandable to twelve**. The copied old ledger and endpoint RTL remain labelled historical six-channel evidence; this block does not implement additional motor generators or per-drive enable/alarm circuits.

## Actual deliverables and checks

`hardware/machine_permission` contains the KiCad schematic/project, source library, watchdog contact footprint, exported XML netlist, ERC JSON, PDF, inspected PNGs, component/boundary model, frozen inputs, event trace and hash manifest. Generator and independent validator are `tools/hardware_build_machine_permission.py` and `tools/hardware_validate_machine_permission.py`.

- KiCad 10.0.4 ERC: **0 errors and 0 warnings**; its ignored-check list is preserved.
- Exact independent connection/component/pin checks: **PASS**.
- `python -m unittest discover -s tests -p test_machine_permission.py -v`: **27 tests passed**. These include actual-export mutations and digital event scenarios.
- The PDF overview, watchdog and latch detail renders were inspected. The manufacturer's watchdog package drawing was also rendered and checked.
- `validation.json` records SHA-256 hashes and calculated limits. `behavior-trace.json` is explicitly a Boolean/event study, not SPICE, analog timing or actual RTL execution.

Root independently implemented `gateware/board_review/tb_permission_connection.sv` using the actual existing endpoint and idealized board equations. Its reported 47 checks were read-only reviewed against this circuit; the equations agree. That bench injects watchdog status and does not establish the watchdog's physical timing. Its authoritative run evidence belongs to the root's separate record.

No PCB, DRC, fabrication outputs, physical machine operation, safety certification or manufacturing readiness is claimed.

## Circuit behavior

U1 is **TPS3431SDRBR**, permanently enabled with EN and SET1 tied to IO_3V3. WDO and ENOUT are wired together, so an uninitialized/disabled watchdog cannot be treated as healthy merely because WDO is released. A Schmitt input conditions this shared open-drain node. A second Schmitt input consumes the FPGA's open-drain CDONE. The FPGA block owns CDONE's pull-up; this block adds no competing pull-down.

The physical equations are:

```text
watchdog_good  = Schmitt(WDO_N wired-AND ENOUT)
config_done   = Schmitt(FPGA_CDONE)
base_ok       = FPGA_LOCAL_RESET_N AND config_done AND EXT_PERMIT_3V3
raw_inhibit_n = base_ok AND watchdog_good
latch_clear_n = raw_inhibit_n AND FPGA_ENDPOINT_READY

arm_latch D = 1; PRE_N = 1
arm_latch CLK = rising FPGA_MOTION_REQUEST
arm_latch CLR_N = latch_clear_n

TX_PERMIT = arm_latch.Q AND FPGA_MOTION_REQUEST AND raw_inhibit_n
```

`raw_inhibit_n` is exported as `HW_WATCHDOG_OK_N` and feeds the endpoint's existing `inhibit_n`. Despite the legacy output name, it includes reset/configuration/external-permit conditions as well as watchdog health. **TX_PERMIT must never feed the endpoint inhibit input**: that would create an arm/progress dependency loop. Endpoint-ready participates only in latch clear, downstream of the raw interlock.

The latch uses the existing RTL `motion_enable` output as its explicit arm clock. A successful zero-rate protocol ARM produces that rising edge. U6's asynchronous clear removes latched permission on any relevant failure. A recovered watchdog signal, CDONE or external permit does not clock the latch. Recovered heartbeat alone cannot resume the outputs. A clock-stalled FPGA can therefore lose physical permission without executing another instruction or clock edge.

During a normal DISARM, the final gate drops immediately with motion request. The latch may retain Q while the endpoint remains ready; a new deliberate ARM edge is still required for the request to rise. An asynchronous failure clears Q. A request held high through failure recovery cannot restore Q.

This design includes the FPGA block's **local service/programming reset**, `FPGA_LOCAL_RESET_N`, rather than only the upstream sequencer reset. Reconfiguration must remove permission even when the power rails remain good.

## Watchdog timing correction

The earlier approximately20ms TPS3431 study was incorrect. The primary source gives:

`tWD(ms) = 77.4 × CWD(nF) + 55`

TI tests timing capacitors from100pF upward. Nominal100pF with negative tolerance would leave that range, so the fitted candidate is **GRM1885C1H121JA01D**,120pF, C0G,50V,5%,0603. The model uses ±0.6% temperature allowance to cover the inspected low-temperature table and high-temperature coefficient, plus the timer's ±9.5% programmable-time factor.

| Timing result | Value / qualification |
| --- | --- |
| Nominal timeout | 64.288ms |
| Capacitor extrema before parasitics | 113.316–126.756pF |
| Fresh component timeout | Calculated in `validation.json`, approximately57.7–71.0ms |
| Additional10pF parasitic allowance | Maximum rises to approximately71.9ms; actual stray capacitance must be measured |
| Watchdog fault/reset pulse | 170–230ms, followed by automatic release |
| CWD initialization |381µs is typical; the model does not relabel it a guaranteed maximum |

PCB leakage is significant beside the watchdog's nanoampere timing current. Actual leakage, parasitic capacitance, solder/environment effects and loaded timing remain physical qualification gates. The reported fresh timing interval is not a whole-board guaranteed fault-response time; logic delays and actual pin levels must also be included.

The existing endpoint toggles `progress_wdi` once per accepted sequence-valid UPDATE while armed. **TPS3431 feeds only on falling edges**, so a feed occurs every two accepted UPDATEs. A free-running FPGA clock, NOP, CRC error, replay, disarmed transfer or ESP activity is not the specified progress source. The source copies preserve this contract. A normal1ms UPDATE cadence gives about2ms between falling edges, comfortably inside the study interval. Every supported faster/slower host period still needs its own declared limits.

The existing FPGA watchdog expires after5ms at its assumed50MHz clock. It acts first during ordinary communication loss with a running FPGA clock. The independent external watchdog covers clock-stall cases on its much longer approximately64ms interval. Those two limits must not be conflated, and neither implements controlled deceleration.

The external watchdog continues timing while disarmed. With no UPDATE stream it periodically asserts for170–230ms and opens another watchdog interval. It does not create a new motion latch or require a new hardware acknowledgement merely because an idle cycle expires. Host recovery must wait for the raw interlock to be healthy, establish a fresh SYNC, then deliberately ARM zero-speed and begin valid updates within the available interval. An attempt made during WDO-low is inhibited; stale ARM/UPDATE authority cannot be silently replayed after release. Target-host startup/retry behavior still needs integration testing.

## Pins, interfaces and loading

Exact package mappings are independently checked against the exported netlist:

| Device | Physical pin map |
| --- | --- |
| TPS3431SDRBR |1 VDD,2 CWD,3 EN,4 GND,5 SET1,6 WDI,7 WDO_N,8 ENOUT; exposed ground pad9 |
| SN74LVC2G17DBVR |1 1A,2 GND,3 2A,4 2Y,5 VCC,6 1Y |
| SN74LVC1G34DBVR |1 NC,2 A,3 GND,4 Y,5 VCC |
| SN74LVC1G11DBVR |1 A,2 GND,3 B,4 Y,5 VCC,6 C |
| SN74LVC2G08DCUR |1 1A,2 1B,3 2Y,4 GND,5 2A,6 2B,7 1Y,8 VCC |
| SN74LVC2G74DCUR |1 CLK,2 D,3 inverted Q,4 GND,5 Q,6 CLR_N,7 PRE_N,8 VCC |

The DFF's Q is **pin5**, not pin3. Its unused inverted output and the buffer's NC pin are explicitly unconnected. All power pins have a local100nF bypass. Exact bypass MPNs and physical boundary connectors remain unselected. Other support resistors have explicit CRCW0603 candidate part numbers in `design-envelope.json`.

`JCTRL1`:1 IO_3V3;2 LOGIC_GND;3 FPGA_LOCAL_RESET_N;4 FPGA_CDONE;5 EXT_PERMIT_3V3;6 FPGA_ENDPOINT_READY;7 FPGA_MOTION_REQUEST;8 FPGA_PROGRESS_WDI.

`JOUT1`:1 TX_PERMIT;2 HW_WATCHDOG_OK_N;3 HW_PERMISSION_LATCHED;4 WD_HEALTH_RAW_N;5 LOGIC_GND. These are schematic integration boundaries, not user-facing connectors. Status loads cannot be added without accounting for their leakage/capacitance. The raw watchdog node is open-drain and must not receive a push-pull driver.

EXT_PERMIT_3V3 is an active-high **protected internal logic signal**, not raw24V. The proposed assembly alias to the existing ISO1212 `PROTECTIVE_STATUS_FPGA` output is reasonable only as a fixed, reserved, active-high assignment. The existing100k bias and this block's10k pull-down both remain. An ordinary CLI/profile change cannot invert or repurpose that hardwired interlock. The ISO1212's undefined brownout output behavior remains a limitation; this is not a certified safety input. The upstream protection/filter/latency evidence belongs to that separate digital-input block.

The final LVC1G11 drives six AM26C31 G inputs plus their six10k pull-downs and this block's own10k default. At3.4V with a2% resistor envelope and six1µA input loads, the load is below2.44mA. The gate's conservative VOH bound is2.4V at3V supply/16mA load, above the transmitters'2.0V VIH. Low-level and power-off bias calculations are retained in the validator. `/G` remains high on the transmitter sheet; **TX_PERMIT low disables the differential outputs**. A separate active-low drive-enable stage has not been implemented here.

The watchdog's WDI high requirement is0.8×VDD. A raw FPGA's conservative loaded VOH cannot simply be assumed to meet that ratio. U3 supplies a buffered WDI with100k pull-down and a20µA load allowance, keeping total high load below55µA. The buffer's ≤100µA bound is VCC−0.1V, which clears the watchdog input requirement. Actual watchdog input leakage is not fully bounded by the inspected limit table; the allowance requires target confirmation.

The Schmitt buffer avoids applying slow open-drain edges to ordinary CMOS gate inputs. CDONE's source10k pull-up and ≤5µA buffer leakage give a high-level estimate above3.14V. Published Schmitt thresholds at3V and4.5V provide useful margin, but they are discrete test points: continuous3.2–3.4V/full-temperature threshold behavior remains a characterization gate, not an invented interpolated device guarantee.

## Defaults, hazards and honest limits

All ordinary request/status/reset inputs have explicit pull-downs except open-drain CDONE. The latch-clear, latch-Q, raw-inhibit and final-permit outputs also have local pull-downs. At zero logic supply, the final gate's maximum10µA Ioff plus six1µA receiver-input allowances produces about24mV across the seven parallel pull-downs. This endpoint calculation assumes the stated topology and no external energized injection; it does not establish every partially powered state.

The TPS3431 source has conflicting text about WDO below its minimum operating supply. ENOUT is included because its documented low behavior makes startup interpretation stronger, but operation below its validity limits is still not a guaranteed permission circuit. The sequencer's narrow rail windows and reset path remain required. Arbitrary brownout slew, held/retained supplies, external backfeed and gate behavior below normal operating limits remain open.

Ordinary logic input slew, latch asynchronous-clear recovery and pulse width require physical validation. SN74LVC2G74's125°C table specifies3.5ns minimum clock/clear pulse and1.8ns inactive-clear setup at3.3V±0.3V. The CLK path has no intentional delay; clear is produced by the raw interlock and endpoint-ready gates. A properly separated SYNC/ARM handshake provides substantial nominal recovery time, but an interlock edge near an ARM edge can violate device timing. The Boolean tests do not prove metastability immunity or a minimum capturable fault pulse.

The watchdog is a single-channel control component. A CWD open circuit can select a much longer default interval; a SET1 fault can disable it; a stuck gate or corrupted FPGA request can defeat assumptions. This is not a redundant or safety-certified stop system. Independent machine safety, drive power/STO where appropriate, brake/gravity/workholding response and fault-specific controlled stopping remain separately required design work. Removing permission can truncate STEP pulses and lose known physical position.

Reserve **10mA on IO_3V3** and **0.9662µF added capacitance** for this block, including the timing-cap allowance. This covers the stated pull-down, transmitter gate-drive and logic-control study loads; board measurements and a complete system budget remain necessary. The custom DRB contact footprint implements pins and exposed center pad from the manufacturer drawing; thermal copper extensions, optional vias, paste, mask, placement and assembly process still need board-level design.

## Reproduction

```powershell
python tools/hardware_build_machine_permission.py
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export netlist --format kicadxml -o hardware/machine_permission/netlist.xml hardware/machine_permission/machine_permission.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch erc --format json -o hardware/machine_permission/erc.json hardware/machine_permission/machine_permission.kicad_sch
& 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe' sch export pdf -o hardware/machine_permission/machine_permission.pdf hardware/machine_permission/machine_permission.kicad_sch
python -m unittest discover -s tests -p test_machine_permission.py -v
python tools/hardware_validate_machine_permission.py
```

Primary links, revisions and page references are recorded in `research/machine-permission/SOURCES.md`. No older block, historical ledger or shared assembly file was edited by this work.
