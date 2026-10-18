from pathlib import Path
import hashlib,json,runpy
H=Path(__file__).resolve().parent;rows=json.loads((H/'derive-AO1-C19506-ground-r678.json').read_bytes())['generated']
for row in rows:
 p=Path(row['file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['SHA256'];runpy.run_path(str(p),run_name='__main__');receipt=H/f"AO1-COM-C19506-1-real-SOURCE-{row['layer']}-ground-current-peers-r{row['revision']}/receipt.json"
 if json.loads(receipt.read_bytes())['selected']:break
