"""Run the six package-import cases omitted by the first native runner."""
import importlib.util,json,os,sys,unittest
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests'),str(ROOT/'tools')];sys.dont_write_bytecode=True
path=ROOT/'reports/board-completion-20261001/source26-ground-routing-host-r02/run_validation.py'
spec=importlib.util.spec_from_file_location('inventory',path);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
before=h.inventory();(OUT/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
temp=OUT/'test-artifacts';temp.mkdir();os.environ['TEMP']=str(temp);os.environ['TMP']=str(temp)
suite=unittest.defaultTestLoader.loadTestsFromName('test_motherboard_return_bridge_sources');started=h.utc()
with(OUT/'native-tests.log').open('w',encoding='utf8')as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
after=h.inventory();(OUT/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
result=dict(passed=r.wasSuccessful()and not r.skipped and before==after,started_utc=started,finished_utc=h.utc(),native_python=sys.executable,tests=r.testsRun,failures=[(t.id(),s)for t,s in r.failures],errors=[(t.id(),s)for t,s in r.errors],skips=[(t.id(),s)for t,s in r.skipped],source_hashes_unchanged=before==after,log_sha256=h.sha(OUT/'native-tests.log'),physical_or_manufacturing_qualification=False)
(OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(not result['passed'])
