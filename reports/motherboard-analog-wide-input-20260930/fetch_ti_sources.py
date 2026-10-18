from pathlib import Path
import urllib.request,hashlib,subprocess
root=Path(__file__).resolve().parent/'sources'
for name in ['tps7a26','tps3702']:
 p=root/(name+'.pdf')
 if not p.exists():p.write_bytes(urllib.request.urlopen(urllib.request.Request('https://www.ti.com/lit/ds/symlink/'+name+'.pdf',headers={'User-Agent':'Mozilla/5.0','Accept':'application/pdf'}),timeout=60).read())
 subprocess.run(['C:/Python314/python.exe','-c','import fitz,sys; d=fitz.open(sys.argv[1]); open(sys.argv[2],"w",encoding="utf-8").write("\\n".join(p.get_text() for p in d))',str(p),str(p.with_suffix('.txt'))],check=True)
 print(name,hashlib.sha256(p.read_bytes()).hexdigest())
