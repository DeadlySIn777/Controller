"""Compare unchanged TI PSpice/TINA releases using their distinct documented pin orders."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess
HERE=Path(__file__).resolve().parent
OUT=HERE/'INA149-vendor-variant-compatibility-r01';OUT.mkdir(exist_ok=False)
TEMPLATE=HERE/'INA149-bidirectional-nominal-r01/rshunt-1e+12-step-5ns/nominal.cir'
TINA=HERE/'INA149-active-model-discovery-r01/SBOM668/INA149_TINA_AIO/INA149.lib'
ORIGINAL=HERE/'INA149-active-model-discovery-r01/SBOMC47/ina149.lib'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
before={str(p):sha(p) for p in (TEMPLATE,TINA,ORIGINAL,Path(__file__))}
assert '.SUBCKT INA149 +IN REF_A V+ VOUT V- REF_B -IN' in TINA.read_text()
assert '.subckt INA149 +IN -IN REF_A REF_B V+ V- VOUT' in ORIGINAL.read_text()
shutil.copyfile(TINA,OUT/'original-TINA-INA149.lib')
shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
rows=[]
for mode in ('psa','ps'):
    folder=OUT/mode;folder.mkdir()
    text=TEMPLATE.read_text()
    text=re.sub(r'(?m)^\.include "[^"]*/ina149.lib"$',f'.include "{unix(OUT/"original-TINA-INA149.lib")}"',text)
    assert '.include "'+unix(OUT/'original-TINA-INA149.lib')+'"' in text
    assert text.count('XINA P N REF REF VCC AGND SHIFT INA149')==1
    text=text.replace('XINA P N REF REF VCC AGND SHIFT INA149','XINA P REF VCC SHIFT AGND REF N INA149')
    deck=folder/'variant.cir';deck.write_text(text)
    command=['wsl','-d','GarciaMechBuilder','--cd',unix(folder),'--','ngspice','-n','-D','ngbehavior='+mode,'-b',unix(deck)]
    try:
        r=subprocess.run(command,capture_output=True,timeout=120)
        log=(r.stdout+r.stderr).decode('utf8',errors='replace');code=r.returncode
    except subprocess.TimeoutExpired as ex:
        log=((ex.stdout or b'')+(ex.stderr or b'')).decode('utf8',errors='replace');code=None
    (folder/'ngspice.log').write_text(log)
    measured={k:float(v)for k,v in re.findall(r'(?m)^\s*(initial_out|final_out|recovered_out)\s*=\s*([\d.eE+-]+)',log)}
    errors=re.findall(r'(?im)^.*(?:error:|simulation\(s\) aborted|timestep too small|no such vector|failed!).*$',log)
    expected={'initial_out':6.249706263805601,'final_out':1.2499412527611202,'recovered_out':6.249706263805601}
    row=dict(mode=mode,returncode=code,passed=code==0 and not errors and len(measured)==3 and all(abs(measured[k]-v)<.01 for k,v in expected.items()),measurements=measured,errors=errors,deck_sha256=sha(deck),log_sha256=sha(folder/'ngspice.log'))
    rows.append(row);print(json.dumps(row),flush=True)
(OUT/'receipt.json').write_text(json.dumps(dict(cases=rows,input_sha256=before,inputs_unchanged=before=={str(p):sha(p) for p in (TEMPLATE,TINA,ORIGINAL,Path(__file__))},
    scope='Compatibility exploration of two original vendor releases; TINA top-level model pin order explicitly differs from PSpice',
    whole_analog_chain_passed=False,physical_qualified=False,manufacturing_ready=False),indent=2)+'\n')
