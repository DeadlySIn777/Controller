"""Native stock-footprint numbering, orientation and package geometry check."""
import hashlib,json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
model=json.loads((ROOT/'hardware/motherboard_io_control/design.json').read_text())
stock=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints');rows=[];errors=[];pads=0
for ref,p in model['components'].items():
 lib,name=p['footprint'].split(':');directory=stock/(lib+'.pretty');src=directory/(name+'.kicad_mod');fp=pcbnew.FootprintLoad(str(directory),name)
 if fp is None:errors.append(ref+' couldnot load');continue
 numbers=[pad.GetNumber() for pad in fp.Pads()];positions={pad.GetNumber():[pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)] for pad in fp.Pads()}
 if set(numbers)!=set(p['pins']) or len(numbers)!=len(set(numbers)):errors.append(ref+' actualpadnumber mismatch')
 if p['kind'] in ['G031C','G031K']:
  # ST LQFP top view: pin1 upper left, count down left, then bottom/right/top.
  n=12 if p['kind']=='G031C' else 8;pitch=.5 if n==12 else .8
  if not positions['1'][0]<0 or not positions['1'][1]<0:errors.append(ref+' pin1 orientation')
  if abs(positions['2'][1]-positions['1'][1]-pitch)>1e-6:errors.append(ref+' pinpitch mismatch')
  if not positions[str(n+1)][0]<0 or not positions[str(n+1)][1]>0:errors.append(ref+' bottomedge numbering')
 if p['kind']=='TP' and any(pad.IsOnLayer(pcbnew.F_Paste) for pad in fp.Pads()):errors.append(ref+' coppertestpadmustnot cause SMTassembly')
 pads+=len(numbers);rows.append({'reference':ref,'MPN':p['mpn'],'footprint':p['footprint'],'pads':len(numbers),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'positions_mm':positions,'assembly_part':p['kind']!='TP'})
report={'ok':not errors,'errors':errors,'native_pcbnew_version':pcbnew.Version(),'physical_footprints':len(rows),'numbered_electrical_pads':pads,'purchased_fitted_parts':sum(r['assembly_part'] for r in rows),'copper_testpads':sum(not r['assembly_part'] for r in rows),'manufacturing_ready':False,'scope':'Native stock-footprint numbering/orientation; prototype land/stencil and mechanical acceptance remain finalPCBwork','rows':rows}
(OUT/'native-footprint-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}));raise SystemExit(bool(errors))
