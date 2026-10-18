"""Native all-part land/pin inventory plus unsuppressed geometry-only DRC.

This unrouteable review fixture is not a production board or placement result.
"""
from pathlib import Path
import hashlib,json,subprocess
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
SRC=ROOT/'hardware/motherboard_power_entry'
STOCK=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=HERE/'native-geometry-r02';out.mkdir(exist_ok=True)
 model=json.loads((SRC/'design.json').read_text());board=pcbnew.BOARD();board.SetCopperLayerCount(6);nets={};rows=[]
 for i,(ref,c) in enumerate((r,c) for r,c in model['components'].items() if c['physical']):
  lib,name=c['footprint'].split(':');folder=SRC/(lib+'.pretty') if lib=='CNC_MB_Entry' else STOCK/(lib+'.pretty')
  fp=pcbnew.FootprintLoad(str(folder),name)
  if fp is None:raise ValueError('Native load failed '+ref)
  fp.SetReference(ref);fp.SetValue(c['mpn']);board.Add(fp);fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(15+23*(i%15)),pcbnew.FromMM(15+23*(i//15))))
  # Stock default reference fields can overlap their own package silk. Put
  # fixture references in the empty grid margin, instead of suppressing DRC.
  pos=fp.GetPosition();fp.Reference().SetPosition(pcbnew.VECTOR2I(pos.x,pos.y-pcbnew.FromMM(9)))
  seen={};pads=[]
  for pad in fp.Pads():
   num=pad.GetNumber()
   if not num:continue
   if num not in c['pins']:raise ValueError('Unassigned physical pad '+ref+'.'+num)
   net=c['pins'][num] or 'NC_'+ref+'_'+num
   if net not in nets:
    ni=pcbnew.NETINFO_ITEM(board,net,len(nets)+1);board.Add(ni);nets[net]=ni
   pad.SetNet(nets[net]);seen[num]=net
   local=pad.GetPosition()-fp.GetPosition();size=pad.GetSize()
   pads.append({'number':num,'net':net,'x_mm':pcbnew.ToMM(local.x),'y_mm':pcbnew.ToMM(local.y),'width_mm':pcbnew.ToMM(size.x),'height_mm':pcbnew.ToMM(size.y)})
  if set(seen)!=set(c['pins']):raise ValueError('Native pin-number set mismatch '+ref)
  rows.append({'ref':ref,'mpn':c['mpn'],'footprint':c['footprint'],'footprint_sha256':sha(folder/(name+'.kicad_mod')),'numbered_pads':pads})
 for a,b in [((0,0),(350,0)),((350,0),(350,350)),((350,350),(0,350)),((0,350),(0,0))]:
  line=pcbnew.PCB_SHAPE(board);line.SetShape(pcbnew.SHAPE_T_SEGMENT);line.SetLayer(pcbnew.Edge_Cuts)
  line.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in a)));line.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in b)));line.SetWidth(pcbnew.FromMM(.05));board.Add(line)
 path=out/'geometry.kicad_pcb';pcbnew.SaveBoard(str(path),board)
 pro=json.loads((ROOT/'reports/motherboard-pcb-integration-20260930/populated-r07-1585/motherboard-populated-candidate.kicad_pro').read_text());pro['meta']['filename']='geometry.kicad_pro'
 pro['board']['design_settings']['rules']['min_clearance']=.15
 for row in pro['net_settings']['classes']:row['clearance']=.15
 path.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n');path.with_suffix('.kicad_dru').write_text('(version 1)\n# No manufacturer exceptions, clearance reductions or suppressed checks.\n')
 cmd=['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--output',str(out/'drc.json'),str(path)]
 r=subprocess.run(cmd,capture_output=True,text=True);(out/'drc-command.txt').write_text(json.dumps(cmd)+'\n'+r.stdout+'\n'+r.stderr)
 d=json.loads((out/'drc.json').read_text());passed=not d['violations'] and not d['ignored_checks']
 coil=next(x for x in rows if x['ref']=='L11001');actual={p['number']:p for p in coil['numbered_pads']}
 for number,x in [('1',3.325),('2',-3.325)]:
  a=actual[number]
  assert abs(a['x_mm']-x)<1e-6 and a['y_mm']==0 and a['width_mm']==2.38 and a['height_mm']==9
 receipt={'passed':passed,'parts_loaded':len(rows),'numbered_pads':sum(len(x['numbered_pads']) for x in rows),'geometry_violations':d['violations'],'ignored_checks':d['ignored_checks'],
  'unconnected_items_count':len(d['unconnected_items']),'every_native_pin_number_and_net_matches':True,'new_coil_exact_manufacturer_lands_verified':True,
  'source_sha256':sha(SRC/'design.json'),'parts':rows,'fixture_contains_no_tracks_or_planes':True,'reference_fields_relocated_to_empty_fixture_margin':True,'whole_motherboard_DRC':False,'manufacturing_ready':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['passed','parts_loaded','numbered_pads','unconnected_items_count','new_coil_exact_manufacturer_lands_verified']}))
 return not passed
if __name__=='__main__':raise SystemExit(main())
