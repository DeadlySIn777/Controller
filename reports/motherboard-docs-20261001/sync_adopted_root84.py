from pathlib import Path
import json,hashlib,shutil
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root84-sync-r01';OUT.mkdir(exist_ok=False)
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
adopt=read(base/'adoption.json');conn=read(base/'independent-connectivity/review.json');drc=read(base/'drc.json');board=base/'motherboard-bounded-merged-candidate.kicad_pcb'
assert adopt['passed']and adopt['adopted']and sha(board)==adopt['board_sha256']
assert adopt['missing_joins']==conn['independent_physical_cluster_missing_joins']==3601
assert adopt['track_via_count']==11038 and adopt['zone_count']==1508 and not drc['violations']and not drc['ignored_checks']and not conn['orphan_copper_items']
assert adopt['all187_reference_resources_actually_SOURCE_anchored']and adopt['retained_bypass_loops']==101 and adopt['receiving_return_endpoints']==207
flash=Path(adopt['additional_complete_FPGA_FLASH_MISO_proof']);f=read(flash)
assert f['passed']and len(f['exact_native_twelve_signal_UUIDs'])==12 and len(f['original_actual_twelve_cut_negatives'])==12 and f['no_signal_vias']and f['board_sha256']==sha(board)
replacements={
 'adopted working PCB r83':'adopted working PCB r84',
 'source26/r83 working PCB':'source26/r84 working PCB',
 '11,026 track/via items and 1,508 zones':'11,038 track/via items and 1,508 zones',
 '622 fully joined and 1,112 incomplete':'623 fully joined and 1,111 incomplete',
 '3,602 uncapped missing joins':'3,601 uncapped missing joins',
 'source26-reference-closure-and-spurs-r83/adoption.json':'source26-FPGA-flash-MISO-r84/adoption.json',
 'source26-reference-closure-and-spurs-r83/independent-connectivity/review.json':'source26-FPGA-flash-MISO-r84/independent-connectivity/review.json',
}
note=' The complete FPGA FLASH_MISO path now connects the actual U1001.N1 and U1002.2 endpoints through twelve F-side conductors, with no signal vias, a measured native path of 66.954 mm, the unchanged 0.40 mm own-reference corridor and twelve actual conductor-cut negatives. Loaded flash/configuration timing and the final manufacturing stackup remain unqualified.'
changes={}
for rel in('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md'):
 p=ROOT/rel;old=p.read_text();before=OUT/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,before);new=old
 for a,b in replacements.items():
  assert a in new,(rel,a);new=new.replace(a,b)
 anchor=' These are scoped local proofs; global power and reference qualification remain incomplete.'
 assert anchor in new;new=new.replace(anchor,note+anchor,1)
 # No trial85/86/87, SOURCE27 stage, historical regression or published24
 # evidence is promoted by this bounded current-status update.
 p.write_text(new,encoding='utf8');after=OUT/'after'/rel;after.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,after)
 changes[rel]=dict(before_sha256=sha(before),after_sha256=sha(after))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,adopted_ROOT84_only=True,source26_unchanged=True,published_CAD24_unchanged=True,old_regression_provenance_retained=True,inputs_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in(base/'adoption.json',base/'independent-connectivity/review.json',base/'drc.json',board,flash)},changes=changes,physical_qualification=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,documents=4,board_revision=84,uncapped_missing_joins=3601)))
