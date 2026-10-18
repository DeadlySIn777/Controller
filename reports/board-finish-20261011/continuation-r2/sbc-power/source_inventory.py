import sys,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
POWER=HERE.parents[1]/'power-audit'
sys.path.insert(0,str(POWER))
import prepare_sbc_198b_five_part as A
import sbc_198b_overlay as live
p=A.p
g,scope=live.overlay()
native=p.base.inventory(p.read(live.COMBINED))[3]
refs={'U11012','C11061','C11062','C11063','C15001','J15001','R11022','U11007','L11001','C11088'}
out={'source':live.SHA,'scope':scope,'footprints':{},'pads':[],'near_vias':[]}
for uid,ch in native.items():
    if p.base.pcbtext.chunk_kind(ch)=='footprint' and p.base.ref_of(ch) in refs:
        ref=p.base.ref_of(ch);out['footprints'][ref]={'uuid':uid,'pose':p.pose(p.base.children(ch)[1]),'sha':hashlib.sha256(ch).hexdigest()}
for r in g['pads']:
    if r['ref'] in refs:out['pads'].append({k:r[k] for k in ('ref','num','uuid','net','x','y','smd','layers','hole')})
for r in g['vias']:
    if (109<r['x']<126 and 156<r['y']<173) or (235<r['x']<250 and 109<r['y']<124):out['near_vias'].append(r)
(HERE/'source-inventory.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('footprints',out['footprints'])
print('pads',[(r['ref'],r['num'],r['net'],r['x'],r['y']) for r in out['pads'] if r['ref']!='J15001'])
print('Jpower',[(r['num'],r['net'],r['x'],r['y']) for r in out['pads'] if r['ref']=='J15001' and ('5V' in r['net'] or 'GND' in r['net'])])
print('near_vias',[(r['uuid'],r['net'],r['x'],r['y'],r['flashed']) for r in out['near_vias']])
