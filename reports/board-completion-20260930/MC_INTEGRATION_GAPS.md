# Motion-card integration requirements — source inspection, 2026-09-30

The former `fpga_core` is a useful FPGA/configuration baseline, but it does not implement IS-1's complete motion card. Frozen `spec/modules.json` provides a pooled 272/320 contact budget and functional groups; it does **not** provide a P1/P2 row/position-to-net allocation. [MC_BOUNDARY_NET_DIRECTIONS.csv](MC_BOUNDARY_NET_DIRECTIONS.csv) enumerates all **194** single-ended boundary conductors with direction. [MC_INTEGRATION_GAPS.json](MC_INTEGRATION_GAPS.json) records the full source hashes, expanded FPGA requirements and proposed alias matches. Candidate names in these files are integration labels, not a new frozen specification.

## Connector boundaries and direct paths

P1 is described as motion/feedback and P2 as links, host, flash and supervision. Both are **logic** boundaries on the MC; raw field voltage and motor differential outputs stay on MIA/MX4/other field cards. The remaining budget is 66 LOGIC_GND signal returns, four switched CORE_5V feeds/four returns, two presence contacts, two identity I2C contacts and 48 spare contacts. Feed the MC regulators from its **PSM-switched slot branch**, not an unswitched raw 5 V rail. Combine local regulator health with the remote PSM qualification before permission. The exact power contact grouping and safe grounding placement still require a real contact map.

| Functional boundary | MC outputs | MC inputs |
|---|---|---|
| MIA, eight standard motors | STEP0–7, DIR0–7, EN0–7_N, TX_PERMIT_A, shared OPI_REARM | ALM0–7, OPI_OK_A, MIA_PRESENT_A/B, MIA_PGOOD |
| MX4, four reserved expansion motors | STEP8–11, DIR8–11, EN8–11_N, TX_PERMIT_B, shared OPI_REARM | ALM8–11, OPI_OK_B, PRESENT_A/B, EXP_PGOOD, MOD_ID0–2 |
| EIA/EX8 capture | Each status CLK/LOAD_N | ENC0–11 A/B/Z, FREQ0/1, MPG A/B, PRB0/1, each status DATA |
| DIC safety | ARM_LAMP, PERMIT_OUT_DRIVE | EXT_PERMIT, PROCESS_PERMIT, SAFETY_STATUS, RESET_ARM, CONTACTOR_FB, STO_FB |
| DIC/DOA/DOB/ACC IOL1 | Separate L0–L3 SCLK/CMD/CS_N | Separate L0–L3 RSP |
| ACC direct commands | PWM0/1, PEN0/1, OUT_PERMIT_ACC, PROC_PERMIT | Through its separate serial response for analog/diagnostic results |
| DOA/DOB permissions | OUT_PERMIT_DOA and OUT_PERMIT_DOB, each own buffer/pull-down | Through their separate serial responses |
| CMC servo SPI | MISO | SCLK, MOSI, separate CS_FB_N/CS_CMD_N |
| CMC flash restore | Flash MISO, CDONE status copy | SCK, MOSI, CS_N, CRESET_N, BUS_SEL |
| PSM/slot status | MC power-good open drain, passive MC presence paths | RAILS_OK, TAMPER_N; 29 slot-status-chain input conductors |
| ESC | MOTION_DISARMED observation | None required on this MC boundary |
| XS reserved | SCLK/CMD/CS_N, SYNC_STROBE, XS_REFCLK, XS_PERMIT | RSP |
| MIR-1 | I2C bidirectional SDA/SCL | Same branch, AT30TSE752A-XM8M-T; not a push-pull buffer path |

The 29 slot lines are presence A/B and PGOOD for EIA, EX8, DIC, DOA, DOB, ACC, ESC, CMC and XS plus two SCART presence lines. They enter a local **40-bit** chain with seven fixed-zero bits and the four-bit marker. The FPGA needs SSR_CLK/SSR_LOAD_N/SSR_DATA, checks the marker and two consecutive matching reads, and retains the frozen fault rules. DIC presence/PGOOD also directly feeds the hardware DIC_OK qualification; a serial status copy is insufficient.

STEP/DIR, enables, alarms, encoders, probes, frequency, MPG, PWM/PEN, external/process permits, XS1 safety feedback and permission nets stay direct. General home/door/machine inputs move to DIC's 24 validated serial DI. Permission is never conveyed solely inside IOL1. IS-1 requires Ioff and source termination at each IOL1 connector and a round trip below 60 ns at 8.333 MHz; this is an unmeasured requirement.

## Ioff requirements and exact candidate parts

IS-1 mandates MC Ioff buffers on every card-bound FPGA output but leaves their general MPN selection to engineering. **SN74LVC07APWR is the MIA/MX4 LED cathode driver**, not the MC boundary buffer. A transmitter buffer alone does not qualify back-power protection of an unpowered receiving card; its receiver boundary and pull defaults must also be implemented.

Source-backed implementation candidates:

- [SN74LVC244APWR](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf), octal, IO_3V3 supply, active-low OE, two groups of four. It provides Ioff. Bank-A OEs are tied active as frozen; STEP/DIR buffer inputs need idle-low pulls and EN_N inputs idle-high pulls so the unconfigured FPGA's weak pulls cannot select an unintended enable.
- [SN74LVC2G126DCUR](https://www.ti.com/lit/ds/symlink/sn74lvc2g126.pdf), dual, IO_3V3 supply, active-high OE and guaranteed Ioff. Bank B needs **13 gated paths**: 12 STEP/DIR/EN_N and TX_PERMIT_B. Seven dual parts provide 14 channels. All used OE pins and OPI_BOE asynchronous clear must be on the same physical positive qualified-enable net. Its inputs/outputs must retain the source polarity and defaults.

SN74LVC244A's active-low OE cannot be connected directly to that positive enable. Inverting it would require OPI_BOE to observe the actual output-enable pin net with correct polarity. SN74LVC126A, the similarly named quad part, has no Ioff guarantee in its datasheet and is not substituted for 2G126. These MPNs are proposed implementation choices; a complete MC output-isolation implementation is still absent.

At the receiving motor cards every AM26C31 STEP/DIR input retains a 10 kΩ pull-down and every enable input a pull-up. The local LED supply and TX-permission gates keep field contacts disabled; software enable defaults alone do not satisfy the requirement.

## FPGA allocation changes and hardware aliases

The current allocation contains **96** user-net entries. It reserves all 12 STEP/DIR, alarm and enable signal labels, but only four ABZ encoder groups and the former general-input arrangement. Physical enable circuits are still reported zero and alarm circuits six in its source. The full proposed requirement ledger has 78 existing name/alias matches (including clock/local reset outside the `user_allocations` list) and 98 new names. Matches are source candidates, not bank fit or implementation proof.

- Keep STEP0–11/DIR0–11 and ALM0–11 balls; change `DRIVE_ENABLEi_FPGA_RESERVED` to actual `ENi_N_FPGA` outputs, adding real downstream circuits.
- Reuse G12/`PROBE_FPGA` as PRB0, G15/`TOOLSETTER_FPGA` as PRB1, and G16/`PROTECTIVE_STATUS_FPGA` as the hardwired EXT_PERMIT status copy. Nineteen other former general-input balls return to the new allocation. Preserve their historical evidence separately.
- Rename old `HOST_SPI_CS_N` as CS_FB_N; add CS_CMD_N. Keep SCLK/MOSI/MISO. Add the ownership-selected flash restore path; never wire competing CMC/FPGA flash drivers together.
- Keep endpoint-ready and motion-request; old progress becomes **progress_m**, and add independent progress_o/output-request, both watchdog OK readbacks, OUT/PROC readbacks, both sticky trip inputs, event-record clear, all OPI inputs/re-arm, PERMIT_OUT_REQ, local SSR and external qualification/status signals. The JSON lists every individual required node.
- The new `mc_permission` has separate OPI_REARM_TX and OPI_REARM_BOE boundary names. They can alias the single frozen motion OPI_REARM strobe (also exported to MIA/MX4); OPI_REARM_OUT aliases the separate OPI_REARM_O. Its WD_REARM_M/O record-clear inputs can alias the single frozen clear strobe only when the event-persistence semantics are satisfied. Do not allocate extra GPIO silently.

**Budget correction needed in the integrated revision:** §6.2 explicitly requires RAW_INHIBIT_N to the FPGA independently of TX_PERMIT. It is absent from the frozen 175-node table, which lists only WD_M_OK, WD_O_OK and TX/OUT/PROC readbacks. Keep this input: current A2/`HW_WATCHDOG_OK_N` is an alias candidate, with polarity explicitly audited (low inhibits). Adding it gives a nominal **176 nodes, 13 spare, at least 39 LVDS-as-GPIO nodes** under the same 189/137 counting model. Exact dedicated-pin/user-GPIO classification and Efinity fit still need proof.

The boundary note's “rows z and d used as ground rows” also needs explicit contact interpretation: fully reserving both rows on both connectors uses 128 contacts and leaves only 192 for 194 single-ended signals before I2C, presence or power. It cannot mean four completely ground-only rows at the retained scope. Ground-adjacent permission contacts and return ratios must be implemented by an actual per-contact map.

MC requires no additional STM32 in IS-1: the remote STM32G031 controllers reside on DIC/DOA/DOB/ACC. The MC is FPGA, clock, flash, local power/qualification, watchdog/permission, boundary buffers, identity/temperature and local status chain. This report changes no frozen file, electrical source or current allocation and claims no target build, HDL fit, circuit ERC, board DRC or measurement.
