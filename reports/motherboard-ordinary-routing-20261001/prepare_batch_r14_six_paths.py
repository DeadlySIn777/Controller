"""Keep six independent paths while the seventh's power contour is investigated."""
from pathlib import Path
import sys,json,shutil
sys.path.insert(0,str(Path('tools').resolve()))
import hardware_route_critical_digital_wip_r05 as authority
e=authority.engine;p=Path(__file__).parent;old=p/'actual-source26-root83-In2-batch-r12';out=p/'actual-source26-root83-In2-batch-r14';out.mkdir(exist_ok=False)
src=old/'motherboard-ordinary-In2-batch-candidate.kicad_pcb';plan=e.read(old/'proposed-groups.json');deferred=plan['groups'][3];assert deferred['source_pair']==['U13004.10','U13008.10']
remove=set(deferred['new_copper_UUIDs']);tree=e.parse(src.read_text());found={e.value(e.child(n,'uuid')[1])for n in tree if isinstance(n,list)and n and n[0]in('segment','via','arc')and e.value(e.child(n,'uuid')[1])in remove};assert found==remove
tree=[n for n in tree if not(isinstance(n,list)and n and n[0]in('segment','via','arc')and e.value(e.child(n,'uuid')[1])in remove)]
dest=out/src.name;dest.write_text(authority.dump_native_board(tree)+'\n')
plan['groups'].pop(3);plan['new_copper_UUIDs']=[u for g in plan['groups']for u in g['new_copper_UUIDs']];plan['deferred_unadopted_group']=deferred;plan['deferred_reason']='Actual post-refill relative IO3 native contour at two old antipads requires independent review; no power exception granted.'
e.write(out/'proposed-groups.json',plan)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in old.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name in('fp-lib-table','manifest.json','piece-eligibility.json'):shutil.copyfile(f,out/f.name)
validator=(p/'verify_root83_In2_batch_r09.py').read_text().replace('actual-source26-root83-In2-batch-r09','actual-source26-root83-In2-batch-r14').replace('len(groups)==7','len(groups)==6').replace('all7_actual_pairs_closed','all6_actual_pairs_closed').replace('actual_pairs=7','actual_pairs=6').replace('Exact seven ordinary','Exact six ordinary')
(p/'verify_root83_In2_batch_r14.py').write_text(validator)
runner=(p/'run_batch_r12_native_checks.py').read_text().replace('batch-r12','batch-r14').replace('batch_r12','batch_r14')
start=runner.index('validator=p/');end=runner.index('jobs=[',start)
runner=runner[:start]+"validator=p/'verify_root83_In2_batch_r14.py';assert validator.exists()\n"+runner[end:]
(p/'run_batch_r14_native_checks.py').write_text(runner)
e.write(out/'deferral.json',dict(input_sha256=e.sha(src),candidate_sha256=e.sha(dest),deferred_route=deferred,original_ROOT83_copper_change=False,removed_only_unadopted_proposed_copper=len(remove),remaining_groups=len(plan['groups']),native_checks_pending=True,manufacturing_ready=False))
print(json.dumps(dict(paths=len(plan['groups']),newCu=len(plan['new_copper_UUIDs']))))
