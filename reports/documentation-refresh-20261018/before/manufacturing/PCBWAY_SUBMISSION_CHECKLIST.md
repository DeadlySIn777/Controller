# PCBWay turnkey submission checklist

**Not ready for manufacture or supplier submission.** No purchase or supplier submission has occurred.

**Readiness reconciliation begun 3 October 2026:** Claude owns active routing. The following is the last verified adopted **Source26/ROOT104, published CAD30** baseline, not a claim that in-progress routing is complete. [Fresh audit and provenance checks](../reports/readiness-reaudit-20261003/README.md).

The source and published board contain **2,688 footprints**: 2,642 purchased fitted parts, 44 bare PCB features and two DNPs. Required motor/I/O and remaining interfaces are represented in source. Recorded native Source26 ERC is **0 errors/70 unsuppressed warnings**, with [exact warning dispositions](../reports/motherboard-erc-20261002/source26-exact-warning-disposition-r01/receipt.json). Source representation does not establish target execution or physical qualification.

The adopted and published native boards share SHA-256 `70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc`: **11,807 track/via items, 1,544 zones/rule areas, 633 fully joined and 1,101 incomplete multi-pad nets, 3,508 required joins**. Recorded regular DRC is **0 errors/0 warnings/no ignored checks**, with zero orphan copper; connectivity completion fails. The **460 × 340 mm, six-layer, 1.6 mm** stackup remains provisional. These native results were not rerun in this readiness audit.

**Source27 reset/health corrections remain staged and unadopted.** Reconcile them with the routing owner's returned successor before electrical/physical release; do not overwrite ongoing routing or silently merge old candidates. The [drill/land audit](../reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json) retains **274 vias intersecting 277 same-net paste SMD lands**, a lower bound excluding tangency/registration margins. Correct geometry or qualify the exact filled/capped fabrication and assembly process; tenting and ordinary DRC do not close this issue.

Full power/return, complete 20 ms inhibit/defaults, actual CNC3/HAL/local-I/O authority, record trust/provisioning, analog chain, exact FPGA vendor fit/timing, mechanics, target load and physical/EMC/thermal qualification remain unfinished. The later report-local FPGA resource optimization is not an adopted complete device implementation. Gerbers, drills, production CPL/drawings, programming/test bundle and final stackup have not been released. **Manufacturing readiness remains false.** Historical six-joint/two-encoder runtime is not twelve proven coordinated axes.

The immutable [Source26 partial cost audit v11](../reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11/README.md) prices 105 exact MPNs; **185 MPNs/720 purchased fitted pieces remain unpriced**. Known-priced consumed parts per board at **1/10/100 are US$1,091.51/$877.37/$796.51**. Purchased modules, displays, fabrication, assembly, programming/test, enclosure and packaging remain separate unknowns. Complete manufactured controller/package totals remain unknown; this is not a PCBWay quotation. Earlier 980-part and CAD21 figures are preserved in [the pre-audit checklist](../reports/readiness-reaudit-20261003/before-docs/manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md).

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
