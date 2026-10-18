"""Three explicit In2 pour-only clearances, isolated from electrical routing."""
from pathlib import Path
import sys,json,shutil,subprocess,uuid,argparse
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-ordinary-routing-20261001')]
import pcbnew as p
import check_io3_backbone_preservation_r07 as g
from hardware_route_logic_return import identity,pad_identity
from hardware_map_motherboard_domains import sha,write
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=False);before=sha(a.board);b=p.LoadBoard(str(a.board))
regions=[('Unloaded CORE-health facing-cell In2 clearance',[343.15,176.10,343.90,176.80]),
         ('Unloaded RAW-array In2 cusp clearance',[323.10,173.98,323.38,174.24]),
         ('Unloaded CORE-health blue-LED In2 cusp clearance',[345.70,173.40,346.20,174.10])]
rows=[]
for index,(name,bounds)in enumerate(regions):
 cut=g.box(*bounds);hits=[];contacts=[]
 for z in b.Zones():
  if z.GetIsRuleArea()or not z.IsOnLayer(p.In2_Cu):continue
  hit=g.intersection(z.GetFilledPolysList(p.In2_Cu),cut)
  if hit.OutlineCount():hits.append(dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),exact_native_intersection=hit.Format(False),minimum_width_mm=p.ToMM(z.GetMinThickness())))
 assert hits and all(h['net']=='/IO_3V3'for h in hits),hits
 for pad in b.GetPads():
  if pad.GetNetname()=='/IO_3V3':
   for layer in(p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu):
    if pad.IsOnLayer(layer)and cut.Collide(pad.GetEffectiveShape(layer)):contacts.append(pad.m_Uuid.AsString())
 for t in b.GetTracks():
  if t.GetNetname()=='/IO_3V3'and t.IsOnLayer(p.In2_Cu)and cut.Collide(t.GetEffectiveShape(p.In2_Cu)):contacts.append(t.m_Uuid.AsString())
 assert not contacts,contacts
 z=p.ZONE(b);z.SetLayer(p.In2_Cu);z.SetIsRuleArea(True);z.SetZoneName(name)
 z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
 z.Outline().Append(cut);b.Add(z)
 rows.append(dict(name=name,bounds_mm=bounds,generated_UUID=z.m_Uuid.AsString(),UUID=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/health-In2-unused-pour/r01/'+str(index))),actual_filled_hits=hits,IO3_metal_contacts=[]))
dest=a.out/'motherboard-health-unused-IO3-candidate.kicad_pcb';p.SaveBoard(str(dest),b)
raw=dest.read_text()
for r in rows:assert raw.count(r['generated_UUID'])==1;raw=raw.replace(r['generated_UUID'],r['UUID'])
dest.write_text(raw,encoding='utf8',newline='\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
for f in a.board.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,a.out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,a.out/f.name)
write(a.out/'proposal.json',dict(input_board=str(a.board),input_board_sha256=before,source_design_sha256=sha(Path('hardware/motherboard/design.json')),
    input_script_sha256=sha(Path(__file__)),regions=rows,other_copper_source_pads_or_zones_changed=False,adopted=False,manufacturing_ready=False))
with(a.out/'native-command.txt').open('w')as log:
 r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(a.out/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert sha(a.board)==before
v=json.loads((a.out/'native.json').read_text())
print(json.dumps(dict(exit=r.returncode,board_sha256=sha(dest),regular_violations=len(v['violations']),ignored=v['ignored_checks'],candidate=str(dest))))
