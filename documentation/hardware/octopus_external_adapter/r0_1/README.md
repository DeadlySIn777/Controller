# Octopus external-driver adapter r0.1

**Engineering candidate for review and PCBWay DFM. Do not build or order from this revision yet.**

This is a separate single-axis StepStick adapter with a keyed four-pin output and a matching factory-made cable. The quote scenario is five assembled adapters and five cables: four axes plus one spare. Quantity and the proposed 500 mm cable length remain provisional.

**Confirmed delivery requirement: full turnkey assembly.** PCBWay is to fabricate the boards, source and fit all 12 components including every connector, manufacture and finish the matching cables, complete the agreed inspections/tests, and deliver depanelled, individually ESD-packed sets. The user receives finished assemblies requiring no soldering or crimping. Installation consists of plugging in each adapter/cable and securing the labelled leads in the driver terminals. This requirement does not change the unresolved compatibility or release gates.

The selected connector pair is a top-mounted JST `B4B-XH-A(LF)(SN)` shrouded header and cable `XHP-4` housing with female contacts. It provides the plug-in connection requested; the PCB header's protected contacts are male. Matching cables will be supplied, so the pictured cable is not assumed compatible.

| J3 cavity | Signal | Driver end |
| --- | --- | --- |
| 1 | +5 V common | Factory splice to PUL+, DIR+, ENA+ |
| 2 | PUL- | PUL- |
| 3 | DIR- | DIR- |
| 4 | ENA- | ENA- |

The candidate uses socket 5 V and an `SN74LVC3G06DCUR` triple open-drain inverter. **The VM contact and plated hole are physically absent**: J1 is an eight-pin header; J2 is a seven-pin header beginning one position lower, at GND. It is based on the **Octopus Pro V1.0 F429/F446** schematic, whose socket control signals are already buffered to 5 V. The user's exact board is unconfirmed. This is not a general 3.3 V-input adapter. The **CL57T V4.1** driver comes from the pasted discussion and also remains unconfirmed.

The **15.24 × 20.32 mm, two-layer** PCB is routed. Final native KiCad 10.0.4 ERC and DRC each report **zero errors and zero warnings**, with **zero unconnected items, zero schematic discrepancies and zero ignored checks**. The independent package check reconciles all **43 pin assignments, 12 components, 11 functional nets**, both header positions and nine SMT placements. Two filled ground copper layers connect the buffer and bypass returns. These are source/CAD results, not measured hardware performance; exact hashes and outstanding gates are in [verification.json](../../../WORKSPACE_REFERENCES.md#artifact-69af94ed95f118bd).

Start with the [actual 3D CAD render](../../../WORKSPACE_REFERENCES.md#artifact-1fa40d037812aa22), [assembly drawing](../../../WORKSPACE_REFERENCES.md#artifact-acdb1dc248330b54), [schematic PDF](../../../WORKSPACE_REFERENCES.md#artifact-51874c34c0a651db), or editable [PCB](../../../WORKSPACE_REFERENCES.md#artifact-0266f8b7171f9216) and [schematic](../../../WORKSPACE_REFERENCES.md#artifact-03e8f44e2ef41af6). The [STEP assembly](../../../WORKSPACE_REFERENCES.md#artifact-ddc59b6f5ce9a9ce) supports mechanical review. The [PCBWay BOM](../../../WORKSPACE_REFERENCES.md#artifact-2a6127b41b469023), [SMT placement file](../../../WORKSPACE_REFERENCES.md#artifact-9af76dd14982e478), [quote draft](PCBWAY_QUOTE_DRAFT.md), [harness specification](HARNESS_SPEC.md), [cable pin map](../../../WORKSPACE_REFERENCES.md#artifact-641aca9618d623af), [cable BOM](../../../WORKSPACE_REFERENCES.md#artifact-85718edb44cdb982), [test plan](FUNCTIONAL_TEST.md), and [sources](SOURCES.md) prepare the review package. All ordering files remain drafts. CPL origin is the lower-left board corner, X right/Y up, millimetres; THT assembly is specified separately.

Prototype order release still needs the exact host and driver identities, socket supply/logic confirmation, populated mechanical fit, driver-terminal/ferrule details, enable polarity and host timing review, and factory DFM/quotation. Quantity and cable length are provisional. The native source/PCB reconciliation is complete for this candidate. Before machine use, a first article requires loaded electrical, pulse, enable, power-sequence and actual-cable tests. The adapter makes no emergency-stop, STO or power-loss inhibition claim; alarm/brake/motor/encoder wiring remains separate.

Gerbers/drills have deliberately not been exported from this unreleased equipment profile. No external submission, quotation, purchase or physical test has occurred. The active twelve-channel controller motherboard, its routing, machine configurations and historical evidence were not edited for this adapter.

The reproducible sources are `build_schematic.py`, `build_pcb.py`, `route_candidate.py` and `package_review.py`. Use KiCad's bundled Python for the PCB scripts. `build_pcb.py` applies saved `routes.json`; changing placement or circuit requires rerouting and fresh native checks. After building, run native DRC with `--refill-zones --save-board --schematic-parity --severity-all`, and native ERC with `--severity-all`. Keep all release gates open until their evidence exists.
