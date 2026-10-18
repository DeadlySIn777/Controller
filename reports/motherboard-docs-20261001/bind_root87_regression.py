from pathlib import Path
import json,hashlib,shutil
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-docs-20261001/source26-root87-regression-sync-r02';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=ROOT/'reports/board-completion-20261001/source26-root87-combined-validation.json';r=json.loads(proof.read_text())
assert r['passed'] and r['host_passed']==1847 and r['actual_KiCad_cases_passed']==235 and len(r['remaining_skips'])==5 and r['scoped_source_files']==2810 and r['all_scoped_source_hashes_unchanged']
assert r['native_ERC']['errors']==0 and r['native_ERC']['warnings']==70 and not r['native_ERC']['ignored_checks']
changes={}
for rel in('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','reports/ENGINEERING_STATUS.md'):
 p=ROOT/rel;old=p.read_text();new=old.replace('source26-root83-combined-validation.json','source26-root87-combined-validation.json')
 # Some current heads state the counts without a separate regression link.
 if new==old:
  anchor=' All 2,810 scoped source hashes stayed unchanged.'
  assert anchor in old,rel
  new=old.replace(anchor,anchor+' [Fresh regression](reports/board-completion-20261001/source26-root87-combined-validation.json).' if rel=='PROJECT_MEMORY.md' else anchor+' [Fresh regression]('+('../reports/'if rel.startswith('docs/')else '')+'board-completion-20261001/source26-root87-combined-validation.json).',1)
 before=OUT/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,before)
 p.write_text(new,encoding='utf8');after=OUT/'after'/rel;after.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,after)
 changes[rel]=dict(before_sha256=sha(before),after_sha256=sha(after))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,current_adopted_ROOT87_regression_only=True,published_CAD24_unchanged=True,history_unchanged=True,regression_sha256=sha(proof),changes=changes,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,documents=4)))
