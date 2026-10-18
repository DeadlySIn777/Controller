"""Native source-owned F256 access and strict return-annulus pitch study.

Copies the real U1001 lands into persisted native fixtures. The bounded
package dimensions are .15 F dogbones/.50-.20 conventional vias under the
existing U1001-specific .125 pad/via rule. This does not relax the frozen
reference checker or qualify a populated-controller route.
"""
from pathlib import Path
import argparse,json,math,subprocess,collections,copy
import pcbnew
import hardware_route_selected_additive_r02 as e
import hardware_route_critical_digital_wip_r03 as wip
import hardware_check_return_corridors_r04 as fast
from hardware_check_return_corridors import uid

def point(xy):return pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in xy])
def track(board,net,start,end,layer,width=.15):
 t=pcbnew.PCB_TRACK(board);t.SetStart(point(start));t.SetEnd(point(end));t.SetWidth(pcbnew.FromMM(width));t.SetLayer(layer);t.SetNetCode(board.GetNetsByName()[net].GetNetCode());board.Add(t);return t
def via(board,net,xy):
 t=pcbnew.PCB_VIA(board);t.SetPosition(point(xy));t.SetWidth(pcbnew.FromMM(.50));t.SetDrill(pcbnew.FromMM(.20));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);t.SetNetCode(board.GetNetsByName()[net].GetNetCode());board.Add(t);return t
def rectangle_zone(board,net,layer,bounds,clearance):
 z=pcbnew.ZONE(board);z.SetLayer(layer);z.SetNetCode(board.GetNetsByName()[net].GetNetCode());z.SetLocalClearance(pcbnew.FromMM(clearance));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetMinThickness(pcbnew.FromMM(.05));z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS);z.SetAssignedPriority(0)
 poly=z.Outline();poly.NewOutline();x,y,x2,y2=bounds
 for xy in [(x,y),(x2,y),(x2,y2),(x,y2)]:poly.Append(point(xy))
 board.Add(z);return z

def fixture(native_board,mode,out,remote_clearance=.25):
 out.mkdir();src=pcbnew.LoadBoard(str(native_board));fp=next(f for f in src.GetFootprints()if f.GetReference()=='U1001')
 board=pcbnew.BOARD();layers=pcbnew.LSET()
 for l in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]:layers.AddLayer(l)
 board.SetEnabledLayers(layers);board.SetCopperLayerCount(6)
 f=pcbnew.FOOTPRINT(fp);board.Add(f);pads={p.GetNumber():p for p in f.Pads()};names={n:p.GetNetname()for n,p in pads.items()};nets={}
 for name in set(names.values()):
  n=pcbnew.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
 for n,p in pads.items():p.SetNetCode(nets[names[n]].GetNetCode())
 for a,b in [((78,30),(112,30)),((112,30),(112,56)),((112,56),(78,56)),((78,56),(78,30))]:
  s=pcbnew.PCB_SHAPE();s.SetShape(pcbnew.SHAPE_T_SEGMENT);s.SetStart(point(a));s.SetEnd(point(b));s.SetLayer(pcbnew.Edge_Cuts);s.SetWidth(pcbnew.FromMM(.05));board.Add(s)
 signal=[]
 sparse=mode=='sparse_outer'
 pairs=[('T14',(104.4,50.8)),('T15',(105.7,52.2))]if sparse else[('T14',(104.8,50.4)),('T15',(105.6,50.4 if mode=='dense' else 49.6))]
 rows={}
 for pin,xy in pairs:
  pad=pads[pin];net=pad.GetNetname();waypoints=[pcbnew.ToMM(pad.GetPosition()),xy]
  if sparse and pin=='T15':waypoints=[pcbnew.ToMM(pad.GetPosition()),(105.7,50.5),xy]
  for start,end in zip(waypoints,waypoints[1:]):signal.append(track(board,net,start,end,pcbnew.F_Cu,.20 if sparse else .15))
  signal.append(via(board,net,xy))
  end=(xy[0],54)if sparse else((104.8,53)if pin=='T14'else(xy[0],48.8))
  signal.append(track(board,net,xy,end,pcbnew.B_Cu,.35 if sparse else .15))
  rows[net]=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},reference_corridor_margin_mm=.40 if sparse else .20,allow_vias=True,via_diameter_mm=.50,via_drill_mm=.20,return_stitch_distance_mm=1.0)
 returns=[('T13',(103.6,50.8)),('T16',(106.5,52.2))]if sparse else[('T13',(104,50.4)),('T16',(106.4,50.4 if mode=='dense' else 49.6))]
 for pin,xy in returns:
  if pads[pin].GetNetname()!='/LOGIC_GND':raise ValueError('Actual FPGA GND source pin changed')
  waypoints=[pcbnew.ToMM(pads[pin].GetPosition()),xy]
  if sparse and pin=='T16':waypoints=[pcbnew.ToMM(pads[pin].GetPosition()),(106.5,50.5),xy]
  for start,end in zip(waypoints,waypoints[1:]):track(board,'/LOGIC_GND',start,end,pcbnew.F_Cu,.20 if sparse else .15)
  via(board,'/LOGIC_GND',xy)
 for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:rectangle_zone(board,'/LOGIC_GND',layer,(90,33,110,55),.15)
 # This SOURCE-connected remote region duplicates the actual root's .25
 # remote LOGIC clearance policy. It is not treated as a nominal fill.
 rectangle_zone(board,'/LOGIC_GND',pcbnew.In1_Cu,(80,32,84,36),remote_clearance)
 via(board,'/LOGIC_GND',(82,34));track(board,'/LOGIC_GND',(82,34),(94,34),pcbnew.In1_Cu,.2)
 path=out/'actual-F256-package-access.kicad_pcb';pcbnew.SaveBoard(str(path),board)
 project=json.loads(native_board.with_suffix('.kicad_pro').read_text());path.with_suffix('.kicad_pro').write_text(json.dumps(project))
 path.with_suffix('.kicad_dru').write_text(native_board.with_suffix('.kicad_dru').read_text())
 drc=out/'native.json';run=subprocess.run([str(e.CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','--output',str(drc),str(path)],capture_output=True,text=True,encoding='utf8',errors='replace');(out/'native.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Actual native package fixture did not execute')
 fresh=pcbnew.LoadBoard(str(path));report=json.loads(drc.read_text());errors=[v for v in report['violations']if v['severity']=='error']
 try:own=fast.return_corridor_check(fresh,{uid(t)for t in signal},rows)
 except ValueError as exc:own=dict(passed=False,reason=str(exc))
 e.write(out/'actual-return-proof.json',own)
 r=dict(mode=mode,remote_clearance_mm=remote_clearance,actual_native_errors=errors,actual_native_warnings=[v for v in report['violations']if v['severity']=='warning'],actual_return_proof=own,
  actual_signal_via_distance_mm=math.dist(pairs[0][1],pairs[1][1]),actual_source_ground_stitch_distance_mm=.8,manifest_rows=rows,
  native_fixture_board_sha256=e.sha(path),current_controller_route_adopted=False,manufacturing_ready=False)
 e.write(out/'review.json',r);return r

def audit(board_path,out):
 board_path=Path(board_path).resolve();out=e.require_new_report(out);fast.dependencies();b=pcbnew.LoadBoard(str(board_path));b.BuildConnectivity()
 _,nodes=e.native_source_check(b,e.read(e.ROOT/'hardware/motherboard/design.json'),e.ROOT/'hardware/motherboard/netlist.xml')
 fp=next(f for f in b.GetFootprints()if f.GetReference()=='U1001');review=e.read(e.ROOT/'reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/critical-digital-source-review.json')
 geometry=e.read(e.ROOT/'reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
 inventory=[]
 for p in fp.Pads():
  critical=p.GetNetname()in geometry['nets'];direct=[]
  for t in b.GetTracks():
   if t.GetNetname()!=p.GetNetname()or isinstance(t,pcbnew.PCB_VIA):continue
   if min(math.dist(tuple(p.GetPosition()),tuple(x))for x in [t.GetStart(),t.GetEnd()])<=p.GetSize().x/2+t.GetWidth()/2:
    direct.append(dict(uuid=uid(t),width_mm=pcbnew.ToMM(t.GetWidth()),layer=b.GetLayerName(t.GetLayer())))
  inventory.append(dict(pin=p.GetNumber(),native_pad_uuid=uid(p),net=p.GetNetname(),xy_mm=pcbnew.ToMM(p.GetPosition()),land_mm=pcbnew.ToMM(p.GetSize()),critical_reviewed=critical,critical_source_reviewed=p.GetNetname()in review['nets'],actual_direct_native_access=direct))
 clearances={}
 for name,layer in [('In1.Cu',pcbnew.In1_Cu),('In4.Cu',pcbnew.In4_Cu)]:
  clearances[name]=dict(collections.Counter(str(round(pcbnew.ToMM(z.GetLocalClearance()),4))for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()=='/LOGIC_GND'and z.HasFilledPolysForLayer(layer)and z.GetFilledPolysList(layer).Area()))
 cases=[]
 for mode in ['sparse_outer','staggered','dense']:cases.append(fixture(board_path,mode,out/mode))
 r=dict(board_sha256=e.sha(board_path),source_design_sha256=e.sha(e.ROOT/'hardware/motherboard/design.json'),source_netlist_sha256=e.sha(e.ROOT/'hardware/motherboard/netlist.xml'),
  tool_sha256=e.sha(__file__),native_package_pads=len(inventory),package_inventory=inventory,critical_pads=sum(p['critical_reviewed']for p in inventory),critical_full_source_pads=sum(p['critical_source_reviewed']for p in inventory),
  critical_pads_without_direct_escape=[p['pin']for p in inventory if p['critical_reviewed']and not p['actual_direct_native_access']],
  actual_filled_LOGIC_local_clearance_histograms=clearances,
  dimensions=dict(pad_diameter_mm=.35,pitch_mm=.8,dogbone_width_mm=.15,signal_via_diameter_mm=.5,signal_via_drill_mm=.2,diagonal_pad_via_gap_mm=math.sqrt(2)*.4-.175-.25,existing_U1001_pad_via_rule_mm=.125,own_reference_annulus_mm=.2,global_maximum_LOGIC_clearance_mm=.25,
   current_strict_checker_antipad_radius_mm=.25+.25+.02,current_strict_checker_outer_annulus_radius_mm=.25+.25+.02+.2),
  cases=cases,prototype_package_access_only=True,current_controller_routes_completed=False,manufacturing_ready=False)
 r['dimensions']['minimum_signal_via_spacing_given_actual_local_015mm']=.72+.4
 r['passed']=cases[0]['actual_return_proof'].get('passed')is True and not cases[0]['actual_native_errors']and all(c['actual_return_proof'].get('passed')is False and c['actual_native_errors'] for c in cases[1:])
 e.write(out/'review.json',r);return r
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=audit(a.board,a.out);print(json.dumps(dict(passed=r['passed'],native_package_pads=r['native_package_pads'],critical_pads=r['critical_pads'],unescaped=len(r['critical_pads_without_direct_escape']),fixture_results=[dict(mode=c['mode'],native_errors=len(c['actual_native_errors']),own_return_pass=c['actual_return_proof']['passed'])for c in r['cases']],manufacturing_ready=False)))
if __name__=='__main__':main()
