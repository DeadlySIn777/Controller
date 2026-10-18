# FPGA reset buffer physical-pin correction

30 September 2026. The FPGA core is now `fpga-core-r0.3`. U4's Nexperia 74LVC1G17GW symbol, model and actual native conductors have been corrected to **NC1, A2, GND3, Y4, VCC5**. The manufacturer's GW ordering entry selects TSSOP5/SOT353-1; its pin-description Table 3 is the independent source. See [Nexperia's primary datasheet](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf), revision 16.1, pages 2–3, retained with hashes in `after/research/fpga-core/`.

The validator now extracts this manufacturer's table independently and checks both the actual native symbol and connected pins. Four added tests cover the human-reviewed physical pin fixture, actual native conductors, a deliberately mirrored wrong model/check expectation and a native symbol pin swap. An electrically incorrect builder/check pair can no longer pass this particular physical-pin check simply by agreeing with itself.

The drawing's reset reference was corrected from R25/C39 to **R22/C39**. The unproved “bounded post-CDONE delay” wording was replaced with “candidate post-CDONE delay.” R7, R14 and R21 were moved into unused drawing positions to remove overlap with U4/U5; their values, physical component count and net connections were preserved. All five core PNGs were refreshed from the actual native PDF; `reset-detail.png` and the configuration detail were visually inspected for this change.

Actual scoped results:

| Evidence | Result | Limit |
|---|---|---|
| Native KiCad XML netlist | Export succeeded; U4 conductor and symbol pin checks pass | Connectivity and source checks |
| Native KiCad 10.0.4 ERC | **0 violations**, errors and warnings included | Existing four suppressions remain explicitly recorded; no PCB DRC |
| Independent hardware validator | `ok=true`, no errors, `manufacturing_ready=false` | No component or whole-controller qualification |
| Focused host tests using frozen copied source and actual native artifacts | **30 passed; 0 failures, errors or skips** | Host tests, not physical measurements |
| Native schematic PDF | Actual export succeeded; reset/configuration detail visually checked | Intermediate circuit drawing, not a fabrication release |

`commands.json` records exact commands, working directories, UTC times and exit codes. Each command has its actual stdout/stderr files. `review.json` records the resulting physical symbol/functions, conductor mapping, ERC severities and suppressions, changed-file inventory and limits. `before-sha256.json`/`before/` preserve the 22 pre-fix files, including the user's already-dirty source. `after-sha256.json`/`after/` retain the actual final scoped code, circuit source, native artifacts and primary sources. `task-source-diff.patch` compares the three owned code files to the captured pre-fix working files, so it does not falsely attribute earlier uncommitted work to this correction. Fourteen pre-existing files changed; BOM, allocation, project settings, primary source contents and the prior computed validation values did not change.

Only the scoped builder, validator, focused test file, `hardware/fpga_core` regenerated outputs and this new report directory were edited. Historical audit and other immutable evidence directories were preserved. `capture.py` refuses to overwrite the completed receipt. The root task owns connected-assembly regeneration and final combined drawing/report updates.

This closes the identified **physical pin-map defect**, not reset-circuit qualification. Cold/warm discharge, Schmitt thresholds, RC tolerances, service hold/handoff, synchronizers and partial-power behavior remain unqualified. No FPGA vendor placement/routing, bitstream, PCB, DRC, custom hardware or physical test was performed. Twelve STEP/DIR pin reservations are still not twelve complete motor interfaces; IS-1 eight-plus-four/full-I/O circuitry and the independent permission integration remain separate work.
