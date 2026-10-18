"""Preserve finite old search evidence when broader grounded r5 supersedes it."""
import datetime,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'new-via-escape-r4'
p=json.loads((out/'progress.json').read_bytes());routes=json.loads((out/'routes-checkpoint.json').read_bytes())
if p['accepted'] or any(r['paths'] for r in routes['results']):raise ValueError('Do not stop an unreviewed positive')
target=out/'stopped.json'
if target.exists():raise ValueError('Fresh stop receipt required')
target.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owned_verified_pid':74376,'reason':'Broader r5 planner retains existing-return choices and can add a physically legal source-rooted ground stitch; avoid running duplicate narrower negative searches','examined_completed_nets':len(routes['results']),'accepted':0,'not_a_global_no_path_result':True,'preserved_partial_files':{str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in out.iterdir() if q.is_file()},'successor':'new-via-escape-r5','native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print(target)
