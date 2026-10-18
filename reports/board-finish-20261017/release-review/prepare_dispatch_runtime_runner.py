from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
source=H.parent/'efinity-bram-behavior-r1/run_isolated_runtime.py'
target=H/'event-dispatch-r1/run_full_runtime_with_dispatch.py'
old=source.read_text()
marker=' if args.mutation:\n'
assert old.count(marker)==1 and not target.exists()
overlay=" shutil.copyfile(Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261017/release-review/event-dispatch-r1/cnc3_runtime_events.v'),inputs/'cnc3_runtime_events.v')\n"
target.write_text(old.replace(marker,overlay+marker))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(target.parent/'runtime-runner-derivation.json').write_text(json.dumps({'source':str(source),'source_SHA256':sha(source),'candidate_runner_SHA256':sha(target),'only_runner_delta':'additional isolated cnc3_runtime_events.v copy overlay; existing tests and two-CPU controls unchanged','adopted':False},indent=2)+'\n')
print(target)
