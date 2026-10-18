"""Read native footprints without inventing missing package geometry."""
from pathlib import Path
import json,hashlib,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
d=json.loads((ROOT/'hardware/motherboard_motors/design.json').read_text())
lib=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
records={};errors=[]
for ref,c in d['components'].items():
 if not c['physical']:continue
 fp=c['footprint']
 if fp in records:continue
 folder,name=fp.split(':',1)
 directory=ROOT/'hardware/motherboard_motors/CNC_Motors.pretty' if folder=='CNC_Motors' else lib/(folder+'.pretty')
 path=directory/(name+'.kicad_mod')
 f=pcbnew.FootprintLoad(str(directory),name)
 if not f:errors.append(fp+' native load failed');continue
 pads={p.GetNumber():{'position_mm':[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],'size_mm':[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)]} for p in f.Pads()}
 expected=set(c['pins'])
 if set(pads)!=expected:errors.append(fp+f' pads {set(pads)} != source {expected}')
 records[fp]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_file':str(path),'pads':pads,'native_pad_number_set_matches':set(pads)==expected,'manufacturer_land_pattern_complete_verification':folder=='CNC_Motors' and ('3640' in name or '4176' in name or name=='ISO1212_DBQ16_TI')}
for fp in ['CNC_Motors:TLP3640A_SO4_11-3C1','CNC_Motors:TLP4176A_2.54SOP4_11-5H1S']:
 p=records[fp]['pads']
 if not (p['1']['position_mm'][0]<0 and p['1']['position_mm'][1]<0 and p['2']['position_mm'][0]<0 and p['2']['position_mm'][1]>0 and p['3']['position_mm'][0]>0 and p['3']['position_mm'][1]>0 and p['4']['position_mm'][0]>0 and p['4']['position_mm'][1]<0):errors.append(fp+' top-view pin orientation differs')
iso=records['CNC_Motors:ISO1212_DBQ16_TI']['pads']
for n in range(1,17):
 q=iso[str(n)];x=-2.7 if n<=8 else 2.7;y=(n-1-3.5)*.635 if n<=8 else (16-n-3.5)*.635
 if any(abs(a-b)>1e-6 for a,b in zip(q['position_mm'],[x,y])) or q['size_mm']!=[1.6,.41]:errors.append(f'ISO1212 TI land{n} geometry mismatch')
result={'scope':'native footprint existence/numbering plus reviewed Toshiba relay top view; not every manufacturer stencil/land qualification','errors':errors,'passed':not errors,'records':records,'manufacturing_ready':False}
(HERE/'native-footprint-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'errors':errors,'distinct_footprints':len(records),'passed':not errors}))
raise SystemExit(0 if not errors else 1)
