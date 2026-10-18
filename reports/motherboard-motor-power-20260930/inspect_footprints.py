"""Native footprint loading and independent primary-source copper inspection."""
from pathlib import Path
import hashlib
import json
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'hardware/motherboard_motor_power'
model=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
lib=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
records={};errors=[]
for ref,c in model['components'].items():
    if not c['physical']:continue
    name=c['footprint']
    if name in records:continue
    folder,fp=name.split(':',1)
    directory=OUT/'CNC_MotorPower.pretty' if folder=='CNC_MotorPower' else lib/(folder+'.pretty')
    native=pcbnew.FootprintLoad(str(directory),fp)
    if native is None:errors.append('Native footprint missing '+name);continue
    pads={p.GetNumber():{'at_mm':[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],'size_mm':[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)],'type':int(p.GetAttribute())} for p in native.Pads()}
    if set(pads)!=set(c['pins']):errors.append('Native pad numbering differs '+name)
    records[name]={'file':str(directory/(fp+'.kicad_mod')),'sha256':hashlib.sha256((directory/(fp+'.kicad_mod')).read_bytes()).hexdigest(),'pads':pads}
iso=records['CNC_MotorPower:ISO7720_DW16_TI_HV']['pads']
for n in range(1,17):
    p=iso[str(n)];expected=[-4.875,round(-4.445+(n-1)*1.27,4)] if n<=8 else [4.875,round(4.445-(n-9)*1.27,4)]
    if p['at_mm']!=expected or p['size_mm']!=[1.65,.6] or p['type']!=int(pcbnew.PAD_ATTRIB_SMD):errors.append('TI HV reference land '+str(n))
ltc=records['CNC_MotorPower:LTC2962_UD16']['pads']
if ltc['17']['type']!=int(pcbnew.PAD_ATTRIB_SMD) or ltc['17']['at_mm']!=[0,0] or ltc['17']['size_mm']!=[1.45,1.45]:errors.append('LTC thermal pad source differs')
result={'passed':not errors,'errors':errors,'distinct_footprints':len(records),'physical_parts':63,'records':records,'scope':'Native pad existence/numbering; TI HV lands and retained LTC thermal copper inspected. No stencil/assembly/isolation qualification.','manufacturing_ready':False}
(HERE/'native-footprint-inspection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':not errors,'errors':errors,'distinct_footprints':len(records)}));raise SystemExit(bool(errors))
