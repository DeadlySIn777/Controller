"""Run with KiCad's Python; source footprint checks, never a manufacturing board."""
import pcbnew,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];d=json.loads((root/'hardware/motherboard_analog_input/design.json').read_text());errors=[];rows=[];geom=0
for ref,p in d['components'].items():
 lib,name=p['footprint'].split(':');base=root/'hardware/motherboard_analog_input/CNC_MB_AI.pretty' if lib=='CNC_MB_AI' else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty');fp=pcbnew.FootprintLoad(str(base),name)
 if fp is None:errors.append(ref+' native load failure');continue
 pads=list(fp.Pads());pins={p.GetNumber() for p in pads if p.GetNumber()}
 if pins!=set(p['pins']):errors.append(ref+' padmap differs')
 rows.append({'ref':ref,'footprint':p['footprint'],'unique_pads':len(pins),'native_pad_shapes':len(pads)})
 for pad in pads:
  n=pad.GetNumber()
  if not n:continue
  xy=pad.GetPosition();sz=pad.GetSize();x,y=pcbnew.ToMM(xy.x),pcbnew.ToMM(xy.y);w,h=pcbnew.ToMM(sz.x),pcbnew.ToMM(sz.y)
  if name=='ADS8684A_DBT38_TI':
   q=int(n);ex=-2.9 if q<=19 else 2.9;ey=(q-1)*.5-4.5 if q<=19 else (38-q)*.5-4.5;ew,eh=1.5,.3
  elif name=='MAX17612_T1033_ADI':
   q=int(n);ex=0 if q==11 else -1.475 if q<=5 else 1.475;ey=0 if q==11 else (q-1)*.5-1 if q<=5 else (10-q)*.5-1;ew,eh=(1.58,2.35) if q==11 else (.7,.3)
  elif name=='PHP1206_Vishay':ex=-1.23825 if n=='1' else 1.23825;ey=0;ew,eh=1.9177,1.8034
  elif name=='PHP2512_Vishay':ex=-2.54 if n=='1' else 2.54;ey=0;ew,eh=2.3114,3.2004
  elif name=='TBU_CA_6.5x4_Bourns':ex={'1':-2.025,'2':0,'3':2.025}[n];ey=0;ew,eh=(.8,3.4) if n=='2' else (1.85,3.4)
  elif name=='REC3.5_R8_A_Single':ex,ey={'2':(11.43,-7.62),'11':(-11.43,-7.62),'14':(-11.43,7.62),'16':(-6.35,7.62),'22':(8.89,7.62),'23':(11.43,7.62)}[n];ew,eh=1.8,1.8
  else:continue
  geom+=1
  if any(abs(a-b)>2e-6 for a,b in zip((x,y,w,h),(ex,ey,ew,eh))):errors.append(ref+'/'+n+' exact vendor land mismatch')
r={'ok':not errors,'errors':errors,'physical_footprints':len(rows),'electrical_pads':sum(q['unique_pads'] for q in rows),'native_pad_shapes':sum(q['native_pad_shapes'] for q in rows),'exact_vendor_geometry_checks':geom,'parts':rows,'manufacturing_ready':False,'scope':'native footprint pad coverage and reviewed vendor copper dimensions, not routed PCB/thermal/stencil proof'}
out=Path(__file__).parent;(out/'native-footprints.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='parts'},indent=2));raise SystemExit(bool(errors))
