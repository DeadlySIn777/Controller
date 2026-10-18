"""Native exact ACC2 package validation; initial48 report remains historical."""
import hashlib,json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hardware/motherboard_acc_control';REPORT=Path(__file__).resolve().parent/'r02-ao-spi-correction'
d=json.loads((OUT/'design.json').read_text());rows=[];errors=[]
for ref,p in d['components'].items():
 lib,name=p['footprint'].split(':');base=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty');f=base/(name+'.kicad_mod');fp=pcbnew.FootprintLoad(str(base),name)
 if not fp:errors.append(ref+' missing native footprint');continue
 nums={x.GetNumber() for x in fp.Pads() if x.GetNumber()}
 if nums!=set(p['pins']):errors.append(ref+' actual native pad set differs')
 rows.append({'reference':ref,'mpn':p['mpn'],'footprint':p['footprint'],'file_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'electrical_pad_count':len(nums),'all_pad_count':len(list(fp.Pads()))})
r={'ok':not errors,'errors':errors,'native_footprints_loaded':len(rows),'unique_electrical_pads':sum(q['electrical_pad_count'] for q in rows),'all_pad_shapes':sum(q['all_pad_count'] for q in rows),'geometry':rows}
(REPORT/'native-footprints.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='geometry'}));raise SystemExit(not r['ok'])
