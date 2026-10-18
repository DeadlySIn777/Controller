import ssl,urllib.request,pathlib,re,json
HERE=pathlib.Path(__file__).resolve().parent/'cap-primary'
HERE.mkdir(exist_ok=True)
C=ssl.create_default_context();C.verify_flags &= ~ssl.VERIFY_X509_STRICT
def fetch(url,name):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 data=urllib.request.urlopen(req,context=C,timeout=30).read();(HERE/name).write_bytes(data);return data
if __name__=='__main__':
 s=fetch('https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1H105K080AB','tdk50-product.html').decode('utf-8')
 print(json.dumps([x for x in re.findall(r'href="([^"]+)',s) if any(k in x.lower() for k in ['105k080ab','graph','sim-c','chara_sheet'])],ensure_ascii=False))
 print(json.dumps(re.findall(r'<script[^>]+src="([^"]+)',s)))
