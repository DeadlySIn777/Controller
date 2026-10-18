"""Read-only primary manufacturer source retention; no supplier contact."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

url = 'https://media.digikey.com/pdf/Data%20Sheets/Murata%20PDFs/GRM188R72A104KA35.pdf'
dest = Path(__file__).resolve().parent / 'sourcing-evidence'
dest.mkdir(exist_ok=True)
with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45) as response:
    data = response.read()
    mime = response.headers.get('Content-Type')
assert data.startswith(b'%PDF'), 'Primary source response is not PDF; do not retain it as datasheet'
path = dest / 'murata-grm188r72a104ka35.pdf'
path.write_bytes(data)
receipt = dict(source_url=url, source_kind='Manufacturer-authored reference sheet hosted by distributor; lastupdated2013-12-24', observed_date='2026-09-30', content_type=mime,
               file=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
(dest / 'murata-grm188r72a104ka35.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
