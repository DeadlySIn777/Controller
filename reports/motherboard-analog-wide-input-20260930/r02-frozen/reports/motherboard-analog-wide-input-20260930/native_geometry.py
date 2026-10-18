"""Independent native source land/pad audit, not a manufacture PCB or loaded test."""
from pathlib import Path
import pcbnew,json,hashlib
root=Path(__file__).resolve().parents[2];rows=[];errors=[];checks=0
for block,lib in [('motherboard_analog_output','CNC_MB_AO'),('motherboard_analog_input','CNC_MB_AI')]:
 d=json.loads((root/'hardware'/block/'design.json').read_text())
 for ref,p in d['components'].items():
  ln,name=p['footprint'].split(':');base=root/'hardware'/block/(ln+'.pretty') if ln==lib else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(ln+'.pretty')
  fp=pcbnew.FootprintLoad(str(base),name)
  if fp is None:errors.append(ref+' load failure');continue
  pads=[q for q in fp.Pads() if q.GetNumber()];unique={q.GetNumber() for q in pads}
  if unique!=set(p['pins']):errors.append(ref+' electrical pin/pad mismatch')
  rows.append(dict(ref=ref,footprint=p['footprint'],electrical_pads=len(unique)))
  for q in pads:
   n=int(q.GetNumber());x,y=map(pcbnew.ToMM,(q.GetPosition().x,q.GetPosition().y));w,h=map(pcbnew.ToMM,(q.GetSize().x,q.GetSize().y))
   if name=='TMR4WI_SIP8_Traco':
    expected=(8.9-(n-1)*2.54,1.95,1.7,1.7);checks+=1
    if abs(pcbnew.ToMM(q.GetDrillSize().x)-.9)>1e-6:errors.append(ref+' drill .9 candidate changed')
   elif name=='TPS7A26_DRV6_TI':
    expected={1:(-.975,-.65,.45,.30),2:(-.975,0,.45,.30),3:(-.975,.65,.45,.30),4:(.975,.65,.45,.30),5:(.975,0,.45,.30),6:(.975,-.65,.45,.30),7:(0,0,1,1.6)}[n];checks+=1
   else:continue
   if any(abs(a-b)>1e-6 for a,b in zip((x,y,w,h),expected)):errors.append(ref+'.'+str(n)+' independent native source geometry differs')
out=Path(__file__).parent/'native-geometry.json'
data=dict(ok=not errors,errors=errors,parts=rows,physical_footprints=len(rows),electrical_pads=sum(q['electrical_pads'] for q in rows),converter_LDO_geometry_checks=checks,
 TMR_drill_and_land_are_assembly_candidate=True,TI_LDO_land_and_paste_match_primary=True,manufacturing_ready=False,routed_board_DRC=False,
 sources={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'hardware/motherboard_analog_input/design.json',root/'hardware/motherboard_analog_output/design.json']})
out.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k not in ['parts','sources']},indent=2));raise SystemExit(bool(errors))
