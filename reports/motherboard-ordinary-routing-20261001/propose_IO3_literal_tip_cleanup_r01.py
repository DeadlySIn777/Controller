"""Literal In2 pour-only DFM cleanup trial, separately reviewed from routing."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent)]
import pcbnew
import check_io3_backbone_preservation_r07 as power
from hardware_route_logic_return import xy,mm
p=Path(__file__).parent;src=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb');out=p/'IO3-literal-unused-tip-cleanup-r01';out.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(src));bounds=(91.05,211.075,91.225,211.325);cut=power.box(*bounds);affected=[]
for z in b.Zones():
 if z.IsOnLayer(pcbnew.In2_Cu)and not z.GetIsRuleArea():
  hit=power.intersection(z.GetFilledPolysList(pcbnew.In2_Cu),cut)
  if hit.OutlineCount():affected.append(dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),exact_intersected_filled_polygon=hit.Format(False)))
assert affected and all(row['net']=='/IO_3V3'for row in affected)
near=[]
for pad in b.GetPads():
 if pad.GetNetname()=='/IO_3V3':
  x,y=mm(pad.GetPosition())
  if bounds[0]-1<=x<=bounds[2]+1 and bounds[1]-1<=y<=bounds[3]+1:near.append(pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber())
assert not near
z=pcbnew.ZONE(b);z.SetLayer(pcbnew.In2_Cu);z.SetIsRuleArea(True);z.SetZoneName('IO3 literal unused inter-antipad tip cleanup 91.05 211.075');z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);z.Outline().Append(cut);b.Add(z)
dest=out/'motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in src.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
(out/'proposal.json').write_text(json.dumps(dict(input_board_sha256=power.sha(src),zone_uuid=z.m_Uuid.AsString(),exact_bounds_mm=bounds,only_actual_filled_net_intersected=affected,IO3_pads_within_1mm=[],no_copper_or_pad_moved=True,native_DRC_topology_receiving_power_and_reference_proof_required=True,adopted=False,manufacturing_ready=False),indent=2))
with(out/'native-command.txt').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(out/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(command_exit=r.returncode,board_sha256=power.sha(dest),adopted=False)))
