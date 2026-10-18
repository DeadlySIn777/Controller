"""Record the authorized before/after diff without modifying project sources."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
before = json.loads((OUT / 'firmware-runtime-before.json').read_text(encoding='utf-8'))
rows, patches = [], []
for name, digest in before['source_sha256'].items():
    old = (OUT / 'before' / name).read_bytes()
    new = (ROOT / name).read_bytes()
    assert hashlib.sha256(old).hexdigest() == digest, name
    rows.append({'path': name, 'before_sha256': digest,
                 'after_sha256': hashlib.sha256(new).hexdigest(), 'changed': old != new})
    patches.extend(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),
                   new.decode('utf-8').splitlines(keepends=True), fromfile='before/' + name, tofile=name))
with (OUT / 'firmware-runtime.diff').open('x', encoding='utf-8', newline='') as handle:
    handle.write(''.join(patches))
with (OUT / 'firmware-runtime-after.json').open('x', encoding='utf-8') as handle:
    json.dump({'recorded_utc': datetime.now(timezone.utc).isoformat(), 'files': rows}, handle, indent=2)
    handle.write('\n')
print(json.dumps({'changed': [row['path'] for row in rows if row['changed']],
                  'unchanged': [row['path'] for row in rows if not row['changed']]}, indent=2))
