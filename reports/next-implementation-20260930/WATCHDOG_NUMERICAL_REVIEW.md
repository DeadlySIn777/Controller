# Independent watchdog numerical review

30 September 2026. Scope: source inspection of `tools/is1_watchdog_analysis.py`, `tests/test_is1_watchdog_analysis.py` and this increment's `README.md`, checked against the retained TPS3851 SBVS300B Rev.B text/PDF and Samsung capacitor HTML. Arithmetic was independently recalculated with Python `Decimal` at 32-digit precision, without importing the reviewed calculation. Retained PDF, extracted text and capacitor HTML hashes match `research/is1-watchdogs/sources.json`. No reviewed file, circuit, frozen specification or numerical-output JSON was edited. Tests were inspected, not executed; no target or physical timing qualification was performed.

**Result:** the default numerical screen and README rounding are correct. They support a conditional candidate-selection screen, not guaranteed watchdog timing or self-test-window qualification. The initial wording gap around the exact 150 µs setup allowance was corrected by the root agent while this review was underway; the revised fields and numerical record were independently rechecked. Physical setup/window closure remains open.

## Independent results

For C in nF and time in ms, retained TI section 7.1.1.2 Equation 1 gives `t = 3.23 C + 0.381`. Table 7-2 applies factors 0.905 and 1.095 to ideal-capacitor timing. The independent calculation uses the reviewed tool's stated initial ±5%, assumed ±0.6% temperature, 10 pF positive parasitics, ±10 nA leakage correction relative to typical 375 nA, and unmeasured 4.31 ms downstream allocation.

| Quantity | 3.3 nF candidate | 4.7 nF comparison |
|---|---:|---:|
| Nominal Equation 1 timeout | 11.0400000000 ms | 15.5620000000 ms |
| Initial-capacitor and IC timing minimum | 9.5088802500 ms | 13.3966697500 ms |
| Initial-capacitor and IC timing maximum | 12.6723802500 ms | 17.8715497500 ms |
| Frozen leakage-approximation minimum | 9.2618963474 ms | 13.0487043019 ms |
| Frozen leakage-approximation maximum | 13.0195687500 ms | 18.3611812500 ms |
| Extended assumed-screen minimum | 9.2083400635 ms | 12.9724271703 ms |
| Extended assumed-screen maximum | 13.1314519125 ms | 18.5051140875 ms |
| Screen maximum + 4.31 ms allocation | 17.4414519125 ms | 22.8151140875 ms |
| Remaining 20 ms allocation | 2.5585480875 ms | −2.8151140875 ms |
| Screen maximum + exact assumed 0.150 ms setup | 13.2814519125 ms | 18.6551140875 ms |

Thus README's 9.26–13.02 ms, approximately 9.21–13.13 ms, 17.44 ms and 2.56 ms are correctly rounded. The 3.3 nF assumed screen exceeds 5 ms but does not exceed 10 ms at its minimum, matching the tests' feed-spacing conclusions. A 1,000 ns pulse divided by the datasheet's stated 50 ns minimum is exactly 20; this ratio is arithmetic, not verification of generated pulse width at the physical WDI pin.

For the frozen 9.06–13.37 ms self-test window, containment is true **only with the tool's exact setup assumption**: lower clearance is 0.1483400635 ms and upper clearance is just 0.0885480875 ms. The arithmetic does not include a qualified maximum setup variation, request-path skew, Schmitt transition delay or timestamp uncertainty.

## Findings

1. **Original request-to-trip wording corrected; qualification remains open.** The initially reviewed `tools/is1_watchdog_analysis.py:64–66` added exactly 0.150 ms and reported `extended_request_to_trip_ms` and `selftest_window_contains_extended_screen`. Retained TI timing table 5.6 places 150 µs in the **NOM** column, with no MIN/MAX; section 6.3.4.4 states that WDI is ignored during the enable setup interval. It does not establish a guaranteed maximum SET1-to-timer-start or request-to-WDO delay. The current source instead reports `extended_request_to_trip_with_nominal_setup_ms`, `set1_setup_nominal_ms`, `set1_setup_maximum_guaranteed: false`, `selftest_window_contains_nominal_setup_screen`, the assumption-based upper clearance, and `selftest_guaranteed_timing_bounds_closed: false`. The revised test explicitly requires both guarantee/closure flags to remain false. README now calls out about 89 µs upper clearance and the open maximum. These changes accurately distinguish arithmetic containment from qualification; the physical maximum and sufficiency of the frozen window still require controlled implementation and measurements. No frozen-window revision was made by this review.

2. **The leakage calculation is correctly described as an approximation, not a production bound.** The retained electrical table lists 347/375/403 nA at CWD = 0.5 V; 375 nA is typical. The tool and README already acknowledge that using `375/(375±10)` is an unqualified sensitivity screen, and correctly avoid multiplying the IC's charge-current tolerances into the timer error again. Its use does not guarantee that ±10 nA board leakage, or the resulting timeout interval, holds over temperature/humidity. For illustration only, using 347 nA solely in that same leakage-correction factor produces an extended screen of 9.1890807901–13.1605463262 ms; that alternative is also not a guaranteed envelope. This shows why the typical-current correction should retain its qualification flag.

   The approximation scales the complete `3.23 C + 0.381` timeout, including the additive evaluation term. An idealized constant-current correction applied only to the charge-dependent `3.23 C` term gives 9.2172960375–13.1200219125 ms instead. The reviewed calculation is slightly wider in this comparison, but that observation does not prove a worst-case physical leakage model: the actual internal evaluation and charge behavior are not modeled.

3. **Capacitor assumptions are bounded honestly; the retained HTML does not establish the chosen 0.6% envelope.** The page identifies CL10C332JB8NNNC as 3.3 nF, ±5%, C0G, −55 to +125°C, 50 V, 0603 and mass production, and labels page data as typical reference data. No retained quantitative temperature/bias/aging/leakage acceptance envelope proves the tool's ±0.6%, 10 pF or ±10 nA assumptions. The tool docstring and README make the assumption/evidence distinction correctly. Keep the required capacitor and assembled-node qualification open.

4. **Minor reusable-API range gap resolved.** The initially reviewed `screen()` accepted any finite positive `cap_nf`, although TI specifies/tested the adjustable capacitor range as 0.1–1,000 nF. The current code rejects cases where `lower_c × (1 − temperature_allowance) < 0.1 nF` or `upper_c × (1 + temperature_allowance) + parasitic_pf/1000 > 1,000 nF`. The added test checks an unsupported 0.01 nF value, nominal boundary values whose tolerance envelopes cross the range, and excessive parasitics. This was verified by source inspection without rerunning tests. The 3.3/4.7 nF results are unchanged.

## Disposition

**Root disposition after the independent review:** the helper now rejects an effective tolerance/temperature/parasitic capacitor envelope outside TI's 0.1-1,000nF recommended range. A ninth regression checks nominal and tolerance-boundary violations. The default numerical record is unchanged; this is a subsequent implementation correction, not an additional reviewer-run physical or target test.

The current [reviewed numerical record](watchdog-numerical-screen-reviewed.json) was checked against 26 independently calculated Decimal values for both capacitor candidates. Maximum difference attributable to binary-float serialization is below 0.000000000001 ms (observed 1.9741 × 10⁻¹⁵ ms). The revised guarantee/closure/manufacturing flags are false for both candidates. README's current arithmetic link now points to this reviewed record; the earlier record remains historical evidence.

Accept the reported default arithmetic and its useful rejection of the 4.7 nF complete-path candidate under the same allowances. Treat tests as checks of the calculation and assumption flags. Preserve the existing 20 ms requirement, independent watchdogs and frozen IS-1 self-test requirements. Before asserting a guaranteed interval or window, qualify capacitor/board leakage and parasitics, enable timing and complete downstream behavior, including accepted WDI edges after SET1 setup. README already states that no physical or complete-machine response is qualified; retain that wording.

Primary retained evidence: [TI TPS3851 SBVS300B](https://www.ti.com/lit/ds/symlink/tps3851.pdf), [Samsung selected capacitor page](https://product.samsungsem.com/mlcc/CL10C332JB8NNN.do), [retained source manifest](../../research/is1-watchdogs/sources.json). Local table-column positions were checked in the retained PDF, rather than inferring guarantee columns from flattened text.
