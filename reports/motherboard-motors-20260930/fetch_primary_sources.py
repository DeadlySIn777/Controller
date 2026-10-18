"""Retain exact manufacturer files used for the new motor interface source."""
from pathlib import Path
import hashlib,json,urllib.request
import fitz
HERE=Path(__file__).resolve().parent
SOURCES={
 'tlp3640a':'https://toshiba.semicon-storage.com/info/docget.jsp?did=159803',
 'tlp4176a':'https://toshiba.semicon-storage.com/info/docget.jsp?did=65816',
 'tps22918':'https://www.ti.com/lit/ds/symlink/tps22918.pdf',
 'smbj':'https://www.vishay.com/docs/88392/smbj.pdf',
 'lvc2g17':'https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf',
}
out=HERE/'sources';out.mkdir(parents=True,exist_ok=True);records=[]
for name,url in SOURCES.items():
 try:
  data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()
  if not data.startswith(b'%PDF'):raise ValueError('Not PDF')
  path=out/(name+'.pdf');path.write_bytes(data);doc=fitz.open(path)
  (out/(name+'.txt')).write_text('\n'.join(p.get_text() for p in doc),encoding='utf-8')
  for i in (0,len(doc)-2,len(doc)-1):
   if i>=0:doc[i].get_pixmap(matrix=fitz.Matrix(2,2)).save(out/(name+f'-page{i+1}.png'))
  records.append({'name':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'pages':len(doc),'status':'retained'})
 except Exception as e:records.append({'name':name,'url':url,'status':'failed','error':str(e)})
(HERE/'source-downloads.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
print(json.dumps(records,indent=2))
