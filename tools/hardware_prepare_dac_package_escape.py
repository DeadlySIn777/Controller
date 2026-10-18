"""Exact AD5683R MSOP10 F-side necks; never an adopted dangling-route release.

Only U14608/U14626 pins 2,3,6,7,8 are permitted. Reviewed .35 mm trunks
remain separate. A .20 mm neck goes straight .85 mm beyond the pad centre,
then staggers .075 mm at a 1.0 mm outward handoff. Every neck still needs
the full .40 mm own-reference envelope and actual native clearance proof.
This tool prepares a coupled-routing input; no dangling input is accepted as
a finished donor. Final complete routes must pass the original-board warning,
source-cluster, native identity and own-return gates before parent adoption.
"""
from pathlib import Path
import argparse,copy,json,math,uuid,shutil
import pcbnew
import hardware_route_critical_digital_wip_r05 as native
import hardware_check_return_corridors_r04 as returns
import hardware_route_critical_digital_additive as critical

engine=native.engine
PINS={'2':(-1,-.075),'3':(-1,.075),'6':(1,.075),'7':(1,0),'8':(1,-.075)}
OWNERS={'U14608':'AO0','U14626':'AO1'}

def recipe(pad,owner,review):
 pin=pad.GetNumber()
 if owner not in OWNERS or pin not in PINS:raise ValueError('Only the literal reviewed DAC signal pins are allowed')
 if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or not pad.IsOnLayer(pcbnew.F_Cu):raise ValueError('Fitted F-side SMD source land required')
 size=pcbnew.ToMM(pad.GetSize())
 if tuple(round(v,6)for v in size)!=(1.5,.35):raise ValueError('Exact manufacturer-reviewed native MSOP land changed')
 row=review['nets'].get(pad.GetNetname())
 if not row or [owner,pin]not in row['source_pins']:raise ValueError('Actual DAC source pin/net not reviewed')
 if not any(p['reference']==owner and p['pin']==pin and p['mpn']=='AD5683RBRMZ-3'for p in row['source_endpoints']):
  raise ValueError('Exact source part/pin identity required')
 direction,stagger=PINS[pin];x,y=pcbnew.ToMM(pad.GetPosition())
 points=[[x,y],[x+direction*.85,y],[x+direction*1.0,y+stagger]]
 if not stagger:points=[points[0],points[-1]]
 length=sum(math.dist(a,b)for a,b in zip(points,points[1:]))
 if length>1.05:raise ValueError('Bounded short package escape exceeded')
 return dict(owner=owner,pin=pin,pad_uuid=pad.m_Uuid.AsString(),net=pad.GetNetname(),
  actual_MPN='AD5683RBRMZ-3',actual_native_pad_mm=[1.5,.35],native_pitch_mm=.5,
  straight_neck_width_mm=.2,trunk_width_mm=.35,points_mm=points,length_mm=length,
  no_vias=True,layer='F.Cu',return_net=row['return_net'],reference_layer='In1.Cu',
  reference_corridor_margin_mm=.4,minimum_new_copper_clearance_mm=.2,
  numeric_land_screen_is_not_native_DRC=True,manufacturer_impedance_claim=False,
  assembly_factory_impedance_and_loaded_profile_qualified=False)

def proposal(board_path,owners,out):
 board_path=Path(board_path).resolve();out=engine.require_new_report(out)
 owners=set(owners)
 if not owners or not owners<=set(OWNERS):raise ValueError('Literal fitted DAC owner required')
 returns.dependencies()
 if engine.sha(engine.ROOT/critical.SOURCE_REVIEW)!=critical.SOURCE_REVIEW_SHA:raise ValueError('Frozen native source review changed')
 review=engine.read(engine.ROOT/critical.SOURCE_REVIEW)
 board=pcbnew.LoadBoard(str(board_path));_,nodes=engine.native_source_check(board,engine.read(engine.ROOT/'hardware/motherboard/design.json'),engine.ROOT/'hardware/motherboard/netlist.xml')
 fps={f.GetReference():f for f in board.GetFootprints()};rows=[]
 for owner in sorted(owners):
  fp=fps[owner]
  if fp.GetOrientationDegrees()!=0 or fp.GetLayer()!=pcbnew.F_Cu:raise ValueError('Unreviewed native DAC pose/orientation')
  pads={p.GetNumber():p for p in fp.Pads()}
  rows.extend(recipe(pads[pin],owner,review)for pin in PINS)
 # The proposal ledger is always emitted. It cannot authorize a missing
 # reference or an actual route whose full continuation has not been built.
 ledger=dict(board_sha256=engine.sha(board_path),source_design_sha256=engine.sha(engine.ROOT/'hardware/motherboard/design.json'),
  source_netlist_sha256=engine.sha(engine.ROOT/'hardware/motherboard/netlist.xml'),
  source_review_sha256=critical.SOURCE_REVIEW_SHA,rows=rows,tool_sha256=engine.sha(__file__),
  coupled_trunk_routing_required=True,staging_only=True,complete_routes=False,manufacturing_ready=False)
 engine.write(out/'package-escape-proposal.json',ledger)
 added=[];by_net={}
 for row in rows:
  source=copy.deepcopy(review['nets'][row['net']]);source.update(layers=['F.Cu'],reference_layers={'F.Cu':'In1.Cu'},reference_corridor_margin_mm=.4,allow_vias=False)
  by_net[row['net']]=source
  for start,end in zip(row['points_mm'],row['points_mm'][1:]):
   t=pcbnew.PCB_TRACK(board);t.SetStart(pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in start]));t.SetEnd(pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in end]));t.SetWidth(pcbnew.FromMM(.2));t.SetLayer(pcbnew.F_Cu);t.SetNetCode(board.GetNetsByName()[row['net']].GetNetCode());board.Add(t);added.append(t)
 try:proof=returns.return_corridor_check(board,{t.m_Uuid.AsString()for t in added},by_net)
 except ValueError as exc:
  engine.write(out/'actual-reference-rejected.json',dict(passed=False,reason=str(exc),proposal_only=True,manufacturing_ready=False));raise
 engine.write(out/'actual-reference-proof.json',proof)
 # Append exact native segment objects to the original authoritative AST.
 tree=engine.parse(board_path.read_text(encoding='utf8'));old=copy.deepcopy(tree)
 for t in added:
  row=['segment',['start',str(pcbnew.ToMM(t.GetStart().x)),str(pcbnew.ToMM(t.GetStart().y))],
   ['end',str(pcbnew.ToMM(t.GetEnd().x)),str(pcbnew.ToMM(t.GetEnd().y))],['width','.2'],['layer','"F.Cu"'],
   ['net',engine.q(t.GetNetname())],['uuid',engine.q(t.m_Uuid.AsString())]]
  tree.append(row)
 if engine.immutable_objects(old)!=engine.immutable_objects(tree):raise ValueError('Proposal changed authoritative lands/poses/source/zone definitions')
 dest=out/'package-escape-coupled-routing-input.kicad_pcb';dest.write_text(native.dump_native_board(tree)+'\n',encoding='utf8')
 for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(board_path.with_suffix(suffix),dest.with_suffix(suffix))
 for folder in board_path.parent.glob('*.pretty'):shutil.copytree(folder,out/folder.name)
 if(board_path.parent/'fp-lib-table').is_file():shutil.copyfile(board_path.parent/'fp-lib-table',out/'fp-lib-table')
 ledger.update(staging_board_sha256=engine.sha(dest),actual_reference_proof=proof,
  added_copper_uuids=[t.m_Uuid.AsString()for t in added],all_old_copper_and_immutable_objects_retained=True,
  native_DRC_pending=True,warning_free_final_routes_required=True)
 engine.write(out/'receipt.json',ledger);return ledger
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--owner',action='append',required=True)
 a=p.parse_args();r=proposal(a.board,a.owner,a.out);print(json.dumps(dict(necks=len(r['rows']),staging_only=True,complete_routes=False,manufacturing_ready=False)))
if __name__=='__main__':main()
