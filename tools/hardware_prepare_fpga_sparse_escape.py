"""Actual SOURCE-owned T14/T15 sparse outer-row access, pending complete trunks.

This applies the copied-package proof to a real controller copy. It does not
grant plane qualification, forgive new dangling warnings or complete a net.
Original lands, source pins, all old copper and all zone definitions stay exact.
"""
from pathlib import Path
import argparse,copy,json,math,shutil
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_audit_fpga_package_access as package
import hardware_check_return_corridors_r04 as returns
import hardware_route_owned_bypass_loops_wip_r03 as warning
e=authority.engine

def apply(board_path,out):
 board_path=Path(board_path).resolve();out=e.require_new_report(out);returns.dependencies()
 b=pcbnew.LoadBoard(str(board_path));_,nodes=e.native_source_check(b,e.read(e.ROOT/'hardware/motherboard/design.json'),e.ROOT/'hardware/motherboard/netlist.xml')
 fp=next(f for f in b.GetFootprints()if f.GetReference()=='U1001');pads={p.GetNumber():p for p in fp.Pads()}
 if pcbnew.ToMM(fp.GetPosition())!=(100.0,44.0)or fp.GetOrientationDegrees()!=0:raise ValueError('Literal reviewed FPGA pose changed')
 review=e.read(e.ROOT/'reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/critical-digital-source-review.json')
 signal=[];ground=[];rows={};ledger=[]
 recipes=[('T14','/fpga_core/IOL1_L1_MISO',[(104.4,50),(104.4,50.8)],(104.4,53.2)),('T15','/fpga_core/IOL1_L3_MISO',[(105.2,50),(105.7,50.5),(105.7,52.2)],(105.7,54))]
 for pin,net,points,stop in recipes:
  p=pads[pin]
  if p.GetNetname()!=net or ["U1001",pin]not in review['nets'][net]['source_pins']:raise ValueError('Actual FPGA source identity changed')
  if pcbnew.ToMM(p.GetSize())!=(.35,.35)or pcbnew.ToMM(p.GetPosition())!=points[0]:raise ValueError('Actual native FPGA land changed')
  row=copy.deepcopy(review['nets'][net]);row.update(via_diameter_mm=.5,via_drill_mm=.2,reference_corridor_margin_mm=.4);rows[net]=row
  for a,z in zip(points,points[1:]):signal.append(package.track(b,net,a,z,pcbnew.F_Cu,.2))
  signal.append(package.via(b,net,points[-1]));signal.append(package.track(b,net,points[-1],stop,pcbnew.B_Cu,.35))
  ledger.append(dict(pin=pin,net=net,source_pins=nodes[net],F_points_mm=points,B_handoff_mm=stop,via_mm=[.5,.2],neck_width_mm=.2,trunk_width_mm=.35,return_net='/LOGIC_GND',reference_corridor_margin_mm=.4))
 for pin,points in [('T13',[(103.6,50),(103.6,50.8)]),('T16',[(106,50),(106.5,50.5),(106.5,52.2)])]:
  if pads[pin].GetNetname()!='/LOGIC_GND'or pcbnew.ToMM(pads[pin].GetPosition())!=points[0]:raise ValueError('Actual numbered FPGA GND source changed')
  for a,z in zip(points,points[1:]):ground.append(package.track(b,'/LOGIC_GND',a,z,pcbnew.F_Cu,.2))
  ground.append(package.via(b,'/LOGIC_GND',points[-1]))
 old=e.parse(board_path.read_text(encoding='utf8'));tree=copy.deepcopy(old)
 for t in signal+ground:
  if isinstance(t,pcbnew.PCB_VIA):
   row=['via',['at',*[str(v)for v in pcbnew.ToMM(t.GetPosition())]],['size','.5'],['drill','.2'],['layers','"F.Cu"','"B.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]]
  else:row=['segment',['start',*[str(v)for v in pcbnew.ToMM(t.GetStart())]],['end',*[str(v)for v in pcbnew.ToMM(t.GetEnd())]],['width',str(pcbnew.ToMM(t.GetWidth()))],['layer',e.q(b.GetLayerName(t.GetLayer()))],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]]
  tree.append(row)
 if e.immutable_objects(old)!=e.immutable_objects(tree):raise ValueError('Actual escape changed immutable source/lands/poses/planes')
 path=out/'motherboard-sparse-FPGA-escape-staging.kicad_pcb';path.write_text(authority.dump_native_board(tree)+'\n',encoding='utf8')
 for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(board_path.with_suffix(suffix),path.with_suffix(suffix))
 for folder in board_path.parent.glob('*.pretty'):shutil.copytree(folder,out/folder.name)
 if(board_path.parent/'fp-lib-table').is_file():shutil.copyfile(board_path.parent/'fp-lib-table',out/'fp-lib-table')
 baseline=e.read(board_path.parent/'baseline-disposition.json')
 known=warning.reviewed_wip_warnings(e.read(board_path.parent/'drc.json'),baseline,e.sha(board_path))
 run=warning.drc(path,out,'actual-native');fresh=pcbnew.LoadBoard(str(path));fresh.BuildConnectivity()
 actual_tree=e.parse(path.read_text(encoding='utf8'))
 if e.immutable_objects(old)!=e.immutable_objects(actual_tree):raise ValueError('Native actual refill changed immutable source/lands/poses/planes')
 old_cu={e.value(e.child(t,'uuid')[1]):e.dump(t)for k in ['segment','via','arc']for t in e.children(old,k)}
 final_cu={e.value(e.child(t,'uuid')[1]):e.dump(t)for k in ['segment','via','arc']for t in e.children(actual_tree,k)}
 if any(final_cu.get(u)!=v for u,v in old_cu.items()):raise ValueError('Actual old copper identity changed')
 e.native_source_check(fresh,e.read(e.ROOT/'hardware/motherboard/design.json'),e.ROOT/'hardware/motherboard/netlist.xml')
 try:proof=returns.return_corridor_check(fresh,{t.m_Uuid.AsString()for t in signal},rows)
 except ValueError as exc:proof=dict(passed=False,reason=str(exc))
 new_defects=warning.new_route_defects(run,known)
 result=dict(board_sha256=e.sha(board_path),staging_board_sha256=e.sha(path),source_design_sha256=e.sha(e.ROOT/'hardware/motherboard/design.json'),source_netlist_sha256=e.sha(e.ROOT/'hardware/motherboard/netlist.xml'),
  exact_recipes=ledger,new_signal_UUIDs=[t.m_Uuid.AsString()for t in signal],new_SOURCE_ground_UUIDs=[t.m_Uuid.AsString()for t in ground],
  all_old_copper_and_immutable_objects_retained=True,actual_reference_proof=proof,native_DRC=run,actual_new_route_defects=new_defects,
  complete_net_routes=False,current_controller_route_adopted=False,manufacturing_ready=False,tool_sha256=e.sha(__file__))
 e.write(out/'receipt.json',result);return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=apply(a.board,a.out);print(json.dumps(dict(actual_own_return_pass=r['actual_reference_proof']['passed'],new_native_defects=len(r['actual_new_route_defects']),complete_routes=False,adopted=False)))
if __name__=='__main__':main()
