"""Run with KiCad's Python; source footprint checks, never a manufacturing board."""
import pcbnew,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];d=json.loads((root/'hardware/motherboard_identity_io/design.json').read_text());errors=[];rows=[];geom=0
for ref,p in d['components'].items():
 lib,name=p['footprint'].split(':');base=root/'hardware/motherboard_identity_io/CNC_MB_Identity.pretty' if lib=='CNC_MB_Identity' else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty');fp=pcbnew.FootprintLoad(str(base),name)
 if fp is None:errors.append(ref+' native load failure');continue
 pads=list(fp.Pads());pins={p.GetNumber() for p in pads if p.GetNumber()}
 if pins!=set(p['pins']):errors.append(ref+' padmap differs')
 rows.append({'ref':ref,'footprint':p['footprint'],'unique_pads':len(pins),'native_pad_shapes':len(pads)})
 for pad in pads:
  n=pad.GetNumber()
  if not n:continue
  xy=pad.GetPosition();sz=pad.GetSize();x,y=pcbnew.ToMM(xy.x),pcbnew.ToMM(xy.y);w,h=pcbnew.ToMM(sz.x),pcbnew.ToMM(sz.y)
  if name=='TCA9517A_DGK8_TI':
   q=int(n);ex=-2.2 if q<=4 else 2.2;ey=(q-1)*.65-.975 if q<=4 else (8-q)*.65-.975;ew,eh=1.4,.45
   if abs(pad.GetRoundRectCornerRadius()/1e6-.05)>2e-6:errors.append(ref+'/'+n+' exact rounded copper radius mismatch')
  elif name=='TPD1E10B06_DPY2_TI':ex,ey=(-.35,0) if n=='1' else (.35,0);ew,eh=.3,.5
  else:continue
  geom+=1
  if any(abs(a-b)>2e-6 for a,b in zip((x,y,w,h),(ex,ey,ew,eh))):errors.append(ref+'/'+n+' exact vendor land mismatch')
r={'ok':not errors,'errors':errors,'physical_footprints':len(rows),'electrical_pads':sum(q['unique_pads'] for q in rows),'native_pad_shapes':sum(q['native_pad_shapes'] for q in rows),'exact_vendor_geometry_checks':geom,'parts':rows,'manufacturing_ready':False,'scope':'native footprint pad coverage and reviewed vendor copper dimensions, not routed PCB/thermal/stencil proof'}
out=Path(__file__).parent;(out/'native-footprints.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='parts'},indent=2));raise SystemExit(bool(errors))
