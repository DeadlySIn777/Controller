"""Create fresh disconnected host/native/unsuppressed ERC regression runners."""
from pathlib import Path
p=Path(__file__).parent
for kind,filename in(('host','run_validation.py'),('native','run_native.py')):
 out=p/f'source26-root87-{kind}-r01';out.mkdir(exist_ok=False)
 s=(p/f'source26-root83-{kind}-r01'/filename).read_text().replace('source26-root83','source26-root87')
 (out/filename).write_text(s)
s=(p/'reconcile-root83-validation-r01.py').read_text().replace('source26-root83','source26-root87')
(p/'reconcile-root87-validation-r01.py').write_text(s)
