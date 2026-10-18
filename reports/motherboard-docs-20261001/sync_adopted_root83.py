from pathlib import Path
import json, hashlib, shutil, collections
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root83-sync-r01';OUT.mkdir(exist_ok=False)
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
adopt=read(base/'adoption.json');conn=read(base/'independent-connectivity/review.json');drc=read(base/'drc.json')
board=base/'motherboard-bounded-merged-candidate.kicad_pcb'
assert adopt['passed']and adopt['adopted']and sha(board)==adopt['board_sha256']
assert adopt['missing_joins']==conn['independent_physical_cluster_missing_joins']==3602
assert conn['source_net_checks_pass']and not conn['orphan_copper_items']and adopt['native_errors']==0
assert adopt['track_via_count']==11026 and adopt['zone_count']==1508
assert collections.Counter(v['type']for v in drc['violations'])=={}
regression=read(ROOT/'reports/board-completion-20261001/source26-root78-combined-validation.json');assert regression['passed']
changes={};replacements={
 'adopted working PCB r81':'adopted working PCB r83',
 'source26/r81 working PCB':'source26/r83 working PCB',
 '11,018 track/via items and 1,509 zones':'11,026 track/via items and 1,508 zones',
 '621 fully joined and 1,113 incomplete':'622 fully joined and 1,112 incomplete',
 '3,604 uncapped missing joins':'3,602 uncapped missing joins',
 'zero errors, one isolated-fill warning and two FIELD_B return-track warnings, all unsuppressed with no ignored checks':'zero errors, zero warnings and no ignored checks',
 '101 actual owned-bypass loops, 207 receiving-return endpoint checks and 51 physically SOURCE-anchored reference-bridge groups':'101 actual owned-bypass loops, 207 receiving-return endpoint checks and 52 physically SOURCE-anchored reference-bridge groups',
 'source26-C19042-local-bypass-r81/adoption.json':'source26-reference-closure-and-spurs-r83/adoption.json',
 'source26-C19042-local-bypass-r81/independent-connectivity/review.json':'source26-reference-closure-and-spurs-r83/independent-connectivity/review.json',
}
note=' The complete AO1 DAC SDO path is now physically routed and independently checked with its exact four segments and 0.40 mm own-reference corridor. The reviewed retirement of one redundant AO1 same-domain zone retains its entire native outline in the keeper; exact disjoint LOGIC polygon composition preserves the prior ADC/reference cuts. All 187 actual filled reference resources are now physically SOURCE-anchored, with no synthetic exemptions. This resource-anchoring result does not establish every SMD local return loop, signal waveform or rail capacity. Separate C14804 adjacent-reference and C19042 circuit proofs also pass.'

for rel in('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md'):
 p=ROOT/rel;old=p.read_text();before=OUT/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,before);new=old
 for a,b in replacements.items():new=new.replace(a,b)
 # The current paragraph alone receives the new evidence; historical tables
 # and the published CAD24 snapshot remain unchanged.
 anchor=' These are scoped local proofs; global power and reference qualification remain incomplete.'
 assert anchor in new;new=new.replace(anchor,note+anchor,1)
 p.write_text(new,encoding='utf8');changes[rel]=dict(before_sha256=sha(before),after_sha256=sha(p))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,adopted_ROOT83_only=True,source26_unchanged=True,published_CAD24_unchanged=True,inputs={str(p.relative_to(ROOT)):sha(p)for p in(base/'adoption.json',base/'independent-connectivity/review.json',base/'drc.json',board)},changes=changes,physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,documents=len(changes),board_revision=83,uncapped_missing_joins=3602)))
