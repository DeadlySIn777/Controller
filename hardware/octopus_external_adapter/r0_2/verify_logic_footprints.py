"""Load every declared footprint and compare physical pad sets to logic spec."""
from pathlib import Path
import json
import pcbnew

root=Path(__file__).resolve().parent
base=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
spec=json.loads((root/'logic_spec.json').read_text())
issues=[]
checked=[]
for ref,s in spec['parts'].items():
    lib,name=s['footprint'].split(':')
    folder=root/(lib+'.pretty') if (root/(lib+'.pretty')).exists() else base/(lib+'.pretty')
    fp=pcbnew.FootprintLoad(str(folder),name)
    if fp is None:
        issues.append(ref+': missing footprint')
        continue
    pads={p.GetNumber() for p in fp.Pads() if p.GetNumber()}
    if pads!=set(s['pins']):
        issues.append(ref+': pad-set mismatch '+str(sorted(pads)))
    checked.append({'reference':ref,'footprint':s['footprint'],'pads':sorted(pads)})
    if ref=='SW1':
        expected={'1':(-2.5,0.0),'2':(0.0,0.0),'3':(2.5,0.0)}
        for pad in fp.Pads():
            xy=(round(pcbnew.ToMM(pad.GetPosition().x),5),round(pcbnew.ToMM(pad.GetPosition().y),5))
            drill=round(pcbnew.ToMM(pad.GetDrillSize().x),5)
            if xy!=expected[pad.GetNumber()] or drill!=0.9:
                issues.append('SW1: manufacturer drill-pattern mismatch')
result={'verification':'native footprint load and exact physical pad-set check',
        'manufacturing_ready':False,'parts':len(checked),'issues':issues,'checked':checked}
(root/'logic-footprint-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'parts':len(checked),'issues':issues}))
assert not issues
