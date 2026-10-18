"""Run the actual KiCad tests that the ordinary host explicitly cannot execute."""
import importlib.util,json,os,re,sys,unittest
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests'),str(ROOT/'tools')]
sys.dont_write_bytecode=True
source=ROOT/'reports/board-completion-20261001/source26-root87-host-r01/receipt.json'
host=json.loads(source.read_text());ids=set()
for row in host['runs'][-1]['skip_cases']:
 if 'KiCad' in row['reason']:ids.add(re.search(r'\(([^()]+)\)$',row['case']).group(1))
loader=unittest.TestLoader()
def leaves(suite):
 for test in suite:
  if isinstance(test,unittest.TestSuite):yield from leaves(test)
  else:yield test
assert ids
runnerpath=ROOT/'reports/board-completion-20261001/source26-root87-host-r01/run_validation.py'
spec=importlib.util.spec_from_file_location('frozen_inventory',runnerpath);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
assert not(OUT/'receipt.json').exists();before=h.inventory()
(OUT/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
temp=OUT/'test-artifacts';temp.mkdir();os.environ['TEMP']=str(temp);os.environ['TMP']=str(temp)
suite=loader.loadTestsFromNames(sorted(ids));started=h.utc()
with(OUT/'native-tests.log').open('w',encoding='utf8')as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
after=h.inventory();changes={k for k in set(before)|set(after)if before.get(k)!=after.get(k)}
(OUT/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
receipt=dict(passed=result.wasSuccessful()and not result.skipped and not changes,started_utc=started,finished_utc=h.utc(),actual_native_python=sys.executable,reported_tests=result.testsRun,failures=[(t.id(),v)for t,v in result.failures],errors=[(t.id(),v)for t,v in result.errors],skipped=result.skipped,selected_test_ids=sorted(ids),native_test_log_sha256=h.sha(OUT/'native-tests.log'),source_hashes_unchanged=not changes,changed_source_paths=sorted(changes),host_skip_receipt_sha256=h.sha(source),board_manufacturing_or_physical_qualification=False,interfaces_disconnected=True)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items()if k not in('selected_test_ids','failures','errors')},indent=2),flush=True)
raise SystemExit(not receipt['passed'])
