"""Numerical initialization study; unchanged vendor models, no circuit adoption."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'INA149-initialization-exploration-r02'
OUT.mkdir(exist_ok=False)
INA = HERE / 'INA149-active-model-discovery-r01/SBOMC47/ina149.lib'
OPA = HERE / 'AI-active-model-discovery-r01/SBOMA34/OPAx197.LIB'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p): return '/mnt/' + p.drive[0].lower() + p.as_posix()[2:]
def write(p,v): p.write_text(json.dumps(v,indent=2)+'\n')
inputs = {str(p.relative_to(ROOT)):sha(p) for p in (INA,OPA,Path(__file__))}
for p in (INA,OPA,Path(__file__)): shutil.copyfile(p,OUT/p.name)

CASES = [
 ('actual_ground_descending', 0, 10, 0, ''),
 ('actual_ground_low_nodeset', 0, 0, 10, '.nodeset v(shift)=2.5 v(scaled)=1.25 v(buf)=1.25 v(adc)=1.25 v(xina.xu1.7)=7.5'),
 ('actual_ground_descending_nodeset', 0, 10, 0, '.nodeset v(shift)=12.5 v(scaled)=6.25 v(buf)=6.25 v(adc)=6.25 v(xina.xu1.7)=7.5'),
 ('centered_reference', -7.5, 0, 10, ''),
 ('centered_reference_descending', -7.5, 10, 0, ''),
 ('offset_reference', -6.5, 0, 10, ''),
 ('offset_reference_descending', -6.5, 10, 0, ''),
]
rows=[]
for name,offset,initial,final,nodeset in CASES:
    case=OUT/name;case.mkdir()
    deck=case/'case.cir'
    deck.write_text(f'''Unchanged INA149 and OPA models; numerical initialization exploration only
.include "{unix(OUT/INA.name)}"
.include "{unix(OUT/OPA.name)}"
VGROUND AGND 0 {offset}
VCC VCC AGND 15
VREF REF AGND 2.5
VD D 0 DC {initial} PULSE({initial} {final} 10u 10n 10n 40u 80u)
BP P AGND V=-10+v(D)/2
BN N AGND V=-10-v(D)/2
XINA P N REF REF VCC AGND SHIFT INA149
RUP SHIFT SCALED 10k
RDOWN SCALED AGND 10k
XBUF SCALED BUF VCC AGND BUF OPAx197
RF BUF ADC 47
CF ADC AGND 2.2n
RADC_APPROX ADC AGND 1Meg
.temp 25
.options method=gear maxord=2 rshunt=1e12 itl1=500 itl4=500
{nodeset}
.control
set noaskquit
set wr_singlescale
set wr_vecnames
tran 5n 45u
let shifted=v(shift)-v(agnd)
let buffered=v(buf)-v(agnd)
let output=v(adc)-v(agnd)
wrdata transient.txt v(d) shifted buffered output
meas tran initial_out avg output from=8u to=9u
meas tran final_out avg output from=40u to=44u
quit
.endc
.end
''')
    cmd=['wsl','-d','GarciaMechBuilder','--cd',unix(case),'--','ngspice','-n','-D','ngbehavior=psa','-b',unix(deck)]
    started=time.monotonic()
    try:
        run=subprocess.run(cmd, capture_output=True, timeout=75)
        log=(run.stdout+run.stderr).decode('utf8',errors='replace');rc=run.returncode
    except subprocess.TimeoutExpired as ex:
        log=((ex.stdout or b'')+(ex.stderr or b'')).decode('utf8',errors='replace');rc=None
    (case/'ngspice.log').write_text(log)
    measured={k:float(v) for k,v in re.findall(r'(?m)^\s*(initial_out|final_out)\s*=\s*([\d.eE+-]+)',log)}
    errors=re.findall(r'(?im)^.*(?:error:|simulation\(s\) aborted|timestep too small|no such vector|failed!).*$',log)
    expected={k:(v+2.5)*.5*1e6/(1e6+47) for k,v in [('initial_out',initial),('final_out',final)]}
    passed=rc==0 and not errors and len(measured)==2 and all(abs(measured[k]-v)<.01 for k,v in expected.items())
    row=dict(name=name,passed=passed,offset_V=offset,initial_V=initial,final_V=final,measured=measured,expected=expected,errors=errors,returncode=rc,elapsed_s=time.monotonic()-started,deck_sha256=sha(deck),log_sha256=sha(case/'ngspice.log'))
    rows.append(row);write(OUT/'checkpoint.json',rows)
    print(json.dumps(row),flush=True)
unchanged=inputs=={str(p.relative_to(ROOT)):sha(p) for p in (INA,OPA,Path(__file__))}
write(OUT/'receipt.json',dict(scope='Numerical initialization exploration only; ideal protection/reference/power and approximate ADC load',inputs=inputs,inputs_unchanged=unchanged,cases=rows,whole_analog_chain_passed=False,physical_qualified=False,manufacturing_ready=False))
