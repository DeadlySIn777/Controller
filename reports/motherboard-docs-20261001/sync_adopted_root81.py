from pathlib import Path
import json, hashlib, shutil, collections
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root81-sync-r01';OUT.mkdir(exist_ok=False)
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
adopt=read(base/'adoption.json');conn=read(base/'independent-connectivity/review.json');drc=read(base/'drc.json')
board=base/'motherboard-bounded-merged-candidate.kicad_pcb'
assert adopt['passed']and adopt['adopted']and sha(board)==adopt['board_sha256']
assert adopt['missing_joins']==conn['independent_physical_cluster_missing_joins']==3604
assert conn['source_net_checks_pass']and not conn['orphan_copper_items']and adopt['native_errors']==0
assert adopt['track_via_count']==11018 and adopt['zone_count']==1509
assert collections.Counter(v['type']for v in drc['violations'])=={'isolated_copper':1,'track_dangling':2}
regression=read(ROOT/'reports/board-completion-20261001/source26-root78-combined-validation.json');assert regression['passed']
changes={};replacements={
 'adopted working PCB r76':'adopted working PCB r81',
 'source26/r76 working PCB':'source26/r81 working PCB',
 '10,993 track/via items and 1,508 zones':'11,018 track/via items and 1,509 zones',
 '620 fully joined and 1,114 incomplete':'621 fully joined and 1,113 incomplete',
 '3,612 uncapped missing joins':'3,604 uncapped missing joins',
 'zero errors, three isolated-fill warnings and two FIELD_B return-track warnings':'zero errors, one isolated-fill warning and two FIELD_B return-track warnings',
 '97 actual owned-bypass loops, 199 receiving-return endpoint checks and 49 physically SOURCE-anchored reference-bridge groups':'101 actual owned-bypass loops, 207 receiving-return endpoint checks and 51 physically SOURCE-anchored reference-bridge groups',
 'source26-FPGA38-rule-r76/adoption.json':'source26-C19042-local-bypass-r81/adoption.json',
 'source26-FPGA38-rule-r76/independent-connectivity/review.json':'source26-C19042-local-bypass-r81/independent-connectivity/review.json',
}
note=' Two additional literal local critical SOURCE-pair paths are independently complete on the combined board; this does not establish complete multi-endpoint clocks or loaded timing. The fresh regression passed 1,847 host cases and all 235 actual KiCad-native cases; only five Windows symlink cases remain skipped. All 2,808 scoped source hashes stayed unchanged. Fresh native ERC retains the same 70 unsuppressed warning semantics and zero errors; transient KiCad pin-object UUIDs were reconciled by exact source-pin identity.'

for rel in('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md'):
 p=ROOT/rel;old=p.read_text();before=OUT/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,before);new=old
 for a,b in replacements.items():new=new.replace(a,b)
 # The current paragraph alone receives the new evidence; historical tables
 # and the published CAD24 snapshot remain unchanged.
 anchor=' These are scoped local proofs; global power and reference qualification remain incomplete.'
 assert anchor in new;new=new.replace(anchor,note+anchor,1)
 p.write_text(new,encoding='utf8');changes[rel]=dict(before_sha256=sha(before),after_sha256=sha(p))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,adopted_ROOT81_only=True,source26_unchanged=True,published_CAD24_unchanged=True,inputs={str(p.relative_to(ROOT)):sha(p)for p in(base/'adoption.json',base/'independent-connectivity/review.json',base/'drc.json',board)},changes=changes,physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,documents=len(changes),board_revision=81,uncapped_missing_joins=3604)))
