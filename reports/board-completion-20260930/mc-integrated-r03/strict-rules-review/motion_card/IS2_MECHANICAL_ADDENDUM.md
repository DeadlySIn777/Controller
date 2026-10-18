# IS-2 proposed mechanical correction: motion-card HB160 pair

Status: source-backed implementation candidate, 2026-09-30. This addendum proposes a correction to the HB160 entry in IS-1; it does not amend or unfreeze the separate `controller-interface-spec` worktree. An integrated interface revision must reference this correction explicitly. Electrical contact-to-net allocation and cage acceptance remain open.

The fixed wiring base and removable 100 × 220 mm standing motion card remain the required arrangement. P1 and P2 retain 160 contacts each, all five rows and all 32 positions. Existing 272 used/48 spare contact budgets, expansion reservations, power contact limits, identity, presence, diagnostics and eight plus four motor capability are preserved. This correction is mechanical; it adds no feature reduction.

## Correct the mating direction

IS-1 specifies `02041601101` angled female on the card and `02011601101` angled male on the base. HARTING's catalogue identifies **both as angled**. Both mating axes lie within their own PCB planes; they cannot face one another for a perpendicular standing card on a passive flat base. The angled female belongs to the rear-access connector arrangement shown in the catalogue.

The following ordinary daughtercard/backplane arrangement resolves that axis conflict:

| Position | Exact proposed part | Geometry and termination | Source |
|---|---|---|---|
| MC P1 and P2 | HARTING **02011601101** | Male, angled, solder/THR, without retention clip, performance level 1 | HARTING catalogue PDF page 9 / printed 02.11 |
| Fixed base P1 and P2 | HARTING **02021601201** | Female, straight, fixing flange, press-in; a/b/c tails 4.5 mm, z/d tails 5.0 mm, performance level 1 | Catalogue PDF page 10 / printed 02.12 and current exact-part product page |

This is the mating family and orientation used in HARTING's system example. Exact envelope, engagement and cage dimensions still require the final supplier drawings/models and assembled CAD. No interposer is specified. The original angled-female card part must not enter a new procurement BOM by accident.

The catalogue also lists straight female solder part `02021602804`, but it is level 2. It does not meet the retained har-bus requirement of at least 500 cycles. It is not substituted here. PCBWay must qualify press-in tooling, support and plated-hole process for `02021601201` before manufacture.

## Preserve contact identity; distinguish drawing views

Each P1/P2 contact retains its row/position identity: `z1..z32`, `a1..a32`, `b1..b32`, `c1..c32`, `d1..d32`. A mating pair connects like-named contacts. This is a physical identity map, not an invented electrical net assignment.

The source drilling drawings are **mounting-side views**. Define origin at the midpoint of row b positions 16/17, x to the drawing's right and y down. For both parts, `x = (16.5 - position) × 2.54 mm`; position 32 is left and position 1 right. The contact coordinates are:

| Row | Angled male card y, mm | Straight female base y, mm |
|---|---:|---:|
| z | +5.08 | −5.08 |
| a | +2.54 | −2.54 |
| b | 0 | 0 |
| c | −2.54 | +2.54 |
| d | −5.08 | +5.08 |

[mechanical.json](mechanical.json) and [hb160-contact-grid.csv](hb160-contact-grid.csv) contain every contact coordinate and the source hashes. The two drawing grids must be transformed into the standing-card/base assembly views before a native footprint or placement is accepted. Copying one gender's grid directly to the other would reverse the rows.

The male source specifies 88.9 ±0.1 mm flange-hole pitch and Ø2.8 +0.1 mm mounting holes; the female specifies 90.0 ±0.1 mm pitch and Ø2.8 +0.1 mm holes. Their flange holes are separate mounting features, not shared coaxial fasteners. The female drilling drawing has a 0.3 ±0.1 mm flange centerline datum; a footprint must follow it rather than rounding the flange centers onto row b. The ledger deliberately leaves that y-offset unassigned pending the exact component engineering drawing/footprint review.

## Concrete allocation and remaining acceptance

A proposed length allocation sets connector centers at 55 and 165 mm along the 220 mm mating edge. It leaves 8 mm outside the nominal 94.0 mm male bodies and a 16 mm gap; the 94.9 mm female bodies leave 7.55 mm outside and 15.1 mm between. Those center positions are an engineering allocation, not a manufacturer dimension. They demonstrate length feasibility only. Card-edge setbacks, the 100 mm insertion depth, adjacent-card pitch, coding keys, exact guide/lever/captive screw, and collision tolerances remain unclosed.

The exact female product page specifies insertion force ≤160 N and withdrawal ≤120 N per connector, at least 500 cycles and **no hot plugging**. For simultaneous P1/P2, the simple upper sums are 320 N insertion and 240 N withdrawal; these are design bounds, not measured service forces. The lever and supported base must be designed and tested for these loads. Presence contacts and pre-leading contacts do not authorize live replacement.

For the selected press-in base, the retained HARTING press-in chapter specifies raw holes Ø1.15 ±0.025 mm, Cu plating at least 25 µm and finish-dependent finished-hole limits. For Au/Ni, Ag, chemical Sn or OSP, the chapter gives 1.00–1.10 mm finished holes; HAL Sn has a different 0.94–1.09 mm range. Minimum PCB thickness is 1.6 mm. These are supplier process requirements to confirm for the exact part and PCBWay stack-up, not final drill instructions for the present review board.

Primary references: [HARTING har-bus catalogue](https://b2b.harting.com/files/livebooks/en/PRD0200000100183/downloads/livebook.pdf), [exact 02021601201 page](https://www.harting.com/en-US/p/DIN-Signal-harbus64-160FP-45-50C1-1-02021601201), [retained 2016 catalogue / press-in chapter printed 00.25](https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf). The complete downloaded-source ledger is [mechanical.json](mechanical.json).
