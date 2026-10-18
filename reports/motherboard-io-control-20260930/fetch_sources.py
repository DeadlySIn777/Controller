import hashlib,json,requests,fitz
from pathlib import Path
OUT=Path(__file__).resolve().parent; D=OUT/'sources';D.mkdir(parents=True,exist_ok=True)
urls={'stm32g031':'https://www.st.com/resource/en/datasheet/stm32g031c8.pdf',
 'an5096':'https://www.st.com/resource/en/application_note/dm00443870-getting-started-with-stm32g0-series-hardware-development-stmicroelectronics.pdf',
 'rm0444':'https://www.st.com/resource/en/reference_manual/dm00371828-stm32g0x1-advanced-armbased-32bit-mcus-stmicroelectronics.pdf',
 'tps3851':'https://www.ti.com/lit/ds/symlink/tps3851.pdf',
 'sn74lvc07a':'https://www.ti.com/lit/ds/symlink/sn74lvc07a.pdf',
 'sn74lvc125a':'https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf'}
rows=[]
for name,url in urls.items():
 p=D/(name+'.pdf')
 try:
  if not p.exists():
   r=requests.get(url,timeout=25);r.raise_for_status();assert r.content.startswith(b'%PDF');p.write_bytes(r.content)
  doc=fitz.open(p);(D/(name+'.txt')).write_text('\n'.join(pg.get_text() for pg in doc),encoding='utf-8')
  rows.append({'name':name,'url':url,'file':str(p.relative_to(OUT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pages':len(doc),'status':'retained_primary'})
 except Exception as exc:rows.append({'name':name,'url':url,'status':'unresolved','error':str(exc)})
(OUT/'primary-sources.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['sha256','file']} for r in rows]))
