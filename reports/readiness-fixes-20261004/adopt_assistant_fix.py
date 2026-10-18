"""Hash-guarded adoption of the tested advisory-only external assistant."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

OUT = Path(__file__).resolve().parent
target = Path('Z:/Programming Projects/Genmitsu1030Cnc/fluidcnc/ai-assistant.js')
app = target.with_name('app.js')
expected = '90a6624e36cba2bd0ab28e77eda844e605edfd17b20a25323f186eb03f32e948'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
candidate = OUT / 'external-ai-assistant-candidate.js'
test = json.loads((OUT / 'assistant-nonactuation-candidate.json').read_text())
assert test['passed'] and test['source_sha256'] == sha(candidate)
assert sha(target) == expected and sha(OUT / 'before/external-ai-assistant.js') == expected
app_before = sha(app)
temp = target.with_name('ai-assistant.readiness-' + uuid.uuid4().hex + '.tmp')
try:
    with temp.open('xb') as handle:
        handle.write(candidate.read_bytes())
        handle.flush()
        os.fsync(handle.fileno())
    shutil.copymode(target, temp)
    assert sha(target) == expected, 'Concurrent external edit detected; adoption refused.'
    os.replace(temp, target)
finally:
    if temp.exists():
        temp.unlink()
assert sha(target) == test['source_sha256']
receipt = dict(adopted_utc=datetime.now(timezone.utc).isoformat(), external_candidate_remains_unadopted_by_controller=True,
               path=str(target), before_sha256=expected, after_sha256=sha(target),
               dedicated_controls_path=str(app), dedicated_controls_sha256_before=app_before,
               dedicated_controls_sha256_after=sha(app), dedicated_controls_unchanged=app_before == sha(app),
               applicable_ancestor_AGENTS_found=[], app_launched=False, machine_transport_opened=False,
               scope='Source-only external assistant safety fix; no product, board or physical qualification.')
(OUT / 'assistant-fix-adoption.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(receipt, indent=2))
