# Motion-card package and connector review — 2026-09-30

The T20F256 pad discrepancy is corrected in a new native footprint. The oscillator's installed KiCad land pattern matches Abracon's drawing. The frozen HB160 connector pair has a mating-direction error; a precise angled-male card / straight-female base correction is recorded as a proposed IS-2 mechanical addendum. These results close source and package-geometry questions. They do not establish a finished, routed or manufacturable motion card.

| Item | Finding | Concrete artifact and remaining limit |
|---|---|---|
| U1 T20F256I4 | Installed stock copper Ø0.32/mask Ø0.47 differs from current Efinix optimum NSMD Ø0.35/Ø0.50 | New `T20F256_Efinix_NSMD` footprint, native-verified; fabrication and assembly process acceptance remain open |
| U1 ball orientation | All 256 current manufacturer ball identities and stock coordinates agree | A1 stays top-view (−6,−6) mm; no exposed pad introduced |
| U1 height visualization | Source overall 1.04 ±0.10 mm, maximum 1.14 mm | A rendered envelope uses 13×13 nominal/basic X/Y and maximum Z; lateral tolerance and reflow geometry remain open |
| Y1 ASE | Stock pads, numbers and centers exactly match source land pattern | Native source comparison passed; no package model claimed |
| HB160 P1/P2 | Frozen parts are both angled; incompatible axes for standing card / flat base | Proposed `02011601101` angled male card plus `02021601201` straight female press-in base; exact cage/footprint/process integration pending |

## Implemented package correction

Created [T20F256_Efinix_NSMD.kicad_mod](../../hardware/motion_card/CNC_Motion.pretty/T20F256_Efinix_NSMD.kicad_mod) from the installed KiCad community `TFBGA-256_13x13mm_Layout16x16_P0.8mm` footprint. Preserved the complete 16×16 0.8 mm grid, pad numbers, A1 marker, nominal body outline and courtyard. Changed all copper pad diameters to 0.35 mm; the inherited 0.075 mm radial mask margin yields the required 0.50 mm aperture. [Library attribution and license](../../hardware/motion_card/CNC_Motion.pretty/README.md) are retained. The footprint is an assembly review candidate; inherited paste apertures do not constitute stencil qualification.

[Efinix Trion Packaging Guide v5.3](https://www.efinixinc.com/docs/trion-packaging-ug-v5.3.pdf), Figure 28/page 29 and Table 12/page 58, supplies the package and selected pad dimensions. The guide also gives NSMD trace clearance 0.10 mm and reference via dimensions in Tables 13/14. Those routing references still require the fabricator's capability and actual stack-up. The drawing's 13 mm basic dimensions and lateral profile tolerance must not be treated as a guaranteed 13 mm maximum collision envelope.

The freshly retrieved official [T20 pinout v3.5](https://www.efinixinc.com/docs/t20_pinout-v3.5.xlsx) supplies exactly the same 256 ball labels and all A–F ball properties as the retained workbook. Native KiCad 10 confirmed unique pad identities, every coordinate, circular 0.35 mm pads, mask margins and absence of an exposed pad. Corners are A1(−6,−6), A16(+6,−6), T1(−6,+6), T16(+6,+6) mm; rows are `ABCDEFGHJKLMNPRT`.

Created [T20F256_source_envelope.wrl](../../hardware/motion_card/3dmodels/T20F256_source_envelope.wrl) as an eight-vertex display envelope. Numeric bounds after KiCad's 2.54 mm VRML unit conversion are x/y ±6.5 mm and z 0–1.14 mm. It rendered successfully in KiCad and was visually inspected. It is not a manufacturer STEP file and asserts no ball, chamfer, marking or assembled solder-joint geometry. Its project-relative path requires model copying/remapping when a generated project is published. No mechanical stand-off part was invented or selected.

The [Abracon ASE source](https://abracon.com/Oscillators/ASEseries.pdf), page 5, gives 3.2 ±0.2 ×2.5 ±0.2 mm body and 1.2 mm maximum height. Stock `Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm` exactly matches its 1.3×1.1 mm pads and 2.10×1.65 mm center spacing: 1 lower-left, 2 lower-right, 3 upper-right, 4 upper-left. No source electrical file was edited by this task; the parent integrator owns footprint assignment.

## Concrete connector correction

The [primary HARTING catalogue](https://b2b.harting.com/files/livebooks/en/PRD0200000100183/downloads/livebook.pdf) shows `02011601101` as angled male (PDF page 9) and `02041601101` as angled female for rear access (page 12). In the frozen arrangement each mating axis is in its own PCB plane, so a perpendicular standing motion card cannot mate with the flat passive base using those two orientations. A further interposer/reorientation would be needed; none is present in IS-1.

The catalogue's standard card/backplane arrangement uses angled male with straight female. The proposed exact pair is card `02011601101` and base `02021601201`, retaining level 1/at least 500 cycles and all 320 P1/P2 contacts. The [current exact female page](https://www.harting.com/en-US/p/DIN-Signal-harbus64-160FP-45-50C1-1-02021601201) confirms straight, press-in, fixing-flange geometry. The solder alternative shown in the catalogue is level 2 and is not an equivalent retained-life substitution.

[IS2_MECHANICAL_ADDENDUM.md](../../hardware/motion_card/IS2_MECHANICAL_ADDENDUM.md) records the controlled revision candidate. [hb160-contact-grid.csv](../../hardware/motion_card/hb160-contact-grid.csv) lists all 320 physical row/position contacts, with separate manufacturer mounting-side coordinate grids for the two genders. This is not an electrical net assignment. Native connector footprints and the 90° card/base assembly transform remain unverified. The female flange centerline's 0.3±0.1 mm datum is explicitly retained as an open exact-footprint detail rather than silently aligning its mounting holes with row b.

Two nominal body lengths fit along 220 mm with proposed centers at 55/165 mm: the 94 mm male bodies leave 8 mm outside/16 mm between, and 94.9 mm female bodies leave 7.55 mm outside/15.1 mm between. These are chosen allocation numbers, not supplier placement requirements or completed cage proof.

The selected female's limits are ≤160 N insertion and ≤120 N withdrawal per connector; the two-connector upper sums are 320/240 N. Guides, lever, base support and retention must be accepted against those loads. Exact guide/key/lever/captive-screw parts, edge setbacks, adjacent-card pitch, engagement tolerances and repair-force measurements remain missing. The female explicitly prohibits hot plugging.

PCBWay press-in tooling and finish-dependent plated-hole requirements are an additional closure item. The retained [HARTING 2016 press-in chapter](https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf), printed page 00.25, gives raw Ø1.15±0.025 mm, ≥25 µm copper and different finished-hole ranges by finish. The current review board's assumed 1.6 mm thickness is not a qualified press-in stack-up. These constraints are documented in the ledger; no connector drill files were generated.

## Evidence and handoff

[mechanical.json](../../hardware/motion_card/mechanical.json) records full SHA256 values, source URLs, package bounds, pad identity, connector dimensions, force limits, physical contact maps and unresolved qualification fields. [PACKAGE_GEOMETRY_CHECK.json](PACKAGE_GEOMETRY_CHECK.json) holds the native KiCad and source-workbook evidence. The scratch package-only board and render are verification artifacts under `tmp/pdfs/motion-card-mechanical/`, not production board outputs.

This task performed source inspection, PDF visual inspection, independent workbook comparison, native footprint geometry checks, model numeric bounds and native 3D rendering. It performed no circuit ERC, production board DRC, FPGA synthesis, target compilation, assembly process qualification or physical measurements. It changed no frozen interface files, machine configuration or existing FPGA electrical source. Parent integration must assign the package footprint, copy/remap its model and explicitly adopt the proposed connector correction before routing the real board.
