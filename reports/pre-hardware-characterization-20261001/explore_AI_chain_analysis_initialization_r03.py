"""Isolate analysis-order convergence without changing either manufacturer's model."""
from pathlib import Path
import hashlib, json, re, subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE / 'AI-chain-analysis-initialization-r03'
OUT.mkdir(exist_ok=False)
DECK = HERE / 'AI-chain-TINA-initialized-quick-r02/case-00/actual-path.cir'
MODELS = [HERE / 'AI-active-model-discovery-r01/SBOMA34/OPAx197.LIB',
          HERE / 'INA149-active-model-discovery-r01/SBOM668/INA149_TINA_AIO/INA149.lib']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
unix = lambda p: '/mnt/' + p.drive[0].lower() + p.as_posix()[2:]
before = {str(p): sha(p) for p in [DECK, *MODELS, Path(__file__)]}
rows = []
for variant in ['transient-only', 'reset-between-analyses', 'transient-only-nominal-passives']:
    folder = OUT / variant
    folder.mkdir()
    text = DECK.read_text()
    if variant.startswith('transient-only'):
        text = re.sub(r'(?ms)^ac dec 100 10 10Meg\n.*?(?=^tran )', '', text)
    else:
        text = text.replace('tran 5n 40u', 'reset\ntran 5n 40u')
    if variant.endswith('nominal-passives'):
        text = re.sub(r'(?m)^(RUP\d .+ )9990$', r'\g<1>10000', text)
        text = re.sub(r'(?m)^(RDOWN\d .+ )10010(?:\.0+)?$', r'\g<1>10000', text)
        text = re.sub(r'(?m)^(RFILTER\d .+ )46\.53$', r'\g<1>47', text)
        text = re.sub(r'(?m)^(CFILTER\d .+ )[^\s]+$', r'\g<1>2.2e-9', text)
        text = re.sub(r'v\((scaled|buf|adc)(\d)\)=([\d.]+)',
                      lambda m: 'v(' + m[1] + m[2] + ')=' + ('6.25' if int(m[2]) < 2 else '4.25'), text)
    deck = folder / 'actual-path.cir'
    deck.write_text(text, encoding='utf8', newline='\n')
    command = ['wsl', '-d', 'GarciaMechBuilder', '--cd', unix(folder), '--', 'ngspice',
               '-n', '-D', 'ngbehavior=psa', '-b', unix(deck)]
    try:
        run = subprocess.run(command, capture_output=True, timeout=180)
        code, log = run.returncode, run.stdout + run.stderr
    except subprocess.TimeoutExpired as exc:
        code, log = None, (exc.stdout or b'') + (exc.stderr or b'')
    (folder / 'ngspice.log').write_bytes(log)
    errors = re.findall(r'(?im)^.*(?:error:|simulation\(s\) aborted|timestep too small|no such vector|failed!).*$', log.decode('utf8', errors='replace'))
    wave = folder / 'transient.txt'
    endpoint = None
    if wave.exists():
        endpoint = [float(v) for v in wave.read_text().splitlines()[-1].split()]
    rows.append(dict(variant=variant, exit_code=code, numerical_completion=code == 0 and not errors and endpoint is not None and endpoint[0] >= 39.999e-6,
                     endpoint=endpoint, errors=errors, deck_sha256=sha(deck), log_sha256=sha(folder/'ngspice.log')))
    print(json.dumps(rows[-1]), flush=True)
receipt = dict(cases=rows, input_sha256=before, source_unchanged=all(sha(Path(p)) == h for p, h in before.items()),
               scope='Diagnostic numerical exploration only; no active device edited or replaced, no measured hardware limits',
               whole_analog_chain_passed=False, physical_qualified=False, manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
