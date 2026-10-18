"""Report-only, literal In3 pour DFM cleanup; original narrow failure retained.

The unused re-entrant cusp is between two existing, unchanged LOGIC barrels.
This does not waive a tiny-area failure: it makes a real, bounded rule-area
change and requires separate native/source/capacity proof on both boards.
"""
from pathlib import Path
import sys,json,shutil,hashlib,importlib.util,math,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle
ROOT=Path(__file__).parent
POWER=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py')
spec=importlib.util.spec_from_file_location('frozen_power',POWER);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(POWER)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
CCK=ROOT/'actual-source26-root84-FPGA-CCK-C1022-F-In2-r06/motherboard-FPGA-flash-CCK-candidate.kicad_pcb'
CORE='/CORE_1V2';BOUNDS=(39.912499,48.775,41.175,50.6)
UID='c052f4ee-df74-43b5-9147-fb73d1f5a408'
VIA_IDS={'a79f6751-7b81-47e3-b7aa-38e6c523272a':((40.462499,49.325),.50,.20),'19e2030b-5063-4161-9c6b-6745ea84ca03':((40.575,50.),.60,.30)}

def make(kind):
 src=BASE if kind=='baseline'else CCK
 out=ROOT/('CORE-literal-antipad-join-'+kind+'-r03');out.mkdir(exist_ok=False)
 board=pcbnew.LoadBoard(str(src));board.BuildConnectivity();cut=p.box(*BOUNDS)
 oldtracks={t.m_Uuid.AsString():t for t in board.GetTracks()};via_rows=[]
 for uid,(pos,diam,drill)in VIA_IDS.items():
  via=oldtracks[uid];assert via.Type()==pcbnew.PCB_VIA_T and via.GetNetname()=='/LOGIC_GND'
  assert mm(via.GetPosition())==pos and pcbnew.ToMM(via.GetWidth(pcbnew.In3_Cu))==diam and pcbnew.ToMM(via.GetDrillValue())==drill
  via_rows.append(dict(uuid=uid,xy=pos,diameter_mm=diam,drill_mm=drill,identity=identity(via)))
 affected=[]
 for zone in board.Zones():
  if zone.IsOnLayer(pcbnew.In3_Cu)and not zone.GetIsRuleArea():
   hit=p.intersection(zone.GetFilledPolysList(pcbnew.In3_Cu),cut)
   if hit.OutlineCount():affected.append(dict(uuid=zone.m_Uuid.AsString(),net=zone.GetNetname(),actual_removed_scope_polygon=hit.Format(False),actual_removed_scope_area_mm2=hit.Area()/1e12))
 assert affected and all(row['net']==CORE for row in affected),'The literal In3 scope touches a different rail'
 # Prove the actual scope has no CORE source/contact/receiving barrel. Protect
 # every real CORE pad/annulus, not only the nominal connected receivers.
 pad_rows=[];via_guards=[]
 for pad in board.GetPads():
  if pad.GetNetname()!=CORE:continue
  xy=mm(pad.GetPosition());size=mm(pad.GetSize());roi=p.box(xy[0]-size[0]/2-1.,xy[1]-size[1]/2-1.,xy[0]+size[0]/2+1.,xy[1]+size[1]/2+1.)
  assert not p.intersection(roi,cut).OutlineCount(),'CORE pad/receiving margin intersects cleanup'
  pad_rows.append(dict(reference=pad.GetParentFootprint().GetReference(),pin=pad.GetNumber(),xy=xy,native_size_mm=size,minimum_retained_margin_mm=1.))
 for via in oldtracks.values():
  if via.Type()!=pcbnew.PCB_VIA_T or via.GetNetname()!=CORE:continue
  guard=circle(tuple(via.GetPosition()),pcbnew.FromMM(1.))
  assert not p.intersection(guard,cut).OutlineCount(),'CORE receiving annulus intersects cleanup'
  via_guards.append(dict(uuid=via.m_Uuid.AsString(),xy=mm(via.GetPosition()),retained_radius_mm=1.))
 pads={(x.GetParentFootprint().GetReference(),x.GetNumber()):x for x in board.GetPads()}
 pts=[mm(pads[key].GetPosition())for key in(('U2001','3'),('L2001','2'),('C2002','1'),('R2003','1'))]
 region=p.box(min(x for x,y in pts)-3,min(y for x,y in pts)-3,max(x for x,y in pts)+3,max(y for x,y in pts)+3)
 assert not p.intersection(region,cut).OutlineCount(),'Regulator/output/sense protected region intersects cleanup'
 zone=pcbnew.ZONE(board);zone.SetLayer(pcbnew.In3_Cu);zone.SetIsRuleArea(True)
 zone.SetZoneName('Literal CORE unused cusp between unchanged LOGIC antipads')
 zone.SetDoNotAllowZoneFills(True);zone.SetDoNotAllowTracks(False);zone.SetDoNotAllowVias(False);zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False);zone.Outline().Append(cut);board.Add(zone)
 dest=out/'motherboard-CORE-literal-antipad-join-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),board)
 # Native SWIG exposes m_Uuid read-only. Replace precisely the new zone's
 # unique native UUID in the saved source, so the paired correction is exact.
 text=dest.read_text();assert text.count(zone.m_Uuid.AsString())==1
 dest.write_text(text.replace(zone.m_Uuid.AsString(),UID),encoding='utf-8')
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
 for file in src.parent.iterdir():
  if file.is_dir()and file.suffix=='.pretty':shutil.copytree(file,out/file.name)
  elif file.name=='fp-lib-table':shutil.copyfile(file,out/file.name)
 report=dict(input_board_sha256=sha(src),input_source_sha256=sha('hardware/motherboard/design.json'),literal_bounds_mm=BOUNDS,actual_existing_antipad_bounding_box_mm=[40.012499,48.875,41.075,50.5],actual_added_collar_mm=.10,native_zone_minimum_feature_width_mm=.20,literal_rule_uuid=UID,existing_LOGIC_clearance_vias=via_rows,only_actual_removed_net=affected,all_CORE_pad_receiving_guards_disjoint=pad_rows,all_actual_CORE_via_guards_disjoint=via_guards,converter_output_sense_thermal_region_disjoint=True,no_tracks_pads_vias_or_existing_zone_definitions_changed=True,original_failed_thin_geometry_report_retained=True,adopted=False,manufacturing_ready=False)
 (out/'proposal.json').write_text(json.dumps(report,indent=2)+'\n')
 with(out/'native-command.log').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(out/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
 print(json.dumps(dict(kind=kind,command_exit=r.returncode,board_sha256=sha(dest),adopted=False)))
if __name__=='__main__':make(sys.argv[1])
