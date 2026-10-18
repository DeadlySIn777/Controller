"""Bounded nominal transient and solver-sensitivity evidence; no full analog claim."""
from pathlib import Path
import hashlib,json,math,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE/'INA149-bidirectional-nominal-r01';OUT.mkdir(exist_ok=False)
TEMPLATE=HERE/'INA149-initialization-exploration-r02/actual_ground_descending_nodeset/case.cir'
SOURCE=ROOT/'hardware/motherboard/design.json'
NATIVE=ROOT/'hardware/motherboard/netlist.xml'
BINDING=HERE/'AI-buffer-SPICE-full-r02/receipt.json'
INA=HERE/'INA149-active-model-discovery-r01/SBOMC47/ina149.lib'
OPA=HERE/'AI-active-model-discovery-r01/SBOMA34/OPAx197.LIB'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
binding=json.loads(BINDING.read_text())
assert binding['passed'] and binding['source_unchanged']
for p in (SOURCE,NATIVE,INA,OPA):assert binding['input_sha256'][str(p)]==sha(p)
inputs={str(p.relative_to(ROOT)):sha(p) for p in (SOURCE,NATIVE,INA,OPA,BINDING,TEMPLATE,Path(__file__))}
retained=OUT/'inputs';retained.mkdir()
for i,p in enumerate(map(lambda q:ROOT/q,inputs)):
    shutil.copyfile(p,retained/f'{i}-{p.name}')
rows=[];waves=[]
for shunt,step in [(1e12,5),(1e11,5),(1e13,5),(1e12,1)]:
    folder=OUT/f'rshunt-{shunt:.0e}-step-{step}ns';folder.mkdir()
    text=TEMPLATE.read_text().replace('tran 5n 45u',f'tran {step}n 79u')
    text=text.replace('rshunt=1e12',f'rshunt={shunt:.0e}')
    text=text.replace('meas tran final_out avg output from=40u to=44u',
                      'meas tran final_out avg output from=40u to=44u\nmeas tran recovered_out avg output from=74u to=78u')
    deck=folder/'nominal.cir';deck.write_text(text)
    cmd=['wsl','-d','GarciaMechBuilder','--cd',unix(folder),'--','ngspice','-n','-D','ngbehavior=psa','-b',unix(deck)]
    started=time.monotonic()
    try:
        result=subprocess.run(cmd,capture_output=True,timeout=180)
        log=(result.stdout+result.stderr).decode('utf8',errors='replace');rc=result.returncode
    except subprocess.TimeoutExpired as ex:
        log=((ex.stdout or b'')+(ex.stderr or b'')).decode('utf8',errors='replace');rc=None
    logfile=folder/'ngspice.log';logfile.write_text(log)
    waveform=folder/'transient.txt';samples=[]
    if waveform.exists():
        for line in waveform.read_text().splitlines()[1:]:
            sample=list(map(float,line.split()))
            assert len(sample)==5 and all(math.isfinite(x)for x in sample)
            samples.append(sample)
    errors=re.findall(r'(?im)^.*(?:error:|simulation\(s\) aborted|timestep too small|no such vector|failed!).*$',log)
    measured={k:float(v) for k,v in re.findall(r'(?m)^\s*(initial_out|final_out|recovered_out)\s*=\s*([\d.eE+-]+)',log)}
    expected={'initial_out':6.249706263805601,'final_out':1.2499412527611202,'recovered_out':6.249706263805601}
    checks={'both_directions_reach_final':len(measured)==3 and all(abs(measured[k]-v)<.01 for k,v in expected.items()),
            'complete_waveform':bool(samples)and samples[-1][0]>=78.999e-6,
            'no_nan_or_infinity':bool(samples),
            'within_ADC_nominal_range':bool(samples)and all(0<r[4]<10.24 for r in samples)}
    passed=rc==0 and not errors and all(checks.values())
    row=dict(shunt_ohm=shunt,max_step_ns=step,passed=passed,checks=checks,measured=measured,expected=expected,errors=errors,
             seconds=time.monotonic()-started,returncode=rc,deck_sha256=sha(deck),log_sha256=sha(logfile),
             waveform_sha256=sha(waveform)if waveform.exists()else None)
    rows.append(row);waves.append(samples);write(OUT/'checkpoint.json',rows)
    print(json.dumps(row),flush=True)
    if not passed:break
unchanged=inputs=={str(p.relative_to(ROOT)):sha(p)for p in (SOURCE,NATIVE,INA,OPA,BINDING,TEMPLATE,Path(__file__))}
delta=None
if len(rows)==4 and all(r['passed']for r in rows):
    delta=max(abs(r['measured'][k]-rows[0]['measured'][k]) for r in rows[1:]for k in expected)
passed=unchanged and len(rows)==4 and all(r['passed']for r in rows)and delta is not None and delta<.001
receipt=dict(passed=passed,input_sha256=inputs,source_unchanged=unchanged,cases=rows,solver_sensitivity_max_final_V=delta,
             source_channel=0,source_references=binding['source_channels'][0],whole_analog_chain_passed=False,
             physical_qualified=False,manufacturing_ready=False,scope='Single exact-Source26 INA149/divider/OPA/filter path, 15V ideal supply, 2.5V ideal reference,25C, -10V common mode, 10→0→10V differential. All original vendor devices retained; .nodeset is only a solver initial guess.',
             remaining=['Four-channel simultaneous corners still fail model convergence','No protected-terminal transient/load protection model','ADC only 1Mohm load approximation; no sampling/quantization/ENOB','No power-up/rail/reference dynamics','No minimum/maximum IC process coverage','No PCB/cable parasitics or physical qualification'])
write(OUT/'receipt.json',receipt)
raise SystemExit(0 if passed else 1)
