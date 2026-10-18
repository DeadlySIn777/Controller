"""Preserve the exact generated source for a failed constructor traceback."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_A_preserved_serialized_grafts_r461.py'
ns={'__file__':str(owner),'__name__':'_inspect_generated_source_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
O=H/'FIELD5-R461-failure-exact-generated-source-r463';O.mkdir(exist_ok=False)
(O/'generated-source.txt').write_text(ns['s'],encoding='utf-8')
lines=ns['s'].splitlines()
for i in range(60,80):print(str(i+1)+': '+lines[i])
