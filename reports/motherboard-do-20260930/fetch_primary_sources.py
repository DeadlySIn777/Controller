"""Retain primary manufacturer-authored source documents, never orders."""
import hashlib
import json
from pathlib import Path
import requests
import pypdf

HERE=Path(__file__).resolve().parent; OUT=HERE/'sources'
URLS={'tps274c65':'https://www.ti.com/lit/ds/symlink/tps274c65.pdf','iso7760':'https://www.ti.com/lit/ds/symlink/iso7760.pdf','csd19538q3a':'https://www.ti.com/lit/ds/symlink/csd19538q3a.pdf','sn74lvc08a':'https://www.ti.com/lit/ds/symlink/sn74lvc08a.pdf','sn74lvc1g74':'https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf','tnpw':'https://www.vishay.com/docs/28758/tnpw_e3.pdf','murata-2u2':'https://www.farnell.com/datasheets/4088041.pdf','kemet-22n':'https://www.tme.com/Document/1eb495a6db632c9d0f71cb50aeea4240/C0805C223K1RACTU.pdf'}
records=[]
for name,url in URLS.items():
    p=OUT/(name+'.pdf')
    try:
        if not p.exists():
            r=requests.get(url,timeout=15);r.raise_for_status()
            if not r.content.startswith(b'%PDF'):raise ValueError('not PDF')
            p.write_bytes(r.content)
        pdf=pypdf.PdfReader(p)
        p.with_suffix('.txt').write_text('\n'.join(page.extract_text() for page in pdf.pages),encoding='utf-8')
        records.append({'name':name,'url':url,'document_role':'primary manufacturer authored; distributor host for two exact capacitor sheets','file':'sources/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pages':len(pdf.pages),'status':'retained_primary_document'})
        print(name,'OK',len(pdf.pages),flush=True)
    except Exception as exc:
        records.append({'name':name,'url':url,'status':'source_fetch_unresolved','error':str(exc)})
        print(name,'UNRESOLVED',str(exc),flush=True)
(HERE/'primary-sources.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
