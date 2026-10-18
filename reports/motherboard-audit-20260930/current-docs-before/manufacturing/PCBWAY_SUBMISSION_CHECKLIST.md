# PCBWay turnkey submission checklist

Current reconciliation: 30 September 2026. **Not ready for manufacture or supplier submission.** The complete controller has no frozen manufacturing board revision; the published native `20260930-14` is a partially routed327-part MC r0.4 only. No order or quote request has been made.

The [readiness report](../reports/board-completion-20260930/READINESS.md) gives current source/native/test/cost evidence and separates unfinished engineering from physical validation and purchasing. The [release manifest](release-manifest.json) now identifies the real partial native PCB instead of claiming no layout exists. It marks no full-controller artifact complete.

Current strict MC ERC has zero violations and no ignored checks. Strict native DRC has zero regular violations and499 capped unconnected items; independent physical connectivity reports711 missing joins. This is a failing routing result. Source assignments cover327 footprints; circuits, full pin allocation, connectors, planes, stackup/process and target integration remain incomplete.

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
