from pathlib import Path
import json, hashlib, shutil, collections
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root76-sync-r01';OUT.mkdir(exist_ok=False)
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
adopt=read(base/'adoption.json');conn=read(base/'independent-connectivity/review.json');drc=read(base/'drc.json')
board=base/'motherboard-literal38-neck-rule-candidate.kicad_pcb'
assert adopt['passed']and adopt['adopted']and sha(board)==adopt['board_sha256']
assert adopt['missing_joins']==conn['independent_physical_cluster_missing_joins']==3612
assert conn['source_net_checks_pass']and not conn['orphan_copper_items']and adopt['native_errors']==0
assert adopt['track_via_count']==10993 and adopt['zone_count']==1508
assert collections.Counter(v['type']for v in drc['violations'])=={'isolated_copper':3,'track_dangling':2}
changes={};replacements={
 'adopted working PCB r73':'adopted working PCB r76',
 'source26/r73 working PCB':'source26/r76 working PCB',
 '10,889 track/via items and 1,507 zones':'10,993 track/via items and 1,508 zones',
 '614 fully joined and 1,120 incomplete':'620 fully joined and 1,114 incomplete',
 '3,645 uncapped missing joins':'3,612 uncapped missing joins',
 '94 actual owned-bypass loops, 193 receiving-return endpoint checks and 47 physically SOURCE-anchored reference-bridge groups':'97 actual owned-bypass loops, 199 receiving-return endpoint checks and 49 physically SOURCE-anchored reference-bridge groups',
 'source26-digital-bias-returns-adopted-r73/adoption.json':'source26-FPGA38-rule-r76/adoption.json',
 'source26-digital-bias-returns-adopted-r73/independent-connectivity/review.json':'source26-FPGA38-rule-r76/independent-connectivity/review.json',
}
note=' Nine literal ordinary SOURCE-pair routes are now complete and independently rechecked on the combined board. The bounded FPGA neck rule applies only to 38 reviewed signal nets inside the F-side BGA area: 0.15 mm short necks with a separate aggregate 1 mm/net limit; all other tracks retain the 0.20 mm minimum and power rules remain unchanged. Native healthy/negative rule controls pass. Contradictory PCBWay process tables leave exact 2 oz fine-line process confirmation outstanding; this rule is not production process qualification.'
for rel in('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md'):
 p=ROOT/rel;old=p.read_text();before=OUT/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,before);new=old
 for a,b in replacements.items():new=new.replace(a,b)
 # The current paragraph alone receives the new evidence; historical tables
 # and the published CAD24 snapshot remain unchanged.
 anchor=' These are scoped local proofs; global power and reference qualification remain incomplete.'
 assert anchor in new;new=new.replace(anchor,note+anchor,1)
 p.write_text(new,encoding='utf8');changes[rel]=dict(before_sha256=sha(before),after_sha256=sha(p))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,adopted_ROOT76_only=True,source26_unchanged=True,published_CAD24_unchanged=True,inputs={str(p.relative_to(ROOT)):sha(p)for p in(base/'adoption.json',base/'independent-connectivity/review.json',base/'drc.json',board)},changes=changes,physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,documents=len(changes),board_revision=76,uncapped_missing_joins=3612)))
