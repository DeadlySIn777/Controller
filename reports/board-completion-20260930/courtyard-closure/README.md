# Source-backed MC courtyard closure

30 September 2026. The four custom parent-library footprints now carry **nine valid courtyards** on the current 327-part MC. Historical child generators, circuit sources, footprints and exported evidence remain unchanged. The parent builder explicitly applies [the opt-in envelope helper](../../../tools/hardware_mc_footprint_envelopes.py) when copying footprints, so the next parent regeneration retains the fix.

The added geometry is F.CrtYd only. Every pad expression, existing nominal F.Fab outline, package assignment and circuit net is preserved. The project uses **0.25 mm beyond the larger of the manufacturer's maximum body and the actual copper extents**, rounded outward to a 0.05 mm grid. This is a placement allowance; it does not establish solder-paste, thermal, manufacturing-process or assembled qualification.

| Custom footprint | Maximum body X/Y, mm | Courtyard local bounds [xmin, ymin, xmax, ymax], mm | Current references |
| --- | --- | --- | --- |
| TPS62901_RPJ9 | 1.6 / 2.1 | [-1.20, -1.45, 1.20, 1.30] | U2001, U2002 |
| XGL4020 | 4.3 / 4.3 | [-2.40, -2.40, 2.40, 2.40] | L2001, L2002 |
| LTC2962_UD16 | 3.1 / 3.1 | [-2.00, -2.00, 2.00, 2.00] | U2003, U2004, U2005 |
| TPS3851_DRB8 | 3.1 / 3.1 | [-1.95, -1.80, 1.95, 1.80] | U3001, U3002 |

The RPJ9 courtyard is asymmetric because its retained copper extends farther toward negative Y. Coilcraft's 4.0 +/-0.3 mm body governs XGL4020; the exact currently fitted -222MEC and -102MEC parts are retained. No XAL4030 substitution was made.

## Primary evidence

- [TI TPS62901 Rev A](https://www.ti.com/lit/ds/symlink/tps62901.pdf), p45, RPJ0009A drawing 4224505/A: retained [PDF](../../../research/logic-power/tps62901.pdf), [review image](tps62901-rpj9-outline.png).
- [Coilcraft XGL4020](https://www.coilcraft.com/getmedia/76c9c081-4945-4c85-9129-9356e1ad6734/xgl4020.pdf), p3, document 1529-3 revised 19 February 2026: retained [PDF](../../../research/logic-power/xgl4020.pdf), [review image](xgl4020-outline.png).
- [ADI LTC2962/2963/2964 Rev 0](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC2962-2963-2964.pdf), p18, UD16 drawing 05-08-1691: official PDF inspected through web tools. [Dimension transcription](../../../research/mc-courtyards/ltc2962-ud16-dimensions.json) explicitly records its scope. Direct PDF transfer timed out; its transcription hash is **not** a hash of the full manufacturer's PDF.
- [TI TPS3851 Rev B](https://www.ti.com/lit/ds/symlink/tps3851.pdf), p33, DRB0008A drawing 4218875/A: retained [PDF](../../../research/is1-watchdogs/tps3851-revb.pdf), [review image](tps3851-drb8-outline.png).

[Footprint change receipt](footprint-change-receipt.json) records source hashes, original parent footprint hashes and courtyard-enabled hashes. Original parent footprints are retained under `historical-inputs/`; all historical child artifacts were left untouched.

## Actual verification

[Independent native review](review_native.py) creates a separate [review PCB](native-review/courtyard-review.kicad_pcb) from frozen published **20260930-12**, adding only the nine sourced courtyard rectangles. It proves the parsed board differs only by those rectangles and checks native footprint positions, pad geometry, electrical nets and copper against the original. The [placement receipt](native-placement-review.json) records **327 footprints, 1,229 pads and 673 copper items unchanged**, all 327 front courtyards present, and **zero positive-area overlap pairs** involving the nine new courtyards. No placement shift is required by this check; no published PCB or track was moved.

[Strict native DRC](native-review/strict-drc.json), KiCad 10.0.4, enables all five normally ignored checks as warnings and includes error, warning and exclusion severities. It records **`ignored_checks: []`, zero regular violations, and 499 capped unconnected items**. The nine `missing_courtyard` findings are closed without exclusions or rule suppression. Unconnected routing remains incomplete; this result **is not a passing whole-board DRC**.

The eight [new focused tests](../../../tests/test_mc_footprint_envelopes.py) pass: primary maximum dimensions, preservation of all pads/body outlines, idempotence, wrong-existing-courtyard rejection, rotated-pad rejection, larger-pad inclusion, nonfinite/nonpositive-size rejection, and unchanged unknown footprints. The existing **13 MC integration tests** also pass. No child source regeneration, full test-suite rerun, target compilation, HDL simulation, synthesis or physical measurement is claimed here.

Root owns the subsequent parent r0.4 regeneration and board staging/publication. This receipt freezes the courtyard-only revision-12 review; subsequent oscillator or board revisions require their own current checks. No fabrication files or manufacturing approval were produced.
