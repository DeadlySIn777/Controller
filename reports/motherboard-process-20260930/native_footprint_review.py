"""Load exact fitted libraries in native pcbnew, independent of the generator."""
import hashlib,json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/motherboard_process'
d=json.loads((OUT/'design.json').read_text())
rows=[];errors=[]
for ref,p in d['components'].items():
 lib,name=p['footprint'].split(':')
 base=OUT/(lib+'.pretty') if lib=='CNC_MB_Process' else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')
 f=base/(name+'.kicad_mod');fp=pcbnew.FootprintLoad(str(base),name)
 if not fp:errors.append(ref+' native footprint missing');continue
 nums={x.GetNumber() for x in fp.Pads() if x.GetNumber()}
 if nums!=set(p['pins']):errors.append(ref+' pad set differs '+str(nums))
 geometry=[{'number':x.GetNumber(),'x_mm':pcbnew.ToMM(x.GetPosition().x),'y_mm':pcbnew.ToMM(x.GetPosition().y),'sx_mm':pcbnew.ToMM(x.GetSize().x),'sy_mm':pcbnew.ToMM(x.GetSize().y)} for x in fp.Pads()]
 rows.append({'reference':ref,'mpn':p['mpn'],'footprint':p['footprint'],'file':str(f),'file_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'electrical_pad_count':len(nums),'all_pad_count':len(list(fp.Pads())),'geometry':geometry})
custom={p['mpn']:p for p in rows if p['footprint'].startswith('CNC_MB_Process:')}
def check(mpn,num,x,y,sx,sy):
 matches=[p for p in custom[mpn]['geometry'] if p['number']==num and all(abs(p[k]-v)<1e-6 for k,v in [('x_mm',x),('y_mm',y),('sx_mm',sx),('sy_mm',sy)])]
 if len(matches)!=1:errors.append(mpn+' primary pad geometry differs '+num)
check('PMV20XNEAR','1',-1,-.95,.7,.6)
check('PMV20XNEAR','2',-1,.95,.7,.6)
check('PMV20XNEAR','3',1,0,.7,.6)
check('TPS1H000AQDGNRQ1','1',-2.2,-.975,1.4,.45)
check('TPS1H000AQDGNRQ1','8',2.2,-.975,1.4,.45)
check('TPS1H000AQDGNRQ1','9',0,0,1.57,1.89)
r={'ok':not errors,'errors':errors,'native_footprints_loaded':len(rows),'unique_electrical_pads':sum(x['electrical_pad_count'] for x in rows),'all_pad_shapes':sum(x['all_pad_count'] for x in rows),'primary_geometry_assertions':6,'geometry':rows}
(Path(__file__).resolve().parent/'native-footprints.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='geometry'}));raise SystemExit(not r['ok'])
