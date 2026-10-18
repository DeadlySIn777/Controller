# PCBWay quote draft — OEA r0.1

**CANDIDATE FOR DFM — DO NOT BUILD.** Local draft, not submitted. No price or lead time has been obtained.

Request a separately itemized turnkey quote for **five assembled single-axis adapter boards and five matching harnesses**. This provisional quantity represents four axes and one spare; it is not a confirmed purchase quantity. Cable length is provisionally 500 mm.

**User-confirmed scope: full turnkey PCB and harness assembly.** Include PCB fabrication, procurement of every BOM item, all nine SMT parts and all three THT connectors fitted, complete cable manufacture/termination, inspection and the agreed functional/continuity tests. Deliver finished sets with no customer soldering, connector fitting, crimping or splice work. PCBWay must include or coordinate harness manufacture as part of this quote; do not treat cables as customer-supplied parts or omit them from the total. Driver-end ferrules/terminations must be resolved before manufacture so that all six labelled leads arrive finished for the identified driver terminals.

| Field | Draft request |
| --- | --- |
| PCB | Two layers; FR-4; 1.6 mm finished thickness; 1 oz finished outer copper |
| Finish | ENIG |
| Appearance | Green soldermask; white silkscreen; retain pin-1, orientation, revision and signal labels |
| Assembly | Full turnkey components, top SMT, top JST THT connector, bottom J1 1x8 and J2 1x7 THT plug headers; upper-right VM position intentionally blank |
| Panel | Panel by PCBWay; factory-designed rails/fiducials; DFM review before manufacture |
| Delivery | Complete sets: depanelled, inspected, tested and individually ESD-packed assembled boards, each paired with its separately identified finished and tested cable |
| Substitutions | Exact MPNs first; submit any alternatives for electrical/footprint/mechanical review before sourcing |
| Testing | Quote the agreed scope from FUNCTIONAL_TEST.md; identify fixture, setup and per-unit costs separately |
| Cable | Factory crimped JST XH four-pin plug, insulated common-positive fanout and six individually labelled driver ends |

Quote PCB fabrication, setup/stencil, parts, SMT/THT assembly, depaneling, harnesses, functional test/fixture, packing and shipping separately. State currency, quantity, validity, lead time and procurement exceptions. No firmware programming is needed for this adapter.

The eventual submission must contain generated Gerbers and drills from the released board, exact fitted BOM, SMD centroid/CPL in millimetres, and legible top/bottom/side assembly drawings. CPL must record board side and rotation. THT headers remain in the BOM and assembly drawings; they must not be silently omitted because the SMD placement file excludes them. Final source/board hashes and evidence will identify the released revision.

**Header orientation is critical:** J1 is the left eight-pin Würth `61300811121`; J2 is the right seven-pin Würth `61300711121`, starting one socket position lower. Viewed from the top, EN is upper left and the upper-right VM position has neither a contact nor a plated pad. Both headers' insulating bodies are below the PCB, with their long mating pins pointing down into the host. J3 is on top and accepts the cable vertically. Final drawings must state mating length, seating height, row separation and pin-1 positions. Obtain a first-article assembly photograph before any repeated assembly.

For the small board, let PCBWay review panelization and depaneling clearance around components. Do not enlarge the individual outline or change header positions to suit a panel. Obtain confirmation of the final individual-board outline, edge quality and any tab remnants because adjacent driver slots constrain fit.

**Open before build release:** actual host/driver identity; input logic and 5 V rail budget; populated mechanical fit; final ERC, DRC and schematic-to-PCB agreement; exact driver terminal and ferrules; cable length/quantity; measured enable/power-sequence behaviour; functional acceptance limits; factory DFM; accepted complete quotation. Native clean checks alone do not verify a physical fit or driver behaviour.

PCBWay's published [file requirements](https://www.pcbway.com/assembly-file-requirements.html), [panel guidance](https://www.pcbway.com/pcb_prototype/Panel_Requirements_for_Assembly.html), and [assembly quote options](https://www.pcbway.com/quotesmt.aspx) support this package. Final panel requirements remain subject to their review.
