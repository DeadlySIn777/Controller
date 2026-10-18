"""Isolated pin-set and conservative copper-pad gap checks; not board DRC."""
from pathlib import Path
import hashlib
import itertools
import json
import math
import pcbnew as p

root=Path(__file__).resolve().parent
base=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
source=root/'logic_spec.json'
spec=json.loads(source.read_text(encoding='utf-8'))
checked=[]
issues=[]
for ref,part in spec['parts'].items():
    lib,name=part['footprint'].split(':')
    folder=(root.parent/'r0_2'/'Adapter.pretty') if lib=='Adapter' else base/(lib+'.pretty')
    fp=p.FootprintLoad(str(folder), name)
    if fp is None:
        issues.append(ref+': footprint missing')
        continue
    pads=[x for x in fp.Pads() if x.GetNumber()]
    if set(x.GetNumber() for x in pads)!=set(part['pins']):
        issues.append(ref+': pad-set mismatch')
    gaps=[]
    for a,b in itertools.combinations(pads,2):
        # Conservative axis-aligned rectangular envelope, including the whole copper pad.
        ca,cb=a.GetPosition(),b.GetPosition()
        sa,sb=a.GetSize(),b.GetSize()
        dx=max(0,abs(p.ToMM(ca.x-cb.x))-(p.ToMM(sa.x)+p.ToMM(sb.x))/2)
        dy=max(0,abs(p.ToMM(ca.y-cb.y))-(p.ToMM(sa.y)+p.ToMM(sb.y))/2)
        gap=math.hypot(dx,dy)
        gaps.append(dict(pads=[a.GetNumber(),b.GetNumber()],lower_bound_mm=round(gap,6)))
        if gap < 0.1524-1e-6:
            issues.append(f'{ref}: copper-envelope gap {gap:.6f} below 6 mil')
    checked.append(dict(reference=ref,footprint=part['footprint'],
        footprint_sha256=hashlib.sha256((folder/(name+'.kicad_mod')).read_bytes()).hexdigest(),
        min_copper_envelope_gap_mm=min(x['lower_bound_mm'] for x in gaps),
        closest_pairs=sorted(gaps,key=lambda x:x['lower_bound_mm'])[:2]))
assert spec['parts']['J2']['pins']['6'] is None
assert all(net!='HOST_VIO' for part in spec['parts'].values() for net in part['pins'].values())
assert len(spec['socket_contract']['rows'])==8
assert spec['socket_contract']['rows'][0]['power_row']['physically_absent']
for i, signal in enumerate(['STEP','DIR','EN'],1):
    assert spec['parts'][f'R{i}']['pins']=={'1':signal,'2':signal+'_GATE'}
    assert spec['parts'][f'R{i+3}']['pins']=={'1':signal+'_GATE','2':'GND'}
    assert spec['parts'][f'Q{i}']['pins']['1']==signal+'_GATE'
    assert spec['parts'][f'Q{i}']['pins']['2']=='GND'
result=dict(status='PASS' if not issues else 'FAIL',
    scope='Native footprint load, exact pad sets, conservative pad-envelope gap, net-contract assertions; not ERC/PCB DRC',
    specification_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    manufacturing_ready=False,checked=checked,issues=issues)
(root/'logic-footprint-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(parts=len(checked),issues=issues,
    minimum_gap_mm=min(x['min_copper_envelope_gap_mm'] for x in checked))))
assert not issues
