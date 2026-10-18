# Proposed IS-2 watchdog input conditioning

30 September 2026. This is a separate circuit proposal, not an agreed revision
of frozen IS-1, an integrated permission circuit or a manufacturing release.
The original 22-part r0.1 circuit remains unchanged beside this folder.

The 29-part candidate preserves two TPS3851G18SDRBT timers, independent Samsung
CL10C332JB8NNNC 3.3 nF capacitors, shared IO_3V3/LOGIC_GND, the wired-AND
RESET/WDO health nodes, separate Schmitt channels, request polarity and
falling-edge watchdog feeds. It adds physical conditioning that frozen IS-1
did not provide.

| Proposed change | Reason | Interface effect |
|---|---|---|
| R3/R4/R5/R7: 100 kΩ to Vishay CRCW06034K70FKEA 4.7 kΩ ±1% | T20 configuration pull-ups are 27–65 kΩ. A 100 kΩ pull does not establish LOW; 10 kΩ also fails the conservative LVC input screen. | Four FPGA-facing request/progress lines draw about 0.750 mA each when HIGH; same polarity and logical signals. |
| U6/U7 SN74LVC1G08DCKR plus C8/C9 decoupling | SET1 has an unusually low 0.25 V LOW threshold. A lightly loaded LVC output provides a 0.1 V maximum LOW test condition. | `WD_M_SET1_BUF = FPGA_MOTION_REQUEST AND FPGA_USER_RESET_N`; output channel equivalent. The existing CDONE-qualified user-reset guard must be connected and qualified. |
| R11/R12 100 kΩ at the physical SET1 pins | Defined passive load/default at each conditioned output. | An internal net is added; no customer terminal. |
| R13 4.7 kΩ at the reset-guard boundary | Two gate inputs plus an unpowered driver can source leakage. A 100 kΩ default cannot bound this input below 0.8 V. | Existing MC user-reset signal is added to the review boundary. Its added HIGH load is about 0.755 mA. |

The new drawing boundary is a non-fitted review symbol, not a selected physical
connector. The proposed gates do not supply the missing sticky arm/trip latches,
the field permission chain or watchdog self-test sequencer. The FPGA must hold
request/progress LOW while reset and maintain the frozen deliberate recovery
rules. Changing the physical pull values and adding the reset guard require a
versioned interface decision; this document does not claim logic-owner approval.

## Conditional electrical screen

The calculation in `tools/watchdog_conditioning_analysis.py` uses IO_3V3 at
3.14–3.465 V, a 27 kΩ FPGA configuration pull-up, the pull-down at its +1%
limit, and **20 µA summed source-current allowance** (T20 10 µA, AND input
5 µA, board allowance 5 µA). It gives **0.59885 V**, leaving **0.20115 V**
below the LVC 0.8 V LOW requirement. These current allowances are desk-screen
inputs; the TI input-current table is tested at GND or 5.5 V and does not
independently certify leakage at every intermediate input voltage. Loaded
startup at temperature, ramping and partial power remain unqualified.

Under a **50 µA maximum external timer-input-load requirement**, a SET1 output
sources at most 85 µA including its 100 kΩ pull. The AND driver's ≤100 µA
characterization gives VOL ≤0.1 V and conservatively VOH ≥2.99 V over the
reviewed rails/temperature table; SET1 requires LOW ≤0.25 V and HIGH ≥0.8 V.
The TPS3851 datasheet does **not** give SET1 or WDI input-current maxima. The
50 µA requirement must therefore be proved or replaced by better source-backed
component evidence before calling the interface qualified. A 66 µA input load
already exceeds the selected ≤100 µA HIGH characterization after the pull load;
the tool deliberately withdraws its VOH claim in that case.

T20 LVCMOS lists VOH ≥VCCIO−0.2 V and VOL ≤0.2 V. The chosen actual GPIO drive
strength must satisfy those levels with approximately 0.750 mA added loading;
typical drive-current entries are not a guaranteed qualification. The existing
upstream LVC user-reset driver must preserve ≥2 V at the aggregate fanout,
including the new approximately 0.755 mA. Neither loaded path is physically
verified here.

## Pulse and timing consequences

The WDI arrangement remains a non-inverting SN74LVC1G34DBVR buffer on each
progress signal. No clock, edge detector or extra pulse generator is added.
For monotonic, slew-qualified FPGA edges and ≤50 pF output loading, its
−40…125°C maximum propagation delay is 4.7 ns. Conservatively taking zero
minimum delay, a 1,000 ns input pulse screens to **995.3–1004.7 ns**, above the
TPS3851 50 ns minimum. This is a datasheet-condition arithmetic screen;
glitches, noise, slow edges, cross-power effects and duplicate physical falling
edges remain measurement requirements. The request AND adds at most 6 ns under
its cited load/temperature table. The timer and downstream clock-stall budget
are otherwise unchanged; the independent approximately 17.44 ms screen still
depends on unmeasured downstream, capacitor and leakage allowances.

On reset assertion, SET1 is requested LOW; any contemporaneous buffered WDI
fall must be checked for ordering. Timer disable is not itself a machine stop:
the complete permission circuit must independently remove permission. On reset
release, the FPGA requests and progress must already be LOW; the guard may not
be used to mask stale HIGH requests. A ramp below the logic devices' valid
operating region can produce unspecified outputs. Power sequencing and the
upstream reset/permission gates must contain that region, with measured fault
injection. No automatic restart is permitted.

The TPS3851 SET1 setup table specifies 150 µs **nominal**, with no guaranteed
maximum. The frozen 9.06–13.37 ms self-test window still has only about 89 µs
upper clearance against the expanded assumed timing screen, before the new
request-path delay and timestamp uncertainties. This proposal does not widen
that window or claim guaranteed self-test timing closure.

## Source and evidence boundaries

Manufacturer source pin tables, regenerated KiCad netlist, native ERC and host
mutation/arithmetic tests are separately recorded in
`reports/board-completion-20260930/watchdog-conditioning/review.json`. No HDL
integration, target compile, vendor FPGA fit, board DRC, circuit transient
simulation or physical measurement is supplied by these checks.

Primary retained sources: [TI TPS3851 Rev B](https://www.ti.com/lit/ds/symlink/tps3851.pdf),
[TI SN74LVC1G08 SCES217AA](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf),
[TI SN74LVC1G34 SCES519O](https://www.ti.com/lit/ds/symlink/sn74lvc1g34.pdf),
[TI SN74LVC2G17 SCES381N](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf),
and `research/fpga-core/trion20-ds-v6.0.pdf` tables 72–75 / configuration states.
Exact retained PDF/text hashes are included in the candidate design and copied
review receipt. The DRB land pattern remains copper-only with stencil, thermal
vias, CWD guard geometry and production routing unqualified.
