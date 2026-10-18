# Bounded obsolete HOME deallocation

30 September 2026. This isolated native candidate removes twelve obsolete direct FPGA home inputs. The frozen IS-1 inheritance at `modules.json` lines5805–5806 puts homes on the existing DI24/IOL1 contract. It retains G12 PROBE, G15 TOOLSETTER and G16 protective/EXT status, all original 64 new allocations, M4/M6 slow enables, the physical FPGA pad geometry and every other native MPN/footprint/pin connection.

The callable is `apply_obsolete_home_deallocation(root_tree, core_tree, allocation_metadata, native_before, copper_evidence)` in the existing owned FPGA source helper. It returns copied source trees and a bounded ledger; it does not edit the original MC, live motherboard, PCB or parent builder. It requires the actual 66 allocated source pins, exact official ball names/banks, each old HOME net's two native endpoints and hash-anchored zero-copper evidence.

| Old input | Actual FPGA ball | Bank | Old boundary pin |
|---|---|---|---|
| HOME0 | B10 | 3A | J1007.1 |
| HOME1 | B11 | 3A | J1007.2 |
| HOME2 | A11 | 3A | J1007.3 |
| HOME3 | C12 | 3A | J1007.4 |
| HOME4 | C11 | 3A | J1007.5 |
| HOME5 | D12 | 3A | J1007.6 |
| HOME6 | C14 | 3B | J1007.7 |
| HOME7 | D13 | 3B | J1007.8 |
| HOME8 | B16 | 3B | J1007.9 |
| HOME9 | A14 | 3B | J1007.10 |
| HOME10 | E12 | 3B | J1007.11 |
| HOME11 | B14 | 3B | J1007.12 |

All 24 exact source endpoints become native NC/test-only. The old label/wire stubs are removed, with literal UUIDs recorded. Each physical FPGA ball gets its manufacturer-derived NC net name; each obsolete boundary pin gets its exact native NC name. This does not create a wildcard exception. The canonical source resource count changes from **163 assigned /20 free to151 assigned /32 free**. No freed ball is reused and optional encoder extensions are not implemented.

J1007 is **not a physical header on this motherboard**: its native MPN and footprint are empty, it is absent from the physical model and there is no J1007 footprint on the actual CAD23 board. Its old `on_board`/`in_bom` flags and “present” value were misleading legacy boundary attributes. The preserved native symbol/UUID is now explicitly excluded from board and BOM, marked DNP and labeled as an obsolete nonphysical NC/test-only boundary. No purchased part is removed and no header lands are invented.

The actual published CAD23 `motion-card-route-candidate.kicad_pcb`, SHA256 `54c0889735c59f3d516319e50912a1db7b034781b32b1b70984885c2741efba5`, has one U1001 pad and **zero segments, vias and zones on each old HOME net**. The similarly named `motherboard-populated-candidate` file in the revision is the earlier population base; its different hash is not the actual published routed board. The helper checks the correct file.

Native whole-source verification checks all **7,422 pins and1,869 component records** before and after. Only the 12 physical FPGA and12 nonphysical boundary net assignments change. Component identity is exact except J1007's truthful excluded-boundary value. ERC is **zero errors /80 unsuppressed warnings before and after**, with no ignored checks; the warnings are70 isolated labels and10 ground-name warnings inherited from this frozen parent snapshot. Missing footprint-library warnings from the first incomplete report copy are preserved as invalid setup evidence; the complete-library r02 check is authoritative.

All **37 disconnected tests pass**, including the previous26 and11 added mutations. They reject copper/stale receipts, added HOME endpoints, a physical J1007, unbounded allocation prerequisites, incorrect NC names and changes to active probe/EXT nets. `canonical-allocation.json`, the two literal ledgers, independent native report and receipt are the review outputs. This is source reconciliation; parent PCB net reconciliation/DRC, real DI home configuration/runtime, FPGA synthesis/timing and physical validation remain separate work.
