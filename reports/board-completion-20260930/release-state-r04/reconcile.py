"""Reconcile incomplete release metadata with real partial native evidence.

This neither creates manufacturing files nor marks any full-controller release
gate complete. The old submission checklist is retained as a dated snapshot.
"""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MFG = ROOT/'manufacturing'
manifest_path = MFG/'release-manifest.json'
checklist_path = MFG/'PCBWAY_SUBMISSION_CHECKLIST.md'


def evidence(relative):
    path = ROOT/relative
    if not path.is_file():
        raise ValueError('Missing real evidence '+relative)
    return {'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    archive = HERE/'historical-inputs'
    archive.mkdir(parents=True,exist_ok=False)
    for path in (manifest_path,checklist_path):
        shutil.copyfile(path,archive/path.name)
    doc = json.loads(manifest_path.read_text())
    doc['board_revision'] = 'full-controller-not-frozen'
    doc['manufacturing_ready'] = False
    doc['partial_candidate'] = {
        'scope':'327-part integrated motion card only; not a complete controller',
        'source_revision':'motion-card-r0.4-proposed-IS2',
        'published_native_revision':'20260930-14',
        'erc_violations':0,'drc_regular_violations':0,'drc_pass':False,
        'drc_reported_unconnected_items':499,'uncapped_physical_missing_joins':711,
        'proposed_outline_mm':[220,100],'proposed_copper_layers':6,
        'proposed_thickness_mm':1.6,'final_stackup_qualified':False,
        'evidence':[
            evidence('hardware/board_review/revisions/20260930-14/motion-card-route-candidate.kicad_pcb'),
            evidence('reports/board-completion-20260930/mc-integrated-r04/review.json'),
            evidence('reports/board-completion-20260930/mc-integrated-r04/fresh-native-routing-inventory/review.json')],
        'fabrication_outputs':[],
    }
    changed = {
        'full_schematic':('partial-integrated-motion-card-only',
            'MC r04 has327 fitted parts and source pin parity; compute and full field interfaces are absent.'),
        'pcb_layout':('partial-motion-card-routing-full-controller-incomplete',
            'Real editable native rev14 exists with673 copper items and711 required missing joins.'),
        'erc':('partial-mc-erc-pass-full-controller-pending',
            'Strict MC ERC0 with no ignored checks; incomplete circuitry is not made complete by ERC.'),
        'drc':('partial-mc-drc-fails-unconnected',
            'Strict MC DRC0 regular violations/no ignored checks,499 capped unconnected items; physical inventory711.'),
        'bom':('partial-mc-exact-parts-costing-full-controller-incomplete',
            '327-part designator BOM exists; procurement gaps and complete motherboard/module/manufacture costs remain.'),
        'placement':('partial-mc-placement-candidate-not-assembly-cpl',
            'Native source placement exists; production CPL, mating/clearance and complete board are unfinished.'),
        'fabrication_zip':('blocked-by-incomplete-schematic-routing-and-physical-contract',
            'No placeholder Gerbers/drills/ZIP generated.'),
        'fabrication_spec':('blocked-by-incomplete-design-final-stackup-not-qualified',
            'Six layers/1.6mm are MC layout assumptions, not a final manufacturing stackup.'),
        'assembly_drawing':('blocked-by-incomplete-board-and-mechanical-contract',
            'Native review/3D renders are not a final PCBWay assembly drawing.'),
        'electrical_review':('partial-mc-source-and-native-review-only',
            'Current pin/package/copper reviews retain explicit power/timing/IO/service gaps.'),
    }
    for item in doc['artifacts']:
        if item['id'] in changed:
            item['status'],item['note'] = changed[item['id']]
    manifest_path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    text = '''# PCBWay turnkey submission checklist

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
'''
    checklist_path.write_text(text,encoding='utf-8')
    receipt = {'historical_inputs':[
        evidence((archive/path.name).relative_to(ROOT).as_posix())
        for path in (manifest_path,checklist_path)],
        'current_outputs':[evidence(p.relative_to(ROOT).as_posix()) for p in (manifest_path,checklist_path)],
        'complete_artifacts':sum(a['status']=='complete' for a in doc['artifacts']),
        'manufacturing_ready':False,'supplier_submission':False,'fabrication_outputs':False}
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
