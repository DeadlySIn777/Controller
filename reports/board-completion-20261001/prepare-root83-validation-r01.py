"""Fresh immutable validation runners; prior receipts stay unchanged."""
from pathlib import Path
p=Path(__file__).parent
for kind,filename in(('host','run_validation.py'),('native','run_native.py')):
 out=p/f'source26-root83-{kind}-r01';out.mkdir(exist_ok=False)
 s=(p/f'source26-root78-{kind}-r01'/filename).read_text().replace('source26-root78','source26-root83')
 (out/filename).write_text(s)
s=(p/'reconcile-root78-validation-r02.py').read_text().replace('source26-root78','source26-root83')
s=s.replace("assert actual==expected and len(actual)==native['reported_tests']==235","assert actual==expected and len(actual)==native['reported_tests'] and len(actual)>=235")
s=s.replace('host=2087,host_passed=1847,actual_native_passed=235','host=result[\'host_reported_tests\'],host_passed=result[\'host_passed\'],actual_native_passed=result[\'actual_KiCad_cases_passed\']')
(p/'reconcile-root83-validation-r01.py').write_text(s)
