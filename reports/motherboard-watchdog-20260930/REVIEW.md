# Fitted watchdog and current motherboard diagnostic RTL review

The native 2,663-part source snapshot has independent motion and output watchdogs, physical permission latches, and final motor/output inhibit paths. The diagnostic gateware now produces the waveform required by the fitted watchdogs and checks real transactions on all four fitted IOL1 links. This closes a source-level interface incompatibility. It does not qualify the complete board's 20 ms electrical withdrawal requirement.

The accepted evidence is `native-r03/review.json` and `rtl-r04/receipt.json`. Earlier numbered directories are retained attempts or superseded evidence. This task changed only the separate diagnostic RTL, its runner, independent source validator and tests. It did not modify the original historical endpoint, hardware sources, native PCB or retained copper.

## Actual fitted hardware and defaults

U3001 and U3002 are **TPS3851G18SDRBT**, the standard `S` timing variant. Each fitted CWD capacitor is Samsung **CL10C332JB8NNNC**, 3.3 nF, 5%, C0G. The watchdog recognizes falling WDI edges; the minimum specified HIGH and LOW widths are 50 ns. The diagnostic image supplies 1 µs HIGH pulses separated by LOW.

Each SET1 path is its own SN74LVC1G08 AND of the corresponding FPGA request and `FPGA_USER_RESET_N`. The receiving request bias is 4.7 kΩ to logic ground. M and O have separate WDI buffers and separate health returns. Each health return joins only that watchdog's open-drain WDO and RESET, then enters its own Schmitt input of U3005. SET1 LOW disables monitoring; normal disarmed operation is therefore different from an armed timeout. The G18 reset threshold is not a complete 3.3 V power-good monitor.

Native-pin evaluation covers the actual U4001–U4019 permission gates and asynchronous latch clears. Rails, configured-user-reset, acquisition health, external permit and tamper state qualify the base permission; each watchdog qualifies its respective permission. Restoring a failed qualification does not automatically re-arm either latch. A new request edge is necessary. Independent sticky watchdog-fault latches are also present.

The ideal graph passes all 4,096 combinations of its twelve reviewed logical inputs and additional startup/fault/re-arm checks. This proves polarity and connectivity in this source snapshot. IC ramp behavior, actual loaded thresholds, fanout, leakage and response times require their own qualification. Missing/unconfigured-module defaults are conditional on the actual reset, pull, supervisor and receiving-rail paths; they have not been measured on a physical board.

## Fault withdrawal follows the final gates

U6042's bank outputs drive `MOTOR_TX_GATE_SOURCE_A/B`. Two series TLP3640A health contacts per bank connect SOURCE to MID to the original FINAL `MOTOR_TX_GATE_A/B`. All six AM26C31IPWR packages and all twelve individual-enable NAND stages consume FINAL. A watchdog fault drives SOURCE LOW through contacts which are already closed; this path does not wait for those health contacts to open or for a rail to discharge.

Every individual enable is formed from its active enable request AND FINAL permission, then inverted for the open-drain LED sink. Removing FINAL makes the sink output high impedance and removes LED current. Each channel's actual TLP3640A normally-open and TLP4176A normally-closed photorelay LEDs are in series. The correct withdrawal events are **NO opening** and **NC closing**. Toshiba specifies a 0.2 ms maximum NO opening and a 1 ms maximum NC closing at the stated 25 °C, 5 mA LED, 200 Ω load, 20 V test point. The NC's 3 ms opening maximum belongs to assertion, not withdrawal. Actual current/temperature/load limits are not implied by these test-point maxima.

The digital-output hardware permission crosses the default-LOW `ISO7762F` isolator to the EN pins of the actual TPS274C65AS devices. TI specifies 33 µs maximum EN-to-90%-output falling delay at 24 V/48 Ω. The complete EN-to-10% output-off value of 57 µs is typical only. Terminal voltage decay for other loads has no complete worst-case bound here. ISO7762F's published power-loss default applies after its primary rail falls below the specified threshold; the 1.7–2.25 V interval is not a guaranteed logic region.

These are electrical inhibit paths. They do not prove a machine's braking time, stop distance, holding-torque behavior or external drive STO response.

## Numerical 20 ms screen

| Quantity | Result | Status |
| --- | ---: | --- |
| Standard TPS3851 nominal timer, `3.23 × CWD[nF] + 0.381` | 11.040 ms | Manufacturer formula |
| 5% capacitor and ±9.5% programmed-timer error | 9.508880–12.672380 ms | Conditional published timer calculation |
| Additional C0G temperature, 10 pF board capacitance and ±10 nA board leakage screen | 9.215803–13.122690 ms | Board parasitic/leakage assumptions unmeasured |
| LTC6994 qualification filter maximum used in this screen | 1.299574 µs | Reviewed resistor and IC tolerance calculation |
| Known conditional timer + reviewed logic/filter + NC closing terms | 14.124020 ms | Not a complete physical upper bound |
| Remaining 20 ms budget for unbounded terms | 5.875980 ms | Not evidence that those terms fit |

The additional C0G screen uses Samsung's official C-code ±30 ppm/K coefficient and a maximum 100 K excursion from 25 °C. The extra board leakage allowance uses the published minimum CWD charge current only to screen additional external leakage; it does not multiply internal charge-current tolerance into the ±9.5% timer specification again.

TPS3851 Table 5.6 lists WDI-to-WDO assertion, initial CWD evaluation, enable setup and startup delays in the NOM column, without maximums. Treating the 50 ns WDI-to-WDO number as a guaranteed maximum would be incorrect. Complete withdrawal also needs actual buffer loading, the series-contact gate RC, relay timing over the required internal ambient and LED currents, complete digital/PWM/analog output decay, health-monitor response and every partial-power ramp path. The independent report keeps these quantities `null` rather than substituting old IS-1 allocations. No full-condition 20 ms pass is claimed.

## Separate bring-up RTL

`gateware/motherboard_bringup/` preserves the byte-for-byte historical CNC1/CNC2 sources and tests. Its motion diagnostic module has six active generators and two encoders. Physical motors 6–11 have STEP/DIR LOW and individual EN_N HIGH. This is not twelve coordinated axes or the future CNC3 production protocol.

The new wrapper runs four real parallel mode-0 SPI masters on fitted IOL1 L0–L3. Each sends complete 40-byte SYNC/read-only transactions and validates the returned CRC32C, header, class, slot, nonzero epoch, preceding sequence, status, age, reserved fields and zero applied output image. Three consecutive failed responses latch that link's fault and stop polling it; the other masters continue. A link restart requires a new nonzero provisioned epoch. Unprogrammed, absent, stale or corrupt MCU responses cannot qualify all four links.

Only a polling cycle with four validated complete responses produces O useful progress. M progress is separate and occurs only for accepted ARM/UPDATE motion frames. IOL1 qualification must precede a diagnostic motion ARM, and a latched IOL1 fault removes that session's authority. NOPs, rejected frames and free-running motion do not feed M.

`FPGA_OUTPUT_REQUEST`, PWM/process/permit-out/ARM-lamp requests, OPI re-arm and power-enable requests stay LOW. Shift-chain clocks stay LOW and load signals inactive HIGH. This image does not implement target MCU firmware, watchdog self-test, acceptance of installed module identities, production configuration or output authority. Because O request stays LOW, the fitted O watchdog normally remains disabled; its armed timeout still needs a controlled diagnostic qualification procedure.

The explicit native pin map is `pin-map-r01.json`; key watchdog balls are **E4 = M** and **L2 = O**. This image uses the CMD select at M9 for its CNC1 diagnostic SPI session. The separate FB select B2 is deliberately unused. A native net map is not a vendor-qualified constraints file or a routed-PCB continuity result.

## Validation achieved

| Evidence | Result | What it proves |
| --- | --- | --- |
| Independent native-pin/default/polarity evaluation | 4,289 assertions passed | Reviewed source connectivity and ideal logic |
| Focused host/negative tests | 23 passed | Mutation detection and timing-claim boundaries |
| Current synthetic-peer RTL bench | 60 checks; five M and 61 O completed pulses | Transaction checks, pulse widths, failure handling and safe constants |
| Historical default endpoint regression | 252 checks passed | Preserved historical six-axis/two-encoder baseline |
| Historical ABI2 discovery regression | 27 checks passed | Preserved historical capability behavior |
| Historical permission bench | 49 checks passed | Preserved ideal permission-connection evidence |
| Strict Verilator lint and Verilog-2005 elaboration | Passed | Current RTL language/static checks |
| Real Yosys `synth_efinix` mapping | 7,788 LUT4; 5,376 FF; 2,733 ADD; one GBUFCE | Family-level synthesis without inferred latches |

The four synthetic MCU peers receive actual CS/SCLK/MOSI transactions and construct independent CRC-correct replies. The bench rejects semantic errors even when their CRC is correct. It exercises bad CRC, class, slot, epoch, stale sequence, card fault, stale age, reserved fields, SOF, version, output permission, applied readback and an all-zero absent-device response. Synthetic peers are not compiled target MCU firmware.

No package fit, vendor place-and-route timing, bitstream, physical 20 ms measurement, board ERC/DRC rerun or manufacturing files are generated by this diagnostic task. Those evidence classes remain distinct.

## Primary sources retained

- TI TPS3851 Rev B: `research/is1-watchdogs/tps3851-revb.pdf`; [official datasheet](https://www.ti.com/lit/ds/symlink/tps3851.pdf).
- Samsung fitted MLCC/C0G definitions: `research/is1-watchdogs/cl10c332jb8nnnc.html` and `sources/samsung-mlcc-part-code.html`; [official MLCC search](https://product.samsungsem.com/mlcc/basic-search.do).
- TI SN74LVC2G17 and permission gates: retained PDFs under `research/is1-watchdogs/` and `research/machine-permission/`.
- TI AM26C31: `research/mc-motor-buffers/am26c31.pdf`; [official datasheet](https://www.ti.com/lit/ds/symlink/am26c31.pdf).
- Toshiba TLP3640A/TLP4176A: retained manufacturer PDFs under `reports/motherboard-motors-20260930/sources/`.
- TI ISO776x and TPS274C65: retained manufacturer PDFs under `reports/motherboard-do-20260930/sources/`; [ISO7760 family](https://www.ti.com/lit/ds/symlink/iso7760.pdf), [TPS274C65](https://www.ti.com/lit/ds/symlink/tps274c65.pdf).
- ADI LTC6994 reviewed manufacturer data: `reports/motherboard-motors-20260930/sources/ltc6994-primary-web-review.json`.

`receipt-r01.json` hashes the accepted reports, executable sources/tests, primary files and visual timing-table excerpts. It records every remaining proof gate explicitly.
