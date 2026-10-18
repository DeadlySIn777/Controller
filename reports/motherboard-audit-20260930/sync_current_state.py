"""Archive then reconcile current source/CAD evidence, without changing history."""
from pathlib import Path
import hashlib,json,re,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
FILES=('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md','hardware/board_review/README.md','manufacturing/release-manifest.json','manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md')
archive=OUT/'current-docs-before'
if not archive.exists():
    for rel in FILES:
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
    (archive/'hashes.json').write_text(json.dumps({r:hashlib.sha256((ROOT/r).read_bytes()).hexdigest() for r in FILES},indent=2)+'\n')
original=json.loads((archive/'hashes.json').read_text())
if any(hashlib.sha256((archive/r).read_bytes()).hexdigest()!=h for r,h in original.items()):raise SystemExit('Archive changed')
source='The reconciled electrical source has **980 physical footprints: 960 purchased fitted parts, 18 bare PCB test pads and two DNP footprints**, across twelve source blocks. It includes all twelve motor interfaces, four ABZ receiving paths, 24 DI, 16 smart DO, power-health and actual I/O acquisition/control. Native integrated ERC is **zero errors, 94 warnings, no ignored checks**; 92 isolated-pin labels and two ground-name warnings remain explicitly unresolved. Independent native pin/MPN/footprint and bounded original-pin/topology checks pass, with **19 integration tests passed**. The 100 I/O-control footprints are not yet populated on the published 880-part PCB.'
cad='Published native CAD **20260930-20** contains the frozen **880-footprint / 878 fitted** snapshot, all source-backed. It preserves the original 327 footprints and all **1,907 track/via items and five filled zones**. Independent uncapped connectivity finds **1,637 missing joins**, 81 of 637 multi-pad nets fully joined, 556 incomplete, 3,317 numbered copper pads, 120 native NC pads and no orphan copper. Native DRC reports **zero regular violations, no ignored checks, 499 capped unconnected items**; this is a failing routing result. The **460 × 340 mm, six-layer, 1.6 mm** outline remains provisional; existing planes occupy the retained core region rather than completing the field/whole-board distribution.'
gap='Complete protected entry/power distribution, module sockets, actual field terminals, probes/pendant/process/PWM, analog/comms, status indications and their routing/mechanics remain engineering work. The 20 ms requirement, partial-power behavior, target firmware, vendor FPGA package fit/timing and physical/EMC/thermal qualification are unproved. No Gerbers, drills, assembly CPL/drawings or final stackup have been released; manufacturing_ready remains false. The single active motherboard and all twelve onboard motor interfaces are resolved decisions; old thirteen-card/rack/cage/P1/P2/MX4/XTB requirements are superseded physical history.'
cost='The frozen **980-part source cost snapshot** prices 60 MPNs and leaves 34 unpriced (185 fitted pieces per board). Known-priced consumed component value per board at **1/10/100 units is US$379.67/$314.26/$280.60**, excluding unpriced parts, missing circuits, PCB/assembly/test and purchased compute/ESP/storage/screens. Catalogue cash includes MOQ excess and is not a stock-covered purchasing basket. Every complete manufacture/controller/package total remains null. Bare copper test pads have no purchased part or assembly placement.'
def write(rel,text):(ROOT/rel).write_text(text,encoding='utf8')
def para_replace(text,prefix,replacement):
    pattern=re.escape(prefix)+r'[^\n]*'
    result,n=re.subn(pattern,replacement,text,count=1)
    if n!=1:raise ValueError('Missing paragraph '+prefix)
    return result
for rel in ('docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md'):
    text=(archive/rel).read_text(encoding='utf8')
    prefix='**Current physical implementation:**' if 'BUILD_PLAN' in rel else '**Current implementation boundary:**'
    text=para_replace(text,prefix,prefix+' '+source+' '+cad+' See [current engineering status](../reports/ENGINEERING_STATUS.md).')
    text=text.replace('**Fresh host evidence:**','**Historical post-r0.4 host evidence:**').replace('The [fresh post-r0.4 host snapshot]','The [historical post-r0.4 host snapshot]')
    if 'BUILD_PLAN' in rel:
        text=para_replace(text,'**Current procurement change:**','**Current procurement evidence:** '+cost+' [Exact frozen calculation](../reports/motherboard-cost-20260930/source-980-reviewed/README.md).')
        text=para_replace(text,'The [current 327-part MC r0.4 exact-MPN cost]','The [current motherboard source cost](../reports/motherboard-cost-20260930/source-980-reviewed/README.md) is partial. '+cost+' Earlier 327-part MC r0.4 and r0.3 cost files remain historical subsets.')
    else:
        text=para_replace(text,'The parent r0.4 supervisor packaging','Current source costing preserves the earlier exact H-grade LTC2962HUD#PBF tube substitution. '+cost+' [Frozen calculation](../reports/motherboard-cost-20260930/source-980-reviewed/README.md). Earlier MC costs remain historical subsets.')
    write(rel,text)
memory=(archive/'PROJECT_MEMORY.md').read_text(encoding='utf8')
memory=para_replace(memory,'- **Live physical CAD view','- **Live physical CAD view (30 September 2026):** '+cad+' Keep the same side panel and immutable previous native revisions. [Current board review](hardware/board_review/README.md).')
memory=para_replace(memory,'- **Current engineering execution following that priority:**','- **Current engineering execution following that priority:** '+source+' '+gap+' Source and published PCB counts are different snapshots; do not blend their ERC/DRC counts.')
memory=para_replace(memory,'- **Current exact-MPN sourcing boundary:**','- **Current exact-MPN sourcing boundary:** '+cost+' [Frozen source/cost receipt](reports/motherboard-cost-20260930/source-980-reviewed/README.md). Earlier MC/r0.3 pricing and package-change records are historical evidence.')
memory=memory.replace('- **Fresh current host evidence','- **Historical post-r0.4 host evidence')
write('PROJECT_MEMORY.md',memory)
status=(archive/'reports/ENGINEERING_STATUS.md').read_text(encoding='utf8')
cut=status.index('## Implemented and checked')
historical=status[cut:]
write('reports/ENGINEERING_STATUS.md','# Controller engineering status — 30 September 2026\n\n'+source+'\n\n'+cad+'\n\n'+gap+'\n\n'+cost+'\n\n[Actual exclusive footprint audit](motherboard-audit-20260930/980-after-io-control/README.md), [880-part native receipt](motherboard-pcb-integration-20260930/populated-r02/report.json), [current ERC](motherboard-integration-20260930/r07-980-io-control-erc.json), [independent source validation](motherboard-integration-20260930/r07-980-io-control-validation2.json), [partial costing](motherboard-cost-20260930/source-980-reviewed/README.md), [competitor comparison and qualified ratings](motherboard-audit-20260930/COMPETITIVE_REVIEW.md).\n\n**Test evidence scope:** 19 current root integration and four frozen cost tests pass. The separate block receipts retain their exact focused results. The 869-case/864-pass/five-skip full run under post-r04-host-validation is historical MC evidence, not a fresh 980-source regression. No target firmware compilation, HDL/vendor package fit or physical measurement follows from these host tests.\n\n## Historical runtime and circuit records\n\nThe retained table below preserves prior software/runtime and MC evidence with its original dates/scopes. Its old card/connector allocation and unfinished-module descriptions are superseded where the current integrated source above actually implements them. Six-joint/two-encoder runtime remains historical baseline evidence; twelve physical motor interfaces are not twelve proven coordinated machine axes.\n\n'+historical)
review=(archive/'hardware/board_review/README.md').read_text(encoding='utf8')
start=review.index('## Current published revision:');end=review.index('## Historical initial CAD scope:')
new='## Current published revision: 20260930-20\n\n'+cad+'\n\n'+source+'\n\n'+gap+'\n\nThe native [PCB](revisions/20260930-20/motherboard-populated-candidate.kicad_pcb), [publication](revisions/20260930-20/publication.json), [DRC](revisions/20260930-20/publication-drc.json) and [independent connectivity](revisions/20260930-20/publication-connectivity/review.json) are exact frozen source-backed engineering files. Boxes for modules/terminals are reservations, not fitted connectors. Previous revisions retain their original source, geometry and evidence.\n\n'+cost+'\n\n'
write('hardware/board_review/README.md',review[:start]+new+review[end:])
manifest=json.loads((archive/'manufacturing/release-manifest.json').read_text())
notes={
'full_schematic':('partial-980-motherboard-source-required-circuits-incomplete',source),
'pcb_layout':('partial-880-motherboard-routing-full-controller-incomplete',cad),
'bom':('partial-980-source-cost-required-circuits-and-prices-incomplete',cost),
'placement':('partial-880-source-native-placement-not-assembly-cpl','Required additional circuits and modules/terminals, mating/clearance and production CPL are unfinished.'),
'erc':('partial-980-erc-zero-errors-94-warnings-full-controller-pending','Zero errors, 94 warnings, ignored_checks=[]; circuitry incomplete; warnings remain documented, not suppressed.'),
'drc':('partial-880-drc-fails-connectivity','Zero regular violations/ignored checks,499 capped unconnected items; independent missing joins1637.'),
'electrical_review':('partial-motherboard-source-native-and-topology-review','Original327-pin/copper retention and64 bounded FPGA promotions; actual watchdog-clear-input repair. Power, timing, full I/O and mechanics remain open.')}
for a in manifest['artifacts']:
    if a['id'] in notes:a['status'],a['note']=notes[a['id']]
board='hardware/board_review/revisions/20260930-20/motherboard-populated-candidate.kicad_pcb'
receipt='hardware/board_review/revisions/20260930-20/publication-connectivity/review.json'
manifest['partial_candidate']=dict(scope='880-source-footprint native PCB; newer980 electrical source; required circuits unfinished',source_revision='motherboard-r0.2-IS2-980-source',published_native_revision='20260930-20',electrical_source_footprints=980,native_pcb_footprints=880,purchased_fitted_source_parts=960,bare_test_pad_footprints=18,source_erc_errors=0,source_erc_warnings=94,drc_regular_violations=0,drc_pass=False,drc_reported_unconnected_items=499,uncapped_physical_missing_joins=1637,proposed_outline_mm=[460,340],proposed_copper_layers=6,proposed_thickness_mm=1.6,final_stackup_qualified=False,evidence=[dict(path=r,sha256=hashlib.sha256((ROOT/r).read_bytes()).hexdigest()) for r in (board,receipt)],fabrication_outputs=[])
write('manufacturing/release-manifest.json',json.dumps(manifest,indent=2)+'\n')
check=(archive/'manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md').read_text(encoding='utf8')
end=check.index('## Files and evidence required before turnkey submission')
write('manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md','# PCBWay turnkey submission checklist\n\n30 September 2026. **Not ready for manufacture or supplier submission.** No order/quote request has been made. The adopted single motherboard is resolved; fabrication remains blocked by incomplete source, routing and mechanical/electrical qualification.\n\n'+source+'\n\n'+cad+'\n\n'+gap+'\n\n'+cost+'\n\nThe [release manifest](release-manifest.json) identifies exact partial source and PCB snapshots and marks no full-controller artifact complete.\n\n'+check[end:])
print(json.dumps({'archived':list(FILES),'source_footprints':980,'published_footprints':880,'manufacturing_ready':False}))
