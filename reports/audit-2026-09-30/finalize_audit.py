"""Bind completed audit artifacts and intentional document edits without rerunning engineering checks."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
before=json.loads((HERE/'source-before.json').read_text(encoding='utf-8'))
changed=[name for name, value in before.items() if not (ROOT/name).exists() or sha(ROOT/name)!=value]
implementation_roots=('cnc1/','controller_backend/','controller_config/','controller_lab/','firmware/','gateware/','hardware/','tests/','tools/','manufacturing/')
implementation_changed=[name for name in changed if name.startswith(implementation_roots)]
assert not implementation_changed, implementation_changed
core=json.loads((HERE/'requirements-core-trace.json').read_text(encoding='utf-8-sig'))
features=json.loads((HERE/'feature-implementation-map.json').read_text(encoding='utf-8'))['features']
assert len(core)==64 and len({r['id'] for r in core})==64
assert [r['id'] for r in features]==[f'F{i:03}' for i in range(1,201)]
source=json.loads((ROOT/'research/architecture-source/source.json').read_text(encoding='utf-8'))
assert sha(ROOT/source['archive_path'])==source['sha256']==sha(Path(source['original_path']))
archive=ROOT/'reports/processor-hardware-20260929'
archive_record=json.loads((archive/'review.json').read_text(encoding='utf-8'))['input_sha256']
archive_errors=[name for name,value in archive_record.items() if sha(archive/'source'/name)!=value]
assert not archive_errors, archive_errors
archive_current_diff=[name for name,value in archive_record.items() if sha(ROOT/name)!=value]
assert all(name.startswith('reports/') for name in archive_current_diff), archive_current_diff
weights=[('requirements_interface',5,5),('motion_runtime_transport',10,20),('electrical_protection_diagnostics',6,20),
         ('touch_model_commissioning',1,15),('configuration_persistence_service',6,10),('esp_ai',2,5),
         ('compute_display',1,5),('cost_manufacture',1,10),('target_physical_verification',2,5),('commercial_release',1,5)]
assert sum(x[1] for x in weights)==35 and sum(x[2] for x in weights)==100
score={'date':'2026-09-30','overall_engineering_completion':35,'requirements_accounting_after_reconciliation':92,
       'meaning':'Judgment rubric for requested complete sellable controller; not reliability probability or certification',
       'manufacturing_ready':False,'sale_ready':False,'rubric':[{'area':a,'earned':e,'weight':w} for a,e,w in weights],
       'requirements_before_reconciliation':76,'current_product_gates':'docs/CURRENT_ACCEPTANCE_GATES.md'}
(HERE/'rating.json').write_text(json.dumps(score,indent=2)+'\n',encoding='utf-8')
records={}
for folder in (HERE,ROOT/'research/architecture-source'):
    for path in folder.glob('*'):
        if path.is_file() and path.name!='final-audit-state.json':records[path.relative_to(ROOT).as_posix()]=sha(path)
for name in ('PROJECT_MEMORY.md','README.md','PROJECT_BRIEFING.md','docs/CURRENT_ACCEPTANCE_GATES.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md',
             'docs/DISPLAY_TIERS.md','docs/EXPANDED_HARDWARE_TARGET.md','docs/MOTION_EXPANSION_8_TO_12.md','docs/MODULAR_REPAIR_AND_MEMORY.md',
             'docs/ARCHITECTURE_DECISIONS.md','docs/INDUSTRIAL_QUALIFICATION.md','reports/ENGINEERING_STATUS.md','reports/VALIDATION.md',
             'reports/FPGA_CORE.md','reports/CONNECTED_CONTROLLER.md','CNC_CONTROLLER_INVESTIGATION.md'):
    records[name]=sha(ROOT/name)
for path in (HERE/'CNC3_BRANCH_CHECKS').glob('*'):
    if path.is_file():records[path.relative_to(ROOT).as_posix()]=sha(path)
md=[p for p in HERE.glob('*.md')]+[ROOT/'docs/CURRENT_ACCEPTANCE_GATES.md']
links=0;broken=[]
for path in md:
    for raw in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
        target=raw.strip('<>').split('#',1)[0]
        if not target or re.match(r'^(https?|app|codex|plugin):',target):continue
        target=re.sub(r':\d+$','',target)
        dest=Path(target) if re.match(r'^[A-Za-z]:[/\\]',target) else path.parent/target
        links+=1
        if dest.name=='final-audit-state.json' and dest.parent.resolve()==HERE:continue
        if not dest.exists():broken.append({'document':path.relative_to(ROOT).as_posix(),'target':target})
state={'date':'2026-09-30','audited_main_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
       'scope':'Main checkout plus clean separate claude/interface-spec at67b1bfc; current visible/inherited chat, seven original sources and memory-recorded later decisions',
       'host_observation_inventory_files':len(before),'during_checks_changed':json.loads((HERE/'check-results.json').read_text())['changed_during_checks'],
       'post_check_preexisting_input_changes':changed,'post_check_implementation_input_changes':implementation_changed,
       'new_sources_and_gates':['research/architecture-source/source.json','docs/CURRENT_ACCEPTANCE_GATES.md'],
       'archive_copy_mismatches':archive_errors,'archive_current_report_annotations':archive_current_diff,
       'requirements':64,'features':200,'end_to_end_feature_acceptance_claims':0,
       'local_links_checked':links,'broken_links':broken,'artifact_sha256':dict(sorted(records.items())),
       'overall_score':35,'accounting_score':92,'manufacturing_ready':False,'supplier_submission_made':False,
       'physical_machine_or_bus_access':False,'historical_evidence_overwritten':False}
(HERE/'final-audit-state.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'implementation_changes':implementation_changed,'report_annotations':archive_current_diff,'links':links,'broken_links':broken,'score':35,'accounting_score':92},indent=2))
assert not broken, broken
