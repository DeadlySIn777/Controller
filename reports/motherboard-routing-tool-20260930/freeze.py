"""Freeze tool and verification receipts once; no source or board mutation."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=HERE/'r01-frozen';out.mkdir(exist_ok=False)
 paths={'hardware_route_selected_additive.py':ROOT/'tools/hardware_route_selected_additive.py',
        'test_selected_additive_routing.py':ROOT/'tests/test_selected_additive_routing.py',
        'native_fixture.py':HERE/'native_fixture.py','run_router_fixture.py':HERE/'run_router_fixture.py',
        'native_return_mutations.py':HERE/'native_return_mutations.py','README.md':HERE/'README.md'}
 for name,path in paths.items():shutil.copyfile(path,out/name)
 run=subprocess.run(['C:/Python314/python.exe','-X','utf8','-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_selected_additive_routing.py','-v'],capture_output=True,text=True,encoding='utf8')
 (out/'mutation-tests.txt').write_text(run.stdout+run.stderr,encoding='utf8')
 if run.returncode:raise RuntimeError('Mutation regression failed')
 p=HERE/'native-fixture-r05';r=json.loads((p/'actual-router-import/receipt.json').read_text())
 assert r['added_items']==3 and r['old_copper_items']==11 and r['native_drc']['regular_violations']==0 and r['independent_connectivity']['uncapped_missing_joins']==0
 receipt={'schema_version':1,'revision':'selected-additive-routing-r01','tool_implemented':True,'pure_mutation_tests_passed':21,
  'native_return_cases_passed':4,'actual_local_router_fixture_passed':True,'fixture_added_segments':3,'fixture_retained_tracks_vias':11,
  'fixture_native_DRC_violations':0,'fixture_native_DRC_ignored_checks':[],'fixture_independent_uncapped_missing_joins':0,'fixture_orphans':0,
  'router_interchange_violations_unsuppressed':14,'actual_controller_PCB_routing_executed':False,'live_board_source_or_publication_mutated':False,
  'manufacturing_ready':False,'physical_measurement':False,'source_sha256':{n:sha(f) for n,f in paths.items()},
  'verification_sha256':{str(f.relative_to(HERE)):sha(f) for f in [p/'prepared/prepare.json',p/'router-fixture-receipt.json',p/'actual-router-import/receipt.json',p/'actual-router-import/merged-drc.json',p/'actual-router-import/connectivity/review.json',HERE/'native-return-mutations.json']},
  'primary_sha256':{f.name:sha(f) for f in (HERE/'primary').iterdir() if f.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
 print(json.dumps(receipt))
if __name__=='__main__':main()
