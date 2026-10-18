from pathlib import Path
import hashlib,json,urllib.request
from pypdf import PdfReader
P=Path(__file__).resolve().parent/'sources-r01';P.mkdir(exist_ok=False)
urls={'RM0444':'https://www.st.com/resource/en/reference_manual/DM00371828-.pdf','DS12992':'https://www.st.com/resource/en/datasheet/stm32g031g4.pdf'}
rows=[]
for name,url in urls.items():
 p=P/(name+'.pdf')
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=75) as f:p.write_bytes(f.read())
  assert p.read_bytes().startswith(b'%PDF')
  reader=PdfReader(p); text='\n'.join(f'\nPAGE {i+1}\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages))
  (P/(name+'.txt')).write_text(text,encoding='utf8')
  rows.append({'name':name,'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pages':len(reader.pages),'status':'PASS'})
 except Exception as e:rows.append({'name':name,'url':url,'status':'BLOCKED','error':str(e)})
(P/'receipt.json').write_text(json.dumps({'retrieved':'2026-10-01','sources':rows},indent=2)+'\n');print(json.dumps(rows))
