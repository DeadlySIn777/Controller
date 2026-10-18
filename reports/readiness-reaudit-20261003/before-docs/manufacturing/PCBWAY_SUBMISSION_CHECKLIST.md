# PCBWay turnkey submission checklist

**Not ready for manufacture or supplier submission.** No purchase or supplier submission has occurred.

The reconciled electrical source has **1585 physical footprints: 1557 purchased fitted parts, 26 bare PCB test pads and two DNP footprints**, across eighteen source blocks. It contains all twelve motor interfaces, four ABZ receiving paths, 24 DI, 16 smart DO, power-health, actual I/O controllers, protected power entry, probe/pendant supplies, purchased-module compute/ESP sockets and process control with its fourth actual acquisition controller. Native integrated ERC is **zero errors, 72 warnings, no ignored checks** (70 isolated-pin labels and two ground-name warnings). Independent native fitted pin/MPN/footprint and exact original-pin/topology checks pass. The 23 root integration, 26 FPGA allocation, 33 ACC, 35 process and 10 ESP focused tests pass; these do not prove firmware execution or physical behavior.

Published native CAD **20260930-21** contains the separate frozen **880-footprint / 878 fitted** snapshot. It preserves the original 327 footprints, **2,088 track/via items and five filled zones**. Independent uncapped connectivity finds **1,600 missing joins**. Native DRC reports **zero regular violations, no ignored checks and 499 capped unconnected items**; routing fails. The **460 × 340 mm, six-layer, 1.6 mm** outline remains provisional; existing planes cover the retained core rather than the whole motherboard.

The additional source parts are being populated onto the existing PCB without discarding its routed copper. Storage and compute raw peripherals, analog/comms, status indicators, actual field terminals, complete power/return routing and mechanical/thermal reconciliation remain engineering work. Logic-rail startup load and monitor-window corrections are under review. The 20 ms inhibit requirement, partial-power behavior, target firmware, vendor FPGA package fit/timing and physical/EMC/thermal qualification remain unproved. Gerbers, drills, final assembly CPL/drawings and a final stackup have not been released; manufacturing_ready remains false. Original six-joint/two-encoder runtime results remain historical baseline evidence; twelve fitted interfaces are not twelve proven coordinated axes.

Only the frozen **980-part subset** has a partial cost calculation: 60 priced MPNs, 34 unpriced and 185 unpriced fitted pieces. Known-priced consumed component value per board at **1/10/100 is US$379.67/$314.26/$280.60**, excluding unpriced parts, later required circuits, PCB/assembly/test and purchased modules/screens. This is not the complete current BOM cost. Every complete manufacturing/controller/package total remains null.

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
