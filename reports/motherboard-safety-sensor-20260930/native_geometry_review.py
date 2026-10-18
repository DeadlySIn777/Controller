"""Native all-footprint/unsuppressed geometry fixture; not a production PCB."""
import json,hashlib,subprocess
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'hardware/motherboard_safety_sensor';OUT=Path(__file__).resolve().parent/'native-geometry';OUT.mkdir(exist_ok=True)
STOCK=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints');d=json.loads((SRC/'design.json').read_text());b=pcbnew.BOARD();b.SetCopperLayerCount(6);nets={};records={};numbered=0
for i,(r,c) in enumerate(d['components'].items()):
 lib,name=c['footprint'].split(':');folder=SRC/(lib+'.pretty') if lib=='CNC_MB_Safety' else STOCK/(lib+'.pretty');fp=pcbnew.FootprintLoad(str(folder),name)
 if fp is None:raise ValueError('Cannot load '+r)
 fp.SetReference(r);fp.SetValue(c['mpn']);b.Add(fp);fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10+20*(i%15)),pcbnew.FromMM(10+18*(i//15))))
 fp.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10+20*(i%15)),pcbnew.FromMM(3+18*(i//15))));fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(.8),pcbnew.FromMM(.8)));fp.Reference().SetTextThickness(pcbnew.FromMM(.1))
 geom={}
 for pad in fp.Pads():
  n=pad.GetNumber()
  if not n:continue
  if n not in c['pins']:raise ValueError('Unexpected native pad '+r+'.'+n)
  net=c['pins'][n] or 'NC_'+r+'_'+n
  if net not in nets:z=pcbnew.NETINFO_ITEM(b,net,len(nets)+1);b.Add(z);nets[net]=z
  pad.SetNet(nets[net]);geom[n]={'size_mm':[pcbnew.ToMM(pad.GetSize().x),pcbnew.ToMM(pad.GetSize().y)],'shape':int(pad.GetShape())};numbered+=1
 if set(geom)!=set(c['pins']):raise ValueError('Missing native pads '+r)
 records[r]={'footprint':c['footprint'],'hash':hashlib.sha256((folder/(name+'.kicad_mod')).read_bytes()).hexdigest(),'pads':geom}
for a,z in [((0,0),(305,0)),((305,0),(305,230)),((305,230),(0,230)),((0,230),(0,0))]:
 l=pcbnew.PCB_SHAPE(b);l.SetShape(pcbnew.SHAPE_T_SEGMENT);l.SetLayer(pcbnew.Edge_Cuts);l.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in a)));l.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in z)));l.SetWidth(pcbnew.FromMM(.05));b.Add(l)
path=OUT/'geometry.kicad_pcb';pcbnew.SaveBoard(str(path),b)
pro=json.loads((ROOT/'reports/motherboard-pcb-integration-20260930/populated-r07-1585/motherboard-populated-candidate.kicad_pro').read_text());pro['meta']['filename']='geometry.kicad_pro';pro['board']['design_settings']['rules']['min_clearance']=.15
for c in pro['net_settings']['classes']:c['clearance']=.15
path.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n');path.with_suffix('.kicad_dru').write_text('(version 1)\n# No footprint exceptions/suppression. Unrouted fixture only.\n')
cmd=['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--output',str(OUT/'drc.json'),str(path)];run=subprocess.run(cmd,text=True,capture_output=True);(OUT/'native-command.txt').write_text(' '.join(cmd)+'\n'+run.stdout+run.stderr)
e=json.loads((OUT/'drc.json').read_text());r={'native_load_parts':len(records),'native_numbered_pads':numbered,'records':records,'regular_violations':e['violations'],'geometry_pass':not e['violations'] and not e['ignored_checks'],'ignored_checks':e['ignored_checks'],'unconnected_display_items':len(e['unconnected_items']),'unrouted_geometry_fixture':True,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['records','regular_violations']}));raise SystemExit(not r['geometry_pass'])
