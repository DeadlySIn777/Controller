from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent
r=json.loads((here/'receipt.json').read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for x in r['files']:
 assert sha(x['path'])==x['after_SHA256'], 'Current file changed; refusing to overwrite later work'
 assert sha(x['backup'])==x['before_SHA256']
for x in r['files']:
 Path(x['path']).write_bytes(Path(x['backup']).read_bytes())
print('Restored the exact four pre-adoption files; frozen evidence retained.')
