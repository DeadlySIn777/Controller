"""Preserve failed r3 adapter; correct exact target loop in a separate r4."""
import datetime,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'continue_ordinary_escapes_r3.py';raw=src.read_bytes();text=raw.decode()
old="loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='row')"
new="loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='row' and ast.unparse(n.iter)==\"old['results']\")"
if text.count(old)!=1:raise ValueError('Exact failed derivative target differs')
text=text.replace(old,new).replace("R.OUT=HERE/'new-via-escape-r3'","R.OUT=HERE/'new-via-escape-r4'")
dst=HERE/'continue_ordinary_escapes_r4.py'
if dst.exists():raise ValueError('Fresh adapter required')
dst.write_text(text,encoding='utf-8')
stop=HERE/'new-via-escape-r3/stopped.json'
stop.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owned_pid':36276,'reason':'Derivative selected prior-plan loop instead of ordinary-net loop; no board emitted and no result credit','source':str(src),'source_sha256':hashlib.sha256(raw).hexdigest(),'corrected_adapter':str(dst),'corrected_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print(str(dst))
