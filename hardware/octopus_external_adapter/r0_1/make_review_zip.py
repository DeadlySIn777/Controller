"""Freeze the reviewed CAD/DFM package. This never generates fabrication files."""
from pathlib import Path
import hashlib
import json
import zipfile

R=Path(__file__).resolve().parent
def digest(b):return hashlib.sha256(b).hexdigest()
status=json.loads((R/'verification.json').read_text())
assert status['manufacturing_ready'] is False
assert status['prototype_order_ready'] is False
for rel,expected in status['files'].items():
    assert digest((R/rel).read_bytes())==expected, f'Stale verification: {rel}'
include=[]
for path in sorted(R.iterdir()):
    if path.is_file() and path.suffix in {'.md','.py','.json','.csv','.svg','.png','.pdf','.step','.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_sym'}:
        if path.name not in {'review_package_manifest.json','schematic-erc.json'}:
            include.append(path)
include += [R/'adapter.net.xml',R/'fp-lib-table',R/'sym-lib-table']
include += sorted((R/'Adapter.pretty').glob('*.kicad_mod'))
include += [R/'evidence'/'pcb-final-drc.json',R/'evidence'/'schematic-final-erc.json']
manifest=dict(status='ENGINEERING REVIEW ONLY - NOT FOR ORDER OR MANUFACTURE',
    generated_fabrication_files=False,submitted_to_pcbway=False,
    scope='Standalone Octopus adapter; main controller sources excluded',
    files={p.relative_to(R).as_posix():digest(p.read_bytes()) for p in sorted(include)})
mp=R/'review_package_manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
include.append(mp)
dest=R.parent/'OEA-r0.1-PCBWay-REVIEW-NOT-FOR-ORDER.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for path in include:z.write(path,arcname='OEA-r0.1-review/'+path.relative_to(R).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    for rel,expected in manifest['files'].items():
        assert digest(z.read('OEA-r0.1-review/'+rel))==expected
print(json.dumps(dict(archive=str(dest),files=len(include),size_bytes=dest.stat().st_size,sha256=digest(dest.read_bytes()),manufacturing_ready=False)))
