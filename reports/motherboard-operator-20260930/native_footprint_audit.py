import json,hashlib
from pathlib import Path
import pcbnew
root=Path(r'C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller');out=root/'hardware/motherboard_operator';p=json.loads((out/'design.json').read_text());rows=[];errors=[]
for ref,x in p['components'].items():
 lib,name=x['footprint'].split(':',1);folder=out/(lib+'.pretty') if lib=='CNC_MB_Operator' else Path(r'C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')
 f=folder/(name+'.kicad_mod');fp=pcbnew.FootprintLoad(str(folder),name)
 if not fp:errors.append(ref+' missing footprint');continue
 pads={pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()};expected=set(x['pins'])
 if pads!=expected:errors.append(ref+' pad set mismatch '+str(pads.symmetric_difference(expected)))
 geometry=[{'number':q.GetNumber(),'x_mm':pcbnew.ToMM(q.GetPosition().x),'y_mm':pcbnew.ToMM(q.GetPosition().y),'sx_mm':pcbnew.ToMM(q.GetSize().x),'sy_mm':pcbnew.ToMM(q.GetSize().y)} for q in fp.Pads()]
 rows.append({'reference':ref,'mpn':x['mpn'],'footprint':x['footprint'],'file':str(f),'file_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'electrical_pad_count':len(pads),'all_pad_count':len(list(fp.Pads())),'geometry':geometry})
r={'ok':not errors,'errors':errors,'native_footprints_loaded':len(rows),'unique_electrical_pads':sum(x['electrical_pad_count'] for x in rows),'all_physical_pads_including_EP_tabs_paste':sum(x['all_pad_count'] for x in rows),'geometry':rows,'manufacturing_ready':False,'qualification':'Native loading/pad-number/shape inventory, not routed DRC, clearance or stencil qualification'}
(root/'reports/motherboard-operator-20260930/native-footprints.json').write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items() if k!='geometry'})
