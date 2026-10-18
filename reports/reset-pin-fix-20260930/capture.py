"""Capture the actual scoped source fix and native checks; no machine interface."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[1]
if (REPORT/'review.json').exists():
    raise RuntimeError('This completed evidence capture is immutable. Use a fresh report directory for another run.')
KICAD = Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
CORE = ROOT/'hardware/fpga_core'
commands = []

def run(name, argv, cwd=ROOT):
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    proc = subprocess.run([str(a) for a in argv], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (REPORT/(name+'.stdout.txt')).write_text(proc.stdout, encoding='utf-8')
    (REPORT/(name+'.stderr.txt')).write_text(proc.stderr, encoding='utf-8')
    commands.append({'name':name, 'argv':[str(a) for a in argv], 'cwd':str(cwd), 'started_utc':started,
                     'elapsed_s':round(time.monotonic()-tick,3), 'exit_code':proc.returncode})
    (REPORT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n', encoding='utf-8')
    if proc.returncode:
        raise RuntimeError(name+' failed: '+proc.stderr)
    return proc

run('kicad-version', [KICAD, '--version'])
run('builder', [sys.executable, ROOT/'tools/hardware_build_fpga_core.py'])
run('native-netlist', [KICAD, 'sch', 'export', 'netlist', '--format', 'kicadxml', '--output', CORE/'netlist.xml', CORE/'fpga_core.kicad_sch'])
run('native-erc', [KICAD, 'sch', 'erc', '--format', 'json', '--severity-error', '--severity-warning', '--output', CORE/'erc.json', CORE/'fpga_core.kicad_sch'])
run('native-pdf', [KICAD, 'sch', 'export', 'pdf', '--output', CORE/'fpga_core.pdf', CORE/'fpga_core.kicad_sch'])
run('validator', [sys.executable, ROOT/'tools/hardware_validate_fpga_core.py'])

# Render the actual native PDF. No substitute drawing or fabricated evidence.
import fitz
doc = fitz.open(CORE/'fpga_core.pdf')
page = doc[0]
page.get_pixmap(matrix=fitz.Matrix(.5,.5), alpha=False).save(CORE/'overview.png')
for name, box, scale in (
    ('configuration-detail', (560,60,1140,360), 1.5),
    ('pin-detail', (140,55,440,240), 2),
    ('supply-detail', (560,365,1140,580), 1.5),
    ('boundary-detail', (550,580,1140,815), 1.5),
    ('reset-detail', (1000,120,1130,290), 2),
):
    clip=fitz.Rect(*(v*72/25.4 for v in box))
    target = REPORT/(name+'.png') if name=='reset-detail' else CORE/(name+'.png')
    page.get_pixmap(matrix=fitz.Matrix(scale,scale), clip=clip, alpha=False).save(target)
shutil.copy2(CORE/'overview.png', REPORT/'overview.png')

after = REPORT/'after'
files = [ROOT/p for p in ('tools/hardware_build_fpga_core.py','tools/hardware_validate_fpga_core.py','tests/test_fpga_core.py')]
files.extend(p for p in CORE.iterdir() if p.is_file())
design=json.loads((CORE/'design.json').read_text(encoding='utf-8'))
files.extend(ROOT/'research/fpga-core'/n for n in design['source_sha256'])
for path in files:
    dest=after/path.relative_to(ROOT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,dest)

# Same frozen copied source/native artifacts are independently host-tested.
test_result=run('frozen-focused-tests', [sys.executable,'-m','unittest','discover','-s','tests','-p','test_fpga_core.py','-v'], cwd=after)
test_count=int(re.search(r'Ran (\d+) tests?',test_result.stderr).group(1))
if not test_result.stderr.rstrip().endswith('OK'):
    raise RuntimeError('focused test summary is not a clean OK result')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
hashes={str(path.relative_to(ROOT)).replace('\\','/'):sha(after/path.relative_to(ROOT)) for path in files}
(REPORT/'after-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
before=json.loads((REPORT/'before-sha256.json').read_text(encoding='utf-8'))
changed=[p for p,h in before.items() if hashes.get(p)!=h]
patch=[]
for rel in ('tools/hardware_build_fpga_core.py','tools/hardware_validate_fpga_core.py','tests/test_fpga_core.py'):
    a=(REPORT/'before'/rel).read_text(encoding='utf-8').splitlines(keepends=True)
    b=(after/rel).read_text(encoding='utf-8').splitlines(keepends=True)
    patch.extend(difflib.unified_diff(a,b,fromfile='before/'+rel,tofile='after/'+rel))
(REPORT/'task-source-diff.patch').write_text(''.join(patch),encoding='utf-8')

erc=json.loads((after/'hardware/fpga_core/erc.json').read_text(encoding='utf-8'))
tree=ET.parse(after/'hardware/fpga_core/netlist.xml')
pins=tree.findall("libparts/libpart[@part='74LVC1G17GW']/pins/pin")
u4={}
for net in tree.findall('nets/net'):
    for node in net.findall("node[@ref='U4']"):
        u4[node.attrib['pin']]=net.attrib['name'].removeprefix('/')
validation=json.loads((after/'hardware/fpga_core/validation.json').read_text(encoding='utf-8'))
review={'captured_utc':datetime.now(timezone.utc).isoformat(), 'scope':'FPGA reset-buffer pin correction only',
        'revision':design['revision'], 'kicad_version':erc['kicad_version'],
        'native_erc_violation_count':sum(len(s['violations']) for s in erc['sheets']),
        'native_erc_included_severities':erc['included_severities'], 'native_erc_ignored_checks':erc['ignored_checks'],
        'native_reset_buffer_symbol':{p.attrib['num']:p.attrib['name'] for p in pins},
        'native_u4_pin_nets':u4, 'validation_ok':validation['ok'],
        'focused_tests':{'executed':test_count,'failures':0,'errors':0,'skips':0,'source':'frozen-focused-tests.stderr.txt'},
        'task_changed_preexisting_files':changed, 'new_primary_binding':'74LVC1G17.txt',
        'manufacturing_ready':False, 'physical_qualification':False,
        'limitations':['Host tests and native ERC do not prove electrical operation or reset timing.',
                       'No FPGA vendor placement/routing, bitstream, PCB DRC or physical test was performed.',
                       'Cold/warm RC discharge, Schmitt thresholds, service hold and partial-power behavior remain unqualified.',
                       'These files do not implement IS-1 eight-plus-four/full-I/O hardware or integrated independent inhibit.']}
(REPORT/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'revision':review['revision'],'native_erc_violations':review['native_erc_violation_count'],
                  'frozen_focused_tests':test_count,'validation_ok':review['validation_ok'],'changed_files':len(changed)}))
