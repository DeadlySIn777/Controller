# BASE FPGA native source reconciliation

The accepted isolated source is `candidate-r03/`. It adds exactly 64 previously NC GPIO connections and their hierarchy ports to the existing native motherboard source. The retained motion-card/FPGA source, live parent schematic and routed PCB were not changed. This is an additive source candidate for root integration, not a completed controller or manufacturing package.

| Evidence | Result |
| --- | --- |
| Reviewed BASE allocation | 161 of 183 user functions, including the existing 50 MHz clock; 22 GPIO remain NC |
| Existing assignments preserved | All 96 assigned GPIO plus clock preserved; optional five-pad reuse not applied |
| New physical connections | Exactly 64 former NC pins, with exact old-to-new native net names |
| FPGA hierarchy ports | 70 before, 134 after |
| Native connectivity audit | 3,173 physical pin nodes before and after; 3,109 unchanged, exactly 64 approved changes |
| Independent physical-net audit | Complete physical node groups agree after the bounded changes; duplicate readable net names rejected |
| Native ERC | 0 errors, **158 warnings**, all `isolated_pin_label`; no suppressed checks |
| Fresh baseline ERC | 0 errors, 36 warnings; the +122 warnings correspond to two labels on each of 61 new singleton FPGA interfaces |
| Existing real root joins | `FPGA_OUTPUT_REQUEST`, `WD_M_OK` and `WD_O_OK` join their actual root nets |
| Manufacturer source | All 256 embedded ball names agree with the official T20F256 v3.5 workbook; bank and worksheet row checked independently |
| Host checks | 21 new mutation/contract tests, 30 retained FPGA tests and 13 fast-input tests pass |
| Native artifacts | KiCad XML netlist, native ERC JSON and nine-page schematic PDF |

The unchanged symbol library remains byte-identical. The GPIO electrical symbol type remains bidirectional because these are programmable physical GPIO; planned signal directions are checked against the reviewed candidate and typed on the hierarchy ports. The reviewed BASE uses LVDS-as-GPIO resources only as 3.3 V digital inputs. Source assignment cannot prove Efinity Interface Designer package legality, timing, bitstream generation or loaded hardware behavior.

## Callable integration

`tools/hardware_apply_motherboard_fpga_allocation.py` provides:

```python
new_root, new_core, metadata = apply_base_allocation(
    root_tree, core_tree, proposal, native_before_xml_tree)
```

It deep-copies both input trees and returns the isolated result. `metadata.exact_pin_rename_ledger` is the complete 64-entry authorization list: reference, ball, manufacturer pin/bank, direction, exact old native NC name and exact new physical net name. There is no wildcard rename exception. A hash of the reviewed pin/function rows prevents silent substitutions. Root retains responsibility for its source model, formal native reconciliation and PCB net assignment.

The root hierarchy repacker only accepts each existing port's simple one-wire/one-label stub. Branches and junctions cause refusal rather than removal. It preserves existing sheet/port/wire UUIDs and names; its layout changes affect the isolated schematic only. `root_sheet_port_map` supplies all 134 exact root names. The helper never modifies existing PCB geometry, pads, rules, planes or copper.

## Actual remaining connections

Three approved semantic aliases preserve the physical historical local nets: G12 `PROBE_FPGA` means `PRB0_FPGA`, G15 `TOOLSETTER_FPGA` means `PRB1_FPGA`, and G16 `PROTECTIVE_STATUS_FPGA` means `EXT_PERMIT_FPGA`. No extra root port was added because the corresponding protected field front ends are not present. Their native nets and original boundary pin connections remain unchanged.

The 61 new singleton interfaces require actual parent bridges or missing circuits. `parent_endpoint_obligations` records the real existing endpoint names and polarity rather than fabricating identities or healthy states. In particular:

- `OPI_REARM_M` must fan out to real `OPI_REARM_TX` and `OPI_REARM_BOE`; A/B OPI circuitry remains separate unfinished work.
- Trip readbacks are physically active-low. The corrected watchdog clear command drives actual `WD_REARM_M/O` inputs of U4018, active-high/default-low. `WD_M/O_TRIP_CLEAR_N` are driven outputs of U4019 and cannot be FPGA command inputs. The original obligation was incorrect; the subsequent audit and preserved correction record supersede it.
- Frequency/MPG receiver endpoints exist on the sixteen-path fast-input region but remain unjoined to these allocated FPGA ports in this isolated candidate.
- Authentic rail, per-bank power, OPI and health-register circuits still require completion; no constant-healthy source is introduced.
- Gateware is still historical evidence. Full twelve-motor/four-encoder plus new interfaces, package fit, timing and a bitstream are not implemented by this source transformation.

Native ERC is **not clean** and has not been suppressed. The warning ledger preserves the unfinished parent connections for root to close. Routing, DRC, manufacturing exports, cost and physical validation are outside this source-only candidate.

## Rejected diagnostics and visual review

`rejected-candidates.json` records earlier isolated diagnostic failures. In the first candidate, renaming only one occurrence of each probe alias split existing physical groups while retaining duplicate readable names. The strengthened checker now rejects that exact failure. The second candidate preserved the groups but exported three unnecessary dangling aliases and failed ERC. These diagnostic directories are retained for provenance and are not approved source.

The accepted PDF's root and FPGA pages were rendered and visually inspected as `accepted-root.png` and `accepted-fpga.png`. All eight sibling pages fit on the root A0 sheet, and new port wires/labels remain within the FPGA page. This is visual source inspection, not mechanical/PCB inspection.
