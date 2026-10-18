"""Record actual current receipts while preserving historical engineering text."""
import collections,hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(r):return json.loads((ROOT/r).read_text())
model=load('hardware/motherboard/design.json');n=len(model['components']);assert n==1585
publication=load('hardware/board_review/revisions/20260930-21/publication.json')
erc=load('reports/motherboard-integration-20260930/r13-1585-modules-erc.json')
vs=[v for s in erc['sheets'] for v in s['violations']];assert not any(v['severity']=='error' for v in vs)
tp=sum(c.get('kind')=='TP' for c in model['components'].values());purchased=sum(not c.get('dnp',False) and c.get('kind')!='TP' for c in model['components'].values())
source=f'The reconciled electrical source has **{n} physical footprints: {purchased} purchased fitted parts, {tp} bare PCB test pads and two DNP footprints**, across eighteen source blocks. It contains all twelve motor interfaces, four ABZ receiving paths, 24 DI, 16 smart DO, power-health, actual I/O controllers, protected power entry, probe/pendant supplies, purchased-module compute/ESP sockets and process control with its fourth actual acquisition controller. Native integrated ERC is **zero errors, 72 warnings, no ignored checks** (70 isolated-pin labels and two ground-name warnings). Independent native fitted pin/MPN/footprint and exact original-pin/topology checks pass. The 23 root integration, 26 FPGA allocation, 33 ACC, 35 process and 10 ESP focused tests pass; these do not prove firmware execution or physical behavior.'
cad='Published native CAD **20260930-21** contains the separate frozen **880-footprint / 878 fitted** snapshot. It preserves the original 327 footprints, **2,088 track/via items and five filled zones**. Independent uncapped connectivity finds **1,600 missing joins**. Native DRC reports **zero regular violations, no ignored checks and 499 capped unconnected items**; routing fails. The **460 × 340 mm, six-layer, 1.6 mm** outline remains provisional; existing planes cover the retained core rather than the whole motherboard.'
gap='The additional source parts are being populated onto the existing PCB without discarding its routed copper. Storage and compute raw peripherals, analog/comms, status indicators, actual field terminals, complete power/return routing and mechanical/thermal reconciliation remain engineering work. Logic-rail startup load and monitor-window corrections are under review. The 20 ms inhibit requirement, partial-power behavior, target firmware, vendor FPGA package fit/timing and physical/EMC/thermal qualification remain unproved. Gerbers, drills, final assembly CPL/drawings and a final stackup have not been released; manufacturing_ready remains false. Original six-joint/two-encoder runtime results remain historical baseline evidence; twelve fitted interfaces are not twelve proven coordinated axes.'
cost='Only the frozen **980-part subset** has a partial cost calculation: 60 priced MPNs, 34 unpriced and 185 unpriced fitted pieces. Known-priced consumed component value per board at **1/10/100 is US$379.67/$314.26/$280.60**, excluding unpriced parts, later required circuits, PCB/assembly/test and purchased modules/screens. This is not the complete current BOM cost. Every complete manufacturing/controller/package total remains null.'
archive=ROOT/'reports/motherboard-audit-20260930/before-1585-doc-sync';archive.mkdir()
files=['PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md','hardware/board_review/README.md','manufacturing/release-manifest.json','manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md']
for r in files:
    target=archive/r;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/r,target)
def write(r,t):(ROOT/r).write_text(t,encoding='utf8')
def replace(t,prefix,new):
    t,count=re.subn(re.escape(prefix)+r'[^\n]*',lambda _:new,t,count=1)
    if count!=1:raise ValueError('Missing exact paragraph '+prefix)
    return t
mem=(ROOT/'PROJECT_MEMORY.md').read_text()
mem=replace(mem,'- **Live physical CAD view','- **Live physical CAD view (30 September 2026):** '+cad+' Keep the same side panel and immutable revisions. [Current board review](hardware/board_review/README.md).')
mem=replace(mem,'- **Current engineering execution following that priority:**','- **Current engineering execution following that priority:** '+source+' '+gap+' Source and published PCB snapshots are distinct.')
write('PROJECT_MEMORY.md',mem)
for r,prefix in [('docs/BUILD_PLAN.md','**Current physical implementation:**'),('docs/PLATFORM_ROADMAP.md','**Current implementation boundary:**')]:
    write(r,replace((ROOT/r).read_text(),prefix,prefix+' '+source+' '+cad+' '+gap))
status=(ROOT/'reports/ENGINEERING_STATUS.md').read_text();history=status[status.index('## Historical runtime and circuit records'):]
write('reports/ENGINEERING_STATUS.md','# Controller engineering status — 30 September 2026\n\n'+source+'\n\n'+cad+'\n\n'+gap+'\n\n'+cost+'\n\n[Current source acceptance](motherboard-integration-20260930/r13-1585-adoption.json), [native ERC](motherboard-integration-20260930/r13-1585-modules-erc.json), [independent native checks](motherboard-integration-20260930/r13-1585-independent-validation.json), [exclusive function audit](motherboard-audit-20260930/1585-process-compute-source/README.md).\n\n**Full regression scope:** the last complete disconnected run remains the immutable 980-source run: 1,070 reported, 1,065 passed and five Windows LinuxCNC symlink cases skipped, with 1,636 scoped hashes unchanged. Later source changes have focused native/host checks and need a fresh full run. Source inspection, host tests, target compilation, HDL simulation, FPGA synthesis, circuit ERC, PCB DRC and measurements are distinct evidence.\n\n'+history)
review=(ROOT/'hardware/board_review/README.md').read_text();start=review.index('## Current published revision:');end=review.index('## Historical initial CAD scope:')
write('hardware/board_review/README.md',review[:start]+'## Current published revision: 20260930-21\n\n'+cad+'\n\n'+source+'\n\n'+gap+'\n\n[Native PCB](revisions/20260930-21/motherboard-populated-candidate.kicad_pcb), [publication receipt](revisions/20260930-21/publication.json), [uncapped connectivity](revisions/20260930-21/publication-connectivity/review.json).\n\n'+review[end:])
manifest=load('manufacturing/release-manifest.json')
notes={'full_schematic':('partial-1585-source-required-circuits-incomplete',source),'pcb_layout':('partial-880-routing-full-controller-incomplete',cad),'bom':('partial-current-designator-bom-full-cost-incomplete',cost),'placement':('partial-880-source-placement-not-production-CPL',gap),'erc':('partial-1585-erc-zero-errors-72-warnings','No ignored checks; full circuitry and isolated labels remain unresolved.'),'drc':('partial-880-drc-fails-connectivity','Zero regular violations;1600 uncapped missing joins;499 capped reported items.'),'electrical_review':('partial-native-review-full-electrical-gates-unfinished',gap)}
for row in manifest['artifacts']:
    if row['id'] in notes:row['status'],row['note']=notes[row['id']]
p=manifest['partial_candidate'];p.update(scope='880-source PCB; newer1585 electrical source; required circuits unfinished',source_revision='motherboard-IS2-1585-source',published_native_revision='20260930-21',electrical_source_footprints=n,purchased_fitted_source_parts=purchased,bare_test_pad_footprints=tp,source_erc_errors=0,source_erc_warnings=72,uncapped_physical_missing_joins=1600)
p['evidence']=[dict(path=r,sha256=hashlib.sha256((ROOT/r).read_bytes()).hexdigest()) for r in ['hardware/board_review/revisions/20260930-21/motherboard-populated-candidate.kicad_pcb','hardware/board_review/revisions/20260930-21/publication-connectivity/review.json']]
write('manufacturing/release-manifest.json',json.dumps(manifest,indent=2)+'\n')
check=(ROOT/'manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md').read_text();tail=check[check.index('## Files and evidence required before turnkey submission'):]
write('manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md','# PCBWay turnkey submission checklist\n\n**Not ready for manufacture or supplier submission.** No purchase or supplier submission has occurred.\n\n'+source+'\n\n'+cad+'\n\n'+gap+'\n\n'+cost+'\n\n'+tail)
print(json.dumps(dict(electrical_source=n,purchased=purchased,testpads=tp,PCB=880,missing_joins=1600,manufacturing_ready=False)))
