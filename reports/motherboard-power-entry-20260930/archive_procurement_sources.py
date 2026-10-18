"""Archive genuine primary records; HTTP errors never become datasheets."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import requests

DEST=Path(__file__).resolve().parent/'sources'
URLS={
 'vishay-crcw-20035.pdf':'https://www.vishay.com/docs/20035/dcrcwe3.pdf',
 'vishay-tnpw-28758.pdf':'https://www.vishay.com/docs/28758/tnpw_e3.pdf',
 'littelfuse-997.pdf':'https://www.littelfuse.com/assetdocs/littelfuse-datasheet-997-mini58v?assetguid=f4bf5724-5a40-4a44-8f08-c52ae959a5ef',
 'tdk-c1608x7r1h473k080aa.html':'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1H473K080AA',
 'tdk-c2012x7r1c475k125ab.html':'https://product.tdk.com/ja/search/capacitor/ceramic/mlcc/info?part_no=C2012X7R1C475K125AB',
 'tdk-c2012c0g1h223j125aa.html':'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012C0G1H223J125AA',
 'tdk-c2012c0g2a103j125aa.html':'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012C0G2A103J125AA',
 'tdk-c3216c0g2a104j160ac.html':'https://product.tdk.com/ja/search/capacitor/ceramic/mlcc/info?part_no=C3216C0G2A104J160AC',
 'murata-grm31cr72a105ka01.pdf':'https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR72A105KA01-01.pdf',
 'murata-grm188r72a103ka01.html':'https://www.murata.com/en-us/products/productdetail?partno=GRM188R72A103KA01D',
 'murata-grm1885c1h331ja01.html':'https://www.murata.com/en-us/products/productdetail?partno=GRM1885C1H331JA01D',
 'keystone3568-current.pdf':'https://www.keyelco.com/product-pdf.cfm?p=306',
}

def fetch(item):
    filename,url=item
    try:
        r=requests.get(url,timeout=15)
        good=r.status_code==200 and (not filename.endswith('.pdf') or r.content.startswith(b'%PDF'))
        if not good:return {'filename':filename,'url':url,'status':r.status_code,'archived':False,'reason':'HTTP failure or non-PDF response'}
        (DEST/filename).write_bytes(r.content)
        return {'filename':filename,'url':url,'status':r.status_code,'archived':True,'sha256':hashlib.sha256(r.content).hexdigest(),'bytes':len(r.content)}
    except Exception as e:return {'filename':filename,'url':url,'archived':False,'reason':str(e)}

if __name__=='__main__':
    DEST.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(fetch,URLS.items()))
    (DEST.parent/'procurement-source-record.json').write_text(json.dumps({'date':'2026-09-30','primary_downloads':rows,'web_open_records_also_reviewed':True,'web_product_records_are_specs_not_full_dynamic_guarantees':True},indent=2)+'\n',encoding='utf8')
    print(json.dumps({'genuine_archives':sum(r['archived'] for r in rows),'unavailable_archives':[r['filename'] for r in rows if not r['archived']]}))
