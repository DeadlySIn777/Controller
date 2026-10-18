import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
STAGE=REPORT/'r13-1585-staged-source'
LIVE=ROOT/'hardware/motherboard'
validation=json.loads((REPORT/'r13-1585-independent-validation.json').read_text())
erc=json.loads((REPORT/'r13-1585-modules-erc.json').read_text())
violations=[v for s in erc['sheets'] for v in s['violations']]
assert validation['source_checks_pass'] and not erc['ignored_checks']
assert not any(v['severity']=='error' for v in violations)
assert len(json.loads((STAGE/'design.json').read_text())['components'])==1585
ARCHIVE=REPORT/'before-r13-1469'
assert not ARCHIVE.exists()
shutil.copytree(LIVE,ARCHIVE)
for f in STAGE.iterdir():
    if f.is_file():shutil.copyfile(f,LIVE/f.name)
    elif f.is_dir():shutil.copytree(f,LIVE/f.name,dirs_exist_ok=True)
hashes={p.relative_to(LIVE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in LIVE.rglob('*') if p.is_file()}
receipt=dict(adopted_after_native_validation=True,physical_parts=1585,errors=0,warnings=len(violations),
    source=str(STAGE.relative_to(ROOT)),hashes=hashes,manufacturing_ready=False,
    scope='Original327 preserved with exact66NC promotions; power-entry contacts; actual compute/ESP sockets; process68 plus actualACC48 provider. Analog/comms, terminals, storage, LEDs and routing remain unfinished.')
(REPORT/'r13-1585-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('physical_parts','errors','warnings','manufacturing_ready')}))
