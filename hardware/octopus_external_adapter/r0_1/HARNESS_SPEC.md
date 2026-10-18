# Matching cable — OEA-H1 r0.1

**DFM candidate; terminal finish and length are not released.** Quote one matching harness per adapter, provisionally five sets.

Full factory harness assembly is a confirmed user requirement. The supplier sources the housing, contacts, conductors, splice, insulation, identification and approved driver-end terminations, then crimps, assembles, labels and tests the complete harness. Deliver each finished harness with its assembled adapter; no customer crimping, splicing, soldering or terminal preparation is part of the requested delivery.

Board end: genuine JST `XHP-4` housing with four `SXH-001T-P0.6` female crimp contacts, mating with `B4B-XH-A(LF)(SN)`. Use **24 AWG stranded copper**, not copper-clad aluminium, with insulation outside diameter within the contact's 0.9–1.9 mm range. Use the manufacturer's specified crimp tooling/process. No pre-tinning of crimped conductors. The family pitch is **2.50 mm**, not 2.54 mm. [JST drawing](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf)

Proposed overall length is **500 ±10 mm**, measured from the plug mating face to each driver termination. Proposed fanout occupies the last **80 mm**. These dimensions are for quotation and must be reconciled with actual driver spacing, routing and strain relief. Colour is supplementary; cavity number and printed terminal label control wiring.

| Cable cavity | Proposed colour | Endpoint labels |
| --- | --- | --- |
| 1 | Red | PUL+, DIR+, ENA+ |
| 2 | White | PUL- |
| 3 | Green | DIR- |
| 4 | Black | ENA- |

Make the cavity-1 conductor branch into three individually insulated red leads using a factory-qualified one-to-three crimp splice or ultrasonic weld. Insulate the joint with appropriately sized heat-shrink and provide strain relief. Each positive lead goes to its own driver terminal. Do not place three wires in one ferrule and do not assume a terminal jumper fits.

Use one individually crimped ferrule per driver lead only after verifying the actual CL57T P1 terminal accepts it. The reviewed manual does not establish the terminal manufacturer's exact MPN, ferrule barrel length, strip length or tightening torque. **Those four details are release gates**; the factory must propose the exact compatible ferrule and terminal preparation for review. Do not tin ends used in a screw clamp. Do not substitute unspecified bare ends for the requested finished harness without updating this controlled specification.

Use a sleeve to keep the four-wire run together and printed heat-shrink identification on all six terminal ends. Mark the harness `OEA-H1 r0.1 — 5 V COMMON+`. The draft is a short cabinet signal harness; its noise immunity and permissible installed length require qualification with the actual equipment. Route apart from motor and power wiring. Any shielded-cable variation needs a defined shield termination and a separate drawing; no shield uses one of the four signal cavities.

The harness supplier's drawing must show the mating-face view, latch side and manufacturer cavity numbers. The board-side view and mating-face view are mirrored; do not populate by a photograph or an assumed left-to-right order. Verify continuity against [cable_pinmap.csv](cable_pinmap.csv), including all three positive branches, before connecting a drive.

Factory inspection: correct contacts and cavity retention; crimp height and pull-force acceptance from the contact/wire process; strain relief and complete splice insulation; six durable endpoint labels; no exposed strands. Test the disconnected harness for all intended connections and unintended shorts. Record the final measured length and continuity result. No high-voltage insulation test may be applied with the adapter or driver attached.
