"""Read-only, bounded extraction of installed primary RAM documentation."""
from pathlib import Path
from html.parser import HTMLParser
import gzip, re, hashlib, json

ROOT=Path('C:/Efinity/2026.1')
class MainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.on=False; self.text=[]
    def handle_starttag(self, tag, attrs):
        if tag=='main': self.on=True
    def handle_endtag(self, tag):
        if tag=='main': self.on=False
        if self.on and tag in ('p','li','pre','td','h1','h2','h3'): self.text.append('\n')
    def handle_data(self,data):
        if self.on: self.text.append(data)
for name in ('syn-ram.html','syn-ram-examples.html','syn-ram-estimator.html','cli-bram-estimator.html'):
    p=ROOT/'doc/topics'/name; parser=MainText();parser.feed(p.read_text(encoding='utf8'))
    t=''.join(parser.text)
    print('\nDOCUMENT',str(p), 'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
    print(t[:24000])
for name in ('T20.db','T20F256.db'):
    p=ROOT/'pt/db/resource'/name
    raw=gzip.decompress(p.read_bytes())
    print('GZIP_DB',name,'len',len(raw),'header',repr(raw[:80]))
    strings=re.findall(rb'[A-Za-z_][A-Za-z_0-9:, .<>=\[\]()-]{4,120}',raw)
    hits=[s.decode('ascii') for s in strings if re.search(rb'RAM|ram|LUT|lut|19728|19600|BRAM|bram',s)]
    print(json.dumps(hits[:100]))
