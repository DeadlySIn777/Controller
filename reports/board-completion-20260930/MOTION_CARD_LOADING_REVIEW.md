# Integrated motion-card loading review

30 September 2026. Read-only review of the exported four-sheet candidate, including the proposed independent `RAW_INHIBIT_N` connection to FPGA A2. This is a powered DC arithmetic screen and source/topology review. It is not measured electrical qualification, vendor FPGA fit, routed timing, PCB DRC or manufacturing acceptance.

The inspected input bytes, primary documents, exact native node inventory and arithmetic are retained in [the r02 snapshot](motion-card-loading-r02/review.json). Its 20 inputs have matching copied hashes. The review covers 58 fitted LVC functional signal nets; deliberate no-connect nets are excluded. The earlier r01 inventory draft also retained no-connect nets and did not recognize the Nexperia part-name prefix. It is retained as a draft and superseded by r02, not counted as a second acceptance run.

## Result

No fitted ordinary LVC-to-LVC or LVC-to-FPGA control net exceeds the cited 3 V / 16 mA current test condition in this bounded screen. Several nets exceed the light-load 100 µA condition, so their documentation must use the correct loaded output limits. No resistor or gate substitution is required merely to remedy those light-load-accounting mistakes. FPGA-driven nets and the TPS3851 timer inputs still lack the qualification needed to freeze an electrical contract.

`FPGA_CRESET_N` meets the local-power block's **external** load allocations: 370 µA HIGH against 1 mA and 20 µA LOW against 100 µA. Its total fitted HIGH screen is 1.115 mA after including the power block's own 4.7k pulldown. Excluding that existing local resistor from the external budget is deliberate; the source block's budget excludes its own pull.

## Source limits and assumptions

The arithmetic uses a conservative 3.465 V rail maximum, all fitted pull resistors at their 1% resistance corner, and the exact native netlist. Grounded pulls use their minimum resistance for the HIGH load; pulls to a live rail use minimum resistance for the LOW load. The configuration pull source is evaluated against the T20's listed 27k minimum. Startup LOW screens instead use maximum pulldown resistance.

- TI ordinary LVC inputs use their **±5 µA maximum at VI = 5.5 V or GND**; SN74LVC1G34 uses the **±2 µA -40 to 125 °C row**. These are the actual datasheet test conditions, not a promise of a continuously guaranteed input-current curve at every intermediate voltage. Ordinary receivers specify VIH ≥2.0 V and VIL ≤0.8 V at VCC 3.0–3.6 V.
- The cited TI LVC outputs specify **VOH ≥2.4 V and VOL ≤0.4 V at VCC =3 V and IOH/IOL =16 mA**, over the relevant -40 to 125 °C rows. The light-load rows specify VOL ≤0.1 V at 100 µA; SN74LVC1G08's full-temperature light-load VOH is VCC−0.15 V. Most other named TI parts use VCC−0.1 V. Do not mix those rows or apply the 100 µA guarantee to a larger load.
- The Nexperia `74LVC1G17GW` is treated separately: its retained datasheet revision 16.1, pp.5–6, specifies ±1 µA input leakage and light-load VOH ≥VCC−0.1 V / VOL ≤0.1 V at 100 µA. Its delayed-reset output has only one fitted 5 µA TI receiver. It is not assigned the TI 16 mA / 0.4 V limit.
- T20 datasheet v6.0, p.58, tables 72–75: 3.3 V LVCMOS input VIL ≤0.8 V / VIH ≥2.0 V, output VOL ≤0.2 V / VOH ≥VCCIO−0.2 V; input/tri-state leakage ±10 µA; internal weak pull-up 27–65k. **Table 74 drive currents are explicitly nominal-voltage, TJ=25 °C data.** They do not qualify the FPGA's loaded output drive across the intended rail and temperature range. Table 129 on p.86 lists GPIO inputs as tri-state with weak pull-up during reset and configuration; table 124 on p.82 separately describes the dedicated configuration-pin pulls.
- The additional 5 µA board leakage used in startup calculations is a declared allocation, not a measured contamination/leakage result. The ±10 µA T20 datum and 27k minimum are used conditionally at the review rail corner; there is no new measured full-corner confirmation.

Primary source bytes are retained in the r02 snapshot. The TI parts are SN74LVC1G08, SN74LVC1G11, SN74LVC1G17, SN74LVC1G34, SN74LVC2G04, SN74LVC2G08, SN74LVC2G17, SN74LVC2G32 and SN74LVC2G74; timer source is TPS3851 datasheet SBVS300B. The exact part revisions and hashes remain in that snapshot rather than a mutable web link.

## Actual fitted loads

Currents below are conservative current allocations in µA, not measured output currents. LOW includes internal FPGA configuration pull-up current where the driven node reaches an FPGA input. The unknown TPS3851 input current is excluded from these first two columns and addressed separately.

| Native net | HIGH allocation | LOW allocation | Consequence |
|---|---:|---:|---|
| FPGA_CRESET_N | 1,114.681 | 20.000 | Four LVC receiver inputs; total includes 4.7k +10k pulls. External budget passes. |
| FPGA_ENDPOINT_READY | 1,104.681 | 10.000 | Original 10k and new 4.7k are both fitted; FPGA drive remains unqualified. |
| FPGA_MOTION_REQUEST | 1,109.681 | 15.000 | Original 10k +new 4.7k; three receiver inputs. FPGA drive remains unqualified. |
| FPGA_PROGRESS_M | 1,096.681 | 2.000 | Original 10k +new 4.7k; one 1G34 receiver. FPGA drive remains unqualified. |
| FPGA_OUTPUT_REQUEST | 759.681 | 15.000 | Three receivers and 4.7k; no FPGA output ball assigned yet. |
| FPGA_USER_RESET_N | 1,119.681 | 153.333 | Two pulls, FPGA input and three LVC inputs; LOW exceeds 100 µA. |
| RAW_INHIBIT_N | 20.000 | 148.333 | FPGA input plus two LVC inputs; LOW exceeds 100 µA. |
| TX_PERMIT | 375.000 | 153.333 | 10k pull, FPGA input and three LVC inputs; LOW exceeds 100 µA. |
| FPGA_LOCAL_RESET_N | 3,510.000 | 212.801 | Original **1k pulldown**, 47k pull-up and FPGA dedicated reset input; both light-load assumptions are invalid. |
| WD_M_OK | 45.000 | 10.000 | Two LVC receivers plus 100k pulldown; light-load screen remains applicable. |
| WD_O_OK | 50.000 | 15.000 | Three LVC receivers plus 100k; light-load screen remains applicable. |
| WD_M_SET1_BUF / WD_O_SET1_BUF | 40.000 each | 5.000 each | 100k pull and one added sticky-trip OR input; timer current unknown. |
| OUT_PERMIT | 360.000 | 10.000 | 10k pull plus two LVC inputs; use loaded HIGH condition. |
| PROC_PERMIT / PERMIT_OUT_DRIVE | 350.000 each | 0.000 fitted | Downstream connectors/field stage are still absent; zero **fitted** receivers is not a future load guarantee. |

The 153.333 µA LOW cases are 3.465/27k +25 µA receiver allocation. `RAW_INHIBIT_N` instead has 20 µA of fitted receiver allocation. The 212.801 µA local reset LOW adds the 47k pull-up at its minimum resistance. Grounded pulldowns do not add a positive sink load to an actively driven LOW output.

For ordinary receivers, the loaded TI limits leave a 0.4 V HIGH margin (2.4−2.0) and 0.4 V LOW margin (0.8−0.4) at the stated test conditions. This supports the powered DC design screen. It does not establish output rise/fall rate, noise, rail-ramp behavior, physical timing or partial-power operation. In particular, dedicated FPGA reset thresholds/ramp behavior remain subject to the separate reset qualification.

## Startup and timer nodes

The integrated original pulls improve the startup screens relative to the isolated watchdog candidate. With receiver leakage allocations, FPGA tri-state allowance and 5 µA board allocation included, the calculated configuration-node maxima are:

| Node | Maximum screen | Margin below ordinary 0.8 V VIL |
|---|---:|---:|
| FPGA_ENDPOINT_READY | 0.442257 V | 0.357743 V |
| FPGA_MOTION_REQUEST | 0.456679 V | 0.343321 V |
| FPGA_PROGRESS_M | 0.419183 V | 0.380817 V |
| Future FPGA_OUTPUT_REQUEST pin | 0.639223 V | 0.160777 V |
| Future FPGA_PROGRESS_O pin | 0.586740 V | 0.213260 V |
| Future OPI/record-clear/PERMIT_OUT_REQ strobes, one receiver | 0.598851 V | 0.201149 V |

Future-pin rows are **conditional design screens**, not implemented endpoints. The frozen weak-pull behavior, actual FPGA pin assignment, configured drive, and sequencing must be qualified when those pins are added. Request guards use actual `FPGA_USER_RESET_N`; they preserve active-HIGH request polarity. Timer SET1 sees a qualified push-pull gate rather than the FPGA's raw VOL limit.

TPS3851 does **not** specify a maximum SET1 or WDI input current in the retained datasheet. With the existing explicit **50 µA timer qualification allocation**, SET1 loading is 90 µA HIGH and 55 µA LOW after adding the new OR input. The light-load gate rows then give VOL ≤0.1 V versus timer SET1 VIL ≤0.25 V, and VOH ≥VCC−0.15 V versus SET1 VIH ≥0.8 V. That comparison is conditional on proving the timer load allocation. It cannot be promoted to a datasheet-only guarantee. WDI likewise has an unqualified timer input load; the 100k pull adds 35 µA to the HIGH allocation, making 85 µA under the 50 µA assumption.

Raw wired-AND timer health nodes still require 3V3 open-drain and Schmitt-threshold qualification. The timer's retained VOL test is at VDD=5 V/3 mA, and the buffer threshold rows are at discrete supply points. The raw 5 V supervisor node is explicitly outside this review's 3V3 arithmetic and remains confined to the power sheet's level-shifting input.

## Integration topology and implementation gaps

The native netlist establishes these actual connections, independently of the combined JSON's leaf names:

- Power buffer U2006 output reaches `FPGA_CRESET_N`; the raw `MC_RAILS_OK_5V` remains local and goes to its input. Permission rail qualification therefore uses the destination 3V3 signal.
- `FPGA_USER_RESET_N` is the proposed delayed CDONE qualifier and the watchdog SET1 guard. It is a proposal alias; it does not prove the analog delay or the required self-test/reset timing.
- `RAW_INHIBIT_N` connects U4003 pin 7 to FPGA A2 and both downstream raw-inhibit receivers. `TX_PERMIT` separately connects U4007 pin 4 to FPGA E6, the permit-output gate, process gate and TX OPI asynchronous clear. **TX_PERMIT does not replace the endpoint's independent raw inhibit input.**
- Both trip-record OR inputs reach the **same actual buffered SET1 nodes as timer pin 5**, rather than sampling the raw FPGA requests.
- Source physical counts are 70 FPGA, 48 local power, 29 watchdog conditioning and 56 permission: **203 fitted candidates**. The ten historical FPGA review connectors, the power/watchdog/permission boundary markers and schematic power flags are excluded from the fitted BOM as intended. Excluding boundary markers does not implement their connectors.

The builder explicitly aliases only public nets appearing on more than one child sheet. Private nets retain their actual child-sheet scope. Combined `design.json` component pins use leaf names plus `source_block`; a consumer must preserve that scope rather than merge identical private leaf names. The root's native validator now reconstructs scoped names from source netlists, which addresses that specific false-merge risk.

Pending source/interface work remains explicit: FPGA allocations for output request/progress O, OPI strobes/readback and watchdog trip clear/readback; proper DIC, tamper and presence qualification; actual Ioff/bank-B output gate and its readback; field permit-output stage; fixed-base/motion-card connectors and identity; target gateware, self-test protocol and self-test timing; analog reset and partial-power validation. Y1001 still has no fitted footprint, and the T20 footprint is a manufacturer-pad-geometry candidate whose assembly process and FPGA fit remain unqualified. This review requires those gaps to be closed before a production component freeze.

## Change recommendation

Retain the actual parallel pulls during this candidate's qualification. Correct any integrated claims of 0.1 V LOW or VCC−0.1 V HIGH on loads above 100 µA; use the cited loaded rows where applicable. Do not weaken pulls solely to recover a light-load specification. Require sourced/full-corner FPGA drive evidence or physical target measurements for the approximately 1.1 mA FPGA loads, and qualify SET1/WDI leakage, raw watchdog-health LOW/thresholds and the unimplemented interfaces. Any change to frozen startup/default or endpoint behavior belongs in the proposed IS-2 coordination, without altering historical IS-1 evidence.
