"""Test unchanged vendor-model numerical completion over actual AI input common modes."""
from pathlib import Path
import hashlib, json, re, subprocess
HERE=Path(__file__).resolve().parent
OUT=HERE/'INA149-common-mode-exploration-r04';OUT.mkdir(exist_ok=False)
TEMPLATE=HERE/'INA149-vendor-variant-compatibility-r01/psa/variant.cir'
MODELS=[HERE/'INA149-vendor-variant-compatibility-r01/original-TINA-INA149.lib',
        HERE/'INA149-initialization-exploration-r02/OPAx197.LIB']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unix=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
before={str(p):sha(p)for p in [TEMPLATE,*MODELS,Path(__file__)]}
rows=[]
for cm,initial,final in [(-10,10,0),(0,10,0),(10,10,0),(-10,6,4),(0,6,4),(10,6,4)]:
    folder=OUT/f'cm-{cm}-initial-{initial}';folder.mkdir()
    text=TEMPLATE.read_text().replace('V=-10+v(D)/2',f'V={cm}+v(D)/2').replace('V=-10-v(D)/2',f'V={cm}-v(D)/2')
    text=text.replace('DC 10 PULSE(10 0 10u 10n 10n 40u 80u)',f'DC {initial} PULSE({initial} {final} 10u 10n 10n 40u 80u)')
    text=text.replace('v(shift)=12.5 v(scaled)=6.25 v(buf)=6.25 v(adc)=6.25',f'v(shift)={initial+2.5} v(scaled)={(initial+2.5)/2} v(buf)={(initial+2.5)/2} v(adc)={(initial+2.5)/2}')
    deck=folder/'actual-path.cir';deck.write_text(text,encoding='utf8',newline='\n')
    cmd=['wsl','-d','GarciaMechBuilder','--cd',unix(folder),'--','ngspice','-n','-D','ngbehavior=psa','-b',unix(deck)]
    try:
        r=subprocess.run(cmd,capture_output=True,timeout=180);code=r.returncode;raw=r.stdout+r.stderr
    except subprocess.TimeoutExpired as e:
        code=None;raw=(e.stdout or b'')+(e.stderr or b'')
    (folder/'ngspice.log').write_bytes(raw);log=raw.decode('utf8',errors='replace')
    errors=re.findall(r'(?im)^.*(?:error:|simulation\(s\) aborted|timestep too small|no such vector|failed!).*$',log)
    measured={k:float(v)for k,v in re.findall(r'(?m)^\s*(initial_out|final_out|recovered_out)\s*=\s*([\d.eE+-]+)',log)}
    expected={'initial_out':(initial+2.5)/2*1e6/(1e6+47),'final_out':(final+2.5)/2*1e6/(1e6+47),'recovered_out':(initial+2.5)/2*1e6/(1e6+47)}
    row=dict(common_mode_V=cm,initial_differential_V=initial,final_differential_V=final,exit_code=code,
             passed=code==0 and not errors and len(measured)==3 and all(abs(measured[k]-v)<.01 for k,v in expected.items()),
             measurements=measured,errors=errors,deck_sha256=sha(deck),log_sha256=sha(folder/'ngspice.log'))
    rows.append(row);print(json.dumps(row),flush=True)
receipt=dict(cases=rows,input_sha256=before,source_unchanged=all(sha(Path(p))==h for p,h in before.items()),
             scope='Original TI TINA INA149 plus OPA model, ideal sources and ADC approximation; nominal25C15V diagnostic exploration only',
             whole_analog_chain_passed=False,physical_qualified=False,manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
