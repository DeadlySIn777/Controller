# Independent review of initial 327-part motor placement

30 September 2026. This receipt freezes the initial staged **20260930-07** placement and integrated five-block MC source state. It is historical input to the pin-aware placement repair; it does not approve these motor positions for routing, signal integrity or manufacture. No shared circuit source, staged board or existing revision was changed during this read-only review.

The native board has **327 footprints**, matching 327 physical BOM rows. All **124 new motor-buffer footprints and 362 physical pads** match the integrated native netlist and their independently checked source/BOM. The four logical boundary symbols acquired no footprint. All **203 previous footprint geometries and positions remain unchanged**. Three retained components acquire expected electrical net-name changes when existing STEP/DIR/enable signals and the actual qualified BOE become shared between sheets; those are recorded separately from geometry changes.

[Native inspection](native-inspection.json) records actual pad coordinates, dimensions, package orientation, copper names, bypass distances, series distances and primary-source hashes. [Series-distance CSV](series-pad-distances.csv) gives all 38 output paths. [Drawing inspection](drawing-inspection.json) checks the top-level five rectangles and exported six-page PDF. [The frozen receipt](review.json) records verified copied input hashes and output hashes.

## Actionable placement findings

**Move each source-series resistor to its actual physical Y pad before routing.** The initial packer anchors every series resistor to the right of the IC, while several physical 244A outputs are on the left. These are straight-line pad-center distances; a routed path can only be longer:

| Signal | Buffer output → resistor raw-side pad | Minimum connection length |
|---|---|---:|
| DIR2 | U5001 pin 3 → R5008 pin 1 | 12.093574 mm |
| EN1_N | U5001 pin 7 → R5006 pin 1 | 11.914887 mm |
| DIR7 | U5003 pin 5 → R5023 pin 1 | 11.769432 mm |
| STEP7 | U5003 pin 7 → R5022 pin 1 | 11.578624 mm |
| STEP2 | U5001 pin 5 → R5007 pin 1 | 11.542077 mm |

These unnecessarily long raw-output paths undermine the intended source-termination placement. The repair should anchor to the actual physical output pad and orient the resistor's **pin 1** toward that pad. It must retain the source net on pin 1 and receiving net on pin 2, then route and qualify loaded edges. This finding does not claim that an unmeasured 12 mm connection already causes a failing waveform, nor that a particular shorter length proves signal integrity.

**Tighten the seven small-buffer bypass placements and provide immediate ground-plane returns.** Each 244A VCC pin 20 to C5001–C5004 pin 1 is 1.616178 mm. Six 2G126 VCC pin 8 to bypass pin 1 distances are 3.727348 mm; U5008/C5008 is 3.254708 mm. Their generic `IC center +4/−4 mm` targets do not use the actual VCC pad. Anchor those capacitors to VCC and minimize the electrical loop with a reviewed adjacent ground return. Direct cap-ground to package-ground distances are 10.651856 mm for 244A and 6.324012–7.790579 mm for 2G126; an appropriately placed plane return changes the real loop, so these straight-line distances are not a measured loop inductance. All eleven capacitors connect pin 1 to IO_3V3 and pin 2 to LOGIC_GND correctly.

## Package geometry checked against primary drawings

All eleven ICs are on F.Cu at 0° with pin 1 upper left. TSSOP pins 1–10 progress downward on the left and 20–11 downward on the right, with **0.65 mm pitch**. VSSOP pins 1–4 progress downward on the left and 8–5 downward on the right, with **0.50 mm pitch**. Supplies are the actual physical pins: 244A VCC 20/GND 10, 2G126 VCC 8/GND 4. No spacing, mirrored numbering or pin-function defect was found in the imported stock footprints.

The stock footprints are **alternate IPC landpatterns, not exact copies of TI's examples**:

| Package | Actual KiCad pads / row-center separation | TI example pads / row-center separation |
|---|---|---|
| PW0020A TSSOP-20 | 1.475 ×0.400 mm / 5.725 mm | 1.500 ×0.450 mm / 5.800 mm |
| DCU0008A VSSOP-8 | 1.250 ×0.350 mm / 2.800 mm | 0.850 ×0.300 mm / 3.100 mm |

Same-column copper gaps are 0.250 mm and 0.150 mm respectively before any process-specific mask expansion. TI explicitly allows alternate IPC-7351 designs; a numerical difference alone does not establish a defect. Assembly owner review of heel/toe, paste, mask web, placement tolerances and the selected PCBWay process remains required. These stock patterns must not be described as identical to the manufacturer's example. Primary evidence is TI SN74LVC244A PW0020A outline/layout on PDF pages 33–35 and SN74LVC2G126 DCU0008A outline/layout on pages 21–23, retained and hashed in this receipt. [TI 244A](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf), [TI 2G126](https://www.ti.com/lit/ds/symlink/sn74lvc2g126.pdf).

## Drawing and verification boundary

The root A0 drawing contains **all five non-overlapping hierarchical sheet rectangles**, including the new motor-buffer sheet. The exported PDF contains the root plus five children: four A0 pages and two A1 pages. No extracted text lies outside any PDF page. All pages were rendered; the top-level and motor-sheet overviews were visually inspected. Those two overviews confirm that the fifth block fits and the motor circuit remains visible and legible when zoomed.

The retained native DRC report contains **zero non-unconnected violations and 499 unconnected items**. Its zero geometry violations do not close the placement priorities above. The integrated native ERC report contains zero violations; this review inspects the retained report, rather than claiming a new ERC invocation. No board was modified, no broad regression was run, no receiver/card interfaces were added, and no physical measurement or manufacturer assembly approval is claimed.
