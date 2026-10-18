"""Independent pcbnew exact package/pad loading and vendor geometry."""
import hashlib,json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hardware/motherboard_analog_output'
d=json.loads((OUT/'design.json').read_text());rows=[];errors=[]
for ref,p in d['components'].items():
 lib,name=p['footprint'].split(':');base=OUT/(lib+'.pretty') if lib=='CNC_MB_AO' else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty');f=base/(name+'.kicad_mod');fp=pcbnew.FootprintLoad(str(base),name)
 if not fp:errors.append(ref+' missing native footprint');continue
 nums={x.GetNumber() for x in fp.Pads() if x.GetNumber()}
 if nums!=set(p['pins']):errors.append(ref+' exact native pad set differs')
 geo=[{'number':x.GetNumber(),'x_mm':pcbnew.ToMM(x.GetPosition().x),'y_mm':pcbnew.ToMM(x.GetPosition().y),'sx_mm':pcbnew.ToMM(x.GetSize().x),'sy_mm':pcbnew.ToMM(x.GetSize().y)} for x in fp.Pads()]
 rows.append({'reference':ref,'mpn':p['mpn'],'footprint':p['footprint'],'file':str(f),'file_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'electrical_pad_count':len(nums),'all_pad_count':len(list(fp.Pads())),'geometry':geo})
by={q['mpn']:q for q in rows}
def check(mpn,num,x,y,sx,sy):
 m=[p for p in by[mpn]['geometry'] if p['number']==num and all(abs(p[k]-v)<1e-6 for k,v in [('x_mm',x),('y_mm',y),('sx_mm',sx),('sy_mm',sy)])]
 if len(m)!=1:errors.append(mpn+' primary geometry differs '+num)
for n in range(1,9):check('TPS7A1650DGNR',str(n),-2.2 if n<=4 else 2.2,(n-1)*.65-.975 if n<=4 else (8-n)*.65-.975,1.4,.45)
check('TPS7A1650DGNR','9',0,0,1.6,1.92)
for n in range(1,11):check('ADS1115IDGSR',str(n),-2.2 if n<=5 else 2.2,(n-1)*.5-1 if n<=5 else (10-n)*.5-1,1.45,.3)
for n in range(1,17):check('ISO7761FDWR',str(n),-4.875 if n<=8 else 4.875,(n-1)*1.27-4.445 if n<=8 else (16-n)*1.27-4.445,1.65,.6)
dc=by['TMR 1-2412']['geometry'];c={p['number']:[p['x_mm'],p['y_mm']] for p in dc}
if c!={'1':[0.0,0.0],'2':[2.54,0.0],'4':[7.62,0.0],'6':[12.7,0.0]}:errors.append('TMR1 single-output exact physical pin spacing differs')
r={'ok':not errors,'errors':errors,'native_footprints_loaded':len(rows),'unique_electrical_pads':sum(q['electrical_pad_count'] for q in rows),'all_pad_shapes':sum(q['all_pad_count'] for q in rows),'primary_geometry_assertions':36,'package_reviews':{'AD5683RBRMZ-3':'RM10 MSOP3x3mm/0.5mm, manufacturerSDO optionfullpinmap; stock IPC land compatible with primary lead span4.65–5.15mm. Native physical pad numbers10.','ADS1115IDGSR':'Exact TI DGS0010A4221984/A05/2015 recommendedland1.45x.3 centres+-2.2.','TPS7A1650DGNR':'Exact DGN0008C4218838/A11/2017 EP1.6x1.92, no electricalDNC2;125umstencil100%coverage.','ISO7761FDWR':'Exact common DW0016B4221009/B07/2016 HV/isolationland copied without copper change from reviewed ISO7720 footprint, but actual5forward1return pins differ.','TMR 1-2412':'Primary4pin1,2,4,6 single-output SIP6; no5. Manufacturerbottomview reflected to native top body/courtyard; height11mm needs parentclearance.'},'geometry':rows,'physical_or_assembly_qualification':False}
(Path(__file__).resolve().parent/'native-footprints.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='geometry'}));raise SystemExit(not r['ok'])
