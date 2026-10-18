from pathlib import Path
import json,hashlib,shutil,collections
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root73-sync-r01';OUT.mkdir(exist_ok=False)
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73'
adopt=json.loads((base/'adoption.json').read_text());conn=json.loads((base/'independent-connectivity/review.json').read_text());drc=json.loads((base/'drc.json').read_text())
host=ROOT/'reports/board-completion-20261001/source26-ground-routing-combined-validation.json';reg=json.loads(host.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
board=base/'motherboard-source26-WIP.kicad_pcb'
if not adopt['passed']or not adopt['adopted']or sha(board)!=adopt['board_sha256']:raise ValueError('Adopted board binding failed')
assert adopt['missing_joins']==conn['independent_physical_cluster_missing_joins']==3645
assert conn['source_net_checks_pass']and not conn['orphan_copper_items']and adopt['native_errors']==0
assert collections.Counter(v['type']for v in drc['violations'])=={'isolated_copper':3,'track_dangling':2}
assert reg['passed']and reg['host_passed']==1847 and reg['actual_KiCad_cases_passed']==210 and len(reg['remaining_skips'])==5 and reg['all_2798_scoped_source_hashes_unchanged']
replacements={
 'adopted working PCB r62':'adopted working PCB r73',
 'source26/r62 working PCB':'source26/r73 working PCB',
 '10,506 track/via items':'10,889 track/via items',
 '609 fully joined and 1,125 incomplete':'614 fully joined and 1,120 incomplete',
 '3,811 uncapped missing joins':'3,645 uncapped missing joins',
 'ten isolated-fill warnings and two FIELD_B return-track warnings':'three isolated-fill warnings and two FIELD_B return-track warnings',
 '93 actual owned-bypass loops, 191 receiving-return endpoint checks and 43 physically SOURCE-anchored reference-bridge groups':'94 actual owned-bypass loops, 193 receiving-return endpoint checks and 47 physically SOURCE-anchored reference-bridge groups',
 'source26-orphan-free-adopted-r62/adoption.json':'source26-digital-bias-returns-adopted-r73/adoption.json',
 'motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/independent-connectivity/review.json':'motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/independent-connectivity/review.json',
}
files=[ROOT/'PROJECT_MEMORY.md',ROOT/'docs/BUILD_PLAN.md',ROOT/'docs/PLATFORM_ROADMAP.md',ROOT/'reports/ENGINEERING_STATUS.md'];changes={}
for p in files:
 rel=p.relative_to(ROOT);copy=OUT/'before'/rel;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,copy);old=p.read_text();new=old
 # The literal current-head strings are unique; old immutable reports and
 # unrelated dated history remain untouched.
 for a,b in replacements.items():
  if a in new:new=new.replace(a,b)
 if p.name=='ENGINEERING_STATUS.md':
  a='**Full regression scope:** the last complete disconnected run remains the immutable 980-source run: 1,070 reported, 1,065 passed and five Windows LinuxCNC symlink cases skipped, with 1,636 scoped hashes unchanged. Later source/tool changes have focused checks; a fresh full run is pending the current tool freeze.'
  b='**Fresh disconnected regression:** 1,847 host cases pass; all 210 cases requiring actual KiCad are separately executed and pass in KiCad Python. Five Windows symlink cases remain explicitly skipped. All 2,798 scoped source hashes remain unchanged. The native cases correspond exactly to the host KiCad skips and are counted once. This closes the earlier stale cost-fixture/published-BOM binding and CPython native-import failures; those failed receipts and the older 980-source run remain immutable history. [Combined validation](board-completion-20261001/source26-ground-routing-combined-validation.json). These checks do not prove target real-time timing, FPGA vendor fit or physical hardware.'
  if a not in new:raise ValueError('Expected engineering regression head changed')
  new=new.replace(a,b)
  a='Actual ordinary routing waits for the exact qualified current-board plane receipt.'
  b='Actual ordinary routing is limited to literal physically SOURCE-anchored filled reference pieces, preserving the full failed-piece ledger; the entire board and whole LOGIC return net are not qualified. Native routing candidates remain unadopted until their complete endpoint, source, old-copper, warning and return-corridor checks pass.'
  if a not in new:raise ValueError('Expected routing head changed')
  new=new.replace(a,b)
 p.write_text(new,encoding='utf8');changes[str(rel)]=dict(before_sha256=sha(copy),after_sha256=sha(p))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,adopted_root73_only=True,current_source26_unchanged=True,published_CAD24_unchanged=True,input_sha256={str(p.relative_to(ROOT)):sha(p)for p in [base/'adoption.json',base/'independent-connectivity/review.json',base/'drc.json',host,board]},changes=changes,physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(updated_documents=len(changes),board_revision=73,physical_missing_joins=3645,full_host_passed=1847,actual_KiCad_passed=210,remaining_skips=5)))
