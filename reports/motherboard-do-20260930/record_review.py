"""Freeze exact DO inputs and record fresh scoped checks; no release claim."""
import datetime, hashlib, json, re, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
inputs=list((ROOT/'hardware/motherboard_do').rglob('*'))+[ROOT/'tools/hardware_build_motherboard_do.py',ROOT/'tools/hardware_validate_motherboard_do.py',ROOT/'tests/test_motherboard_do.py']
inputs=[p for p in inputs if p.is_file() and p.suffix not in ['.kicad_prl']]
before={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
runs=[]
for pattern in ['test_motherboard_do.py','test_motherboard_di.py','test_motherboard_motors.py']:
    command=['C:/Python314/python.exe','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v']
    p=subprocess.run(command,cwd=ROOT,text=True,encoding='utf-8',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    logfile=OUT/(pattern.removesuffix('.py')+'.txt'); logfile.write_text(p.stdout,encoding='utf-8')
    match=re.search(r'Ran (\d+) tests?',p.stdout)
    runs.append({'command':command,'returncode':p.returncode,'tests':int(match.group(1)) if match else None,'log':logfile.name})
after={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
changed=[name for name in before if before[name]!=after[name]]
for p in inputs:
    destination=OUT/'source'/p.relative_to(ROOT); destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists() and destination.read_bytes()!=p.read_bytes(): raise ValueError('Immutable snapshot differs: '+str(p))
    if not destination.exists(): shutil.copyfile(p,destination)
erc=json.loads((ROOT/'hardware/motherboard_do/erc.json').read_text()); vs=[v for s in erc['sheets'] for v in s['violations']]
receipt={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'One-motherboard sixteen sourcing-DO frontend source r0.1',
 'physical_components':110,'numbered_electrical_copper_pads':552,'unnumbered_paste_only_apertures':228,
 'native_ERC':{'errors':sum(v['severity']=='error' for v in vs),'warnings':sum(v['severity']=='warning' for v in vs),'ignored_checks':erc['ignored_checks'],
 'warning_justification':'Exactly two ISO7762 GND2 pin9 ground-name warnings, connected to the independently checked isolated FIELD_A/B_0V returns.'},
 'native_footprint_loading':json.loads((OUT/'native-footprint-review.json').read_text())['ok'],
 'independent_source_validation':json.loads((ROOT/'hardware/motherboard_do/validation.json').read_text())['ok'],
 'test_runs':runs,'total_scoped_tests':sum(r['tests'] or 0 for r in runs),'input_hashes':before,'changed_inputs_during_tests':changed,
 'manufacturing_ready':False,'PCB_DRC':'not applicable to this source region; final parent PCB required',
 'target_firmware_compilation':'not implemented','physical_measurements':'not performed',
 'parent_engineering_gaps':json.loads((ROOT/'hardware/motherboard_do/design.json').read_text())['unimplemented_parent_obligations'],
 'cost_boundary':'The frozen701/699-part cost receipt is unchanged. These110 frontend parts need a future exact integrated recost.'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'ok':not changed and all(r['returncode']==0 for r in runs),'tests':receipt['total_scoped_tests'],'frozen_inputs':len(before),'changed':changed}))
raise SystemExit(bool(changed) or any(r['returncode'] for r in runs))
