"""Remove doubled CR introduced by the preceding status writer; no content changes."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/pre-hardware-characterization-20261001/status-line-ending-correction-r01';OUT.mkdir(exist_ok=False)
writer=ROOT/'reports/pre-hardware-characterization-20261001/record_stateful_characterization_r03.py'
shutil.copyfile(writer,OUT/writer.name)
rows=[]
for name in ('PROJECT_MEMORY.md','reports/ENGINEERING_STATUS.md','docs/CURRENT_ACCEPTANCE_GATES.md'):
    p=ROOT/name;before=p.read_bytes();after=before.replace(b'\r\r\n',b'\r\n')
    assert before.count(b'\r\r\n')>0 and b'\r\r\n'not in after
    (OUT/p.name).write_bytes(before)
    p.write_bytes(after)
    rows.append(dict(path=name,doubled_sequences_removed=before.count(b'\r\r\n'),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest()))
(OUT/'receipt.json').write_text(json.dumps(dict(passed=True,changes=rows,semantic_content_changed=False,electrical_source_or_PCB_modified=False),indent=2)+'\n')
