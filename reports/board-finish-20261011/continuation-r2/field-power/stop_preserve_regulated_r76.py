import json,os,hashlib
from pathlib import Path
import psutil
H=Path(__file__).resolve().parent
p=psutil.Process(54240);cmd=p.cmdline();assert any('construct_regulated_adaptive_feeds_r76.py' in x for x in cmd)
out=H/'regulated-adaptive-source-feeds-r76';assert (out/'checkpoint.json').exists()
def sh(x):return hashlib.sha256(x.read_bytes()).hexdigest()
snapshot={x.name:sh(x) for x in out.iterdir() if x.is_file()};p.terminate();p.wait(20)
(out/'owned-termination-r1.json').write_text(json.dumps({'owned_pid':54240,'verified_command':cmd,'accepted_checkpoint_and_object_hashes':snapshot,'reason':'Preserve accepted FIELD5 source hub; resume with exact latest CORE/root hard composition and local narrower-first route ordering before expensive whole-outline fallback. No live/native board changed.','original_files_changed':False},indent=1)+'\n',encoding='utf-8');print(sh(out/'owned-termination-r1.json'))
