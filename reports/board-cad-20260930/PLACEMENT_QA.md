# Independent placement-study QA — revision 20260930-03

30 September 2026. Read-only native CAD review of the published revision with KiCad 10.0.4's `pcbnew` API. **Passed the scoped source/manifest/geometry checks, with two missing watchdog courtyards.** This is not a manufacturing approval or a clean routed-board DRC result. Only the QA script and this report/JSON were written; electrical sources, native boards, manifests and prior evidence were not edited.

Actual machine-readable results, native pad-to-net maps and hashes are in `PLACEMENT_QA.json`; the independent implementation is `qa_native_placement.py`. It does not import the board generator or its result-check functions. Command: KiCad bundled Python running `reports/board-cad-20260930/qa_native_placement.py`; exit status **0**, no review errors.

| Saved native study | Footprints / pads / pad nets | Source-assigned / placement-only | Native courtyards | Available 3D models |
|---|---:|---:|---:|---:|
| Motion card, proposed 220 × 100 mm | 70 / 411 / 214 | 68 / 2 | 70 / 70 | 68 / 70 |
| Separate watchdog candidate, provisional 60 × 45 mm | 22 / 68 / 18 | 22 / 0 | 20 / 22 | 20 / 22 |

Every saved native pad number matches its actual source symbol's complete pin set; every native pad net matches the actual source XML node, including unconnected/NC nets. Each footprint assignment, position, rotation, pad size/shape/angle/net, non-text component bounding box, available-model declaration and BOM metadata matches the published manifest. Live BOM/XML/design hashes, source footprint hashes, placement input, generator input, frozen interface specification and the copied custom footprint library match their recorded inputs. The published manifest equals the immutable revision03 manifest, and the failed partial build is absent from its revision list.

Both native boards contain exactly four outline segments at the declared dimensions, **zero copper tracks/vias and zero copper zones**. The default saved native copper-layer count is two and thickness is 1.6 mm; these are study settings, not a qualified stackup. Conservative bounding-envelope checks find **zero pad intersections, zero component-envelope intersections, zero present-courtyard intersections and zero checked envelopes/pads outside either outline**. These checks are not native DRC and do not establish creepage, copper clearance, footprint manufacturing suitability, BGA escape or routability.

Watchdog U1/U2 (`CNC_IS1:TPS3851_DRB8`) have **no native courtyard shapes and no available 3D model**. Their actual copper pads and non-text bounding geometry were checked, but missing courtyards mean there is no complete courtyard clearance review for these two packages. Core U1/Y1 have native courtyards and sourced placement-only footprints but their referenced STEP models are absent. No invented package geometry was credited. The source/primary-package review and remaining mechanical qualification limits are documented in `SOURCE_REVIEW.md`.

The motion-card study intentionally omits 116 source boundary/power-symbol nodes; the separate watchdog study omits eight. The omitted-node lists match the manifest exactly. Core J1–J10 remain logical boundaries, not fitted connectors. The 70-part core study is not a complete motion card or the entire 13-sheet electrical assembly. Required card-local power/supervision and identity, connector selection/mating/positioning, card-bound Ioff interfaces, startup conditioning, permission/self-test and sticky-trip latches, integrated watchdogs and final gate/net allocation remain missing. The standalone watchdog circuit also retains the documented unconfigured-T20 pull-up/100k default-state conflict and partial-power integration limits. No eight/twelve-motor runtime, HDL fit, loaded real-time behavior or physical electrical measurement follows from this placement.

Root separately reports native DRC revision03 with **197 motion-card / 50 watchdog unrouted items** and zero other reported violations. That report is a separate evidence class, not this independent script's result; missing custom courtyards still require review. The manifests explicitly retain `routing=false`, `drc_pass=false`, `physical_measurement=false` and `manufacturing_ready=false`, which this review confirmed.

Reviewed native file SHA-256:

- Motion card: `73f8c143148fc05dfeb94472f49b872102beabe1897751b1158d120b0ec181f8`
- Watchdogs: `d78d1e4be9dd54a1b3675cb76572fdc12da67ba25e57570c3a64ebcd0ecc7525`
- Immutable manifest: `005a689aa63b763e3430b945e8b3a3238467237174214e70ceaaa2ea0695e093`

Disposition: suitable to present as editable source-backed placement progress with unfinished regions clearly labelled. **Not a routed or fabrication-ready controller.** No changes to the frozen IS-1 specification were made.
