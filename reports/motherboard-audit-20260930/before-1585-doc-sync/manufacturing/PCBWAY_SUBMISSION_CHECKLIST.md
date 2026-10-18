# PCBWay turnkey submission checklist

30 September 2026. **Not ready for manufacture or supplier submission.** No order/quote request has been made. The adopted single motherboard is resolved; fabrication remains blocked by incomplete source, routing and mechanical/electrical qualification.

The reconciled electrical source has **980 physical footprints: 960 purchased fitted parts, 18 bare PCB test pads and two DNP footprints**, across twelve source blocks. It includes all twelve motor interfaces, four ABZ receiving paths, 24 DI, 16 smart DO, power-health and actual I/O acquisition/control. Native integrated ERC is **zero errors, 94 warnings, no ignored checks**; 92 isolated-pin labels and two ground-name warnings remain explicitly unresolved. Independent native pin/MPN/footprint and bounded original-pin/topology checks pass, with **19 integration tests passed**. The 100 I/O-control footprints are not yet populated on the published 880-part PCB.

Published native CAD **20260930-20** contains the frozen **880-footprint / 878 fitted** snapshot, all source-backed. It preserves the original 327 footprints and all **1,907 track/via items and five filled zones**. Independent uncapped connectivity finds **1,637 missing joins**, 81 of 637 multi-pad nets fully joined, 556 incomplete, 3,317 numbered copper pads, 120 native NC pads and no orphan copper. Native DRC reports **zero regular violations, no ignored checks, 499 capped unconnected items**; this is a failing routing result. The **460 × 340 mm, six-layer, 1.6 mm** outline remains provisional; existing planes occupy the retained core region rather than completing the field/whole-board distribution.

Complete protected entry/power distribution, module sockets, actual field terminals, probes/pendant/process/PWM, analog/comms, status indications and their routing/mechanics remain engineering work. The 20 ms requirement, partial-power behavior, target firmware, vendor FPGA package fit/timing and physical/EMC/thermal qualification are unproved. No Gerbers, drills, assembly CPL/drawings or final stackup have been released; manufacturing_ready remains false. The single active motherboard and all twelve onboard motor interfaces are resolved decisions; old thirteen-card/rack/cage/P1/P2/MX4/XTB requirements are superseded physical history.

The frozen **980-part source cost snapshot** prices 60 MPNs and leaves 34 unpriced (185 fitted pieces per board). Known-priced consumed component value per board at **1/10/100 units is US$379.67/$314.26/$280.60**, excluding unpriced parts, missing circuits, PCB/assembly/test and purchased compute/ESP/storage/screens. Catalogue cash includes MOQ excess and is not a stock-covered purchasing basket. Every complete manufacture/controller/package total remains null. Bare copper test pads have no purchased part or assembly placement.

The [release manifest](release-manifest.json) identifies exact partial source and PCB snapshots and marks no full-controller artifact complete.

## Files and evidence required before turnkey submission

- Reconciled complete-controller schematic, exact pin/bank/terminal maps, power/fault/default-state review and actual electrical limits.
- Fully routed native PCB, zero required unconnected joins, native ERC/DRC with justified documented exceptions only, independent connectivity and mechanical/mating review.
- Final approved stackup, copper weights, material/thickness/finish, impedance/clearance/via/process rules and board outline.
- Real Gerbers, drill data and fabrication ZIP from that exact released board.
- Exact fitted-parts PCBWay BOM, origin/orientation-verified CPL and assembly drawings; distinguish purchased compute/ESP/storage/display modules and incomplete costs.
- Exact programmed BOM lines, versioned images, recovery procedure, actual FPGA package fit/timing, compatible compute images and safe startup/service behavior.
- Bounded motion-link measurements before final layout, bring-up/proof-test limits, fixture/programming/functional-test scope, and subsequent physical qualification.
- PCBWay quote tied to those exact files and quantities1/10/100/1,000; purchasing terms and any order remain separate actions.

Current design has none of the released Gerber/drill/CPL/assembly/stackup package. Review PDFs and3D renders are engineering evidence; they must not be renamed as factory-ready files. The [original28September checklist](../reports/board-completion-20260930/release-state-r04/historical-inputs/PCBWAY_SUBMISSION_CHECKLIST.md) retains the earlier repository inventory, supplier requirements and open tasks as historical evidence. Its claims that no PCB or hierarchical assembly existed are superseded, and its older user-choice list does not reopen decisions already recorded in project memory.

Supplier reference requirements remain linked in that retained checklist. Current manufacturer capability, source availability and final pricing must be verified for the actual completed package before submission. No supplier communication, upload, purchase or fabrication output is performed by this reconciliation.
