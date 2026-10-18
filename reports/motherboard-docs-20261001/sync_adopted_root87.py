from pathlib import Path
import json, hashlib, shutil
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root87-sync-r01';OUT.mkdir(exist_ok=False)
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
adopt=read(base/'adoption.json');conn=read(base/'independent-connectivity/review.json');drc=read(base/'drc.json');board=base/'motherboard-bounded-merged-candidate.kicad_pcb'
assert adopt['passed'] and adopt['adopted'] and sha(board)==adopt['board_sha256']
assert adopt['missing_joins']==conn['independent_physical_cluster_missing_joins']==3594
assert adopt['track_via_count']==11103 and adopt['zone_count']==1509 and not drc['violations'] and not drc['ignored_checks'] and not conn['orphan_copper_items']
assert conn['fully_joined_multiple_pad_nets']==625 and conn['incomplete_multiple_pad_nets']==1109
assert adopt['all187_reference_resources_actually_SOURCE_anchored'] and adopt['retained_bypass_loops']==101 and adopt['receiving_return_endpoints']==207
seven=Path(adopt['additional_seven_complete_SOURCE_pair_proof']);proof=read(seven);assert proof['passed'] and proof['board_sha256']==sha(board)
power=Path(adopt['current_unchanged_r07_power_proof']);assert read(power)['passed']
replacements={
 'adopted working PCB r84':'adopted working PCB r87',
 'source26/r84 working PCB':'source26/r87 working PCB',
 '11,038 track/via items and 1,508 zones':'11,103 track/via items and 1,509 zones',
 '623 fully joined and 1,111 incomplete':'625 fully joined and 1,109 incomplete',
 '3,601 uncapped missing joins':'3,594 uncapped missing joins',
 'source26-FPGA-flash-MISO-r84/adoption.json':'source26-seven-path-larger-IO3-cleanup-trial-r87/adoption.json',
 'source26-FPGA-flash-MISO-r84/independent-connectivity/review.json':'source26-seven-path-larger-IO3-cleanup-trial-r87/independent-connectivity/review.json',
}
note=' Seven additional literal ordinary SOURCE-pair routes now pass actual endpoint and individual conductor-cut checks through 65 added conductors. Their common In1 reference, source-owned transition stitches and unchanged IO3 preservation guard pass on the actual combined board after a separately reviewed local unused-tip cleanup. The composed power chain retains the original MISO power proof and all actual receiver contacts; it does not establish loaded rail capacity or whole-board timing.'
changes={}
for rel in ('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md'):
 p=ROOT/rel;old=p.read_text();before=OUT/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,before);new=old
 for a,b in replacements.items():
  assert a in new,(rel,a);new=new.replace(a,b)
 anchor=' These are scoped local proofs; global power and reference qualification remain incomplete.'
 assert anchor in new;new=new.replace(anchor,note+anchor,1)
 p.write_text(new,encoding='utf8');after=OUT/'after'/rel;after.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,after)
 changes[rel]=dict(before_sha256=sha(before),after_sha256=sha(after))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,adopted_ROOT87_only=True,source26_unchanged=True,published_CAD24_unchanged=True,source83_regression_provenance_retained=True,inputs_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in (base/'adoption.json',base/'independent-connectivity/review.json',base/'drc.json',board,seven,power)},changes=changes,physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,documents=4,board_revision=87,uncapped_missing_joins=3594)))
