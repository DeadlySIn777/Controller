"""Retain exact primary AO source candidates; no procurement actions."""
import hashlib,json,urllib.request,concurrent.futures
from pathlib import Path
import fitz
out=Path(__file__).resolve().parent/'sources'
urls={k:'https://www.ti.com/lit/ds/symlink/'+k+'.pdf' for k in ['iso7761','iso7720','sn74lvc1g125','sn74lvc1g08','sn74lvc1g06']}
urls['ad5683r']='https://www.analog.com/media/en/technical-documentation/data-sheets/ad5683r_5682r_5681r_5683.pdf'
def get(kv):
 k,url=kv
 try:
  data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=15).read()
  if not data.startswith(b'%PDF'):raise ValueError('not PDF')
  p=out/(k+'.pdf');p.write_bytes(data);doc=fitz.open(p);(out/(k+'.txt')).write_text('\n'.join(x.get_text() for x in doc),encoding='utf-8')
  return {'id':k,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'pages':len(doc),'status':'retained'}
 except Exception as e:return {'id':k,'url':url,'status':'not retained','error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:r=list(pool.map(get,urls.items()))
(out/'ao-manifest.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
