"""Retain primary sources for actual analog source development."""
import concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
import fitz
OUT=Path(__file__).resolve().parent/'sources';OUT.mkdir(exist_ok=True)
urls={n:'https://www.ti.com/lit/ds/symlink/'+n+'.pdf' for n in ['ads1115','iso1540','tps7a16','iso7742','tps3700','dac80501','opa197','sn74lvc1g14']}
urls['tmr1']='https://www.tracopower.com/products/tmr1.pdf'
def get(item):
 n,url=item
 try:
  b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=12).read()
  if not b.startswith(b'%PDF'):raise ValueError('not PDF')
  p=OUT/(n+'.pdf');p.write_bytes(b);doc=fitz.open(p);(OUT/(n+'.txt')).write_text('\n'.join(q.get_text() for q in doc),encoding='utf-8')
  return {'id':n,'url':url,'sha256':hashlib.sha256(b).hexdigest(),'pages':len(doc),'status':'retained'}
 except Exception as exc:return {'id':n,'url':url,'status':'not retained','error':str(exc)}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:r=list(pool.map(get,urls.items()))
(OUT/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
