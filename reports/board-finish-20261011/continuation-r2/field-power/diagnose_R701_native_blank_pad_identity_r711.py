import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
p = psutil.Process(); p.cpu_affinity(list(range(16, 28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json, pickle, hashlib, sys
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'sbc-power'))
import contact_layout as L
import ordinary_routes as O
M = ROOT / 'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
NG = ROOT / 'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-geometry.json'
OUT = H / 'R701-native-blank-pad-identity-diagnosis-r711'
assert not OUT.exists(); OUT.mkdir()
g, h, b, q, c = pickle.loads(M.read_bytes())
ng = json.loads(NG.read_bytes())
rows = {'host_U11017_pads': [], 'actual_native_U11017_pads': [], 'actual_unmapped': []}
def shapeinfo(x):
    return {'type': x.geom_type, 'bounds': list(x.bounds) if not x.is_empty else None, 'area_mm2': x.area, 'sha256': hashlib.sha256(x.wkb).hexdigest()}
for pad in h['pads']:
    if pad['ref'] == 'U11017':
        rows['host_U11017_pads'].append({k: v for k, v in pad.items() if k not in ('layers', 'hole')} | {'layer_shapes': {layer: [shapeinfo(s) for s in L.poly(records)] for layer, records in pad['layers'].items()}, 'hole_record': pad.get('hole')})
index = {}
for pad in h['pads']:
    index.setdefault((pad['ref'], str(pad['num']), pad['x'], pad['y'], pad['net']), []).append(pad)
for pad in ng['pads']:
    options = index.get((pad['ref'], str(pad['num']), *pad['at'], pad['net']), [])
    if pad['ref'] == 'U11017':
        rows['actual_native_U11017_pads'].append(pad)
    if len(options) != 1:
        rows['actual_unmapped'].append(pad)
(OUT / 'receipt.json').write_text(json.dumps({'status': 'NATIVE_IDENTITY_DIAGNOSIS_NO_EXCLUSION_OR_MUTATION', 'model_SHA256': hashlib.sha256(M.read_bytes()).hexdigest(), 'native_SHA256': hashlib.sha256(NG.read_bytes()).hexdigest(), **rows}, indent=1, allow_nan=False) + '\n', encoding='utf-8')
print('R711', hashlib.sha256((OUT / 'receipt.json').read_bytes()).hexdigest(), 'unmapped', len(rows['actual_unmapped']))
